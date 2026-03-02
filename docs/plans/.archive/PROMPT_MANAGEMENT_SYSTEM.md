# Prompt Management System

**Date:** 2026-01-28
**Status:** Complete and ready for use

## Overview

The system now supports full database-backed prompt management with a UI for creating, editing, and versioning prompts for different template types (OPR, MPP, Aggregators, etc.).

## Architecture

### Three-Tier Prompt System

1. **Database Prompts** (highest priority)
   - User-created/edited prompts stored in PostgreSQL
   - Fully versionable with change tracking
   - Managed via web UI at `/prompts`

2. **File-Based Template Prompts** (fallback)
   - Template-specific prompts in `reference/company/prompts/`
   - Currently: `prompt  opr.md` (8,552 chars)
   - Loaded at runtime by ContentGenerator

3. **Hardcoded Default Prompts** (final fallback)
   - Built into PromptManager
   - Used when no database or file prompt exists

### System Flow

```
User creates content for project
    |
    v
ContentGenerator.generate_field()
    |
    v
PromptManager.get_prompt()
    |
    +-- Check Database (if session provided)
    |       |
    |       +-- Found? Return database prompt
    |       |
    |       +-- Not found? Continue to fallback
    |
    +-- Check Template Files (reference/company/prompts/)
    |       |
    |       +-- Found? Return file prompt
    |       |
    |       +-- Not found? Continue to fallback
    |
    +-- Use Hardcoded Default Prompt
```

## Database Schema

### `prompts` Table
- **id**: UUID primary key
- **name**: Prompt name (e.g., "meta_title", "OPR Template Prompt")
- **template_type**: Template type (opr, mpp, aggregators, etc.)
- **content_variant**: Content variant (standard, luxury)
- **content**: The actual prompt text
- **character_limit**: Optional character limit for output
- **version**: Current version number
- **is_active**: Active status
- **created_by** / **updated_by**: User references
- **created_at** / **updated_at**: Timestamps

### `prompt_versions` Table
- Complete history of all prompt changes
- Stores every version with change reason
- Linked to parent prompt via foreign key

## API Endpoints

All endpoints at `/api/v1/prompts`:

### GET `/api/v1/prompts`
List prompts with optional filtering.

**Query Parameters:**
- `template_type`: Filter by template (opr, mpp, etc.)
- `content_variant`: Filter by variant (standard, luxury)
- `search`: Search prompt names
- `is_active`: Filter by active status

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "meta_title",
      "template_type": "opr",
      "content_variant": "standard",
      "version": 3,
      "is_active": true,
      "character_limit": 60,
      "updated_at": "2026-01-28T10:00:00Z",
      "updated_by": {"name": "Admin User"}
    }
  ]
}
```

### GET `/api/v1/prompts/{id}`
Get detailed prompt information.

**Response:**
```json
{
  "id": "uuid",
  "name": "meta_title",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Generate an SEO meta title...",
  "character_limit": 60,
  "version": 3,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z",
  "updated_by": {
    "id": "user-uuid",
    "name": "Admin User"
  }
}
```

### POST `/api/v1/prompts`
Create a new prompt.

**Request Body:**
```json
{
  "name": "meta_title",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Generate an SEO meta title for...",
  "character_limit": 60
}
```

**Response:** Same as GET single prompt

**Validation:**
- Template type must be one of: `["aggregators", "opr", "mpp", "adop", "adre", "commercial"]`
- Content variant must be one of: `["standard", "luxury"]`

### PUT `/api/v1/prompts/{id}`
Update prompt content (creates new version).

**Request Body:**
```json
{
  "content": "Updated prompt content...",
  "change_reason": "Fixed typo in instructions"
}
```

**Response:** Updated prompt with incremented version

**Versioning:**
- Creates new PromptVersion record
- Increments version number
- Preserves full history

### GET `/api/v1/prompts/{id}/versions`
Get version history for a prompt.

**Response:**
```json
{
  "items": [
    {
      "version": 3,
      "content": "Latest prompt content...",
      "change_reason": "Fixed typo",
      "created_at": "2026-01-28T10:00:00Z",
      "created_by": {"name": "Admin User"}
    },
    {
      "version": 2,
      "content": "Previous prompt content...",
      "change_reason": "Initial version",
      "created_at": "2026-01-20T00:00:00Z",
      "created_by": {"name": "Admin User"}
    }
  ]
}
```

## Frontend UI

### Pages

**`/prompts`** - PromptsPage.tsx
- Lists all prompts
- Filter by template type and variant
- Search by name
- Shows version and last update info
- Click to edit

**`/prompts/{id}`** - PromptEditorPage.tsx
- Edit prompt content
- View current version
- Add change reason
- Save creates new version
- Side panel shows version history

### Components

- **PromptList.tsx** - Displays prompt list with filters
- **PromptEditor.tsx** - Markdown editor for prompt content
- **VersionHistory.tsx** - Shows version timeline

## How to Add Prompts for New Templates

### Method 1: Via UI (Recommended)

1. Navigate to `/prompts` page
2. Click "Create Prompt"
3. Fill in form:
   - **Name**: Descriptive name (e.g., "MPP Template Prompt", "meta_title")
   - **Template Type**: Select from dropdown (or request new type)
   - **Content Variant**: standard or luxury
   - **Content**: Paste your prompt
   - **Character Limit**: Optional (for field-level prompts)
4. Save
5. Prompt is now active and will be used by ContentGenerator

### Method 2: Via File + Seed Script

1. **Create prompt file:**
   ```bash
   # Create new file in reference/company/prompts/
   touch "reference/company/prompts/prompt  mpp.md"
   ```

2. **Write your prompt:**
   ```markdown
   You MUST follow this system exactly.
   [Your detailed prompt instructions...]
   ```

3. **Update seed script:**
   Edit [backend/scripts/seed_prompts.py](backend/scripts/seed_prompts.py#L58-L60):
   ```python
   template_files = {
       "opr": "prompt  opr.md",
       "mpp": "prompt  mpp.md",  # Add this
   }
   ```

4. **Run seed script:**
   ```bash
   cd backend
   python scripts/seed_prompts.py
   ```

5. **Update ContentGenerator:**
   Edit [backend/app/services/content_generator.py](backend/app/services/content_generator.py#L358-L363):
   ```python
   prompt_files = {
       "opr": "prompt  opr.md",
       "mpp": "prompt  mpp.md",  # Add this
   }
   ```

### Method 3: Direct Database Insert

Use the API to create prompts programmatically:

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/prompts",
    json={
        "name": "MPP Template Prompt",
        "template_type": "mpp",
        "content_variant": "standard",
        "content": "Your prompt content here...",
        "character_limit": None
    },
    headers={"Authorization": f"Bearer {token}"}
)
```

## Adding New Template Types

To add a completely new template type (beyond the current 6):

### 1. Add to Valid Templates List

Edit [backend/app/api/routes/prompts.py](backend/app/api/routes/prompts.py#L255):
```python
valid_templates = [
    "aggregators", "opr", "mpp", "adop", "adre", "commercial",
    "your_new_template"  # Add here
]
```

### 2. Add to TemplateType Enum

Edit [backend/app/models/enums.py](backend/app/models/enums.py) (if exists):
```python
class TemplateType(str, Enum):
    AGGREGATORS = "aggregators"
    OPR = "opr"
    MPP = "mpp"
    YOUR_NEW = "your_new_template"  # Add here
```

### 3. Create Prompts for Template

Use any of the three methods above to create prompts:
- Template-level prompt: "YOUR_NEW Template Prompt"
- Field-level prompts: "meta_title", "meta_description", etc.

### 4. Update Google Sheets Integration

If this template needs a Google Sheet, ensure sheets_manager.py creates the sheet with the appropriate template name.

## Integration with Google Drive

When a user creates a new Google Sheet template:

1. **Sheet created via API** (`POST /api/v1/projects`)
   - Project record created with `template_type`
   - Sheet created in Google Drive
   - Placeholder content inserted

2. **User creates matching prompt**
   - Go to `/prompts` → Create Prompt
   - Set `template_type` to match sheet template
   - ContentGenerator will use this prompt automatically

3. **Content generation**
   - System calls `ContentGenerator.generate_all()`
   - Prompts loaded from database (if exist) or files (fallback)
   - Brand context + template prompt combined
   - Content generated and populated in sheet

## Current Prompt Inventory

### Template-Level Prompts
- **OPR Template Prompt** (file: `prompt  opr.md`)
  - 8,552 characters
  - Detailed instructions for OPR website content
  - Includes: payment plan rules, healthcare lookup, investment sections

### Field-Level Prompts
- **meta_title** - SEO title generation (60 chars)
- **meta_description** - SEO description (160 chars)
- **h1** - Page heading (60 chars)
- **url_slug** - URL-friendly slug
- **short_description** - Brief summary (500 chars)
- **long_description** - Comprehensive description (2000 chars)
- **location_description** - Area/neighborhood description (1000 chars)
- **amenities_description** - Facilities description (1000 chars)
- **payment_plan_description** - Payment structure (500 chars)
- **investment_highlights** - Investment bullet points (800 chars)

All field-level prompts currently use hardcoded defaults. Can be overridden by creating database records with matching names and template types.

## Testing the System

### 1. API Testing

```bash
# List prompts
curl http://localhost:8000/api/v1/prompts

# Get specific prompt
curl http://localhost:8000/api/v1/prompts/{prompt-id}

# Create prompt
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_prompt",
    "template_type": "opr",
    "content_variant": "standard",
    "content": "Test prompt content",
    "character_limit": 100
  }'

# Update prompt
curl -X PUT http://localhost:8000/api/v1/prompts/{prompt-id} \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content",
    "change_reason": "Testing update"
  }'

# Get versions
curl http://localhost:8000/api/v1/prompts/{prompt-id}/versions
```

### 2. Integration Testing

```python
# Test prompt loading in ContentGenerator
from app.services.content_generator import ContentGenerator

generator = ContentGenerator()

# Check template prompts loaded from files
print(generator.template_prompts.keys())  # Should show ['opr']

# Test system message building
opr_msg = generator._build_system_message("opr")
print(len(opr_msg))  # Should be ~13,960 chars
print("STEP 1" in opr_msg)  # Should be True
```

### 3. UI Testing

1. Navigate to http://localhost:3000/prompts
2. Verify prompt list displays
3. Click "Create Prompt"
4. Fill form and save
5. Edit prompt
6. View version history

## Troubleshooting

### Issue: Prompts not loading from database

**Symptom:** ContentGenerator still using file-based prompts

**Solution:**
- Ensure database has prompt records (run seed script)
- Check that prompt names match field names exactly
- Verify `template_type` and `content_variant` match

### Issue: API returns 500 error

**Symptom:** CRUD operations fail

**Solution:**
- Check database connection
- Verify migrations are up to date: `alembic upgrade head`
- Check user exists (prompts require `created_by` user)

### Issue: Frontend can't load prompts

**Symptom:** Empty list or 404 errors

**Solution:**
- Verify API is running: `curl http://localhost:8000/api/v1/prompts`
- Check authentication (user must be logged in)
- Check CORS settings if making cross-origin requests

## Future Enhancements

### Short Term
- [ ] Add admin role check for prompt creation/updates
- [ ] Add prompt preview with sample data
- [ ] Implement prompt duplication (copy to new template)
- [ ] Add bulk import/export for prompts

### Medium Term
- [ ] A/B testing for prompts (run multiple versions, track performance)
- [ ] Prompt templates (reusable prompt structures)
- [ ] Prompt validation (syntax checking, variable detection)
- [ ] Usage analytics (which prompts generate best content)

### Long Term
- [ ] AI-assisted prompt optimization
- [ ] Multi-language support for prompts
- [ ] Prompt marketplace (share/discover prompts)

## Related Files

### Backend
- [backend/app/api/routes/prompts.py](backend/app/api/routes/prompts.py) - API endpoints
- [backend/app/services/prompt_manager.py](backend/app/services/prompt_manager.py) - Prompt loading logic
- [backend/app/services/content_generator.py](backend/app/services/content_generator.py) - Content generation
- [backend/app/models/database.py](backend/app/models/database.py#L734) - Prompt & PromptVersion models
- [backend/scripts/seed_prompts.py](backend/scripts/seed_prompts.py) - Database seeding

### Frontend
- [frontend/src/pages/PromptsPage.tsx](frontend/src/pages/PromptsPage.tsx) - Prompt list page
- [frontend/src/pages/PromptEditorPage.tsx](frontend/src/pages/PromptEditorPage.tsx) - Edit page
- [frontend/src/components/prompts/PromptList.tsx](frontend/src/components/prompts/PromptList.tsx)
- [frontend/src/components/prompts/PromptEditor.tsx](frontend/src/components/prompts/PromptEditor.tsx)
- [frontend/src/components/prompts/VersionHistory.tsx](frontend/src/components/prompts/VersionHistory.tsx)

### Reference
- [reference/company/prompts/](reference/company/prompts/) - Template prompt files
- [reference/company/brand-guidelines/brand-context-prompt.md](reference/company/brand-guidelines/brand-context-prompt.md) - Brand context

## Documentation
- [PROMPT_INTEGRATION_FIX.md](PROMPT_INTEGRATION_FIX.md) - Initial OPR template fix
- [PROMPT_MANAGEMENT_SYSTEM.md](PROMPT_MANAGEMENT_SYSTEM.md) - This document
