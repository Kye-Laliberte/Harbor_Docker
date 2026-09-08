"""remove persisted ship speed

Revision ID: 8a4f2c1d9e7b
Revises: 6c2d1f8a4b7e
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8a4f2c1d9e7b"
down_revision: Union[str, Sequence[str], None] = "6c2d1f8a4b7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("ships")}
    if "average_speed_kmh" in columns:
        op.drop_constraint("ck_ship_average_speed", "ships", type_="check")
        op.drop_column("ships", "average_speed_kmh")


def downgrade() -> None:
    op.add_column("ships", sa.Column("average_speed_kmh", sa.Float(), nullable=True))
    op.create_check_constraint("ck_ship_average_speed", "ships", "average_speed_kmh > 0")