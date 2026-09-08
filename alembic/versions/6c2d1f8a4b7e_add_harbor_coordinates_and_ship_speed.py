"""add harbor coordinates and learned ship speed

Revision ID: 6c2d1f8a4b7e
Revises: 7f6e38485af9
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c2d1f8a4b7e"
down_revision: Union[str, Sequence[str], None] = "7f6e38485af9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE IF EXISTS voyage RENAME TO voyages")
    op.add_column("harbors", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("harbors", sa.Column("longitude", sa.Float(), nullable=True))
    op.create_check_constraint("ck_harbor_latitude", "harbors", "latitude >= -90 AND latitude <= 90")
    op.create_check_constraint("ck_harbor_longitude", "harbors", "longitude >= -180 AND longitude <= 180")

    op.add_column("ships", sa.Column("average_speed_kmh", sa.Float(), nullable=True))
    op.create_check_constraint("ck_ship_average_speed", "ships", "average_speed_kmh > 0")


def downgrade() -> None:
    op.drop_constraint("ck_ship_average_speed", "ships", type_="check")
    op.drop_column("ships", "average_speed_kmh")

    op.drop_constraint("ck_harbor_longitude", "harbors", type_="check")
    op.drop_constraint("ck_harbor_latitude", "harbors", type_="check")
    op.drop_column("harbors", "longitude")
    op.drop_column("harbors", "latitude")