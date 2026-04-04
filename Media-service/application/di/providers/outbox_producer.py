from dishka import Provider, Scope, provide

from application.outbox_producer_worker.worker import OutboxProducerWorker
from application.rabbitmq.publisher import RabbitMQPublisher
from application.repositories.database.commiter import Commiter
from application.repositories.files_outbox_repository import FilesOutboxRepository


class OutboxProducerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_outbox_worker_service(
        self,
        outbox_repository: FilesOutboxRepository,
        commiter: Commiter,
        publisher: RabbitMQPublisher,
    ) -> OutboxProducerWorker:
        return OutboxProducerWorker(
            outbox_repository=outbox_repository,
            commiter=commiter,
            publisher=publisher,
        )
