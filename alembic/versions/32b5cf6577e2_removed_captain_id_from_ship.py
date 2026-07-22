"""removed  captain table and captain_id from ship 

Revision ID: 32b5cf6577e2
Revises: 88582088655b
Create Date: 2026-07-17 22:36:24.635841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '32b5cf6577e2'
down_revision: Union[str, Sequence[str], None] = '88582088655b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    #op.drop_index(op.f('ix_captains_id'), table_name='captains')

    op.drop_table(
            "captains"
        ),
    
    
    pass



def downgrade() -> None:
    """Downgrade schema."""
    
    op.create_table('captains',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('experience_years', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')),
    op.create_index(op.f('ix_captains_id'), 'captains', ['id'], unique=False),
    pass
   
   
    # ### end Alembic commands ###
