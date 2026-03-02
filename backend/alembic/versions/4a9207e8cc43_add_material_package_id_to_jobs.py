"""add material_package_id to jobs

Revision ID: 4a9207e8cc43
Revises: 685cd40ce46f
Create Date: 2026-02-05 17:43:48.225731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4a9207e8cc43'
down_revision: Union[str, None] = '685cd40ce46f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable column first (material_packages table now exists)
    op.add_column(
        'jobs',
        sa.Column('material_package_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # Add FK constraint
    op.create_foreign_key(
        'fk_jobs_material_package_id',
        'jobs', 'material_packages',
        ['material_package_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index for lookups
    op.create_index('idx_jobs_material_package_id', 'jobs', ['material_package_id'])


def downgrade() -> None:
    op.drop_index('idx_jobs_material_package_id', table_name='jobs')
    op.drop_constraint('fk_jobs_material_package_id', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'material_package_id')
