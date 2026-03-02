# Monitoring & Observability Setup Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Monitoring Architecture](#monitoring-architecture)
4. [Cloud Monitoring Setup](#cloud-monitoring-setup)
5. [Sentry Error Tracking](#sentry-error-tracking)
6. [Application Logging](#application-logging)
7. [Custom Metrics](#custom-metrics)
8. [Alert Policies](#alert-policies)
9. [Dashboards](#dashboards)
10. [Uptime Checks](#uptime-checks)
11. [Cost Monitoring](#cost-monitoring)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)

---

## Overview

This guide covers the complete monitoring and observability setup for the PDP Automation system. The monitoring stack provides real-time visibility into application performance, errors, and infrastructure health.

**Monitoring Stack:**
- **Cloud Monitoring**: Infrastructure metrics, logs, and alerts
- **Sentry**: Application error tracking and performance monitoring
- **Cloud Logging**: Centralized log aggregation
- **Cloud Trace**: Distributed tracing (optional)
- **Uptime Monitoring**: Endpoint availability checks

**Key Objectives:**
- Detect issues before users report them
- Reduce mean time to resolution (MTTR)
- Track API performance and errors
- Monitor Anthropic API usage and costs
- Alert on-call engineers for critical issues

---

## Prerequisites

### Required Accounts

**1. GCP Project Access:**
```bash
export PROJECT_ID="YOUR-GCP-PROJECT-ID"
export REGION="us-central1"

# Verify access
gcloud config set project $PROJECT_ID
```

**2. Sentry Account:**
- Sign up at https://sentry.io
- Create organization: "PDP Automation"
- Create projects: "pdp-backend" and "pdp-frontend"

**3. Notification Channels:**
- Email addresses for alerts
- Slack webhook URL (optional)
- PagerDuty integration key (optional)

### Enable Required APIs

```bash
# Enable monitoring and logging APIs
gcloud services enable \
  monitoring.googleapis.com \
  logging.googleapis.com \
  cloudtrace.googleapis.com \
  clouderrorreporting.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled | grep -E "monitoring|logging"
```

---

## Monitoring Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Backend (Cloud Run)          Frontend (Cloud Storage)      │
│  ├─ FastAPI logs             ├─ JS errors                   │
│  ├─ Custom metrics            ├─ Performance metrics         │
│  └─ Traces                    └─ User interactions           │
└───────────────┬───────────────────────────┬─────────────────┘
                │                           │
                ├───────────────────────────┤
                │                           │
        ┌───────▼──────┐          ┌────────▼────────┐
        │ Cloud Logging │          │     Sentry      │
        │ & Monitoring  │          │  Error Tracking │
        └───────┬───────┘          └────────┬────────┘
                │                           │
        ┌───────▼────────────────────────────▼────────┐
        │           Alert Policies                     │
        │  ├─ High error rate                          │
        │  ├─ Slow response time                       │
        │  ├─ API quota exceeded                       │
        │  └─ Service unavailable                      │
        └────────────────┬─────────────────────────────┘
                         │
        ┌────────────────▼──────────────────┐
        │     Notification Channels         │
        │  ├─ Email                         │
        │  ├─ Slack                         │
        │  └─ PagerDuty                     │
        └───────────────────────────────────┘
```

---

## Cloud Monitoring Setup

### 1. Install Monitoring Agent (Backend)

**Add to backend/requirements.txt:**
```txt
google-cloud-logging==3.8.0
google-cloud-monitoring==2.18.0
google-cloud-trace==1.11.1
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
prometheus-client==0.19.0
```

**Backend monitoring setup (app/monitoring.py):**
```python
import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from google.cloud import logging as cloud_logging
from google.cloud import monitoring_v3
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize Cloud Logging
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger("pdp-automation")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

ANTHROPIC_API_CALLS = Counter(
    'anthropic_api_calls_total',
    'Total Anthropic API calls',
    ['model', 'status']
)

ANTHROPIC_TOKEN_USAGE = Counter(
    'anthropic_tokens_total',
    'Total Anthropic tokens used',
    ['model', 'token_type']
)

DATABASE_QUERIES = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP metrics."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Increment active requests
        ACTIVE_REQUESTS.inc()

        # Start timer
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.exception("Request failed", extra={
                "path": request.url.path,
                "method": request.method,
            })
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            ACTIVE_REQUESTS.dec()

            # Log slow requests
            if duration > 5.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path}",
                    extra={
                        "duration": duration,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                    }
                )

        return response


def setup_monitoring(app: FastAPI) -> None:
    """Configure monitoring for the application."""

    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)

    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )

    logger.info("Monitoring configured successfully")


def track_anthropic_call(model: str, tokens: dict, success: bool) -> None:
    """Track Anthropic API call metrics."""
    status = "success" if success else "error"

    ANTHROPIC_API_CALLS.labels(
        model=model,
        status=status
    ).inc()

    if success and tokens:
        ANTHROPIC_TOKEN_USAGE.labels(
            model=model,
            token_type="prompt"
        ).inc(tokens.get("prompt_tokens", 0))

        ANTHROPIC_TOKEN_USAGE.labels(
            model=model,
            token_type="completion"
        ).inc(tokens.get("completion_tokens", 0))


def track_database_query(operation: str, duration: float) -> None:
    """Track database query metrics."""
    DATABASE_QUERIES.labels(operation=operation).observe(duration)
```

**Enable monitoring in main.py:**
```python
from app.monitoring import setup_monitoring

app = FastAPI(title="PDP Automation API")

# Setup monitoring
setup_monitoring(app)
```

### 2. Configure Cloud Logging

**Structured logging (app/logging_config.py):**
```python
import logging
import json
from typing import Any, Dict

from google.cloud import logging as cloud_logging


class StructuredLogger:
    """Structured logger for Cloud Logging."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

    def log(
        self,
        message: str,
        severity: str = "INFO",
        **kwargs: Any
    ) -> None:
        """Log structured message."""
        log_entry = {
            "message": message,
            "severity": severity,
            **kwargs
        }

        if severity == "ERROR":
            self.logger.error(json.dumps(log_entry))
        elif severity == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif severity == "DEBUG":
            self.logger.debug(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry))

    def info(self, message: str, **kwargs: Any) -> None:
        self.log(message, "INFO", **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.log(message, "ERROR", **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.log(message, "WARNING", **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.log(message, "DEBUG", **kwargs)


# Example usage
logger = StructuredLogger("pdp-automation")

logger.info(
    "PDP generated successfully",
    user_id="user123",
    pdp_id="pdp456",
    duration_ms=1234
)
```

### 3. Create Custom Metrics

```bash
# Create custom metric descriptor
gcloud monitoring metric-descriptors create \
  custom.googleapis.com/pdp/generation_count \
  --project=$PROJECT_ID \
  --display-name="PDP Generation Count" \
  --description="Number of PDPs generated" \
  --metric-kind=CUMULATIVE \
  --value-type=INT64 \
  --unit=1

# Create metric for Anthropic API calls
gcloud monitoring metric-descriptors create \
  custom.googleapis.com/anthropic/api_calls \
  --project=$PROJECT_ID \
  --display-name="Anthropic API Calls" \
  --description="Number of Anthropic API calls" \
  --metric-kind=CUMULATIVE \
  --value-type=INT64 \
  --unit=1
```

**Write custom metrics from Python:**
```python
from google.cloud import monitoring_v3
import time

def write_custom_metric(
    project_id: str,
    metric_type: str,
    value: int
) -> None:
    """Write custom metric to Cloud Monitoring."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_type}"
    series.resource.type = "global"

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)

    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )

    point = monitoring_v3.Point(
        {"interval": interval, "value": {"int64_value": value}}
    )

    series.points = [point]
    client.create_time_series(name=project_name, time_series=[series])


# Usage
write_custom_metric(
    project_id="YOUR-GCP-PROJECT-ID",
    metric_type="pdp/generation_count",
    value=1
)
```

---

## Sentry Error Tracking

### 1. Backend Integration

**Install Sentry SDK:**
```bash
pip install sentry-sdk[fastapi]==1.39.0
```

**Configure Sentry (app/main.py):**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.config import settings

# Initialize Sentry
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    release=f"pdp-backend@{settings.VERSION}",
    integrations=[
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes=[500, 501, 502, 503, 504, 505]
        ),
        SqlalchemyIntegration(),
    ],
    # Performance monitoring
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,  # 10% of transactions

    # Error filtering
    ignore_errors=[
        KeyboardInterrupt,
        ConnectionError,
    ],

    # PII filtering
    send_default_pii=False,

    # Additional context
    attach_stacktrace=True,
    max_breadcrumbs=50,
)

app = FastAPI()

# Add user context to Sentry
@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    # Get user from request (if authenticated)
    user = getattr(request.state, "user", None)

    if user:
        sentry_sdk.set_user({
            "id": user.id,
            "email": user.email,
            "username": user.name,
        })

    sentry_sdk.set_tag("endpoint", request.url.path)
    sentry_sdk.set_tag("method", request.method)

    response = await call_next(request)
    return response
```

**Capture custom exceptions:**
```python
from sentry_sdk import capture_exception, capture_message

try:
    # Generate PDP
    result = await generate_pdp(data)
except AnthropicError as e:
    # Capture exception with context
    capture_exception(e, level="error", extras={
        "user_id": user.id,
        "pdp_data": data,
        "anthropic_model": "claude-sonnet-4-5"
    })
    raise

# Capture informational message
capture_message(
    "PDP generation took longer than expected",
    level="warning",
    extras={"duration_ms": 5000}
)
```

### 2. Frontend Integration

**Install Sentry SDK:**
```bash
npm install @sentry/react @sentry/browser
```

**Configure Sentry (src/monitoring/sentry.ts):**
```typescript
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';

export function initSentry() {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENV,
    release: `pdp-frontend@${import.meta.env.VITE_APP_VERSION}`,

    integrations: [
      new BrowserTracing({
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          React.useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
      }),
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Performance Monitoring
    tracesSampleRate: 0.1,

    // Session Replay
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Filter out PII
    beforeSend(event, hint) {
      // Don't send password fields
      if (event.request?.data) {
        delete event.request.data.password;
      }
      return event;
    },

    // Ignore specific errors
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Network request failed',
    ],
  });
}

// Set user context after authentication
export function setUserContext(user: User) {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.name,
  });
}

// Clear user context on logout
export function clearUserContext() {
  Sentry.setUser(null);
}
```

**Wrap app with Sentry (src/main.tsx):**
```typescript
import { initSentry } from './monitoring/sentry';

// Initialize Sentry
initSentry();

const root = ReactDOM.createRoot(document.getElementById('root')!);

root.render(
  <React.StrictMode>
    <Sentry.ErrorBoundary
      fallback={<ErrorFallback />}
      showDialog
    >
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>
);
```

---

## Application Logging

### Log Levels

```python
# DEBUG: Detailed information for debugging
logger.debug("Processing PDP generation request", extra={
    "user_id": user.id,
    "input_data": data
})

# INFO: General informational messages
logger.info("PDP generated successfully", extra={
    "pdp_id": pdp.id,
    "duration_ms": 1234
})

# WARNING: Something unexpected but not critical
logger.warning("Anthropic rate limit approaching", extra={
    "usage_percent": 85,
    "requests_remaining": 150
})

# ERROR: Error occurred but application continues
logger.error("Failed to send email notification", extra={
    "user_id": user.id,
    "error": str(e)
})

# CRITICAL: Critical error requiring immediate attention
logger.critical("Database connection lost", extra={
    "database_url": "postgresql://...",
    "error": str(e)
})
```

### Log Correlation

**Add trace IDs to logs:**
```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_trace_id(request: Request, call_next):
    # Generate or extract trace ID
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))

    # Add to request state
    request.state.trace_id = trace_id

    # Add to all logs
    logger = logging.LoggerAdapter(
        logging.getLogger("pdp-automation"),
        {"trace_id": trace_id}
    )

    request.state.logger = logger

    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id

    return response
```

---

## Custom Metrics

### Backend Metrics

**PDP Generation Metrics:**
```python
PDP_GENERATION_COUNT = Counter(
    'pdp_generation_total',
    'Total number of PDPs generated',
    ['status']
)

PDP_GENERATION_DURATION = Histogram(
    'pdp_generation_duration_seconds',
    'PDP generation duration',
    buckets=[1, 5, 10, 30, 60, 120]
)

# Track PDP generation
start = time.time()
try:
    pdp = await generate_pdp(data)
    PDP_GENERATION_COUNT.labels(status='success').inc()
except Exception:
    PDP_GENERATION_COUNT.labels(status='error').inc()
    raise
finally:
    duration = time.time() - start
    PDP_GENERATION_DURATION.observe(duration)
```

**Anthropic API Metrics:**
```python
ANTHROPIC_API_LATENCY = Histogram(
    'anthropic_api_latency_seconds',
    'Anthropic API call latency',
    ['model']
)

ANTHROPIC_API_COST = Counter(
    'anthropic_api_cost_dollars',
    'Estimated Anthropic API cost',
    ['model']
)

# Track Anthropic call
start = time.time()
response = await anthropic_client.messages.create(
    model="claude-sonnet-4-5-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
latency = time.time() - start

ANTHROPIC_API_LATENCY.labels(model="claude-sonnet-4-5").observe(latency)

# Estimate cost (approximate)
tokens = response.usage.total_tokens
cost = (tokens / 1000) * 0.01  # $0.01 per 1K tokens
ANTHROPIC_API_COST.labels(model="claude-sonnet-4-5").inc(cost)
```

---

## Alert Policies

### Create Alert Policies

**1. High Error Rate:**
```bash
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL_CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s \
  --aggregation-cross-series-reducer=REDUCE_MEAN \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/request_count"
    AND resource.type="cloud_run_revision"
    AND metric.label.response_code_class="5xx"
  '
```

**2. Slow Response Time:**
```bash
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL_CHANNEL_ID \
  --display-name="Slow Response Time" \
  --condition-display-name="P95 latency > 10s" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=300s \
  --aggregation-aligner=ALIGN_DELTA \
  --aggregation-per-series-aligner=ALIGN_PERCENTILE_95 \
  --condition-threshold-filter='
    metric.type="run.googleapis.com/request_latencies"
    AND resource.type="cloud_run_revision"
  '
```

**3. Anthropic API Quota:**
```bash
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL_CHANNEL_ID,SLACK_CHANNEL_ID \
  --display-name="Anthropic API Quota Warning" \
  --condition-display-name="Anthropic calls > 80% of quota" \
  --condition-threshold-value=8000 \
  --condition-threshold-duration=60s \
  --condition-threshold-filter='
    metric.type="custom.googleapis.com/anthropic/api_calls"
  '
```

**4. Database Connection Pool Exhausted:**
```bash
gcloud alpha monitoring policies create \
  --notification-channels=PAGERDUTY_CHANNEL_ID \
  --display-name="Database Connection Pool Exhausted" \
  --condition-display-name="Active connections > 90% of pool" \
  --condition-threshold-value=45 \
  --condition-threshold-duration=60s \
  --condition-threshold-filter='
    metric.type="custom.googleapis.com/database/active_connections"
  '
```

### Configure Notification Channels

**Email:**
```bash
gcloud alpha monitoring channels create \
  --display-name="Engineering Team Email" \
  --type=email \
  --channel-labels=email_address=eng-team@your-domain.com
```

**Slack:**
```bash
gcloud alpha monitoring channels create \
  --display-name="Engineering Slack Channel" \
  --type=slack \
  --channel-labels=url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**PagerDuty:**
```bash
gcloud alpha monitoring channels create \
  --display-name="PagerDuty On-Call" \
  --type=pagerduty \
  --channel-labels=service_key=YOUR_PAGERDUTY_SERVICE_KEY
```

---

## Dashboards

### Create Custom Dashboard

```bash
# Create dashboard configuration file
cat > dashboard.json <<EOF
{
  "displayName": "PDP Automation Dashboard",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.response_code_class=\"5xx\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF

# Create dashboard
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

**Dashboard Widgets:**
- Request rate (requests/second)
- Error rate (%)
- Response time (P50, P95, P99)
- Active instances
- Memory usage
- CPU utilization
- Anthropic API calls
- Anthropic token usage
- Database query performance
- PDP generation count

---

## Uptime Checks

### Configure Uptime Monitoring

```bash
# Create uptime check for backend
gcloud monitoring uptime-checks create \
  pdp-api-health-check \
  --resource-type=uptime-url \
  --host=api.pdp-automation.com \
  --path=/health \
  --port=443 \
  --protocol=HTTPS \
  --check-interval=60s \
  --timeout=10s \
  --display-name="PDP API Health Check"

# Create uptime check for frontend
gcloud monitoring uptime-checks create \
  pdp-web-uptime-check \
  --resource-type=uptime-url \
  --host=pdp-automation.com \
  --path=/ \
  --port=443 \
  --protocol=HTTPS \
  --check-interval=60s \
  --timeout=10s \
  --display-name="PDP Web Uptime Check"

# Create alert on uptime check failure
gcloud alpha monitoring policies create \
  --notification-channels=PAGERDUTY_CHANNEL_ID \
  --display-name="Service Down" \
  --condition-display-name="Uptime check failed" \
  --condition-threshold-value=1 \
  --condition-threshold-duration=180s \
  --condition-threshold-filter='
    metric.type="monitoring.googleapis.com/uptime_check/check_passed"
    AND metric.label.check_id="pdp-api-health-check"
  ' \
  --condition-threshold-comparison=COMPARISON_LT
```

---

## Cost Monitoring

### Budget Alerts

```bash
# Create budget
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="PDP Automation Monthly Budget" \
  --budget-amount=1000 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100 \
  --notification-channels=EMAIL_CHANNEL_ID

# Monitor Anthropic API costs
# (Track via custom metrics and alert when approaching budget)
```

---

## Troubleshooting

### Common Issues

**Issue: Metrics not appearing**
```bash
# Verify monitoring agent is running
gcloud run services describe pdp-automation-api \
  --region=$REGION \
  --format='value(status.conditions)'

# Check logs for errors
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

**Issue: Alerts not firing**
```bash
# Check alert policy status
gcloud alpha monitoring policies list

# Test notification channel
gcloud alpha monitoring channels verify <CHANNEL_ID>
```

---

## Security Considerations

- Never log sensitive data (passwords, API keys, PII)
- Use structured logging for easier querying
- Implement log retention policies
- Restrict access to logs and metrics
- Enable audit logging for compliance

---

**Last Updated**: 2026-01-15
**Maintained By**: DevOps Team
**Next Review**: 2026-04-15
