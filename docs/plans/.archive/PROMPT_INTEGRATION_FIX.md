# Prompt Integration Fix - OPR Template

**Date:** 2026-01-28
**Status:** Complete
**Issue:** content_generator.py was using generic one-liner prompts instead of template-specific detailed prompts from reference/company/prompts/

## Problem Description

The content generation system had two sources of prompt information:
1. Detailed template-specific prompts in `reference/company/prompts/prompt  opr.md` (8,552 chars)
2. Generic one-liner instructions hardcoded in `content_generator.py`

The system was only using the generic instructions, ignoring the detailed OPR prompt that contains:
- STEP-by-step instructions for content extraction
- Payment plan formatting rules
- Healthcare and education lookup requirements
- Investment section guidelines
- FAQ structure requirements

## Solution Implemented

### Changes to content_generator.py

1. **Added template prompt loading** ([content_generator.py:93](backend/app/services/content_generator.py#L93))
   - New method `_load_template_prompts()` loads template-specific prompts from files
   - Reads from `reference/company/prompts/` directory
   - Maps filenames to template types (currently only "opr")

2. **Updated system message building** ([content_generator.py:395-425](backend/app/services/content_generator.py#L395-L425))
   - `_build_system_message()` now checks for template-specific prompts first
   - Falls back to generic one-liner if template-specific prompt not found
   - Template-specific prompts are appended after brand context

3. **Fixed path resolution** ([content_generator.py:296-297](backend/app/services/content_generator.py#L296-L297), [content_generator.py:348-349](backend/app/services/content_generator.py#L348-L349))
   - Paths now resolve relative to project root (not backend directory)
   - Uses `Path(__file__).parent.parent.parent.parent` to reach project root

### How It Works

For OPR template:
```
Brand Context (5,408 chars)
+
TEMPLATE TYPE: OPR
+
Detailed OPR Prompt (8,552 chars)
=
Complete System Message (13,960 chars)
```

For other templates (MPP, aggregators, etc.):
```
Brand Context (5,408 chars)
+
TEMPLATE TYPE: MPP
+
Generic one-liner instruction
=
Complete System Message (5,483 chars)
```

## Files Modified

- `backend/app/services/content_generator.py`
  - Added `_load_template_prompts()` method
  - Modified `__init__()` to call template loading
  - Modified `_build_system_message()` to use template-specific prompts
  - Fixed path resolution for brand context and template prompts

## Testing

Created and ran integration test verifying:
- OPR prompt file loads successfully (8,552 chars)
- Brand context combines with OPR prompt (13,960 chars total)
- OPR-specific instructions present (STEP 1, PAYMENT PLAN, etc.)
- MPP template uses generic fallback correctly
- Path resolution works from backend directory

## Current Template Mapping

```python
prompt_files = {
    "opr": "prompt  opr.md",
    # Future templates to be added here
}
```

Only OPR is mapped currently. The files in `reference/company/prompts/`:
- `prompt  opr.md` - Template-specific (now being used)
- `prompt  MJL.md` - Project-specific example (not a template)
- `prompt GRAND POLO.md` - Project-specific example (not a template)
- `prompt Palm Jebel.md` - Project-specific example (not a template)

## Next Steps

### Phase 1: Add More Template Prompts (Future)
When creating prompts for other templates (mpp, aggregators, etc.):
1. Create markdown files in `reference/company/prompts/`
2. Add mapping to `prompt_files` dict in `_load_template_prompts()`
3. Test with integration test

### Phase 2: Database Integration (TODO)
The system has infrastructure for database-backed prompt management:
- Database table: `prompts` ([database.py:734](backend/app/models/database.py#L734))
- API endpoints: `/api/v1/prompts` ([prompts.py](backend/app/api/routes/prompts.py))
- Frontend UI: PromptsPage.tsx, PromptEditorPage.tsx

To fully implement:

1. **PromptManager Updates**
   - Query database for active prompts by (field_name, template_type, variant)
   - Fall back to file-based prompts if database is empty
   - Cache database prompts for performance

2. **API Implementation**
   - Complete TODOs in `prompts.py`
   - Implement CRUD operations with database
   - Add version control and audit logging

3. **Frontend Integration**
   - Connect PromptList to API endpoints
   - Enable prompt editing with version history
   - Show current prompts being used in content_generator.py

4. **Migration Path**
   - Seed database with current file-based prompts
   - Allow users to edit via UI
   - Database becomes source of truth
   - Keep files as backup/defaults

## Architecture Notes

### Prompt Hierarchy
1. Database prompts (when implemented) - highest priority
2. File-based template prompts (current implementation)
3. Hardcoded generic prompts (fallback)

### System Message Structure
```
[Brand Context from brand-context-prompt.md]

TEMPLATE TYPE: {TEMPLATE_TYPE}
[Template-specific prompt OR generic instruction]

Generate content that follows these brand guidelines strictly.
Return ONLY the requested content, no additional commentary or formatting.
```

### Field-Level vs Template-Level Prompts
Current design uses:
- **Template-level prompts**: Single comprehensive prompt for entire template (OPR, MPP, etc.)
- **Field-level prompts**: Managed by PromptManager (meta_title, meta_description, etc.)

The template-level prompt provides context for ALL fields in that template, while field-level prompts specify individual field requirements.

## Verification

To verify the fix is working:

```python
from app.services.content_generator import ContentGenerator

generator = ContentGenerator()

# Check OPR prompt is loaded
assert "opr" in generator.template_prompts
assert len(generator.template_prompts["opr"]) > 8000

# Check system message uses OPR prompt
opr_msg = generator._build_system_message("opr")
assert "STEP 1 — USE DEVELOPER" in opr_msg
assert "PAYMENT PLAN" in opr_msg
assert len(opr_msg) > 13000

# Check fallback for MPP
mpp_msg = generator._build_system_message("mpp")
assert "My Property Portal" in mpp_msg
assert "STEP 1" not in mpp_msg
assert len(mpp_msg) < 6000
```

## Impact

- OPR content generation now uses the detailed 8,552-char prompt with specific rules
- Payment plan formatting will follow the CRITICAL RULE specifications
- Healthcare/education sections will follow lookup requirements
- Investment sections will use proper formatting
- All other templates continue to work with generic instructions until their prompts are added
