"""
Main application, include fastapi routers and configurate it
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from application.configs.settings import settings
from application.infrastructure.logging import logger
from application.integrations.http_client import close_http_client, init_http_client
from application.web.middlewares import (
    register_dev_log_middleware,
    register_errors_handlers,
    register_prod_log_middleware,
)
from application.web.views import router as api_router

# Включаем отслеживание памяти, для дебага ошибок в ассинхронных функциях
if settings.app.mode == "DEV":
    import tracemalloc

    tracemalloc.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    await init_http_client()
    yield
    logger.info("Выключение...")
    await close_http_client()


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
