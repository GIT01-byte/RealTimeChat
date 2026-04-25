from application.core.schemas.users import UserRead, UserSelfInfo
from application.exceptions.exceptions import (
    AccessTokenRevokedError,
    InvalidTokenError,
    UserInactiveError,
    UserNotFoundError,
)
from application.infrastructure.logging import logger
from application.infrastructure.redis_client import RedisClient
from application.infrastructure.security import (
    decode_access_token,
)
from application.infrastructure.time_decorator import (
    async_timed_report,
)
from application.repositories.users_repo import UsersRepo
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login/")


@inject
@async_timed_report()
async def get_current_user_from_token(
    redis_client: FromDishka[RedisClient],
    users_repo: FromDishka[UsersRepo],
    token: str = Depends(oauth2_scheme),
) -> UserSelfInfo:
    """
    Возвращает текущего активного пользователя на основании JWT-токена.

    :param token: JWT-токен
    :param redis: Клиент Redis для хранения черных списков
    :raises InvalidTokenError: Если токен недействителен
    :raises AccessTokenRevokedError: Если токен аннулирован
    :raises UserNotFoundError: Если пользователь не найден
    :return: Словарь с данными текущего пользователя, jti (уникального ID JWT-токена), iat (время последнего входа в систему)
    """
    try:
        # Декодируем JWT-токен
        payload = decode_access_token(token)

        # Извлекаем данные из токена
        if not payload.sub or not payload.jti:
            raise InvalidTokenError("Missing required claims: sub or jti")

        # Проверка чёрного списка Redis
        redis_client = await redis_client.get_redis_client()
        if await redis_client.exists(f"blacklist:access:{payload.jti}"):
            raise AccessTokenRevokedError()

        # Запрашиваем пользователя из базы данных
        db_user = await users_repo.select_user_by_user_id(int(payload.sub))

        # Проверяем полученного user'а
        if not db_user:
            raise UserNotFoundError()

        return UserSelfInfo(
            jwt_payload=payload,
            user_db=UserRead.model_validate(db_user),
        )

    except PyJWTError as err:
        logger.error(f"Ошибка декодирования токена: {err}")
        raise InvalidTokenError()


@inject
@async_timed_report()
async def get_current_active_user(
    current_user: UserSelfInfo = Depends(get_current_user_from_token),
) -> UserSelfInfo:
    """
    Возвращает активного пользователя.

    :param current_user: Пользователь из зависимости get_current_user_from_token
    :raises UserInactiveError: Если пользователь неактивен
    :return: Активный пользователь
    """
    if current_user.user_db.is_active:
        return current_user
    raise UserInactiveError()
