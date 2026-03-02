# Backup & Disaster Recovery Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Backup Strategy](#backup-strategy)
4. [Database Backups](#database-backups)
5. [File Storage Backups](#file-storage-backups)
6. [Application Backups](#application-backups)
7. [Backup Verification](#backup-verification)
8. [Disaster Recovery Plans](#disaster-recovery-plans)
9. [Recovery Procedures](#recovery-procedures)
10. [Testing DR Plan](#testing-dr-plan)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)

---

## Overview

This guide covers the comprehensive backup and disaster recovery (DR) strategy for the PDP Automation system. The strategy ensures business continuity with minimal data loss and downtime in the event of failures or disasters.

**Backup Architecture:**
- **Database**: Neon PostgreSQL with automatic continuous backups
- **File Storage**: Cloud Storage with versioning and cross-region replication
- **Application Code**: Git repository with multiple remote copies
- **Configuration**: Secret Manager with version history

**Recovery Objectives:**
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss

| Component | RTO | RPO |
|-----------|-----|-----|
| Database | 30 minutes | Point-in-time (continuous) |
| File Storage | 5 minutes | 0 (real-time replication) |
| Backend API | 5 minutes | 0 (stateless) |
| Frontend | 1 minute | 0 (static assets) |

---

## Prerequisites

### Required Access

**1. GCP Project Access:**
```bash
export PROJECT_ID="YOUR-GCP-PROJECT-ID"
export REGION="us-central1"
export BACKUP_REGION="us-west1"

# Verify access
gcloud config set project $PROJECT_ID
```

**2. Neon Database Access:**
- Neon console access (https://console.neon.tech)
- API key for automated operations
- Database connection credentials

**3. Required Permissions:**
- Storage Admin (for bucket backups)
- Cloud Run Admin (for service recovery)
- Secret Manager Admin (for secrets backup)

### Install Required Tools

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Install PostgreSQL client
sudo apt install postgresql-client  # Linux
brew install postgresql@15          # macOS

# Install gsutil (included with gcloud)
gcloud components install gsutil
```

---

## Backup Strategy

### Backup Types

**1. Automated Backups:**
- Database: Continuous backup via Neon
- File Storage: Real-time replication via Cloud Storage
- Frequency: Continuous
- Retention: 7-30 days (configurable)

**2. Manual Backups:**
- Pre-deployment snapshots
- Major version upgrades
- Before data migrations
- Retention: 90 days

**3. Snapshot Backups:**
- Weekly full backups
- Daily incremental backups
- Retention: 4 weeks (weekly), 7 days (daily)

### Backup Schedule

```
┌──────────────┬──────────────┬─────────────┬─────────────┐
│   Component  │   Frequency  │  Retention  │    Type     │
├──────────────┼──────────────┼─────────────┼─────────────┤
│  Database    │  Continuous  │   30 days   │  Automatic  │
│  Files       │  Real-time   │   Unlimited │  Automatic  │
│  Config      │  On change   │   100 ver   │  Automatic  │
│  Full Backup │  Weekly      │   4 weeks   │    Manual   │
│  Pre-deploy  │  On demand   │   90 days   │    Manual   │
└──────────────┴──────────────┴─────────────┴─────────────┘
```

---

## Database Backups

### Neon Automatic Backups

**Neon provides continuous backup automatically:**

```bash
# View backup status (via Neon console)
# Navigate to: Project → Backups

# Backup features:
# - Point-in-time recovery (PITR)
# - Continuous backup of all transactions
# - 7-day retention (free tier)
# - 30-day retention (paid tier)
# - Restore to any point in time within retention period
```

**Backup retention policy:**
- **Free tier**: 7 days of PITR
- **Paid tier**: 30 days of PITR
- **Custom retention**: Contact Neon support

### Manual Database Backups

**1. Full Database Dump:**

```bash
#!/bin/bash
# scripts/backup_database.sh

set -e

# Configuration
DATABASE_URL="postgresql://user:pass@ep-xxx.us-central-1.aws.neon.tech/neondb?sslmode=require"
BACKUP_DIR="/tmp/backups"
BACKUP_BUCKET="gs://pdp-automation-backups/database"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="pdp_automation_${DATE}.sql"
BACKUP_COMPRESSED="${BACKUP_FILE}.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."

# Dump database
pg_dump "$DATABASE_URL" \
  --verbose \
  --format=plain \
  --no-owner \
  --no-acl \
  --file="$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
echo "Compressing backup..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Upload to Cloud Storage
echo "Uploading to Cloud Storage..."
gsutil cp "$BACKUP_DIR/$BACKUP_COMPRESSED" "$BACKUP_BUCKET/"

# Verify upload
if gsutil ls "$BACKUP_BUCKET/$BACKUP_COMPRESSED" > /dev/null 2>&1; then
  echo "✓ Backup uploaded successfully"
else
  echo "✗ Backup upload failed"
  exit 1
fi

# Clean up local file
rm "$BACKUP_DIR/$BACKUP_COMPRESSED"

echo "Backup completed: $BACKUP_BUCKET/$BACKUP_COMPRESSED"
```

**2. Schema-Only Backup:**

```bash
# Backup schema only (for quick restores)
pg_dump "$DATABASE_URL" \
  --schema-only \
  --no-owner \
  --no-acl \
  --file=schema_backup.sql

# Upload to Cloud Storage
gsutil cp schema_backup.sql gs://pdp-automation-backups/database/schema/
```

**3. Data-Only Backup:**

```bash
# Backup data only (exclude schema)
pg_dump "$DATABASE_URL" \
  --data-only \
  --no-owner \
  --no-acl \
  --file=data_backup.sql

# Upload to Cloud Storage
gsutil cp data_backup.sql gs://pdp-automation-backups/database/data/
```

**4. Table-Specific Backup:**

```bash
# Backup specific tables
pg_dump "$DATABASE_URL" \
  --table=users \
  --table=pdps \
  --table=tasks \
  --file=critical_tables_backup.sql

gsutil cp critical_tables_backup.sql gs://pdp-automation-backups/database/tables/
```

### Automated Backup Script (Cron Job)

```bash
# Create backup script
cat > /usr/local/bin/pdp-db-backup.sh <<'EOF'
#!/bin/bash
/path/to/scripts/backup_database.sh 2>&1 | tee -a /var/log/pdp-backup.log
EOF

chmod +x /usr/local/bin/pdp-db-backup.sh

# Add to crontab (daily at 3 AM)
crontab -e

# Add line:
0 3 * * * /usr/local/bin/pdp-db-backup.sh
```

### Cloud Scheduler (GCP Alternative)

```bash
# Create Cloud Scheduler job for automated backups
gcloud scheduler jobs create http pdp-database-backup \
  --schedule="0 3 * * *" \
  --uri="https://backup-service-xxx.run.app/backup/database" \
  --http-method=POST \
  --time-zone="UTC" \
  --description="Daily database backup"
```

---

## File Storage Backups

### Cloud Storage Configuration

**1. Enable Versioning:**

```bash
# Enable versioning for uploads bucket
gsutil versioning set on gs://pdp-automation-uploads

# Verify versioning
gsutil versioning get gs://pdp-automation-uploads
# Output: gs://pdp-automation-uploads: Enabled
```

**2. Configure Lifecycle Management:**

```bash
# Create lifecycle policy
cat > lifecycle_policy.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 90,
          "isLive": false
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 1,
          "matchesPrefix": ["temp/"]
        }
      },
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "NEARLINE"
        },
        "condition": {
          "age": 30,
          "matchesStorageClass": ["STANDARD"]
        }
      }
    ]
  }
}
EOF

# Apply lifecycle policy
gsutil lifecycle set lifecycle_policy.json gs://pdp-automation-uploads

# Verify lifecycle policy
gsutil lifecycle get gs://pdp-automation-uploads
```

**3. Enable Cross-Region Replication:**

```bash
# Create backup bucket in different region
gsutil mb -p $PROJECT_ID \
  -c STANDARD \
  -l $BACKUP_REGION \
  gs://pdp-automation-uploads-backup

# Set up replication (requires Turbo Replication - paid feature)
# Or use gsutil rsync for periodic sync:

#!/bin/bash
# Sync to backup region daily
gsutil -m rsync -r -d \
  gs://pdp-automation-uploads/ \
  gs://pdp-automation-uploads-backup/
```

### Manual File Backups

```bash
# Full backup of uploads bucket
gsutil -m rsync -r gs://pdp-automation-uploads/ \
  gs://pdp-automation-backups/uploads/$(date +%Y%m%d)/

# Backup frontend assets
gsutil -m rsync -r gs://pdp-automation-web/ \
  gs://pdp-automation-backups/frontend/$(date +%Y%m%d)/

# Verify backup size
gsutil du -sh gs://pdp-automation-backups/
```

### Restore Files from Versioning

```bash
# List all versions of a file
gsutil ls -a gs://pdp-automation-uploads/path/to/file.pdf

# Restore specific version
gsutil cp gs://pdp-automation-uploads/path/to/file.pdf#1234567890 \
  gs://pdp-automation-uploads/path/to/file.pdf

# Restore entire bucket to previous state
gsutil -m rsync -r -d \
  gs://pdp-automation-uploads-backup/ \
  gs://pdp-automation-uploads/
```

---

## Application Backups

### Backend Configuration Backup

**1. Export Secrets:**

```bash
#!/bin/bash
# scripts/backup_secrets.sh

BACKUP_DIR="./backups/secrets"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="secrets_${DATE}.json"

mkdir -p "$BACKUP_DIR"

# Export all secrets (values are NOT exported for security)
gcloud secrets list --format=json > "$BACKUP_DIR/$BACKUP_FILE"

# Upload to secure backup location
gsutil cp "$BACKUP_DIR/$BACKUP_FILE" \
  gs://pdp-automation-backups/secrets/

echo "Secrets metadata backed up: $BACKUP_FILE"
```

**2. Export Cloud Run Configuration:**

```bash
# Export Cloud Run service configuration
gcloud run services describe pdp-automation-api \
  --region=$REGION \
  --format=yaml > backend_service_config.yaml

# Upload to backup
gsutil cp backend_service_config.yaml \
  gs://pdp-automation-backups/config/
```

**3. Export IAM Policies:**

```bash
# Export IAM policies
gcloud projects get-iam-policy $PROJECT_ID \
  --format=json > iam_policy_backup.json

gsutil cp iam_policy_backup.json \
  gs://pdp-automation-backups/config/
```

### Frontend Configuration Backup

```bash
# Backup frontend environment configuration
# (Already backed up in Git repository)

# Backup build configuration
gsutil cp frontend/vite.config.ts \
  gs://pdp-automation-backups/config/

# Backup package.json and package-lock.json
gsutil cp frontend/package*.json \
  gs://pdp-automation-backups/config/
```

---

## Backup Verification

### Automated Verification Script

```bash
#!/bin/bash
# scripts/verify_backups.sh

set -e

echo "Verifying backups..."

# 1. Verify database backup
LATEST_DB_BACKUP=$(gsutil ls -l gs://pdp-automation-backups/database/ | sort -k2 | tail -n 1 | awk '{print $3}')

if [ -z "$LATEST_DB_BACKUP" ]; then
  echo "✗ No database backup found"
  exit 1
fi

# Check backup age (should be less than 24 hours old)
BACKUP_TIME=$(gsutil ls -L "$LATEST_DB_BACKUP" | grep "Time created:" | awk '{print $3,$4}')
BACKUP_TIMESTAMP=$(date -d "$BACKUP_TIME" +%s)
CURRENT_TIMESTAMP=$(date +%s)
AGE_HOURS=$(( ($CURRENT_TIMESTAMP - $BACKUP_TIMESTAMP) / 3600 ))

if [ $AGE_HOURS -gt 24 ]; then
  echo "✗ Database backup is too old ($AGE_HOURS hours)"
  exit 1
else
  echo "✓ Database backup is current (${AGE_HOURS}h old)"
fi

# 2. Verify file storage versioning
VERSIONING_STATUS=$(gsutil versioning get gs://pdp-automation-uploads)

if [[ "$VERSIONING_STATUS" == *"Enabled"* ]]; then
  echo "✓ File versioning is enabled"
else
  echo "✗ File versioning is disabled"
  exit 1
fi

# 3. Verify cross-region replication
UPLOAD_COUNT=$(gsutil ls -r gs://pdp-automation-uploads/ | wc -l)
BACKUP_COUNT=$(gsutil ls -r gs://pdp-automation-uploads-backup/ | wc -l)

if [ $UPLOAD_COUNT -eq $BACKUP_COUNT ]; then
  echo "✓ Cross-region replication is current"
else
  echo "⚠ Cross-region replication may be out of sync"
fi

echo "Backup verification completed"
```

### Test Restore Procedure

```bash
#!/bin/bash
# scripts/test_restore.sh

set -e

echo "Testing database restore..."

# 1. Create test database
TEST_DB="pdp_automation_test_restore"
createdb $TEST_DB

# 2. Download latest backup
LATEST_BACKUP=$(gsutil ls gs://pdp-automation-backups/database/ | sort | tail -n 1)
gsutil cp "$LATEST_BACKUP" /tmp/test_restore.sql.gz

# 3. Restore to test database
gunzip /tmp/test_restore.sql.gz
psql $TEST_DB < /tmp/test_restore.sql

# 4. Verify data integrity
psql $TEST_DB -c "SELECT COUNT(*) FROM users;"
psql $TEST_DB -c "SELECT COUNT(*) FROM pdps;"

# 5. Clean up
dropdb $TEST_DB
rm /tmp/test_restore.sql

echo "✓ Restore test completed successfully"
```

---

## Disaster Recovery Plans

### Scenario 1: Database Corruption

**Problem**: Database data is corrupted or accidentally deleted.

**Recovery Steps:**

```bash
# 1. Identify last known good state
# Check recent backups
gsutil ls -l gs://pdp-automation-backups/database/

# 2. Stop backend API (prevent further corruption)
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=0 \
  --max-instances=0

# 3. Restore from Neon backup (preferred method)
# Navigate to Neon console → Backups
# Select restore point
# Click "Restore" → Creates new database branch
# Get new connection string

# 4. Update backend with new connection string
echo -n "new-database-connection-string" | \
  gcloud secrets versions add database-url --data-file=-

# 5. Restart backend API
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=1 \
  --max-instances=10

# 6. Verify restoration
curl https://api.pdp-automation.com/health

# RTO: 30 minutes
# RPO: Point-in-time (continuous)
```

**Alternative: Restore from manual backup:**

```bash
# Download backup
gsutil cp gs://pdp-automation-backups/database/pdp_automation_20260115.sql.gz /tmp/

# Decompress
gunzip /tmp/pdp_automation_20260115.sql.gz

# Create new Neon database branch
# (Use Neon console or API)

# Restore data
psql "$NEW_DATABASE_URL" < /tmp/pdp_automation_20260115.sql

# Update connection string and restart
```

### Scenario 2: Region Outage (us-central1)

**Problem**: Primary GCP region is unavailable.

**Recovery Steps:**

```bash
# 1. Verify outage scope
gcloud compute regions describe us-central1

# 2. Activate backup region (us-west1)

# Backend: Deploy to backup region
gcloud run deploy pdp-automation-api \
  --image=gcr.io/$PROJECT_ID/pdp-automation-api:latest \
  --region=us-west1 \
  --platform=managed \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=10 \
  --service-account=pdp-api@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-secrets="DATABASE_URL=database-url:latest,..."

# 3. Update DNS to point to new region
# Update A/CNAME records to point to new Cloud Run URL

# 4. Frontend: Already on global CDN (no action needed)

# 5. Database: Switch to Neon backup region (if configured)
# Neon handles regional failover automatically

# 6. Monitor new deployment
gcloud run services logs pdp-automation-api \
  --region=us-west1 \
  --follow

# RTO: 5 minutes
# RPO: 0 (stateless backend, real-time replication)
```

### Scenario 3: Accidental Data Deletion

**Problem**: User or admin accidentally deletes data.

**Recovery Steps:**

```bash
# 1. Identify what was deleted and when
# Check audit logs
gcloud logging read "protoPayload.methodName=delete" \
  --limit=50 \
  --format=json

# 2. Stop application (prevent cascading deletes)
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=0

# 3. Restore from point-in-time (Neon)
# Navigate to Neon console → Backups
# Select time before deletion
# Restore to new branch

# 4. Extract deleted data
pg_dump "$RESTORED_DATABASE_URL" \
  --table=deleted_table \
  --data-only > deleted_data.sql

# 5. Import data to production
psql "$PRODUCTION_DATABASE_URL" < deleted_data.sql

# 6. Verify data integrity
psql "$PRODUCTION_DATABASE_URL" -c "SELECT COUNT(*) FROM deleted_table;"

# 7. Restart application
gcloud run services update pdp-automation-api \
  --region=$REGION \
  --min-instances=1

# RTO: 1 hour
# RPO: Point-in-time (depends on when deletion occurred)
```

### Scenario 4: Complete Infrastructure Loss

**Problem**: Entire GCP project is compromised or deleted.

**Recovery Steps:**

```bash
# 1. Create new GCP project
gcloud projects create pdp-automation-recovery \
  --name="PDP Automation Recovery"

export NEW_PROJECT_ID="pdp-automation-recovery"

# 2. Enable required APIs
gcloud services enable run.googleapis.com storage.googleapis.com \
  secretmanager.googleapis.com --project=$NEW_PROJECT_ID

# 3. Restore database
# Create new Neon project
# Restore from manual backup:
gsutil cp gs://pdp-automation-backups/database/latest.sql.gz /tmp/
gunzip /tmp/latest.sql.gz
psql "$NEW_NEON_URL" < /tmp/latest.sql

# 4. Restore secrets
# Manually recreate secrets (values must be retrieved from secure storage)
echo -n "$NEW_DATABASE_URL" | \
  gcloud secrets create database-url --data-file=- --project=$NEW_PROJECT_ID

# 5. Deploy backend
gcloud run deploy pdp-automation-api \
  --image=gcr.io/$PROJECT_ID/pdp-automation-api:latest \
  --region=$REGION \
  --project=$NEW_PROJECT_ID \
  --set-secrets="..."

# 6. Restore frontend
gsutil -m rsync -r gs://pdp-automation-backups/frontend/latest/ \
  gs://pdp-automation-web-new/

# 7. Update DNS
# Point domain to new infrastructure

# 8. Test thoroughly before switching traffic

# RTO: 4-6 hours
# RPO: Last backup (up to 24 hours)
```

---

## Recovery Procedures

### Database Recovery Commands

```bash
# Quick reference for common recovery operations

# 1. Restore entire database from backup
psql "$DATABASE_URL" < backup.sql

# 2. Restore specific table
pg_restore --table=table_name backup.sql | psql "$DATABASE_URL"

# 3. Restore with transaction rollback on error
psql "$DATABASE_URL" --single-transaction < backup.sql

# 4. Restore schema only
psql "$DATABASE_URL" < schema_backup.sql

# 5. Restore data only
psql "$DATABASE_URL" < data_backup.sql
```

### File Storage Recovery

```bash
# 1. Restore entire bucket
gsutil -m rsync -r -d \
  gs://pdp-automation-backups/uploads/latest/ \
  gs://pdp-automation-uploads/

# 2. Restore specific file version
gsutil cp gs://pdp-automation-uploads/file.pdf#1234567890 \
  gs://pdp-automation-uploads/file.pdf

# 3. Restore from cross-region backup
gsutil -m rsync -r \
  gs://pdp-automation-uploads-backup/ \
  gs://pdp-automation-uploads/
```

---

## Testing DR Plan

### Quarterly DR Test Checklist

**Test Schedule**: Every 3 months (January, April, July, October)

**Test Procedure:**

```bash
# 1. Create test environment
./scripts/create_test_environment.sh

# 2. Test database restore
./scripts/test_database_restore.sh

# 3. Test file restore
./scripts/test_file_restore.sh

# 4. Test full application recovery
./scripts/test_full_recovery.sh

# 5. Document results
# - Time to restore: _____ minutes
# - Data loss: _____ minutes/hours
# - Issues encountered: _____
# - Improvements needed: _____

# 6. Update DR plan based on learnings

# 7. Clean up test environment
./scripts/cleanup_test_environment.sh
```

---

## Troubleshooting

### Common Issues

**Issue: Backup script fails**
```bash
# Check logs
tail -f /var/log/pdp-backup.log

# Verify permissions
gcloud projects get-iam-policy $PROJECT_ID

# Test connection
pg_dump "$DATABASE_URL" --schema-only
```

**Issue: Restore fails with permission errors**
```bash
# Grant necessary permissions
psql "$DATABASE_URL" -c "GRANT ALL PRIVILEGES ON DATABASE neondb TO restore_user;"
```

**Issue: Backup size too large**
```bash
# Compress backup
pg_dump "$DATABASE_URL" | gzip > backup.sql.gz

# Split large backups
pg_dump "$DATABASE_URL" | split -b 1G - backup.sql.part_
```

---

## Security Considerations

**1. Backup Encryption**
- Cloud Storage uses encryption at rest by default
- Consider customer-managed encryption keys (CMEK)
- Encrypt backups before uploading

**2. Access Control**
- Restrict backup bucket access
- Use IAM conditions for time-based access
- Audit backup access regularly

**3. Retention Policies**
- Follow data retention regulations
- Secure deletion after retention period
- Document retention decisions

**4. Testing**
- Test restores regularly
- Verify backup integrity
- Practice DR procedures

**5. Compliance**
- GDPR right to deletion
- Data residency requirements
- Audit trail for all backup operations

---

**Last Updated**: 2026-01-15
**Maintained By**: DevOps Team
**Next Review**: 2026-04-15
**Next DR Test**: 2026-04-15
