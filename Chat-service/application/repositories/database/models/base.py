from sqlalchemy import MetaData
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
)

from application.configs.settings import settings
from application.repositories.database.mixins.intpk import intpk


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention=settings.db.naming_convention,
    )

    id: Mapped[intpk]
