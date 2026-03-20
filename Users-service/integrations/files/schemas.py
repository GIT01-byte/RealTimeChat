import datetime
from uuid import UUID
from fastapi import UploadFile
from pydantic import BaseModel


class NSFileUploadRequest(BaseModel):
    file: UploadFile
    upload_context: str
    entity_id: int


class NSFileUploadResponse(BaseModel):
    uuid: str
    s3_url: str
    content_type: str
    category: str
    uploaded_at_s3: str
