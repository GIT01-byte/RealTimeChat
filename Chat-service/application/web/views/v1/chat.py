from dishka.integrations.fastapi import FromDishka, inject
from fastapi import (
    APIRouter,
)

from application.configs.settings import settings
from application.utils.logging import logger


router = APIRouter(prefix=settings.api.v1.service, tags=["Real Time Chat"])

# ----- Основные API ендпоинты -----


@router.get("/health_check/")
async def health_check():
    return {"success": "Сервис Real-Time чата запущен"}


# ----- Вспомогательные API ендпоинты -----
