from fastapi import UploadFile

from application.core.files.schemas.categories import (
    CATEGORIES_BY_NAME,
    CHAT_MESSAGE_FILES_NAME,
    MESSAGE_AUDIO,
    MESSAGE_IMAGES,
    MESSAGE_VIDEOS,
    USERS_AVATAR_NAME,
    USERS_AVATARS,
    FileCategory,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EmptyFileError,
    FileCategoryNotSupportedError,
    ValidateFileFailedError,
)
from application.utils.logging import logger


class FileCategoryDetector:
    async def detect(self, file: UploadFile, upload_context: str) -> FileCategory:
        try:
            if not file or not file.content_type:
                raise EmptyFileError

            if (
                file.content_type in MESSAGE_VIDEOS.content_types
                and upload_context == CHAT_MESSAGE_FILES_NAME
            ):
                return MESSAGE_VIDEOS
            elif (
                file.content_type in MESSAGE_IMAGES.content_types
                and upload_context == CHAT_MESSAGE_FILES_NAME
            ):
                return MESSAGE_IMAGES
            elif (
                file.content_type in MESSAGE_AUDIO.content_types
                and upload_context == CHAT_MESSAGE_FILES_NAME
            ):
                return MESSAGE_AUDIO
            elif (
                file.content_type in USERS_AVATARS.content_types
                and upload_context == USERS_AVATAR_NAME
            ):
                return USERS_AVATARS
            else:
                raise FileCategoryNotSupportedError
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка определения категории файла: {e}")
            raise ValidateFileFailedError(
                detail=f"Failed to process file category for {file.filename}: {str(e)}"
            ) from e

    async def get_category_rules(self, category: str) -> FileCategory:
        category_obj = CATEGORIES_BY_NAME.get(category)
        if not category_obj:
            raise FileCategoryNotSupportedError
        return category_obj
