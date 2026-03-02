# API Endpoints

**Last Updated:** 2026-01-15
**Related Documents:**
- [API Design](../01-architecture/API_DESIGN.md)
- [Service Layer](./SERVICE_LAYER.md)
- [Error Handling](./ERROR_HANDLING.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Endpoints](#authentication-endpoints)
3. [Upload and Jobs Endpoints](#upload-and-jobs-endpoints)
4. [Projects Endpoints](#projects-endpoints)
5. [Prompts Endpoints](#prompts-endpoints)
6. [QA Endpoints](#qa-endpoints)
7. [Workflow Endpoints](#workflow-endpoints)
8. [Templates Endpoints](#templates-endpoints)
9. [Health Endpoints](#health-endpoints)
10. [Related Documentation](#related-documentation)

---

## Overview

This document provides detailed specifications for all API endpoints including request/response formats, authentication requirements, and error cases.

**Base URL:** `https://pdp-automation-api-dev.run.app/v1`

**Authentication:** All endpoints except `/health` and `/readiness` require JWT token in `Authorization: Bearer <token>` header.

---

## Authentication Endpoints

### POST /api/auth/google

Authenticate with Google OAuth token and receive JWT tokens.

**Request:**
```http
POST /api/auth/google
Content-Type: application/json

{
  "token": "ya29.a0AfH6SMBx..."
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
    "role": "user",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

**Errors:**
- `401 Unauthorized` - Invalid Google token
- `403 Forbidden` - Email domain not allowed (@your-domain.com only)

---

### GET /api/auth/me

Get current authenticated user profile.

**Request:**
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@your-domain.com",
  "name": "John Doe",
  "picture_url": "https://lh3.googleusercontent.com/...",
  "role": "user",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "last_login_at": "2026-01-15T10:00:00Z"
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid token

---

### POST /api/auth/refresh

Refresh access token using refresh token.

**Request:**
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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors:**
- `401 Unauthorized` - Invalid or expired refresh token

---

### POST /api/auth/logout

Logout and invalidate session.

**Request:**
```http
POST /api/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (204 No Content)**

---

## Upload and Jobs Endpoints

### POST /api/upload

Upload PDF and create processing job.

**Request:**
```http
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

Form Data:
  file: <pdf_file>
  template_type: "opr"  // aggregators, opr, mpp, adop, adre, commercial
  template_id: "550e8400-e29b-41d4-a716-446655440000"
```

**Response (200 OK):**
```json
{
  "job_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "created_at": "2026-01-15T10:00:00Z",
  "estimated_completion": "2026-01-15T10:05:00Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid file type, file too large (>50MB), malformed PDF
- `413 Payload Too Large` - File exceeds size limit
- `429 Too Many Requests` - Rate limit exceeded (100/hour for user, 500/hour for admin)

---

### GET /api/jobs/{job_id}

Get job status and result.

**Request:**
```http
GET /api/jobs/660e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <token>
```

**Response (200 OK):**
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
    },
    {
      "id": "classify_images",
      "label": "Classify images",
      "status": "completed",
      "started_at": "2026-01-15T10:03:00Z",
      "completed_at": "2026-01-15T10:03:45Z"
    },
    {
      "id": "generate_content",
      "label": "Generate content",
      "status": "completed",
      "started_at": "2026-01-15T10:03:45Z",
      "completed_at": "2026-01-15T10:04:15Z"
    },
    {
      "id": "push_to_sheets",
      "label": "Push to Google Sheets",
      "status": "completed",
      "started_at": "2026-01-15T10:04:15Z",
      "completed_at": "2026-01-15T10:04:30Z"
    }
  ],
  "result": {
    "project_id": "770e8400-e29b-41d4-a716-446655440002",
    "sheet_url": "https://docs.google.com/spreadsheets/d/ABC123.../edit",
    "zip_url": "https://storage.googleapis.com/pdp-automation-assets-dev/outputs/660e8400.../images.zip",
    "image_count": 45,
    "floor_plan_count": 8
  },
  "error_message": null,
  "created_at": "2026-01-15T10:00:00Z",
  "started_at": "2026-01-15T10:00:00Z",
  "completed_at": "2026-01-15T10:04:30Z"
}
```

**Errors:**
- `404 Not Found` - Job ID doesn't exist
- `403 Forbidden` - Not authorized to view this job

---

### GET /api/jobs

List user's jobs with pagination and filtering.

**Request:**
```http
GET /api/jobs?page=1&limit=50&status=completed
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (int, default: 1)
- `limit` (int, default: 50, max: 100)
- `status` (string: "pending" | "processing" | "completed" | "failed" | "cancelled")
- `date_from` (ISO 8601 date)
- `date_to` (ISO 8601 date)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "completed",
      "progress": 100,
      "current_step": "Complete",
      "created_at": "2026-01-15T10:00:00Z",
      "completed_at": "2026-01-15T10:04:30Z"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 50,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

---

### POST /api/jobs/{job_id}/cancel

Cancel running job.

**Request:**
```http
POST /api/jobs/660e8400-e29b-41d4-a716-446655440001/cancel
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Errors:**
- `404 Not Found` - Job doesn't exist
- `400 Bad Request` - Job already completed or cancelled

---

## Projects Endpoints

### GET /api/projects

List projects with filtering, pagination, and sorting.

**Request:**
```http
GET /api/projects?search=marina&developer=Emaar&page=1&limit=50&sort=-created_at
Authorization: Bearer <token>
```

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
  - Options: `created_at`, `-created_at`, `name`, `-name`, `starting_price`, `-starting_price`

**Response (200 OK):**
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
      "created_by": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Doe"
      },
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

---

### GET /api/projects/{id}

Get project detail with all related data.

**Request:**
```http
GET /api/projects/770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer <token>
```

**Response (200 OK):**
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
  "description": "Luxury waterfront apartments in the heart of Dubai Marina...",
  "property_types": ["apartment", "penthouse"],
  "unit_sizes": [
    {
      "type": "1BR",
      "sqft_min": 650,
      "sqft_max": 750
    },
    {
      "type": "2BR",
      "sqft_min": 1100,
      "sqft_max": 1300
    }
  ],
  "amenities": ["Swimming Pool", "Gymnasium", "Parking", "Security", "Concierge"],
  "features": ["Sea View", "Balcony", "Smart Home", "Built-in Wardrobes"],
  "total_units": 250,
  "floors": 30,
  "buildings": 2,
  "custom_fields": {
    "sales_contact": "John Smith",
    "priority": "high",
    "internal_code": "MB-2026-001"
  },
  "images": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "category": "exterior",
      "image_url": "https://storage.googleapis.com/.../exterior_001.jpg",
      "thumbnail_url": "https://storage.googleapis.com/.../exterior_001_thumb.jpg",
      "width": 1920,
      "height": 1080,
      "display_order": 1
    }
  ],
  "floor_plans": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "unit_type": "1BR",
      "bedrooms": 1,
      "bathrooms": 1,
      "total_sqft": 750,
      "balcony_sqft": 100,
      "builtup_sqft": 650,
      "image_url": "https://storage.googleapis.com/.../floor_plan_1br.jpg",
      "display_order": 1
    }
  ],
  "original_pdf_url": "https://storage.googleapis.com/.../original.pdf",
  "processed_zip_url": "https://storage.googleapis.com/.../images.zip",
  "sheet_url": "https://docs.google.com/spreadsheets/d/ABC123.../edit",
  "workflow_status": "published",
  "published_url": "https://opr.com/properties/marina-bay-residences",
  "published_at": "2026-01-15T12:00:00Z",
  "created_by": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@your-domain.com"
  },
  "created_at": "2026-01-15T10:00:00Z",
  "last_modified_by": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Jane Smith",
    "email": "jane@your-domain.com"
  },
  "last_modified_at": "2026-01-15T11:30:00Z"
}
```

**Errors:**
- `404 Not Found` - Project ID doesn't exist

---

### PUT /api/projects/{id}

Update project fields.

**Request:**
```http
PUT /api/projects/770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Marina Bay Residences - Updated",
  "starting_price": 1600000,
  "custom_fields": {
    "priority": "urgent",
    "notes": "High demand property"
  }
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Marina Bay Residences - Updated",
  "starting_price": 1600000,
  "custom_fields": {
    "priority": "urgent",
    "notes": "High demand property"
  },
  "last_modified_at": "2026-01-15T12:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Project doesn't exist
- `403 Forbidden` - User not authorized to edit
- `400 Bad Request` - Invalid field values
- `422 Unprocessable Entity` - Validation errors

---

### DELETE /api/projects/{id}

Delete project (admin only).

**Request:**
```http
DELETE /api/projects/770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer <token>
```

**Response (204 No Content)**

**Errors:**
- `404 Not Found` - Project doesn't exist
- `403 Forbidden` - User is not admin

---

### POST /api/projects/{id}/approve

Approve project (admin only).

**Request:**
```http
POST /api/projects/770e8400-e29b-41d4-a716-446655440002/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "comments": "Looks good, approved for publication"
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "workflow_status": "approved",
  "approval": {
    "action": "approved",
    "approver": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Jane Smith"
    },
    "comments": "Looks good, approved for publication",
    "approved_at": "2026-01-15T12:00:00Z"
  }
}
```

**Errors:**
- `404 Not Found` - Project doesn't exist
- `403 Forbidden` - User is not admin
- `400 Bad Request` - Project not in "pending_approval" status

---

### GET /api/projects/{id}/history

Get project revision history.

**Request:**
```http
GET /api/projects/770e8400-e29b-41d4-a716-446655440002/history
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "field": "starting_price",
      "old_value": "1500000",
      "new_value": "1600000",
      "changed_by": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Jane Smith"
      },
      "changed_at": "2026-01-15T11:30:00Z"
    },
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "field": "workflow_status",
      "old_value": "draft",
      "new_value": "pending_approval",
      "changed_by": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Doe"
      },
      "changed_at": "2026-01-15T10:30:00Z"
    }
  ],
  "total": 15
}
```

---

### POST /api/projects/export

Export selected projects to CSV/JSON.

**Request:**
```http
POST /api/projects/export
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_ids": [
    "770e8400-e29b-41d4-a716-446655440002",
    "880e8400-e29b-41d4-a716-446655440003"
  ],
  "format": "csv",
  "fields": ["name", "developer", "location", "starting_price", "workflow_status"]
}
```

**Response (200 OK):**
```json
{
  "export_url": "https://storage.googleapis.com/pdp-automation-assets-dev/exports/export_2026-01-15.csv",
  "expires_at": "2026-01-16T10:00:00Z",
  "project_count": 2
}
```

**Errors:**
- `400 Bad Request` - Invalid project IDs or format

---

## Prompts Endpoints

### GET /api/prompts

List prompts with filtering.

**Request:**
```http
GET /api/prompts?template_type=opr&content_variant=standard
Authorization: Bearer <token>
```

**Query Parameters:**
- `template_type` (string: "aggregators" | "opr" | "mpp" | "adop" | "adre" | "commercial")
- `content_variant` (string: "standard" | "luxury")
- `search` (string) - Search prompt names
- `is_active` (boolean) - Filter by active status

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "cc0e8400-e29b-41d4-a716-446655440007",
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

---

### GET /api/prompts/{id}

Get prompt detail.

**Request:**
```http
GET /api/prompts/cc0e8400-e29b-41d4-a716-446655440007
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "name": "Meta Description",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Create a compelling meta description for this real estate project...",
  "character_limit": 160,
  "version": 3,
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z",
  "updated_by": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Admin User"
  }
}
```

**Errors:**
- `404 Not Found` - Prompt doesn't exist

---

### POST /api/prompts

Create new prompt (admin only).

**Request:**
```http
POST /api/prompts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Meta Title",
  "template_type": "opr",
  "content_variant": "standard",
  "content": "Create a compelling meta title for this real estate project...",
  "character_limit": 60
}
```

**Response (201 Created):**
```json
{
  "id": "dd0e8400-e29b-41d4-a716-446655440008",
  "name": "Meta Title",
  "template_type": "opr",
  "content_variant": "standard",
  "version": 1,
  "is_active": true,
  "created_at": "2026-01-15T12:00:00Z"
}
```

**Errors:**
- `403 Forbidden` - User is not admin
- `400 Bad Request` - Validation errors

---

### PUT /api/prompts/{id}

Update prompt (creates new version, admin only).

**Request:**
```http
PUT /api/prompts/cc0e8400-e29b-41d4-a716-446655440007
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Updated prompt content with improved clarity...",
  "change_reason": "Improved clarity and added examples"
}
```

**Response (200 OK):**
```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "version": 4,
  "content": "Updated prompt content with improved clarity...",
  "updated_at": "2026-01-15T12:30:00Z"
}
```

**Errors:**
- `403 Forbidden` - User is not admin
- `404 Not Found` - Prompt doesn't exist

---

### GET /api/prompts/{id}/versions

Get prompt version history.

**Request:**
```http
GET /api/prompts/cc0e8400-e29b-41d4-a716-446655440007/versions
Authorization: Bearer <token>
```

**Response (200 OK):**
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
    },
    {
      "version": 2,
      "content": "Original prompt content...",
      "change_reason": "Initial version",
      "created_at": "2026-01-01T00:00:00Z",
      "created_by": {
        "name": "Admin User"
      }
    }
  ]
}
```

---

## QA Endpoints

### POST /api/qa/compare

Run QA comparison at checkpoint.

**Request:**
```http
POST /api/qa/compare
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_id": "770e8400-e29b-41d4-a716-446655440002",
  "checkpoint_type": "generation",
  "input_content": {...},
  "comparison_target": {...}
}
```

**Response (200 OK):**
```json
{
  "id": "ee0e8400-e29b-41d4-a716-446655440009",
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
      },
      {
        "field": "payment_plan",
        "expected": "60/40",
        "actual": "70/30",
        "severity": "medium"
      }
    ],
    "missing": ["property_tax"],
    "extra": []
  },
  "performed_at": "2026-01-15T12:00:00Z"
}
```

---

### GET /api/qa/history

Get QA history for user or project.

**Request:**
```http
GET /api/qa/history?project_id=770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer <token>
```

**Query Parameters:**
- `project_id` (string, optional)
- `checkpoint_type` (string, optional)
- `page` (int)
- `limit` (int)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "ee0e8400-e29b-41d4-a716-446655440009",
      "project_id": "770e8400-e29b-41d4-a716-446655440002",
      "checkpoint_type": "generation",
      "status": "passed",
      "performed_at": "2026-01-15T12:00:00Z",
      "performed_by": {
        "name": "John Doe"
      }
    }
  ],
  "total": 30,
  "page": 1,
  "pages": 1
}
```

---

## Workflow Endpoints

### GET /api/workflow/items

Get Kanban board items.

**Request:**
```http
GET /api/workflow/items?status=pending_approval
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (string) - Filter by workflow_status
- `assigned_to` (string) - Filter by assigned user

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Marina Bay Residences",
      "workflow_status": "pending_approval",
      "assigned_to": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Jane Smith"
      },
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

---

### PUT /api/workflow/items/{id}

Update workflow item (move column, assign user).

**Request:**
```http
PUT /api/workflow/items/770e8400-e29b-41d4-a716-446655440002
Authorization: Bearer <token>
Content-Type: application/json

{
  "workflow_status": "approved",
  "assigned_to": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "workflow_status": "approved",
  "assigned_to": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Jane Smith"
  }
}
```

---

## Templates Endpoints

### GET /api/templates

List website templates.

**Request:**
```http
GET /api/templates
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "ff0e8400-e29b-41d4-a716-446655440010",
      "name": "OPR Standard Template",
      "template_type": "opr",
      "content_variant": "standard",
      "sheet_template_url": "https://docs.google.com/spreadsheets/d/...",
      "field_mappings": {
        "meta_title": "B2",
        "meta_description": "B3",
        "h1": "B4"
      },
      "is_active": true
    }
  ]
}
```

---

## Health Endpoints

### GET /health

Basic health check.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:00:00Z"
}
```

---

### GET /readiness

Readiness check (verifies external dependencies).

**Request:**
```http
GET /readiness
```

**Response (200 OK):**
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

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "checks": {
    "database": "ok",
    "storage": "ok",
    "anthropic_api": "error"
  },
  "timestamp": "2026-01-15T10:00:00Z"
}
```

---

## Related Documentation

- [API Design](../01-architecture/API_DESIGN.md) - API design principles
- [Service Layer](./SERVICE_LAYER.md) - Service implementations
- [Error Handling](./ERROR_HANDLING.md) - Error handling patterns

---

**Last Updated:** 2026-01-15
