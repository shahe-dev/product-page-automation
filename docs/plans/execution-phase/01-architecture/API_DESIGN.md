# API Design

**Last Updated:** 2026-01-15
**Related Documents:**
- [System Architecture](./SYSTEM_ARCHITECTURE.md)
- [Data Flow](./DATA_FLOW.md)
- [Database Schema](./DATABASE_SCHEMA.md)
- [API Endpoints](../04-backend/API_ENDPOINTS.md)

---

## Table of Contents

1. [Overview](#overview)
2. [API Principles](#api-principles)
3. [Base URL and Versioning](#base-url-and-versioning)
4. [Authentication](#authentication)
5. [Request/Response Format](#requestresponse-format)
6. [Core Endpoints](#core-endpoints)
7. [Pagination and Filtering](#pagination-and-filtering)
8. [Rate Limiting](#rate-limiting)
9. [Error Responses](#error-responses)
10. [Webhook Support](#webhook-support)
11. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 API is a RESTful API built with FastAPI that provides programmatic access to all system functionality. The API follows industry best practices for REST design, including resource-based URLs, standard HTTP methods, and JSON request/response payloads.

**Key Features:**
- **RESTful Design** - Resource-oriented endpoints with standard HTTP verbs
- **JSON Payloads** - All requests and responses use JSON
- **JWT Authentication** - Secure token-based authentication
- **OpenAPI Spec** - Auto-generated documentation at `/docs`
- **Rate Limiting** - Per-user quotas to prevent abuse
- **CORS Support** - Cross-origin requests for frontend integration
- **Async Processing** - Background jobs for long-running tasks

---

## API Principles

### 1. RESTful Resource Design

Endpoints are organized around resources (nouns), not actions (verbs):

**Good:**
```
GET    /api/projects          # List projects
POST   /api/projects          # Create project
GET    /api/projects/{id}     # Get project
PUT    /api/projects/{id}     # Update project
DELETE /api/projects/{id}     # Delete project
```

**Bad:**
```
POST /api/getProjects
POST /api/createProject
POST /api/updateProject
POST /api/deleteProject
```

### 2. HTTP Methods

| Method | Purpose | Idempotent | Safe |
|--------|---------|------------|------|
| GET | Retrieve resource(s) | Yes | Yes |
| POST | Create resource | No | No |
| PUT | Update/replace resource | Yes | No |
| PATCH | Partial update | No | No |
| DELETE | Delete resource | Yes | No |

### 3. Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 OK | Success | GET, PUT, PATCH successful |
| 201 Created | Resource created | POST successful |
| 204 No Content | Success, no body | DELETE successful |
| 400 Bad Request | Invalid input | Validation errors |
| 401 Unauthorized | Missing/invalid auth | No valid token |
| 403 Forbidden | Insufficient permissions | User lacks access |
| 404 Not Found | Resource doesn't exist | Invalid ID |
| 409 Conflict | Resource conflict | Duplicate entry |
| 422 Unprocessable Entity | Semantic errors | Business logic failure |
| 429 Too Many Requests | Rate limit exceeded | Quota reached |
| 500 Internal Server Error | Server error | Unexpected failures |
| 503 Service Unavailable | Temporary outage | Maintenance mode |

### 4. Consistent Naming

- **URLs:** lowercase with hyphens (`/api/floor-plans`, not `/api/FloorPlans`)
- **JSON keys:** camelCase (`firstName`, not `first_name`)
- **Collections:** plural (`/api/projects`, not `/api/project`)
- **Resources:** singular in path params (`/api/projects/{id}`, not `/api/projects/{ids}`)

### 5. Versioning Strategy

API version included in base URL:
```
https://api.pdp-automation.com/v1/projects
```

Version changes when:
- Breaking changes to response format
- Removal of endpoints or fields
- Changes to authentication mechanism

Non-breaking changes (additive fields, new endpoints) do NOT require version bump.

---

## Base URL and Versioning

### Production
```
Base URL: https://api.pdp-automation.com/v1
Example:  https://api.pdp-automation.com/v1/projects
```

### Development
```
Base URL: https://pdp-automation-api-dev.run.app/v1
Example:  https://pdp-automation-api-dev.run.app/v1/projects
```

### Local Development
```
Base URL: http://localhost:8000/v1
Example:  http://localhost:8000/v1/projects
```

---

## Authentication

### OAuth 2.0 with Google

The API uses **Google OAuth 2.0** for authentication with JWT tokens for subsequent requests.

#### 1. Authenticate with Google

**Frontend Flow:**
```
User clicks "Sign in with Google"
  ↓
Redirect to Google OAuth consent screen
  ↓
User approves access
  ↓
Google redirects back with authorization code
  ↓
Frontend exchanges code for Google token
  ↓
Frontend sends Google token to API
```

**Endpoint:**
```http
POST /api/auth/google
Content-Type: application/json

{
  "token": "google_oauth_token_here"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def50200a1b2c3d4e5f6...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@your-domain.com",
    "name": "John Doe",
    "picture_url": "https://lh3.googleusercontent.com/...",
    "role": "user"
  }
}
```

**Errors:**
- `401 Unauthorized` - Invalid Google token
- `403 Forbidden` - Email domain not allowed (must be @your-domain.com)

#### 2. Include Token in Requests

All subsequent API requests must include the JWT token in the `Authorization` header:

```http
GET /api/projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3. Token Expiry and Refresh

**Access Token:** Expires after 1 hour
**Refresh Token:** Expires after 7 days

**Refresh Endpoint:**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "def50200a1b2c3d4e5f6..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "new_access_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. Logout

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

**Response (204 No Content)**

---

## Request/Response Format

### Request Format

**Headers:**
```http
Content-Type: application/json
Authorization: Bearer <token>
Accept: application/json
```

**Body (JSON):**
```json
{
  "name": "Marina Bay Residences",
  "developer": "Emaar Properties",
  "starting_price": 1500000
}
```

### Response Format

**Success Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Marina Bay Residences",
  "developer": "Emaar Properties",
  "starting_price": 1500000,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

**Error Response:**
```json
{
  "error_code": "PROJECT_NOT_FOUND",
  "message": "Project with ID '550e8400...' not found",
  "details": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "trace_id": "abc123-def456"
}
```

**Pagination Response:**
```json
{
  "items": [
    {
      "id": "550e8400...",
      "name": "Marina Bay Residences"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3,
  "has_next": true,
  "has_prev": false
}
```

---

## Core Endpoints

### Authentication & Users

#### POST /api/auth/google
Authenticate with Google OAuth token.

**Request:**
```json
{
  "token": "google_oauth_token"
}
```

**Response (200):**
```json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@your-domain.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

#### GET /api/auth/me
Get current authenticated user.

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@your-domain.com",
  "name": "John Doe",
  "picture_url": "https://...",
  "role": "user",
  "created_at": "2026-01-01T00:00:00Z",
  "last_login_at": "2026-01-15T10:00:00Z"
}
```

#### POST /api/auth/logout
Invalidate current session.

**Response (204 No Content)**

---

### File Upload & Jobs

#### POST /api/upload
Upload PDF and create processing job.

**Request:**
```http
POST /api/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Form Data:
  file: <pdf_file>
  template_type: "opr"  // aggregators, opr, mpp, adop, adre, commercial
  template_id: "550e8400-e29b-41d4-a716-446655440000"
```

**Response (200):**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "created_at": "2026-01-15T10:00:00Z",
  "estimated_completion": "2026-01-15T10:05:00Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid file type, file too large (>50MB)
- `413 Payload Too Large` - File exceeds size limit
- `429 Too Many Requests` - Rate limit exceeded

#### GET /api/jobs/{job_id}
Get job status and result.

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "steps": [
    {
      "id": "upload",
      "label": "Upload PDF",
      "status": "completed",
      "started_at": "2026-01-15T10:00:00Z",
      "completed_at": "2026-01-15T10:00:10Z"
    },
    {
      "id": "extract_text",
      "label": "Extract text",
      "status": "completed",
      "started_at": "2026-01-15T10:00:10Z",
      "completed_at": "2026-01-15T10:02:30Z"
    },
    {
      "id": "extract_images",
      "label": "Extract images",
      "status": "completed",
      "started_at": "2026-01-15T10:00:10Z",
      "completed_at": "2026-01-15T10:03:00Z"
    }
  ],
  "result": {
    "project_id": "770e8400-e29b-41d4-a716-446655440002",
    "sheet_url": "https://docs.google.com/spreadsheets/d/...",
    "zip_url": "https://storage.googleapis.com/pdp-automation-assets-dev/...",
    "image_count": 45,
    "floor_plan_count": 8
  },
  "error_message": null,
  "created_at": "2026-01-15T10:00:00Z",
  "completed_at": "2026-01-15T10:04:30Z"
}
```

**Errors:**
- `404 Not Found` - Job ID doesn't exist
- `403 Forbidden` - Not authorized to view this job

#### GET /api/jobs
List user's jobs.

**Query Parameters:**
- `page` (int, default: 1)
- `limit` (int, default: 50, max: 100)
- `status` (string: "pending" | "processing" | "completed" | "failed")
- `date_from` (ISO 8601 date)
- `date_to` (ISO 8601 date)

**Response (200):**
```json
{
  "items": [
    {
      "id": "660e8400...",
      "status": "completed",
      "progress": 100,
      "created_at": "2026-01-15T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1
}
```

---

### Projects

#### GET /api/projects
List projects with filtering and pagination.

**Query Parameters:**
- `page` (int, default: 1)
- `limit` (int, default: 50, max: 100)
- `search` (string) - Full-text search on name, developer, location
- `developer` (string) - Filter by developer
- `emirate` (string) - Filter by emirate
- `status` (string) - Filter by workflow_status
- `price_min` (float) - Minimum starting price
- `price_max` (float) - Maximum starting price
- `date_from` (ISO 8601 date) - Created after this date
- `date_to` (ISO 8601 date) - Created before this date
- `sort` (string) - Sort field (prefix with `-` for descending)
  - Examples: `created_at`, `-created_at`, `name`, `-starting_price`

**Response (200):**
```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Marina Bay Residences",
      "developer": "Emaar Properties",
      "location": "Dubai Marina",
      "emirate": "Dubai",
      "starting_price": 1500000,
      "workflow_status": "published",
      "created_at": "2026-01-15T10:00:00Z",
      "image_count": 45,
      "floor_plan_count": 8
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3,
  "has_next": true,
  "has_prev": false
}
```

#### GET /api/projects/{id}
Get project detail with all related data.

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Marina Bay Residences",
  "developer": "Emaar Properties",
  "location": "Dubai Marina",
  "emirate": "Dubai",
  "starting_price": 1500000,
  "price_per_sqft": 2000,
  "handover_date": "2027-12-31",
  "payment_plan": "60/40",
  "description": "Luxury waterfront apartments...",
  "property_types": ["apartment", "penthouse"],
  "unit_sizes": [
    {
      "type": "1BR",
      "sqft_min": 650,
      "sqft_max": 750
    }
  ],
  "amenities": ["Pool", "Gym", "Parking"],
  "features": ["Sea View", "Balcony", "Smart Home"],
  "total_units": 250,
  "floors": 30,
  "buildings": 2,
  "custom_fields": {
    "sales_contact": "John Smith",
    "priority": "high"
  },
  "images": [
    {
      "id": "880e8400...",
      "category": "exterior",
      "image_url": "https://storage.googleapis.com/.../exterior_001.jpg",
      "thumbnail_url": "https://storage.googleapis.com/.../exterior_001_thumb.jpg",
      "width": 1920,
      "height": 1080
    }
  ],
  "floor_plans": [
    {
      "id": "990e8400...",
      "unit_type": "1BR",
      "bedrooms": 1,
      "bathrooms": 1,
      "total_sqft": 750,
      "balcony_sqft": 100,
      "builtup_sqft": 650,
      "image_url": "https://storage.googleapis.com/.../floor_plan_1br.jpg"
    }
  ],
  "original_pdf_url": "https://storage.googleapis.com/.../original.pdf",
  "processed_zip_url": "https://storage.googleapis.com/.../images.zip",
  "sheet_url": "https://docs.google.com/spreadsheets/d/...",
  "workflow_status": "published",
  "published_url": "https://opr.com/properties/marina-bay-residences",
  "created_by": {
    "id": "user-uuid",
    "name": "John Doe",
    "email": "john@your-domain.com"
  },
  "created_at": "2026-01-15T10:00:00Z",
  "last_modified_by": {
    "id": "user-uuid-2",
    "name": "Jane Smith",
    "email": "jane@your-domain.com"
  },
  "last_modified_at": "2026-01-15T11:30:00Z"
}
```

**Errors:**
- `404 Not Found` - Project ID doesn't exist

#### PUT /api/projects/{id}
Update project fields.

**Request:**
```json
{
  "name": "Marina Bay Residences - Updated",
  "starting_price": 1600000,
  "custom_fields": {
    "priority": "urgent"
  }
}
```

**Response (200):**
```json
{
  "id": "770e8400...",
  "name": "Marina Bay Residences - Updated",
  "starting_price": 1600000,
  ...
}
```

**Errors:**
- `404 Not Found` - Project doesn't exist
- `403 Forbidden` - User not authorized to edit
- `400 Bad Request` - Invalid field values

#### DELETE /api/projects/{id}
Delete project (admin only).

**Response (204 No Content)**

**Errors:**
- `404 Not Found` - Project doesn't exist
- `403 Forbidden` - User is not admin

#### POST /api/projects/{id}/fields
Add custom field to project.

**Request:**
```json
{
  "key": "sales_contact",
  "value": "John Smith"
}
```

**Response (200):**
```json
{
  "id": "770e8400...",
  "custom_fields": {
    "sales_contact": "John Smith",
    "priority": "high"
  }
}
```

#### GET /api/projects/{id}/history
Get project revision history.

**Response (200):**
```json
{
  "items": [
    {
      "id": "rev-uuid-1",
      "field": "starting_price",
      "old_value": "1500000",
      "new_value": "1600000",
      "changed_by": {
        "id": "user-uuid",
        "name": "Jane Smith"
      },
      "changed_at": "2026-01-15T11:30:00Z"
    }
  ],
  "total": 15
}
```

#### POST /api/projects/export
Export selected projects.

**Request:**
```json
{
  "project_ids": ["770e8400...", "880e8400..."],
  "format": "csv",
  "fields": ["name", "developer", "location", "starting_price"]
}
```

**Response (200):**
```json
{
  "export_url": "https://storage.googleapis.com/.../export_2026-01-15.csv",
  "expires_at": "2026-01-16T10:00:00Z"
}
```

---

### Prompts

#### GET /api/prompts
List prompts with filtering.

**Query Parameters:**
- `template_type` (string: "aggregators" | "opr" | "mpp" | "adop" | "adre" | "commercial")
- `content_variant` (string: "standard" | "luxury")
- `search` (string) - Search prompt names
- `is_active` (boolean) - Filter by active status

**Response (200):**
```json
{
  "items": [
    {
      "id": "prompt-uuid-1",
      "name": "Meta Description",
      "template_type": "opr",
      "content_variant": "standard",
      "version": 3,
      "is_active": true,
      "character_limit": 160,
      "updated_at": "2026-01-15T10:00:00Z",
      "updated_by": {
        "name": "Admin User"
      }
    }
  ]
}
```

#### GET /api/prompts/{id}
Get prompt detail.

**Response (200):**
```json
{
  "id": "prompt-uuid-1",
  "name": "Meta Description",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Create a compelling meta description...",
  "character_limit": 160,
  "version": 3,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "updated_by": {
    "id": "user-uuid",
    "name": "Admin User"
  }
}
```

#### POST /api/prompts
Create new prompt.

**Request:**
```json
{
  "name": "Meta Title",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Create a compelling meta title...",
  "character_limit": 60
}
```

**Response (201 Created):**
```json
{
  "id": "prompt-uuid-2",
  "name": "Meta Title",
  "version": 1,
  ...
}
```

#### PUT /api/prompts/{id}
Update prompt (creates new version).

**Request:**
```json
{
  "content": "Updated prompt content...",
  "change_reason": "Improved clarity"
}
```

**Response (200):**
```json
{
  "id": "prompt-uuid-1",
  "version": 4,
  "content": "Updated prompt content...",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

#### GET /api/prompts/{id}/versions
Get prompt version history.

**Response (200):**
```json
{
  "items": [
    {
      "version": 3,
      "content": "Previous prompt content...",
      "change_reason": "Fixed typo",
      "created_at": "2026-01-10T10:00:00Z",
      "created_by": {
        "name": "Admin User"
      }
    }
  ]
}
```

---

### QA

#### POST /api/qa/compare
Run QA comparison.

**Request:**
```json
{
  "project_id": "770e8400...",
  "checkpoint_type": "generation",
  "input_content": {...},
  "comparison_target": {...}
}
```

**Response (200):**
```json
{
  "id": "qa-uuid-1",
  "status": "passed",
  "matches": 45,
  "differences": 2,
  "missing": 1,
  "extra": 0,
  "result": {
    "differences": [
      {
        "field": "starting_price",
        "expected": "1500000",
        "actual": "1600000",
        "severity": "high"
      }
    ],
    "missing": ["property_tax"],
    "extra": []
  },
  "performed_at": "2026-01-15T10:00:00Z"
}
```

#### GET /api/qa/history
Get QA history for user or project.

**Query Parameters:**
- `project_id` (string, optional)
- `checkpoint_type` (string, optional)
- `page` (int)
- `limit` (int)

**Response (200):**
```json
{
  "items": [
    {
      "id": "qa-uuid-1",
      "project_id": "770e8400...",
      "checkpoint_type": "generation",
      "status": "passed",
      "performed_at": "2026-01-15T10:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "pages": 1
}
```

---

### Workflow

#### GET /api/workflow/items
Get Kanban board items.

**Query Parameters:**
- `status` (string) - Filter by workflow_status

**Response (200):**
```json
{
  "items": [
    {
      "id": "770e8400...",
      "name": "Marina Bay Residences",
      "workflow_status": "pending_approval",
      "assigned_to": {
        "id": "user-uuid",
        "name": "Jane Smith"
      },
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

#### PUT /api/workflow/items/{id}
Update workflow item (move column, assign user).

**Request:**
```json
{
  "workflow_status": "approved",
  "assigned_to": "user-uuid"
}
```

**Response (200):**
```json
{
  "id": "770e8400...",
  "workflow_status": "approved",
  "assigned_to": {
    "id": "user-uuid",
    "name": "Jane Smith"
  }
}
```

---

### Templates

#### GET /api/templates
List website templates.

**Response (200):**
```json
{
  "items": [
    {
      "id": "template-uuid-1",
      "name": "OPR Standard Template",
      "template_type": "opr",
      "content_variant": "standard",
      "sheet_template_url": "https://docs.google.com/spreadsheets/d/...",
      "field_mappings": {
        "meta_title": "B2",
        "meta_description": "B3"
      }
    }
  ]
}
```

---

### Health

#### GET /health
Basic health check.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:00:00Z"
}
```

#### GET /readiness
Readiness check (verifies external dependencies).

**Response (200):**
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "storage": "ok",
    "anthropic_api": "ok"
  },
  "timestamp": "2026-01-15T10:00:00Z"
}
```

---

## Pagination and Filtering

### Pagination

All list endpoints support pagination with consistent query parameters:

**Query Parameters:**
- `page` (int, default: 1) - Page number (1-indexed)
- `limit` (int, default: 50, max: 100) - Items per page

**Response Structure:**
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "limit": 50,
  "pages": 3,
  "has_next": true,
  "has_prev": true
}
```

### Filtering

Common filter parameters across endpoints:

- `search` - Full-text search (uses PostgreSQL `tsvector`)
- `date_from` / `date_to` - Date range (ISO 8601 format)
- `sort` - Sort field (prefix with `-` for descending)

**Example:**
```
GET /api/projects?search=marina&date_from=2026-01-01&sort=-created_at&page=1&limit=25
```

---

## Rate Limiting

### Per-User Quotas

| Role | Requests per Hour | Concurrent Jobs |
|------|-------------------|-----------------|
| User | 100 | 5 |
| Admin | 500 | 20 |

### Rate Limit Headers

Response headers indicate current rate limit status:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642240800
```

### Rate Limit Exceeded Response

**Status:** 429 Too Many Requests

```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 3600
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "error_code": "ERROR_CODE_HERE",
  "message": "Human-readable error message",
  "details": {
    "field": "additional context"
  },
  "trace_id": "abc123-def456"
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid auth token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `PROJECT_NOT_FOUND` | 404 | Project ID doesn't exist |
| `JOB_NOT_FOUND` | 404 | Job ID doesn't exist |
| `UPLOAD_FILE_TOO_LARGE` | 400 | File exceeds 50MB limit |
| `UPLOAD_INVALID_FILE_TYPE` | 400 | Not a PDF file |
| `UPLOAD_MALFORMED_PDF` | 400 | PDF corrupted or encrypted |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `ANTHROPIC_QUOTA_EXCEEDED` | 429 | Anthropic API quota exceeded |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

### Validation Errors

**Status:** 422 Unprocessable Entity

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "starting_price",
        "message": "Must be a positive number"
      },
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

---

## Webhook Support

### Planned (Future Release)

The API will support webhooks for async event notifications:

**Event Types:**
- `job.completed` - Processing job finished
- `job.failed` - Processing job failed
- `project.approved` - Project approved by reviewer
- `project.published` - Project marked as published

**Webhook Payload:**
```json
{
  "event": "job.completed",
  "timestamp": "2026-01-15T10:00:00Z",
  "data": {
    "job_id": "660e8400...",
    "project_id": "770e8400...",
    "status": "completed"
  }
}
```

---

## Related Documentation

- [System Architecture](./SYSTEM_ARCHITECTURE.md) - Overall system design
- [Data Flow](./DATA_FLOW.md) - How data moves through the system
- [API Endpoints](../04-backend/API_ENDPOINTS.md) - Detailed endpoint documentation
- [Error Handling](../04-backend/ERROR_HANDLING.md) - Error patterns and strategies

---

**Last Updated:** 2026-01-15
