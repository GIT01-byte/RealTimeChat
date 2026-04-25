from datetime import datetime, timedelta, timezone

from application.configs.settings import settings
from application.core.schemas.users import (
    AccessToken,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EntityNotFoundError,
    LogoutUserFailedError,
    RefreshTokenExpiredError,
    RepositoryInternalError,
)
from application.infrastructure.logging import logger
from application.infrastructure.security import (
    create_access_token,
    hash_token,
)
from application.infrastructure.security import (
    create_refresh_token as gen_refresh_token,
)
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.users import RefreshToken
from application.repositories.refresh_tokens_repo import RefreshTokensRepo


class TokensService:
    def __init__(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        commiter: Commiter,
    ) -> None:
        self.refresh_tokens_repo = refresh_tokens_repo
        self.commiter = commiter

    async def issue_tokens(
        self, user_id: int, user_role: str
    ) -> tuple[AccessToken, str]:
        try:
            access_token = create_access_token(user_id=user_id, user_role=user_role)
            refresh_token_raw, refresh_hash = gen_refresh_token()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt.refresh_token_expire_days
            )

            await self.refresh_tokens_repo.create_refresh_token(
                user_id, refresh_hash, expires_at
            )
            await self.commiter.commit()
            logger.info(f"[AuthService] Токены выданы для user_id={user_id}")

            return access_token, refresh_token_raw
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(
                f"[AuthService] Ошибка выдачи токенов для user_id={user_id}: {e}"
            )
            raise RepositoryInternalError("Failed to issue tokens") from e

    async def get_valid_token(self, raw_token: str) -> RefreshToken:
        token_prefix = raw_token[:8]
        try:
            token_hash = hash_token(raw_token)
            stored = await self.refresh_tokens_repo.get_refresh_token(token_hash)

            if not stored or stored.revoked:
                logger.warning(
                    f"[AuthService] Токен {token_prefix}... отозван или не найден"
                )
                raise EntityNotFoundError(detail="Refresh token not found")

            if stored.expires_at <= datetime.now(timezone.utc):
                await self.refresh_tokens_repo.delete_refresh_token(stored)
                logger.warning(f"[AuthService] Токен {token_prefix}... истёк")
                raise RefreshTokenExpiredError()

            return stored
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка валидации токена {token_prefix}...: {e}"
            )
            raise RepositoryInternalError("Failed to validate refresh token") from e

    async def invalidate_all_refresh_tokens(self, user_id: int) -> None:
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
