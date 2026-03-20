from pydantic import BaseModel, ConfigDict


class ChatMessageCreate(BaseModel):
    recipient_id: int
    text: str


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
