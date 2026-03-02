"""Switch enum fields from String to SQLAlchemy Enum (native_enum=False)

This migration documents the ORM-level change from String() to
SQLAlchemy Enum(native_enum=False) for all enum-typed columns.

Since native_enum=False stores values as VARCHAR (same as String),
no actual database schema change is required. The change is purely
at the SQLAlchemy ORM layer to enable automatic string-to-enum
coercion, fixing AttributeError crashes when accessing .value on
fields that were returned as plain strings.

Revision ID: 003_enum_column_types
Revises: 002_add_auth_tables
Create Date: 2026-01-28 20:00:00.000000

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '003_enum_column_types'
down_revision: Union[str, None] = '002_add_auth_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: SQLAlchemy Enum(native_enum=False) uses VARCHAR storage,
    identical to the existing String columns. The change is ORM-level only."""
    pass


def downgrade() -> None:
    """No-op: reverting to String columns requires no schema change."""
    pass
