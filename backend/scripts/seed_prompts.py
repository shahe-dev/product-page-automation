"""
Seed script to populate prompts table for all 6 template types.

Iterates TEMPLATE_FIELD_REGISTRY and seeds every field for each template
using prompt content from PromptManager defaults.

Usage:
    python scripts/seed_prompts.py           # Skip existing
    python scripts/seed_prompts.py --force   # Overwrite existing
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.config.database import async_session_factory
from app.models.database import Prompt, PromptVersion, User
from app.services.prompt_manager import PromptManager
from app.services.template_fields import TEMPLATE_FIELD_REGISTRY


async def seed_all_prompts(force: bool = False):
    """Seed prompts for all template types and fields."""
    pm = PromptManager()
    defaults = pm.get_default_prompts()

    async with async_session_factory() as db:
        user_query = select(User).limit(1)
        result = await db.execute(user_query)
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            print("ERROR: No users in database. Create a user first.")
            return

        print(f"Using user: {admin_user.name} ({admin_user.email})")

        created = 0
        skipped = 0

        for template_type, fields in TEMPLATE_FIELD_REGISTRY.items():
            print(f"\n--- {template_type.upper()} ({len(fields)} fields) ---")

            for field_name in fields:
                # Look up prompt content: template-specific key first, then generic
                template_key = f"{template_type}:{field_name}"
                if template_key in defaults:
                    prompt_data = defaults[template_key]
                elif field_name in defaults:
                    prompt_data = defaults[field_name]
                else:
                    print(f"  WARN: No default prompt for {template_type}:{field_name}")
                    continue

                # Check if exists
                existing_query = select(Prompt).where(
                    Prompt.name == field_name,
                    Prompt.template_type == template_type,
                    Prompt.content_variant == "standard",
                )
                result = await db.execute(existing_query)
                existing = result.scalar_one_or_none()

                if existing and not force:
                    skipped += 1
                    continue

                if existing and force:
                    # Update existing
                    existing.content = prompt_data["content"]
                    existing.character_limit = prompt_data.get("character_limit")
                    existing.version += 1
                    existing.updated_by = admin_user.id

                    version_record = PromptVersion(
                        prompt_id=existing.id,
                        version=existing.version,
                        content=prompt_data["content"],
                        character_limit=prompt_data.get("character_limit"),
                        change_reason="Force re-seed",
                        created_by=admin_user.id,
                    )
                    db.add(version_record)
                    print(f"  UPDATED: {field_name} (v{existing.version})")
                    created += 1
                else:
                    # Create new
                    new_prompt = Prompt(
                        name=field_name,
                        template_type=template_type,
                        content_variant="standard",
                        content=prompt_data["content"],
                        character_limit=prompt_data.get("character_limit"),
                        version=1,
                        is_active=True,
                        created_by=admin_user.id,
                        updated_by=admin_user.id,
                    )
                    db.add(new_prompt)
                    await db.flush()

                    version_record = PromptVersion(
                        prompt_id=new_prompt.id,
                        version=1,
                        content=prompt_data["content"],
                        character_limit=prompt_data.get("character_limit"),
                        change_reason="Initial seed",
                        created_by=admin_user.id,
                    )
                    db.add(version_record)
                    print(f"  CREATED: {field_name}")
                    created += 1

        await db.commit()
        print(f"\nDone. Created/updated: {created}, Skipped: {skipped}")


async def main():
    force = "--force" in sys.argv
    if force:
        print("FORCE MODE: Overwriting existing prompts\n")
    await seed_all_prompts(force=force)


if __name__ == "__main__":
    asyncio.run(main())
