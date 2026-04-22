from dishka import make_async_container

from application.di.providers.auth_api import AuthProvider
from application.di.providers.databases import DatabaseProvider
from application.di.providers.repositories import RepositoryProvider

app_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    AuthProvider(),
)
