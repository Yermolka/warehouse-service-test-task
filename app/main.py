import asyncio
import os
from threading import Thread

import uvicorn

from api.main import app
from cache.warehouse_redis import WarehouseRedis
from config.config import DbConfig, KafkaConfig, RedisConfig
from db import Db
from kafka.consumer import WarehouseConsumer
from kafka.producer import WarehouseProducer
from services.warehouse import WarehouseService

db_config = DbConfig()
kafka_config = KafkaConfig()
redis_config = RedisConfig()

db = Db(db_config)
redis = WarehouseRedis(redis_config)

asyncio.run(db.init())

for _ in range(int(os.getenv("NUM_CONSUMERS", 1))):
    consumer = WarehouseConsumer(kafka_config, db=db, redis_config=redis_config)

    consumer_thread = Thread(target=asyncio.run, args=(consumer.start_consume(),))
    consumer_thread.start()

# Init kafka topic
producer = WarehouseProducer(kafka_config)
producer.create_topic()

warehouse_service = WarehouseService()
warehouse_service.setup(db, redis)

app.dependency_overrides[WarehouseService] = lambda: warehouse_service

uvicorn.run(app, host="0.0.0.0", port=8000)
