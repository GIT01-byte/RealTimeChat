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

LOG_PREFIX = "[FilesOutboxRepository]"


class FilesOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_outbox_message(
        self,
        message_name: str,
        body: dict[str, Any] | list[Any],
        traceparent: str | None = None,
    ) -> FilesOutboxOrm | None:
        logger.debug(f"{LOG_PREFIX} Создание outbox сообщения message_name={message_name!r}")
        try:
            new_message = FilesOutboxOrm(
                message_name=message_name,
                body=body,
                status=FilesOutboxStatusesEnum.PENDING.value,
                traceparent=traceparent,
            )
            self.session.add(new_message)
            logger.debug(f"{LOG_PREFIX} Outbox сообщение message_name={message_name!r} добавлено в сессию")
            return new_message
        except SQLAlchemyError as e:
            logger.exception(f"{LOG_PREFIX} Ошибка БД при создании outbox сообщения message_name={message_name!r}")
            raise RepositoryInternalError(
                "Не удалось создать outbox сообщение из-за ошибки базы данных."
            ) from e

    async def get_one_pending_locked(self) -> FilesOutboxOrm | None:
        logger.debug(f"{LOG_PREFIX} Получение одного PENDING сообщения с блокировкой")
        try:
            stmt = (
                select(FilesOutboxOrm)
                .where(FilesOutboxOrm.status == FilesOutboxStatusesEnum.PENDING.value)
                .order_by(FilesOutboxOrm.created_at_db)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            result = await self.session.execute(stmt)
            message = result.scalars().one_or_none()
            if message:
                logger.debug(f"{LOG_PREFIX} Найдено PENDING сообщение id={message.id}")
            else:
                logger.debug(f"{LOG_PREFIX} PENDING сообщений не найдено")
            return message
        except SQLAlchemyError as e:
            logger.exception(f"{LOG_PREFIX} Ошибка БД при получении PENDING сообщения")
            raise RepositoryInternalError(
                "Не удалось получить outbox сообщение из-за ошибки базы данных."
            ) from e

    async def mark_as_success(self, message: FilesOutboxOrm) -> None:
        logger.debug(f"{LOG_PREFIX} Отметка сообщения id={message.id} как SUCCESS")
        message.status = FilesOutboxStatusesEnum.SUCCESS.value
        self.session.add(message)
        logger.debug(f"{LOG_PREFIX} Сообщение id={message.id} отмечено как SUCCESS")
