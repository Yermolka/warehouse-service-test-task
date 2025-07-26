from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, insert, select, update

from config.config import DbConfig
from models.movement import Movement, MovementData, MovementEvent, WarehouseProducts


class Db:
    config: DbConfig
    pool: AsyncConnectionPool
    engine: AsyncEngine

    def __init__(self, config: DbConfig):
        self.config = config

    async def init(self):
        self.engine = create_async_engine(
            f"postgresql+psycopg://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.db_name}",
            pool_size=self.config.pool_size,
            echo=True,
            echo_pool=True,
            isolation_level="AUTOCOMMIT",
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def close(self):
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        sessionmaker = async_sessionmaker(bind=self.engine)
        async with sessionmaker() as session:
            yield session

    async def get_movement_by_id(self, movement_id: UUID) -> Movement | None:
        async with self.session() as session:
            res = await session.execute(select(Movement).where(Movement.id == movement_id))
            row = res.first()
            if row is None:
                return None
            return row.tuple()[0]

    async def get_warehouse_product_quantity(self, warehouse_id: UUID, product_id: UUID) -> int | None:
        async with self.session() as session:
            res = await session.execute(
                select(WarehouseProducts.quantity).where(
                    WarehouseProducts.warehouse_id == warehouse_id, WarehouseProducts.product_id == product_id
                )
            )
            row = res.first()
            if row is None:
                return None
            return row.tuple()[0]

    async def upsert_movement(self, data: MovementData):
        async with self.session() as session:
            res = await session.execute(select(Movement).where(Movement.id == data.movement_id))
            row = res.first()
            if row is None:
                movement = Movement.from_data(data)
                await session.execute(insert(Movement).values(movement.model_dump()))
            else:
                movement = row.tuple()[0]
                if movement.event_type == data.event or movement.event_type == MovementEvent.FULL:
                    raise ValueError(f"Movement {data.movement_id} already exists")

                movement.merge_data_values(data)
                await session.execute(update(Movement).where(Movement.id == data.movement_id).values(movement.model_dump()))  # type: ignore

            quantity_delta = data.quantity if data.event == MovementEvent.ARRIVAL else -data.quantity
            await self.update_warehouse_product_quantity(data.warehouse_id, data.product_id, quantity_delta)

    async def update_warehouse_product_quantity(self, warehouse_id: UUID, product_id: UUID, quantity: int):
        async with self.session() as session:
            exists_res = await session.execute(
                select(WarehouseProducts).where(
                    WarehouseProducts.warehouse_id == warehouse_id, WarehouseProducts.product_id == product_id
                )
            )
            if exists_res.first() is not None:
                await session.execute(
                    update(WarehouseProducts)
                    .where(WarehouseProducts.warehouse_id == warehouse_id, WarehouseProducts.product_id == product_id)  # type: ignore
                    .values(quantity=WarehouseProducts.quantity + quantity)
                )
            else:
                await session.execute(
                    insert(WarehouseProducts).values(warehouse_id=warehouse_id, product_id=product_id, quantity=quantity)
                )
