from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    EntityNotFoundError,
    RepositoryInternalError,
)
from application.infrastructure.logging import logger
from application.repositories.database.models.users import RefreshToken

LOG_PREFIX = "[RefreshTokensRepo]"


class RefreshTokensRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_refresh_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        logger.debug(f"Попытка создания refresh токена для user_id: {user_id}")
        try:
            token = RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            self.session.add(token)
            logger.info(
                f"Refresh токен ID:{token.id} для user_id:{user_id} успешно создан."
            )
            return token
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при создании refresh токена для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось создать refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании refresh токена для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось создать refresh токен из-за неожиданной ошибки"
            ) from e

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        logger.debug(
            "Попытка получить refresh токен по хэшу (первые 8 символов): %s...",
            token_hash[:8],
        )
        try:
            token = await self.session.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            if not token:
                logger.debug("Refresh токен по заданному хэшу не найден.")
                raise EntityNotFoundError("Refresh токен не найден.")
            logger.debug(
                f"Найден refresh токен ID:{token.id} для user_id:{token.user_id}."
            )
            return token
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при получении refresh токена (хэш: {token_hash[:8]}...)"
            )
            raise RepositoryInternalError(
                "Не удалось получить refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении refresh токена (хэш: {token_hash[:8]}...)"
            )
            raise RepositoryInternalError(
                "Не удалось получить refresh токен из-за неожиданной ошибки"
            ) from e

    async def invalidate_all_refresh_tokens(self, user_id: int) -> None:
        logger.debug(f"Попытка аннулировать все refresh токены для user_id: {user_id}")
        try:
            query = delete(RefreshToken).where(RefreshToken.user_id == user_id)
            result = await self.session.execute(query)

            logger.info(
                f"Аннулировано {result.rowcount} refresh токенов для user_id: {user_id}"  # type: ignore
            )  # type: ignore
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при аннулировании refresh токенов для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось аннулировать refresh токены из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при аннулировании refresh токенов для user_id {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось аннулировать refresh токены из-за неожиданной ошибки"
            ) from e

    async def delete_refresh_token(self, token_obj: RefreshToken) -> None:
        logger.debug(f"Попытка удалить refresh токен ID: {token_obj.id}")
        try:
            await self.session.delete(token_obj)
            logger.info(f"Удален refresh токен ID: {token_obj.id}")
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при удалении refresh токена ID: {token_obj.id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить refresh токен из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при удалении refresh токена ID: {token_obj.id}"
            )
            raise RepositoryInternalError(
                "Не удалось удалить refresh токен из-за неожиданной ошибки"
            ) from e
