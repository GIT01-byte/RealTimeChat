import json
from uuid import UUID

from application.configs.settings import settings
from application.core.schemas.users import (
    RegisterUserUseCaseInput,
    UserCreate,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    LogoutUserFailedError,
    RedisConnectionError,
    RegistrationFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.redis_client import get_redis_client
from application.infrastructure.security import (
    ACCESS_TOKEN_TYPE,
    decode_access_token,
    hash_password,
)
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from application.web.views.v1.deps import clear_cookie_with_tokens
from fastapi import Response


class RegisterUserUseCase:
    def __init__(
        self,
        users_repo: UsersRepo,
        refresh_tokens_repo: RefreshTokensRepo,
        commiter: Commiter,
    ) -> None:
        self.users_repo = users_repo
        self.refresh_tokens_repo = refresh_tokens_repo
        self.commiter = commiter

    async def execute(self, data: RegisterUserUseCaseInput):
        try:
            # 1. Проверка на текущего пользователя
            current_user_token = data.request.cookies.get(ACCESS_TOKEN_TYPE)
            if current_user_token:
                try:
                    payload = decode_access_token(current_user_token)

                    # Извлечение данных из токена
                    if payload.jti and payload.sub:
                        user_id = int(payload.sub)
                        logger.info(
                            f"Авто-выход пользователя {user_id} перед новой регистрацией"
                        )

                        await self._loggout_user(
                            response=data.response,
                            access_jti=payload.jti,
                            user_id=user_id,
                        )
                except (ValueError, TypeError, Exception) as e:
                    logger.warning(f"Не удалось выполнить авто-выход: {e}")
                    pass
            # 1. Подготавливаем данные для БД
            profile_dict = None
            if data.profile:
                try:
                    profile_dict = json.loads(data.profile)
                except json.JSONDecodeError:
                    logger.warning(f"Некорректный JSON в profile: {data.profile}")
                    profile_dict = None
            payload = UserCreate(
                username=data.username,
                profile=profile_dict,
                avatar=str(data.avatar_uuid),
                password=data.password,
            )

            # 2. Региструрем пользователя
            new_user = await self._register_user_to_db(payload=payload)

            return RegisterUserUseCaseOutput()

        except BaseAPIException:
            raise
        except Exception:
            ...

    async def _register_user_to_db(
        self, payload: UserCreate
    ) -> dict[str, str | UUID | None]:
        logger.info(f"[AuthService] Регистрация пользователя {payload.username!r}")
        try:
            hashed_password = hash_password(payload.password)

            created_user = await self.users_repo.create_user(
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
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка регистрации {payload.username!r}: {e}"
            )
            raise RegistrationFailedError(
                f"Internal error during registration: {e}"
            ) from e

    async def _loggout_user(
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
            await self.refresh_tokens_repo.invalidate_all_refresh_tokens(user_id)
            logger.info(f"[AuthService] Пользователь ID={user_id} вышел из системы")
        except Exception as e:
            logger.exception(
                f"[AuthService] Ошибка выхода пользователя ID={user_id}: {e}"
            )
            raise LogoutUserFailedError() from e
