import datetime
from typing import List
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    recipient_id: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=4096)
    videos: List[UUID]
    images: List[UUID]
    audios: List[UUID]


class ChatMessageMediaCreate(BaseModel):
    def __init__(
        self,
        video_files: List[UploadFile] | None = None,
        image_files: List[UploadFile] | None = None,
        audio_files: List[UploadFile] | None = None,
    ):
        self.video_files = video_files
        self.image_files = image_files
        self.audio_files = audio_files


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    sender_id: int
    recipient_id: int
    text: str
    created_at: datetime.datetime
