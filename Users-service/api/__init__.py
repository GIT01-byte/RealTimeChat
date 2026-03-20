from fastapi import APIRouter

from . import authentication

api_router = APIRouter()

api_router.include_router(authentication.auth, tags=["Auth"], prefix="/users") # type: ignore
api_router.include_router(authentication.auth_usage, tags=["Usage"], prefix="/users") # type: ignore
api_router.include_router(authentication.dev_usage, tags=["Dev usage"], prefix="/users") # type: ignore
