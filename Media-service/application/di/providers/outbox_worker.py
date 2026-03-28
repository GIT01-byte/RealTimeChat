from dishka import Provider, Scope, provide

from application.outbox_worker.worker import OutboxWorker
from application.rabbitmq.publisher import RabbitMQPublisher
from application.repositories.database.commiter import Commiter
from application.repositories.files_outbox_repository import FilesOutboxRepository


class OutboxWorkerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_outbox_worker_service(
        self,
        outbox_repository: FilesOutboxRepository,
        commiter: Commiter,
        publisher: RabbitMQPublisher,
    ) -> OutboxWorker:
        return OutboxWorker(
            outbox_repository=outbox_repository,
            commiter=commiter,
            publisher=publisher,
        )
