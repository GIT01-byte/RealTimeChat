import os
import sys
from uuid import UUID

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from typing import Optional
from datetime import datetime

from sqlalchemy import Sequence, or_, select, delete
from sqlalchemy.exc import SQLAlchemyError
from pydantic import EmailStr

from exceptions.exceptions import (
    UserAlreadyExistsError,
    EntityNotFoundError,
    RepositoryInternalError,
)

from core.db.db_manager import db_manager
from core.models.users import AvatarFiles, RefreshToken, User

from integrations.files.schemas import NSFileUploadResponse

from utils.logging import logger
from utils.time_decorator import time_all_methods, sync_timed_report, async_timed_report


@time_all_methods(async_timed_report())
class UsersRepo:
    @staticmethod
    async def create_user(payload: dict) -> Optional[User]:
        username = payload.get("username")
        email = payload.get("email")
        logger.debug(
            f"Попытка создания пользователя с именем: {username!r}, email: {email!r}"
        )
        try:
            async with db_manager.session_factory() as session:
                existing_user = await session.scalar(
                    select(User).filter(
                        or_(User.username == username, User.email == email)
                    )
                )
                if existing_user:
                    logger.warning(
                        f"Пользователь с именем: {username!r} или email: {email!r} уже существует"
                    )
                    raise UserAlreadyExistsError(
                        f"Пользователь с именем {username!r} или email {email!r} уже существует"
                    )

                new_user = User(**payload)
                session.add(new_user)

                await session.flush()
                await session.commit()
                await session.refresh(new_user)
                logger.info(
                    f"Пользователь ID:{new_user.id}, Роль: {new_user.role}, Имя: {new_user.username!r} успешно создан."
                )
                return new_user
        except UserAlreadyExistsError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании пользователя {username!r}")
            raise RepositoryInternalError(
                "Не удалось создать пользователя из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании пользователя {username!r}"
            )
            raise RepositoryInternalError(
                "Не удалось создать пользователя из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def select_user_by_user_id(user_id: int) -> User | None:
        logger.debug(f"Попытка выбрать пользователя по ID: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(select(User).where(User.id == user_id))
                if not user:
                    logger.debug(f"Пользователь с ID: {user_id} не найден.")
                    raise EntityNotFoundError(f"Пользователь с ID {user_id} не найден.")
                logger.debug(
                    f"Найден пользователь ID: {user_id}, имя: {user.username!r}, Роль: {user.role}"
                )
                return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при выборе пользователя по ID {user_id}")
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по ID из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при выборе пользователя по ID {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по ID из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def select_user_by_username(username: str) -> User | None:
        logger.debug(f"Попытка выбрать пользователя по имени: {username!r}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(
                    select(User).where(User.username == username)
                )
                if not user:
                    logger.debug(f"Пользователь с именем: {username!r} не найден.")
                    raise EntityNotFoundError(
                        f"Пользователь с именем {username!r} не найден."
                    )
                logger.debug(
                    f"Найден пользователь с именем: {username!r}, ID: {user.id}, Роль: {user.role}"
                )
                return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при выборе пользователя по имени {username!r}")
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по имени из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при выборе пользователя по имени {username!r}"
            )
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по имени из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def select_user_by_email(email: EmailStr) -> User | None:
        logger.debug(f"Попытка выбрать пользователя по email: {email!r}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(select(User).where(User.email == email))
                if not user:
                    logger.debug(f"Пользователь с email: {email!r} не найден.")
                    raise EntityNotFoundError(
                        f"Пользователь с email {email!r} не найден."
                    )
                logger.debug(
                    f"Найден пользователь с email: {email!r}, ID: {user.id}, Роль: {user.role}"
                )
                return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при выборе пользователя по email {email!r}")
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по email из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при выборе пользователя по email {email!r}"
            )
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по email из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_all_users():
        logger.debug("Попытка получить всех пользователей")
        try:
            async with db_manager.session_factory() as session:
                all_users = await session.scalars(select(User))
                users_list = all_users.all()
                logger.debug(f"Получено пользователей: {len(users_list)}")
                return users_list
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при получении всех пользователей")
            raise RepositoryInternalError(
                "Не удалось получить всех пользователей из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception("Неожиданная ошибка при получении всех пользователей")
            raise RepositoryInternalError(
                "Не удалось получить всех пользователей из-за неожиданной ошибки"
            ) from e


class RefreshTokensRepo:
    @staticmethod
    async def create_refresh_token(
        user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        logger.debug(f"Попытка создания refresh токена для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                token = RefreshToken(
                    user_id=user_id, token_hash=token_hash, expires_at=expires_at
                )
                session.add(token)
                await session.flush()
                await session.commit()
                await session.refresh(token)
                logger.info(
                    f"Refresh токен ID:{token.id} для user_id:{user_id} успешно создан."
                )
                return token
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при создании refresh токена для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось создать refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании refresh токена для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось создать refresh токен из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_refresh_token(token_hash: str) -> Optional[RefreshToken]:
        logger.debug(
            "Попытка получить refresh токен по хэшу (первые 8 символов): %s...",
            token_hash[:8],
        )
        try:
            async with db_manager.session_factory() as session:
                token = await session.scalar(
                    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
                )
                if not token:
                    logger.debug("Refresh токен по заданному хэшу не найден.")
                    raise EntityNotFoundError("Refresh токен не найден.")
                logger.debug(
                    f"Найден refresh токен ID:{token.id} для user_id:{token.user_id}."
                )
                return token
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при получении refresh токена (хэш: {token_hash[:8]}...)"
            )
            raise RepositoryInternalError(
                "Не удалось получить refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении refresh токена (хэш: {token_hash[:8]}...)"
            )
            raise RepositoryInternalError(
                "Не удалось получить refresh токен из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def invalidate_all_refresh_tokens(user_id: int) -> None:
        logger.debug(f"Попытка аннулировать все refresh токены для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                query = delete(RefreshToken).where(RefreshToken.user_id == user_id)
                result = await session.execute(query)
                await session.commit()
                logger.info(f"Аннулировано {result.rowcount} refresh токенов для user_id: {user_id}")  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при аннулировании refresh токенов для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось аннулировать refresh токены из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при аннулировании refresh токенов для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось аннулировать refresh токены из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def delete_refresh_token(token_obj: RefreshToken) -> None:
        logger.debug(f"Попытка удалить refresh токен ID: {token_obj.id}")
        try:
            async with db_manager.session_factory() as session:
                await session.delete(token_obj)
                await session.commit()
                logger.info(f"Удален refresh токен ID: {token_obj.id}")
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при удалении refresh токена ID: {token_obj.id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при удалении refresh токена ID: {token_obj.id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить refresh токен из-за неожиданной ошибки"
            ) from e


class AvatarFilesRepo:
    @staticmethod
    async def create_avatar(
        user_id: int, file_data: NSFileUploadResponse
    ) -> AvatarFiles:
        logger.debug(f"Попытка создания аватара для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                avatar = AvatarFiles(
                    user_id=user_id,
                    uuid=UUID(file_data.uuid),
                    s3_url=file_data.s3_url,
                    category=file_data.category,
                    content_type=file_data.content_type,
                    uploaded_at_s3=file_data.uploaded_at_s3,
                )
                session.add(avatar)
                await session.flush()
                await session.commit()
                await session.refresh(avatar)
                logger.info(
                    f"Аватар ID:{avatar.id} для user_id:{user_id} успешно создан"
                )
                return avatar
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании аватара для user_id {user_id}")
            raise RepositoryInternalError(
                "Не удалось создать аватар из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании аватара для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось создать аватар из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_avatar_by_user_id(user_id: int) -> Optional[AvatarFiles]:
        logger.debug(f"Попытка получить аватар для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                avatar = await session.scalar(
                    select(AvatarFiles).where(AvatarFiles.user_id == user_id)
                )
                if not avatar:
                    logger.debug(f"Аватар для user_id: {user_id} не найден")
                    return None
                logger.debug(f"Найден аватар ID:{avatar.id} для user_id:{user_id}")
                return avatar
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении аватара для user_id {user_id}")
            raise RepositoryInternalError(
                "Не удалось получить аватар из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении аватара для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось получить аватар из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_avatar_by_uuid(uuid: UUID) -> Optional[AvatarFiles]:
        logger.debug(f"Попытка получить аватар по UUID: {uuid}")
        try:
            async with db_manager.session_factory() as session:
                avatar = await session.scalar(
                    select(AvatarFiles).where(AvatarFiles.uuid == uuid)
                )
                if not avatar:
                    logger.debug(f"Аватар с UUID: {uuid} не найден")
                    raise EntityNotFoundError(f"Аватар с UUID {uuid} не найден")
                logger.debug(f"Найден аватар ID:{avatar.id} с UUID:{uuid}")
                return avatar
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении аватара по UUID {uuid}")
            raise RepositoryInternalError(
                "Не удалось получить аватар из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении аватара по UUID {uuid}")
            raise RepositoryInternalError(
                "Не удалось получить аватар из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def delete_avatar(avatar_obj: AvatarFiles) -> None:
        logger.debug(f"Попытка удалить аватар ID: {avatar_obj.id}")
        try:
            async with db_manager.session_factory() as session:
                await session.delete(avatar_obj)
                await session.commit()
                logger.info(f"Удален аватар ID: {avatar_obj.id}")
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при удалении аватара ID: {avatar_obj.id}")
            raise RepositoryInternalError(
                "Не удалось удалить аватар из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при удалении аватара ID: {avatar_obj.id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить аватар из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def delete_avatar_by_user_id(user_id: int) -> None:
        logger.debug(f"Попытка удалить аватар для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                query = delete(AvatarFiles).where(AvatarFiles.user_id == user_id)
                result = await session.execute(query)
                await session.commit()
                logger.info(f"Удалено {result.rowcount} аватаров для user_id: {user_id}")  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при удалении аватаров для user_id {user_id}")
            raise RepositoryInternalError(
                "Не удалось удалить аватары из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при удалении аватаров для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить аватары из-за неожиданной ошибки"
            ) from e
