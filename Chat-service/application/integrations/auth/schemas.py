from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserData(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    jti: str
    access_expire: datetime
    iat: datetime
