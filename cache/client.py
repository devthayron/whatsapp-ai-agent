from functools import lru_cache

import redis
import redis.asyncio as aioredis

from config import settings

_OPTIONS = {
    "decode_responses": True,
    "socket_connect_timeout": 1,
    "socket_timeout": 5,
}


@lru_cache
def get_redis() -> redis.Redis:
    """Cliente síncrono (webhook)."""
    return redis.Redis.from_url(settings.REDIS_URL, **_OPTIONS)


@lru_cache
def get_async_redis() -> aioredis.Redis:
    """Cliente assíncrono (worker)."""
    return aioredis.Redis.from_url(settings.REDIS_URL, **_OPTIONS)
