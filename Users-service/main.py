"""
Main application, include fastapi routers and configurate it
"""

import tracemalloc
from contextlib import asynccontextmanager

from api import api_router
from core.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from utils.logging import logger
from utils.middlewares import (
    register_dev_log_middleware,
    register_errors_handlers,
    register_prod_log_middleware,
)

# Включаем отслеживание памяти, для дебага ошибок в ассинхронных функциях
tracemalloc.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    yield
    logger.info("Выключение...")


def create_app() -> FastAPI:
    app = FastAPI(
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    origins = [
        "http://127.0.0.1",
        "http://localhost",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://176.12.67.28",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем обработчики исключений
    register_errors_handlers(app)

    # Подключаем логирование запросов в зависимости от режима запуска
    if settings.app.mode == "PROD":
        logger.info("Start prod logging middleware")
        register_prod_log_middleware(app)
    elif settings.app.mode == "DEV":
        logger.info("Start dev logging middleware")
        register_dev_log_middleware(app)
    else:
        logger.exception(f"[APP] Invalide app mode: {settings.app.mode}")
        raise RuntimeError(f"[APP] Invalide app mode: {settings.app.mode}")

    # Подключаем api роутеры
    app.include_router(api_router)

    # Подключаем prometheus метрики
    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=8002,
        reload=settings.app.mode == "DEV",
        log_level="info",  # TODO add app log level settings
    )
