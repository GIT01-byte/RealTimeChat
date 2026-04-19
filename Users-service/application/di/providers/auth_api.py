from dishka import Provider


# TODO add provider (use cases)
class AuthProvider(Provider):
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
