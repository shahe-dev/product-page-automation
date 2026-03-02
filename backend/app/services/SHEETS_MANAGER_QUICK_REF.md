# SheetsManager Quick Reference

## Import

```python
from app.services.sheets_manager import SheetsManager
from app.models.enums import TemplateType
```

## Initialize

```python
manager = SheetsManager()
```

## Create Sheet

```python
result = await manager.create_project_sheet(
    project_name="Project Name",
    template_type=TemplateType.AGGREGATORS.value
)
# Returns: SheetResult(sheet_id, sheet_url, title, template_type, created_at)
```

## Populate Sheet

```python
content = {
    "meta_title": "Title",
    "meta_description": "Description",
    "project_name": "Name",
    # ... up to 17 fields
}

result = await manager.populate_sheet(
    sheet_id="sheet-id",
    content=content,
    template_type=TemplateType.AGGREGATORS.value
)
# Returns: PopulateResult(sheet_id, total_fields, fields_written, fields_failed, failures)
```

## Validate Content

```python
result = await manager.read_back_validate(
    sheet_id="sheet-id",
    content=content,
    template_type=TemplateType.AGGREGATORS.value
)
# Returns: ValidationResult(sheet_id, total_checked, matches, mismatches, details)
```

## Share Sheet

```python
success = await manager.share_sheet(
    sheet_id="sheet-id",
    email="user@example.com",
    role="writer"  # or "reader", "owner"
)
# Returns: bool
```

## Template Types

```python
TemplateType.AGGREGATORS
TemplateType.OPR
TemplateType.MPP
TemplateType.ADOP
TemplateType.ADRE
TemplateType.COMMERCIAL
```

## Available Fields (17 total)

### SEO
- meta_title, meta_description, h1, url_slug

### Content
- short_description, long_description
- location_description, amenities_description
- payment_plan_description, investment_highlights

### Project Data
- project_name, developer, location
- starting_price, bedrooms, completion_date, property_type

## Exceptions

```python
from app.services.sheets_manager import (
    CredentialsError,        # Credentials missing/invalid
    TemplateNotFoundError,   # Template sheet not found
    SheetOperationError,     # General operation failure
    RateLimitError,          # Rate limit exceeded
)
```

## Error Handling Pattern

```python
from app.services.sheets_manager import SheetsManagerError

try:
    result = await manager.create_project_sheet(...)
except SheetsManagerError as e:
    logger.error(f"Sheets operation failed: {e}")
    # Handle error
```

## Complete Example

```python
from app.services.sheets_manager import SheetsManager, SheetsManagerError
from app.models.enums import TemplateType
import logging

logger = logging.getLogger(__name__)

async def create_project_output(project_data: dict) -> str:
    """Create and populate Google Sheet for project."""
    manager = SheetsManager()

    try:
        # 1. Create sheet
        sheet = await manager.create_project_sheet(
            project_name=project_data["name"],
            template_type=TemplateType.AGGREGATORS.value
        )

        # 2. Prepare content
        content = {
            "meta_title": project_data["meta_title"],
            "project_name": project_data["name"],
            "developer": project_data["developer"],
            # ... more fields
        }

        # 3. Populate
        populate_result = await manager.populate_sheet(
            sheet_id=sheet.sheet_id,
            content=content,
            template_type=TemplateType.AGGREGATORS.value
        )

        logger.info(f"Populated {populate_result.fields_written} fields")

        # 4. Validate
        validation = await manager.read_back_validate(
            sheet_id=sheet.sheet_id,
            content=content,
            template_type=TemplateType.AGGREGATORS.value
        )

        if validation.mismatches > 0:
            logger.warning(f"{validation.mismatches} validation mismatches")

        # 5. Share
        await manager.share_sheet(
            sheet_id=sheet.sheet_id,
            email="content.team@example.com",
            role="writer"
        )

        return sheet.sheet_url

    except SheetsManagerError as e:
        logger.error(f"Failed to create sheet: {e}")
        raise
```

## Configuration Required

In `.env`:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
GOOGLE_DRIVE_ROOT_FOLDER_ID=0AOEEIstP54k2Uk9PVA
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID
```

## Rate Limits

- Max retries: 3
- Initial delay: 1 second
- Max delay: 16 seconds
- Exponential backoff on 429 errors

## Performance

- Batch updates: Single API call for all fields
- Async/await: Non-blocking operations
- Retry logic: Automatic with exponential backoff

## Testing

```bash
# Run tests
pytest tests/test_sheets_manager.py -v

# Run validation
python scripts/validate_sheets_manager.py

# Check types
mypy app/services/sheets_manager.py --ignore-missing-imports
```

## Common Patterns

### Create and populate in one go
```python
async def quick_sheet(name: str, content: dict) -> str:
    manager = SheetsManager()
    sheet = await manager.create_project_sheet(name, "aggregators")
    await manager.populate_sheet(sheet.sheet_id, content, "aggregators")
    return sheet.sheet_url
```

### Batch operations
```python
async def create_multiple_sheets(projects: list[dict]) -> list[str]:
    manager = SheetsManager()
    urls = []

    for project in projects:
        sheet = await manager.create_project_sheet(
            project["name"],
            project["template_type"]
        )
        await manager.populate_sheet(
            sheet.sheet_id,
            project["content"],
            project["template_type"]
        )
        urls.append(sheet.sheet_url)

    return urls
```

### Validation with retry
```python
async def populate_with_validation(
    sheet_id: str,
    content: dict,
    template: str,
    max_attempts: int = 3
) -> bool:
    manager = SheetsManager()

    for attempt in range(max_attempts):
        await manager.populate_sheet(sheet_id, content, template)
        validation = await manager.read_back_validate(sheet_id, content, template)

        if validation.mismatches == 0:
            return True

        logger.warning(f"Validation failed, retry {attempt + 1}/{max_attempts}")

    return False
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| CredentialsError | Set GOOGLE_APPLICATION_CREDENTIALS |
| TemplateNotFoundError | Verify template IDs, check service account access |
| SheetOperationError | Check sheet ID, verify permissions |
| RateLimitError | Reduce operation frequency |

## Documentation

- Full guide: `SHEETS_MANAGER_USAGE.md`
- Summary: `SHEETS_MANAGER_SUMMARY.md`
- Tests: `tests/test_sheets_manager.py`
- Validation: `scripts/validate_sheets_manager.py`
