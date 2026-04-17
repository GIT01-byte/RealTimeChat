from exceptions.exceptions import (
    EntityNotFoundError,
    RepositoryInternalError,
    UserAlreadyExistsError,
)
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from utils.logging import logger
from utils.time_decorator import async_timed_report, time_all_methods

from core.db.db_manager import db_manager
from core.models.users import User


@time_all_methods(async_timed_report())
class UsersRepo:
    @staticmethod
    async def create_user(
        username: str,
        hashed_password: bytes,
        avatar: str | None,
        profile: str | None,
    ) -> User:
        logger.debug(f"Попытка создания пользователя с именем: {username!r}")
        try:
            async with db_manager.session_factory() as session:
                existing_user = await session.scalar(
                    select(User).filter(or_(User.username == username))
                )
                if existing_user:
                    logger.warning(
                        f"Пользователь с именем: {username!r} уже существует"
                    )
                    raise UserAlreadyExistsError(
                        f"Пользователь с именем {username!r} уже существует"
                    )

                new_user = User(
                    username=username,
                    hashed_password=hashed_password,
                    avatar=avatar,
                    profile=profile,
                )
                session.add(new_user)

                await session.flush()
                await session.commit()
                await session.refresh(new_user)
                logger.info(
                    f"Пользователь ID:{new_user.id}, Роль: {new_user.role}, Имя: {new_user.username!r} успешно создан."
                )
                return new_user
        except UserAlreadyExistsError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании пользователя {username!r}")
            raise RepositoryInternalError(
                "Не удалось создать пользователя из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании пользователя {username!r}"
            )
            raise RepositoryInternalError(
                "Не удалось создать пользователя из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def select_user_by_user_id(user_id: int) -> User:
        logger.debug(f"Попытка выбрать пользователя по ID: {user_id}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(select(User).where(User.id == user_id))
                if not user:
                    logger.debug(f"Пользователь с ID: {user_id} не найден.")
                    raise EntityNotFoundError(f"Пользователь с ID {user_id} не найден.")
                logger.debug(
                    f"Найден пользователь ID: {user_id}, имя: {user.username!r}, Роль: {user.role}"
                )
                return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при выборе пользователя по ID {user_id}")
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по ID из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при выборе пользователя по ID {user_id}"
            )
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по ID из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def select_user_by_username(username: str) -> User:
        logger.debug(f"Попытка выбрать пользователя по имени: {username!r}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(
                    select(User).where(User.username == username)
                )
                if not user:
                    logger.debug(f"Пользователь с именем: {username!r} не найден.")
                    raise EntityNotFoundError(
                        f"Пользователь с именем {username!r} не найден."
                    )
                logger.debug(
                    f"Найден пользователь с именем: {username!r}, ID: {user.id}, Роль: {user.role}"
                )
                return user
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при выборе пользователя по имени {username!r}")
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по имени из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при выборе пользователя по имени {username!r}"
            )
            raise RepositoryInternalError(
                "Не удалось выбрать пользователя по имени из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_all_users():
        logger.debug("Попытка получить всех пользователей")
        try:
            async with db_manager.session_factory() as session:
                all_users = await session.scalars(select(User))
                users_list = all_users.all()
                logger.debug(f"Получено пользователей: {len(users_list)}")
                return users_list
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при получении всех пользователей")
            raise RepositoryInternalError(
                "Не удалось получить всех пользователей из-за ошибки базы данных"
            ) from e
        except Exception as e:
            logger.exception("Неожиданная ошибка при получении всех пользователей")
            raise RepositoryInternalError(
                "Не удалось получить всех пользователей из-за неожиданной ошибки"
            ) from e

    @staticmethod
    async def get_all_users_data():
        logger.debug("Попытка получить username и avatar всех пользователей")
        try:
            async with db_manager.session_factory() as session:
                all_users_data = await session.scalars(select(User))
                result = all_users_data.all()
                users_data_list = [
                    {"id": user.id, "username": user.username, "avatar": user.avatar}
                    for user in result
                ]
                logger.debug(
                    f"Получено записей username + avatar: {len(users_data_list)}"
                )
                return users_data_list
        except SQLAlchemyError as e:
            logger.exception("Ошибка БД при получении username и avatar пользователей")
            raise RepositoryInternalError(
                "Не удалось получить данные пользователей из-за ошибки базы данных"
            ) from e

    @staticmethod
    async def update_user(
        user_id: int,
        username: str | None = None,
        avatar: str | None = None,
        profile: dict | None = None,
    ) -> User:
        """
        Обновляет данные пользователя. Обновляются только переданные поля (partial update).

        Args:
            user_id: ID пользователя
            username: Новое имя пользователя
            avatar: UUID аватара в виде строки
            profile: Дополнительные данные профиля

        Returns:
            User: Обновлённый объект пользователя

        Raises:
            EntityNotFoundError: Пользователь не найден
            UserAlreadyExistsError: Имя уже занято
            RepositoryInternalError: Ошибка БД
        """
        logger.debug(f"[UsersRepo] Обновление пользователя ID={user_id}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(select(User).where(User.id == user_id))
                if not user:
                    logger.warning(f"[UsersRepo] Пользователь ID={user_id} не найден")
                    raise EntityNotFoundError(f"Пользователь с ID {user_id} не найден")

                if username is not None:
                    existing = await session.scalar(
                        select(User).where(
                            User.username == username, User.id != user_id
                        )
                    )
                    if existing:
                        logger.warning(f"[UsersRepo] Имя {username!r} уже занято")
                        raise UserAlreadyExistsError()
                    user.username = username

                if avatar is not None:
                    user.avatar = avatar

                if profile is not None:
                    user.profile = profile

                await session.commit()
                await session.refresh(user)
                logger.info(
                    f"[UsersRepo] Пользователь ID={user_id} обновлён: "
                    f"username={user.username!r}, avatar={user.avatar}"
                )
                return user
        except (EntityNotFoundError, UserAlreadyExistsError):
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"[UsersRepo] Ошибка БД при обновлении пользователя ID={user_id}"
            )
            raise RepositoryInternalError("Не удалось обновить пользователя") from e
        except Exception as e:
            logger.exception(
                f"[UsersRepo] Неожиданная ошибка при обновлении пользователя ID={user_id}"
            )
            raise RepositoryInternalError("Не удалось обновить пользователя") from e

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Удаляет пользователя из БД.

        Args:
            user_id: ID пользователя

        Raises:
            EntityNotFoundError: Пользователь не найден
            RepositoryInternalError: Ошибка БД
        """
        logger.debug(f"[UsersRepo] Удаление пользователя ID={user_id}")
        try:
            async with db_manager.session_factory() as session:
                user = await session.scalar(select(User).where(User.id == user_id))
                if not user:
                    logger.warning(f"[UsersRepo] Пользователь ID={user_id} не найден")
                    raise EntityNotFoundError(f"Пользователь с ID {user_id} не найден")
                await session.delete(user)
                await session.commit()
                logger.info(f"[UsersRepo] Пользователь ID={user_id} удалён")
        except EntityNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"[UsersRepo] Ошибка БД при удалении пользователя ID={user_id}"
            )
            raise RepositoryInternalError("Не удалось удалить пользователя") from e
        except Exception as e:
            logger.exception(
                f"[UsersRepo] Неожиданная ошибка при удалении пользователя ID={user_id}"
            )
            raise RepositoryInternalError("Не удалось удалить пользователя") from e

    @staticmethod
    async def search_users(search_query: str) -> list[dict]:
        logger.debug(f"Попытка поиска пользователей по шаблону: {search_query!r}")
        try:
            search_pattern = f"%{search_query}%"
            async with db_manager.session_factory() as session:
                users_data = await session.scalars(
                    select(User).filter(User.username.ilike(search_pattern))
                )
                result = users_data.all()
                users_data_list = [
                    {"id": user.id, "username": user.username, "avatar": user.avatar}
                    for user in result
                ]
                logger.debug(
                    f"Найдено пользователей по запросу {search_query!r}: {len(users_data_list)}"
                )
                return users_data_list
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при поиске пользователей по шаблону {search_query!r}"
            )
            raise RepositoryInternalError(
                "Не удалось выполнить поиск пользователей из-за ошибки базы данных"
            ) from e
