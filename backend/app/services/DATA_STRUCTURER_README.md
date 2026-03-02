# Data Structurer Service (DEV-STRUCT-001)

## Overview

The Data Structurer service converts raw markdown text from property brochures into structured JSON with per-field confidence scoring and validation. It uses Claude Sonnet 4.5 to intelligently extract and structure project information.

## Features

- **Intelligent Extraction**: Uses Claude Sonnet 4.5 for context-aware field extraction
- **Confidence Scoring**: Per-field confidence scores (0.0-1.0) to flag uncertain data
- **Validation**: Comprehensive validation of data types, ranges, and formats
- **Cost Tracking**: Token usage and cost tracking per API call
- **Retry Logic**: Exponential backoff retry on rate limits and timeouts
- **Error Handling**: Graceful degradation on parse errors

## Usage

### Basic Usage

```python
from app.services.data_structurer import DataStructurer

# Initialize the service
structurer = DataStructurer()

# Structure markdown text
result = await structurer.structure(
    markdown_text=extracted_markdown,
    template_type="aggregators"
)

# Access structured data
print(f"Project: {result.project_name}")
print(f"Developer: {result.developer}")
print(f"Price Range: {result.currency} {result.price_min:,} - {result.price_max:,}")
print(f"Overall Confidence: {result.overall_confidence:.2%}")
```

### With Custom API Key

```python
structurer = DataStructurer(
    api_key="your-anthropic-api-key",
    model="claude-sonnet-4-5-20250514"
)
```

## Data Structure

### Input

Raw markdown text from PDF extraction:

```markdown
# Project Name by Developer

## Location
Emirate: Dubai
Community: Dubai Marina

## Pricing
- Price Range: AED 1,200,000 - 4,500,000
- Bedrooms: Studio, 1BR, 2BR, 3BR

## Timeline
- Handover: Q4 2026
```

### Output

`StructuredProject` with:

```python
{
    "project_name": "Project Name",
    "developer": "Developer",
    "emirate": "Dubai",
    "community": "Dubai Marina",
    "price_min": 1200000,
    "price_max": 4500000,
    "bedrooms": ["Studio", "1BR", "2BR", "3BR"],
    "handover_date": "Q4 2026",

    # Quality metrics
    "confidence_scores": {
        "project_name": FieldConfidence(field_name="project_name", confidence=1.0, ...)
    },
    "overall_confidence": 0.92,
    "missing_fields": ["community", "total_units"],
    "needs_review_fields": ["emirate"],

    # Cost tracking
    "token_usage": {"input": 1500, "output": 800},
    "structuring_cost": 0.0165
}
```

## Extractable Fields

### Core Information
- `project_name`: Official project name
- `developer`: Developer/builder company
- `emirate`: Dubai, Abu Dhabi, etc.
- `community`: Major area (Dubai Marina, Downtown Dubai)
- `sub_community`: Specific district or sub-area
- `property_type`: Residential, Commercial, or Mixed-use

### Pricing
- `price_min/max`: Price range in base currency units
- `currency`: AED (default), USD, or EUR
- `price_per_sqft`: Price per square foot

### Specifications
- `bedrooms`: List of configurations (["Studio", "1BR", "2BR"])
- `total_units`: Total number of units
- `floors`: Number of floors/stories

### Timeline
- `handover_date`: Expected completion (e.g., "Q4 2026", "2027")
- `launch_date`: Project launch date

### Features
- `amenities`: List of amenities (pool, gym, parking)
- `key_features`: Notable features (beachfront, smart home)
- `payment_plan`: Payment structure with percentages

### Metadata
- `description`: Brief 1-2 sentence project description

## Confidence Scoring

Confidence scores indicate data quality:

- **1.0**: Explicitly stated in document
- **0.8-0.9**: Strongly implied or derived from clear context
- **0.6-0.7**: Inferred from partial information (flagged for review)
- **0.4-0.5**: Educated guess based on limited data
- **0.0-0.3**: No relevant information found

Fields with confidence < 0.7 are flagged in `needs_review_fields`.

## Validation

The service validates:

### Critical Issues (prevent save)
- Negative prices
- `price_min` > `price_max`
- Invalid data types

### Warnings (log but allow)
- Non-standard bedroom formats
- Out-of-range numeric values (units, floors)
- Non-standard property types
- Invalid date formats
- Missing critical fields (project_name, developer, emirate)

## Cost Tracking

Token usage and cost are tracked per call:

```python
result.token_usage  # {"input": 1500, "output": 800}
result.structuring_cost  # 0.0165 (USD)
```

**Pricing (as of Jan 2025)**:
- Input: $3 per million tokens
- Output: $15 per million tokens

Typical cost per brochure: $0.01 - $0.05

## Error Handling

### Retry Logic

Automatic retry with exponential backoff for:
- Rate limit errors (429): 3 retries, up to 10s delay
- Timeout errors: 3 retries
- API errors: 3 retries

### Graceful Degradation

On unrecoverable errors:
- Returns `StructuredProject` with empty fields
- Sets `overall_confidence = 0.0`
- Logs error details
- Includes error in `description` field

## Testing

Run tests with:

```bash
cd backend
pytest tests/services/test_data_structurer.py -v
```

**Test Coverage**: 86% (17 tests, all passing)

Tests cover:
- Successful structuring
- Confidence score parsing
- Validation logic
- Error handling
- Retry logic
- Cost calculation
- Type conversion

## Integration

### With Data Extractor

```python
from app.services.data_extractor import DataExtractor
from app.services.data_structurer import DataStructurer

# Extract markdown from PDF
extractor = DataExtractor()
extraction_result = await extractor.extract(pdf_bytes)

# Structure the extracted markdown
structurer = DataStructurer()
structured = await structurer.structure(extraction_result.markdown_text)
```

### With Job Manager

The service is typically called from the job manager as part of the content generation pipeline.

## Configuration

Settings from `app.config.settings`:

```python
ANTHROPIC_API_KEY: str          # Required
ANTHROPIC_MODEL: str            # Default: "claude-sonnet-4-5-20250514"
ANTHROPIC_MAX_TOKENS: int       # Default: 4096
ANTHROPIC_TEMPERATURE: float    # Default: 0.0 (deterministic)
ANTHROPIC_TIMEOUT: int          # Default: 300 seconds
```

## Performance

- **Average processing time**: 3-8 seconds per brochure
- **Token usage**: 1000-3000 input tokens, 500-1500 output tokens
- **Cost per brochure**: $0.01 - $0.05
- **Confidence threshold**: 0.7 (below this = needs review)

## Logging

The service logs:
- Structuring start/completion
- Token usage and cost
- Validation issues and warnings
- API errors and retries
- Parse failures

Log level: INFO (errors at ERROR level)

## Files

- **Service**: `backend/app/services/data_structurer.py`
- **Tests**: `backend/tests/services/test_data_structurer.py`
- **Example**: `backend/examples/data_structurer_example.py`
- **Documentation**: `backend/app/services/DATA_STRUCTURER_README.md`

## Dependencies

- `anthropic`: Claude API client
- `app.config.settings`: Configuration management
- Python 3.11+ (uses modern type hints)

## Phase

Phase 3 (Content Generation) - DEV-STRUCT-001
