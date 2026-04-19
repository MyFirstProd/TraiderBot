from __future__ import annotations

from redis.asyncio import Redis

from app.config.settings import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(get_settings().REDIS_URL, encoding="utf-8", decode_responses=True)
    return _client
