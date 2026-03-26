import asyncio

from application.configs.settings import settings
from application.core.chats.schemas.messages import (
    ChatMessageCreate,
)
from application.core.chats.schemas.send_message_uc import SendMessageInputDTO
from application.core.chats.use_cases.send_message import SendMessageUseCase
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    GetMessagesBetweenUsersFailedError,
    SendMessagesFailedError,
)
from application.integrations.auth.auth import get_current_user, get_users
from application.integrations.auth.schemas import UserData
from application.repositories.chat_messages_repo import ChatMessagesRepo
from application.utils.logging import logger
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])

active_connections: dict[int, WebSocket] = {}


# Функция для отправки сообщения пользователю, если он подключен
async def notify_user(user_id: int, message: dict):
    websocket = active_connections.get(user_id)
    if not websocket:
        return
    try:
        await websocket.send_json(message)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        logger.debug(f"Пользователь {user_id} отключился во время отправки сообщения")
    except Exception as e:
        await websocket.close()
        active_connections.pop(user_id, None)
        logger.exception(f"WebSocket error: {e}")


# ----- Основные API ендпоинты -----
@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


@router.get("/")
@inject
async def get_chat(user_data: UserData = Depends(get_current_user)):
    logger.info(f"Получен запрос на получение чата для пользователя {user_data}")
    users_all = await get_users()
    users_online = {
        user["id"]: True
        for user in users_all["users"]
        if user["id"] in active_connections
    }
    return {
        "user_data": user_data,
        "users_all": users_all["users"],
        "users_online": users_online,
    }


@router.post("/messages")
@inject
async def send_message(
    send_message_uc: FromDishka[SendMessageUseCase],
    message: ChatMessageCreate,
    current_user: UserData = Depends(get_current_user),
):
    try:
        send_message_data = SendMessageInputDTO(
            sender_id=current_user.id,
            recipient_id=message.recipient_id,
            text=message.text,
        )
        send_message_output = await send_message_uc.execute(data=send_message_data)

        # Формируем данные сообщения для отправки
        message_data = {
            "sender_id": send_message_output.sender_id,
            "recipient_id": send_message_output.recipient_id,
            "text": send_message_output.text,
        }

        # Уведомляем получателя и отправителя через WebSocket
        await notify_user(send_message_output.recipient_id, message_data)
        await notify_user(send_message_output.sender_id, message_data)

        return {
            "recipient_id": send_message_output.recipient_id,
            "text": send_message_output.text,
            "status": "ok",
            "msg": "Message saved!",
        }
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при отправке сообщения: {e}")
        raise SendMessagesFailedError from e


@router.get("/messages/{user_id}")
@inject
async def get_messages(
    session: FromDishka[AsyncSession],
    user_id: int,
    current_user: UserData = Depends(get_current_user),
):
    try:
        messages_repo = ChatMessagesRepo(session=session)
        messages = await messages_repo.get_messages_between_users(
            user_id_1=user_id, user_id_2=current_user.id
        )
        return {"data": messages}
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при получении сообщений user_id={user_id}: {e}")
        raise GetMessagesBetweenUsersFailedError from e


@router.websocket("/ws/{user_id}")
@inject
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    Вебсокет для активного подкючения к серверу
    по id активного пользователя

    Args:
        websocket (WebSocket): вебсокет подлкючение
        user_id (int): ID пользователя прошедший авторизацию
    """
    try:
        await websocket.accept()
        active_connections[user_id] = websocket
        logger.info(f"Пользователь {user_id} подключился")
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
        logger.info(f"Пользователь {user_id} отключился")
    except Exception as e:
        await websocket.close()
        active_connections.pop(user_id, None)
        logger.exception(f"WebSocket error: {e}")


# ----- Вспомогательные API ендпоинты -----
@router.websocket("/test/ws")
async def test_websocket_endpoint(websocket: WebSocket):
    """Test websocket endpoint"""
    print(f"Websocket connection: {websocket}")
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        print(f"WebSocket disconnect: {e}")
    except Exception as e:
        print(f"Websocket exception: {e}")


# ----- Старый код для удобного обращения -----

# class RoomConnection:
#     """ "
#     Класс активных подключений к комнате
#     """

#     def __init__(self, room_id: UUID) -> None:
#         self.active_connections: dict[UUID, WebSocket] = {}
#         self.room_id = room_id

#     async def add_client(self, client: ChatClient):
#         """Подключение клиента к комнате"""
#         await client.websocket.accept()
#         self.active_connections[client.client_id] = client.websocket

#     async def remove_client(self, client_id: UUID):
#         """Отключение клиента от комнаты"""
#         del self.active_connections[client_id]

#     def get_all_connections(self):
#         return list(self.active_connections.values())

#     async def broadcast(self, message: ChatMessage):
#         for client in self.active_connections.values():
#             await client.send_json(data=message.model_dump(mode="json"))


# @router.websocket("/ws/{room_id}/{client_name}")
# async def ws(
#     websocket: WebSocket,
#     room_id: UUID,
#     client_name: str,
# ):
#     client = ChatClient(client_id=uuid4(), client_name=client_name, websocket=websocket)
#     room = RoomConnection(room_id)
#     await room.add_client(client)
#     logger.info(f"Client {client_name!r} connected to room {room_id}")

#     session_maker: async_sessionmaker[AsyncSession] = websocket.app.state.session_maker
#     try:
#         async with session_maker() as session:
#             chat_messages_repo = ChatMessagesRepo(session=session)
#             while True:
#                 data = await websocket.receive_text()
#                 msg_db = await chat_messages_repo.create(
#                     author_id=client.client_id, room_id=room_id, text=data
#                 )
#                 await session.commit()
#                 await room.broadcast(
#                     ChatMessage(
#                         author_id=msg_db.author_id,
#                         author_name=client_name,
#                         text=msg_db.text,
#                         time=msg_db.created_at,
#                     )
#                 )
#     except WebSocketDisconnect:
#         await room.remove_client(client.client_id)
#         logger.info(f"Client {client_name!r} disconnected from room {room_id}")
#     except Exception as e:
#         logger.exception(
#             f"Unexpected error in ws handler client={client_name!r} room={room_id}: {e}"
#         )
#         await websocket.close()
