import asyncio

import uvicorn

from application.di.container import outbox_worker_container
from application.outbox_worker.worker import OutboxWorker
from application.utils.logging import logger


async def run_worker() -> None:
    logger.info("Запуск outbox воркера...")
    async with outbox_worker_container() as request_container:
        worker = await request_container.get(OutboxWorker)
        try:
            while True:
                try:
                    await worker._process_messages()
                except asyncio.CancelledError:
                    logger.info("Outbox worker остановлен")
                    break
                except Exception as e:
                    logger.error(f"Ошибка в outbox worker: {e}")
                await asyncio.sleep(worker.poll_interval)
        finally:
            await worker.publisher.close()
            logger.info("Outbox worker остановлен")


async def run_healh_check() -> None:
    config = uvicorn.Config(
        app="application.outbox_worker.health:app",
        host="0.0.0.0",
        port=18004,
        log_level="info",
    )
    server = uvicorn.Server(config=config)
    await server.serve()


async def main() -> None:
    logger.info("Запуск outbox воркера с health-check сервером...")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_worker())
        tg.create_task(run_healh_check())


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Outbox worker завершен пользователем")
