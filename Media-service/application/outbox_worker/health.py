from typing import Any

from dishka import FromDishka
from dishka.integrations.fastapi import inject, setup_dishka
from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from application.di.container import outbox_worker_container
from application.rabbitmq.publisher import RabbitMQPublisher
from application.utils.logging import logger

app = FastAPI(
    title="Outbox Worker Health Check",
    version="1.0.0",
)

setup_dishka(outbox_worker_container, app)


async def check_database(session: AsyncSession) -> bool:
    try:
        result = await session.execute(text("SELECT 1"))
        return result.scalars().first() == 1
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        return False


async def check_rabbitmq(publisher: RabbitMQPublisher) -> bool:
    try:
        return publisher.is_connected()
    except Exception as e:
        logger.error(f"Ошибка проверки подключения к RabbitMQ: {e}")
        return False


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
@inject
async def ready_check(
    session: FromDishka[AsyncSession],
    publisher: FromDishka[RabbitMQPublisher],
) -> dict[str, Any]:
    database_ok = await check_database(session)
    rabbitmq_ok = await check_rabbitmq(publisher)

    checks = {
        "database": "ok" if database_ok else "failed",
        "rabbitmq": "ok" if rabbitmq_ok else "failed",
    }

    if not (database_ok, rabbitmq_ok):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }
