from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from application.exceptions.exceptions import (
    RepositoryInternalError,
)
from application.repositories.database.models.files_outbox import (
    FilesOutboxOrm,
    FilesOutboxStatusesEnum,
)
from application.utils.logging import logger


class FilesOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_outbox_message(
        self,
        message_name: str,
        body: dict[str, Any] | list[Any],
        traceparent: str | None = None,
    ) -> FilesOutboxOrm | None:
        """Creates an outbox message in the database."""
        try:
            new_message = FilesOutboxOrm(
                message_name=message_name,
                body=body,
                status=FilesOutboxStatusesEnum.PENDING.value,
                traceparent=traceparent,
            )
            self.session.add(new_message)
            return new_message
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании outbox сообщения: {e}")
            raise RepositoryInternalError(
                "Failed to create outbox message due to a database error."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при создании outbox сообщения: {e}")
            raise RepositoryInternalError(
                "Failed to create outbox message due to an unexpected error."
            ) from e

    async def get_one_pending_locked(self):
        stmt = (
            select(FilesOutboxOrm)
            .where(FilesOutboxOrm.status == FilesOutboxStatusesEnum.PENDING.value)
            .order_by(FilesOutboxOrm.created_at_db)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()

    async def mark_as_success(self, message: FilesOutboxOrm):
        message.status = FilesOutboxStatusesEnum.SUCCESS.value
        self.session.add(message)
