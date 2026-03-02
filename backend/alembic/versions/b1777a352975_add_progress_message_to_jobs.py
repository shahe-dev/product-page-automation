"""add progress_message to jobs

Revision ID: b1777a352975
Revises: 301c11af3c4e
Create Date: 2026-02-04 14:09:20.363429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1777a352975'
down_revision: Union[str, None] = '301c11af3c4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add progress_message column for granular substep visibility
    op.add_column('jobs', sa.Column('progress_message', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'progress_message')
