from fastapi import UploadFile

from application.configs.settings import settings
from application.core.files.schemas.files import (
    FileUploadUCInputDTO,
    FileUploadUCOutputDTO,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import FilesUploadFailedError
from application.rabbitmq.contracts.files import (
    FileCreatedMessage,
    FilesOutboxCreateBody,
    FilesOutboxMessageName,
)
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.files_outbox import (
    FilesOutboxStatusesEnum,
)
from application.repositories.files_outbox_repository import FilesOutboxRepository
from application.repositories.files_repository import FileRepository
from application.repositories.storage.s3.client import S3Client
from application.utils.logging import logger


class UploadFileUseCase:
    def __init__(
        self,
        s3_client: S3Client,
        file_meta_repo: FileRepository,
        outbox_repo: FilesOutboxRepository,
        commiter: Commiter,
    ) -> None:
        self.s3_client = s3_client
        self.file_meta_repo = file_meta_repo
        self.outbox_repo = outbox_repo
        self.commiter = commiter

    async def execute(self, data: FileUploadUCInputDTO) -> FileUploadUCOutputDTO:
        """
        1. Загрузка в temp S3
        2. Сохранение метаданных + outbox message (транзакция)
        3. Возврат результата
        """
        try:
            logger.info(
                f"[UploadFile] Начало загрузки файла: {data.unique_filename}, "
                f"file_id: {data.file_id}, размер: {data.size} bytes"
            )
            # Проверяем, включена ли outbox feature
            if not settings.outbox:
                logger.info(
                    "[UploadFile] Outbox отключен, пропускаем этап сохранения в outbox"
                )

                # Шаг 1: Загрузка в S3
                await self.s3_client.put_object(
                    file=data.file.file,
                    key=data.s3_upload_key,
                )
                logger.info(
                    f"[UploadFile] Файл загружен в S3: {data.unique_filename}, file_id: {data.file_id}"
                )

                # Шаг 2: Сохранение метаданных
                s3_url = await self.s3_client.get_file_url(key=data.s3_upload_key)
                file_meta = await self._save_meta(data=data, s3_url=s3_url)

                # Шаг 3: Возврат результата
                return FileUploadUCOutputDTO(
                    upload_status=FilesOutboxStatusesEnum.SUCCESS.value,
                    file_id=file_meta.file_id,
                    size=file_meta.size,
                    unique_filename=file_meta.filename,
                    content_type=file_meta.content_type,
                    category=file_meta.category,
                )

            logger.info(
                "[UploadFile] Outbox включен, этап сохранения в outbox будет реализован"
            )
            # Шаг 1: Загрузка в temp S3
            await self._temp_upload_s3(
                file=data.file, s3_temp_upload_key=data.s3_temp_upload_key
            )
            logger.info(
                f"[UploadFile] Файл загружен в temp S3: {data.unique_filename}, file_id: {data.file_id}"
            )

            # Шаг 2: Сохранение метаданных + outbox message (транзакция)
            file_meta, outbox_message = await self._save_meta_and_outbox(data=data)
            logger.info(
                f"[UploadFile] Метаданные и outbox сохранены: {data.unique_filename}, "
                f"file_id: {data.file_id}, статус: {outbox_message.status}"
            )

            # Шаг 3: Возврат результата
            return FileUploadUCOutputDTO(
                upload_status=outbox_message.status,
                file_id=file_meta.file_id,
                size=file_meta.size,
                unique_filename=file_meta.filename,
                content_type=file_meta.content_type,
                category=file_meta.category,
            )

        except BaseAPIException as e:
            logger.error(
                f"[UploadFile] Ошибка загрузки файла: {data.unique_filename}, "
                f"file_id: {data.file_id}, {e.detail}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"[UploadFile] Неожиданная ошибка загрузки файла: {data.unique_filename}, "
                f"file_id: {data.file_id}: {e}"
            )
            raise FilesUploadFailedError(detail=f"Unexpected error: {str(e)}") from e

    async def _temp_upload_s3(self, file: UploadFile, s3_temp_upload_key: str):
        """Загружает файл во временное хранилище S3"""
        try:
            logger.info(f"[UploadFile] Загрузка в temp S3: {s3_temp_upload_key}")

            await self.s3_client.put_object(
                file=file.file,
                key=s3_temp_upload_key,
            )

            logger.info(
                f"[UploadFile] Успешно загружено в temp S3: {s3_temp_upload_key}"
            )
        except Exception as e:
            logger.exception(
                f"[UploadFile] Ошибка загрузки в temp S3: {s3_temp_upload_key}: {e}"
            )
            raise FilesUploadFailedError(
                detail=f"Failed to upload file to temporary S3: {str(e)}"
            ) from e

    async def _save_meta_and_outbox(self, data: FileUploadUCInputDTO):
        """Атомарно сохраняет метаданные и outbox message"""
        try:
            logger.info(
                f"[UploadFile] Создание записи в БД: file_id: {data.file_id}, "
                f"filename: {data.unique_filename}"
            )

            # Создание метаданных
            file_metadata_in_db = await self.file_meta_repo.create_metadata(
                file_id=data.file_id,
                entity_id=data.entity_id,
                upload_context=data.upload_context,
                filename=data.unique_filename,
                size=data.size,
                content_type=data.content_type,
                category=data.category,
            )
            if not file_metadata_in_db:
                logger.error(
                    f"[UploadFile] Не удалось создать метаданные: file_id: {data.file_id}"
                )
                raise FilesUploadFailedError(
                    detail="Не удалось сохранить метаданные в БД"
                )
            logger.info(
                f"[UploadFile] Метаданные созданы: file_id: {data.file_id}, id: {file_metadata_in_db.id}"
            )

            # Создание outbox message
            message_body = FilesOutboxCreateBody(
                file_id=data.file_id,
                upload_context=data.upload_context,
                s3_temp_upload_key=data.s3_temp_upload_key,
                s3_upload_key=data.s3_upload_key,
                status=FilesOutboxStatusesEnum.PENDING.value,
            )
            message = FileCreatedMessage(
                sender=settings.app.name,
                body=message_body,
            )

            file_message_outbox_in_db = await self.outbox_repo.create_outbox_message(
                message_name=FilesOutboxMessageName.upload_start.value,
                body=message.model_dump(mode="json"),
            )
            if not file_message_outbox_in_db:
                logger.error(
                    f"[UploadFile] Не удалось создать outbox message: file_id: {data.file_id}"
                )
                raise FilesUploadFailedError(
                    detail="Не удалось сохранить сообщение для отправки файла в Outbox"
                )
            logger.info(
                f"[UploadFile] Outbox message создан: file_id: {data.file_id}, "
                f"message_id: {file_message_outbox_in_db.id}"
            )

            await self.commiter.commit()
            logger.info(
                f"[UploadFile] Транзакция успешно завершена: file_id: {data.file_id}"
            )
            return (file_metadata_in_db, file_message_outbox_in_db)

        except BaseAPIException:
            await self.commiter.rollback()
            logger.error(
                f"[UploadFile] Откат транзакции (BaseAPIException): file_id: {data.file_id}"
            )
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(
                f"[UploadFile] Откат транзакции (Exception): file_id: {data.file_id}: {e}"
            )
            raise FilesUploadFailedError(
                detail=f"Произошла ошибка при создании метаданных файла: {str(e)}"
            ) from e

    async def _save_meta(self, data: FileUploadUCInputDTO, s3_url: str):
        """При отключенной outbox feature сохраняет метаданные файла"""
        try:
            logger.info(
                f"[UploadFile] Создание записи в БД: file_id: {data.file_id}, "
                f"filename: {data.unique_filename}"
            )

            # Создание метаданных
            file_metadata_in_db = await self.file_meta_repo.create_metadata(
                file_id=data.file_id,
                entity_id=data.entity_id,
                upload_context=data.upload_context,
                filename=data.unique_filename,
                size=data.size,
                content_type=data.content_type,
                category=data.category,
                s3_url=s3_url,
            )
            if not file_metadata_in_db:
                logger.error(
                    f"[UploadFile] Не удалось создать метаданные: file_id: {data.file_id}"
                )
                raise FilesUploadFailedError(
                    detail="Не удалось сохранить метаданные в БД"
                )
            logger.info(
                f"[UploadFile] Метаданные созданы: file_id: {data.file_id}, id: {file_metadata_in_db.id}"
            )

            await self.commiter.commit()
            logger.info(
                f"[UploadFile] Метаданные успешно сохранены: file_id: {data.file_id}"
            )
            return file_metadata_in_db
        except BaseAPIException:
            await self.commiter.rollback()
            logger.error(
                f"[UploadFile] Откат транзакции (BaseAPIException): file_id: {data.file_id}"
            )
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(
                f"[UploadFile] Откат транзакции (Exception) file_id: {data.file_id}: {e}"
            )
            raise FilesUploadFailedError(
                detail=f"Произошла ошибка при создании метаданных файла: {str(e)}"
            ) from e
