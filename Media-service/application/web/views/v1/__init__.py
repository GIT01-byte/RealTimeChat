from fastapi import APIRouter

from application.configs.settings import settings

from .media import router as media_router

router = APIRouter(prefix=settings.api.v1.prefix)
router.include_router(
    media_router,
)
