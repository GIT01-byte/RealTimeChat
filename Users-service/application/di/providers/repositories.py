from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_users_repo(self, session: AsyncSession) -> UsersRepo:
        return UsersRepo(session=session)

    @provide(scope=Scope.REQUEST)
    def get_refresh_tokens_repo(self, session: AsyncSession) -> RefreshTokensRepo:
        return RefreshTokensRepo(session=session)
