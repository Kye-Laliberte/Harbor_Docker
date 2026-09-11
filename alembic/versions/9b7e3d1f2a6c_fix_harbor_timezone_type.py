"""store harbor timezone as an IANA timezone string

Revision ID: 9b7e3d1f2a6c
Revises: 8a4f2c1d9e7b
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b7e3d1f2a6c"
down_revision: Union[str, Sequence[str], None] = "8a4f2c1d9e7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column(
            "harbors",
            "timezone",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.String(length=50),
            existing_nullable=False,
            postgresql_using="timezone::text",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column(
            "harbors",
            "timezone",
            existing_type=sa.String(length=50),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="timezone::timestamptz",
        )