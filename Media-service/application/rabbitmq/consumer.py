import json
from typing import Callable, Awaitable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from application.configs.settings import settings
from application.utils.logging import logger


class RabbitMQConsumer:
    def __init__(self):
        self.url = settings.rabbitmq.RABBITMQ_URL
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)

    async def consume(
        self,
        queue_name: str,
        callback_func: Callable[[dict], Awaitable[None]],
    ):
        """Запускает прослушивание очереди."""
        if not self.channel:
            await self.connect()

        async def callback(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    logger.info(f"[RabbitMQ] Received message from {queue_name}")
                    await callback_func(body)  # pyright: ignore[reportGeneralTypeIssues]
                except json.JSONDecodeError as e:
                    logger.error(f"[RabbitMQ] JSON decode error: {e}")
                    raise
                except Exception as e:
                    logger.exception(f"[RabbitMQ] Error processing message: {e}")
                    raise

        assert self.channel is not None
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.consume(callback=callback)
        logger.info(f"[RabbitMQ] Started consuming from {queue_name}")

    async def close(self):
        """Закрывает соединение."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    def is_connected(self) -> bool:
        """Проверяет, подключено ли устройство."""
        return self.connection is not None and not self.connection.is_closed
