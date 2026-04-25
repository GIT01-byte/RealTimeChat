from application.infrastructure.redis_client import RedisClient


class RedisService:
    def __init__(self, redis_client: RedisClient):
        self._redis = redis_client.get_redis_client()

    async def set_value(self, key: str, value: str, expire_seconds: int = 0) -> None:
        await self._redis.set(key, value, ex=expire_seconds)

    async def get_value(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def delete_value(self, key: str) -> None:
        await self._redis.delete(key)
