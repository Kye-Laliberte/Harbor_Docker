"""drop captains table

Revision ID: 5c53be169ebf
Revises: 47a723c3899f
Create Date: 2026-07-22 16:34:20.873323

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c53be169ebf'
down_revision: Union[str, Sequence[str], None] = '47a723c3899f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_table('captains')
    

def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('captains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('experience_years', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
    

    pass
