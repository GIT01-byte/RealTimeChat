from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.files.use_cases.delete_file import DeleteFileUseCase
from application.core.files.use_cases.process_file import ProcessFileUseCase
from application.core.files.use_cases.upload_file import UploadFileUseCase
from application.repositories.database.commiter import Commiter
from application.repositories.files_outbox_repository import FilesOutboxRepository
from application.repositories.files_repository import FileRepository
from application.repositories.storage.s3.client import S3Client
from application.services.file_category_detector import FileCategoryDetector
from application.services.file_name_generator import FileMetadataFenerator
from application.services.file_parser import FileParser
from application.services.file_validator import FileValidator
from application.services.file_virus_scanner import ClamavVirusScanner


class FilesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_virus_scanner(self) -> ClamavVirusScanner:
        return ClamavVirusScanner()

    @provide(scope=Scope.APP)
    def get_file_parser(self) -> FileParser:
        return FileParser()

    @provide(scope=Scope.APP)
    def get_file_validator(self, file_parser: FileParser) -> FileValidator:
        return FileValidator(file_parser=file_parser)

    @provide(scope=Scope.APP)
    def get_category_detector(self) -> FileCategoryDetector:
        return FileCategoryDetector()

    @provide(scope=Scope.APP)
    def get_filename_generator(self) -> FileMetadataFenerator:
        return FileMetadataFenerator()

    @provide(scope=Scope.APP)
    def get_file_processing_use_case(
        self,
        virus_scanner: ClamavVirusScanner,
        file_validator: FileValidator,
        file_category_detector: FileCategoryDetector,
        file_name_generator: FileMetadataFenerator,
    ) -> ProcessFileUseCase:
        return ProcessFileUseCase(
            virus_scanner=virus_scanner,
            file_validator=file_validator,
            file_category_detector=file_category_detector,
            file_meta_generator=file_name_generator,
        )

    @provide(scope=Scope.REQUEST)
    def get_file_upload_use_case(
        self,
        s3_client: S3Client,
        file_meta_repo: FileRepository,
        outbox_repo: FilesOutboxRepository,
        commiter: Commiter,
    ) -> UploadFileUseCase:
        return UploadFileUseCase(
            s3_client=s3_client,
            file_meta_repo=file_meta_repo,
            outbox_repo=outbox_repo,
            commiter=commiter,
        )

    @provide(scope=Scope.REQUEST)
    def delete_file_use_case(
        self,
        s3_client: S3Client,
        file_meta_repo: FileRepository,
        commiter: Commiter,
    ) -> DeleteFileUseCase:
        return DeleteFileUseCase(
            s3_client=s3_client,
            file_meta_repo=file_meta_repo,
            commiter=commiter,
        )


# Create File Metadata Use case provider
