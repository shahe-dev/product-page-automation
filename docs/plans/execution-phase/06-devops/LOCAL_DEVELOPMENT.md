# Local Development Setup Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Database Setup](#database-setup)
7. [Docker Development](#docker-development)
8. [Environment Configuration](#environment-configuration)
9. [IDE Configuration](#ide-configuration)
10. [Development Workflow](#development-workflow)
11. [Testing Locally](#testing-locally)
12. [Debugging](#debugging)
13. [Troubleshooting](#troubleshooting)
14. [Security Considerations](#security-considerations)

---

## Overview

This guide provides comprehensive instructions for setting up a complete local development environment for the PDP Automation system. The development environment mirrors the production infrastructure using local services and Docker containers.

**Local Development Stack:**
- Backend: Python 3.10 + FastAPI (http://localhost:8000)
- Frontend: React 19 + Vite (http://localhost:5174)
- Database: PostgreSQL 16 (localhost:5432)
- Cache: Redis 7 (localhost:6379)
- AI: Anthropic API (development key)

**Development Philosophy:**
- Environment parity with production
- Hot-reloading for rapid iteration
- Comprehensive test coverage
- Pre-commit hooks for code quality
- Docker for consistent environments

---

## Prerequisites

### Required Software

**1. Python 3.10+**
```bash
# Verify installation
python3 --version  # Should show 3.10 or higher

# Windows
# Download from python.org and install

# macOS
brew install python@3.10

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

**2. Node.js 18+**
```bash
# Verify installation
node --version  # Should show v18 or higher
npm --version

# Windows
# Download from nodejs.org and install

# macOS
brew install node@18

# Linux
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**3. PostgreSQL 15+**
```bash
# Verify installation
psql --version

# Windows
# Download installer from postgresql.org

# macOS
brew install postgresql@15
brew services start postgresql@15

# Linux (Ubuntu/Debian)
sudo apt install postgresql-15 postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**4. Docker & Docker Compose**
```bash
# Verify installation
docker --version
docker-compose --version

# Install Docker Desktop (Windows/macOS)
# https://docs.docker.com/desktop/

# Linux
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

**5. Git**
```bash
# Verify installation
git --version

# Windows
# Download from git-scm.com

# macOS
brew install git

# Linux
sudo apt install git
```

### Optional Tools

- **VS Code**: Recommended IDE with Python and ESLint extensions
- **Postman/Insomnia**: API testing
- **pgAdmin**: PostgreSQL GUI client
- **Redis Insight**: Redis GUI client

---

## Quick Start

**For experienced developers who want to get started immediately:**

```bash
# 1. Clone repository
git clone https://github.com/your-org/pdp-automation.git
cd pdp-automation

# 2. Start all services with Docker Compose
docker-compose up -d

# 3. Access the application
# - Frontend: http://localhost:5174
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs

# 4. Stop services
docker-compose down
```

For detailed setup instructions, continue reading the following sections.

---

## Backend Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/pdp-automation.git
cd pdp-automation

# Verify repository structure
ls -la
# Should see: backend/, frontend/, docker-compose.yml, README.md
```

### 2. Create Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Verify activation (should show venv path)
which python
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (testing, linting, formatting)
pip install -r requirements-dev.txt

# Verify installation
pip list
```

**Key Dependencies:**
- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **sqlalchemy**: ORM
- **alembic**: Database migrations
- **asyncpg**: Async PostgreSQL driver
- **pydantic**: Data validation
- **python-jose**: JWT handling
- **anthropic**: Anthropic API client
- **PyMuPDF** (>=1.26.6): PDF image extraction and page rendering
- **pymupdf4llm** (>=0.2.9): PDF text extraction as markdown
- **Pillow** (11.1.0): Image manipulation and optimization
- **opencv-python-headless** (4.10.0.84): Watermark removal via inpainting
- **imagehash** (4.3.1): Perceptual hash deduplication
- **pytest**: Testing framework
- **black**: Code formatter
- **flake8**: Linter

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
nano .env  # or use your preferred editor
```

**Backend .env Configuration:**
```bash
# Application Settings
DEBUG=true
ENVIRONMENT=development
PORT=8000
LOG_LEVEL=DEBUG

# Database (Local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://dev:dev123@localhost:5432/pdp_automation

# Redis (Local Redis)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=dev-secret-key-change-in-production-NEVER-commit-this
JWT_SECRET_KEY=jwt-dev-secret-DO-NOT-use-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Cloud Platform
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
GCS_BUCKET_NAME=pdp-automation-dev-assets
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-dev.json

# Google OAuth (Phase 0)
GOOGLE_OAUTH_CLIENT_ID=your-dev-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-dev-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5174/auth/callback
ALLOWED_DOMAIN=your-domain.com

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022

# CORS
CORS_ORIGINS=http://localhost:5174,http://127.0.0.1:5174

# Upload Settings
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,xlsx,csv,txt

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Email (Optional for development)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@your-domain.com
SMTP_PASSWORD=your-app-specific-password
```

### 5. Set Up Database

```bash
# Create database
createdb pdp_automation

# Or using psql
psql -U postgres
CREATE DATABASE pdp_automation;
CREATE USER dev WITH PASSWORD 'dev123';
GRANT ALL PRIVILEGES ON DATABASE pdp_automation TO dev;
\q

# Run database migrations
alembic upgrade head

# Verify migrations
alembic current
# Should show: (head)
```

### 6. Create Service Account (GCP)

```bash
# Create credentials directory
mkdir -p credentials

# Download service account key from GCP Console
# 1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
# 2. Select project: YOUR-GCP-PROJECT-ID
# 3. Create service account: "pdp-dev"
# 4. Grant roles: Storage Admin, Vertex AI User
# 5. Create and download JSON key
# 6. Save as: backend/credentials/service-account-dev.json

# IMPORTANT: Add to .gitignore
echo "credentials/" >> .gitignore
```

### 7. Start Development Server

```bash
# Start FastAPI with hot-reloading
uvicorn app.main:app --reload --port 8000

# Or use the development script
python run_dev.py

# Server should start on http://localhost:8000
# API documentation available at http://localhost:8000/docs
```

**Verify Backend:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","database":"connected"}

# Open interactive API docs
# Navigate to: http://localhost:8000/docs
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
# From repository root
cd frontend
```

### 2. Install Dependencies

```bash
# Install Node.js packages
npm install

# This installs:
# - React 19
# - Vite (build tool)
# - React Router DOM
# - Axios (HTTP client)
# - TanStack Query (data fetching)
# - Tailwind CSS (styling)
# - ESLint + Prettier (code quality)
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env.local

# Edit .env.local
nano .env.local
```

**Frontend .env.local Configuration:**
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Google OAuth (Phase 0 - IMPORTANT!)
VITE_GOOGLE_OAUTH_CLIENT_ID=your-dev-client-id.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=http://localhost:5174/auth/callback

# Feature Flags
VITE_ENABLE_DEBUG=true
VITE_ENABLE_MOCK_DATA=false

# Environment
VITE_ENV=development
```

### 4. Start Development Server

```bash
# Start Vite dev server with hot module replacement (HMR)
npm run dev

# Server starts on http://localhost:5174
# Hot reloading enabled - changes reflect immediately
```

**Verify Frontend:**
```bash
# Application should open in browser automatically
# If not, navigate to: http://localhost:5174

# Check console for errors
# Test API connectivity (should see login screen)
```

### 5. Build for Production (Local Test)

```bash
# Build optimized production bundle
npm run build

# Preview production build locally
npm run preview

# Build output in: dist/
# Preview runs on: http://localhost:4173
```

---

## Database Setup

### Local PostgreSQL Configuration

**1. Create Development Database:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE pdp_automation;
CREATE USER dev WITH PASSWORD 'dev123';
GRANT ALL PRIVILEGES ON DATABASE pdp_automation TO dev;

# Enable required extensions
\c pdp_automation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\q
```

**2. Initialize Schema:**
```bash
cd backend

# Run all migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history --verbose
```

**3. Seed Development Data:**
```bash
# Create seed data script
python scripts/seed_dev_data.py

# This creates:
# - Test user accounts (admin@your-domain.com, user@your-domain.com)
# - Sample projects
# - Example tasks
# - Test PDPs
```

**4. Database Management Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Upgrade to specific version
alembic upgrade <revision_id>

# Downgrade one version
alembic downgrade -1

# Reset database (CAUTION: Deletes all data)
alembic downgrade base
alembic upgrade head

# Backup database
pg_dump -U dev pdp_automation > backup_$(date +%Y%m%d).sql

# Restore database
psql -U dev pdp_automation < backup_20260115.sql
```

### Using Neon PostgreSQL (Staging/Production)

**IMPORTANT: Development Strategy**

This project uses a two-phase database approach:

1. **Development Phase:** Local PostgreSQL via Docker (docker-compose.yml)
   - Fast iteration with zero network latency
   - No risk of hitting Neon free tier limits (100 hours/month)
   - Isolated development environment

2. **Staging/Production Phase:** Neon PostgreSQL (cloud)
   - Serverless, auto-scales to zero
   - Production-ready with automatic backups
   - Point-in-time recovery

**Neon is already configured:**
- Project: `pdp-automation-dev`
- Host: `your-db-host.neon.tech`
- Connection string saved in `neondb/neon-connection-details.txt`

### Migration from Docker to Neon

When development is complete and ready for staging/production:

```bash
# 1. Stop local containers
docker-compose down

# 2. Update DATABASE_URL in .env
# FROM (local Docker):
DATABASE_URL=postgresql+asyncpg://pdpuser:localdevpassword@localhost:5432/pdp_automation

# TO (Neon production):
DATABASE_URL=postgresql+asyncpg://your-db-user:PASSWORD@your-db-host.neon.tech/neondb?sslmode=require

# 3. Run migrations against Neon
alembic upgrade head

# 4. Verify connectivity
python -c "from app.core.database import engine; print('Connected to Neon!')"
```

**Why migration is seamless:**
- Same PostgreSQL version (16) in both environments
- Same extensions (uuid-ossp, pg_trgm)
- Same encoding (UTF-8) and collation (C.UTF-8)
- Only the connection string changes - no code modifications required

---

## Docker Development

### Full Stack with Docker Compose

**docker-compose.yml** (Project root):
```yaml
version: '3.8'

services:
  # PostgreSQL Database (matches Neon PostgreSQL 16 for migration compatibility)
  postgres:
    image: postgres:16-alpine
    container_name: pdp-postgres
    environment:
      POSTGRES_DB: pdp_automation
      POSTGRES_USER: pdpuser
      POSTGRES_PASSWORD: localdevpassword
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C.UTF-8 --lc-ctype=C.UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pdpuser -d pdp_automation"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: pdp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: pdp-backend
    ports:
      - "8000:8000"
    environment:
      DEBUG: "true"
      DATABASE_URL: postgresql+asyncpg://dev:dev123@postgres:5432/pdp_automation
      REDIS_URL: redis://redis:6379/0
      CORS_ORIGINS: http://localhost:5174
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
      - /app/venv  # Prevent overwriting venv
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: pdp-frontend
    ports:
      - "5174:5174"
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    env_file:
      - ./frontend/.env.local
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Prevent overwriting node_modules
    depends_on:
      - backend
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: pdp-network
```

**Backend Dockerfile.dev:**
```dockerfile
# backend/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Development command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Frontend Dockerfile.dev:**
```dockerfile
# frontend/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 5174

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Stop and remove volumes (resets database)
docker-compose down -v

# Rebuild services
docker-compose build

# Rebuild and start
docker-compose up -d --build

# Execute commands in container
docker-compose exec backend bash
docker-compose exec postgres psql -U dev pdp_automation

# Run migrations in container
docker-compose exec backend alembic upgrade head

# Run tests in container
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

---

## Environment Configuration

### Backend Environment Variables Reference

```bash
# ===============================================
# APPLICATION SETTINGS
# ===============================================
DEBUG=true                          # Enable debug mode
ENVIRONMENT=development             # Environment name
PORT=8000                          # Server port
LOG_LEVEL=DEBUG                    # Logging level (DEBUG, INFO, WARNING, ERROR)
WORKERS=1                          # Uvicorn workers (1 for dev)

# ===============================================
# DATABASE
# ===============================================
DATABASE_URL=postgresql+asyncpg://dev:dev123@localhost:5432/pdp_automation
DB_POOL_SIZE=5                     # Connection pool size
DB_MAX_OVERFLOW=10                 # Max overflow connections
DB_POOL_TIMEOUT=30                 # Connection timeout (seconds)
DB_ECHO=false                      # Log SQL queries

# ===============================================
# REDIS CACHE
# ===============================================
REDIS_URL=redis://localhost:6379/0
REDIS_TTL=3600                     # Cache TTL (seconds)
REDIS_MAX_CONNECTIONS=10           # Connection pool size

# ===============================================
# SECURITY
# ===============================================
SECRET_KEY=dev-secret-key-CHANGE-IN-PRODUCTION
JWT_SECRET_KEY=jwt-dev-secret-CHANGE-IN-PRODUCTION
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===============================================
# GOOGLE CLOUD PLATFORM
# ===============================================
GCP_PROJECT_ID=YOUR-GCP-PROJECT-ID
GCS_BUCKET_NAME=pdp-automation-dev-assets
VERTEX_AI_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/service-account-dev.json

# ===============================================
# GOOGLE OAUTH (PHASE 0 - CRITICAL!)
# ===============================================
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5174/auth/callback
ALLOWED_DOMAIN=your-domain.com               # Only @your-domain.com emails allowed

# ===============================================
# ANTHROPIC API
# ===============================================
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_TIMEOUT=60                  # Request timeout (seconds)

# ===============================================
# CORS
# ===============================================
CORS_ORIGINS=http://localhost:5174,http://127.0.0.1:5174
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=*

# ===============================================
# FILE UPLOADS
# ===============================================
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,xlsx,csv,txt,png,jpg,jpeg
UPLOAD_TEMP_DIR=/tmp/uploads

# ===============================================
# RATE LIMITING
# ===============================================
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# ===============================================
# EMAIL (OPTIONAL)
# ===============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@your-domain.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@pdp-automation.com
```

### Frontend Environment Variables Reference

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Google OAuth (Phase 0)
VITE_GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
VITE_OAUTH_REDIRECT_URI=http://localhost:5174/auth/callback

# Feature Flags
VITE_ENABLE_DEBUG=true
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_ANALYTICS=false

# Environment
VITE_ENV=development
VITE_APP_VERSION=1.0.0
```

---

## IDE Configuration

### VS Code Configuration

**.vscode/settings.json:**
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=100",
    "--ignore=E203,W503"
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--line-length=100"
  ],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.pytest_cache": true,
    "**/.coverage": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/venv": true,
    "**/.venv": true,
    "**/dist": true,
    "**/.next": true
  }
}
```

**.vscode/launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "DEBUG": "true"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "--cov=app"
      ],
      "cwd": "${workspaceFolder}/backend",
      "console": "integratedTerminal"
    }
  ]
}
```

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.vscode-pylance",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens",
    "rangav.vscode-thunder-client"
  ]
}
```

---

## Development Workflow

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Make changes and commit regularly
git add .
git commit -m "feat: add new feature"

# 3. Keep branch up to date
git fetch origin
git rebase origin/main

# 4. Push to remote
git push origin feature/your-feature-name

# 5. Create Pull Request on GitHub
```

### Commit Message Convention

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat:     New feature
fix:      Bug fix
docs:     Documentation changes
style:    Code style changes (formatting)
refactor: Code refactoring
test:     Adding tests
chore:    Maintenance tasks

# Examples:
git commit -m "feat(auth): add Google OAuth login"
git commit -m "fix(pdp): resolve duplicate task issue"
git commit -m "docs(api): update endpoint documentation"
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        files: \.(js|jsx|ts|tsx|css|json|md)$
```

---

## Testing Locally

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_pdp_generation.py

# Run specific test
pytest tests/test_pdp_generation.py::test_create_pdp

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v

# View coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- TaskList.test.tsx

# Run E2E tests
npm run test:e2e
```

### API Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Get API version
curl http://localhost:8000/version

# Login (Phase 0 - OAuth callback simulation)
curl -X POST http://localhost:8000/api/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code":"test-code","state":"test-state"}'

# Create PDP (requires auth token)
curl -X POST http://localhost:8000/api/pdps \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test PDP","description":"Test description"}'
```

---

## Debugging

### Backend Debugging

**Using VS Code Debugger:**
1. Set breakpoints in Python code
2. Press F5 or select "FastAPI Backend" configuration
3. Debug through code execution

**Using Python Debugger (pdb):**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Commands:
# n - next line
# s - step into function
# c - continue execution
# p variable_name - print variable
# q - quit debugger
```

### Frontend Debugging

**Browser DevTools:**
1. Open Chrome DevTools (F12)
2. Use "Sources" tab to set breakpoints
3. Use "Console" for logging
4. Use "Network" tab for API requests

**React DevTools:**
```bash
# Install React DevTools extension for Chrome/Firefox
# Inspect component state and props
# Track component re-renders
```

---

## Troubleshooting

### Backend Issues

**Issue: "ModuleNotFoundError"**
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: "Database connection failed"**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Verify credentials in .env
psql -U dev pdp_automation

# Reset database
dropdb pdp_automation
createdb pdp_automation
alembic upgrade head
```

**Issue: "Port 8000 already in use"**
```bash
# Find process using port 8000
lsof -i :8000          # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>          # macOS/Linux
taskkill /PID <PID> /F # Windows
```

### Frontend Issues

**Issue: "npm install fails"**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: "API requests fail (CORS error)"**
```bash
# Verify backend CORS_ORIGINS includes frontend URL
# backend/.env:
CORS_ORIGINS=http://localhost:5174

# Restart backend server
```

**Issue: "Vite port 5174 already in use"**
```bash
# Change port in vite.config.ts
export default defineConfig({
  server: {
    port: 5175
  }
})

# Or kill process on port 5174
lsof -ti :5174 | xargs kill
```

### Docker Issues

**Issue: "Container fails to start"**
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Issue: "Database volume permissions"**
```bash
# Remove and recreate volume
docker-compose down -v
docker volume rm pdp_postgres_data
docker-compose up -d
```

---

## Security Considerations

### Development Environment Security

**1. Secrets Management**
- Never commit `.env` files to Git
- Use `.env.example` as template with dummy values
- Rotate API keys regularly
- Use different keys for dev/staging/production

**2. Service Account Keys**
- Store GCP service account keys in `credentials/` (gitignored)
- Use minimal permissions for dev service accounts
- Never commit service account JSON files

**3. Database Security**
- Use strong passwords even in development
- Don't expose PostgreSQL port publicly
- Regular backups of development database

**4. OAuth Configuration (Phase 0)**
- Restrict OAuth redirect URIs to localhost for dev
- Use separate OAuth client for development
- Test domain restriction (@your-domain.com) in dev environment

**5. Dependency Security**
```bash
# Scan for vulnerabilities
pip-audit                    # Backend
npm audit                    # Frontend

# Update dependencies
pip install --upgrade -r requirements.txt
npm update
```

**6. Local HTTPS (Optional)**
```bash
# Generate self-signed certificates for testing
mkcert localhost 127.0.0.1 ::1

# Configure Vite to use HTTPS
# vite.config.ts:
server: {
  https: {
    key: fs.readFileSync('./localhost-key.pem'),
    cert: fs.readFileSync('./localhost.pem')
  }
}
```

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Vite Documentation**: https://vitejs.dev/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Docker Documentation**: https://docs.docker.com/

---

**Last Updated**: 2026-01-15
**Maintained By**: DevOps Team
**Next Review**: 2026-04-15
