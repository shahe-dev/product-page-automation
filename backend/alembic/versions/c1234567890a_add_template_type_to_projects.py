"""add template_type and template_id to projects

Revision ID: c1234567890a
Revises: b1777a352975
Create Date: 2026-02-04 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1234567890a'
down_revision: Union[str, None] = 'b1777a352975'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add template_type column with default 'opr' for existing rows
    op.add_column(
        'projects',
        sa.Column('template_type', sa.String(length=50), nullable=False, server_default='opr')
    )

    # Add check constraint for valid template types
    op.create_check_constraint(
        'check_project_template_type',
        'projects',
        "template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')"
    )

    # Add template_id foreign key column
    op.add_column(
        'projects',
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'projects_template_id_fkey',
        'projects',
        'templates',
        ['template_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for template_type
    op.create_index('idx_projects_template_type', 'projects', ['template_type'])

    # Create index for template_id
    op.create_index('idx_projects_template_id', 'projects', ['template_id'])


def downgrade() -> None:
    op.drop_index('idx_projects_template_id', table_name='projects')
    op.drop_index('idx_projects_template_type', table_name='projects')
    op.drop_constraint('projects_template_id_fkey', 'projects', type_='foreignkey')
    op.drop_constraint('check_project_template_type', 'projects', type_='check')
    op.drop_column('projects', 'template_id')
    op.drop_column('projects', 'template_type')
