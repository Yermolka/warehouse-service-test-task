import os
from asyncio import sleep
from datetime import datetime, timedelta
from random import randint
from uuid import uuid4

import aiohttp
import pytest

from config.config import KafkaConfig
from kafka.producer import WarehouseProducer
from models.movement import Movement, MovementData, MovementEvent, MovementPublic

APP_HOST = os.getenv("APP_HOST", "http://localhost:8000")
KAFKA_CONFIG = KafkaConfig()


def mock_movement_pair() -> tuple[MovementData, MovementData]:
    movement_id = uuid4()
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


@pytest.mark.asyncio
@pytest.mark.parametrize("data_from, data_to", [mock_movement_pair()])
async def test_movements(data_from: MovementData, data_to: MovementData):
    movement_from = Movement.from_data(data_from)

    movement_full = Movement.from_data(data_to)
    movement_full.merge_data_values(data_from)

    producer = WarehouseProducer(KAFKA_CONFIG)
    producer.produce_msg(data_from)

    # Wait for the message to be processed
    await sleep(0.1)

    async with aiohttp.ClientSession(f"{APP_HOST}/api/") as session:
        async with session.get(f"movements/{data_from.movement_id}") as response:
            assert response.status == 200
            json_data = await response.json()

            expected_public_movement = MovementPublic.from_movement(movement_from)
            actual_public_movement = MovementPublic.from_dict(json_data)
            assert expected_public_movement == actual_public_movement

        async with session.get(f"warehouses/{data_from.warehouse_id}/products/{data_from.product_id}") as response:
            assert response.status == 200
            json_data = await response.json()

            assert json_data["quantity"] == 0

    producer.produce_msg(data_to)

    await sleep(0.1)

    async with aiohttp.ClientSession(f"{APP_HOST}/api/") as session:
        async with session.get(f"movements/{data_from.movement_id}") as response:
            assert response.status == 200
            json_data = await response.json()

            expected_public_movement = MovementPublic.from_movement(movement_full)
            actual_public_movement = MovementPublic.from_dict(json_data)
            assert expected_public_movement == actual_public_movement

        async with session.get(f"warehouses/{data_to.warehouse_id}/products/{data_to.product_id}") as response:
            assert response.status == 200
            json_data = await response.json()

            assert json_data["quantity"] == data_to.quantity
