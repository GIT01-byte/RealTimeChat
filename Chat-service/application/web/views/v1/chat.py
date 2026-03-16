from dishka.integrations.fastapi import inject
from fastapi import (
    APIRouter,
)
from starlette.websockets import WebSocket

from application.configs.settings import settings

router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])


# class ChatMessage:
#     def __init__(self, author_id: UUID, text: str, time: datetime.datetime) -> None:
#         self.author_id: UUID = author_id
#         self.text: str = text
#         self.time: datetime.datetime = time

# class ChatClient:
#     def __init__(self, name: str, connection: WebSocket) -> None:
#         self.id: UUID = uuid4()
#         self.name: str = name
#         self.connection: WebSocket = connection
#         self.is_connected: bool = True

#     async def connect(self, websocket: WebSocket):
#         self.connection = websocket
#         await websocket.accept()
#         logger.info(f"Client {self.name} connected")

#     async def disconnect(self, websocket: WebSocket):
#         if self.is_connected:
#             self.is_connected = False
#             await websocket.close()
#             logger.info(f"Client {self.name} disconnected")


#     async def accept_msg(self, msg: ChatMessage):
#         if self.is_connected:
#             await self.connection.send_text(msg.text)
#         else:
#             raise Exception("Client is not connected")

#     async def join_room(self, room_id: int):


#     async def leave_room(self, room_id: int):
#         pass


# class ChatRoom:
#     def __init__(self, room_id: int) -> None:
#         self.room_id = room_id
#         self.clients: list[ChatClient] = []
#         self.messages: list[ChatMessage] = []

#     async def add_client(self, client: ChatClient):
#         self.clients.append(client)
#         logger.info(f"Client {client.name} joined room {self.room_id}")

#     async def save_message(self, msg: ChatMessage):
#         self.messages.append(msg)

#     async def broadcast(self, msg: ChatMessage):
#         logger.info(f"[{msg.time}] {msg.author_id}: {msg.text}")
#         self.messages.append(msg)
#         for client in self.clients:
#             await client.accept_msg(msg)


# ----- Основные API ендпоинты -----
@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


@router.websocket("/ws/{room_id}/{client_name}")
@inject
async def ws(websocket: WebSocket, client_name: str):
    """
    1) Принимает websocket соединение
    2) Создает нового клиента
    3) Добавляет клиента в комнату
    4) Передает управление обработчику сообщений
    """
    pass


# ----- Вспомогательные API ендпоинты -----
