from uuid import UUID, uuid4

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.websockets import WebSocket

from application.configs.settings import settings
from application.core.chats.schemas.files import ChatClient, ChatMessage
from application.repositories.chat_messages_repo import ChatMessagesRepo
from application.utils.logging import logger

router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])


# ----- Основные API ендпоинты -----
@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


class RoomConnection:
    """ "
    Класс активных подключений к комнате
    """

    def __init__(self, room_id: UUID) -> None:
        self.active_connections: dict[UUID, WebSocket] = {}
        self.room_id = room_id

    async def add_client(self, client: ChatClient):
        """Подключение клиента к комнате"""
        await client.websocket.accept()
        self.active_connections[client.client_id] = client.websocket

    async def remove_client(self, client_id: UUID):
        """Отключение клиента от комнаты"""
        del self.active_connections[client_id]

    def get_all_connections(self):
        return list(self.active_connections.values())

    async def broadcast(self, message: ChatMessage):
        for client in self.active_connections.values():
            await client.send_json(data=message.model_dump(mode="json"))


@router.websocket("/ws/{room_id}/{client_name}")
async def ws(
    websocket: WebSocket,
    room_id: UUID,
    client_name: str,
):
    client_id = uuid4()
    client = ChatClient(
        client_id=client_id, client_name=client_name, websocket=websocket
    )
    room = RoomConnection(room_id)
    await room.add_client(client)
    logger.info(f"Клиент {client_name} подключился к комнате {room_id}")

    session_maker: async_sessionmaker[AsyncSession] = websocket.app.state.session_maker
    async with session_maker() as session:
        chat_messages_repo = ChatMessagesRepo(session=session)
        while True:
            data = await websocket.receive_text()
            msg_db = await chat_messages_repo.create(
                author_id=client.client_id, room_id=room_id, text=data
            )
            await session.commit()
            msg = ChatMessage(
                author_id=msg_db.author_id,
                author_name=client_name,
                text=msg_db.text,
                time=msg_db.created_at,
            )
            await room.broadcast(msg)


# ----- Вспомогательные API ендпоинты -----
