"""Compatibility bridge for a revision recorded by an older deployment.

Revision ID: 7f6e38485af9
Revises: 55e8bb63560e, 56b4e2d5b108
"""
from typing import Sequence, Union

from alembic import op


revision: str = "7f6e38485af9"
down_revision: Union[str, Sequence[str], None] = ("55e8bb63560e", "56b4e2d5b108")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """The older deployment already applied this revision's changes."""


def downgrade() -> None:
    """The bridge has no database operations to reverse."""