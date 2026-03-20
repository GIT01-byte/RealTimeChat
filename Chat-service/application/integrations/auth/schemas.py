from datetime import datetime

from pydantic import BaseModel, EmailStr


class RequestUserData(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    is_active: bool
    jti: str
    access_expire: datetime
    iat: datetime
