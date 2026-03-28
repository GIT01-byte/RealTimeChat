from fastapi import UploadFile
from pydantic import BaseModel

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EmptyFileError,
    ValidateFileFailedError,
)
from application.services.file_category_detector import FileCategory
from application.services.file_parser import FileParser
from application.utils.logging import logger


class FileValidationReport(BaseModel):
    is_valid: bool
    size_valid: bool
    extension_valid: bool
    integrity_valid: bool
    errors: list[str] = []


class FileValidator:
    def __init__(
        self,
        file_parser: FileParser = FileParser(),
    ) -> None:
        self.file_parser = file_parser

    def _validate_file_not_empty(self, file: UploadFile) -> None:
        if not file or not file.filename or not file.size:
            raise EmptyFileError

    async def _validate_file_mime(
        self, file: UploadFile, category: FileCategory
    ) -> tuple[bool, str | None]:
        try:
            detected_mime = self.file_parser.excract_file_mime_type(file)

            if not detected_mime:
                return (
                    False,
                    f"Failed to detect Mime type of file {file.filename}, category: {category.name}",
                )
            if detected_mime not in category.content_types:
                return (
                    False,
                    f"File {file.filename} with MIME {detected_mime} is not supported for category: {category.name}",
                )

            return True, None
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка проверки целостности файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to validate file integrity for {file.filename}: {str(e)}"
            ) from e

    async def _validate_file_extension(
        self, file: UploadFile, category: FileCategory
    ) -> tuple[bool, str | None]:
        try:
            extension = self.file_parser.excract_file_extension(file)

            if not extension:
                return (False, f"File {file.filename!r} has no extension")
            if extension not in category.extensions:
                return (
                    False,
                    f"File {file.filename!r} with extension {extension!r} is not supported for category: {category.name}",
                )

            return True, None
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка проверки расширения файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to validate file extension for {file.filename}: {str(e)}"
            ) from e

    async def _validate_file_size(
        self, file: UploadFile, category: FileCategory
    ) -> tuple[bool, str | None]:
        try:
            file_size = self.file_parser.excract_file_size(file)

            if not file_size:
                return (False, "File has no size")
            if file_size > category.max_size:
                return (
                    False,
                    f"File size {file.size} bytes exceeds the maximum allowed size for category: {category.name}",
                )

            return True, None
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка проверки размера файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to validate file size for {file.filename}: {str(e)}"
            ) from e

    async def validate_file(
        self, file: UploadFile, category: FileCategory
    ) -> FileValidationReport:
        try:
            self._validate_file_not_empty(file)

            errors = []

            validate_max_size, size_errors = await self._validate_file_size(
                file, category
            )
            if size_errors:
                errors.append(size_errors)

            validate_extension, extension_errors = await self._validate_file_extension(
                file, category
            )
            if extension_errors:
                errors.append(extension_errors)

            validate_integrity, integrity_errors = await self._validate_file_mime(
                file, category
            )
            if integrity_errors:
                errors.append(integrity_errors)

            return FileValidationReport(
                is_valid=all(
                    [validate_max_size, validate_extension, validate_integrity]
                ),
                size_valid=validate_max_size,
                extension_valid=validate_extension,
                integrity_valid=validate_integrity,
                errors=errors,
            )
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка валидации файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to validate file {file.filename}: {str(e)}"
            ) from e
