import datetime
from typing import Any
from uuid import UUID, uuid4

from dishka.integrations.fastapi import inject
from fastapi import (
    APIRouter,
)
from starlette.websockets import WebSocket

from application.configs.settings import settings
from application.utils.logging import logger

router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])


class ChatMessage:
    def __init__(
        self, author_id: UUID, author_name: str, text: str, time: datetime.datetime
    ) -> None:
        self.author_id: UUID = author_id
        self.author_name: str = author_name
        self.text: str = text
        self.time: datetime.datetime = time


class ChatClient:
    def __init__(self, name: str, connection: WebSocket) -> None:
        self.id: UUID = uuid4()
        self.name: str = name
        self.connection: WebSocket = connection
        self.is_connected: bool = True

    async def connect(self, websocket: WebSocket):
        self.connection = websocket
        await websocket.accept()
        await websocket.send_text(f"Client with ID {self.id} connected")
        logger.info(f"Client {self.name} connected")

    async def disconnect(self, websocket: WebSocket):
        if self.is_connected:
            self.is_connected = False
            await websocket.close()
            logger.info(f"Client {self.name} disconnected")

    async def accept_data(self, data: dict[str, Any]):
        if self.is_connected:
            await self.connection.send_json(data)
        else:
            raise Exception("Client is not connected")


class ChatRoom:
    def __init__(self, room_id: int) -> None:
        self.room_id = room_id
        self.clients: list[ChatClient] = []
        self.messages: list[ChatMessage] = []

    async def create_room(self, client: ChatClient):
        """Создание новой комнаты"""
        self.clients.append(client)
        logger.info(f"Client {client.name} created room {self.room_id}")

    async def add_client(self, client: ChatClient):
        self.clients.append(client)
        logger.info(f"Client {client.name} joined room {self.room_id}")

    async def broadcast(self, msg: ChatMessage):
        logger.info(f"[{msg.time}] {msg.author_id}: {msg.text}")
        self.messages.append(msg)
        for client in self.clients:
            data = {
                "author_id": str(msg.author_id),
                "author_name": msg.author_name,
                "text": msg.text,
                "time": str(msg.time),
            }
            await client.accept_data(data)


class ChatMenager:  # TODO сделать чтобы он отвечал за корректные соединения и подключения комнат и пользователей
    pass


# ----- Основные API ендпоинты -----
@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


@router.websocket("/ws/{room_id}/{client_name}")
@inject
async def ws(websocket: WebSocket, room_id: int, client_name: str):
    """
    1) Принимает websocket соединение
    2) Создает нового клиента
    3) Добавляет клиента в комнату
    4) Передает управление обработчику сообщений
    """
    client = ChatClient(client_name, websocket)
    await client.connect(websocket)
    room = ChatRoom(room_id)
    await room.add_client(client)
    while True:
        data = await websocket.receive_text()
        msg = ChatMessage(client.id, client.name, data, datetime.datetime.now())
        await room.broadcast(msg)


# ----- Вспомогательные API ендпоинты -----
