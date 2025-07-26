import json
from uuid import UUID

from cache.warehouse_redis import CACHE_TTL, EMPTY_CACHE_VALUE, WarehouseRedis
from db import Db
from models.movement import Movement, WarehouseProducts


class WarehouseService:
    db: Db
    redis: WarehouseRedis

    def setup(self, db: Db, redis: WarehouseRedis):
        self.db = db
        self.redis = redis

    async def get_warehouse_product_quantity(self, warehouse_id: UUID, product_id: UUID) -> int:
        wh_product_cache_key = WarehouseProducts.get_cache_key(warehouse_id, product_id)
        wh_product_quant_str: str | None = await self.redis.get(wh_product_cache_key)  # type: ignore

        if wh_product_quant_str is None:
            wh_product_quant: int | None = await self.db.get_warehouse_product_quantity(warehouse_id, product_id)
            await self.redis.set(wh_product_cache_key, wh_product_quant or 0, ex=CACHE_TTL)  # type: ignore
        else:
            wh_product_quant = int(wh_product_quant_str)

        if wh_product_quant is None:
            wh_product_quant = 0

        # Quantity may be negative if the msg queue is not in the correct order
        # i.e. event of departure is received before event of arrival
        return max(wh_product_quant, 0)

    async def get_movement(self, movement_id: UUID) -> Movement | None:
        movement_cache_key = Movement.get_cache_key(movement_id)
        movement_dict: str | None = await self.redis.get(movement_cache_key)

        if movement_dict == EMPTY_CACHE_VALUE:
            return None

        if movement_dict is None:
            movement = await self.db.get_movement_by_id(movement_id)
            await self.redis.set(
                movement_cache_key,
                json.dumps(movement.model_dump(mode="json")) if movement else EMPTY_CACHE_VALUE,
                ex=CACHE_TTL,
            )
        else:
            movement = Movement(**json.loads(movement_dict))

        return movement
