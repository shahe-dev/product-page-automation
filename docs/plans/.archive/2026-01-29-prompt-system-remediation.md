# Prompt System Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the prompt system so that (1) database-backed prompts are actually used during content generation, (2) all 6 template types have proper template-specific prompt definitions, and (3) the admin UI prompt edits take effect at runtime.

**Architecture:** Three phases. Phase 1 wires the database into the generation pipeline (the `db=None` fix). Phase 2 defines template-specific field configurations and prompt content for all 6 template types. Phase 3 updates the seed script to populate the database with all prompts on first deploy.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy async, PostgreSQL, Anthropic Claude API

---

## Audit Summary (Context for Implementer)

These are the verified findings that motivate every task below:

| # | Finding | Location | Impact |
|---|---------|----------|--------|
| F1 | `db=None` hardcoded -- database prompts never read | `content_generator.py:210` | Admin UI edits have zero effect |
| F2 | Only 10 generic fields defined in `FIELD_LIMITS` | `content_generator.py:59-70` | Templates require 45-75 fields each |
| F3 | Defaults in `get_default_prompts()` are template-agnostic | `prompt_manager.py:159-369` | Same prompt for OPR, aggregators, commercial, etc. |
| F4 | Only OPR has a file-based template prompt | `content_generator.py:373-378` | 5 of 6 template types get a one-liner fallback |
| F5 | Seed script only covers OPR | `seed_prompts.py:30-32, 122` | Database has no prompts for other templates |
| F6 | `generate_all()` has no access to db session | `content_generator.py:97` | Cannot query prompts table |
| F7 | `_step_generate_content()` has db access via `self.job_repo.db` but does not pass it | `job_manager.py:912-913` | Session available but not threaded through |

---

## Phase 1: Wire Database Prompts into Generation Pipeline

**Objective:** Make the existing database prompt path functional so admin edits take effect.

### Task 1.1: Pass database session from JobManager to ContentGenerator

**Files:**
- Modify: `backend/app/services/job_manager.py:881-921`
- Modify: `backend/app/services/content_generator.py:87-95, 97-175, 177-296`

**Step 1: Modify ContentGenerator to accept an optional db session**

In `content_generator.py`, change `__init__` and `generate_all` to accept and store an optional `AsyncSession`:

```python
# content_generator.py line 87
def __init__(self, db: Optional[AsyncSession] = None):
    """Initialize content generator with Anthropic client and brand context."""
    self.settings = get_settings()
    self.client = anthropic_service
    self.brand_context = self._load_brand_context()
    self.prompt_manager = PromptManager()
    self.template_prompts = self._load_template_prompts()
    self.db = db

    logger.info("ContentGenerator initialized with model: %s", self.settings.ANTHROPIC_MODEL)
```

Add the import at the top of `content_generator.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
```

**Step 2: Thread db session into generate_field()**

In `generate_field()` at line 206-211, replace `db=None` with `db=self.db`:

```python
prompt_template = await self.prompt_manager.get_prompt(
    field_name=field_name,
    template_type=template_type,
    variant=content_variant,
    db=self.db
)
```

**Step 3: Pass db session from job_manager**

In `job_manager.py` at line 912, pass the database session:

```python
generator = ContentGenerator(db=self.job_repo.db)
```

**Step 4: Write the test**

Create: `backend/tests/test_prompt_db_integration.py`

```python
"""Test that database prompts are used when available."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.content_generator import ContentGenerator
from app.services.prompt_manager import PromptManager, PromptTemplate


@pytest.mark.asyncio
async def test_generate_field_uses_db_prompt_when_available():
    """When db session is provided and prompt exists, use it."""
    mock_db = AsyncMock()
    mock_prompt = MagicMock()
    mock_prompt.content = "DB prompt: Generate meta title for {project_name}"
    mock_prompt.character_limit = 60
    mock_prompt.version = 2
    mock_prompt.name = "meta_title"
    mock_prompt.template_type = "opr"
    mock_prompt.content_variant = "standard"
    mock_prompt.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_prompt
    mock_db.execute = AsyncMock(return_value=mock_result)

    generator = ContentGenerator(db=mock_db)

    # Mock the Anthropic API call
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test Title Here")]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=10)
    generator.client.messages_create = AsyncMock(return_value=mock_response)

    result = await generator.generate_field(
        field_name="meta_title",
        structured_data={"project_name": "Test Project", "developer": "Test Dev", "location": "Dubai"},
        template_type="opr",
    )

    assert result.content == "Test Title Here"
    assert result.prompt_version == "v2"
    # Verify db.execute was called (prompt lookup happened)
    mock_db.execute.assert_called()


@pytest.mark.asyncio
async def test_generate_field_falls_back_when_no_db():
    """When db session is None, fall back to hardcoded defaults."""
    generator = ContentGenerator(db=None)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Fallback Title")]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=10)
    generator.client.messages_create = AsyncMock(return_value=mock_response)

    result = await generator.generate_field(
        field_name="meta_title",
        structured_data={"project_name": "Test Project", "developer": "Test Dev", "location": "Dubai"},
        template_type="opr",
    )

    assert result.content == "Fallback Title"
    assert result.prompt_version == "v1"  # Default version
```

**Step 5: Run tests**

Run: `pytest backend/tests/test_prompt_db_integration.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/content_generator.py backend/app/services/job_manager.py backend/tests/test_prompt_db_integration.py
git commit -m "fix: wire database session into prompt lookup pipeline

Previously db=None was hardcoded in content_generator.py:210,
causing all database-backed prompts to be ignored. Now the
AsyncSession is passed from job_manager through ContentGenerator
to PromptManager.get_prompt(), enabling admin-edited prompts
to take effect at generation time."
```

---

### Task 1.2: Update ContentGenerator singleton to handle db session lifecycle

**Files:**
- Modify: `backend/app/services/content_generator.py:437-454`

The current singleton pattern caches a single `ContentGenerator` instance. Since `db` sessions are request-scoped, the singleton must not cache the session.

**Step 1: Change approach -- make ContentGenerator non-singleton, instantiated per-pipeline-run**

In `content_generator.py`, remove the singleton pattern entirely. The `ContentGenerator` is cheap to construct (brand context and template prompts are small file reads that only happen once during init). Replace lines 437-454:

```python
def get_content_generator(db: Optional[AsyncSession] = None) -> ContentGenerator:
    """
    Create a ContentGenerator instance.

    Args:
        db: Optional database session for prompt lookups.
            When provided, prompts are read from the database.
            When None, falls back to hardcoded defaults.

    Returns:
        ContentGenerator instance
    """
    return ContentGenerator(db=db)
```

NOTE: If brand context / template file reads prove expensive, cache them at module level separately. But do NOT cache the db session.

**Step 2: Update job_manager.py to use factory**

At `job_manager.py` line 885-913, replace:

```python
from app.services.content_generator import ContentGenerator
# ...
generator = ContentGenerator()
```

with:

```python
from app.services.content_generator import get_content_generator
# ...
generator = get_content_generator(db=self.job_repo.db)
```

**Step 3: Commit**

```bash
git add backend/app/services/content_generator.py backend/app/services/job_manager.py
git commit -m "refactor: remove ContentGenerator singleton, pass db per pipeline run"
```

---

## Phase 2: Define Template-Specific Field Configurations

**Objective:** Each template type gets its own field set, character limits, and prompt content.

### Task 2.1: Create template field registry

**Files:**
- Create: `backend/app/services/template_fields.py`

This file defines exactly which fields each template type requires and their character limits. These replace the single `FIELD_LIMITS` dict.

**Step 1: Write the registry**

```python
"""
Template field definitions for all 6 template types.

Each template type maps to an ordered dict of field_name -> character_limit.
These define which fields ContentGenerator produces for each template.

Source of truth: docs/TEMPLATES_REFERENCE.md
Google Sheet: PDP Master - All Templates (1pef6Q-54l2mFOX6QgwOLQONviBijgaRgI7gA2GHn_Ck)
"""

from typing import Optional


# Type alias for field definitions: {field_name: character_limit_or_None}
FieldDefs = dict[str, Optional[int]]


# --- AGGREGATORS TEMPLATE ---
# Purpose: Third-party aggregator websites (24+ domains)
# Total fields: ~65 content fields
AGGREGATORS_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 160,
    "url_slug": None,
    "image_alt": 125,
    # Hero
    "h1": 70,
    "hero_description": 400,
    # About
    "about_h2": 50,
    "about_description": 700,
    "selling_point_1": 80,
    "selling_point_2": 80,
    "selling_point_3": 80,
    # Amenities (5 items)
    "amenities_h2": 50,
    "amenity_1_title": 40,
    "amenity_1_description": 150,
    "amenity_2_title": 40,
    "amenity_2_description": 150,
    "amenity_3_title": 40,
    "amenity_3_description": 150,
    "amenity_4_title": 40,
    "amenity_4_description": 150,
    "amenity_5_title": 40,
    "amenity_5_description": 150,
    # Payment Plan
    "payment_plan_h2": 50,
    "payment_plan_description": 800,
    # Location
    "location_h2": 50,
    "location_description": 550,
    "nearby_1": 80,
    "nearby_2": 80,
    "nearby_3": 80,
    "nearby_4": 80,
    # Developer
    "developer_h2": 50,
    "developer_description": 500,
    # FAQ (5 pairs)
    "faq_1_question": 80,
    "faq_1_answer": 200,
    "faq_2_question": 80,
    "faq_2_answer": 200,
    "faq_3_question": 80,
    "faq_3_answer": 200,
    "faq_4_question": 80,
    "faq_4_answer": 200,
    "faq_5_question": 80,
    "faq_5_answer": 200,
}


# --- OPR TEMPLATE ---
# Purpose: opr.ae - Dubai off-plan residential (investment-focused)
# Total fields: ~45 content fields
OPR_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 156,
    "url_slug": None,
    "image_alt": 125,
    # Hero
    "h1": 70,
    "hero_subheading": 150,
    # Project Details (data fields, not generated)
    # Overview
    "overview_h2": 50,
    "overview_description": 500,
    # Location Access (6-8 bullets)
    "location_access_1": 60,
    "location_access_2": 60,
    "location_access_3": 60,
    "location_access_4": 60,
    "location_access_5": 60,
    "location_access_6": 60,
    # Signature Features & Amenities
    "amenities_intro": 200,
    "amenity_bullet_1": 30,
    "amenity_bullet_2": 30,
    "amenity_bullet_3": 30,
    "amenity_bullet_4": 30,
    "amenity_bullet_5": 30,
    "amenity_bullet_6": 30,
    "amenity_bullet_7": 30,
    "amenity_bullet_8": 30,
    # Payment Plan
    "payment_plan_headline": 10,
    "payment_plan_description": 200,
    # Investment Opportunities
    "investment_intro": 200,
    "investment_bullet_1": 100,
    "investment_bullet_2": 100,
    "investment_bullet_3": 100,
    "investment_bullet_4": 100,
    # About the Area
    "area_description": 400,
    # Lifestyle & Attractions, Healthcare, Education
    "lifestyle_bullets": 400,
    "healthcare_bullets": 300,
    "education_bullets": 300,
    # Developer
    "developer_description": 300,
    # FAQ (12-18 Q&A)
    "faq_1_question": 100,
    "faq_1_answer": 200,
    "faq_2_question": 100,
    "faq_2_answer": 200,
    "faq_3_question": 100,
    "faq_3_answer": 200,
    "faq_4_question": 100,
    "faq_4_answer": 200,
    "faq_5_question": 100,
    "faq_5_answer": 200,
    "faq_6_question": 100,
    "faq_6_answer": 200,
    "faq_7_question": 100,
    "faq_7_answer": 200,
    "faq_8_question": 100,
    "faq_8_answer": 200,
    "faq_9_question": 100,
    "faq_9_answer": 200,
    "faq_10_question": 100,
    "faq_10_answer": 200,
    "faq_11_question": 100,
    "faq_11_answer": 200,
    "faq_12_question": 100,
    "faq_12_answer": 200,
}


# --- MPP TEMPLATE ---
# Purpose: main-portal.com - comprehensive project pages
# Total fields: ~75 content fields
MPP_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 160,
    "url_slug": None,
    "image_alt": 125,
    # Hero
    "h1": 70,
    "hero_description": 400,
    # Project Overview
    "overview_h2": 50,
    "overview_description": 700,
    # Payment Plan
    "payment_plan_h2": 50,
    "payment_plan_description": 800,
    # Key Points (2 with images)
    "key_point_1_title": 60,
    "key_point_1_description": 300,
    "key_point_2_title": 60,
    "key_point_2_description": 300,
    # Amenities (8 items)
    "amenities_h2": 50,
    "amenity_1_title": 40,
    "amenity_1_description": 150,
    "amenity_2_title": 40,
    "amenity_2_description": 150,
    "amenity_3_title": 40,
    "amenity_3_description": 150,
    "amenity_4_title": 40,
    "amenity_4_description": 150,
    "amenity_5_title": 40,
    "amenity_5_description": 150,
    "amenity_6_title": 40,
    "amenity_6_description": 150,
    "amenity_7_title": 40,
    "amenity_7_description": 150,
    "amenity_8_title": 40,
    "amenity_8_description": 150,
    # Location
    "location_h2": 50,
    "location_description": 550,
    "location_area_description": 400,
    "location_future_dev": 300,
    # Developer
    "developer_h2": 50,
    "developer_description": 500,
    "developer_stat_1": 60,
    "developer_stat_2": 60,
    "developer_stat_3": 60,
    # FAQ (5 pairs)
    "faq_1_question": 80,
    "faq_1_answer": 200,
    "faq_2_question": 80,
    "faq_2_answer": 200,
    "faq_3_question": 80,
    "faq_3_answer": 200,
    "faq_4_question": 80,
    "faq_4_answer": 200,
    "faq_5_question": 80,
    "faq_5_answer": 200,
}


# --- ADOP TEMPLATE ---
# Purpose: abudhabioffplan.ae - Abu Dhabi new development projects
# Total fields: ~55 content fields
ADOP_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 160,
    "url_slug": None,
    "image_alt": 125,
    # Hero
    "h1": 70,
    "hero_description": 400,
    # About Project (3 paragraphs)
    "about_h2": 50,
    "about_paragraph_1": 500,
    "about_paragraph_2": 500,
    "about_paragraph_3": 500,
    # Key Benefits
    "key_benefits_h2": 50,
    "key_benefit_1": 150,
    "key_benefit_2": 150,
    "key_benefit_3": 150,
    # Area Infrastructure
    "infrastructure_h2": 50,
    "infrastructure_description": 500,
    "infrastructure_bullet_1": 100,
    "infrastructure_bullet_2": 100,
    "infrastructure_bullet_3": 100,
    "infrastructure_bullet_4": 100,
    # Investment
    "investment_h2": 50,
    "investment_description": 500,
    "investment_bullet_1": 100,
    "investment_bullet_2": 100,
    "investment_bullet_3": 100,
    # Developer
    "developer_h2": 50,
    "developer_description": 500,
    # FAQ (8 Q&A pairs)
    "faq_1_question": 80,
    "faq_1_answer": 200,
    "faq_2_question": 80,
    "faq_2_answer": 200,
    "faq_3_question": 80,
    "faq_3_answer": 200,
    "faq_4_question": 80,
    "faq_4_answer": 200,
    "faq_5_question": 80,
    "faq_5_answer": 200,
    "faq_6_question": 80,
    "faq_6_answer": 200,
    "faq_7_question": 80,
    "faq_7_answer": 200,
    "faq_8_question": 80,
    "faq_8_answer": 200,
}


# --- ADRE TEMPLATE ---
# Purpose: secondary-market-portal.com - Abu Dhabi ready/secondary market
# Total fields: ~65 content fields
ADRE_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 160,
    "url_slug": None,
    "image_alt": 125,
    # Hero
    "h1": 70,
    "hero_marketing_h2": 60,
    "hero_description": 400,
    # Amenities (detailed with H3 subheads)
    "amenities_h2": 50,
    "amenity_1_h3": 40,
    "amenity_1_description": 200,
    "amenity_2_h3": 40,
    "amenity_2_description": 200,
    "amenity_3_h3": 40,
    "amenity_3_description": 200,
    "amenity_4_h3": 40,
    "amenity_4_description": 200,
    "amenity_5_h3": 40,
    "amenity_5_description": 200,
    # Developer
    "developer_h2": 50,
    "developer_description": 500,
    # Economic Appeal
    "economic_appeal_h2": 50,
    "rental_appeal": 300,
    "resale_appeal": 300,
    "enduser_appeal": 300,
    # Location (categorized)
    "location_h2": 50,
    "location_description": 550,
    "entertainment_1": 80,
    "entertainment_2": 80,
    "entertainment_3": 80,
    "healthcare_1": 80,
    "healthcare_2": 80,
    "healthcare_3": 80,
    "education_1": 80,
    "education_2": 80,
    "education_3": 80,
    # FAQ (8 pairs)
    "faq_1_question": 80,
    "faq_1_answer": 200,
    "faq_2_question": 80,
    "faq_2_answer": 200,
    "faq_3_question": 80,
    "faq_3_answer": 200,
    "faq_4_question": 80,
    "faq_4_answer": 200,
    "faq_5_question": 80,
    "faq_5_answer": 200,
    "faq_6_question": 80,
    "faq_6_answer": 200,
    "faq_7_question": 80,
    "faq_7_answer": 200,
    "faq_8_question": 80,
    "faq_8_answer": 200,
}


# --- COMMERCIAL TEMPLATE ---
# Purpose: cre.main-portal.com - Office and retail projects
# Total fields: ~70 content fields
COMMERCIAL_FIELDS: FieldDefs = {
    # SEO
    "meta_title": 60,
    "meta_description": 160,
    "url_slug": None,
    "image_alt": 125,
    # Hero (with 3 economic indicators)
    "h1": 70,
    "hero_description": 400,
    "economic_indicator_1_label": 30,
    "economic_indicator_1_value": 20,
    "economic_indicator_2_label": 30,
    "economic_indicator_2_value": 20,
    "economic_indicator_3_label": 30,
    "economic_indicator_3_value": 20,
    # About Area
    "area_h2": 50,
    "area_description": 500,
    # Project Details / Passport
    "project_passport_h2": 50,
    "project_passport_description": 400,
    # Economic Appeal
    "economic_appeal_h2": 50,
    "economic_appeal_description": 500,
    # Payment Plan
    "payment_plan_h2": 50,
    "payment_plan_description": 800,
    # Advantages (3 items)
    "advantage_1_title": 60,
    "advantage_1_description": 200,
    "advantage_2_title": 60,
    "advantage_2_description": 200,
    "advantage_3_title": 60,
    "advantage_3_description": 200,
    # Amenities (5 items)
    "amenities_h2": 50,
    "amenity_1_title": 40,
    "amenity_1_description": 150,
    "amenity_2_title": 40,
    "amenity_2_description": 150,
    "amenity_3_title": 40,
    "amenity_3_description": 150,
    "amenity_4_title": 40,
    "amenity_4_description": 150,
    "amenity_5_title": 40,
    "amenity_5_description": 150,
    # Developer
    "developer_h2": 50,
    "developer_description": 500,
    # Location (Social/Education/Medicine)
    "location_h2": 50,
    "location_description": 550,
    "social_facility_1": 80,
    "social_facility_2": 80,
    "social_facility_3": 80,
    "education_nearby_1": 80,
    "education_nearby_2": 80,
    "education_nearby_3": 80,
    "medical_nearby_1": 80,
    "medical_nearby_2": 80,
    "medical_nearby_3": 80,
}


# --- REGISTRY ---

TEMPLATE_FIELD_REGISTRY: dict[str, FieldDefs] = {
    "aggregators": AGGREGATORS_FIELDS,
    "opr": OPR_FIELDS,
    "mpp": MPP_FIELDS,
    "adop": ADOP_FIELDS,
    "adre": ADRE_FIELDS,
    "commercial": COMMERCIAL_FIELDS,
}


def get_fields_for_template(template_type: str) -> FieldDefs:
    """
    Get field definitions for a template type.

    Args:
        template_type: One of: aggregators, opr, mpp, adop, adre, commercial

    Returns:
        Dict mapping field_name -> character_limit (or None)

    Raises:
        ValueError: If template_type is not recognized
    """
    if template_type not in TEMPLATE_FIELD_REGISTRY:
        raise ValueError(
            f"Unknown template type: {template_type}. "
            f"Valid types: {list(TEMPLATE_FIELD_REGISTRY.keys())}"
        )
    return TEMPLATE_FIELD_REGISTRY[template_type]
```

**Step 2: Write test**

Create: `backend/tests/test_template_fields.py`

```python
"""Test template field registry."""
import pytest
from app.services.template_fields import (
    get_fields_for_template,
    TEMPLATE_FIELD_REGISTRY,
    AGGREGATORS_FIELDS,
    OPR_FIELDS,
    MPP_FIELDS,
    ADOP_FIELDS,
    ADRE_FIELDS,
    COMMERCIAL_FIELDS,
)


def test_all_six_templates_registered():
    assert set(TEMPLATE_FIELD_REGISTRY.keys()) == {
        "aggregators", "opr", "mpp", "adop", "adre", "commercial"
    }


@pytest.mark.parametrize("template_type,min_fields", [
    ("aggregators", 30),
    ("opr", 40),
    ("mpp", 30),
    ("adop", 25),
    ("adre", 30),
    ("commercial", 30),
])
def test_template_has_minimum_field_count(template_type, min_fields):
    fields = get_fields_for_template(template_type)
    assert len(fields) >= min_fields, (
        f"{template_type} has {len(fields)} fields, expected >= {min_fields}"
    )


def test_all_templates_have_seo_fields():
    required_seo = {"meta_title", "meta_description", "url_slug", "h1"}
    for name, fields in TEMPLATE_FIELD_REGISTRY.items():
        assert required_seo.issubset(fields.keys()), (
            f"{name} missing SEO fields: {required_seo - fields.keys()}"
        )


def test_unknown_template_raises():
    with pytest.raises(ValueError, match="Unknown template type"):
        get_fields_for_template("nonexistent")


def test_character_limits_are_positive_or_none():
    for name, fields in TEMPLATE_FIELD_REGISTRY.items():
        for field_name, limit in fields.items():
            if limit is not None:
                assert limit > 0, f"{name}.{field_name} has non-positive limit: {limit}"
```

**Step 3: Run tests**

Run: `pytest backend/tests/test_template_fields.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/template_fields.py backend/tests/test_template_fields.py
git commit -m "feat: add template field registry for all 6 template types

Defines per-template field sets with character limits based on
TEMPLATES_REFERENCE.md and the PDP Master Google Sheet.
Replaces the single 10-field FIELD_LIMITS dict."
```

---

### Task 2.2: Integrate template field registry into ContentGenerator

**Files:**
- Modify: `backend/app/services/content_generator.py:55-70, 97-175`

**Step 1: Replace FIELD_LIMITS with template-specific lookup**

Remove the `FIELD_LIMITS` class variable (lines 58-70) and update `generate_all()`:

```python
# At top of content_generator.py, add import:
from app.services.template_fields import get_fields_for_template

# In ContentGenerator class, remove FIELD_LIMITS dict entirely.
# Then in generate_all() at line 135, replace:
#   fields_to_generate = list(self.FIELD_LIMITS.keys())
# with:
    template_fields = get_fields_for_template(template_type)
    fields_to_generate = list(template_fields.keys())
```

And update the character limit lookup in the loop (line 147):

```python
    character_limit = template_fields.get(field_name)
```

Also update the field validation in `generate_field()` at line 201-202:

```python
# Replace:
#   if field_name not in self.FIELD_LIMITS:
#       raise ValueError(f"Unknown field: {field_name}")
# with:
    template_fields = get_fields_for_template(template_type)
    if field_name not in template_fields:
        raise ValueError(f"Unknown field '{field_name}' for template '{template_type}'")
```

And the limit lookup at line 222:

```python
# Replace:
#   limit = character_limit or self.FIELD_LIMITS.get(field_name)
# with:
    limit = character_limit or template_fields.get(field_name)
```

**Step 2: Write test**

Add to `backend/tests/test_prompt_db_integration.py`:

```python
@pytest.mark.asyncio
async def test_generate_all_uses_template_specific_fields():
    """generate_all() should use template-specific field set."""
    from app.services.template_fields import get_fields_for_template

    generator = ContentGenerator(db=None)

    # Mock the API so we don't actually call Claude
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated content")]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)
    generator.client.messages_create = AsyncMock(return_value=mock_response)

    result = await generator.generate_all(
        structured_data={"project_name": "Test", "developer": "Dev", "location": "Dubai"},
        template_type="aggregators",
    )

    aggregator_fields = get_fields_for_template("aggregators")
    # All generated fields should be from the aggregators field set
    for field_name in result.fields:
        assert field_name in aggregator_fields, (
            f"Field '{field_name}' generated but not in aggregators template"
        )
```

**Step 3: Run tests**

Run: `pytest backend/tests/test_prompt_db_integration.py -v`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/app/services/content_generator.py backend/tests/test_prompt_db_integration.py
git commit -m "feat: use template-specific field sets in content generation

ContentGenerator now generates fields defined per template type
instead of the same 10 fields for all templates."
```

---

### Task 2.3: Make PromptManager template-aware for defaults

**Files:**
- Modify: `backend/app/services/prompt_manager.py:159-369`

**Step 1: Restructure defaults by template type**

The current `get_default_prompts()` returns a flat dict. Restructure it to be keyed by `(template_type, field_name)` so different templates get different default prompts.

Replace `get_default_prompts()` with:

```python
def get_default_prompts(self) -> dict:
    """
    Get all default prompt templates.

    Returns:
        Dictionary keyed by field_name. For template-specific prompts,
        keys are "{template_type}:{field_name}".
        Falls back to generic prompts when template-specific not found.
    """
    # Generic prompts (fallback for any template type)
    generic = self._get_generic_field_prompts()

    # Template-specific overrides
    # OPR: investment-focused, neutral tone, ROI emphasis
    opr_overrides = self._get_opr_prompts()
    # Aggregators: SEO-focused, searchability
    agg_overrides = self._get_aggregators_prompts()
    # MPP: balanced buyers/investors
    mpp_overrides = self._get_mpp_prompts()
    # ADOP: Abu Dhabi new developments
    adop_overrides = self._get_adop_prompts()
    # ADRE: Abu Dhabi secondary market
    adre_overrides = self._get_adre_prompts()
    # Commercial: B2B, office/retail
    commercial_overrides = self._get_commercial_prompts()

    # Merge: template-specific keys override generic
    merged = dict(generic)
    for template_type, overrides in [
        ("opr", opr_overrides),
        ("aggregators", agg_overrides),
        ("mpp", mpp_overrides),
        ("adop", adop_overrides),
        ("adre", adre_overrides),
        ("commercial", commercial_overrides),
    ]:
        for field_name, prompt_data in overrides.items():
            merged[f"{template_type}:{field_name}"] = prompt_data

    return merged
```

Then update `get_prompt()` lookup (line 91-108) to check template-specific key first:

```python
# Fall back to default prompts
template_key = f"{template_type}:{field_name}"

# Try template-specific default first
if template_key in self.default_prompts:
    prompt_dict = self.default_prompts[template_key]
elif field_name in self.default_prompts:
    prompt_dict = self.default_prompts[field_name]
else:
    logger.warning("No default prompt for field '%s' (template=%s), using generic", field_name, template_type)
    return self._get_generic_prompt(field_name, template_type)

logger.debug(
    "Using default prompt: %s (template=%s, variant=%s)",
    field_name, template_type, variant
)

return PromptTemplate(
    field_name=field_name,
    template_type=template_type,
    content=prompt_dict["content"],
    character_limit=prompt_dict.get("character_limit"),
    version=prompt_dict.get("version", 1)
)
```

**Step 2: Implement template-specific prompt methods**

Each method returns prompts for fields unique to that template. These are long -- each template has 30-70 fields. The prompts should follow the patterns established in `prompt  opr.md` and `TEMPLATES_REFERENCE.md`.

NOTE TO IMPLEMENTER: The exact prompt text for each field is the most important part of this system. Each prompt must:
- Reference the correct field character limits from `template_fields.py`
- Use the correct tone for the template (investment for OPR, SEO for aggregators, B2B for commercial)
- Include all required `{placeholder}` variables
- End with "Return ONLY the [field] text, nothing else."
- Follow brand guidelines (no prohibited terms)

This is content-heavy work. Start with `_get_generic_field_prompts()` (the existing 10 prompts renamed) and then create one method per template type. Each method only needs to define prompts for fields that are DIFFERENT from the generic set.

Example skeleton for one template:

```python
def _get_aggregators_prompts(self) -> dict:
    """Aggregator-specific prompt overrides. SEO-focused."""
    return {
        "about_h2": {
            "content": """Generate an H2 heading for the About section of this property listing.

Project: {project_name}
Location: {location}

Requirements:
- 20-50 characters
- Include project name or location
- SEO-optimized for property search
- Informative, not salesy

Return ONLY the H2 text, nothing else.""",
            "character_limit": 50,
            "version": 1,
        },
        "about_description": {
            "content": """Write the About section description for this property listing page.

Project: {project_name}
Developer: {developer}
Location: {location}
Price: {starting_price}
Handover: {handover_date}
Property Types: {property_types}
Amenities: {amenities}

Requirements:
- 400-700 characters
- First sentence: what the project is and where
- Second: key features and property types
- Third: target buyer and investment appeal
- SEO-optimized with natural keyword placement
- Professional advisor tone
- No prohibited marketing terms

Return ONLY the description text, nothing else.""",
            "character_limit": 700,
            "version": 1,
        },
        # ... remaining aggregator-specific fields
    }
```

**IMPORTANT:** Writing all 6 template prompt methods is the largest task in this plan. Budget accordingly. Each method should cover every field in the corresponding `*_FIELDS` dict from `template_fields.py` that is NOT already covered by the generic defaults.

**Step 3: Commit**

```bash
git add backend/app/services/prompt_manager.py
git commit -m "feat: template-specific default prompts for all 6 template types

PromptManager now returns different default prompts based on
template_type. Each template has tone, field, and character
limit requirements matching TEMPLATES_REFERENCE.md."
```

---

## Phase 3: Seed Script and Deployment

**Objective:** Populate the database with all prompts for all 6 templates so admin UI has content to manage.

### Task 3.1: Rewrite seed_prompts.py for all 6 template types

**Files:**
- Modify: `backend/scripts/seed_prompts.py`

**Step 1: Update seed script**

Replace the existing script. Key changes:
- Iterate all 6 template types (not just OPR)
- Seed field prompts for every field in each template's field registry
- Seed both `standard` and `luxury` variants
- Use upsert logic (skip if exists, or force-update with `--force` flag)

```python
"""
Seed script to populate prompts table for all 6 template types.

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
```

**Step 2: Commit**

```bash
git add backend/scripts/seed_prompts.py
git commit -m "feat: rewrite seed script for all 6 template types

Seeds prompts for every field across aggregators, opr, mpp,
adop, adre, and commercial templates. Supports --force flag
to overwrite existing prompts."
```

---

### Task 3.2: Remove dead template prompt file loading

**Files:**
- Modify: `backend/app/services/content_generator.py:360-394, 396-434`

The `_load_template_prompts()` and `_build_system_message()` methods load `.md` files from `reference/company/prompts/` and inject them as system-level context. With database-backed per-field prompts now active, these file-based template prompts create a confusing dual-path.

**Step 1: Simplify system message building**

The system message should contain:
1. Brand context (from `brand-context-prompt.md` -- keep this)
2. Template type identifier
3. NO template-specific prompt file content (that is now in the per-field prompts)

Replace `_load_template_prompts()` and `_build_system_message()`:

```python
def _build_system_message(self, template_type: str) -> str:
    """
    Build system message with brand context and template type.

    Args:
        template_type: Template type (aggregators, opr, mpp, etc.)

    Returns:
        Complete system message for Claude
    """
    template_descriptions = {
        "aggregators": "Content for third-party property listing aggregator websites. Focus on SEO, searchability, and clear property information for comparison shoppers.",
        "opr": "Content for opr.ae, the Off-Plan Real Estate website. Emphasize investment potential, ROI data, payment plan structure, and factual property analysis for investors.",
        "mpp": "Content for main-portal.com, the the company main site. Balanced approach for both end-user buyers and investors with comprehensive project information.",
        "adop": "Content for abudhabioffplan.ae, Abu Dhabi off-plan developments. Focus on new project features, area infrastructure, and investment benefits specific to Abu Dhabi market.",
        "adre": "Content for secondary-market-portal.com, Abu Dhabi ready/secondary market. Cover economic appeal for rental, resale, and end-user segments with location-categorized information.",
        "commercial": "Content for cre.main-portal.com, commercial real estate (office/retail). Professional B2B tone with economic indicators, project passport data, and business-focused amenities.",
    }

    template_context = template_descriptions.get(
        template_type,
        "General real estate content for Dubai/UAE property market."
    )

    return f"""{self.brand_context}

TEMPLATE TYPE: {template_type.upper()}
TEMPLATE CONTEXT: {template_context}

Generate content that follows these brand guidelines strictly. Return ONLY the requested content, no additional commentary or formatting."""
```

Remove `_load_template_prompts()` method and the `self.template_prompts` attribute from `__init__`.

**Step 2: Commit**

```bash
git add backend/app/services/content_generator.py
git commit -m "refactor: simplify system message, remove file-based template prompts

Template-specific instructions are now in per-field database prompts.
System message provides brand context + template type description only."
```

---

### Task 3.3: Validation -- end-to-end smoke test

**Files:**
- Create: `backend/tests/test_prompt_system_e2e.py`

**Step 1: Write integration test**

```python
"""End-to-end smoke tests for prompt system."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.content_generator import ContentGenerator
from app.services.template_fields import TEMPLATE_FIELD_REGISTRY


@pytest.mark.asyncio
@pytest.mark.parametrize("template_type", list(TEMPLATE_FIELD_REGISTRY.keys()))
async def test_all_templates_generate_without_errors(template_type):
    """Every template type should generate all its fields without errors."""
    generator = ContentGenerator(db=None)

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated test content")]
    mock_response.usage = MagicMock(input_tokens=50, output_tokens=20)
    generator.client.messages_create = AsyncMock(return_value=mock_response)

    sample_data = {
        "project_name": "Test Residences",
        "developer": "Test Properties",
        "location": "Dubai Marina",
        "emirate": "Dubai",
        "starting_price": 1500000,
        "handover_date": "Q4 2027",
        "amenities": ["Pool", "Gym", "Spa", "Kids Area", "BBQ"],
        "property_types": ["1BR", "2BR", "3BR"],
        "payment_plan": "60/40",
        "description": "A test project for validation.",
    }

    result = await generator.generate_all(sample_data, template_type)

    expected_fields = set(TEMPLATE_FIELD_REGISTRY[template_type].keys())
    generated_fields = set(result.fields.keys())

    # All expected fields should have been attempted
    # (some may be in errors if prompt formatting fails, but none should crash)
    assert len(result.errors) == 0, f"Errors: {result.errors}"
    assert generated_fields == expected_fields, (
        f"Missing: {expected_fields - generated_fields}, "
        f"Extra: {generated_fields - expected_fields}"
    )
```

**Step 2: Run all tests**

Run: `pytest backend/tests/test_prompt_system_e2e.py backend/tests/test_prompt_db_integration.py backend/tests/test_template_fields.py -v`
Expected: ALL PASS

**Step 3: Commit**

```bash
git add backend/tests/test_prompt_system_e2e.py
git commit -m "test: add end-to-end smoke tests for all 6 template types"
```

---

## Implementation Order and Dependencies

```
Phase 1 (wiring)
  Task 1.1: Pass db session           <- no dependencies
  Task 1.2: Remove singleton          <- depends on 1.1

Phase 2 (field definitions)
  Task 2.1: Template field registry   <- no dependencies (can parallel with Phase 1)
  Task 2.2: Integrate into generator  <- depends on 2.1 + 1.1
  Task 2.3: Template-aware defaults   <- depends on 2.1

Phase 3 (deployment)
  Task 3.1: Rewrite seed script       <- depends on 2.1 + 2.3
  Task 3.2: Remove dead file loading  <- depends on 2.2
  Task 3.3: E2E smoke test            <- depends on all above
```

Tasks 1.1 and 2.1 can be done in parallel. Everything else is sequential.

---

## Files Modified (Summary)

| File | Action | Tasks |
|------|--------|-------|
| `backend/app/services/content_generator.py` | Modify | 1.1, 1.2, 2.2, 3.2 |
| `backend/app/services/job_manager.py` | Modify | 1.1, 1.2 |
| `backend/app/services/prompt_manager.py` | Modify | 2.3 |
| `backend/app/services/template_fields.py` | Create | 2.1 |
| `backend/scripts/seed_prompts.py` | Rewrite | 3.1 |
| `backend/tests/test_prompt_db_integration.py` | Create | 1.1, 2.2 |
| `backend/tests/test_template_fields.py` | Create | 2.1 |
| `backend/tests/test_prompt_system_e2e.py` | Create | 3.3 |

## What This Plan Does NOT Cover

1. **Writing the actual prompt text for all ~350 fields across 6 templates.** Task 2.3 provides the structure and skeleton methods, but the prompt copywriting is a content task that requires domain expertise and iterative testing with Claude output quality. The generic defaults will work as fallbacks.

2. **Google Sheets field mapping.** The `_step_populate_sheet()` in job_manager.py writes generated content to Google Sheets. The field names in `template_fields.py` must eventually map to Sheet cell addresses. That is a separate task.

3. **Frontend prompt editor updates.** The admin UI already has CRUD for prompts. Once the database path is live, it should work. But the UI may need updates to show template-specific field lists.

4. **Luxury variant prompts.** This plan seeds `standard` variant only. Luxury variant prompts are a content task.
