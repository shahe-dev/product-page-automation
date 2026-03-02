# Error Handling

**Last Updated:** 2026-01-15
**Related Documents:**
- [API Design](../01-architecture/API_DESIGN.md)
- [Service Layer](./SERVICE_LAYER.md)
- [API Endpoints](./API_ENDPOINTS.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Error Response Format](#error-response-format)
3. [Error Codes](#error-codes)
4. [Exception Hierarchy](#exception-hierarchy)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Retry Strategies](#retry-strategies)
7. [Logging and Monitoring](#logging-and-monitoring)
8. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system implements a comprehensive error handling strategy that ensures:
- **Consistent error responses** across all endpoints
- **Detailed error information** for debugging
- **Graceful degradation** when external services fail
- **Automatic retries** for transient errors
- **Comprehensive logging** for all errors

**Error Handling Principles:**
1. **Fail Fast** - Detect errors early and report them immediately
2. **Provide Context** - Include helpful error messages and debugging information
3. **Log Everything** - Comprehensive logging for troubleshooting
4. **Retry Transient Errors** - Automatic retry with exponential backoff
5. **Don't Expose Internals** - Sanitize error messages for users

---

## Error Response Format

All error responses follow a consistent JSON format:

```json
{
  "error_code": "ERROR_CODE_HERE",
  "message": "Human-readable error message",
  "details": {
    "field": "additional context"
  },
  "retry_after": null,
  "trace_id": "abc123-def456"
}
```

**Fields:**
- `error_code` - Machine-readable error code (UPPER_SNAKE_CASE)
- `message` - Human-readable error message
- `details` - Additional context (optional)
- `retry_after` - Seconds to wait before retrying (optional, for 429 errors)
- `trace_id` - Unique identifier for this error (for support/debugging)

---

## Error Codes

### Authentication Errors (401)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or expired token | Missing or invalid JWT token |
| `TOKEN_EXPIRED` | 401 | Token has expired | JWT access token expired (> 1 hour) |
| `INVALID_GOOGLE_TOKEN` | 401 | Invalid Google OAuth token | Google token verification failed |
| `REFRESH_TOKEN_INVALID` | 401 | Invalid refresh token | Refresh token expired or invalid |

**Example:**
```json
{
  "error_code": "TOKEN_EXPIRED",
  "message": "Token has expired. Please refresh your token.",
  "details": {
    "expired_at": "2026-01-15T10:00:00Z"
  },
  "trace_id": "abc123-def456"
}
```

---

### Authorization Errors (403)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `FORBIDDEN` | 403 | Insufficient permissions | User lacks required role |
| `DOMAIN_NOT_ALLOWED` | 403 | Email domain not allowed | Email not from @your-domain.com domain |
| `NOT_PROJECT_OWNER` | 403 | Not authorized to access this project | User doesn't own project |
| `ADMIN_REQUIRED` | 403 | Admin access required | Operation requires admin role |

**Example:**
```json
{
  "error_code": "ADMIN_REQUIRED",
  "message": "Admin access required for this operation",
  "details": {
    "required_role": "admin",
    "user_role": "user"
  },
  "trace_id": "abc123-def456"
}
```

---

### Not Found Errors (404)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `PROJECT_NOT_FOUND` | 404 | Project not found | Project ID doesn't exist |
| `JOB_NOT_FOUND` | 404 | Job not found | Job ID doesn't exist |
| `PROMPT_NOT_FOUND` | 404 | Prompt not found | Prompt ID doesn't exist |
| `USER_NOT_FOUND` | 404 | User not found | User ID doesn't exist |

**Example:**
```json
{
  "error_code": "PROJECT_NOT_FOUND",
  "message": "Project with ID '770e8400-e29b-41d4-a716-446655440002' not found",
  "details": {
    "project_id": "770e8400-e29b-41d4-a716-446655440002"
  },
  "trace_id": "abc123-def456"
}
```

---

### Validation Errors (400, 422)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed | Pydantic validation errors |
| `INVALID_FILE_TYPE` | 400 | Invalid file type | File is not a PDF |
| `FILE_TOO_LARGE` | 400 | File too large | File exceeds 50MB limit |
| `MALFORMED_PDF` | 400 | Malformed or encrypted PDF | PDF is corrupted or encrypted |
| `INVALID_STATUS_TRANSITION` | 400 | Invalid workflow status transition | Cannot transition from current status |

**Validation Error Example:**
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "starting_price",
        "message": "Must be a positive number",
        "value": -1000000
      },
      {
        "field": "email",
        "message": "Invalid email format",
        "value": "invalid-email"
      }
    ]
  },
  "trace_id": "abc123-def456"
}
```

---

### Rate Limit Errors (429)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded | Too many requests in time window |
| `UPLOAD_LIMIT_EXCEEDED` | 429 | Upload limit exceeded | Too many uploads in time window |

**Example:**
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. You can make 100 requests per hour.",
  "details": {
    "limit": 100,
    "window_seconds": 3600,
    "requests_made": 101
  },
  "retry_after": 3600,
  "trace_id": "abc123-def456"
}
```

---

### External Service Errors (503, 429)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `ANTHROPIC_API_ERROR` | 503 | Anthropic API error | Anthropic API request failed |
| `ANTHROPIC_QUOTA_EXCEEDED` | 429 | Anthropic quota exceeded | Anthropic API quota/rate limit |
| `SHEETS_API_ERROR` | 503 | Google Sheets API error | Sheets API request failed |
| `STORAGE_ERROR` | 503 | Cloud Storage error | GCS operation failed |
| `DATABASE_ERROR` | 503 | Database error | Database connection/query failed |

**Example:**
```json
{
  "error_code": "ANTHROPIC_QUOTA_EXCEEDED",
  "message": "Anthropic API quota exceeded. Please try again later.",
  "details": {
    "service": "anthropic",
    "quota_type": "tokens_per_minute"
  },
  "retry_after": 60,
  "trace_id": "abc123-def456"
}
```

---

### Internal Server Errors (500)

| Error Code | HTTP Status | Message | Description |
|------------|-------------|---------|-------------|
| `INTERNAL_SERVER_ERROR` | 500 | Internal server error | Unexpected server error |
| `PROCESSING_ERROR` | 500 | Processing error | Job processing failed |
| `UNKNOWN_ERROR` | 500 | Unknown error occurred | Unhandled exception |

**Example:**
```json
{
  "error_code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred. Our team has been notified.",
  "details": {},
  "trace_id": "abc123-def456"
}
```

---

## Exception Hierarchy

### Custom Exceptions

```python
# app/exceptions.py

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Authentication failed."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=401,
            details=details
        )


class AuthorizationError(AppException):
    """User not authorized."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            error_code="FORBIDDEN",
            message=message,
            status_code=403,
            details=details
        )


class NotFoundError(AppException):
    """Resource not found."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            error_code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource.capitalize()} with ID '{resource_id}' not found",
            status_code=404,
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(AppException):
    """Request validation failed."""
    def __init__(self, errors: list):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            status_code=422,
            details={"errors": errors}
        )


class RateLimitError(AppException):
    """Rate limit exceeded."""
    def __init__(self, limit: int, window_seconds: int):
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message=f"Rate limit exceeded. You can make {limit} requests per {window_seconds} seconds.",
            status_code=429,
            details={
                "limit": limit,
                "window_seconds": window_seconds
            }
        )


class ExternalServiceError(AppException):
    """External service error."""
    def __init__(self, service: str, message: str, retry_after: int = None):
        super().__init__(
            error_code=f"{service.upper()}_API_ERROR",
            message=f"{service} API error: {message}",
            status_code=503,
            details={"service": service}
        )
        self.retry_after = retry_after
```

---

## Error Handling Patterns

### API Layer Error Handler

```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uuid
import logging

app = FastAPI()
logger = logging.getLogger(__name__)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    trace_id = str(uuid.uuid4())

    # Log error with context
    logger.error(
        f"[{trace_id}] {exc.error_code}: {exc.message}",
        extra={
            "trace_id": trace_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None),
            "details": exc.details
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "trace_id": trace_id
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    trace_id = str(uuid.uuid4())

    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"[{trace_id}] Validation error: {len(errors)} fields",
        extra={
            "trace_id": trace_id,
            "path": request.url.path,
            "errors": errors
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
            "trace_id": trace_id
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    trace_id = str(uuid.uuid4())

    # Log full exception with stack trace
    logger.exception(
        f"[{trace_id}] Unexpected error: {str(exc)}",
        extra={
            "trace_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "user_id": getattr(request.state, "user_id", None)
        }
    )

    # Send to Sentry
    sentry_sdk.capture_exception(exc)

    # Return generic error to user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Our team has been notified.",
            "details": {},
            "trace_id": trace_id
        }
    )
```

---

### Service Layer Error Handling

```python
# app/services/project_service.py

class ProjectService:
    async def get_project(self, project_id: str) -> Project:
        """Get project by ID."""
        project = await self.db.projects.find_one({"id": project_id})

        if not project:
            raise NotFoundError("project", project_id)

        return project

    async def update_project(
        self,
        project_id: str,
        updates: dict,
        user: User
    ) -> Project:
        """Update project with authorization check."""
        project = await self.get_project(project_id)

        # Check authorization
        if project.created_by != user.id and user.role != "admin":
            raise AuthorizationError(
                "You are not authorized to update this project",
                details={
                    "project_id": project_id,
                    "user_id": user.id,
                    "owner_id": project.created_by
                }
            )

        # Validate updates
        if "starting_price" in updates and updates["starting_price"] < 0:
            raise ValidationError([{
                "field": "starting_price",
                "message": "Must be a positive number",
                "value": updates["starting_price"]
            }])

        # Perform update
        try:
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": updates}
            )
        except Exception as e:
            logger.exception(f"Database error updating project {project_id}")
            raise ExternalServiceError(
                "database",
                f"Failed to update project: {str(e)}"
            )

        return await self.get_project(project_id)
```

---

### External Service Error Handling

```python
# app/services/anthropic_service.py

class AnthropicService:
    async def extract_data_from_pdf(
        self,
        pdf_pages: List[str],
        prompt: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Extract data with automatic retry."""
        for attempt in range(max_retries):
            try:
                response = await self.client.messages.create(
                    model="claude-sonnet-4-5-20241022",
                    max_tokens=4096,
                    system=prompt,
                    messages=[
                        {"role": "user", "content": "\n\n".join(pdf_pages)}
                    ]
                )

                return json.loads(response.content[0].text)

            except anthropic.RateLimitError as e:
                # Rate limit - wait and retry
                wait_time = 2 ** attempt * 10  # Exponential backoff
                logger.warning(
                    f"Anthropic rate limit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise ExternalServiceError(
                        "anthropic",
                        "Rate limit exceeded",
                        retry_after=60
                    )

            except anthropic.APIError as e:
                # API error - retry
                logger.error(f"Anthropic API error: {str(e)}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt * 5)
                else:
                    raise ExternalServiceError(
                        "anthropic",
                        f"API request failed: {str(e)}"
                    )

            except Exception as e:
                # Unexpected error - don't retry
                logger.exception("Unexpected error calling Anthropic")
                raise ExternalServiceError(
                    "anthropic",
                    f"Unexpected error: {str(e)}"
                )
```

---

## Retry Strategies

### Exponential Backoff

```python
# app/utils/retry.py

import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)
T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_wait: int = 1,
    backoff_factor: int = 2,
    max_wait: int = 60,
    retry_on: tuple = (Exception,)
) -> T:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        backoff_factor: Multiplier for wait time
        max_wait: Maximum wait time in seconds
        retry_on: Tuple of exceptions to retry on

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func()
        except retry_on as e:
            last_exception = e

            if attempt < max_retries - 1:
                wait_time = min(initial_wait * (backoff_factor ** attempt), max_wait)
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries} failed, "
                    f"waiting {wait_time}s before retry. Error: {str(e)}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"All {max_retries} retry attempts failed. Last error: {str(e)}"
                )

    raise last_exception


def retry(
    max_retries: int = 3,
    initial_wait: int = 1,
    backoff_factor: int = 2,
    retry_on: tuple = (Exception,)
):
    """Decorator for retrying async functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                initial_wait=initial_wait,
                backoff_factor=backoff_factor,
                retry_on=retry_on
            )
        return wrapper
    return decorator


# Usage example
@retry(max_retries=3, initial_wait=2, retry_on=(anthropic.RateLimitError, anthropic.APIError))
async def call_anthropic_api(prompt: str) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-5-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

---

## Logging and Monitoring

### Structured Logging

```python
# app/config/logging.py

import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

# Set JSON formatter for production
if settings.ENVIRONMENT == "production":
    for handler in logging.root.handlers:
        handler.setFormatter(JSONFormatter())
```

### Sentry Integration

```python
# app/main.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
    ],
    before_send=lambda event, hint: _filter_sensitive_data(event, hint)
)


def _filter_sensitive_data(event, hint):
    """Remove sensitive data from Sentry events."""
    # Remove Authorization headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        if "Authorization" in headers:
            headers["Authorization"] = "[FILTERED]"

    # Remove password fields
    if "extra" in event:
        for key in list(event["extra"].keys()):
            if "password" in key.lower() or "token" in key.lower():
                event["extra"][key] = "[FILTERED]"

    return event
```

---

## Related Documentation

- [API Design](../01-architecture/API_DESIGN.md) - API error responses
- [Service Layer](./SERVICE_LAYER.md) - Service error handling
- [API Endpoints](./API_ENDPOINTS.md) - Endpoint-specific errors

---

**Last Updated:** 2026-01-15
