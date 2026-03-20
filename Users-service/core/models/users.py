import os
import sys
from uuid import UUID, uuid7

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from datetime import datetime
from typing import Any, List

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Boolean,
    JSON,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from core.models.base import Base
from .mixins import (
    intpk,
    str_128,
    str_64,
    created_at,
    updated_at,
)


class FileBase:
    uuid: Mapped[UUID] = mapped_column(unique=True, default=uuid7, index=True)
    s3_url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    uploaded_at_s3: Mapped[str]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]

    username: Mapped[str_64] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[bytes] = mapped_column(nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    profile: Mapped[Any | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str_64] = mapped_column(String, default="user", nullable=False)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    avatar: Mapped[List["AvatarFiles"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "avatar") or self.avatar is None:
            self.avatar = []


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str_128] = mapped_column(unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[created_at]

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class AvatarFiles(Base, FileBase):
    __tablename__ = "avatar"
    
    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(
        back_populates="avatar",
    )
