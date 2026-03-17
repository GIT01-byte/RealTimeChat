from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from application.repositories.database.mixins import list_obj_uuids
from application.repositories.database.mixins.created_at_updated_at import (
    created_at,
    updated_at,
)
from application.repositories.database.models.base import Base


class ChatRooms(Base):
    __tablename__ = "chat_rooms"

    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid4, index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=True)

    members_uuids: Mapped[list_obj_uuids]
    messages_uuids: Mapped[list_obj_uuids]

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    def __repr__(self) -> str:
        return f"<ChatRoom(id={self.id}, title='{self.title}')>"
