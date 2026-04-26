from fastapi import Response

from application.configs.settings import settings
from application.core.schemas.roles import ALL_ROLES, AccessRights
from application.core.schemas.users import (
    TokenResponse,
    UserRead,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EntityNotFoundError,
    InvalidPasswordError,
    LogoutUserFailedError,
    RepositoryInternalError,
    UserInactiveError,
    ValidateAuthUserFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.security import (
    check_password,
)
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.users import User
from application.repositories.users_repo import UsersRepo
from application.services.cookie_service import CookieService
from application.services.redis_service import RedisService
from application.services.tokens_service import TokensService


class UsersService:
    def __init__(
        self,
        tokens_service: TokensService,
        redis_service: RedisService,
        cookie_service: CookieService,
        users_repo: UsersRepo,
        commiter: Commiter,
    ) -> None:
        self.tokens_service = tokens_service
        self.redis_service = redis_service
        self.cookie_service = cookie_service
        self.users_repo = users_repo
        self.commiter = commiter

    async def get_user_by_user_id(self, user_id: int) -> User:
        try:
            user = await self.users_repo.select_user_by_user_id(user_id)
            if not user.is_active:
                logger.warning(f"[AuthService] Пользователь ID={user_id} неактивен")
                raise UserInactiveError()
            return user
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка получения пользователя ID={user_id}: {e}"
            )
            raise RepositoryInternalError("Failed to get user by id") from e

    async def get_user_by_login(self, login: str) -> User:
        try:
            user = await self.users_repo.select_user_by_username(login)
            if not user.is_active:
                logger.warning(f"[AuthService] Пользователь {login!r} неактивен")
                raise UserInactiveError()
            return user
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка получения пользователя {login!r}: {e}"
            )
            raise RepositoryInternalError("Failed to get user by login") from e

    async def get_role_rights(self, role: str) -> AccessRights:
        role_obj = ALL_ROLES.get(role)
        if not role_obj:
            logger.warning(f"[AuthService] Роль {role!r} не найдена")
            raise EntityNotFoundError(detail="User role not found")
        return role_obj.rights

    async def loggout_user(
        self, response: Response, access_jti: str, user_id: int
    ) -> None:
        logger.info(f"[AuthService] Выход пользователя ID={user_id}")
        try:
            # 1. Очищение кук
            self.cookie_service.clear_cookie_with_tokens(response)

            # 2. Установка access в blacklist
            ttl = settings.jwt.access_token_expire_minutes * 60
            self.redis_service.set_value(f"blacklist:access:{access_jti}", "1", ttl)

            # 3. Инвалидация всех refresh токенов
            await self.tokens_service.invalidate_all_refresh_tokens(user_id)

            logger.info(f"[AuthService] Пользователь ID={user_id} вышел из системы")
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка выхода пользователя ID={user_id}: {e}"
            )
            raise LogoutUserFailedError() from e

    async def authenticate_user(
        self, response: Response, login: str, password: str
    ) -> TokenResponse:
        logger.info(f"[AuthService] Аутентификация пользователя {login!r}")
        try:
            user_db = await self.get_user_by_login(login=login)

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

            access_token, refresh_token = await self.tokens_service.issue_tokens(
                user_id=user.id, user_role=user.role
            )
            self.cookie_service.set_tokens_cookie(
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
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Неожиданная ошибка аутентификации {login!r}: {e}"
            )
            raise ValidateAuthUserFailedError() from e
