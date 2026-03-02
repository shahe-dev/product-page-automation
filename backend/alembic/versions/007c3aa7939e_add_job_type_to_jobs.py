"""add job_type to jobs

Revision ID: 007c3aa7939e
Revises: c1234567890a
Create Date: 2026-02-05 17:42:39.210358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007c3aa7939e'
down_revision: Union[str, None] = 'c1234567890a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add job_type column with default 'full' for backward compatibility
    op.add_column(
        'jobs',
        sa.Column('job_type', sa.String(length=50), nullable=False, server_default='full')
    )

    # Add check constraint for valid job types
    op.create_check_constraint(
        'check_job_type',
        'jobs',
        "job_type IN ('full', 'extraction', 'generation')"
    )

    # Add index for filtering by job type
    op.create_index('idx_jobs_job_type', 'jobs', ['job_type'])


def downgrade() -> None:
    op.drop_index('idx_jobs_job_type', table_name='jobs')
    op.drop_constraint('check_job_type', 'jobs', type_='check')
    op.drop_column('jobs', 'job_type')
