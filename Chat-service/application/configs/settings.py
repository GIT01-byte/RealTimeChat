from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_PATH = Path(__file__).parent.parent.parent
ENV_PATH = BASE_PATH / ".env"


class AppConfig(BaseModel):
    name: str = "Real_Time_Chat"
    mode: str
    host: str = "0.0.0.0"
    port: int = 8001


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    service: str = "/real_time_chat"


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


class RedisSettings(BaseModel):
    host: str
    port: int

    @property
    def REDIS_URL(self):
        return f"redis://{self.host}:{self.port}/1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        case_sensitive=False,
        env_nested_delimiter="_",
        env_prefix="RTCHAT_",
    )
    app: AppConfig
    api: ApiPrefix = ApiPrefix()
    db: DatabaseSettings
    redis: RedisSettings


settings = Settings()  # type: ignore
if settings:
    print()
    print(f"-------- {settings.app.name} --------")
    print(f"INFO:     Run mode: {settings.app.mode}")
    print(f"INFO:     Database url: {settings.db.DB_URL_asyncpg}")
    print(f"INFO:     Redis url: {settings.redis.REDIS_URL}")
    print("-------------------------------------")
    print()
else:
    raise
