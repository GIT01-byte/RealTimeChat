from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.database.commiter import Commiter
from application.repositories.database.connection import async_session


class DatabaseProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_db_session(self) -> AsyncIterator[AsyncSession]:
        async with async_session() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    async def commiter(self, session: AsyncSession) -> Commiter:
        return Commiter(session=session)
