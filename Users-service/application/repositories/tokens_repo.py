from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from application.exceptions.exceptions import (
    EntityNotFoundError,
    RepositoryInternalError,
)
from application.infrastructure.logging import logger
from core.db.db_manager import db_manager
from core.models.users import RefreshToken


class RefreshTokensRepo:
    @staticmethod
    async def create_refresh_token(
        user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        logger.debug(f"Попытка создания refresh токена для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                token = RefreshToken(
                    user_id=user_id, token_hash=token_hash, expires_at=expires_at
                )
                session.add(token)
                await session.flush()
                await session.commit()
                await session.refresh(token)
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

    @staticmethod
    async def get_refresh_token(token_hash: str) -> Optional[RefreshToken]:
        logger.debug(
            "Попытка получить refresh токен по хэшу (первые 8 символов): %s...",
            token_hash[:8],
        )
        try:
            async with db_manager.session_factory() as session:
                token = await session.scalar(
                    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
                )
                if not token:
                    logger.debug("Refresh токен по заданному хэшу не найден.")
                    raise EntityNotFoundError("Refresh токен не найден.")
                logger.debug(
                    f"Найден refresh токен ID:{token.id} для user_id:{token.user_id}."
                )
                return token
        except EntityNotFoundError:
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

    @staticmethod
    async def invalidate_all_refresh_tokens(user_id: int) -> None:
        logger.debug(f"Попытка аннулировать все refresh токены для user_id: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                query = delete(RefreshToken).where(RefreshToken.user_id == user_id)
                result = await session.execute(query)
                await session.commit()
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

    @staticmethod
    async def delete_refresh_token(token_obj: RefreshToken) -> None:
        logger.debug(f"Попытка удалить refresh токен ID: {token_obj.id}")
        try:
            async with db_manager.session_factory() as session:
                await session.delete(token_obj)
                await session.commit()
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
