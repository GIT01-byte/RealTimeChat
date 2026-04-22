from dishka import Provider, Scope, provide

from application.configs.settings import settings
from application.repositories.storage.s3.client import S3Client


class S3Provider(Provider):
    @provide(scope=Scope.APP)
    def get_s3_client(self) -> S3Client:
        return S3Client(
            access_key=settings.s3.accesskey,
            secret_key=settings.s3.secretkey,
            endpoint_url=settings.s3.endpointurl,
            bucket_name=settings.s3.bucketname,
        )
