"""add_timezone_to_timestamps

Revision ID: bcdbcc963682
Revises: b1af478a9ca2
Create Date: 2026-10-12 15:42:45.965716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcdbcc963682'
down_revision: Union[str, Sequence[str], None] = 'b1af478a9ca2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to use TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ)."""
    # PostgreSQL: ALTER COLUMN TYPE TIMESTAMP WITH TIME ZONE USING column_name AT TIME ZONE 'UTC'
    # For SQLite/others, standard alter_column handles type swap.
    op.alter_column(
        'users',
        'created_at',
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )
    op.alter_column(
        'sessions',
        'start_time_utc',
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="start_time_utc AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    """Downgrade schema to use TIMESTAMP WITHOUT TIME ZONE."""
    op.alter_column(
        'sessions',
        'start_time_utc',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False,
        postgresql_using="start_time_utc AT TIME ZONE 'UTC'"
    )
    op.alter_column(
        'users',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True,
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )
