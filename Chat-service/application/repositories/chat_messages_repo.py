from typing import List

from application.exceptions.exceptions import RepositoryInternalError
from application.repositories.database.models.chat_messages import ChatMessages
from application.utils.logging import logger
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


class ChatMessagesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        sender_id: int,
        recipient_id: int,
        text: str,
        images: List[str] | None,
        audios: List[str] | None,
        videos: List[str] | None,
    ) -> ChatMessages:
        try:
            new_message = ChatMessages(
                sender_id=sender_id,
                recipient_id=recipient_id,
                text=text,
                images=images,
                audios=audios,
                videos=videos,
            )
            self.session.add(new_message)
            return new_message
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при создании сообщения sender_id={sender_id}, recipient_id={recipient_id}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to create message due to a database error."
            ) from e

    async def get_messages_between_users(
        self, user_id_1: int, user_id_2: int
    ) -> list[ChatMessages]:
        try:
            stmt = (
                select(ChatMessages)
                .filter(
                    or_(
                        and_(
                            ChatMessages.sender_id == user_id_1,
                            ChatMessages.recipient_id == user_id_2,
                        ),
                        and_(
                            ChatMessages.sender_id == user_id_2,
                            ChatMessages.recipient_id == user_id_1,
                        ),
                    )
                )
                .order_by(ChatMessages.id)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при получении сообщений между user_id={user_id_1} и user_id={user_id_2}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to get messages due to a database error."
            ) from e
