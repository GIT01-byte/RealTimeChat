# Main app, include fastapi routers ...
import tracemalloc
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from application.di.containers import chat_api_container
from application.utils.errors_handlers import register_errors_handlers
from application.utils.logging import logger
from application.web.views.v1.media import router as api_router

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
        "http://127.0.0.1",  # TODO сдеалть загрузку из env переменных
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
        logger.info("\n----------- New request -----------")
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Headers: {request.headers}")
        try:
            body = await request.json()
            logger.info(f"Body: {body}\n")
        except Exception as e:
            logger.warning(f"Could not decode JSON body: {e}\n")
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
