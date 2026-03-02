# Agent Brief: DEV-MONITORING-001

**Agent ID:** DEV-MONITORING-001
**Agent Name:** Monitoring Agent
**Type:** Development
**Phase:** 6 - DevOps
**Context Budget:** 50,000 tokens

---

## Mission

Implement monitoring, alerting, and logging infrastructure using Google Cloud Operations (Stackdriver).

---

## Documentation to Read

### Primary
1. `docs/06-devops/MONITORING_SETUP.md` - Monitoring requirements

### Secondary
1. `docs/06-devops/BACKUP_RECOVERY.md` - Recovery procedures

---

## Dependencies

**Upstream:** DEV-CLOUDRUN-001
**Downstream:** None (Final DevOps phase)

---

## Outputs

### `infrastructure/monitoring/alerts.yaml`
### `infrastructure/monitoring/dashboards.json`
### `backend/app/utils/logging.py`

---

## Acceptance Criteria

1. **Logging:**
   - Structured JSON logging
   - Request/response logging
   - Error logging with stack traces
   - Correlation IDs
   - PII redaction

2. **Metrics:**
   - Request latency
   - Error rates
   - Job processing time
   - API call counts
   - Database query time

3. **Dashboards:**
   - System overview
   - API performance
   - Job processing status
   - Error tracking
   - Cost monitoring

4. **Alerts:**
   - High error rate (>1%)
   - High latency (>2s p95)
   - Service down
   - Job failures
   - Budget threshold

5. **Notification Channels:**
   - Slack integration
   - Email alerts
   - PagerDuty (critical only)

6. **Log Retention:**
   - 30 days standard logs
   - 90 days error logs
   - 1 year audit logs

---

## Alert Definitions

```yaml
# Critical: Immediate action required
- High Error Rate: >5% for 5 minutes
- Service Unavailable: Health check fails 3x
- Database Connection Failed

# Warning: Investigation needed
- Elevated Latency: >1s p95 for 10 minutes
- High Memory Usage: >80% for 15 minutes
- Job Queue Backlog: >100 jobs pending
```

---

## QA Pair: QA-MONITORING-001

---

**Begin execution.**
