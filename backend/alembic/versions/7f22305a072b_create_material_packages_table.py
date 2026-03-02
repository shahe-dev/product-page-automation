"""create material_packages table

Revision ID: 7f22305a072b
Revises: 007c3aa7939e
Create Date: 2026-02-05 17:42:58.144205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7f22305a072b'
down_revision: Union[str, None] = '007c3aa7939e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'material_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('gcs_base_path', sa.String(length=500), nullable=False),
        sa.Column('package_version', sa.String(length=10), nullable=False, server_default='1.0'),
        sa.Column('extraction_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('structured_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.CheckConstraint("status IN ('pending', 'ready', 'expired', 'error')", name='check_material_package_status')
    )

    op.create_index('idx_material_packages_project_id', 'material_packages', ['project_id'])
    op.create_index('idx_material_packages_status', 'material_packages', ['status'])
    op.create_index('idx_material_packages_source_job', 'material_packages', ['source_job_id'])


def downgrade() -> None:
    op.drop_index('idx_material_packages_source_job', table_name='material_packages')
    op.drop_index('idx_material_packages_status', table_name='material_packages')
    op.drop_index('idx_material_packages_project_id', table_name='material_packages')
    op.drop_table('material_packages')
