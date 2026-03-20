import datetime
from typing import Annotated, List

from sqlalchemy import ARRAY, DateTime, String, func
from sqlalchemy.orm import mapped_column


str_64 = Annotated[str, 64]
str_128 = Annotated[str, 128]
intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime.datetime, mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)]
updated_at = Annotated[datetime.datetime, mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)]
