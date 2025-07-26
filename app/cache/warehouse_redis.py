from redis import asyncio as aioredis

from config.config import RedisConfig

CACHE_TTL = 60  # 1 minute
EMPTY_CACHE_VALUE = b""


class WarehouseRedis(aioredis.Redis):
    def __init__(self, config: RedisConfig):
        super().__init__(host=config.host, port=config.port, db=config.db, password=config.password)
