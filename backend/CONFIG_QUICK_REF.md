# Configuration Quick Reference

## Essential Commands

```bash
# Setup
cp .env.example .env          # Create environment file
python scripts/validate_config.py  # Validate configuration

# Development
docker-compose up             # Start full stack
python app/main.py            # Run API only
uvicorn app.main:app --reload # Run with auto-reload

# Testing
pytest tests/test_config.py   # Test configuration
pytest --cov=app.config       # Test with coverage

# Production
gcloud builds submit          # Build container
gcloud run deploy             # Deploy to Cloud Run
```

## Required Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
JWT_SECRET=your-secret-min-32-chars
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
ANTHROPIC_API_KEY=sk-ant-api03-your-key
TEMPLATE_SHEET_ID_AGGREGATORS=sheet-id
TEMPLATE_SHEET_ID_OPR=sheet-id
TEMPLATE_SHEET_ID_MPP=sheet-id
TEMPLATE_SHEET_ID_ADOP=sheet-id
TEMPLATE_SHEET_ID_ADRE=sheet-id
TEMPLATE_SHEET_ID_COMMERCIAL=sheet-id
GOOGLE_DRIVE_ROOT_FOLDER_ID=folder-id
```

## Common Imports

```python
# Settings
from app.config import get_settings
settings = get_settings()

# Database
from app.config import get_db_session, Base
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@app.get("/endpoint")
async def handler(db: AsyncSession = Depends(get_db_session)):
    pass

# Logging
from app.config import setup_logging, get_logger
setup_logging(level="INFO", environment="development")
logger = get_logger(__name__)

# Secrets (Production)
from app.config.secrets import get_secret_manager
sm = get_secret_manager()
secret = sm.get_secret("SECRET_NAME")
```

## Key Endpoints

```
GET  /              - API info
GET  /health        - Health check (200=healthy, 503=unhealthy)
GET  /config/info   - Config info (debug mode only)
GET  /docs          - API documentation (debug mode only)
```

## Configuration Properties

```python
settings = get_settings()

# Environment checks
settings.is_production   # True if ENVIRONMENT=production
settings.is_development  # True if ENVIRONMENT=development
settings.is_staging      # True if ENVIRONMENT=staging

# Database
settings.DATABASE_URL           # Async URL
settings.database_url_sync      # Sync URL (for Alembic)

# Templates
settings.get_template_sheet_id("aggregators")  # Get sheet ID by name
```

## Validation Rules

- DATABASE_URL must start with `postgresql://` or `postgresql+asyncpg://`
- JWT_SECRET minimum 32 characters
- ENVIRONMENT must be: development, staging, or production
- ANTHROPIC_TEMPERATURE must be 0.0-1.0
- Template IDs cannot contain "your-"

## Database Connection Strings

```bash
# Local PostgreSQL
postgresql+asyncpg://user:pass@localhost:5432/dbname

# PostgreSQL with SSL
postgresql+asyncpg://user:pass@host/db?sslmode=require

# Cloud SQL Proxy
postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance

# Docker Compose
postgresql+asyncpg://pdp_user:pdp_password@postgres:5432/pdp_automation
```

## Generate Secrets

```bash
# JWT Secret (32 chars hex)
openssl rand -hex 32

# JWT Secret (48 chars base64)
openssl rand -base64 48

# Strong password
openssl rand -base64 24
```

## GCP Secret Manager

```bash
# Create secret
echo -n "secret-value" | gcloud secrets create SECRET_NAME --data-file=-

# Update secret
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# List secrets
gcloud secrets list
```

## Docker Commands

```bash
# Build image
docker build -t pdp-api .

# Run container
docker run -p 8000:8000 --env-file .env pdp-api

# Full stack
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop stack
docker-compose down
```

## Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Check database status
curl http://localhost:8000/health | jq .database

# Check in production
curl https://pdp-api.run.app/health
```

## Troubleshooting

```bash
# Validate configuration
python scripts/validate_config.py

# Check .env exists
ls -la .env

# Test database connection
psql $DATABASE_URL

# Check logs
tail -f /var/log/pdp-automation.log

# Docker logs
docker-compose logs -f api
```

## Environment-Specific Settings

### Development
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
DATABASE_ECHO=true
```

### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
RELOAD=false
DATABASE_ECHO=false
```

### Production
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
RELOAD=false
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
```

## File Locations

```
backend/
├── .env                     # Your configuration (DO NOT COMMIT)
├── .env.example             # Template
├── app/
│   ├── main.py             # Application entry point
│   └── config/
│       ├── __init__.py     # Package exports
│       ├── settings.py     # Settings class
│       ├── database.py     # Database setup
│       ├── secrets.py      # Secret Manager
│       └── logging.py      # Logging config
├── scripts/
│   └── validate_config.py  # Validation script
├── tests/
│   └── test_config.py      # Configuration tests
├── Dockerfile              # Container build
├── docker-compose.yml      # Local stack
└── requirements.txt        # Dependencies
```

## Template Names

Valid template names for `get_template_sheet_id()`:
- aggregators
- opr
- mpp
- adop
- adre
- commercial

Case insensitive: `"AGGREGATORS"`, `"Aggregators"`, `"aggregators"` all work.

## Log Levels

- DEBUG - Detailed diagnostic information
- INFO - General informational messages
- WARNING - Warning messages
- ERROR - Error messages
- CRITICAL - Critical errors

## Feature Flags

```bash
ENABLE_REGISTRATION=false   # Allow new user registration
ENABLE_METRICS=true         # Collect metrics
ENABLE_AUDIT_LOG=true       # Log all actions
```

## CORS Configuration

```bash
# Development (comma-separated)
ALLOWED_ORIGINS=http://localhost:5174,http://127.0.0.1:5174

# Production
ALLOWED_ORIGINS=https://pdp.example.com,https://pdp-staging.example.com
```

## Connection Pool Monitoring

```python
from app.config import get_connection_pool_status

status = await get_connection_pool_status()
print(f"Pool: {status['size']}")
print(f"Active: {status['checked_out']}")
print(f"Overflow: {status['overflow']}")
```

## Test Fixtures

```python
@pytest.fixture
def test_settings():
    return Settings(
        ENVIRONMENT="development",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
        JWT_SECRET="a" * 32,
        # ... other required fields
    )

def test_example(test_settings):
    assert test_settings.is_development
```

## Error Messages

| Error | Fix |
|-------|-----|
| `ValidationError: DATABASE_URL is required` | Add DATABASE_URL to .env |
| `JWT_SECRET must be at least 32 characters` | Generate longer secret |
| `Connection refused` | Start PostgreSQL |
| `Permission denied` | Grant Secret Manager access |
| `Secret not found` | Create secret in Secret Manager |

## Performance Tuning

```bash
# Increase pool for high traffic
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20

# Adjust timeouts
DATABASE_POOL_TIMEOUT=60
DATABASE_POOL_RECYCLE=1800

# Rate limiting
RATE_LIMIT_PER_MINUTE=120
```

## Security Checklist

- [ ] JWT_SECRET is 32+ characters
- [ ] DATABASE_URL uses SSL in production
- [ ] Secrets in Secret Manager, not .env (production)
- [ ] ALLOWED_ORIGINS restricted to known domains
- [ ] DEBUG=false in production
- [ ] ALLOWED_EMAIL_DOMAIN set to organization domain
- [ ] ENABLE_AUDIT_LOG=true in production

## Quick Test

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
createdb pdp_automation

# Create .env
cp .env.example .env
# Edit .env with values

# Validate
python scripts/validate_config.py

# Run tests
pytest tests/test_config.py -v

# Start server
python app/main.py

# Check health
curl http://localhost:8000/health
```
