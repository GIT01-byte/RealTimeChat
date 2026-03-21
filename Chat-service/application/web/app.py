# Main app, include fastapi routers ...
import tracemalloc
from contextlib import asynccontextmanager

from application.di.containers import chat_api_container
from application.utils.errors_handlers import register_errors_handlers
from application.utils.logging import logger
from application.web.views.v1.chat import router as api_router
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

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
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем middleware для просмотра содержимого http запроса
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Новый запрос: {request.method} {request.url}")
        response = await call_next(request)
        return response

    # Инитиализируеум dishka
    setup_dishka(chat_api_container, app)

    # Подключаем api роутеры
    app.include_router(api_router)

    # Подключаем обработчики исключений
    register_errors_handlers(app)

    return app


app = create_app()
