import json

from confluent_kafka import Producer

from config.config import KafkaConfig
from logger import logger
from models.movement import MovementData


class WarehouseProducer(Producer):
    def __init__(self, config: KafkaConfig):
        super().__init__(config.to_dict())
        self.topic_name = config.topic_name

    def create_topic(self) -> None:
        self.produce(self.topic_name, "create_movement")
        self.flush()

    def produce_msg(self, data: MovementData) -> None:
        self.produce(self.topic_name, json.dumps({"data": data.to_dict()}), callback=self.delivery_report)
        self.flush()

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Kafka producer delivery error: {err}")
