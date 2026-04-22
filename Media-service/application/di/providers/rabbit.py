# RabbbitMQ - class with Publish, connection, consume
from dishka import Provider, Scope, provide

from application.rabbitmq.consumer import RabbitMQConsumer
from application.rabbitmq.publisher import RabbitMQPublisher
from application.utils.logging import logger


class RabbitProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_rabbimq_publisher(self) -> RabbitMQPublisher:
        try:
            publisher = RabbitMQPublisher()
            await publisher.connect()
            return publisher
        except Exception as e:
            logger.error(f"[RabbitMQ] Publisher failed to connect: {e}")
            raise

    @provide(scope=Scope.APP)
    async def get_rabbimq_consumer(self) -> RabbitMQConsumer:
        try:
            consumer = RabbitMQConsumer()
            await consumer.connect()
            return consumer
        except Exception as e:
            logger.error(f"[RabbitMQ] Consumer failed to connect: {e}")
            raise
