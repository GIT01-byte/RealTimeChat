from datetime import datetime

from pydantic import BaseModel


class UserData(BaseModel):
    id: int
    username: str
    is_active: bool
    jti: str
    access_expire: datetime
    iat: datetime


ACCESS_EXPIRE_NAME = "expire"
ACCESS_ISSUED_AT_NAME = "iat"
