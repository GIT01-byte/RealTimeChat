import datetime
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

LOG_PREFIX = "[FileRepository]"


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
        s3_url: str | None = None,
    ) -> FilesMetadataOrm | None:
        logger.debug(
            f"{LOG_PREFIX} Создание метаданных файла file_id={file_id!r}, entity_id={entity_id}, context={upload_context!r}"
        )
        try:
            existing_metadata = await self.session.scalar(
                select(FilesMetadataOrm).filter(
                    or_(FilesMetadataOrm.file_id == file_id)
                )
            )
            if existing_metadata:
                logger.warning(
                    f"{LOG_PREFIX} Метаданные с UUID {file_id!r} уже существуют"
                )
                raise DataConflictError(
                    f"Метаданные с UUID: {file_id!r} уже существуют."
                )

            new_meta = FilesMetadataOrm(
                file_id=file_id,
                entity_id=entity_id,
                upload_context=upload_context,
                s3_url=s3_url,
                filename=filename,
                size=size,
                content_type=content_type,
                category=category,
            )
            self.session.add(new_meta)
            await self.session.flush()
            logger.debug(
                f"{LOG_PREFIX} Метаданные файла file_id={file_id!r} успешно созданы"
            )
            return new_meta
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при создании метаданных file_id={file_id!r}"
            )
            raise RepositoryInternalError(
                "Не удалось создать метаданные из-за ошибки базы данных."
            ) from e

    async def get_files_metadata(self, file_uuid: UUID) -> FilesMetadataOrm | None:
        logger.debug(f"{LOG_PREFIX} Получение метаданных файла file_uuid={file_uuid!r}")
        try:
            stmt = (
                select(FilesMetadataOrm)
                .where(FilesMetadataOrm.file_id == str(file_uuid))
                .order_by(FilesMetadataOrm.id)
            )
            result = await self.session.scalars(stmt)
            metadata = result.first()

            if not metadata:
                logger.debug(
                    f"{LOG_PREFIX} Метаданные файла file_uuid={file_uuid!r} не найдены"
                )
                raise EntityNotFoundError(
                    f"Метаданные файла с UUID: {file_uuid} не найдены."
                )

            logger.debug(
                f"{LOG_PREFIX} Метаданные файла file_uuid={file_uuid!r} получены"
            )
            return metadata
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при получении метаданных file_uuid={file_uuid!r}"
            )
            raise RepositoryInternalError(
                f"Не удалось получить метаданные файла с UUID {file_uuid} из-за ошибки базы данных."
            ) from e

    async def delete_file_metadata(self, file_metadata_obj: FilesMetadataOrm) -> None:
        logger.debug(
            f"{LOG_PREFIX} Удаление метаданных файла file_id={file_metadata_obj.file_id!r}"
        )
        try:
            await self.session.delete(file_metadata_obj)
            await self.session.flush()
            logger.debug(
                f"{LOG_PREFIX} Метаданные файла file_id={file_metadata_obj.file_id!r} удалены"
            )
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при удалении метаданных file_id={file_metadata_obj.file_id!r}"
            )
            raise RepositoryInternalError(
                f"Не удалось удалить метаданные файла с UUID {file_metadata_obj.file_id} из-за ошибки базы данных."
            ) from e

    async def update_file_status(
        self, file_id: UUID, status: str
    ) -> FilesMetadataOrm | None:
        logger.debug(
            f"{LOG_PREFIX} Обновление статуса файла file_id={file_id!r} -> {status!r}"
        )
        try:
            result = await self.session.scalars(
                select(FilesMetadataOrm).filter(
                    FilesMetadataOrm.file_id == str(file_id)
                )
            )
            metadata = result.first()

            if not metadata:
                logger.debug(
                    f"{LOG_PREFIX} Файл file_id={file_id!r} не найден при обновлении статуса"
                )
                raise EntityNotFoundError(
                    f"Метаданные файла с UUID: {file_id} не найдены."
                )

            metadata.status = status
            self.session.add(metadata)
            await self.session.flush()
            logger.debug(
                f"{LOG_PREFIX} Статус файла file_id={file_id!r} обновлён на {status!r}"
            )
            return metadata
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при обновлении статуса file_id={file_id!r}"
            )
            raise RepositoryInternalError(
                f"Не удалось обновить статус файла с UUID {file_id} из-за ошибки базы данных."
            ) from e

    async def update_file_s3_url(
        self, file_id: UUID, s3_url: str
    ) -> FilesMetadataOrm | None:
        logger.debug(f"{LOG_PREFIX} Обновление S3 URL файла file_id={file_id!r}")
        try:
            result = await self.session.scalars(
                select(FilesMetadataOrm).filter(
                    FilesMetadataOrm.file_id == str(file_id)
                )
            )
            metadata = result.first()

            if not metadata:
                logger.debug(
                    f"{LOG_PREFIX} Файл file_id={file_id!r} не найден при обновлении S3 URL"
                )
                raise EntityNotFoundError(
                    f"Метаданные файла с UUID: {file_id} не найдены."
                )

            metadata.s3_url = s3_url
            self.session.add(metadata)
            await self.session.flush()
            logger.debug(f"{LOG_PREFIX} S3 URL файла file_id={file_id!r} обновлён")
            return metadata
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при обновлении S3 URL file_id={file_id!r}"
            )
            raise RepositoryInternalError(
                f"Не удалось обновить S3 URL файла с UUID {file_id} из-за ошибки базы данных."
            ) from e

    async def mark_as_linked(
        self, file_id: UUID, linked_at: datetime.datetime
    ) -> FilesMetadataOrm | None:
        logger.debug(f"{LOG_PREFIX} Привязка файла file_id={file_id!r} к сообщению")
        try:
            result = await self.session.scalars(
                select(FilesMetadataOrm).filter(
                    FilesMetadataOrm.file_id == str(file_id)
                )
            )
            file = result.first()

            if not file:
                logger.warning(
                    f"{LOG_PREFIX} Файл file_id={file_id!r} не найден при попытке пометить как привязанный"
                )
                raise EntityNotFoundError(f"Файл с UUID: {file_id} не найден.")

            file.is_linked = True
            file.linked_at = linked_at
            self.session.add(file)
            await self.session.flush()
            logger.debug(
                f"{LOG_PREFIX} Файл file_id={file_id!r} успешно помечен привязанным"
            )
            return file
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"{LOG_PREFIX} Ошибка БД при привязке файла file_id={file_id!r}"
            )
            raise RepositoryInternalError(
                f"Не удалось привязать файл с UUID {file_id} из-за ошибки базы данных."
            ) from e
