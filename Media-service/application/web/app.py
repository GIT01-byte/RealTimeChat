"""
Main application, include fastapi routers and configurate it
"""

import tracemalloc
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from application.configs.settings import settings
from application.di.container import file_api_container
from application.utils.logging import logger
from application.utils.middlewares import (
    register_dev_log_middleware,
    register_errors_handlers,
    register_prod_log_middleware,
)
from application.web.views import router as api_router

# Включаем отслеживание памяти, для дебага ошибок в ассинхронных функциях
tracemalloc.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    yield
    logger.info("Выключение...")


def create_app() -> FastAPI:
    app = FastAPI(
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

    # Инитиализируеум dishka
    setup_dishka(file_api_container, app)

    # Подключаем api роутеры
    app.include_router(api_router)

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

    # Подключаем prometheus метрики
    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
