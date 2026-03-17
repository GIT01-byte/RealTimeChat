import datetime
from typing import Annotated

from sqlalchemy import DateTime, func
from sqlalchemy.orm import mapped_column

created_at = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False),
]
updated_at = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
]
