from application.di.providers.auth_api import AuthProvider
from application.di.providers.databases import DatabaseProvider
from application.di.providers.redis_client import RedisClientProvider
from application.di.providers.repositories import RepositoryProvider
from dishka import make_async_container

users_api_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    RedisClientProvider(),
    AuthProvider(),
)
