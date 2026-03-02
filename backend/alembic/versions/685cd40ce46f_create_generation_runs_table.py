"""create generation_runs table

Revision ID: 685cd40ce46f
Revises: 7f22305a072b
Create Date: 2026-02-05 17:43:23.679788

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '685cd40ce46f'
down_revision: Union[str, None] = '7f22305a072b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_package_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generated_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sheet_url', sa.String(length=500), nullable=True),
        sa.Column('drive_folder_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_package_id'], ['material_packages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('project_id', 'template_type', name='uq_generation_runs_project_template'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='check_generation_run_status'),
    )

    op.create_index('idx_generation_runs_project_id', 'generation_runs', ['project_id'])
    op.create_index('idx_generation_runs_status', 'generation_runs', ['status'])
    op.create_index('idx_generation_runs_template_type', 'generation_runs', ['template_type'])


def downgrade() -> None:
    op.drop_index('idx_generation_runs_template_type', table_name='generation_runs')
    op.drop_index('idx_generation_runs_status', table_name='generation_runs')
    op.drop_index('idx_generation_runs_project_id', table_name='generation_runs')
    op.drop_table('generation_runs')
