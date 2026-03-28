from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from application.rabbitmq.contracts.base import RabbitMQMessage


class FilesOutboxMessageName(StrEnum):
    upload_start = "file.upload.started"


class FilesOutboxCreateBody(BaseModel):
    file_id: UUID
    upload_context: str
    s3_temp_upload_key: str
    s3_upload_key: str
    status: str


class FileCreatedMessage(RabbitMQMessage[FilesOutboxCreateBody]):
    pass
