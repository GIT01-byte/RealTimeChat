import os
import sys

# Добавляем корневую директорию проекта в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from uuid import UUID
import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Response, UploadFile

from core.settings import settings
from core.db.repositories import AvatarFilesRepo, UsersRepo, RefreshTokensRepo
from core.models.users import RefreshToken, User
from core.schemas.users import TokenResponse, UserRead
from core.app_redis.client import get_redis_client
from core.schemas.users import AccessToken

from exceptions.exceptions import (
    EntityNotFoundError,
    FilesUploadError,
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

from utils.security import (
    check_password,
    create_access_token,
    create_refresh_token as gen_refresh_token,
    hash_password,
    hash_token,
)
from utils.logging import logger
from utils.time_decorator import time_all_methods, async_timed_report

from api.auth_deps import (
    clear_cookie_with_tokens,
    set_tokens_cookie,
)

from integrations.files.schemas import NSFileUploadRequest, NSFileUploadResponse
from integrations.files.files import (
    MS_upload_file,
)
from integrations.files.constants import USERS_AVATAR_NAME

from services.roles import ALL_ROLES, AccessRights


@time_all_methods(async_timed_report())
class AuthService:
    async def _get_user_by_user_id(self, user_id: int) -> User:
        """
        Приватный вспомогательный метод для получения пользователя из базы данных
        по user_id с проверкой его статуса активности.

        Params:
            user_id(int): ID пользователя

        Returns:
            User: Пользователь, соответствующий переданному id.

        Raises:
            UserNotFoundError: Если пользователь с указанным логином не найден.
            UserInactiveError: Если пользователь с данным логином неактивен.
        """
        try:
            # Получение пользователя из БД
            user = await UsersRepo.select_user_by_user_id(user_id)
            if not user:
                logger.warning(f"Пользователь ID {user_id} не найден")
                raise EntityNotFoundError(detail="User not found")

            # Проверка статуса активности
            if not user.is_active:
                logger.warning(f"Пользователь ID {user_id} неактивен")
                raise UserInactiveError()

            logger.debug(f"Пользователь ID {user_id} найден и активен")
            return user
        except EntityNotFoundError:
            logger.warning(f"Пользователь ID {user_id} не найден")
            raise EntityNotFoundError(detail="User not found")

    async def _get_user_by_login(self, login: str) -> User:
        """
        Приватный вспомогательный метод для получения пользователя из базы данных
        по логину с проверкой его статуса активности.

        Args:
            login(str): Строка, содержащая логин пользователя.

        Returns:
            User: Пользователь, соответствующий переданному логину.

        Raises:
            UserNotFoundError: Если пользователь с указанным логином не найден.
            UserInactiveError: Если пользователь с данным логином неактивен.
        """
        try:
            # Получение пользователя из БД
            user = await UsersRepo.select_user_by_username(login)
            if not user:
                logger.warning(f"Пользователь {login!r} не найден")
                raise EntityNotFoundError(detail="User not found")

            if not user.is_active:
                logger.warning(f"Пользователь {login!r} неактивен")
                raise UserInactiveError()

            logger.debug(f"Пользователь {login!r} найден и активен")
            return user
        except EntityNotFoundError:
            logger.warning(f"Пользователь {login!r} не найден")
            raise EntityNotFoundError(detail="User not found")

    async def _get_valid_token(self, raw_token: str) -> RefreshToken:
        """
        Приватный вспомогательный метод для проверки валидности токена
        путем сравнения хэша с сохраненным значением.

        Params:
            raw_token(str): Строка, представляющая исходный токен.

        Returns:
            RefreshToken: Объект токена, если токен действителен и не истек срок его действия.

        Raises:
            RefreshTokenNotFoundError: если токен не найден в хранилище.
            RefreshTokenExpiredError: если токен устарел.
        """
        try:
            # Хэшируем токен
            token_hash = hash_token(raw_token)

            # Получаем токен из репозитория
            stored = await RefreshTokensRepo.get_refresh_token(token_hash)

            # Проверка на отзыв
            if not stored or stored.revoked:
                logger.warning(f"Токен {raw_token[:8]}... отозван")
                raise EntityNotFoundError(detail="Refresh token not found")

            # Проверка срока действия
            now = datetime.now(timezone.utc)
            if stored.expires_at <= now:
                await RefreshTokensRepo.delete_refresh_token(stored)
                logger.warning(f"Токен {raw_token[:8]}... истек")
                raise RefreshTokenExpiredError()

            logger.debug(f"Токен {raw_token[:8]}... валиден")
            return stored
        except EntityNotFoundError:
            logger.warning(f"Токен {raw_token[:8]}... не найден")
            raise EntityNotFoundError(detail="Refresh token not found")

    async def _issue_tokens(
        self, user_id: int, user_role: str
    ) -> tuple[AccessToken, str]:
        """
        Приватный вспомогательный метод для генерации Access и Refresh токенов,
        а также для сохранения хэша Refresh токена в базе данных.

        Params:
            user_id(int): ID пользователя, для которого генерируются токены.

        Returns:
            tuple: Кортеж из Access токена (str) и "сырого" Refresh токена (str)

        Raises:
            RepositoryInternalError: Если произошла ошибка при сохранении Refresh токена в БД.
        """
        logger.debug(f"Начало создания токенов для пользователя ID: {user_id}.")

        # 1. Создание Access токена
        access_token = create_access_token(user_id=user_id, user_role=user_role)

        # 2. Создание Refresh токена и его хэша
        refresh_token_raw, refresh_hash = gen_refresh_token()
        logger.debug(
            f"Refresh токен (hash: {refresh_hash[:8]}...) сгенерирован для пользователя ID: {user_id}."
        )

        # 3. Сохранение Refresh токена в БД
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.refresh_token_expire_days
        )
        logger.debug(f"Refresh токен истекает в: {expires_at.isoformat()}.")

        try:
            await RefreshTokensRepo.create_refresh_token(
                user_id, refresh_hash, expires_at
            )
            logger.info(f"Refresh токен сохранен для пользователя ID: {user_id}")
        except Exception as e:
            logger.exception(
                f"Ошибка сохранения Refresh токена для пользователя ID: {user_id}"
            )
            raise RepositoryInternalError(
                "Failed to save refresh token to database"
            ) from e

        return access_token, refresh_token_raw

    async def authenticate_user(
        self, response: Response, login: str, password: str
    ) -> TokenResponse:
        """
        Аутентифицирует пользователя, проверяя учетные данные и активность
        Если аутентификация успешна, генерирует токены (access и refresh)
        вставляет hash refresh в БД и устанавливает их в HTTP-куки

        Params:
            response(Response): Объект Response FastAPI для установки куки
            login(str): Логин пользователя (username)
            password(str): Пароль пользователя

        Returns:
            TokenResponse: Словарь с информацией о пользователе и сгенерированными токенами

        Raises:
            UserNotFoundError: Если пользователь с указанным логином не найден
            InvalidPasswordError: Если предоставленный пароль неверен
            UserInactiveError: Если пользователь неактивен
            RepositoryInternalError: Если произошла внутренняя ошибка сервера
                                    во время операций с БД или Redis
        """
        logger.info(f"Аутентификация пользователя {login!r}")
        try:
            # 1. Получение пользователя из БД и проверка на активность
            user_data_from_db = await self._get_user_by_login(login=login)

            # 2. Проверка пароля
            if not check_password(
                password=password, hashed_password=user_data_from_db.hashed_password
            ):
                logger.warning(f"Неверный пароль для {login!r}")
                raise InvalidPasswordError()

            # 3. Преобразование данных пользователя в Pydantic модель
            user = UserRead(
                id=user_data_from_db.id,
                username=user_data_from_db.username,
                email=user_data_from_db.email,  # type: ignore
                is_active=user_data_from_db.is_active,
                role=user_data_from_db.role,
            )

            # 4. Генерация токенов и сохранение Refresh токена в БД
            access_token, refresh_token = await self._issue_tokens(
                user_id=user.id, user_role=user.role
            )

            # 5. Установка токенов в куки
            set_tokens_cookie(
                response=response,
                access_token=access_token.token,
                refresh_token=refresh_token,
            )

            logger.info(f"Пользователь {user.username!r} аутентифицирован")
            return TokenResponse(
                access_token=access_token.token,
                access_expire=access_token.expire,
                refresh_token=refresh_token,
            )

        except (EntityNotFoundError, InvalidPasswordError, UserInactiveError):
            raise
        except Exception as e:
            logger.exception(f"Ошибка аутентификации {login!r}")
            raise ValidateAuthUserFailedError() from e

    async def _upload_avatar(self, file: UploadFile, entity_id: int) -> NSFileUploadResponse:
        """
        Загружает аватар в S3 через Media Service
        
        Args:
            file: Файл аватара для загрузки
            entity_id: ID пользователя
            
        Returns:
            NSFileUploadResponse: Ответ с метаданными загруженного файла
            
        Raises:
            FilesUploadError: Ошибка загрузки файла в S3
        """
        logger.info(f"Загрузка аватара {file.filename!r} для user_id: {entity_id}")
        try:
            request = NSFileUploadRequest(
                upload_context=USERS_AVATAR_NAME, file=file, entity_id=entity_id
            )
            response = await MS_upload_file(request)
            if not response:
                logger.error(f"Пустой ответ при загрузке {file.filename!r}")
                raise FilesUploadError(f"No response for {file.filename}")
            logger.info(f"Аватар {file.filename!r} успешно загружен в S3, UUID: {response.uuid}")
            return response
        except (HTTPException, FilesUploadError):
            raise
        except Exception as e:
            logger.exception(f"Неожиданная ошибка загрузки аватара {file.filename!r}: {e}")
            raise FilesUploadError from e

    async def _save_file_to_db(
        self, user_id: int, file_data: NSFileUploadResponse
    ) -> UUID:
        """
        Сохраняет метаданные аватара в базу данных
        
        Args:
            user_id: ID пользователя
            file_data: Метаданные загруженного файла
            
        Returns:
            UUID: Уникальный идентификатор сохраненного аватара
            
        Raises:
            RepositoryInternalError: Ошибка сохранения в БД
        """
        logger.debug(f"Сохранение метаданных аватара {file_data.uuid} для user_id: {user_id}")
        try:
            result = await AvatarFilesRepo.create_avatar(
                user_id=user_id, file_data=file_data
            )
            if not result:
                logger.error(f"Не удалось сохранить аватар {file_data.uuid} в БД")
                raise RepositoryInternalError(f"Failed to save avatar file {file_data.uuid}")

            logger.info(f"Метаданные аватара {file_data.uuid} сохранены в БД")
            return result.uuid
        except RepositoryInternalError:
            raise
        except Exception as e:
            logger.exception(f"Неожиданная ошибка сохранения аватара {file_data.uuid}: {e}")
            raise RepositoryInternalError from e

    async def register_user_to_db(
        self, payload: dict, password: str, avatar_file: UploadFile | None = None
    ) -> dict[str, str | UUID | None]:
        """
        Регистрирует нового пользователя в базе данных с опциональным аватаром
        Хеширует пароль перед сохранением

        Args:
            payload: Словарь с данными пользователя (username, email, profile)
            password: Пароль пользователя в открытом виде
            avatar_file: Опциональный файл аватара

        Returns:
            dict: Словарь с user_id, new_username, role, avatar_uuid

        Raises:
            UserAlreadyExistsError: Пользователь с таким username или email уже существует
            RegistrationFailedError: Ошибка при регистрации
            FilesUploadError: Ошибка загрузки аватара
        """
        username = payload.get("username", "N/A")
        email = payload.get("email", "N/A")
        logger.info(f"Начало регистрации пользователя {username!r}, email: {email!r}")
        try:
            # 1. Хеширование пароля и создание пользователя
            logger.debug(f"Хеширование пароля для {username!r}")
            hashed_password = hash_password(password)
            full_payload = {**payload, "hashed_password": hashed_password}
            
            logger.debug(f"Создание пользователя {username!r} в БД")
            created_user_in_db = await UsersRepo.create_user(full_payload)

            if not created_user_in_db:
                logger.error(f"UsersRepo.create_user вернул None для {username!r}")
                raise RegistrationFailedError(
                    "User registration failed: no user returned"
                )

            logger.info(f"Пользователь {username!r} создан в БД, ID: {created_user_in_db.id}")

            # 2. Обработка аватара (если есть)
            avatar_uuid = None
            if avatar_file:
                logger.info(f"Обработка аватара {avatar_file.filename!r} для {username!r}")
                try:
                    # Загружаем в S3
                    upload_response = await self._upload_avatar(
                        file=avatar_file, entity_id=int(created_user_in_db.id)
                    )
                    if not upload_response:
                        logger.error(f"Пустой ответ при загрузке аватара {avatar_file.filename!r}")
                        raise FilesUploadError(
                            f"No upload response for {avatar_file.filename}"
                        )

                    # Сохраняем в БД
                    file_uuid = await self._save_file_to_db(
                        user_id=int(created_user_in_db.id), file_data=upload_response
                    )
                    if not file_uuid:
                        logger.error(f"Не получен UUID для аватара {avatar_file.filename!r}")
                        raise RepositoryInternalError(
                            f"No UUID returned for {avatar_file.filename}"
                        )

                    avatar_uuid = file_uuid
                    logger.info(
                        f"Аватар {avatar_file.filename!r} успешно обработан, UUID: {avatar_uuid}"
                    )
                except (FilesUploadError, RepositoryInternalError) as e:
                    logger.error(f"Ошибка обработки аватара для {username!r}: {e}")
                    raise
            else:
                logger.debug(f"Аватар не предоставлен для {username!r}")

            logger.info(
                f"Регистрация {username!r} завершена успешно, роль: {created_user_in_db.role}, аватар: {avatar_uuid or 'нет'}"
            )
            return {
                "user_id": str(created_user_in_db.id),
                "new_username": created_user_in_db.username,
                "role": created_user_in_db.role,
                "avatar_uuid": avatar_uuid,
            }

        except (UserAlreadyExistsError, FilesUploadError, RepositoryInternalError):
            raise
        except Exception as e:
            logger.exception(f"Неожиданная ошибка регистрации {username!r}: {e}")
            raise RegistrationFailedError(
                f"Internal error during registration: {e}"
            ) from e

    async def revoke_token(self, jti: str, expire: int):
        """
        Отзывает токен, добавляя его идентификатор (jti) в черный список Redis
        Токен считается отозванным, если его jti присутствует в Redis

        Params:
            jti: Уникальный идентификатор токена (JWT ID)
            expire: Время жизни записи в Redis в секундах (должно соответствовать
                    времени жизни самого токена для надежности)
        """
        logger.debug(f"Отзыв токена JTI: {jti!r}")
        try:
            redis_conn = await get_redis_client()
            if not redis_conn:
                logger.error("Ошибка подключения к Redis")
                raise RedisConnectionError()

            await redis_conn.setex(f"revoked:{jti}", expire, "1")
            logger.info(f"Токен JTI: {jti!r} отозван")

        except RedisConnectionError:
            raise
        except Exception as e:
            logger.exception(f"Ошибка отзыва токена JTI: {jti!r}")
            raise RevokeTokenFailedError(
                "Failed to revoke token due to internal error"
            ) from e

    async def loggout_user_logic(
        self, response: Response, access_jti: str, user_id: int
    ):
        """
        Процедура выхода текущего пользователя из системы

        Params:
            response(Response): Объект Response FastAPI
            access_jti(str): Строка уникального индефикатора access токена
            user_id(int): ID текущего пользвателя
        Raises:
            LogoutUserFailedError: Если процедура выхода завершилась неудачно
        """
        logger.info("Логаут пользователя")
        try:
            redis_conn = await get_redis_client()
            if not redis_conn:
                logger.error("Ошибка подключения к Redis")
                raise RedisConnectionError()

            clear_cookie_with_tokens(response)
            ttl = settings.jwt.access_token_expire_minutes * 60
            await redis_conn.setex(f"blacklist:access:{access_jti}", ttl, "1")
            await RefreshTokensRepo.invalidate_all_refresh_tokens(user_id)
            logger.info(f"Пользователь ID {user_id} вышел из системы")

        except Exception as ex:
            logger.exception(f"Ошибка выхода пользователя ID {user_id}: {ex}")
            raise LogoutUserFailedError()

    async def refresh(self, response: Response, raw_token: str) -> TokenResponse:
        """
        Процедура обновления токенов аутентификации пользователя.

        Params:
            response(Response): Объект Response FastAPI
            raw_token(str): Строка токена

        Returns:
            TokenResponse: Объект-парой с новыми токенами

        Raises:
            RefreshTokenNotRequiredError: Если токен не найден
        """
        try:
            logger.info("Обновление токенов")
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

            logger.info(f"Токены обновлены для пользователя ID: {user.id}")
            return TokenResponse(
                access_token=access_token.token,
                access_expire=access_token.expire,
                refresh_token=refresh_token,
            )
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.exception("Ошибка обновления токенов")
            raise RefreshUserTokensFailedError()

    async def get_role_rights(self, role: str) -> AccessRights:
        """
        Возвращает список прав для указанной роли пользователя.

        Params:
            role(str): Роль пользователя

        Returns:
            list[str]: Список прав для указанной роли
        """
        role_obj = ALL_ROLES.get(role, None)
        if not role_obj:
            logger.warning(f"Роль {role!r} не найдена")
            raise EntityNotFoundError(detail="User role not found")
        logger.debug(f"Права роли {role!r} получены")
        return role_obj.rights


if __name__ == "__main__":

    async def test_get_role_rights():
        service = AuthService()
        role_rights = await service.get_role_rights("admin")  # Example usage
        print(role_rights)

    asyncio.run(test_get_role_rights())
