from uuid import UUID, uuid7

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from application.repositories.database.crud import (
    created_at,
    updated_at,
)
from application.repositories.database.models.base import Base


class FilesMetadataOrm(Base):
    file_id: Mapped[UUID] = mapped_column(unique=True, default=uuid7(), index=True)

    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    upload_context: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_url: Mapped[str | None] = mapped_column(String(512), unique=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[str] = mapped_column(String, default="created", nullable=False)

    created_at_db: Mapped[created_at]
    updated_at_db: Mapped[updated_at]
