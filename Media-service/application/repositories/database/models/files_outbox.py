from enum import StrEnum
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from application.repositories.database.crud.db_crud import (
    created_at,
    updated_at,
)
from application.repositories.database.models.base import Base


class FilesOutboxStatusesEnum(StrEnum):
    PENDING = "pending"
    SUCCESS = "sucess"
    FAILED = "failed"


class FilesOutboxOrm(Base):
    message_name: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default=FilesOutboxStatusesEnum.PENDING.value
    )

    traceparent: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at_db: Mapped[created_at]
    updated_at_db: Mapped[updated_at]
