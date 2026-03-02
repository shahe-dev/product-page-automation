# Google Sheets Manager - Usage Guide

## Overview

The `SheetsManager` service provides Google Sheets integration for PDP Automation v.3. It handles template copying, content population, validation, and permission management with built-in rate limiting and retry logic.

## Features

- Template-based sheet creation on Shared Drive
- Batch content updates (single API call)
- Read-back validation
- Permission management
- Exponential backoff retry logic
- Support for 6 template types
- Comprehensive error handling

## Configuration

Required environment variables in `.env`:

```bash
# Service account credentials path
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# GCP Project
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID

# Shared Drive folder for output
GOOGLE_DRIVE_ROOT_FOLDER_ID=0AOEEIstP54k2Uk9PVA

# Template sheet IDs (6 templates)
TEMPLATE_SHEET_ID_AGGREGATORS=YOUR_AGGREGATORS_SHEET_ID
TEMPLATE_SHEET_ID_OPR=YOUR_OPR_SHEET_ID
TEMPLATE_SHEET_ID_MPP=YOUR_MPP_SHEET_ID
TEMPLATE_SHEET_ID_ADOP=YOUR_ADOP_SHEET_ID
TEMPLATE_SHEET_ID_ADRE=YOUR_ADRE_SHEET_ID
TEMPLATE_SHEET_ID_COMMERCIAL=YOUR_COMMERCIAL_SHEET_ID
```

## Basic Usage

### Initialize Manager

```python
from app.services.sheets_manager import SheetsManager

manager = SheetsManager()
```

### Create Project Sheet

```python
from app.models.enums import TemplateType

# Create new sheet from template
result = await manager.create_project_sheet(
    project_name="Downtown Dubai Luxury Apartments",
    template_type=TemplateType.AGGREGATORS.value
)

print(f"Sheet created: {result.sheet_url}")
print(f"Sheet ID: {result.sheet_id}")
```

### Populate Sheet with Content

```python
# Prepare content dictionary
content = {
    "meta_title": "Downtown Dubai Luxury Apartments - Properties for Sale",
    "meta_description": "Discover exclusive luxury apartments in Downtown Dubai...",
    "h1": "Downtown Dubai Luxury Apartments",
    "url_slug": "downtown-dubai-luxury-apartments",
    "short_description": "Premium residential development...",
    "long_description": "Experience unparalleled luxury...",
    "location_description": "Located in the heart of Downtown Dubai...",
    "amenities_description": "World-class amenities including...",
    "payment_plan_description": "Flexible payment plans available...",
    "investment_highlights": "Prime location, high ROI potential...",
    "project_name": "Downtown Dubai Luxury Apartments",
    "developer": "Emaar Properties",
    "location": "Downtown Dubai",
    "starting_price": "AED 1,200,000",
    "bedrooms": "1-3 BR",
    "completion_date": "Q4 2026",
    "property_type": "Apartment"
}

# Populate sheet
populate_result = await manager.populate_sheet(
    sheet_id=result.sheet_id,
    content=content,
    template_type=TemplateType.AGGREGATORS.value
)

print(f"Fields written: {populate_result.fields_written}")
print(f"Fields failed: {populate_result.fields_failed}")

if populate_result.failures:
    for failure in populate_result.failures:
        print(f"Failed to write {failure['field']}: {failure['error']}")
```

### Validate Content

```python
# Read back and validate
validation_result = await manager.read_back_validate(
    sheet_id=result.sheet_id,
    content=content,
    template_type=TemplateType.AGGREGATORS.value
)

print(f"Matches: {validation_result.matches}")
print(f"Mismatches: {validation_result.mismatches}")

# Check for mismatches
for detail in validation_result.details:
    if not detail['match']:
        print(f"Mismatch in {detail['field']}:")
        print(f"  Expected: {detail['expected']}")
        print(f"  Actual: {detail['actual']}")
```

### Share Sheet

```python
# Share with team member
await manager.share_sheet(
    sheet_id=result.sheet_id,
    email="team.member@example.com",
    role="writer"  # Can be: reader, writer, owner
)
```

## Complete Workflow Example

```python
from app.services.sheets_manager import SheetsManager
from app.models.enums import TemplateType

async def create_and_populate_project_sheet(
    project_name: str,
    template_type: str,
    content: dict[str, str],
    share_with: list[str] | None = None
):
    """Complete workflow for creating and populating a project sheet."""
    manager = SheetsManager()

    try:
        # 1. Create sheet from template
        print(f"Creating sheet: {project_name}")
        sheet_result = await manager.create_project_sheet(
            project_name=project_name,
            template_type=template_type
        )

        # 2. Populate with content
        print("Populating sheet...")
        populate_result = await manager.populate_sheet(
            sheet_id=sheet_result.sheet_id,
            content=content,
            template_type=template_type
        )

        if populate_result.fields_failed > 0:
            print(f"Warning: {populate_result.fields_failed} fields failed to write")

        # 3. Validate content
        print("Validating content...")
        validation_result = await manager.read_back_validate(
            sheet_id=sheet_result.sheet_id,
            content=content,
            template_type=template_type
        )

        if validation_result.mismatches > 0:
            print(f"Warning: {validation_result.mismatches} validation mismatches")

        # 4. Share with team members
        if share_with:
            print("Sharing sheet...")
            for email in share_with:
                await manager.share_sheet(
                    sheet_id=sheet_result.sheet_id,
                    email=email,
                    role="writer"
                )

        print(f"Success! Sheet URL: {sheet_result.sheet_url}")
        return sheet_result

    except Exception as e:
        print(f"Error creating sheet: {e}")
        raise


# Usage
content = {
    "meta_title": "Project Title",
    "project_name": "My Project",
    # ... other fields
}

result = await create_and_populate_project_sheet(
    project_name="My New Project",
    template_type=TemplateType.AGGREGATORS.value,
    content=content,
    share_with=["user1@example.com", "user2@example.com"]
)
```

## Field Mapping

All 6 templates share the same field structure with EN/AR/RU columns:
- EN content: Column B
- AR content: Column C
- RU content: Column D

### Available Fields

| Field Name | Cell | Description |
|------------|------|-------------|
| meta_title | B2 | SEO meta title |
| meta_description | B3 | SEO meta description |
| h1 | B4 | Page heading |
| url_slug | B5 | URL slug |
| short_description | B6 | Brief description |
| long_description | B7 | Detailed description |
| location_description | B8 | Location details |
| amenities_description | B9 | Amenities overview |
| payment_plan_description | B10 | Payment plan details |
| investment_highlights | B11 | Investment highlights |
| project_name | B12 | Project name |
| developer | B13 | Developer name |
| location | B14 | Location |
| starting_price | B15 | Starting price |
| bedrooms | B16 | Bedroom configuration |
| completion_date | B17 | Completion date |
| property_type | B18 | Property type |

## Template Types

Six template types are supported:

```python
from app.models.enums import TemplateType

TemplateType.AGGREGATORS  # "aggregators"
TemplateType.OPR          # "opr"
TemplateType.MPP          # "mpp"
TemplateType.ADOP         # "adop"
TemplateType.ADRE         # "adre"
TemplateType.COMMERCIAL   # "commercial"
```

## Error Handling

The service provides specific exceptions for different error scenarios:

```python
from app.services.sheets_manager import (
    CredentialsError,
    TemplateNotFoundError,
    SheetOperationError,
    RateLimitError
)

try:
    result = await manager.create_project_sheet(
        project_name="Test Project",
        template_type="aggregators"
    )
except CredentialsError as e:
    # Credentials missing or invalid
    print(f"Credentials error: {e}")
except TemplateNotFoundError as e:
    # Template sheet not found
    print(f"Template not found: {e}")
except SheetOperationError as e:
    # General operation failure
    print(f"Operation failed: {e}")
except RateLimitError as e:
    # Rate limit exceeded after retries
    print(f"Rate limit exceeded: {e}")
```

## Rate Limiting

The service implements automatic retry with exponential backoff:
- Maximum 3 retries per operation
- Initial delay: 1 second
- Maximum delay: 16 seconds
- Automatically handles Google Sheets API 429 errors

Google Sheets API Limits:
- 60 requests/minute per user
- 300 requests/minute per project

The service handles these limits transparently.

## Best Practices

### 1. Batch Operations

Use batch_update internally for efficiency:
```python
# Good: Single batch update
populate_result = await manager.populate_sheet(
    sheet_id=sheet_id,
    content=all_content,
    template_type=template_type
)

# Avoid: Multiple individual updates
# Don't update fields one by one
```

### 2. Validate After Population

Always validate critical content:
```python
validation_result = await manager.read_back_validate(
    sheet_id=sheet_id,
    content=content,
    template_type=template_type
)

if validation_result.mismatches > 0:
    # Handle validation failures
    for detail in validation_result.details:
        if not detail['match']:
            # Log or retry
            pass
```

### 3. Handle Errors Gracefully

```python
from app.services.sheets_manager import SheetsManagerError

try:
    result = await manager.create_project_sheet(...)
except SheetsManagerError as e:
    # Log error
    logger.error(f"Sheets operation failed: {e}")
    # Notify user or retry
```

### 4. Use Type Hints

```python
from app.models.enums import TemplateType
from app.services.sheets_manager import SheetResult

async def create_sheet(
    name: str,
    template: TemplateType
) -> SheetResult:
    manager = SheetsManager()
    return await manager.create_project_sheet(
        project_name=name,
        template_type=template.value
    )
```

## Logging

The service logs all operations:

```python
import logging

# Enable debug logging for detailed output
logging.getLogger('app.services.sheets_manager').setLevel(logging.DEBUG)
```

Log messages include:
- Sheet creation events
- Population success/failure
- Validation results
- Sharing operations
- Rate limit retries
- Error details

## Performance Considerations

### Batch Updates
- All field updates use single `batch_update()` call
- Reduces API calls from N to 1 (where N = number of fields)

### Async/Await
- gspread is synchronous but wrapped with `asyncio.to_thread()`
- Doesn't block event loop during API calls
- Allows concurrent operations

### Rate Limiting
- Automatic retry with exponential backoff
- Handles 429 errors transparently
- Maximum 3 retries before failure

## Troubleshooting

### Credentials Error
```
CredentialsError: GOOGLE_APPLICATION_CREDENTIALS not configured
```
**Solution**: Set environment variable to service account key path

### Template Not Found
```
TemplateNotFoundError: Template sheet not found: aggregators
```
**Solution**: Verify template sheet IDs in settings, ensure service account has access

### Sheet Not Found
```
SheetOperationError: Sheet not found: xyz123
```
**Solution**: Verify sheet ID, ensure it's on Shared Drive and accessible

### Rate Limit Exceeded
```
RateLimitError: populate_sheet failed after 3 attempts
```
**Solution**: Reduce operation frequency, implement application-level rate limiting

### Permission Denied
```
APIError: The caller does not have permission
```
**Solution**: Ensure service account has Editor/Owner access to Shared Drive

## Testing

Run tests with pytest:

```bash
# All tests
pytest tests/test_sheets_manager.py -v

# Specific test class
pytest tests/test_sheets_manager.py::TestSheetCreation -v

# With coverage
pytest tests/test_sheets_manager.py --cov=app.services.sheets_manager
```

## References

- [gspread Documentation](https://docs.gspread.org/)
- [Google Sheets API Limits](https://developers.google.com/sheets/api/limits)
- [Google Drive API Reference](https://developers.google.com/drive/api/v3/reference)
