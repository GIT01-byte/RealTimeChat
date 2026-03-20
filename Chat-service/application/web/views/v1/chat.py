import asyncio
from typing import List

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from application.configs.settings import settings
from application.core.chats.schemas.files import (
    ChatMessageCreate,
    ChatMessageRead,
)
from application.integrations.auth.auth import get_current_user
from application.integrations.auth.schemas import UserData
from application.repositories.chat_messages_repo import ChatMessagesRepo

router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])

active_connections: dict[int, WebSocket] = {}


# ----- Основные API ендпоинты -----
@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


# Страница чата
@router.get("/", summary="Chat Page")
async def get_chat_page(
    request: Request, user_data: UserData = Depends(get_current_user)
):
    users_all = ...  # TODO Users Repo get all users
    return {
        "page": "Чат",
        "user_data": user_data,
        "users_all": users_all,
    }  # TODO return template_response (Jinja)


@router.post("/messages", response_model=ChatMessageCreate)
async def send_message(
    session: FromDishka[AsyncSession],
    message: ChatMessageCreate,
    current_user: UserData = Depends(get_current_user),
):
    messages_repo = ChatMessagesRepo(session=session)
    # Add new message to the database
    await messages_repo.create(
        sender_id=current_user.user_id,
        recipient_id=message.recipient_id,
        text=message.text,
    )

    return {
        "recipient_id": message.recipient_id,
        "text": message.text,
        "status": "ok",
        "msg": "Message saved!",
    }


@router.get("/messages/{user_id}", response_model=List[ChatMessageRead])
async def get_messages(
    session: FromDishka[AsyncSession],
    user_id: int,
    current_user: UserData = Depends(get_current_user),
):
    messages_repo = ChatMessagesRepo(session=session)
    return (
        await messages_repo.get_messages_between_users(
            user_id_1=user_id, user_id_2=current_user.user_id
        )
        or []
    )


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    Вебсокет для активного подкючения к серверу
    по id активного пользователя

    Args:
        websocket (WebSocket): вебсокет подлкючение
        user_id (int): ID пользователя прошедший авторизацию
    """
    await websocket.accept()
    active_connections[user_id] = websocket
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)


# ----- Вспомогательные API ендпоинты -----


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
