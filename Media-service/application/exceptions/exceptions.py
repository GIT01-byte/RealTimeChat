from fastapi import status

from application.exceptions.base import BaseAPIException, RepositoryError


# --- Базовые исключения Репозитория ---
class RepositoryInternalError(RepositoryError):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(detail=detail)


class EntityNotFoundError(BaseAPIException):
    def __init__(self, detail: str = "Entity not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class DataConflictError(BaseAPIException):
    def __init__(self, detail: str = "Data conflict occurred"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


# --- Базовые исключения API ---
# Исключения обработки файлов
class EmptyFileError(BaseAPIException):
    def __init__(self, detail: str = "File is empty"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileCategoryNotSupportedError(BaseAPIException):
    def __init__(self, detail: str = "File category is not supported"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileMaxSizeLimitError(BaseAPIException):
    def __init__(self, detail: str = "File size exceeds the maximum limit"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileInvalidExtensionError(BaseAPIException):
    def __init__(self, detail: str = "File extension is invalid"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


class FileVirusFound(BaseAPIException):
    def __init__(self, detail: str = "Virus found in file"):
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)


# Исключения S3
class S3DeleteObjectFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error deleting object from S3"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class S3PutObjectFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error uploading object to S3"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class S3GetObjectFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error gettiobject from S3"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Исключения сервисов о проваленной работе
class FilesUploadFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error uploading files"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ViewFileFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error viewing file"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DeleteFileFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error deleting file"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ValidateFileFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error validating file"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VirusScanFileFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error scanning file for viruses"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ProcessFileFailedError(BaseAPIException):
    def __init__(self, detail: str = "Error processing file"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
