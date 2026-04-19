from fastapi import UploadFile
from pydantic import BaseModel


class MSFileUploadRequest(BaseModel):
    file: UploadFile
    upload_context: str
    entity_id: int


class MSFileUploadResponse(BaseModel):
    ok: bool
    message: str
    status: str

    uuid: str
    size: int
    content_type: str
    category: str


VIDEO_FILES_NAME = "video"
IMAGE_FILES_NAME = "image"
AUDIO_FILES_NAME = "audio"

CHAT_MESSAGE_FILES_NAME = "chat_message_files"
USERS_AVATAR_NAME = "users_avatars"
