from pathlib import Path

from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent
DOTENV_FILE_PATH = BASE_DIR / ".env"


class AppSettings(BaseModel):
    name: str = "Users_Service"
    mode: str
    host: str = "0.0.0.0"
    port: int = 8002
    enable_time_reports: bool = False


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    service: str = "/users_service"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class JwtAuth(BaseModel):
    model_config = ConfigDict(strict=True)

    private_key_path: Path = BASE_DIR / "keys" / "private_key.pem"
    public_key_path: Path = BASE_DIR / "keys" / "public_key.pem"
    algorithm: str = "EdDSA"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 60 * 24 * 30


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
        env_file=str(DOTENV_FILE_PATH),
        case_sensitive=False,
        env_nested_delimiter="_",
        env_prefix="USERS_",
    )

    app: AppSettings
    api: ApiPrefix = ApiPrefix()
    jwt: JwtAuth = JwtAuth()
    db: DatabaseSettings
    redis: RedisSettings


settings = Settings()  # type: ignore

print()
print(f"-------- {settings.app.name} --------")
print(f"Run mode: {settings.app.mode}")
print(f"DB URL: {settings.db.DB_URL_asyncpg}")
print(f"Redis URL: {settings.redis.REDIS_URL}")
print(f"JWT Algorithm: {settings.jwt.algorithm}")
print("-------------------------------")
print()
