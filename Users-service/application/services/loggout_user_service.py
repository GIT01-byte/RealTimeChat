from application.configs.settings import settings
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    LogoutUserFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.redis_client import RedisClient
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.web.views.v1.deps import clear_cookie_with_tokens
from fastapi import Response


class LoggoutUserService:
    def __init__(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        redis_client: RedisClient,
        commiter: Commiter,
    ) -> None:
        self.refresh_tokens_repo = refresh_tokens_repo
        self.redis_client = redis_client
        self.commiter = commiter

    async def loggout_user(
        self, response: Response, access_jti: str, user_id: int
    ) -> None:
        logger.info(f"[AuthService] Выход пользователя ID={user_id}")
        try:
            # 1. Очищение кук
            clear_cookie_with_tokens(response)

            # 2. Установка Redis blacklist
            await self._set_redis_blacklist(access_jti)

            # 3. Инвалидация всех refresh токенов
            await self._invalidate_all_refresh_tokens(user_id)

            logger.info(f"[AuthService] Пользователь ID={user_id} вышел из системы")
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка выхода пользователя ID={user_id}: {e}"
            )
            raise LogoutUserFailedError() from e

    async def _set_redis_blacklist(self, access_jti: str) -> None:
        try:
            redis_conn = await self.redis_client.get_redis_client()
            ttl = settings.jwt.access_token_expire_minutes * 60
            await redis_conn.setex(f"blacklist:access:{access_jti}", ttl, "1")
            logger.debug(f"Успешно установлен Redis blacklist: {access_jti}")
        except Exception as e:
            logger.exception(f"Failed to set Redis blacklist: {str(e)}")
            raise

    async def _invalidate_all_refresh_tokens(self, user_id: int) -> None:
        try:
            await self.refresh_tokens_repo.invalidate_all_refresh_tokens(user_id)
            await self.commiter.commit()
            logger.info(
                f"Успешно аннулированы все refresh токены для user_id: {user_id}"
            )
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(f"Ошибка инвалидации refresh токенов: {str(e)}")
            raise LogoutUserFailedError(
                detail=f"Failed to invalidate refresh tokens: {str(e)}"
            ) from e
