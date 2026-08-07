"""merge enum and timestamp migrations

Revision ID: 55e8bb63560e
Revises: f1a2b3c4d5e6, f3b7a9c0d1e2
Create Date: 2026-08-07 19:44:12.661440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55e8bb63560e'
down_revision: Union[str, Sequence[str], None] = ('f1a2b3c4d5e6', 'f3b7a9c0d1e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
