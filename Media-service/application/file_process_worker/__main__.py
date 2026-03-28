import asyncio

import uvicorn

from application.di.container import file_processor_container
from application.file_process_worker.worker import FileProcessorWorker
from application.utils.logging import logger


async def run_worker() -> None:
    logger.info("Запуск file process воркера...")
    async with file_processor_container() as request_container:
        worker = await request_container.get(FileProcessorWorker)
        try:
            try:
                await worker.start()
            except asyncio.CancelledError:
                logger.info("File process worker остановлен")
            except Exception as e:
                logger.error(f"Ошибка в file process worker: {e}")
        finally:
            await worker.consumer.close()
            logger.info("File process worker остановлен")


async def run_healh_check() -> None:
    config = uvicorn.Config(
        app="application.file_process_worker.health:app",
        host="0.0.0.0",
        port=18005,
        log_level="info",
    )
    server = uvicorn.Server(config=config)
    await server.serve()


async def main() -> None:
    logger.info("Запуск file process воркера с health-check сервером...")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_worker())
        tg.create_task(run_healh_check())


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("File process worker завершен пользователем")
