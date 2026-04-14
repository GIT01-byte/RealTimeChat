"""Recreate avatar cloumn in users model

Revision ID: 0d8b0cdeecc8
Revises: 987f0f1dcc27
Create Date: 2026-04-14 15:46:12.583917

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0d8b0cdeecc8"
down_revision: Union[str, Sequence[str], None] = "987f0f1dcc27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_avatar_uuid"), table_name="avatar")
    op.drop_table("avatar")
    op.add_column("users", sa.Column("avatar", sa.Uuid(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "avatar")
    op.create_table(
        "avatar",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "user_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column("uuid", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "s3_url",
            sa.VARCHAR(length=512),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "content_type",
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "uploaded_at_s3", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("avatar_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("avatar_pkey")),
        sa.UniqueConstraint(
            "s3_url",
            name=op.f("avatar_s3_url_key"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_index(op.f("ix_avatar_uuid"), "avatar", ["uuid"], unique=True)
