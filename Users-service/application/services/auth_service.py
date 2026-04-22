import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Response

from application.configs.settings import settings
from application.core.schemas.roles import ALL_ROLES, AccessRights
from application.core.schemas.users import (
    AccessToken,
    TokenResponse,
    UserCreate,
    UserRead,
)
from application.exceptions.exceptions import (
    EntityNotFoundError,
    InvalidPasswordError,
    LogoutUserFailedError,
    RedisConnectionError,
    RefreshTokenExpiredError,
    RefreshUserTokensFailedError,
    RegistrationFailedError,
    RepositoryInternalError,
    RevokeTokenFailedError,
    UserAlreadyExistsError,
    UserInactiveError,
    ValidateAuthUserFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.redis_client import get_redis_client
from application.infrastructure.security import (
    check_password,
    create_access_token,
    hash_password,
    hash_token,
)
from application.infrastructure.security import (
    create_refresh_token as gen_refresh_token,
)
from application.infrastructure.time_decorator import (
    async_timed_report,
    time_all_methods,
)
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from application.web.views.v1.deps import clear_cookie_with_tokens, set_tokens_cookie


@time_all_methods(async_timed_report())
class AuthService:
    async def _get_user_by_user_id(self, user_id: int) -> User:
        try:
            user = await UsersRepo.select_user_by_user_id(user_id)
            if not user.is_active:
                logger.warning(f"[AuthService] Пользователь ID={user_id} неактивен")
                raise UserInactiveError()
            return user
        except (EntityNotFoundError, UserInactiveError):
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка получения пользователя ID={user_id}: {e}"
            )
            raise RepositoryInternalError("Failed to get user by id") from e

    async def _get_user_by_login(self, login: str) -> User:
        try:
            user = await UsersRepo.select_user_by_username(login)
            if not user.is_active:
                logger.warning(f"[AuthService] Пользователь {login!r} неактивен")
                raise UserInactiveError()
            return user
        except (EntityNotFoundError, UserInactiveError):
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка получения пользователя {login!r}: {e}"
            )
            raise RepositoryInternalError("Failed to get user by login") from e

    async def _get_valid_token(self, raw_token: str) -> RefreshToken:
        token_prefix = raw_token[:8]
        try:
            token_hash = hash_token(raw_token)
            stored = await RefreshTokensRepo.get_refresh_token(token_hash)

            if not stored or stored.revoked:
                logger.warning(
                    f"[AuthService] Токен {token_prefix}... отозван или не найден"
                )
                raise EntityNotFoundError(detail="Refresh token not found")

            if stored.expires_at <= datetime.now(timezone.utc):
                await RefreshTokensRepo.delete_refresh_token(stored)
                logger.warning(f"[AuthService] Токен {token_prefix}... истёк")
                raise RefreshTokenExpiredError()

            return stored
        except (EntityNotFoundError, RefreshTokenExpiredError):
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка валидации токена {token_prefix}...: {e}"
            )
            raise RepositoryInternalError("Failed to validate refresh token") from e

    async def _issue_tokens(
        self, user_id: int, user_role: str
    ) -> tuple[AccessToken, str]:
        try:
            access_token = create_access_token(user_id=user_id, user_role=user_role)
            refresh_token_raw, refresh_hash = gen_refresh_token()

            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt.refresh_token_expire_days
            )
            await RefreshTokensRepo.create_refresh_token(
                user_id, refresh_hash, expires_at
            )
            logger.info(f"[AuthService] Токены выданы для user_id={user_id}")
            return access_token, refresh_token_raw
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка выдачи токенов для user_id={user_id}: {e}"
            )
            raise RepositoryInternalError("Failed to issue tokens") from e

    async def authenticate_user(
        self, response: Response, login: str, password: str
    ) -> TokenResponse:
        logger.info(f"[AuthService] Аутентификация пользователя {login!r}")
        try:
            user_db = await self._get_user_by_login(login=login)

            if not check_password(
                password=password, hashed_password=user_db.hashed_password
            ):
                logger.warning(f"[AuthService] Неверный пароль для {login!r}")
                raise InvalidPasswordError()

            user = UserRead(
                id=user_db.id,
                username=user_db.username,
                is_active=user_db.is_active,
                role=user_db.role,
                avatar=user_db.avatar,
            )

            access_token, refresh_token = await self._issue_tokens(
                user_id=user.id, user_role=user.role
            )
            set_tokens_cookie(
                response=response,
                access_token=access_token.token,
                refresh_token=refresh_token,
            )

            logger.info(
                f"[AuthService] Пользователь {login!r} (ID={user.id}) аутентифицирован"
            )
            return TokenResponse(
                access_token=access_token.token,
                access_expire=access_token.expire,
                refresh_token=refresh_token,
            )
        except (EntityNotFoundError, InvalidPasswordError, UserInactiveError):
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Неожиданная ошибка аутентификации {login!r}: {e}"
            )
            raise ValidateAuthUserFailedError() from e

    async def register_user_to_db(
        self, payload: UserCreate
    ) -> dict[str, str | UUID | None]:
        logger.info(f"[AuthService] Регистрация пользователя {payload.username!r}")
        try:
            hashed_password = hash_password(payload.password)

            created_user = await UsersRepo.create_user(
                username=payload.username,
                hashed_password=hashed_password,
                avatar=payload.avatar,
                profile=payload.profile,
            )
            if not created_user:
                raise RegistrationFailedError(
                    "User registration failed: no user returned"
                )

            logger.info(
                f"[AuthService] Пользователь {payload.username!r} зарегистрирован: "
                f"ID={created_user.id}, роль={created_user.role}, аватар={created_user.avatar}"
            )
            return {
                "user_id": str(created_user.id),
                "new_username": created_user.username,
                "role": created_user.role,
                "avatar_uuid": created_user.avatar,
            }
        except (UserAlreadyExistsError, RepositoryInternalError):
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка регистрации {payload.username!r}: {e}"
            )
            raise RegistrationFailedError(
                f"Internal error during registration: {e}"
            ) from e

    async def revoke_token(self, jti: str, expire: int) -> None:
        logger.debug(f"[AuthService] Отзыв токена JTI={jti!r}")
        try:
            redis_conn = await get_redis_client()
            if not redis_conn:
                raise RedisConnectionError()
            await redis_conn.setex(f"revoked:{jti}", expire, "1")
            logger.info(f"[AuthService] Токен JTI={jti!r} отозван")
        except RedisConnectionError:
            raise
        except Exception as e:
            logger.exception(f"[AuthService] Ошибка отзыва токена JTI={jti!r}: {e}")
            raise RevokeTokenFailedError("Failed to revoke token") from e

    async def loggout_user_logic(
        self, response: Response, access_jti: str, user_id: int
    ) -> None:
        logger.info(f"[AuthService] Выход пользователя ID={user_id}")
        try:
            redis_conn = await get_redis_client()
            if not redis_conn:
                raise RedisConnectionError()

            clear_cookie_with_tokens(response)
            ttl = settings.jwt.access_token_expire_minutes * 60
            await redis_conn.setex(f"blacklist:access:{access_jti}", ttl, "1")
            await RefreshTokensRepo.invalidate_all_refresh_tokens(user_id)
            logger.info(f"[AuthService] Пользователь ID={user_id} вышел из системы")
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка выхода пользователя ID={user_id}: {e}"
            )
            raise LogoutUserFailedError() from e

    async def refresh(self, response: Response, raw_token: str) -> TokenResponse:
        logger.info("[AuthService] Обновление токенов")
        try:
            stored = await self._get_valid_token(raw_token)
            user = await self._get_user_by_user_id(stored.user_id)
            await RefreshTokensRepo.delete_refresh_token(stored)

            access_token, refresh_token = await self._issue_tokens(
                user_id=user.id, user_role=user.role
            )
            set_tokens_cookie(
                response=response,
                access_token=access_token.token,
                refresh_token=refresh_token,
            )

            logger.info(f"[AuthService] Токены обновлены для user_id={user.id}")
            return TokenResponse(
                access_token=access_token.token,
                access_expire=access_token.expire,
                refresh_token=refresh_token,
            )
        except (EntityNotFoundError, RefreshTokenExpiredError):
            raise
        except Exception as e:
            logger.exception(f"[AuthService] Ошибка обновления токенов: {e}")
            raise RefreshUserTokensFailedError() from e

    async def get_role_rights(self, role: str) -> AccessRights:
        role_obj = ALL_ROLES.get(role)
        if not role_obj:
            logger.warning(f"[AuthService] Роль {role!r} не найдена")
            raise EntityNotFoundError(detail="User role not found")
        return role_obj.rights


if __name__ == "__main__":

    async def test_get_role_rights():
        service = AuthService()
        print(await service.get_role_rights("admin"))

    asyncio.run(test_get_role_rights())
