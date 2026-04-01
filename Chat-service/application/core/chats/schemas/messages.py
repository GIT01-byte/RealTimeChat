import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    recipient_id: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=4096)


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    sender_id: int
    recipient_id: int
    text: str
    created_at: datetime.datetime
