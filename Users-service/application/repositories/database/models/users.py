from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from application.repositories.database.models.base import Base
from application.repositories.database.models.mixins import (
    created_at,
    intpk,
    str_64,
    str_128,
    updated_at,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[intpk]

    username: Mapped[str_64] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[bytes] = mapped_column(nullable=False)
    avatar: Mapped[str | None]
    profile: Mapped[Any | None] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str_64] = mapped_column(String, default="user", nullable=False)

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[intpk]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str_128] = mapped_column(unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[created_at]

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
