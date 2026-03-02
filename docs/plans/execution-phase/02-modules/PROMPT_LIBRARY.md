# Module: Prompt Library

**Module Number:** 6
**Category:** AI Configuration
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Prompt Organization](#prompt-organization)
7. [API Endpoints](#api-endpoints)
8. [UI Components](#ui-components)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Prompt Library Module** provides centralized, version-controlled management of all AI prompts used throughout the PDP automation system. It organizes prompts by website and template type, tracks all changes with complete version history, and enables pre-generation customization for optimal content quality.

**Position in System:** Configuration layer supporting content generation with reusable, versioned prompt templates.

---

## Purpose & Goals

### Primary Purpose

Maintain a centralized repository of AI prompts with full version control, enabling prompt optimization, reuse, and customization while preserving historical performance data.

### Goals

1. **Centralization:** Single source of truth for all AI prompts
2. **Version Control:** Track every prompt change with user attribution
3. **Reusability:** Share successful prompts across projects
4. **Customization:** Pre-generation prompt editing
5. **Organization:** Group by website, template type, and field
6. **Performance Tracking:** Link prompts to content quality metrics
7. **Rollback Capability:** Revert to previous prompt versions
8. **Collaboration:** Share and review prompt improvements

---

## Key Features

### Core Capabilities

- ✅ **Version Control** - Complete history of all prompt changes
- ✅ **Template Organization** - Group by template type (Aggregators, OPR, MPP, ADOP, ADRE, Commercial) and content type
- ✅ **Field-Level Prompts** - Individual prompts for each content field
- ✅ **Pre-Generation Editing** - Customize prompts before content generation
- ✅ **Prompt Reuse** - Save and reapply successful prompt patterns
- ✅ **Change History** - Track who changed what and when
- ✅ **Diff Viewer** - Compare prompt versions side-by-side
- ✅ **Performance Metrics** - Link prompts to QA scores
- ✅ **Active/Archived Status** - Manage prompt lifecycle
- ✅ **Import/Export** - Backup and share prompt libraries

### Prompt Categories

**By Template Type:**
- Aggregators prompts (24+ third-party aggregator domains)
- OPR prompts (opr.ae)
- MPP prompts (main-portal.com)
- ADOP prompts (abudhabioffplan.ae)
- ADRE prompts (secondary-market-portal.com)
- Commercial prompts (cre.main-portal.com)

**By Content Type:**
- SEO metadata (meta title, description, URL slug)
- Page content (H1, overview, descriptions)
- Specialized content (amenities, investment highlights, FAQs)
- Image content (alt tags)

**By Field:**
Each content field has its own dedicated prompt with specific requirements and character limits.

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • PromptsPage.tsx            - Browse/search prompts   │
│ • PromptEditorPage.tsx       - Edit with preview       │
│ • PromptVersionHistory.tsx   - View change history     │
│ • PromptCustomizer.tsx       - Pre-gen customization   │
│ • PromptDiffViewer.tsx       - Compare versions        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/prompts               - CRUD operations         │
│ • /api/prompts/versions      - Version management      │
│ • /api/prompts/templates     - Template retrieval      │
│ • /api/prompts/customize     - Pre-gen customization   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • PromptService              - Business logic          │
│ • PromptVersionService       - Version control         │
│ • PromptTemplateService      - Template management     │
│ • PromptPerformanceTracker   - Quality metrics         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ • prompts                    - Active prompts          │
│ • prompt_versions            - Version history         │
│ • prompt_templates           - Reusable templates      │
│ • prompt_performance         - Quality metrics         │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `prompts`

**Purpose:** Store active prompts for content generation

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identification
    name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'opr_meta_title'
    display_name VARCHAR(100) NOT NULL,  -- e.g., 'OPR Meta Title'

    -- Organization
    template_type VARCHAR(50) NOT NULL,  -- 'aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'
    content_variant VARCHAR(50),     -- 'standard', 'luxury', etc.
    field_name VARCHAR(100),       -- 'meta_title', 'overview', etc.
    category VARCHAR(50),          -- 'seo', 'content', 'image'

    -- Prompt Content
    content TEXT NOT NULL,
    -- Example:
    -- "Generate a compelling meta title (max 60 characters) for this
    --  off-plan project. Include the project name and 'Off-Plan Dubai'.
    --  Focus on luxury and location. Format: {Project Name} | {Key Selling Point}."

    -- Specifications
    character_limit INTEGER,       -- Max output length
    required_elements JSONB,       -- ["project_name", "location"]
    output_format VARCHAR(50),     -- 'text', 'list', 'json'

    -- AI Configuration
    model VARCHAR(50) DEFAULT 'claude-sonnet-4-5-20241022',
    temperature DECIMAL(2, 1) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 500,

    -- Version Control
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,

    -- Description
    description TEXT,
    usage_notes TEXT,

    -- Performance
    usage_count INTEGER DEFAULT 0,
    average_qa_score DECIMAL(3, 2),
    last_used_at TIMESTAMP,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_template_type CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial')),
    CONSTRAINT valid_temperature CHECK (temperature BETWEEN 0 AND 2),
    CONSTRAINT valid_qa_score CHECK (average_qa_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_prompts_name ON prompts(name);
CREATE INDEX idx_prompts_template_type ON prompts(template_type);
CREATE INDEX idx_prompts_field ON prompts(field_name);
CREATE INDEX idx_prompts_active ON prompts(is_active) WHERE is_active = true;
CREATE INDEX idx_prompts_category ON prompts(category);
```

---

### Table: `prompt_versions`

**Purpose:** Complete version history of all prompt changes

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,

    -- Version Information
    version INTEGER NOT NULL,
    content TEXT NOT NULL,

    -- Specifications (snapshot at this version)
    character_limit INTEGER,
    required_elements JSONB,
    model VARCHAR(50),
    temperature DECIMAL(2, 1),

    -- Change Information
    changed_by UUID REFERENCES users(id),
    change_reason VARCHAR(255),
    change_notes TEXT,
    change_type VARCHAR(50),
    -- Types: 'created', 'content_updated', 'spec_updated', 'performance_improvement'

    -- Comparison with Previous Version
    diff_summary TEXT,  -- High-level summary of changes

    -- Performance (if available)
    avg_qa_score_at_version DECIMAL(3, 2),
    usage_count_at_version INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id),
    CONSTRAINT unique_prompt_version UNIQUE (prompt_id, version)
);

CREATE INDEX idx_prompt_versions_prompt ON prompt_versions(prompt_id);
CREATE INDEX idx_prompt_versions_version ON prompt_versions(prompt_id, version DESC);
CREATE INDEX idx_prompt_versions_changed_by ON prompt_versions(changed_by);
```

---

### Table: `prompt_templates`

**Purpose:** Reusable prompt template sets

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template Information
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Organization
    template_type VARCHAR(50) NOT NULL,
    content_variant VARCHAR(50),

    -- Template Content
    prompts JSONB NOT NULL,
    -- {
    --   "meta_title": "prompt_id_1",
    --   "meta_description": "prompt_id_2",
    --   "overview": "prompt_id_3",
    --   ...
    -- }

    -- Usage
    is_default BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_template_type CHECK (template_type IN ('aggregators', 'opr', 'mpp', 'adop', 'adre', 'commercial'))
);

CREATE INDEX idx_prompt_templates_template_type ON prompt_templates(template_type);
CREATE INDEX idx_prompt_templates_default ON prompt_templates(is_default)
    WHERE is_default = true;
```

---

### Table: `prompt_performance`

**Purpose:** Track prompt effectiveness and quality metrics

```sql
CREATE TABLE prompt_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    prompt_version INTEGER,

    -- Usage Instance
    project_id UUID REFERENCES projects(id),
    generated_content_id UUID REFERENCES generated_content(id),

    -- Quality Metrics
    qa_score DECIMAL(3, 2),
    factual_accuracy_score DECIMAL(3, 2),
    compliance_score DECIMAL(3, 2),

    -- User Feedback
    user_rating INTEGER,  -- 1-5 stars
    user_feedback TEXT,

    -- Generation Metrics
    tokens_used INTEGER,
    generation_time_ms INTEGER,
    character_count INTEGER,
    met_char_limit BOOLEAN,

    -- Result
    was_regenerated BOOLEAN DEFAULT false,
    final_status VARCHAR(50),  -- 'approved', 'rejected', 'modified'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_prompt FOREIGN KEY (prompt_id) REFERENCES prompts(id),
    CONSTRAINT valid_qa_score CHECK (qa_score BETWEEN 0 AND 1),
    CONSTRAINT valid_rating CHECK (user_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_prompt_performance_prompt ON prompt_performance(prompt_id);
CREATE INDEX idx_prompt_performance_project ON prompt_performance(project_id);
CREATE INDEX idx_prompt_performance_qa_score ON prompt_performance(qa_score DESC);
```

---

## Prompt Organization

### Template-Specific Prompts

Prompts are organized by template type. Each template shares common prompt patterns with site-specific variations.

**Common SEO Prompts (All Templates):**
```yaml
meta_title:
  display_name: "Meta Title"
  category: "seo"
  char_limit: 60
  content: |
    Generate a compelling meta title (max 60 characters) for this Dubai
    off-plan project. Include the project name and location. Format:
    "{Project Name} | Off-Plan Dubai" or "{Project Name} by {Developer} | Dubai"

meta_description:
  display_name: "Meta Description"
  category: "seo"
  char_limit: 160
  content: |
    Create an engaging meta description (max 160 characters) highlighting
    the project's key selling points: location, developer reputation,
    starting price, and main amenities. Include a call-to-action.

url_slug:
  display_name: "URL Slug"
  category: "seo"
  char_limit: 100
  content: |
    Generate an SEO-friendly URL slug using lowercase, hyphens only.
    Format: {project-name}-{developer-name}
    Example: downtown-elite-residence-emaar
```

**Common Content Prompts (All Templates):**
```yaml
h1_heading:
  display_name: "H1 Heading"
  category: "content"
  char_limit: 70
  content: |
    Create an H1 heading (max 70 characters) with format:
    "{Project Name} by {Developer} | {Location}"

overview_paragraph_1:
  display_name: "Overview - First Paragraph"
  category: "content"
  char_limit: 500
  content: |
    Write an engaging opening paragraph (300-500 characters) introducing
    the project. Focus on luxury, lifestyle, and unique selling points.
    Mention the developer's reputation and project location.

overview_paragraph_2:
  display_name: "Overview - Second Paragraph"
  category: "content"
  char_limit: 500
  content: |
    Write a second paragraph (300-500 characters) describing the location
    benefits, connectivity, and nearby landmarks. Emphasize convenience
    and lifestyle advantages.

amenities_intro:
  display_name: "Amenities Introduction"
  category: "content"
  char_limit: 300
  content: |
    Write a brief introduction (200-300 characters) to the project's
    amenities, emphasizing world-class facilities and luxury lifestyle.

investment_highlights:
  display_name: "Investment Highlights"
  category: "content"
  char_limit: 600
  content: |
    Create an investment-focused paragraph (400-600 characters)
    highlighting ROI potential, payment plan benefits, handover timeline,
    and developer track record.
```

**Image Prompts (All Templates):**
```yaml
image_alt_text:
  display_name: "Image Alt Text Generator"
  category: "image"
  char_limit: 125
  content: |
    Generate SEO-optimized alt text (max 125 characters) for this image.
    Describe what's shown, include project name, and use relevant keywords
    like "luxury", "Dubai", "off-plan", etc.
```

---

### Commercial Template Prompts

```yaml
commercial_meta_title:
  display_name: "Meta Title (Commercial)"
  category: "seo"
  char_limit: 60
  content: |
    Generate a commercial property meta title (max 60 characters).
    Focus on business benefits, location, and ROI potential.
    Format: "{Project Name} | Commercial Property Dubai"

commercial_roi_calculator_intro:
  display_name: "ROI Calculator Introduction"
  category: "content"
  char_limit: 400
  content: |
    Write an introduction (300-400 characters) for the ROI calculator
    section, emphasizing commercial investment returns, rental yields,
    and business opportunities.
```

---

## API Endpoints

### Prompt Management

#### `GET /api/prompts`

**Description:** List all prompts with filters

**Query Parameters:**
```typescript
{
  template_type?: 'aggregators' | 'opr' | 'mpp' | 'adop' | 'adre' | 'commercial';
  category?: 'seo' | 'content' | 'image';
  field_name?: string;
  is_active?: boolean;
  search?: string;
}
```

**Response:**
```json
{
  "prompts": [
    {
      "id": "uuid",
      "name": "opr_meta_title",
      "display_name": "OPR Meta Title",
      "template_type": "opr",
      "category": "seo",
      "field_name": "meta_title",
      "character_limit": 60,
      "version": 3,
      "usage_count": 245,
      "average_qa_score": 0.92,
      "last_used_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

#### `GET /api/prompts/{id}`

**Description:** Get prompt details with current content

**Response:**
```json
{
  "id": "uuid",
  "name": "opr_meta_title",
  "display_name": "OPR Meta Title",
  "content": "Generate a compelling meta title...",
  "template_type": "opr",
  "category": "seo",
  "field_name": "meta_title",
  "character_limit": 60,
  "required_elements": ["project_name", "location"],
  "model": "claude-sonnet-4-5-20241022",
  "temperature": 0.7,
  "version": 3,
  "description": "Creates SEO-optimized meta titles for OPR project pages",
  "usage_notes": "Always include 'Dubai' or 'Off-Plan Dubai' for SEO",
  "performance": {
    "usage_count": 245,
    "average_qa_score": 0.92,
    "average_rating": 4.5
  }
}
```

---

#### `PUT /api/prompts/{id}`

**Description:** Update prompt (creates new version)

**Request Body:**
```json
{
  "content": "Updated prompt content...",
  "change_reason": "Improved SEO focus",
  "change_notes": "Added emphasis on luxury keywords based on QA feedback"
}
```

**Response:**
```json
{
  "id": "uuid",
  "version": 4,
  "content": "Updated prompt content...",
  "created_version_id": "uuid",
  "updated_at": "2025-01-15T15:00:00Z"
}
```

---

#### `GET /api/prompts/{id}/versions`

**Description:** Get version history

**Response:**
```json
{
  "prompt_id": "uuid",
  "current_version": 4,
  "versions": [
    {
      "version": 4,
      "content": "Updated prompt...",
      "changed_by": "user@your-domain.com",
      "change_reason": "Improved SEO focus",
      "created_at": "2025-01-15T15:00:00Z",
      "avg_qa_score": null,
      "usage_count": 0
    },
    {
      "version": 3,
      "content": "Previous prompt...",
      "changed_by": "user@your-domain.com",
      "change_reason": "Character limit compliance",
      "created_at": "2025-01-10T10:00:00Z",
      "avg_qa_score": 0.92,
      "usage_count": 245
    }
  ]
}
```

---

#### `POST /api/prompts/{id}/revert`

**Description:** Revert to previous version

**Request Body:**
```json
{
  "version": 3,
  "reason": "Version 4 producing lower quality results"
}
```

---

### Template Management

#### `GET /api/prompts/templates/{template_type}`

**Description:** Get complete prompt template for a template type

**Response:**
```json
{
  "template_type": "opr",
  "template_name": "OPR Standard Template",
  "prompts": {
    "meta_title": {
      "prompt_id": "uuid",
      "content": "Generate a compelling meta title...",
      "char_limit": 60
    },
    "meta_description": {
      "prompt_id": "uuid",
      "content": "Create an engaging meta description...",
      "char_limit": 160
    },
    "overview": {
      "prompt_id": "uuid",
      "content": "Write an engaging opening paragraph...",
      "char_limit": 500
    }
  }
}
```

---

#### `POST /api/prompts/customize`

**Description:** Create customized prompt set for project

**Request Body:**
```json
{
  "project_id": "uuid",
  "base_template": "opr",
  "customizations": {
    "meta_title": "Custom prompt for this specific project...",
    "overview": "Tailored overview prompt..."
  }
}
```

---

## UI Components

### PromptsPage.tsx

**Location:** `frontend/src/pages/PromptsPage.tsx`

**Features:**
- Searchable table of all prompts
- Filter by website, category, field
- Sort by usage, QA score, last used
- Quick actions: Edit, View Versions, Clone

---

### PromptEditorPage.tsx

**Location:** `frontend/src/pages/PromptEditorPage.tsx`

**Features:**
- Rich text editor with syntax highlighting
- Live preview with sample data
- Character counter for output limits
- AI model configuration (model, temperature, max tokens)
- Version comparison viewer
- Save with change reason required

---

### PromptCustomizer.tsx

**Location:** `frontend/src/components/PromptCustomizer.tsx`

**Features:**
- Pre-generation prompt editing
- Show all prompts for selected template
- Inline editing for each prompt
- Reset to default option
- Save custom prompt set

---

## Workflow Diagrams

### Prompt Lifecycle

```
┌─────────────────┐
│ Create Prompt   │
│ (Version 1)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Use in Content Gen      │
│ - Track QA scores       │
│ - Gather user feedback  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Analyze Performance     │
│ - QA score: 0.85        │
│ - Feedback: "Too long"  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Edit Prompt             │
│ (Version 2)             │
│ Reason: "Shorten output"│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Use New Version         │
│ - Track performance     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Compare Versions        │
│ - V1: QA 0.85           │
│ - V2: QA 0.93           │
└────────┬────────────────┘
         │
         ▼
   Keep V2 Active
```

---

## Code Examples

### Backend: Prompt Service

```python
# backend/app/services/prompt_service.py
from typing import Dict, List
from uuid import UUID
from app.models.prompt import Prompt
from app.models.prompt_version import PromptVersion

class PromptService:
    def __init__(self, db):
        self.db = db

    async def update_prompt(
        self,
        prompt_id: UUID,
        new_content: str,
        user_id: UUID,
        change_reason: str,
        change_notes: str = None
    ) -> Dict:
        """Update prompt and create new version"""

        # Get current prompt
        prompt = await self._get_prompt(prompt_id)

        # Create version record for current state
        old_version = PromptVersion(
            prompt_id=prompt.id,
            version=prompt.version,
            content=prompt.content,
            character_limit=prompt.character_limit,
            model=prompt.model,
            temperature=prompt.temperature,
            changed_by=user_id,
            change_reason=change_reason,
            change_notes=change_notes,
            change_type='content_updated'
        )
        self.db.add(old_version)

        # Update prompt
        prompt.content = new_content
        prompt.version += 1
        prompt.updated_at = datetime.utcnow()

        await self.db.commit()

        return {
            'prompt_id': prompt.id,
            'new_version': prompt.version,
            'content': new_content
        }

    async def get_template_prompts(
        self,
        template_type: str,
        content_variant: str = None
    ) -> Dict:
        """Get all prompts for a template type"""

        query = select(Prompt).where(
            Prompt.template_type == template_type,
            Prompt.is_active == True
        )

        if content_variant:
            query = query.where(Prompt.content_variant == content_variant)

        result = await self.db.execute(query)
        prompts = result.scalars().all()

        # Organize by field name
        template = {}
        for prompt in prompts:
            template[prompt.field_name] = {
                'prompt_id': prompt.id,
                'content': prompt.content,
                'char_limit': prompt.character_limit,
                'required_elements': prompt.required_elements
            }

        return template
```

---

## Configuration

### Environment Variables

```bash
# Prompt Settings
ENABLE_PROMPT_VERSIONING=true
ENABLE_PROMPT_CUSTOMIZATION=true
MAX_PROMPT_VERSION_HISTORY=50

# Performance Tracking
TRACK_PROMPT_PERFORMANCE=true
MIN_USAGE_FOR_METRICS=10
```

---

## Brand Context Integration

### Overview

The Prompt Library works in conjunction with the **Brand Context Layer** to ensure all generated content adheres to the company brand guidelines. This separation of concerns allows:

- **Field prompts** to focus on structure, format, and character limits
- **Brand context** to handle voice, tone, terminology, and language rules

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION REQUEST                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  BRAND CONTEXT LAYER (Prepended to all prompts)                 │
│  ─────────────────────────────────────────────────────────────  │
│  Source: reference/company/brand-guidelines/                    │
│          brand-context-prompt.md                                │
│                                                                 │
│  Contains:                                                      │
│  • Brand voice directive (advisor vs salesperson)               │
│  • Audience calibration rules                                   │
│  • Terminology standards (property types, amenities)            │
│  • Language prohibitions (banned phrases, vague adjectives)     │
│  • Content structure rules                                      │
│  • Quality checklist                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FIELD-SPECIFIC PROMPT (From Prompt Library)                    │
│  ─────────────────────────────────────────────────────────────  │
│  Source: prompts table / prompt_templates                       │
│                                                                 │
│  Contains:                                                      │
│  • Field-specific instructions                                  │
│  • Character limits                                             │
│  • Output format requirements                                   │
│  • Required elements                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  COMBINED PROMPT → Anthropic API                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Brand Context File Location

```
reference/
└── company/
    └── brand-guidelines/
        ├── Brand-Content-Guidelines.md  # Full guidelines (reference)
        └── brand-context-prompt.md                   # Condensed for AI injection
```

### Key Brand Rules Enforced

| Category | Rule | Enforcement |
|----------|------|-------------|
| **Voice** | Advisor tone, not salesperson | Brand context preamble |
| **Terminology** | "apartment" not "flat" | Terminology standards section |
| **Specificity** | No "world-class amenities" | Language prohibitions |
| **Claims** | Yields must be "projected" | Investment terms section |
| **Structure** | Lead with differentiator | Content hierarchy rules |

### Implementation Example

```python
# backend/app/services/content_generator.py

class ContentGenerator:
    def __init__(self):
        self.brand_context = self._load_brand_context()

    def _load_brand_context(self) -> str:
        """Load brand context from file"""
        context_path = "reference/company/brand-guidelines/brand-context-prompt.md"
        with open(context_path, 'r') as f:
            return f.read()

    async def generate_field(
        self,
        field_name: str,
        field_prompt: str,
        project_data: dict,
        char_limit: int = None
    ) -> str:
        """Generate content with brand context prepended"""

        # Combine brand context + field prompt
        full_prompt = f"""
{self.brand_context}

---
## Field-Specific Instructions

{field_prompt}

---
## Project Data

{json.dumps(project_data, indent=2)}
"""

        response = await self.anthropic_client.messages.create(
            model="claude-sonnet-4-5-20241022",
            max_tokens=char_limit or 500,
            system=full_prompt,
            messages=[
                {"role": "user", "content": f"Generate the {field_name} content."}
            ]
        )

        return response.content[0].text
```

### Updating Brand Guidelines

When brand guidelines change:

1. Update the source document: `Brand-Content-Guidelines.md`
2. Update the condensed version: `brand-context-prompt.md`
3. No changes required to individual field prompts
4. All future generations automatically use updated guidelines

### Rollback Procedure

To revert brand context changes:

1. Restore previous version of `brand-context-prompt.md` from version control
2. No database changes required
3. All prompts continue working with restored guidelines

---

## Related Documentation

### Core Documentation
- [Modules > Content Generation](./CONTENT_GENERATION.md) - Prompt usage and brand context pipeline
- [Modules > QA Module](./QA_MODULE.md) - Performance tracking

### Brand Guidelines
- [Brand Content Guidelines](../../reference/company/brand-guidelines/Brand-Content-Guidelines.md) - Full reference
- [Brand Context Prompt](../../reference/company/brand-guidelines/brand-context-prompt.md) - AI injection version

### Integration Points
- [Integrations > Anthropic](../05-integrations/ANTHROPIC_API_INTEGRATION.md) - Prompt execution with brand context

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
