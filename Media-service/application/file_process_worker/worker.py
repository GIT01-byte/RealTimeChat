import asyncio

from application.exceptions.base import BaseAPIException
from application.rabbitmq.consumer import RabbitMQConsumer
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.files_outbox import (
    FilesOutboxStatusesEnum,
)
from application.repositories.files_repository import FileRepository
from application.repositories.storage.s3.client import S3Client
from application.utils.logging import logger


class FileProcessorWorker:
    def __init__(
        self,
        file_meta_repo: FileRepository,
        s3_client: S3Client,
        commiter: Commiter,
        consumer: RabbitMQConsumer,
    ) -> None:
        self.file_meta_repo = file_meta_repo
        self.s3_client = s3_client
        self.commiter = commiter
        self.consumer = consumer

    async def _process_file_message(self, message: dict):
        try:
            body = message.get("body")
            if not body or not isinstance(body, dict):
                return

            sender = message.get("sender")
            status = body.get("status")
            file_id = body.get("file_id")
            s3_upload_key = body.get("s3_upload_key")
            s3_temp_upload_key = body.get("s3_temp_upload_key")

            # Валидация обязательных полей
            if (
                not sender
                or not status
                or not file_id
                or not s3_upload_key
                or not s3_temp_upload_key
            ):
                logger.warning(
                    "[FileProcessor] Отсутствует body в сообщении или body не dict"
                )
                return

            if status != "pending" or sender != "Media_Service":
                logger.warning(
                    "[FileProcessor] Некорректный статус или sender в сообщении"
                )
                return

            # Перемещение файла из временной папки в постоянную
            await self.s3_client.move_file(
                src_key=s3_temp_upload_key,
                dest_key=s3_upload_key,
            )

            # Получение URL файла и обновление метаданных
            s3_url = await self.s3_client.get_file_url(key=s3_upload_key)
            await self.file_meta_repo.update_file_status(
                file_id=file_id,
                status=FilesOutboxStatusesEnum.SUCCESS.value,
            )
            updated_meta = await self.file_meta_repo.update_file_s3_url(
                file_id=file_id, s3_url=s3_url
            )
            if not updated_meta:
                logger.warning("[FileProcessor] Обновление метаданных не удалось")
                return

            await self.commiter.commit()
            logger.info(
                f"[FileProcessor] Файл обработан: ID({updated_meta.file_id!r}), статус({updated_meta.status!r}), S3-URL({updated_meta.s3_url!r})"
            )
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception:
            await self.commiter.rollback()
            logger.exception("[FileProcessor] Ошибка обработки")
            raise

    async def start(self):
        """Слушает RabbitMQ и обрабатывает сообщения"""
        await self.consumer.connect()
        await self.consumer.consume(
            queue_name="file.upload.started",
            callback_func=self._process_file_message,
        )
        logger.info("[FileProcessor] Worker запущен")
        await asyncio.Future()
