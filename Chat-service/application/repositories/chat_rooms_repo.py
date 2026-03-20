from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    DataConflictError,
    EntityNotFoundError,
    RepositoryInternalError,
)
from application.repositories.database.models.chat_rooms import ChatRooms
from application.utils.logging import logger


class ChatRoomsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        title: str,
        owner_id: UUID,
        member_uuids: list[UUID],
        messages_uuids: list[UUID],
        description: str | None = None,
    ) -> ChatRooms:
        try:
            new_room = ChatRooms(
                title=title,
                owner_id=owner_id,
                member_uuids=member_uuids,
                messages_uuids=messages_uuids,
                description=description,
            )
            self.session.add(new_room)
            logger.info(f"Комната создана: title={title!r}, owner_id={owner_id}")
            return new_room
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при создании комнаты title={title!r}: {e}")
            raise RepositoryInternalError(
                "Failed to create chat room due to a database error."
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при создании комнаты title={title!r}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to create chat room due to an unexpected error."
            ) from e

    async def add_member(
        self,
        room_uuid: UUID,
        member_uuid: UUID,
    ) -> UUID:
        try:
            result = await self.session.execute(
                select(ChatRooms).where(ChatRooms.uuid == room_uuid)
            )
            room_obj = result.scalar_one_or_none()
            if not room_obj:
                logger.warning(f"Комната не найдена: room_uuid={room_uuid}")
                raise EntityNotFoundError(f"Chat room {room_uuid} not found.")

            if member_uuid in room_obj.members_uuids:
                logger.warning(
                    f"Участник уже в комнате: member_uuid={member_uuid}, room_uuid={room_uuid}"
                )
                raise DataConflictError(
                    f"Member {member_uuid} already exists in room {room_uuid}."
                )

            room_obj.members_uuids.append(member_uuid)
            flag_modified(room_obj, "members_uuids")
            logger.info(
                f"Участник добавлен: member_uuid={member_uuid}, room_uuid={room_uuid}"
            )
            return member_uuid
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при добавлении участника member_uuid={member_uuid} в room_uuid={room_uuid}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to add member due to a database error."
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при добавлении участника member_uuid={member_uuid} в room_uuid={room_uuid}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to add member due to an unexpected error."
            ) from e

    async def get_by_uuid(
        self,
        room_uuid: UUID,
    ) -> ChatRooms:
        try:
            result = await self.session.execute(
                select(ChatRooms).where(ChatRooms.uuid == room_uuid)
            )
            room_obj = result.scalar_one_or_none()
            if not room_obj:
                logger.warning(f"Комната не найдена: room_uuid={room_uuid}")
                raise EntityNotFoundError(f"Chat room {room_uuid} not found.")
            return room_obj
        except BaseAPIException:
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"Ошибка БД при получении комнаты room_uuid={room_uuid}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to get chat room due to a database error."
            ) from e
        except Exception as e:
            logger.exception(
                f"Неожиданная ошибка при получении комнаты room_uuid={room_uuid}: {e}"
            )
            raise RepositoryInternalError(
                "Failed to get chat room due to an unexpected error."
            ) from e

    async def get_all_rooms(self) -> list[ChatRooms]:
        try:
            result = await self.session.execute(select(ChatRooms))
            rooms_list = result.scalars().all()
            return list(rooms_list)
        except SQLAlchemyError as e:
            logger.exception(f"Ошибка БД при получении списка комнат: {e}")
            raise RepositoryInternalError(
                "Failed to get chat rooms due to a database error."
            ) from e
        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении списка комнат: {e}")
            raise RepositoryInternalError(
                "Failed to get chat rooms due to an unexpected error."
            ) from e
