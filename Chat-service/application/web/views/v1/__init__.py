from fastapi import APIRouter

from application.configs.settings import settings

from .chat import router as chat_router

router = APIRouter(prefix=settings.api.v1.prefix)
router.include_router(
    chat_router,
)
