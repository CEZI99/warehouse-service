import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

async def init_cache():
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    redis = aioredis.from_url(
        redis_url,
        encoding="utf8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True
    )
    FastAPICache.init(
        RedisBackend(redis),
        prefix="warehouse-cache",
        enable=True,
        expire=3600  # Общее время жизни кэша по умолчанию
    )
