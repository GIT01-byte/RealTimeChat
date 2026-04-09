from application.core.chats.schemas.send_message_uc import (
    SendMessageInputDTO,
    SendMessageOutputDTO,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import SendMessagesFailedError
from application.repositories.chat_messages_repo import ChatMessagesRepo
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.chat_messages import ChatMessages
from application.utils.logging import logger


class SendMessageUseCase:
    def __init__(
        self,
        chat_messages_repo: ChatMessagesRepo,
        commiter: Commiter,
    ) -> None:
        self.chat_messages_repo = chat_messages_repo
        self.commiter = commiter

    async def execute(self, data: SendMessageInputDTO):
        try:
            # Добавляем сообщение в БД
            db_message = await self._save_message_db(data)

            return SendMessageOutputDTO(
                message_id=db_message.id,
                sender_id=db_message.sender_id,
                recipient_id=db_message.recipient_id,
                images=db_message.images,
                audios=db_message.audios,
                videos=db_message.videos,
                text=db_message.text,
            )
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Ошибка при отправке сообщения: {e}")
            raise SendMessagesFailedError(detail="Failed to send message.") from e

    async def _save_message_db(self, data: SendMessageInputDTO) -> ChatMessages:
        try:
            db_message = await self.chat_messages_repo.create(
                sender_id=data.sender_id,
                recipient_id=data.recipient_id,
                text=data.text,
                images=data.images,
                audios=data.audios,
                videos=data.videos,
            )
            await self.commiter.commit()
            return db_message
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(f"Ошибка при сохранении сообщения в БД: {e}")
            raise SendMessagesFailedError(
                detail="Failed to save message to database."
            ) from e
