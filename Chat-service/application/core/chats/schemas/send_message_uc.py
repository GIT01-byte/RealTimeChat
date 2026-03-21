from pydantic import BaseModel


class SendMessageInputDTO(BaseModel):
    sender_id: int
    recipient_id: int
    text: str


class SendMessageOutputDTO(BaseModel):
    message_id: int
    sender_id: int
    recipient_id: int
    text: str
    # is_read: bool
