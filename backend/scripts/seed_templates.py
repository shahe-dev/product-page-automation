#!/usr/bin/env python
"""
Seed the templates table with field-to-cell mappings for all 6 template types.

This script populates the templates table so that SheetsManager and ContentGenerator
can read field mappings from the database (enabling admin edits without code deployment).

Usage:
    python scripts/seed_templates.py          # Skip existing
    python scripts/seed_templates.py --force  # Overwrite existing
"""

import sys
import asyncio
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.models.database import Template
from app.models.enums import TemplateType, ContentVariant
from app.services.template_fields import get_cell_mapping, TEMPLATE_FIELD_REGISTRY
from app.config.database import async_session_factory


# Human-readable names for each template type
TEMPLATE_NAMES = {
    "aggregators": "Aggregators Template",
    "opr": "OPR Template",
    "mpp": "MPP Template",
    "adop": "ADOP Template",
    "adre": "ADRE Template",
    "commercial": "Commercial Project Template",
}

# Master template sheet URL (shared across all templates)
MASTER_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1pef6Q-54l2mFOX6QgwOLQONviBijgaRgI7gA2GHn_Ck"
)


async def seed_templates(force: bool = False) -> None:
    """
    Seed templates table with field mappings from TEMPLATE_FIELD_REGISTRY.

    Args:
        force: If True, overwrite existing templates. If False, skip existing.
    """
    async with async_session_factory() as session:
        created = 0
        updated = 0
        skipped = 0

        for template_type in TEMPLATE_FIELD_REGISTRY:
            name = TEMPLATE_NAMES[template_type]
            cell_mapping = get_cell_mapping(template_type, "en")
            field_count = len(cell_mapping)

            # Check if template already exists
            result = await session.execute(
                select(Template).where(
                    Template.template_type == TemplateType(template_type),
                    Template.content_variant == ContentVariant.STANDARD,
                )
            )
            existing_template = result.scalar_one_or_none()

            if existing_template and not force:
                print(f"  SKIP {template_type} (exists, use --force)")
                skipped += 1
                continue

            if existing_template and force:
                # Update existing template
                existing_template.field_mappings = cell_mapping
                existing_template.name = name
                existing_template.sheet_template_url = MASTER_SHEET_URL
                print(f"  UPDATE {template_type} ({field_count} fields)")
                updated += 1
            else:
                # Create new template
                template = Template(
                    name=name,
                    template_type=TemplateType(template_type),
                    content_variant=ContentVariant.STANDARD,
                    sheet_template_url=MASTER_SHEET_URL,
                    field_mappings=cell_mapping,
                    is_active=True,
                )
                session.add(template)
                print(f"  CREATE {template_type} ({field_count} fields)")
                created += 1

        await session.commit()

        print(f"\nDone. Created: {created}, Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    force = "--force" in sys.argv
    print(f"Seeding templates (force={force})...")
    asyncio.run(seed_templates(force))
