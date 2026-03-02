# Configuration Module

Centralized configuration management for PDP Automation v.3 backend.

## Files

- `settings.py` - Main configuration settings using Pydantic
- `database.py` - Database connection and session management
- `secrets.py` - GCP Secret Manager integration for production
- `logging.py` - Structured logging configuration
- `__init__.py` - Package exports

## Quick Start

### 1. Environment Setup

```bash
# Copy example file
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Import Settings

```python
from app.config import get_settings

settings = get_settings()
print(settings.DATABASE_URL)
print(settings.ANTHROPIC_API_KEY)
```

### 3. Use Database Session

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_db_session

@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

## Configuration Categories

### Environment
- `ENVIRONMENT` - development, staging, or production
- `DEBUG` - Enable debug mode
- `LOG_LEVEL` - Logging verbosity

### Database
- `DATABASE_URL` - PostgreSQL connection string (required)
- `DATABASE_POOL_SIZE` - Connection pool size (default: 5)
- `DATABASE_MAX_OVERFLOW` - Max overflow connections (default: 10)

### Authentication
- `JWT_SECRET` - JWT signing key (min 32 chars, required)
- `JWT_EXPIRY_HOURS` - Access token lifetime (default: 1)
- `REFRESH_TOKEN_EXPIRY_DAYS` - Refresh token lifetime (default: 7)

### Google OAuth
- `GOOGLE_CLIENT_ID` - OAuth client ID (required)
- `GOOGLE_CLIENT_SECRET` - OAuth client secret (required)
- `GOOGLE_REDIRECT_URI` - OAuth callback URL

### Google Cloud
- `GCP_PROJECT_ID` - GCP project identifier
- `GCS_BUCKET_NAME` - Cloud Storage bucket for assets
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account key path

### Anthropic
- `ANTHROPIC_API_KEY` - API key (required)
- `ANTHROPIC_MODEL` - Model identifier (default: claude-sonnet-4-5-20250514)
- `ANTHROPIC_TEMPERATURE` - Model temperature (0.0-1.0)

### Google Sheets Templates
- `TEMPLATE_SHEET_ID_AGGREGATORS` - Aggregators template
- `TEMPLATE_SHEET_ID_OPR` - OPR template
- `TEMPLATE_SHEET_ID_MPP` - MPP template
- `TEMPLATE_SHEET_ID_ADOP` - Ad Operations template
- `TEMPLATE_SHEET_ID_ADRE` - Ad Revenue template
- `TEMPLATE_SHEET_ID_COMMERCIAL` - Commercial template

### Application
- `ALLOWED_ORIGINS` - CORS allowed origins (comma-separated)
- `ALLOWED_EMAIL_DOMAIN` - Restrict login to email domain
- `API_V1_PREFIX` - API version prefix (default: /api/v1)

## Validation

Settings are validated on load using Pydantic:

```python
from app.config import get_settings

try:
    settings = get_settings()
except Exception as e:
    print(f"Configuration error: {e}")
```

Common validation errors:
- Missing required variables
- Invalid DATABASE_URL format
- JWT_SECRET too short
- Invalid ENVIRONMENT value
- Temperature out of range

## Production Secrets

In production, secrets can be loaded from GCP Secret Manager:

```python
from app.config.secrets import get_secret_manager

secret_manager = get_secret_manager()
api_key = secret_manager.get_secret("ANTHROPIC_API_KEY")
```

Secrets are automatically loaded from environment variables first, then Secret Manager.

## Logging

Setup logging at application startup:

```python
from app.config.logging import setup_logging

setup_logging(
    level="INFO",
    environment="development",
    log_file="/var/log/pdp-automation.log"  # optional
)
```

Production uses JSON structured logging, development uses colored console output.

## Database

### Health Check

```python
from app.config import check_database_connection

if await check_database_connection():
    print("Database OK")
```

### Initialize Schema

```python
from app.config import initialize_database

await initialize_database()  # Creates all tables
```

### Pool Status

```python
from app.config import get_connection_pool_status

status = await get_connection_pool_status()
print(f"Active connections: {status['checked_out']}/{status['size']}")
```

### Shutdown

```python
from app.config import close_database

await close_database()  # Close all connections
```

## Template Helpers

Get template sheet ID by name:

```python
settings = get_settings()
sheet_id = settings.get_template_sheet_id("aggregators")
```

Supported template names:
- aggregators
- opr
- mpp
- adop
- adre
- commercial

## Properties

Settings object provides convenience properties:

```python
settings = get_settings()

if settings.is_production:
    print("Running in production")

if settings.is_development:
    print("Development mode")

# Get sync database URL for Alembic
alembic_url = settings.database_url_sync
```

## Security Best Practices

1. Never commit `.env` files to version control
2. Use minimum 32-character JWT_SECRET
3. Rotate secrets regularly in production
4. Use GCP Secret Manager for production secrets
5. Enable audit logging in production
6. Restrict ALLOWED_EMAIL_DOMAIN to your organization

## Testing

Override settings for tests:

```python
from app.config import Settings

def get_test_settings():
    return Settings(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test_db",
        JWT_SECRET="test-secret-at-least-32-characters-long",
        ANTHROPIC_API_KEY="test-key",
        # ... other required fields
    )
```

## Troubleshooting

### Import Error
```
ImportError: cannot import name 'get_settings'
```
Ensure you're importing from `app.config`, not `app.config.settings`.

### Validation Error
```
ValidationError: DATABASE_URL must start with 'postgresql://'
```
Check your DATABASE_URL format in `.env`.

### Secret Not Found
```
ValueError: Required secret 'JWT_SECRET' not found
```
Add missing variable to `.env` file.

### Connection Pool Exhausted
```
TimeoutError: QueuePool limit of size 5 overflow 10 reached
```
Increase `DATABASE_POOL_SIZE` or `DATABASE_MAX_OVERFLOW` in settings.
