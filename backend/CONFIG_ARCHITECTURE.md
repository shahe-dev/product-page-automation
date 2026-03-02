# Configuration System Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                         │
│                        (app/main.py)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ imports
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Configuration Package                         │
│                      (app/config/)                              │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Settings    │  │  Database    │  │   Logging    │         │
│  │  (settings.py│  │ (database.py)│  │ (logging.py) │         │
│  │              │  │              │  │              │         │
│  │ • Pydantic   │  │ • SQLAlchemy │  │ • JSON fmt   │         │
│  │ • Validation │  │ • Async pool │  │ • Color fmt  │         │
│  │ • .env load  │  │ • Sessions   │  │ • Levels     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐                                              │
│  │   Secrets    │                                              │
│  │  (secrets.py)│                                              │
│  │              │                                              │
│  │ • GCP SM     │                                              │
│  │ • Env vars   │                                              │
│  │ • Rotation   │                                              │
│  └──────────────┘                                              │
└───────┬────────────────────────────────────────────────────────┘
        │
        │ reads from
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Configuration Sources                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  .env file   │  │  Environment │  │  GCP Secret  │         │
│  │              │  │  Variables   │  │   Manager    │         │
│  │ Development  │  │  System env  │  │  Production  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Development Environment

```
.env file
    │
    ▼
Environment Variables
    │
    ▼
Pydantic Settings
    │
    ├─▶ Validation
    ├─▶ Type Coercion
    └─▶ Default Values
        │
        ▼
    Settings Object (cached)
        │
        ├─▶ FastAPI Routes
        ├─▶ Database Engine
        ├─▶ Logging Config
        └─▶ Application Logic
```

### Production Environment

```
GCP Secret Manager
    │
    ▼
Secret Manager Client
    │
    ├─▶ Load to env vars (startup)
    └─▶ Direct access (runtime)
        │
        ▼
Environment Variables
    │
    ▼
Pydantic Settings
    │
    ├─▶ Validation
    ├─▶ Type Coercion
    └─▶ Default Values
        │
        ▼
    Settings Object (cached)
        │
        ├─▶ FastAPI Routes
        ├─▶ Database Engine
        ├─▶ Logging Config
        └─▶ Application Logic
```

## Settings Loading Sequence

```
1. Application Start
   └─▶ Import app.config

2. Settings Module Init
   └─▶ Define Settings class (Pydantic)

3. get_settings() called
   ├─▶ Check @lru_cache
   │   └─▶ Return cached if exists
   │
   └─▶ Create new Settings instance
       ├─▶ Load .env file (if exists)
       ├─▶ Read environment variables
       ├─▶ Apply defaults
       ├─▶ Validate all fields
       │   ├─▶ Type checking
       │   ├─▶ Custom validators
       │   └─▶ Raise errors if invalid
       ├─▶ Log configuration (safe values)
       └─▶ Cache and return

4. Settings Available
   └─▶ Used throughout application
```

## Database Connection Flow

```
Application Startup
    │
    ▼
create_database_engine()
    │
    ├─▶ Read settings.DATABASE_URL
    ├─▶ Configure pool size
    ├─▶ Set timeouts
    └─▶ Create AsyncEngine
        │
        ▼
Global engine instance
    │
    ├─▶ async_session_factory
    │   └─▶ get_db_session() dependency
    │       └─▶ FastAPI route handlers
    │
    └─▶ get_db_context()
        └─▶ Background tasks, scripts
```

## Request Lifecycle

```
HTTP Request
    │
    ▼
FastAPI Router
    │
    ├─▶ CORS Middleware
    ├─▶ GZip Middleware
    └─▶ Route Handler
        │
        ▼
    Depends(get_db_session)
        │
        ├─▶ Create session from pool
        ├─▶ Execute handler logic
        ├─▶ Commit or rollback
        └─▶ Return session to pool
            │
            ▼
        Response
```

## Validation Pipeline

```
Environment Variable
    │
    ▼
Pydantic Field
    │
    ├─▶ Type coercion
    │   └─▶ str → int, bool, list, etc.
    │
    ├─▶ Field validators
    │   ├─▶ @field_validator
    │   ├─▶ Custom logic
    │   └─▶ Raise ValueError if invalid
    │
    ├─▶ Pydantic validation
    │   ├─▶ Required fields
    │   ├─▶ Type constraints
    │   └─▶ Format validation
    │
    └─▶ Valid value
        └─▶ Settings object
```

## Logging Architecture

```
Application Code
    │
    ├─▶ logger.info()
    ├─▶ logger.error()
    └─▶ logger.debug()
        │
        ▼
    Logger Handler
        │
        ├─▶ Development
        │   └─▶ ColoredFormatter
        │       └─▶ Console (colored)
        │
        └─▶ Production
            └─▶ JsonFormatter
                └─▶ stdout (JSON)
                    └─▶ Cloud Logging
```

## Secret Management Flow

### Development
```
Application → os.getenv() → .env file → Value
```

### Production
```
Application
    │
    ▼
SecretManager.get_secret()
    │
    ├─▶ Check os.getenv() first
    │   └─▶ Return if found
    │
    └─▶ GCP Secret Manager
        ├─▶ Authenticate
        ├─▶ Fetch secret
        └─▶ Return value
```

## Configuration Categories

```
Settings
    ├── Environment (3)
    │   ├── ENVIRONMENT
    │   ├── DEBUG
    │   └── LOG_LEVEL
    │
    ├── Database (7)
    │   ├── DATABASE_URL
    │   ├── DATABASE_POOL_SIZE
    │   ├── DATABASE_MAX_OVERFLOW
    │   ├── DATABASE_POOL_TIMEOUT
    │   ├── DATABASE_POOL_RECYCLE
    │   └── DATABASE_ECHO
    │
    ├── Authentication (5)
    │   ├── JWT_SECRET
    │   ├── JWT_ALGORITHM
    │   ├── JWT_EXPIRY_HOURS
    │   ├── REFRESH_TOKEN_EXPIRY_DAYS
    │   └── PASSWORD_MIN_LENGTH
    │
    ├── Google OAuth (5)
    │   ├── GOOGLE_CLIENT_ID
    │   ├── GOOGLE_CLIENT_SECRET
    │   ├── GOOGLE_REDIRECT_URI
    │   ├── GOOGLE_TOKEN_URI
    │   └── GOOGLE_AUTH_URI
    │
    ├── Google Cloud (3)
    │   ├── GCP_PROJECT_ID
    │   ├── GCS_BUCKET_NAME
    │   └── GOOGLE_APPLICATION_CREDENTIALS
    │
    ├── Anthropic (5)
    │   ├── ANTHROPIC_API_KEY
    │   ├── ANTHROPIC_MODEL
    │   ├── ANTHROPIC_MAX_TOKENS
    │   ├── ANTHROPIC_TEMPERATURE
    │   └── ANTHROPIC_TIMEOUT
    │
    ├── Templates (6)
    │   ├── TEMPLATE_SHEET_ID_AGGREGATORS
    │   ├── TEMPLATE_SHEET_ID_OPR
    │   ├── TEMPLATE_SHEET_ID_MPP
    │   ├── TEMPLATE_SHEET_ID_ADOP
    │   ├── TEMPLATE_SHEET_ID_ADRE
    │   └── TEMPLATE_SHEET_ID_COMMERCIAL
    │
    ├── Google Drive (2)
    │   ├── GOOGLE_DRIVE_ROOT_FOLDER_ID
    │   └── GOOGLE_DRIVE_API_VERSION
    │
    ├── Application (5)
    │   ├── API_V1_PREFIX
    │   ├── ALLOWED_ORIGINS
    │   ├── ALLOWED_EMAIL_DOMAIN
    │   ├── MAX_UPLOAD_SIZE_MB
    │   └── RATE_LIMIT_PER_MINUTE
    │
    ├── Server (4)
    │   ├── HOST
    │   ├── PORT
    │   ├── WORKERS
    │   └── RELOAD
    │
    └── Features (3)
        ├── ENABLE_REGISTRATION
        ├── ENABLE_METRICS
        └── ENABLE_AUDIT_LOG
```

## File Organization

```
backend/
├── app/
│   ├── config/
│   │   ├── __init__.py         # Package exports
│   │   ├── settings.py         # Pydantic settings (330 lines)
│   │   ├── database.py         # Database config (200 lines)
│   │   ├── secrets.py          # Secret Manager (190 lines)
│   │   ├── logging.py          # Logging setup (140 lines)
│   │   └── README.md           # Module documentation
│   │
│   └── main.py                 # FastAPI app (140 lines)
│
├── scripts/
│   └── validate_config.py      # Validation tool (300 lines)
│
├── tests/
│   └── test_config.py          # Config tests (250 lines)
│
├── .env.example                # Template (120 lines)
├── requirements.txt            # Dependencies (40 lines)
├── Dockerfile                  # Container build (40 lines)
├── docker-compose.yml          # Local stack (60 lines)
├── pytest.ini                  # Test config (15 lines)
├── CONFIG_SUMMARY.md           # Implementation summary
├── CONFIGURATION_GUIDE.md      # Deployment guide
└── CONFIG_QUICK_REF.md         # Quick reference
```

## Dependency Graph

```
FastAPI Application
    │
    ├─▶ app.config.Settings
    │   └─▶ Pydantic BaseSettings
    │       └─▶ Environment variables
    │
    ├─▶ app.config.Database
    │   ├─▶ SQLAlchemy AsyncEngine
    │   ├─▶ Settings.DATABASE_URL
    │   └─▶ Connection pooling
    │
    ├─▶ app.config.Logging
    │   ├─▶ Settings.LOG_LEVEL
    │   └─▶ Settings.ENVIRONMENT
    │
    └─▶ app.config.Secrets (prod only)
        ├─▶ GCP Secret Manager
        └─▶ Settings.GCP_PROJECT_ID
```

## Error Handling

```
Configuration Loading
    │
    ├─▶ Missing required variable
    │   └─▶ ValidationError with field name
    │
    ├─▶ Invalid format
    │   └─▶ ValidationError with constraint
    │
    ├─▶ Value out of range
    │   └─▶ ValidationError with limits
    │
    └─▶ Type mismatch
        └─▶ ValidationError with expected type
            │
            ▼
        Application fails to start
            │
            └─▶ Clear error message in logs
```

## Scaling Considerations

### Connection Pool Sizing

```
Traffic Level    Pool Size    Max Overflow    Total Connections
─────────────────────────────────────────────────────────────────
Low (dev)             5             10                15
Medium (staging)     10             10                20
High (production)    20             20                40
Very High            50             20                70
```

### Environment-Based Behavior

```
Development:
    ├─▶ Verbose logging (DEBUG)
    ├─▶ Small connection pool
    ├─▶ Auto-reload enabled
    ├─▶ /docs endpoint enabled
    └─▶ Colored console logs

Production:
    ├─▶ Minimal logging (WARNING)
    ├─▶ Large connection pool
    ├─▶ No auto-reload
    ├─▶ /docs endpoint disabled
    └─▶ Structured JSON logs
```

## Security Layers

```
1. Environment Isolation
   └─▶ Separate configs per environment

2. Secret Management
   ├─▶ GCP Secret Manager (prod)
   └─▶ Environment variables (dev)

3. Validation
   ├─▶ Type checking
   ├─▶ Format validation
   └─▶ Constraint checking

4. Access Control
   ├─▶ Email domain restriction
   ├─▶ CORS origin whitelisting
   └─▶ Rate limiting

5. Audit Logging
   └─▶ All configuration changes logged
```

## Monitoring Points

```
Application Health
    │
    ├─▶ /health endpoint
    │   ├─▶ Database connection
    │   └─▶ Overall status
    │
    ├─▶ Connection pool metrics
    │   ├─▶ Active connections
    │   ├─▶ Pool size
    │   └─▶ Overflow usage
    │
    ├─▶ Configuration status
    │   ├─▶ Environment
    │   ├─▶ Feature flags
    │   └─▶ Non-secret values
    │
    └─▶ Error logs
        ├─▶ Validation failures
        ├─▶ Connection errors
        └─▶ Secret access errors
```

## Deployment Pipeline

```
1. Development
   ├─▶ .env file created
   ├─▶ Validation script passes
   └─▶ Local testing

2. Build
   ├─▶ Docker image created
   ├─▶ Dependencies installed
   └─▶ Health check configured

3. Deploy
   ├─▶ Secrets in Secret Manager
   ├─▶ Environment variables set
   └─▶ Database migrations applied

4. Verify
   ├─▶ Health check passes
   ├─▶ Logs show no errors
   └─▶ Database connected
```
