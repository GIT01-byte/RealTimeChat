from typing import Annotated
from uuid import UUID

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column

list_obj_uuids = Annotated[
    list[UUID], mapped_column(JSONB, nullable=False, default=list)
]
