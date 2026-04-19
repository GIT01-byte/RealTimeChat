from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from application.repositories.files_outbox_repository import FilesOutboxRepository
from application.repositories.files_repository import FileRepository


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_outbox_message_repo(self, session: AsyncSession) -> FilesOutboxRepository:
        return FilesOutboxRepository(session=session)

    @provide(scope=Scope.REQUEST)
    def get_files_repo(self, session: AsyncSession) -> FileRepository:
        return FileRepository(session=session)
