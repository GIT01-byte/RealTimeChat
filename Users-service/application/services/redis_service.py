from application.configs.settings import settings
from application.exceptions.base import BaseAPIException
from application.infrastructure.logging import logger
from application.infrastructure.redis_client import RedisClient


class RedisService:
    def __init__(
        self,
        redis_client: RedisClient,
    ) -> None:
        self.redis_client = redis_client

    async def set_redis_blacklist(self, access_jti: str) -> None:
        try:
            redis_conn = await self.redis_client.get_redis_client()

            ttl = settings.jwt.access_token_expire_minutes * 60
            await redis_conn.setex(f"blacklist:access:{access_jti}", ttl, "1")

            logger.debug(f"Успешно установлен Redis blacklist: {access_jti}")
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Failed to set Redis blacklist: {str(e)}")
            raise

    async def set_revoked_token(self, jti: str, expire: int) -> None:
        try:
            redis_conn = await self.redis_client.get_redis_client()

            await redis_conn.setex(f"revoked:{jti}", expire, "1")

            logger.debug(f"Успешно установлен Redis revoked token: {jti}")
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"Failed to set Redis revoked token: {str(e)}")
            raise
