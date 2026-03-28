from dishka import make_async_container

from application.di.providers.databases import DatabaseProvider
from application.di.providers.file_processor import FileProcessorProvider
from application.di.providers.files_api import FilesProvider
from application.di.providers.outbox_worker import OutboxWorkerProvider
from application.di.providers.rabbit import RabbitProvider
from application.di.providers.repositories import RepositoryProvider
from application.di.providers.s3 import S3Provider

file_api_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    S3Provider(),
    FilesProvider(),
)
outbox_worker_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    RabbitProvider(),
    OutboxWorkerProvider(),
)
file_processor_container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    RabbitProvider(),
    S3Provider(),
    FileProcessorProvider(),
)
