"""normalize legacy harbor timezone values

Revision ID: 9c8d4e2f1b7a
Revises: 9b7e3d1f2a6c
"""
from typing import Sequence, Union

from alembic import op


revision: str = "9c8d4e2f1b7a"
down_revision: Union[str, Sequence[str], None] = "9b7e3d1f2a6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "UPDATE harbors SET timezone = 'UTC' "
            "WHERE timezone IS NULL OR timezone ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'")


def downgrade() -> None:
    pass