from dishka import make_async_container

from application.di.providers.databases import DatabaseProvider
from application.di.providers.repositories import RepositoryProvider
from application.di.providers.chat_service import ChatServiceProvider


chat_api_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    ChatServiceProvider(),
)
