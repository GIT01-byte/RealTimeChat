from application.infrastructure.redis_client import RedisClient


class RedisService:
    def __init__(self, redis_client: RedisClient):
        self._redis = redis_client.get_redis_client()

    def set_value(self, key: str, value: str, expire_seconds: int = 0) -> None:
        self._redis.set(key, value, ex=expire_seconds)

    def get_value(self, key: str) -> str | None:
        return self._redis.get(key)  # type: ignore

    def delete_value(self, key: str) -> None:
        self._redis.delete(key)
