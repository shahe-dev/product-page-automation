"""Initial schema with all 22 tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all 22 tables for PDP Automation v.3:
    - 16 core tables
    - 3 QA module tables
    - 3 content module tables
    """

    # =====================================================================
    # CORE TABLES (16)
    # =====================================================================

    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('google_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('picture_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='user', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("email ~ '@your-domain\\.com$'", name='check_email_domain'),
        sa.CheckConstraint("role IN ('admin', 'user')", name='check_user_role'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_google_id', 'users', ['google_id'])
    op.create_index('idx_users_role', 'users', ['role'])

    # templates table (needed before jobs and projects)
    op.create_table(
        'templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('content_variant', sa.String(length=50), server_default='standard', nullable=False),
        sa.Column('sheet_template_url', sa.String(length=500), nullable=False),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')", name='check_template_type'),
        sa.CheckConstraint("content_variant IN ('standard', 'luxury')", name='check_content_variant'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_templates_template_type', 'templates', ['template_type'])
    op.create_index('idx_templates_active', 'templates', ['is_active'])
    op.create_index('idx_templates_field_mappings', 'templates', ['field_mappings'], postgresql_using='gin')

    # jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processing_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('progress', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('cloud_task_name', sa.String(length=500), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')", name='check_job_template_type'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')", name='check_job_status'),
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='check_job_progress_range'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['template_id'], ['templates.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index(op.f('idx_jobs_created_at'), 'jobs', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index(op.f('idx_jobs_completed_at'), 'jobs', ['completed_at'], postgresql_ops={'completed_at': 'DESC'})

    # projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('developer', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('emirate', sa.String(length=100), nullable=True),
        sa.Column('starting_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('price_per_sqft', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('handover_date', sa.Date(), nullable=True),
        sa.Column('payment_plan', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('property_types', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('unit_sizes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('amenities', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('total_units', sa.Integer(), nullable=True),
        sa.Column('floors', sa.Integer(), nullable=True),
        sa.Column('buildings', sa.Integer(), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('original_pdf_url', sa.String(length=500), nullable=True),
        sa.Column('processed_zip_url', sa.String(length=500), nullable=True),
        sa.Column('sheet_url', sa.String(length=500), nullable=True),
        sa.Column('generated_content', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('workflow_status', sa.String(length=50), server_default='draft', nullable=False),
        sa.Column('published_url', sa.String(length=500), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processing_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "workflow_status IN ('draft', 'pending_approval', 'revision_requested', 'approved', 'publishing', 'published', 'qa_verified', 'complete')",
            name='check_workflow_status'
        ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.id']),
        sa.ForeignKeyConstraint(['processing_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_projects_name', 'projects', ['name'])
    op.create_index('idx_projects_developer', 'projects', ['developer'])
    op.create_index('idx_projects_emirate', 'projects', ['emirate'])
    op.create_index('idx_projects_status', 'projects', ['workflow_status'])
    op.create_index(op.f('idx_projects_created_at'), 'projects', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_projects_created_by', 'projects', ['created_by'])
    op.create_index('idx_projects_is_active', 'projects', ['is_active'])
    op.execute("""
        CREATE INDEX idx_projects_search ON projects
        USING gin(to_tsvector('english',
            coalesce(name, '') || ' ' ||
            coalesce(developer, '') || ' ' ||
            coalesce(location, '') || ' ' ||
            coalesce(description, '')
        ))
    """)
    op.create_index('idx_projects_property_types', 'projects', ['property_types'], postgresql_using='gin')
    op.create_index('idx_projects_amenities', 'projects', ['amenities'], postgresql_using='gin')

    # project_images table
    op.create_table(
        'project_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('format', sa.String(length=10), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("category IN ('interior', 'exterior', 'amenity', 'logo', 'floor_plan', 'other')", name='check_image_category'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_images_project_id', 'project_images', ['project_id'])
    op.create_index('idx_project_images_category', 'project_images', ['category'])
    op.create_index('idx_project_images_order', 'project_images', ['project_id', 'display_order'])

    # project_floor_plans table
    op.create_table(
        'project_floor_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('unit_type', sa.String(length=50), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Integer(), nullable=True),
        sa.Column('total_sqft', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('balcony_sqft', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('builtup_sqft', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_floor_plans_project_id', 'project_floor_plans', ['project_id'])
    op.create_index('idx_project_floor_plans_unit_type', 'project_floor_plans', ['unit_type'])
    op.create_index('idx_project_floor_plans_order', 'project_floor_plans', ['project_id', 'display_order'])

    # project_approvals table
    op.create_table(
        'project_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("action IN ('submitted', 'approved', 'rejected', 'revision_requested')", name='check_approval_action'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_approvals_project_id', 'project_approvals', ['project_id'])
    op.create_index('idx_project_approvals_approver_id', 'project_approvals', ['approver_id'])
    op.create_index(op.f('idx_project_approvals_created_at'), 'project_approvals', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # project_revisions table
    op.create_table(
        'project_revisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_revisions_project_id', 'project_revisions', ['project_id'])
    op.create_index('idx_project_revisions_field', 'project_revisions', ['field'])
    op.create_index('idx_project_revisions_changed_by', 'project_revisions', ['changed_by'])
    op.create_index(op.f('idx_project_revisions_created_at'), 'project_revisions', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # job_steps table
    op.create_table(
        'job_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_id', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('step_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')", name='check_job_step_status'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_steps_job_id', 'job_steps', ['job_id'])
    op.create_index('idx_job_steps_step_id', 'job_steps', ['step_id'])
    op.create_index('idx_job_steps_status', 'job_steps', ['status'])

    # prompts table
    op.create_table(
        'prompts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('content_variant', sa.String(length=50), server_default='standard', nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('character_limit', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), server_default=sa.text('1'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')", name='check_prompt_template_type'),
        sa.CheckConstraint("content_variant IN ('standard', 'luxury')", name='check_prompt_content_variant'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prompts_template_type', 'prompts', ['template_type'])
    op.create_index('idx_prompts_content_variant', 'prompts', ['content_variant'])
    op.create_index('idx_prompts_name', 'prompts', ['name'])
    op.create_index('idx_prompts_active', 'prompts', ['is_active'])

    # prompt_versions table
    op.create_table(
        'prompt_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('prompt_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('character_limit', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_prompt_versions_prompt_id', 'prompt_versions', ['prompt_id'])
    op.create_index(op.f('idx_prompt_versions_version'), 'prompt_versions', ['prompt_id', 'version'], postgresql_ops={'version': 'DESC'})
    op.create_index(op.f('idx_prompt_versions_created_at'), 'prompt_versions', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # qa_comparisons table
    op.create_table(
        'qa_comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checkpoint_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('matches', sa.Integer(), nullable=True),
        sa.Column('differences', sa.Integer(), nullable=True),
        sa.Column('missing', sa.Integer(), nullable=True),
        sa.Column('extra', sa.Integer(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("checkpoint_type IN ('extraction', 'generation', 'publication', 'content', 'image', 'final')", name='check_qa_checkpoint_type'),
        sa.CheckConstraint("status IN ('passed', 'failed')", name='check_qa_comparison_status'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_comparisons_project_id', 'qa_comparisons', ['project_id'])
    op.create_index('idx_qa_comparisons_checkpoint_type', 'qa_comparisons', ['checkpoint_type'])
    op.create_index('idx_qa_comparisons_status', 'qa_comparisons', ['status'])
    op.create_index(op.f('idx_qa_comparisons_performed_at'), 'qa_comparisons', ['performed_at'], postgresql_ops={'performed_at': 'DESC'})

    # notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("type IN ('info', 'success', 'warning', 'error', 'approval', 'mention')", name='check_notification_type'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['user_id', 'is_read'])
    op.create_index(op.f('idx_notifications_created_at'), 'notifications', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # workflow_items table
    op.create_table(
        'workflow_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_items_project_id', 'workflow_items', ['project_id'])
    op.create_index('idx_workflow_items_assigned_to', 'workflow_items', ['assigned_to'])

    # publication_checklists table
    op.create_table(
        'publication_checklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('all_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')", name='check_publication_template_type'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_publication_checklists_project_id', 'publication_checklists', ['project_id'])
    op.create_index('idx_publication_checklists_template_type', 'publication_checklists', ['template_type'])

    # execution_history table
    op.create_table(
        'execution_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_execution_history_action', 'execution_history', ['action'])
    op.create_index('idx_execution_history_entity', 'execution_history', ['entity_type', 'entity_id'])
    op.create_index('idx_execution_history_user_id', 'execution_history', ['user_id'])
    op.create_index(op.f('idx_execution_history_created_at'), 'execution_history', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # =====================================================================
    # QA MODULE TABLES (3)
    # =====================================================================

    # qa_checkpoints table
    op.create_table(
        'qa_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('checkpoint_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('issues_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("checkpoint_type IN ('extraction', 'content', 'image', 'final', 'generation', 'publication')", name='check_checkpoint_type'),
        sa.CheckConstraint("status IN ('pending', 'passed', 'failed', 'skipped')", name='check_checkpoint_status'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checked_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_checkpoints_project_id', 'qa_checkpoints', ['project_id'])
    op.create_index('idx_qa_checkpoints_status', 'qa_checkpoints', ['status'])

    # qa_issues table
    op.create_table(
        'qa_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('checkpoint_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggestion', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("severity IN ('critical', 'high', 'medium', 'low')", name='check_issue_severity'),
        sa.ForeignKeyConstraint(['checkpoint_id'], ['qa_checkpoints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_issues_checkpoint_id', 'qa_issues', ['checkpoint_id'])
    op.create_index('idx_qa_issues_project_id', 'qa_issues', ['project_id'])
    op.create_index('idx_qa_issues_severity', 'qa_issues', ['severity'])
    op.create_index('idx_qa_issues_is_resolved', 'qa_issues', ['is_resolved'])

    # qa_overrides table
    op.create_table(
        'qa_overrides',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('override_type', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('overridden_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("override_type IN ('accept', 'reject', 'defer')", name='check_override_type'),
        sa.ForeignKeyConstraint(['issue_id'], ['qa_issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['overridden_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_overrides_issue_id', 'qa_overrides', ['issue_id'])

    # =====================================================================
    # CONTENT MODULE TABLES (3)
    # =====================================================================

    # extracted_data table
    op.create_table(
        'extracted_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extraction_type', sa.String(length=50), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('structured_content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("extraction_type IN ('text', 'image', 'table', 'metadata')", name='check_extraction_type'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_extracted_data_project_id', 'extracted_data', ['project_id'])
    op.create_index('idx_extracted_data_job_id', 'extracted_data', ['job_id'])
    op.create_index('idx_extracted_data_type', 'extracted_data', ['extraction_type'])

    # generated_content table
    op.create_table(
        'generated_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('content_variant', sa.String(length=50), server_default='standard', nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('prompt_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('generation_params', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('is_approved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')", name='check_generated_content_template_type'),
        sa.CheckConstraint("content_variant IN ('standard', 'luxury')", name='check_generated_content_variant'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_versions.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_generated_content_project_id', 'generated_content', ['project_id'])
    op.create_index('idx_generated_content_field', 'generated_content', ['field_name'])
    op.create_index('idx_generated_content_template', 'generated_content', ['template_type'])

    # content_qa_results table
    op.create_table(
        'content_qa_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('generated_content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("check_type IN ('brand_compliance', 'seo_score', 'readability', 'factual_accuracy')", name='check_content_qa_type'),
        sa.ForeignKeyConstraint(['generated_content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_content_qa_results_content_id', 'content_qa_results', ['generated_content_id'])
    op.create_index('idx_content_qa_results_check_type', 'content_qa_results', ['check_type'])
    op.create_index('idx_content_qa_results_passed', 'content_qa_results', ['passed'])


def downgrade() -> None:
    """Drop all tables in reverse order to respect foreign key constraints."""

    # Content module tables
    op.drop_table('content_qa_results')
    op.drop_table('generated_content')
    op.drop_table('extracted_data')

    # QA module tables
    op.drop_table('qa_overrides')
    op.drop_table('qa_issues')
    op.drop_table('qa_checkpoints')

    # Core tables
    op.drop_table('execution_history')
    op.drop_table('publication_checklists')
    op.drop_table('workflow_items')
    op.drop_table('notifications')
    op.drop_table('qa_comparisons')
    op.drop_table('prompt_versions')
    op.drop_table('prompts')
    op.drop_table('job_steps')
    op.drop_table('project_revisions')
    op.drop_table('project_approvals')
    op.drop_table('project_floor_plans')
    op.drop_table('project_images')
    op.drop_table('projects')
    op.drop_table('jobs')
    op.drop_table('templates')
    op.drop_table('users')
