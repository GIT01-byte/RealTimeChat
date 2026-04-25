from application.core.schemas.users import (
    RefreshTokensUCInputDTO,
    TokenResponse,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    RefreshUserTokensFailedError,
)
from application.infrastructure.logging import logger
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.services.cookie_service import CookieService
from application.services.tokens_service import TokensService
from application.services.users_service import UsersService
from fastapi import Response


class RefreshTokensUseCase:
    def __init__(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        tokens_service: TokensService,
        users_service: UsersService,
        cookie_service: CookieService,
        commiter: Commiter,
    ) -> None:
        self.refresh_tokens_repo = refresh_tokens_repo
        self.tokens_service = tokens_service
        self.users_service = users_service
        self.cookie_service = cookie_service
        self.commiter = commiter

    async def execute(
        self,
        data: RefreshTokensUCInputDTO,
        response: Response,
    ) -> TokenResponse:
        logger.info("[AuthService] Обновление токенов")
        try:
            stored = await self.tokens_service.get_valid_token(data.raw_token)
            user = await self.users_service.get_user_by_user_id(stored.user_id)

            await self.refresh_tokens_repo.delete_refresh_token(stored)

            access_token, refresh_token = await self.tokens_service.issue_tokens(
                user_id=user.id, user_role=user.role
            )
            self.cookie_service.set_tokens_cookie(
                response=response,
                access_token=access_token.token,
                refresh_token=refresh_token,
            )

            await self.commiter.commit()

            logger.info(f"[AuthService] Токены обновлены для user_id={user.id}")

            return TokenResponse(
                access_token=access_token.token,
                access_expire=access_token.expire,
                refresh_token=refresh_token,
            )
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(f"[AuthService] Ошибка обновления токенов: {e}")
            raise RefreshUserTokensFailedError() from e
