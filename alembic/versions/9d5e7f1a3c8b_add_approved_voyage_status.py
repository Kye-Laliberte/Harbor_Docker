"""add approved voyage status

Revision ID: 9d5e7f1a3c8b
Revises: 9c8d4e2f1b7a
"""
from typing import Sequence, Union

from alembic import op


revision: str = "9d5e7f1a3c8b"
down_revision: Union[str, Sequence[str], None] = "9c8d4e2f1b7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE voyage_status ADD VALUE IF NOT EXISTS 'approved' AFTER 'scheduled'")


def downgrade() -> None:
    pass