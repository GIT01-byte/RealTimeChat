from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).parent.parent.parent
ENV_PATH = BASE_PATH / ".env"


class AppConfig(BaseModel):
    name: str = "Media_Service"
    mode: str
    host: str = "0.0.0.0"
    port: int = 8003


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    service: str = "/media_service"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class DatabaseSettings(BaseModel):
    # DB URL
    host: str
    port: int
    user: str
    pwd: str
    name: str
    # Other DB settings
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @property
    def DB_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.name}"


class S3Settings(BaseModel):
    accesskey: str
    secretkey: str
    endpointurl: str
    bucketname: str


class RabbitMQSettings(BaseModel):
    host: str = "localhost"
    port: int = 55672
    login: str = "quest"
    password: str = "quest"

    @property
    def RABBITMQ_URL(self):
        return f"amqp://{self.login}:{self.password}@{self.host}:{self.port}/"


class OutboxSettings(BaseModel):
    enabled: bool = True
    poll_interval: float = 1.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        case_sensitive=False,
        env_nested_delimiter="_",
        env_prefix="MEDIA_",
    )
    app: AppConfig
    api: ApiPrefix = ApiPrefix()
    db: DatabaseSettings
    s3: S3Settings
    rabbitmq: RabbitMQSettings
    outbox: OutboxSettings


settings = Settings()  # type: ignore
if settings:
    print()
    print(f"-------- {settings.app.name} --------")
    print(f"INFO:     Host-port: {settings.app.host}:{settings.app.port}")
    print(f"INFO:     Run mode: {settings.app.mode}")
    print(f"INFO:     Database url: {settings.db.DB_URL_asyncpg}")
    print(f"INFO:     S3 url: {settings.s3.endpointurl}/{settings.s3.bucketname}")
    print(f"INFO:     RabbitMQ url: {settings.rabbitmq.RABBITMQ_URL}")
    print("-------------------------------------")
    print()
else:
    raise
