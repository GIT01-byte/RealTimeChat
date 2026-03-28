from application.rabbitmq.publisher import RabbitMQPublisher
from application.repositories.database.commiter import Commiter
from application.repositories.database.models.files_outbox import FilesOutboxOrm
from application.repositories.files_outbox_repository import FilesOutboxRepository
from application.utils.logging import logger


class OutboxWorker:
    def __init__(
        self,
        outbox_repository: FilesOutboxRepository,
        commiter: Commiter,
        publisher: RabbitMQPublisher,
        poll_interval: float = 1.0,
    ) -> None:
        self.outbox_repo = outbox_repository
        self.commiter = commiter
        self.publisher = publisher
        self.poll_interval = poll_interval

    async def _process_messages(self) -> None:
        try:
            message = await self.outbox_repo.get_one_pending_locked()

            if not message:
                await self.commiter.commit()
                return

            try:
                await self._publish_message(self.publisher, message)
                await self.outbox_repo.mark_as_success(message)
                await self.commiter.commit()

                logger.info(
                    f"Успешно обработано сообщение из Outbox: ID {message.id}, Type {message.message_name}"
                )
                await self.commiter.commit()

            except Exception as e:
                logger.exception(f"Ошибка при отправке сообщения {message.id}: {e}")
                await self.commiter.rollback()

        except Exception as e:
            logger.exception(f"Необработанная ошибка в _process_messages: {e}")
            await self.commiter.rollback()

    async def _publish_message(
        self, publisher: RabbitMQPublisher, message: FilesOutboxOrm
    ) -> None:
        queue_name = message.message_name
        await publisher.publish(
            queue_name=queue_name,
            message=message.body,
        )
