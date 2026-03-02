# Configuration Guide - PDP Automation v.3

Complete guide to configuring and deploying the PDP Automation backend.

## Quick Start (Development)

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your values
nano .env
```

### 3. Configure Required Variables

Minimum required configuration for local development:

```bash
# Database (use PostgreSQL)
DATABASE_URL=postgresql+asyncpg://pdp_user:pdp_password@localhost:5432/pdp_automation

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET=your-generated-secret-key-here-min-32-chars

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Google Sheets Template IDs (from spreadsheet URLs)
TEMPLATE_SHEET_ID_AGGREGATORS=actual-sheet-id
TEMPLATE_SHEET_ID_OPR=actual-sheet-id
TEMPLATE_SHEET_ID_MPP=actual-sheet-id
TEMPLATE_SHEET_ID_ADOP=actual-sheet-id
TEMPLATE_SHEET_ID_ADRE=actual-sheet-id
TEMPLATE_SHEET_ID_COMMERCIAL=actual-sheet-id

# Google Drive
GOOGLE_DRIVE_ROOT_FOLDER_ID=actual-folder-id
```

### 4. Setup Database

```bash
# Create PostgreSQL database
createdb pdp_automation

# Run migrations
alembic upgrade head
```

### 5. Validate Configuration

```bash
# Run validation script
python scripts/validate_config.py
```

### 6. Start Development Server

```bash
# Run with auto-reload
python app/main.py

# Or use uvicorn directly
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for API documentation.

## Production Deployment

### Pre-Deployment Checklist

- [ ] All required environment variables set
- [ ] JWT_SECRET is strong (32+ chars)
- [ ] Database migrations up to date
- [ ] GCP service account configured
- [ ] Secrets stored in GCP Secret Manager
- [ ] CORS origins set to production domains
- [ ] DEBUG=false
- [ ] ENVIRONMENT=production
- [ ] Database connection pool sized appropriately
- [ ] Audit logging enabled
- [ ] Monitoring configured

### Production Environment Variables

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Use Secret Manager for these:
# - JWT_SECRET
# - GOOGLE_CLIENT_SECRET
# - ANTHROPIC_API_KEY
# - DATABASE_URL (with SSL enabled)

# Production database URL with SSL
DATABASE_URL=postgresql+asyncpg://user:pass@cloudsql/dbname?host=/cloudsql/project:region:instance

# Increase pool for production
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Production CORS
ALLOWED_ORIGINS=https://pdp.example.com,https://pdp-staging.example.com

# Enable all security features
ENABLE_AUDIT_LOG=true
ENABLE_METRICS=true
```

### GCP Secret Manager Setup

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
gcloud secrets create JWT_SECRET --data-file=-
# Enter secret value, press Ctrl+D

gcloud secrets create ANTHROPIC_API_KEY --data-file=-
gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding JWT_SECRET \
    --member="serviceAccount:pdp-automation@project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Cloud Run Deployment

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/pdp-automation-api

# Deploy to Cloud Run
gcloud run deploy pdp-automation-api \
    --image gcr.io/PROJECT_ID/pdp-automation-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production \
    --set-env-vars GCP_PROJECT_ID=PROJECT_ID \
    --vpc-connector pdp-connector \
    --cloudsql-instances PROJECT_ID:REGION:INSTANCE
```

## Configuration Reference

### Environment Values

- `development` - Local development, verbose logging, debug mode
- `staging` - Testing environment, similar to production
- `production` - Production environment, Secret Manager, structured logging

### Database Configuration

**Connection String Format:**
```
postgresql+asyncpg://user:password@host:port/database?param=value
```

**SSL Parameters:**
```
?sslmode=require&sslrootcert=/path/to/ca.pem
```

**Cloud SQL Proxy:**
```
?host=/cloudsql/project:region:instance
```

**Pool Sizing:**
- Development: 5 connections, 10 overflow
- Staging: 10 connections, 10 overflow
- Production: 20-50 connections, 10-20 overflow

### JWT Configuration

**Secret Generation:**
```bash
# Strong secret (recommended)
openssl rand -hex 32

# Even stronger
openssl rand -base64 48
```

**Token Lifetimes:**
- Access Token: 1 hour (configurable)
- Refresh Token: 7 days (configurable)

### Google OAuth Setup

1. Go to Google Cloud Console
2. APIs & Services > Credentials
3. Create OAuth 2.0 Client ID
4. Application type: Web application
5. Add authorized redirect URIs:
   - Development: `http://localhost:5174/auth/callback`
   - Production: `https://pdp.example.com/auth/callback`
6. Copy Client ID and Client Secret to environment

### Google Sheets Template IDs

Extract from spreadsheet URLs:
```
https://docs.google.com/spreadsheets/d/[TEMPLATE_ID]/edit
                                         ^^^^^^^^^^^^
```

Each template must be:
- Shared with service account email
- Have proper column structure
- Include all required sheets

### CORS Configuration

**Development:**
```bash
ALLOWED_ORIGINS=http://localhost:5174,http://127.0.0.1:5174
```

**Production:**
```bash
ALLOWED_ORIGINS=https://pdp.example.com,https://pdp-staging.example.com
```

**Important:** Never use `*` in production. List all allowed origins explicitly.

## Security Best Practices

### Secrets Management

1. Never commit `.env` files to git
2. Use GCP Secret Manager in production
3. Rotate secrets regularly (quarterly minimum)
4. Use different secrets per environment
5. Minimum 32-character JWT secrets
6. Use strong database passwords

### Database Security

1. Enable SSL for database connections
2. Use connection pooling to prevent exhaustion
3. Set appropriate timeouts
4. Enable query logging in staging only
5. Use read replicas for heavy queries
6. Regular backups and test restoration

### API Security

1. Enable CORS only for known domains
2. Implement rate limiting per user
3. Enable audit logging
4. Validate all inputs
5. Use HTTPS only in production
6. Implement request size limits

## Troubleshooting

### Configuration Loading Errors

**Error:** `ValidationError: DATABASE_URL is required`
```bash
# Check .env file exists
ls -la .env

# Verify DATABASE_URL is set
grep DATABASE_URL .env
```

**Error:** `JWT_SECRET must be at least 32 characters`
```bash
# Generate new secret
openssl rand -hex 32

# Update .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
```

### Database Connection Issues

**Error:** `Connection refused`
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

**Error:** `SSL connection required`
```bash
# Add SSL parameter
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

### Secret Manager Issues

**Error:** `Permission denied`
```bash
# Grant access to service account
gcloud secrets add-iam-policy-binding SECRET_NAME \
    --member="serviceAccount:EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

**Error:** `Secret not found`
```bash
# List available secrets
gcloud secrets list

# Create missing secret
gcloud secrets create SECRET_NAME --data-file=-
```

## Monitoring and Logging

### Application Logs

**Development:** Colored console output
**Production:** Structured JSON logs

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Database connection status
curl http://localhost:8000/health | jq .database
```

### Metrics

Connection pool metrics:
```python
from app.config import get_connection_pool_status

status = await get_connection_pool_status()
print(f"Active: {status['checked_out']}/{status['size']}")
```

## Support

For issues or questions:
1. Check validation script: `python scripts/validate_config.py`
2. Review logs in structured JSON format
3. Check GCP logs in Cloud Console
4. Verify all secrets are accessible
5. Test database connectivity separately

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
