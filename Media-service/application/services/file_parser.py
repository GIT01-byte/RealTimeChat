import magic
from fastapi import UploadFile

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EmptyFileError,
    ValidateFileFailedError,
)
from application.utils.logging import logger


class FileParser:
    def excract_file_extension(self, file: UploadFile) -> str:
        try:
            if not file.filename:
                raise EmptyFileError(detail="File has no filename")
            return file.filename.split(".")[-1].lower()
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка получения размера файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to get file size for {file.filename}: {str(e)}"
            ) from e

    def excract_file_size(self, file: UploadFile) -> int:
        try:
            if not file.size:
                raise EmptyFileError(detail="File has no size")
            return file.size
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка получения размера файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to get file size for {file.filename}: {str(e)}"
            ) from e

    def excract_file_mime_type(self, file: UploadFile) -> str:
        try:
            if not file.filename:
                raise EmptyFileError(detail="File has no filename")

            file_content = file.file.read(2048)
            file.file.seek(0)

            mime_type = magic.from_buffer(file_content, mime=True)

            if not mime_type:
                raise ValidateFileFailedError(
                    detail=f"Failed to detect MIME type for {file.filename}"
                )

            return mime_type
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка определения типа файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to detect MIME type for {file.filename}: {str(e)}"
            ) from e
