import json
from typing import Final

from confluent_kafka import Consumer, Message

from cache.warehouse_redis import WarehouseRedis
from config.config import KafkaConfig, RedisConfig
from db import Db
from kafka.metrics import KAFKA_CONSUMER_MESSAGES_PROCESSED
from logger import logger
from models.movement import Movement, MovementData, WarehouseProducts


class WarehouseConsumer(Consumer):
    EXPECTED_DATA_FIELDS: Final[list[str]] = ["movement_id", "warehouse_id", "timestamp", "event", "product_id", "quantity"]
    name: Final[str] = "warehouse_consumer"
    running: bool = False
    config: KafkaConfig

    def __init__(self, config: KafkaConfig, db: Db, redis_config: RedisConfig):
        self.config = config
        super().__init__(config.to_dict())
        self.topics = [config.topic_name]
        self.db = db
        self.redis = WarehouseRedis(redis_config)

    async def start_consume(self) -> None:
        self.subscribe(self.topics)
        self.running = True

        logger.info(f"Kafka consumer subscribed to topics: {self.topics}")

        while self.running:
            msg = self.poll(timeout=self.config.max_poll_interval_ms / 1000)

            if msg is None:
                continue

            if msg.error():
                logger.error(f"Kafka consumer error: {msg.error()}")
                continue

            status = await self.process(msg)
            self.commit()

            KAFKA_CONSUMER_MESSAGES_PROCESSED.labels(topic=msg.topic(), status="ok" if status else "error").inc()
        else:
            logger.info("Kafka consumer stopped")
            self.close()

    async def process(self, msg: Message) -> bool:
        # Should not happen, for typechecking
        value_bytes = msg.value()
        if value_bytes is None:
            return False

        try:
            value: dict = json.loads(value_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(f"Kafka consumer invalid message: {value_bytes}", exc_info=e)
            return False

        if not isinstance(value, dict) or value.get("data") is None:
            logger.error(f"Kafka consumer invalid message structure: {value}")
            return False

        data: dict = value["data"]

        try:
            movement_data = MovementData.from_dict(data)
        except Exception as e:
            logger.error(f"Kafka consumer invalid message data: {data}", exc_info=e)
            return False

        try:
            await self.db.upsert_movement(movement_data)
        except ValueError as e:
            logger.error(f"Kafka consumer duplicate movement: {value}", exc_info=e)
            return False

        # Invalidate cache
        await self.redis.delete(WarehouseProducts.get_cache_key(movement_data.warehouse_id, movement_data.product_id))
        await self.redis.delete(Movement.get_cache_key(movement_data.movement_id))

        return True
