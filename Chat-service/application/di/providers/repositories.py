from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.chat_messages_repo import ChatMessagesRepo
from application.repositories.chat_rooms_repo import ChatRoomsRepo


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_chat_rooms_repo(self, session: AsyncSession) -> ChatRoomsRepo:
        return ChatRoomsRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_chat_messages_repo(self, session: AsyncSession) -> ChatMessagesRepo:
        return ChatMessagesRepo(session=session)
