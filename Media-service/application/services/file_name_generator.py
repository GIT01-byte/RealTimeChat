from uuid import UUID

from fastapi import UploadFile

from application.core.files.schemas.categories import SOURCE_SERVICE
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EmptyFileError,
    ValidateFileFailedError,
)
from application.services.file_category_detector import FileCategory
from application.utils.logging import logger


class FileMetadataFenerator:
    async def generate_unigue_filename(
        self, file: UploadFile, file_id: UUID, category: FileCategory
    ) -> str:
        try:
            if not file.filename or not category:
                raise EmptyFileError(detail="Empty filename or category")

            extension = file.filename.split(".")[-1].lower()

            if not extension:
                raise EmptyFileError(detail=f"File {file.filename!r} has no extension")

            new_filename = f"{category.name}/{file_id}.{extension}"
            return new_filename
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка генерации уникального имени файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to generate unique filename for {file.filename}: {str(e)}"
            ) from e

    async def generate_s3_temp_upload_key(self, file: UploadFile, file_id: UUID) -> str:
        try:
            if not file.filename:
                raise EmptyFileError(detail="Empty filename")

            extension = file.filename.split(".")[-1].lower()

            if not extension:
                raise EmptyFileError(detail=f"File {file.filename!r} has no extension")

            s3_temp_upload_key = f"temp/{SOURCE_SERVICE}/{file_id}.{extension}"
            return s3_temp_upload_key
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка генерации временного ключа S3: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to generate temp s3 upload key for {file.filename}: {str(e)}"
            ) from e

    async def generate_s3_upload_key(
        self, upload_context: str, entity_id: int, unique_filename: str
    ):
        return f"{SOURCE_SERVICE}/{upload_context}/{entity_id}/{unique_filename}"
