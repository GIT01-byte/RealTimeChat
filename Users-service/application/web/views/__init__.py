from application.configs.settings import settings
from fastapi import APIRouter

from .v1 import router as router_api_v1

router = APIRouter(
    prefix=settings.api.prefix,
    tags=["Users Service"],
)
router.include_router(router_api_v1)
