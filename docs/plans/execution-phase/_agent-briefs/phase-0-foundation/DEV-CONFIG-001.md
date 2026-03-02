# Agent Brief: DEV-CONFIG-001

**Agent ID:** DEV-CONFIG-001
**Agent Name:** Configuration Agent
**Type:** Development
**Phase:** 0 - Foundation
**Context Budget:** 45,000 tokens

---

## Mission

Set up the complete configuration management system for PDP Automation v.3, including environment variables, settings management, database connection, and secret handling for local development and production environments.

---

## Documentation to Read

### Primary (MUST READ)
1. `docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md` - Required environment variables and secrets
2. `docs/06-devops/LOCAL_DEVELOPMENT.md` - Local development setup requirements

### Secondary (SHOULD READ)
3. `docs/01-architecture/INFRASTRUCTURE.md` - Production infrastructure details
4. `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` - GCP configuration requirements

---

## Dependencies

**Upstream (Required Before Start):** None - This is a foundational agent

**Downstream (Waiting on You):**
- DEV-AUTH-001 (needs JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
- DEV-DB-001 (needs DATABASE_URL)
- All integration agents (need API keys and credentials)
- All backend agents (need Settings singleton)

---

## Outputs to Produce

### File 1: `backend/app/config/settings.py`
Pydantic BaseSettings configuration class with:
- All environment variables
- Validation rules
- Secret Manager integration for production
- Environment-specific defaults

### File 2: `backend/app/config/database.py`
Database connection configuration:
- Async SQLAlchemy engine setup
- Connection pooling configuration (use default pool for async, NOT QueuePool)
- Session factory
- Health check utility

### File 3: `backend/app/config/__init__.py`
Package exports for clean imports

### File 4: `backend/.env.example`
Template environment file with:
- All required variables
- Example values (not real secrets)
- Comments explaining each variable
- Grouped by category

### File 5: `frontend/.env.local.example`
Frontend environment template with:
- API base URL
- Google OAuth client ID (public)
- Feature flags

### File 6: `backend/alembic.ini`
Alembic configuration file:
- Script location pointing to alembic/
- Logging configuration
- sqlalchemy.url placeholder (overridden by env.py)

### File 7: `backend/alembic/env.py`
Alembic environment configuration:
- Loads DATABASE_URL from environment
- Imports Base from models for metadata
- Supports both offline and online migrations
- Uses sync engine for migrations (converts asyncpg to psycopg2)

### File 8: `backend/alembic/script.py.mako`
Alembic migration template for generating new migrations

---

## Acceptance Criteria

Your work will be validated against these criteria:

1. **Pydantic BaseSettings** used for all configuration
2. **Secret Manager integration** for production secrets:
   - Loads from GCP Secret Manager when `ENVIRONMENT=production`
   - Falls back to environment variables for development
3. **Environment-specific configurations**:
   - Development: Local defaults, verbose logging
   - Staging: Cloud resources, moderate logging
   - Production: Cloud resources, structured logging
4. **All required variables documented** in .env.example
5. **Validation on critical variables**:
   - DATABASE_URL format validation
   - Required variables raise clear errors
   - Type coercion for booleans, integers
6. **Type-safe configuration access** throughout the application

---

## Technical Specifications

### Settings Class Structure
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 1
    REFRESH_TOKEN_EXPIRY_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:5174/auth/callback"

    # Google Cloud
    GCP_PROJECT_ID: str = "YOUR-GCP-PROJECT-ID"
    GCS_BUCKET_NAME: str = "pdp-automation-assets-dev"
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None

    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"

    # Application
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5174"]
    API_V1_PREFIX: str = "/api/v1"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Database Configuration
```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

def create_database_engine(settings: Settings):
    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG
    )

async def get_db_session() -> AsyncSession:
    # FastAPI dependency for database sessions
    ...
```

### Required Environment Variables

Refer to `docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md` for the complete list including:

**Core:**
- ENVIRONMENT
- DEBUG
- DATABASE_URL

**Authentication:**
- JWT_SECRET
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

**Google Cloud:**
- GCP_PROJECT_ID
- GCS_BUCKET_NAME
- GOOGLE_APPLICATION_CREDENTIALS

**Anthropic:**
- ANTHROPIC_API_KEY

**Google Sheets (6 Templates):**
- TEMPLATE_SHEET_ID_AGGREGATORS
- TEMPLATE_SHEET_ID_OPR
- TEMPLATE_SHEET_ID_MPP
- TEMPLATE_SHEET_ID_ADOP
- TEMPLATE_SHEET_ID_ADRE
- TEMPLATE_SHEET_ID_COMMERCIAL

**Google Drive:**
- GOOGLE_DRIVE_ROOT_FOLDER_ID

---

## Quality Standards

- Never commit real secrets to .env.example
- Use descriptive variable names
- Group related variables with comments
- Provide sensible defaults where possible
- Validate URLs and connection strings
- Log configuration loading (without secrets) at startup

---

## QA Pair

Your outputs will be reviewed by: **QA-CONFIG-001**

The QA agent will verify:
- No secrets in committed files
- All required variables have defaults or validation
- .env.example matches actual requirements
- Secret Manager integration is secure
- Environment isolation working

---

## Output Format

When complete, confirm:
```
AGENT: DEV-CONFIG-001
STATUS: COMPLETE
OUTPUTS:
  - backend/app/config/settings.py (XXX lines)
  - backend/app/config/database.py (XXX lines)
  - backend/.env.example (XXX lines)
  - frontend/.env.local.example (XXX lines)
NOTES: [Any implementation notes or decisions]
```

---

**Begin execution.**
