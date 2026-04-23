from application.core.use_cases.refresh_tokens import RefreshTokensUseCase
from application.core.use_cases.register_user import RegisterUserUseCase
from application.infrastructure.redis_client import RedisClient
from application.repositories.database.commiter import Commiter
from application.repositories.refresh_tokens_repo import RefreshTokensRepo
from application.repositories.users_repo import UsersRepo
from application.services.redis_service import RedisService
from application.services.tokens_service import TokensService
from application.services.users_service import UsersService
from dishka import Provider, Scope, provide


# TODO add provider (use cases)
class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def get_users_service(
        self,
        tokens_service: TokensService,
        redis_service: RedisService,
        users_repo: UsersRepo,
        commiter: Commiter,
    ) -> UsersService:
        return UsersService(
            tokens_service=tokens_service,
            redis_service=redis_service,
            users_repo=users_repo,
            commiter=commiter,
        )

    @provide(scope=Scope.APP)
    def get_tokens_service(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        commiter: Commiter,
    ) -> TokensService:
        return TokensService(
            refresh_tokens_repo=refresh_tokens_repo,
            commiter=commiter,
        )

    @provide(scope=Scope.APP)
    def get_redis_service(
        self,
        redis_client: RedisClient,
    ) -> RedisService:
        return RedisService(
            redis_client=redis_client,
        )

    @provide(scope=Scope.APP)
    def get_register_user_use_case(
        self,
        users_repo: UsersRepo,
        users_service: UsersService,
        commiter: Commiter,
    ) -> RegisterUserUseCase:
        return RegisterUserUseCase(
            users_repo=users_repo,
            users_service=users_service,
            commiter=commiter,
        )

    @provide(scope=Scope.APP)
    def get_refresh_tokens_use_case(
        self,
        refresh_tokens_repo: RefreshTokensRepo,
        tokens_service: TokensService,
        users_service: UsersService,
        commiter: Commiter,
    ) -> RefreshTokensUseCase:
        return RefreshTokensUseCase(
            refresh_tokens_repo=refresh_tokens_repo,
            tokens_service=tokens_service,
            users_service=users_service,
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
