from typing import Optional
from uuid import UUID

from exceptions.exceptions import (
    EntityNotFoundError,
    RepositoryInternalError,
)
from integrations.files.schemas import MSFileUploadResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from utils.logging import logger

from core.db.db_manager import db_manager


class AvatarFilesRepo:
    @staticmethod
    async def create_avatar(user_id: int, file_data: MSFileUploadResponse):  # FIXME
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
                logger.info(
                    f"Удалено {result.rowcount} аватаров для user_id: {user_id}"  # type: ignore
                )  # type: ignore
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
