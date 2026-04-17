from uuid import UUID, uuid7

from application.repositories.database.mixins.created_at_updated_at import (
    created_at,
    read_at,
)
from application.repositories.database.mixins.list_obj_uuids import list_obj_uuids
from application.repositories.database.models.base import Base
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid7, index=True)

    sender_id: Mapped[int] = mapped_column(nullable=False)
    recipient_id: Mapped[int] = mapped_column(nullable=False)

    text: Mapped[str] = mapped_column(String(4096), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    videos: Mapped[list_obj_uuids]
    images: Mapped[list_obj_uuids]
    audios: Mapped[list_obj_uuids]

    created_at: Mapped[created_at]
    read_at: Mapped[read_at]

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, uuid={self.uuid}, sender_id={self.sender_id}, recipient_id={self.recipient_id}, text={self.text[:50]!r}, images={self.images}, videos={self.videos}, audios={self.audios})>"
