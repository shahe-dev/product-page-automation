"""Fix ImageCategory check constraint drift and add partial unique index on prompts

P0-15: The ImageCategory enum in Python defines 8 values including
location_map and master_plan, but the migration 001 check constraint
only allows 6. This migration drops the old constraint and creates
a new one with all 8 values.

Also adds 'manager' to the user role check constraint (P0-5 / P2-18).

P0-16: The Prompt model docstring states "One active prompt per
(template_type, content_variant, name) combination" but no unique
constraint enforced this. This migration adds a partial unique index
on (template_type, content_variant, name) WHERE is_active = true.

Revision ID: 004_fix_constraints
Revises: 003_enum_column_types
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '004_fix_constraints'
down_revision: Union[str, None] = '003_enum_column_types'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # P0-15: Fix ImageCategory check constraint to include all 8 enum values
    op.drop_constraint('check_image_category', 'project_images', type_='check')
    op.create_check_constraint(
        'check_image_category',
        'project_images',
        "category IN ('interior', 'exterior', 'amenity', 'logo', "
        "'floor_plan', 'location_map', 'master_plan', 'other')"
    )

    # P0-5 / P2-18: Fix UserRole check constraint to include 'manager'
    op.drop_constraint('check_user_role', 'users', type_='check')
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('admin', 'manager', 'user')"
    )

    # P0-16: Partial unique index -- one active prompt per (template_type,
    # content_variant, name) combination
    op.execute(
        "CREATE UNIQUE INDEX uq_prompts_active_per_type_variant_name "
        "ON prompts (template_type, content_variant, name) "
        "WHERE is_active = true"
    )


def downgrade() -> None:
    # Remove prompts unique index
    op.execute("DROP INDEX IF EXISTS uq_prompts_active_per_type_variant_name")

    # Revert UserRole check constraint
    op.drop_constraint('check_user_role', 'users', type_='check')
    op.create_check_constraint(
        'check_user_role',
        'users',
        "role IN ('admin', 'user')"
    )

    # Revert ImageCategory check constraint to original 6 values
    op.drop_constraint('check_image_category', 'project_images', type_='check')
    op.create_check_constraint(
        'check_image_category',
        'project_images',
        "category IN ('interior', 'exterior', 'amenity', 'logo', "
        "'floor_plan', 'other')"
    )
