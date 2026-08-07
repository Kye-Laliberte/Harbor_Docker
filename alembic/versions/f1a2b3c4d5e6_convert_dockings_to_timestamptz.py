"""convert dockings timestamps to timestamptz

Revision ID: f1a2b3c4d5e6
Revises: d0e78520728c
Create Date: 2026-08-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd0e78520728c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: convert arrival_date and departure_date to timestamptz."""
    # Postgres: convert TIMESTAMP (without time zone) columns to TIMESTAMP WITH TIME ZONE
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == 'postgresql':
        op.execute("""
            ALTER TABLE dockings
            ALTER COLUMN arrival_date TYPE TIMESTAMP WITH TIME ZONE
            USING arrival_date AT TIME ZONE 'UTC';
        """)
        op.execute("""
            ALTER TABLE dockings
            ALTER COLUMN departure_date TYPE TIMESTAMP WITH TIME ZONE
            USING departure_date AT TIME ZONE 'UTC';
        """)
    else:
        # For other DBs (SQLite used in tests), no-op; SQLite doesn't support timestamptz column types in the same way
        pass


def downgrade() -> None:
    """Downgrade schema: convert arrival_date and departure_date back to timestamp without tz."""
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect == 'postgresql':
        op.execute("""
            ALTER TABLE dockings
            ALTER COLUMN arrival_date TYPE TIMESTAMP WITHOUT TIME ZONE
            USING arrival_date AT TIME ZONE 'UTC';
        """)
        op.execute("""
            ALTER TABLE dockings
            ALTER COLUMN departure_date TYPE TIMESTAMP WITHOUT TIME ZONE
            USING departure_date AT TIME ZONE 'UTC';
        """)
    else:
        pass
