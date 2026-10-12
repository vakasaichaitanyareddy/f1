import redis.asyncio as aioredis
from app.core.config import settings
import json
from typing import Optional, Any

class RedisClient:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        try:
            self._redis = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await self._redis.ping()
        except Exception:
            # Graceful degradation if Redis is offline during local test
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            return None
        try:
            val = await self._redis.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 60) -> bool:
        if not self._redis:
            return False
        try:
            await self._redis.set(key, json.dumps(value), ex=ttl_seconds)
            return True
        except Exception:
            return False

    async def close(self):
        if self._redis:
            await self._redis.close()

redis_client = RedisClient()
