from typing import List

from pydantic import BaseModel


class SendMessageInputDTO(BaseModel):
    sender_id: int
    recipient_id: int
    text: str
    videos: List[str] | None
    images: List[str] | None
    audios: List[str] | None


class SendMessageOutputDTO(BaseModel):
    message_id: int
    sender_id: int
    recipient_id: int
    text: str
    videos: List[str] | None
    images: List[str] | None
    audios: List[str] | None
    # is_read: bool
