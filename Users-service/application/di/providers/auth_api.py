from application.core.use_cases.refresh_tokens import RefreshTokensUseCase
from application.core.use_cases.register_user import RegisterUserUseCase
from application.infrastructure.redis_client import RedisClient
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from application.services.cookie_service import CookieService
from application.services.redis_service import RedisService
from application.services.tokens_service import TokensService
from application.services.users_service import UsersService
from dishka import Provider, Scope, provide


class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def get_cookie_service(
        self,
    ) -> CookieService:
        return CookieService()

    @provide(scope=Scope.APP)
    def get_redis_service(
        self,
        redis_client: RedisClient,
    ) -> RedisService:
        return RedisService(
            redis_client=redis_client,
        )

    @provide(scope=Scope.REQUEST)
    def get_users_service(
        self,
        tokens_service: TokensService,
        redis_service: RedisService,
        users_repo: UsersRepo,
        cookie_service: CookieService,
        commiter: Commiter,
    ) -> UsersService:
        return UsersService(
            tokens_service=tokens_service,
            redis_service=redis_service,
            users_repo=users_repo,
            cookie_service=cookie_service,
            commiter=commiter,
        )

    @provide(scope=Scope.REQUEST)
    def get_tokens_service(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        commiter: Commiter,
    ) -> TokensService:
        return TokensService(
            refresh_tokens_repo=refresh_tokens_repo,
            commiter=commiter,
        )

    @provide(scope=Scope.REQUEST)
    def get_register_user_use_case(
        self,
        users_repo: UsersRepo,
        users_service: UsersService,
        commiter: Commiter,
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            users_repo=users_repo,
            users_service=users_service,
            commiter=commiter,
        )

    @provide(scope=Scope.REQUEST)
    def get_refresh_tokens_use_case(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        tokens_service: TokensService,
        users_service: UsersService,
        cookie_service: CookieService,
        commiter: Commiter,
    ) -> RefreshTokensUseCase:
        return RefreshTokensUseCase(
            refresh_tokens_repo=refresh_tokens_repo,
            tokens_service=tokens_service,
            users_service=users_service,
            cookie_service=cookie_service,
            commiter=commiter,
        )
