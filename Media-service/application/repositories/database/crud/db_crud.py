import datetime
from typing import Annotated

from sqlalchemy import ARRAY, DateTime, String
from sqlalchemy.orm import mapped_column
from sqlalchemy_utc import UtcDateTime, utcnow


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[
    datetime.datetime,
    mapped_column(UtcDateTime(), server_default=utcnow(), nullable=False),
]
updated_at = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=utcnow(),
        onupdate=utcnow(),
        nullable=False,
    ),
]
str_256 = Annotated[str, mapped_column(String(256))]
media_url = Annotated[list[str], mapped_column(ARRAY(String), default=[])]
