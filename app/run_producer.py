import os
from datetime import datetime, timedelta
from random import randint
from uuid import UUID, uuid4

from config.config import KafkaConfig
from kafka.producer import WarehouseProducer
from models.movement import MovementData, MovementEvent

APP_HOST = os.getenv("APP_HOST", "http://localhost:8000")
KAFKA_CONFIG = KafkaConfig()

LOAD_SIZE = 1_000_000


def mock_movement_pair(movement_id: UUID) -> tuple[MovementData, MovementData]:
    movement_id = movement_id
    warehouse_id_from = uuid4()
    warehouse_id_to = uuid4()
    product_id = uuid4()
    quantity = randint(0, 1000000)
    timestamp = datetime.now()

    data_from = MovementData(
        movement_id=movement_id,
        warehouse_id=warehouse_id_from,
        timestamp=timestamp,
        event=MovementEvent.DEPARTURE,
        product_id=product_id,
        quantity=quantity,
    )
    data_to = MovementData(
        movement_id=movement_id,
        warehouse_id=warehouse_id_to,
        timestamp=timestamp + timedelta(seconds=1),
        event=MovementEvent.ARRIVAL,
        product_id=product_id,
        quantity=quantity,
    )

    return data_from, data_to


if __name__ == "__main__":
    producer = WarehouseProducer(KAFKA_CONFIG)
    movement_ids = [uuid4() for _ in range(LOAD_SIZE)]
    for movement_id in movement_ids:
        data_from, data_to = mock_movement_pair(movement_id)
        producer.produce_msg(data_from)
        producer.produce_msg(data_to)
