from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from application.exceptions.exceptions import RepositoryInternalError
from application.repositories.database.models.chat_messages import ChatMessages
from application.utils.logging import logger


class ChatMessagesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        author_id: UUID,
        room_id: UUID,
        text: str,
    ) -> ChatMessages:
        try:
            new_message = ChatMessages(
                author_id=author_id,
                room_id=room_id,
                text=text,
            )
            self.session.add(new_message)
            return new_message
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при создании сообщения author_id={author_id}, room_id={room_id}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to create message due to a database error."
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании сообщения author_id={author_id}, room_id={room_id}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to create message due to an unexpected error."
            ) from e
