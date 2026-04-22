from datetime import datetime
from typing import Any, Optional

from fastapi import Form, Request, Response
from pydantic import BaseModel, Field


class RegisterUserUseCaseInput(BaseModel):
    request: Request
    response: Response
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    profile: Optional[str] = Field(None)
    avatar_uuid: Optional[str] = Field(None)


class RegisterUserUseCaseOutput(BaseModel):
    user_id: str
    new_username: str
    role: str
    avatar_uuid: str | None = None


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
