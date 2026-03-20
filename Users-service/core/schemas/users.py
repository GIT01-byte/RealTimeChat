import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, EmailStr


class AvatarFileRead(BaseModel):
    model_config = {"from_attributes": True}
    
    uuid: UUID
    s3_url: str
    category: str
    content_type: str


class UserRead(BaseModel):
    model_config = {"from_attributes": True}
    
    id: int
    username: str
    email: Optional[EmailStr] = None
    profile: Optional[Any] = None
    is_active: bool
    role: str
    avatar: List[AvatarFileRead] = []


class UserSelfInfo(BaseModel):
    jwt_payload: JWTPayload
    user_db: UserRead


class JWTPayload(BaseModel):
    sub: str
    exp: datetime
    jti: str
    role: str
    iat: datetime


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
