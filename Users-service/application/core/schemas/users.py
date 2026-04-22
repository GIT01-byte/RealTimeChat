from datetime import datetime
from typing import Any

from fastapi import Form
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    avatar: str | None = None
    profile: Any | None = None


class UserUpdate(BaseModel):
    username: str | None = None
    avatar: str | None = None
    profile: Any | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    avatar: str | None = None
    profile: Any | None = None
    is_active: bool
    role: str


class JWTPayload(BaseModel):
    sub: str
    exp: datetime
    jti: str
    role: str
    iat: datetime


class UserSelfInfo(BaseModel):
    jwt_payload: JWTPayload
    user_db: UserRead


class AccessToken(BaseModel):
    token: str
    expire: datetime


class TokenResponse(BaseModel):
    access_token: str
    access_expire: datetime
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    login: str = Form()
    password: str = Form()
