from uuid import UUID

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    DeleteFileFailedError,
    EntityNotFoundError,
    S3DeleteObjectFailedError,
)
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.files import FilesMetadataOrm
from application.repositories.files_repository import FileRepository
from application.repositories.storage.s3.client import S3Client
from application.utils.logging import logger


class DeleteFileUseCase:
    def __init__(
        self,
        file_meta_repo: FileRepository,
        s3_client: S3Client,
        commiter: Commiter,
    ) -> None:
        self.s3_client = s3_client
        self.file_meta_repo = file_meta_repo
        self.commiter = commiter

    async def execute(self, file_id: UUID):
        try:
            logger.info(f"[DeleteFile] Начало удаления файла: file_id: {file_id}")

            # 1. Получение файла из БД
            file_obj = await self.file_meta_repo.get_files_metadata(file_uuid=file_id)

            if not file_obj:
                logger.error(f"[DeleteFile] Файл не найден: file_id: {file_id}")
                raise EntityNotFoundError(detail="File not found")
            if not file_obj.s3_url:
                logger.error(
                    f"[DeleteFile] S3 URL отсутствует: file_id: {file_obj.file_id}"
                )
                raise DeleteFileFailedError(detail="S3 URL is missing")

            # 2. Удаление из S3
            await self._delete_file_s3(s3_key=file_obj.s3_url, file_id=file_obj.file_id)

            # 3. Подтверждение удаления из S3
            await self._confirm_deletion_s3(
                s3_key=file_obj.s3_url, file_id=file_obj.file_id
            )

            # 4. Удаление метаданных из БД
            await self._delete_file_db(file_obj=file_obj)

            logger.info(
                f"[DeleteFile] Файл успешно удален: file_id: {file_obj.file_id}"
            )
            return file_id

        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[DeleteFile] Неожиданная ошибка удаления: file_id: {file_id}: {e}"
            )
            raise DeleteFileFailedError(
                detail=f"Failed to delete file: {str(e)}"
            ) from e

    async def _delete_file_s3(self, s3_key: str, file_id: UUID) -> None:
        try:
            await self.s3_client.delete_object(key=s3_key)
            logger.info(f"[DeleteFile] Файл удален из S3: file_id: {file_id}")
        except Exception as e:
            logger.exception(
                f"[DeleteFile] Ошибка удаления из S3: file_id: {file_id}: {e}"
            )
            raise S3DeleteObjectFailedError(
                detail=f"Failed to delete from S3: {str(e)}"
            ) from e

    async def _confirm_deletion_s3(self, s3_key: str, file_id: UUID):
        try:
            file_exists = await self.s3_client.head_object(key=s3_key)
            if file_exists:
                logger.error(
                    f"[DeleteFile] Файл все еще существует в S3: file_id: {file_id}"
                )
                raise S3DeleteObjectFailedError(detail="File still exists in S3")
            logger.info(f"[DeleteFile] Подтверждено удаление из S3: file_id: {file_id}")
        except S3DeleteObjectFailedError:
            raise
        except Exception as e:
            logger.exception(
                f"[DeleteFile] Ошибка подтверждения удаления: file_id: {file_id}: {e}"
            )
            raise S3DeleteObjectFailedError(
                detail=f"Failed to confirm deletion: {str(e)}"
            ) from e

    async def _delete_file_db(self, file_obj: FilesMetadataOrm):
        try:
            await self.file_meta_repo.delete_file_metadata(file_metadata_obj=file_obj)
            await self.commiter.commit()
            logger.info(
                f"[DeleteFile] Метаданные удалены из БД: file_id: {file_obj.file_id}"
            )
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(
                f"[DeleteFile] Ошибка удаления метаданных: file_id: {file_obj.file_id}: {e}"
            )
            raise DeleteFileFailedError(
                detail=f"Failed to delete metadata: {str(e)}"
            ) from e
