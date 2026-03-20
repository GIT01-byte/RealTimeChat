from uuid import UUID, uuid7

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from application.repositories.database.mixins.created_at_updated_at import (
    created_at,
)
from application.repositories.database.models.base import Base


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid7, index=True)

    sender_id: Mapped[int] = mapped_column(nullable=False)
    recipient_id: Mapped[int] = mapped_column(nullable=False)

    text: Mapped[str] = mapped_column(String(4096), nullable=False)

    created_at: Mapped[created_at]

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, uuid={self.uuid}, v={self.sender_id}, recipient_id={self.recipient_id}, text={self.text[:50]!r})>"
