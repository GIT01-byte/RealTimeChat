from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    DataConflictError,
    EntityNotFoundError,
    RepositoryInternalError,
)
from application.repositories.database.models.files import FilesMetadataOrm
from application.utils.logging import logger


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_metadata(
        self,
        file_id: UUID,
        entity_id: int,
        upload_context: str,
        filename: str,
        size: int,
        content_type: str,
        category: str,
    ) -> FilesMetadataOrm | None:
        try:
            existing_metadata = await self.session.scalar(
                select(FilesMetadataOrm).filter(
                    or_(FilesMetadataOrm.file_id == file_id)
                )
            )
            if existing_metadata:
                raise DataConflictError(
                    f"Метаданные с UUID: {file_id!r} уже существуют."
                )

            new_meta = FilesMetadataOrm(
                file_id=file_id,
                entity_id=entity_id,
                upload_context=upload_context,
                filename=filename,
                size=size,
                content_type=content_type,
                category=category,
            )
            self.session.add(new_meta)
            await self.session.flush()
            return new_meta
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании метаданных: {e}")
            raise RepositoryInternalError(
                "Не удалось создать метаданные из-за ошибки базы данных."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при создании метаданных: {e}")
            raise RepositoryInternalError(
                "Не удалось создать метаданные из-за неожиданной ошибки."
            ) from e

    async def get_files_metadata(self, file_uuid: UUID) -> FilesMetadataOrm | None:
        try:
            stmt = (
                select(FilesMetadataOrm)
                .where(FilesMetadataOrm.file_id == str(file_uuid))
                .order_by(FilesMetadataOrm.id)
            )
            result = await self.session.scalars(stmt)
            metadata = result.first()

            if metadata:
                return metadata

            raise EntityNotFoundError(
                f"Метаданные файла с UUID: {file_uuid} не найдены."
            )
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении метаданных: {e}")
            raise RepositoryInternalError(
                f"Не удалось получить метаданные файла с UUID {file_uuid} из-за ошибки базы данных."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении метаданных: {e}")
            raise RepositoryInternalError(
                f"Не удалось получить метаданные файла с UUID {file_uuid} из-за неожиданной ошибки."
            ) from e

    async def delete_file_metadata(self, file_metadata_obj: FilesMetadataOrm) -> None:
        try:
            await self.session.delete(file_metadata_obj)
            await self.session.flush()
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при удалении метаданных: {e}")
            raise RepositoryInternalError(
                f"Не удалось удалить метаданные файла с UUID {file_metadata_obj.file_id} из-за ошибки базы данных."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при удалении метаданных: {e}")
            raise RepositoryInternalError(
                f"Не удалось удалить метаданные файла с UUID {file_metadata_obj.file_id} из-за неожиданной ошибки."
            ) from e

    async def update_file_status(
        self, file_id: UUID, status: str
    ) -> FilesMetadataOrm | None:
        try:
            stmt = select(FilesMetadataOrm).filter(
                FilesMetadataOrm.file_id == str(file_id)
            )
            result = await self.session.scalars(stmt)
            metadata = result.first()

            if not metadata:
                raise EntityNotFoundError(
                    f"Метаданные файла с UUID: {file_id} не найдены."
                )

            metadata.status = status
            self.session.add(metadata)
            await self.session.flush()
            return metadata
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при обновлении статуса: {e}")
            raise RepositoryInternalError(
                f"Не удалось обновить статус файла с UUID {file_id} из-за ошибки базы данных."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при обновлении статуса: {e}")
            raise RepositoryInternalError(
                f"Не удалось обновить статус файла с UUID {file_id} из-за неожиданной ошибки."
            ) from e

    async def update_file_s3_url(
        self, file_id: UUID, s3_url: str
    ) -> FilesMetadataOrm | None:
        try:
            stmt = select(FilesMetadataOrm).filter(
                FilesMetadataOrm.file_id == str(file_id)
            )
            result = await self.session.scalars(stmt)
            metadata = result.first()

            if not metadata:
                raise EntityNotFoundError(
                    f"Метаданные файла с UUID: {file_id} не найдены."
                )

            metadata.s3_url = s3_url
            self.session.add(metadata)
            await self.session.flush()
            return metadata
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при обновлении статуса: {e}")
            raise RepositoryInternalError(
                f"Не удалось обновить статус файла с UUID {file_id} из-за ошибки базы данных."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при обновлении статуса: {e}")
            raise RepositoryInternalError(
                f"Не удалось обновить статус файла с UUID {file_id} из-за неожиданной ошибки."
            ) from e
