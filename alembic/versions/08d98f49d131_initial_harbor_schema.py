"""initial harbor schema

Revision ID: 08d98f49d131
Revises: 
Create Date: 2026-07-17 11:52:06.798701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08d98f49d131'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table('captains',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('experience_years', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_captains_id'), 'captains', ['id'], unique=False)
    op.create_table('harbors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('dock_count', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_harbors_id'), 'harbors', ['id'], unique=False)

    op.create_table('docks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('dock_code', sa.Integer(), nullable=False),
    sa.Column('dock_name', sa.String(length=100), nullable=False),
    sa.Column('harbor_id', sa.Integer(), nullable=False),
    sa.Column('dock_status', sa.Enum('active', 'inactive', 'maintenance', name='dock_status_enum'), nullable=False),
    sa.Column('cargo_capacity', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['harbor_id'], ['harbors.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('dock_code')
    )

    op.create_index(op.f('ix_docks_id'), 'docks', ['id'], unique=False)
    op.create_table('ships',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ship_name', sa.String(length=100), default="Unknown Ship", nullable=False),
    sa.Column('captain_id', sa.Integer(), nullable=False),
    sa.Column('registration_number', sa.String(length=100), nullable=False),
    sa.Column('ship_status', sa.Enum('docked', 'sailing', 'maintenance', name='ship_status_enum'), nullable=False),
    sa.Column('cargo_capacity', sa.Integer(), nullable=False),
    sa.Column('current_cargo', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['captain_id'], ['captains.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('registration_number')
    )
    op.create_index(op.f('ix_ships_id'), 'ships', ['id'], unique=False)
    op.create_table('dockings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ship_id', sa.Integer(), nullable=False),
    sa.Column('dock_id', sa.Integer(), nullable=False),
    sa.Column('arrival_date', sa.TIMESTAMP(), nullable=False),
    sa.Column('departure_date', sa.TIMESTAMP(), nullable=True),
    sa.Column('ship_clearance_status', sa.Enum('pending', 'approved', 'denied', name='ship_clearance_status_enum'), nullable=False),
    sa.Column('purpose', sa.String(length=200), nullable=True),
    sa.CheckConstraint('departure_date IS NULL OR departure_date >= arrival_date', name='check_departure_after_arrival'),
    sa.ForeignKeyConstraint(['dock_id'], ['docks.id'], ),
    sa.ForeignKeyConstraint(['ship_id'], ['ships.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dockings_id'), 'dockings', ['id'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
   
    op.drop_index(op.f('ix_dockings_id'), table_name='dockings')
    op.drop_table('dockings')
    op.drop_index(op.f('ix_ships_id'), table_name='ships')
    op.drop_table('ships')
    op.drop_index(op.f('ix_docks_id'), table_name='docks')
    op.drop_table('docks')
    op.drop_index(op.f('ix_harbors_id'), table_name='harbors')
    op.drop_table('harbors')
    op.drop_index(op.f('ix_captains_id'), table_name='captains')
    op.drop_table('captains')
   
