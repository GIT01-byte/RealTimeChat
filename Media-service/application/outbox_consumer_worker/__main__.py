import asyncio
import sys

import uvicorn

from application.configs.settings import settings
from application.di.container import outbox_consumer_container
from application.outbox_consumer_worker.worker import OutboxConsumerWorker
from application.utils.logging import logger


async def run_worker() -> None:
    logger.info("Запуск outbox consumer worker...")
    async with outbox_consumer_container() as request_container:
        worker = await request_container.get(OutboxConsumerWorker)
        try:
            try:
                await worker.start()
            except asyncio.CancelledError:
                logger.info("Outbox consumer worker остановлен")
            except Exception as e:
                logger.error(f"Ошибка в outbox consumer worker: {e}")
        finally:
            await worker.consumer.close()
            logger.info("Outbox consumer worker остановлен")


async def run_healh_check() -> None:
    config = uvicorn.Config(
        app="application.outbox_consumer_worker.health:app",
        host="0.0.0.0",
        port=18005,
        log_level="info",
    )
    server = uvicorn.Server(config=config)
    await server.serve()


async def main() -> None:
    logger.info("Запуск outbox consumer worker вместе с health-check сервером...")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_worker())
        tg.create_task(run_healh_check())


if __name__ == "__main__":
    if not settings.rabbitmq:
        logger.info("RabbitMQ не настроен, outbox consumer отключён")
        sys.exit(0)
    if not settings.outbox:
        logger.info("Outbox consumer отключён")
        sys.exit(0)
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Outbox consumer worker остановлен пользователем")
