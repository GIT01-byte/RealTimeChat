from application.configs.settings import settings
from redis.asyncio import Redis


class RedisClient:
    def __init__(self) -> None:
        self.url = settings.redis.REDIS_URL
        self.redis_connection: Redis | None = None

    async def get_redis_client(self) -> Redis:
        if self.redis_connection is None:
            self.redis_connection = Redis.from_url(
                self.url, decode_responses=True, encoding="utf-8"
            )
        return self.redis_connection

    async def close_redis_client(self) -> None:
        if self.redis_connection is not None:
            await self.redis_connection.close()
