"""add alt_text and filename to project_images

Revision ID: a5b3c7d9e1f2
Revises: 32eae96873a4
Create Date: 2026-02-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5b3c7d9e1f2'
down_revision: str = '32eae96873a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('project_images', sa.Column('alt_text', sa.String(500), nullable=True))
    op.add_column('project_images', sa.Column('filename', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('project_images', 'filename')
    op.drop_column('project_images', 'alt_text')
