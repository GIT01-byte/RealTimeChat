import json
from typing import Any

import aio_pika

from application.configs.settings import settings


class RabbitMQPublisher:
    def __init__(self):
        self.url = settings.rabbitmq.RABBITMQ_URL
        self.connection = None
        self.channel = None

    async def connect(self):
        # 1. Создаем подключение и канал с подтверждениями
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        # Включаем подтверждения для надежности [1]
        await self.channel.set_qos(prefetch_count=10)

    async def publish(self, queue_name: str, message: dict[str, Any] | list[Any]):
        if not self.channel:
            await self.connect()

        # 2. Сериализация и отправка
        assert self.channel is not None
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )
        print(f"Sent: {message}")

    async def close(self):
        """Закрывает соединение."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    def is_connected(self) -> bool:
        """Проверяет, подключено ли устройство."""
        return self.connection is not None and not self.connection.is_closed
