from application.core.use_cases.register_user import RegisterUserUseCase
from application.infrastructure.redis_client import RedisClient
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from application.services.loggout_user_service import LoggoutUserService
from dishka import Provider, Scope, provide


# TODO add provider (use cases)
class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def get_loggout_user_service(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        redis_client: RedisClient,
        commiter: Commiter,
    ) -> LoggoutUserService:
        return LoggoutUserService(
            refresh_tokens_repo=refresh_tokens_repo,
            redis_client=redis_client,
            commiter=commiter,
        )

    @provide(scope=Scope.APP)
    def get_register_user_use_case(
        self,
        users_repo: UsersRepo,
        refresh_tokens_repo: RefreshTokensRepo,
        loggout_user_service: LoggoutUserService,
        commiter: Commiter,
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            users_repo=users_repo,
            refresh_tokens_repo=refresh_tokens_repo,
            loggout_user_service=loggout_user_service,
            commiter=commiter,
        )

    # @provide(scope=Scope.APP)
    # def get_file_processing_use_case(
    #     self,
    #     virus_scanner: ClamavVirusScanner,
    #     file_validator: FileValidator,
    #     file_category_detector: FileCategoryDetector,
    #     file_name_generator: FileMetadataFenerator,
    # ) -> ProcessFileUseCase:
    #     return ProcessFileUseCase(
    #         virus_scanner=virus_scanner,
    #         file_validator=file_validator,
    #         file_category_detector=file_category_detector,
    #         file_meta_generator=file_name_generator,
    #     )

    # @provide(scope=Scope.REQUEST)
    # def get_file_upload_use_case(
    #     self,
    #     s3_client: S3Client,
    #     file_meta_repo: FileRepository,
    #     outbox_repo: FilesOutboxRepository,
    #     commiter: Commiter,
    # ) -> UploadFileUseCase:
    #     return UploadFileUseCase(
    #         s3_client=s3_client,
    #         file_meta_repo=file_meta_repo,
    #         outbox_repo=outbox_repo,
    #         commiter=commiter,
    #     )
    pass
