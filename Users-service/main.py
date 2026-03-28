import tracemalloc
from contextlib import asynccontextmanager

from api import api_router
from core.settings import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from utils.errors_handlers import register_errors_handlers
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
        "http://176.12.67.28",
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
        port=8002,
        reload=settings.app.mode == "DEV",
        log_level="info",
    )
