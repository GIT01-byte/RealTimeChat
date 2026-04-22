from application.infrastructure.redis_client import RedisClient
from dishka import Provider, Scope, provide


class RedisClientProvider(Provider):
    @provide(scope=Scope.APP)
    def get_redis_client(self) -> RedisClient:
        return RedisClient()
