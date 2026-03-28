from dishka import Provider, Scope, provide

from application.file_process_worker.worker import FileProcessorWorker
from application.rabbitmq.consumer import RabbitMQConsumer
from application.repositories.database.commiter import Commiter
from application.repositories.files_repository import FileRepository
from application.repositories.storage.s3.client import S3Client


class FileProcessorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_outbox_worker_service(
        self,
        file_meta_repo: FileRepository,
        s3_client: S3Client,
        commiter: Commiter,
        consumer: RabbitMQConsumer,
    ) -> FileProcessorWorker:
        return FileProcessorWorker(
            file_meta_repo=file_meta_repo,
            s3_client=s3_client,
            commiter=commiter,
            consumer=consumer,
        )
