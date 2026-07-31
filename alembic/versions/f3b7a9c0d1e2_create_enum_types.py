"""create enum types and convert text columns to native ENUMs

Revision ID: f3b7a9c0d1e2
Revises: dee3a0431a6e
Create Date: 2026-07-30 18:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f3b7a9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'd0e78520728c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create enum types and alter columns to use them."""
    bind = op.get_bind()

    # Create enum types if they don't already exist
    postgresql.ENUM('active', 'inactive', 'maintenance', name='dock_status_enum').create(bind, checkfirst=True)
    postgresql.ENUM('small', 'medium', 'large', name='vessel_size_enum').create(bind, checkfirst=True)
    postgresql.ENUM('docked', 'sailing', 'maintenance', name='ship_status_enum').create(bind, checkfirst=True)
    postgresql.ENUM('pending', 'approved', 'denied', name='ship_clearance_status_enum').create(bind, checkfirst=True)
    postgresql.ENUM('scheduled', 'departed', 'arrived', 'cancelled', name='voyage_status').create(bind, checkfirst=True)

    # Alter table columns to use the new enum types. Use USING to cast values.
    # Only alter if the column type is not already the target enum (idempotent)
    op.execute("""
    DO $$
    BEGIN
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='docks' AND column_name='dock_status') != 'dock_status_enum' THEN
            EXECUTE 'ALTER TABLE docks ALTER COLUMN dock_status TYPE dock_status_enum USING dock_status::dock_status_enum';
            EXECUTE 'ALTER TABLE docks ALTER COLUMN dock_status SET DEFAULT ''active''::dock_status_enum';
        END IF;
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='docks' AND column_name='dock_size') != 'vessel_size_enum' THEN
            EXECUTE 'ALTER TABLE docks ALTER COLUMN dock_size TYPE vessel_size_enum USING dock_size::vessel_size_enum';
        END IF;
    END
    $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='ships' AND column_name='ship_status') != 'ship_status_enum' THEN
            EXECUTE 'ALTER TABLE ships ALTER COLUMN ship_status TYPE ship_status_enum USING ship_status::ship_status_enum';
        END IF;
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='ships' AND column_name='ship_size') != 'vessel_size_enum' THEN
            EXECUTE 'ALTER TABLE ships ALTER COLUMN ship_size TYPE vessel_size_enum USING ship_size::vessel_size_enum';
        END IF;
    END
    $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='dockings' AND column_name='ship_clearance_status') != 'ship_clearance_status_enum' THEN
            EXECUTE 'ALTER TABLE dockings ALTER COLUMN ship_clearance_status TYPE ship_clearance_status_enum USING ship_clearance_status::ship_clearance_status_enum';
            EXECUTE 'ALTER TABLE dockings ALTER COLUMN ship_clearance_status SET DEFAULT ''pending''::ship_clearance_status_enum';
        END IF;
    END
    $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        IF (SELECT coalesce(udt_name, '') FROM information_schema.columns WHERE table_name='voyage' AND column_name='travel_status') != 'voyage_status' THEN
            EXECUTE 'ALTER TABLE voyage ALTER COLUMN travel_status TYPE voyage_status USING travel_status::voyage_status';
            EXECUTE 'ALTER TABLE voyage ALTER COLUMN travel_status SET DEFAULT ''scheduled''::voyage_status';
        END IF;
    END
    $$;
    """)


def downgrade() -> None:
    """Downgrade schema: revert enum columns back to text and drop types."""
    bind = op.get_bind()

    # Alter columns back to text
    op.execute("ALTER TABLE docks ALTER COLUMN dock_size TYPE TEXT USING dock_size::text")
    op.execute("ALTER TABLE docks ALTER COLUMN dock_status DROP DEFAULT")
    op.execute("ALTER TABLE docks ALTER COLUMN dock_status TYPE TEXT USING dock_status::text")

    op.execute("ALTER TABLE ships ALTER COLUMN ship_size TYPE TEXT USING ship_size::text")
    op.execute("ALTER TABLE ships ALTER COLUMN ship_status TYPE TEXT USING ship_status::text")

    op.execute("ALTER TABLE dockings ALTER COLUMN ship_clearance_status DROP DEFAULT")
    op.execute("ALTER TABLE dockings ALTER COLUMN ship_clearance_status TYPE TEXT USING ship_clearance_status::text")

    op.execute("ALTER TABLE voyage ALTER COLUMN travel_status DROP DEFAULT")
    op.execute("ALTER TABLE voyage ALTER COLUMN travel_status TYPE TEXT USING travel_status::text")

    # Drop enum types if they exist (after columns are reverted)
    postgresql.ENUM(name='dock_status_enum').drop(bind, checkfirst=True)
    postgresql.ENUM(name='vessel_size_enum').drop(bind, checkfirst=True)
    postgresql.ENUM(name='ship_status_enum').drop(bind, checkfirst=True)
    postgresql.ENUM(name='ship_clearance_status_enum').drop(bind, checkfirst=True)
    postgresql.ENUM(name='voyage_status').drop(bind, checkfirst=True)
