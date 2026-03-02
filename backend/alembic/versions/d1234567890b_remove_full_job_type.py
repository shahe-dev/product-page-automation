"""Remove FULL job type from jobs table.

Clean cutover to EXTRACTION + GENERATION only pipeline.
Existing 'full' jobs are migrated to 'extraction'.

Revision ID: d1234567890b
Revises: 4a9207e8cc43
Create Date: 2026-02-05 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1234567890b'
down_revision: Union[str, None] = '4a9207e8cc43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove FULL job type - migrate to extraction, update constraint."""
    # 1. Migrate existing 'full' jobs to 'extraction'
    op.execute(
        "UPDATE jobs SET job_type = 'extraction' WHERE job_type = 'full'"
    )

    # 2. Update server default
    op.alter_column(
        'jobs',
        'job_type',
        server_default='extraction'
    )

    # 3. Drop old constraint if exists, create new one (PostgreSQL)
    # Use raw SQL to handle constraint that may or may not exist
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.constraint_column_usage
                WHERE constraint_name = 'ck_jobs_job_type'
            ) THEN
                ALTER TABLE jobs DROP CONSTRAINT ck_jobs_job_type;
            END IF;
        END $$;
    """)

    # Create new constraint without 'full'
    op.execute("""
        ALTER TABLE jobs ADD CONSTRAINT ck_jobs_job_type
        CHECK (job_type IN ('extraction', 'generation'))
    """)


def downgrade() -> None:
    """Restore FULL job type support."""
    # Drop and recreate constraint with 'full'
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.constraint_column_usage
                WHERE constraint_name = 'ck_jobs_job_type'
            ) THEN
                ALTER TABLE jobs DROP CONSTRAINT ck_jobs_job_type;
            END IF;
        END $$;
    """)

    op.execute("""
        ALTER TABLE jobs ADD CONSTRAINT ck_jobs_job_type
        CHECK (job_type IN ('full', 'extraction', 'generation'))
    """)

    # Restore server default
    op.alter_column(
        'jobs',
        'job_type',
        server_default='full'
    )
