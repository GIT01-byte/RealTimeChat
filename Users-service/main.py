import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from contextlib import asynccontextmanager
import tracemalloc

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from core.settings import settings
from api import api_router

from prometheus_fastapi_instrumentator import Instrumentator

from errors_handlers import register_errors_handlers

from utils.logging import logger


# Включаем отслеживание памяти, для дебага ошибок с ассинхронными функциями
tracemalloc.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения...")
    yield
    logger.info("Выключение...")


def create_app() -> FastAPI:
    main_app = FastAPI(
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    origins = [
        "http://127.0.0.1",
    ]

    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключаем middleware для просмотра содержимого http запроса
    @main_app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"\n----------- New request -----------")
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Headers: {request.headers}")
        try:
            body = await request.json()
            logger.info(f"Body: {body}\n")
        except Exception as e:
            logger.warning(f"Could not decode JSON body: {e}\n")
        response = await call_next(request)
        return response

    # Подключаем api-роутеры
    main_app.include_router(api_router)
    
    # Подключаем обработчики исключений
    register_errors_handlers(main_app)

    # Подключаем prometheus-метрики
    Instrumentator().instrument(main_app).expose(main_app)

    # Подключаем админ панель
    # setup_admin(app, db_manager.engine)

    return main_app


main_app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:main_app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.mode == "DEV",
        log_level="info",
    )
