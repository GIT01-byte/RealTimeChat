from application.exceptions.base import BaseAPIException, RepositoryError
from fastapi import status


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


# Исключения сервисов о проваленной работе
class SendMessagesFailedError(BaseAPIException):
    def __init__(self, detail: str = "Failed to send message"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class GetMessagesBetweenUsersFailedError(BaseAPIException):
    def __init__(self, detail: str = "Failed to get messages between users"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class GetUsersListFailedError(BaseAPIException):
    def __init__(self, detail: str = "Failed to get users list"):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
