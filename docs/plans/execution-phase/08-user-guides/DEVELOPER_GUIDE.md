# Developer Guide

**PDP Automation v.3 API**
*Complete guide for web developers integrating with PDP Automation*

---

## Table of Contents

1. [Introduction](#introduction)
2. [API Overview](#api-overview)
3. [Authentication](#authentication)
4. [Uploading Files](#uploading-files)
5. [Retrieving Project Data](#retrieving-project-data)
6. [Monitoring Job Status](#monitoring-job-status)
7. [Webhooks (Coming Soon)](#webhooks-coming-soon)
8. [Error Handling](#error-handling)
9. [Rate Limits](#rate-limits)
10. [Code Examples](#code-examples)
11. [Testing in Sandbox](#testing-in-sandbox)
12. [API Reference](#api-reference)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)
15. [FAQs](#faqs)

---

## Introduction

### Who Is This Guide For?

This guide is for **Web Developers** who need to:
- Integrate PDP Automation with external systems
- Automate property content generation workflows
- Build custom frontends or integrations
- Programmatically access project data
- Trigger processing via API

### What You'll Learn

By the end of this guide, you'll be able to:
- Authenticate with the PDP Automation API
- Upload PDF files programmatically
- Monitor processing jobs in real-time
- Retrieve generated content and assets
- Handle errors gracefully
- Implement webhooks for event notifications
- Build robust integrations

### Prerequisites

**Technical Knowledge:**
- REST API concepts
- JSON data format
- OAuth 2.0 authentication
- HTTP methods (GET, POST, PUT, DELETE)
- Asynchronous programming

**Tools:**
- Programming language (Python, JavaScript, PHP, etc.)
- HTTP client library
- Google Cloud credentials (for OAuth)

---

## API Overview

### Base URL

```
Production: https://api.pdp-automation.com
Sandbox: https://sandbox-api.pdp-automation.com
```

**Always use sandbox for development and testing.**

### API Version

Current version: **v1**

All endpoints are prefixed with `/api/v1/`

Example:
```
https://api.pdp-automation.com/api/v1/projects
```

### Content Type

All requests and responses use JSON:

```
Content-Type: application/json
```

For file uploads, use multipart/form-data:

```
Content-Type: multipart/form-data
```

### Response Format

All API responses follow this structure:

**Success Response:**
```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "meta": {
    "timestamp": "2026-01-15T10:30:00Z",
    "version": "v1"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "meta": {
    "timestamp": "2026-01-15T10:30:00Z",
    "version": "v1"
  }
}
```

---

## Authentication

PDP Automation uses **OAuth 2.0** with Google for authentication.

### Step 1: Obtain Google OAuth Token

Your application must first authenticate users via Google OAuth.

**Redirect user to Google OAuth:**
```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code&
  scope=openid%20email%20profile&
  hd=your-domain.com
```

**Parameters:**
- `client_id`: Your Google Cloud OAuth client ID
- `redirect_uri`: Your callback URL
- `hd=your-domain.com`: Restricts to @your-domain.com domain

### Step 2: Exchange Code for Token

After user approves, Google redirects to your callback with a code:

```
https://your-app.com/callback?code=AUTHORIZATION_CODE
```

Exchange this code for an access token:

```bash
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code=AUTHORIZATION_CODE&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET&
redirect_uri=YOUR_REDIRECT_URI&
grant_type=authorization_code
```

**Response:**
```json
{
  "access_token": "ya29.a0AfH6SMBx...",
  "expires_in": 3600,
  "token_type": "Bearer",
  "refresh_token": "1//0gHNw...",
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

### Step 3: Authenticate with PDP Automation API

Use the Google ID token to authenticate with PDP Automation:

```bash
POST https://api.pdp-automation.com/api/v1/auth/google
Content-Type: application/json

{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "pdp_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "pdp_refresh_1a2b3c4d5e6f...",
    "expires_in": 86400,
    "user": {
      "id": "user_abc123",
      "email": "sarah@your-domain.com",
      "name": "Sarah Chen",
      "role": "user"
    }
  }
}
```

### Step 4: Use Access Token in Requests

Include the PDP access token in all API requests:

```bash
GET https://api.pdp-automation.com/api/v1/projects
Authorization: Bearer pdp_eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Refresh

Access tokens expire after 24 hours. Use the refresh token to obtain a new one:

```bash
POST https://api.pdp-automation.com/api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "pdp_refresh_1a2b3c4d5e6f..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "pdp_eyJhbGciOiJIUzI1NiIsInR5cCI6...",
    "expires_in": 86400
  }
}
```

---

## Uploading Files

Upload PDF brochures programmatically.

### Endpoint

```
POST /api/v1/upload
```

### Request

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Body (multipart/form-data):**
```
file: <PDF file>
template_type: "aggregators" | "opr" | "mpp" | "adop" | "adre" | "commercial"
content_variant: "standard" | "luxury"
```

### Example: Python

```python
import requests

url = "https://api.pdp-automation.com/api/v1/upload"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

files = {
    "file": open("marina_heights_brochure.pdf", "rb")
}

data = {
    "template_type": "opr",
    "content_variant": "standard"
}

response = requests.post(url, headers=headers, files=files, data=data)
result = response.json()

if result["success"]:
    job_id = result["data"]["job_id"]
    print(f"Upload successful! Job ID: {job_id}")
else:
    print(f"Upload failed: {result['error']['message']}")
```

### Example: JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('marina_heights_brochure.pdf'));
form.append('template_type', 'opr');
form.append('content_variant', 'standard');

axios.post('https://api.pdp-automation.com/api/v1/upload', form, {
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    ...form.getHeaders()
  }
})
.then(response => {
  const jobId = response.data.data.job_id;
  console.log(`Upload successful! Job ID: ${jobId}`);
})
.catch(error => {
  console.error('Upload failed:', error.response.data.error.message);
});
```

### Example: cURL

```bash
curl -X POST https://api.pdp-automation.com/api/v1/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@marina_heights_brochure.pdf" \
  -F "template_type=opr" \
  -F "content_variant=standard"
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "project_id": "proj_abc123",
    "status": "queued",
    "estimated_duration": "5-10 minutes"
  }
}
```

### Available Template Types

```
aggregators  - Third-party aggregator domains (24+)
opr          - Off-Plan Residences (opr.ae)
mpp          - the company (main-portal.com)
adop         - Abu Dhabi Off Plan (abudhabioffplan.ae)
adre         - Abu Dhabi Real Estate (secondary-market-portal.com)
commercial   - Commercial Real Estate (cre.main-portal.com)
```

### Content Variants

```
standard     - Standard tone and style
luxury       - Premium luxury tone
```

To get all available templates:

```bash
GET /api/v1/templates
```

---

## Retrieving Project Data

Fetch project information and generated content.

### Get All Projects

```
GET /api/v1/projects
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `template_type`: Filter by template (aggregators, opr, mpp, adop, adre, commercial)
- `content_variant`: Filter by variant (standard, luxury)
- `status`: Filter by status (processing, review, approved, published)

**Example:**
```bash
GET /api/v1/projects?template_type=opr&status=approved&per_page=50
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "proj_abc123",
        "name": "Marina Heights",
        "template_type": "opr",
        "content_variant": "standard",
        "status": "approved",
        "developer": "Emaar Properties",
        "starting_price": 1200000,
        "currency": "AED",
        "created_at": "2026-01-14T08:00:00Z",
        "updated_at": "2026-01-15T09:15:00Z"
      },
      // ... more projects
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 147,
      "total_pages": 3
    }
  }
}
```

### Get Single Project

```
GET /api/v1/projects/{project_id}
```

**Example:**
```bash
GET /api/v1/projects/proj_abc123
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "proj_abc123",
      "name": "Marina Heights",
      "template_type": "opr",
      "content_variant": "standard",
      "status": "approved",

      // SEO Content
      "meta_title": "Marina Heights | Luxury Apartments in Dubai Marina",
      "meta_description": "Discover luxury waterfront living...",
      "h1_heading": "Marina Heights - Luxury Waterfront Living",
      "url_slug": "marina-heights-dubai-marina",
      "overview": "Marina Heights represents the pinnacle...",

      // Project Details
      "developer": "Emaar Properties",
      "starting_price": 1200000,
      "currency": "AED",
      "handover_date": "Q4 2026",
      "payment_plan": "60/40",
      "unit_types": ["1 BR", "2 BR", "3 BR"],
      "total_units": 250,

      // Location
      "location": "Dubai Marina",
      "community": "Dubai Marina",
      "sub_community": "Marina Promenade",

      // Images
      "images": {
        "exterior": [
          "https://storage.pdp-automation.com/projects/proj_abc123/exterior_01.png",
          // ... 10 total
        ],
        "interior": [
          "https://storage.pdp-automation.com/projects/proj_abc123/interior_01.png",
          // ... 10 total
        ],
        "amenities": [
          "https://storage.pdp-automation.com/projects/proj_abc123/amenity_01.png",
          // ... 5 total
        ],
        "logos": [
          "https://storage.pdp-automation.com/projects/proj_abc123/logo_01.png",
          // ... 3 total
        ]
      },

      // Floor Plans
      "floor_plans": [
        {
          "type": "1 BR",
          "bedrooms": 1,
          "bathrooms": 1,
          "area_sqft": 650,
          "image_url": "https://storage.pdp-automation.com/projects/proj_abc123/floorplan_1br.png"
        },
        // ... more floor plans
      ],

      // Assets
      "google_sheet_url": "https://docs.google.com/spreadsheets/d/...",
      "zip_url": "https://storage.pdp-automation.com/projects/proj_abc123/assets.zip",
      "pdf_url": "https://storage.pdp-automation.com/projects/proj_abc123/original.pdf",

      // Timestamps
      "created_at": "2026-01-14T08:00:00Z",
      "updated_at": "2026-01-15T09:15:00Z",
      "submitted_at": "2026-01-14T09:30:00Z",
      "approved_at": "2026-01-15T09:15:00Z"
    }
  }
}
```

### Download Assets

Download the ZIP file containing all images and floor plans:

```python
import requests

# Get project data first
response = requests.get(
    "https://api.pdp-automation.com/api/v1/projects/proj_abc123",
    headers={"Authorization": "Bearer YOUR_ACCESS_TOKEN"}
)

project = response.json()["data"]["project"]
zip_url = project["zip_url"]

# Download ZIP file
zip_response = requests.get(zip_url)
with open("marina_heights_assets.zip", "wb") as f:
    f.write(zip_response.content)

print("Assets downloaded successfully!")
```

---

## Monitoring Job Status

After uploading a file, monitor the processing job.

### Get Job Status

```
GET /api/v1/jobs/{job_id}
```

**Example:**
```bash
GET /api/v1/jobs/job_xyz789
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_xyz789",
      "project_id": "proj_abc123",
      "status": "processing",
      "progress": 60,
      "current_step": "Extracting images",
      "steps": [
        {"name": "Upload PDF", "status": "completed", "duration": 10},
        {"name": "Extract text", "status": "completed", "duration": 30},
        {"name": "Extract images", "status": "in_progress", "duration": null},
        {"name": "Classify images", "status": "pending", "duration": null},
        {"name": "Detect floor plans", "status": "pending", "duration": null},
        {"name": "Remove watermarks", "status": "pending", "duration": null},
        {"name": "Generate SEO content", "status": "pending", "duration": null},
        {"name": "Create Google Sheet", "status": "pending", "duration": null},
        {"name": "Package ZIP", "status": "pending", "duration": null}
      ],
      "estimated_completion": "2026-01-15T10:38:00Z",
      "started_at": "2026-01-15T10:28:00Z"
    }
  }
}
```

### Poll Job Status

Poll the job endpoint until completion:

**Python Example:**
```python
import requests
import time

job_id = "job_xyz789"
url = f"https://api.pdp-automation.com/api/v1/jobs/{job_id}"
headers = {"Authorization": "Bearer YOUR_ACCESS_TOKEN"}

while True:
    response = requests.get(url, headers=headers)
    job = response.json()["data"]["job"]

    status = job["status"]
    progress = job["progress"]
    current_step = job["current_step"]

    print(f"Status: {status}, Progress: {progress}% - {current_step}")

    if status == "completed":
        print("Processing complete!")
        project_id = job["project_id"]
        print(f"Project ID: {project_id}")
        break
    elif status == "failed":
        print(f"Processing failed: {job['error']}")
        break

    time.sleep(5)  # Poll every 5 seconds
```

**JavaScript Example:**
```javascript
async function pollJobStatus(jobId, accessToken) {
  const url = `https://api.pdp-automation.com/api/v1/jobs/${jobId}`;
  const headers = { 'Authorization': `Bearer ${accessToken}` };

  while (true) {
    const response = await fetch(url, { headers });
    const data = await response.json();
    const job = data.data.job;

    console.log(`Status: ${job.status}, Progress: ${job.progress}% - ${job.current_step}`);

    if (job.status === 'completed') {
      console.log('Processing complete!');
      console.log(`Project ID: ${job.project_id}`);
      return job.project_id;
    } else if (job.status === 'failed') {
      throw new Error(`Processing failed: ${job.error}`);
    }

    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
  }
}
```

### Job Status Values

- `queued`: Job queued, waiting to start
- `processing`: Job is running
- `completed`: Job finished successfully
- `failed`: Job failed (see error field)
- `cancelled`: Job was cancelled

---

## Webhooks (Coming Soon)

Webhooks allow you to receive real-time notifications when events occur.

**Note:** Webhooks are planned for Q2 2026. Check the API changelog for updates.

### Webhook Events

Once available, you'll be able to subscribe to these events:

```
project.created      - New project created
project.processing   - Processing started
project.completed    - Processing completed
project.failed       - Processing failed
project.submitted    - Submitted for approval
project.approved     - Approved by marketing
project.rejected     - Rejected by marketing
project.published    - Published on website
```

### Webhook Payload (Future)

```json
POST https://your-app.com/webhooks/pdp
Content-Type: application/json
X-PDP-Signature: sha256=...

{
  "event": "project.completed",
  "timestamp": "2026-01-15T10:35:00Z",
  "data": {
    "project_id": "proj_abc123",
    "job_id": "job_xyz789",
    "project_name": "Marina Heights",
    "template_type": "opr"
  }
}
```

### Registering Webhooks (Future)

```bash
POST /api/v1/webhooks
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN

{
  "url": "https://your-app.com/webhooks/pdp",
  "events": ["project.completed", "project.approved"],
  "secret": "your_webhook_secret"
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error context
    }
  }
}
```

### Common Error Codes

**Authentication Errors:**
- `INVALID_TOKEN`: Access token is invalid or expired
- `TOKEN_EXPIRED`: Access token has expired
- `UNAUTHORIZED`: User not authorized for this action

**Validation Errors:**
- `MISSING_FIELD`: Required field missing
- `INVALID_FORMAT`: Field format invalid
- `FILE_TOO_LARGE`: File exceeds size limit (50MB)
- `INVALID_FILE_TYPE`: Only PDF files allowed

**Processing Errors:**
- `PDF_ENCRYPTED`: PDF is password-protected
- `PDF_CORRUPTED`: PDF file is corrupted
- `GEMINI_QUOTA_EXCEEDED`: Google Gemini API quota exceeded
- `ANTHROPIC_QUOTA_EXCEEDED`: Anthropic API quota exceeded

**Rate Limit Errors:**
- `RATE_LIMIT_EXCEEDED`: Too many requests

### Error Handling Example

**Python:**
```python
import requests

try:
    response = requests.post(url, headers=headers, files=files, data=data)
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx

    result = response.json()
    if result["success"]:
        print("Success!")
    else:
        # API returned error in response body
        error = result["error"]
        print(f"Error {error['code']}: {error['message']}")

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed. Check your access token.")
    elif e.response.status_code == 429:
        print("Rate limit exceeded. Please wait before retrying.")
    else:
        print(f"HTTP Error: {e.response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

**JavaScript:**
```javascript
async function uploadFile(file, accessToken) {
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      body: formData
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Authentication failed. Check your access token.');
      } else if (response.status === 429) {
        throw new Error('Rate limit exceeded. Please wait before retrying.');
      }
      throw new Error(`HTTP Error: ${response.status}`);
    }

    const result = await response.json();

    if (!result.success) {
      const error = result.error;
      throw new Error(`${error.code}: ${error.message}`);
    }

    return result.data;

  } catch (error) {
    console.error('Upload failed:', error.message);
    throw error;
  }
}
```

### Retry Logic

Implement exponential backoff for transient errors:

```python
import time

def upload_with_retry(url, headers, files, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            elif e.response.status_code >= 500:  # Server error
                wait_time = 2 ** attempt
                print(f"Server error. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise  # Don't retry client errors (4xx)

    raise Exception("Max retries exceeded")
```

---

## Rate Limits

### Current Limits

**Anonymous (no authentication):**
- 5 requests per hour

**Authenticated User:**
- 50 requests per hour

**Authenticated Admin:**
- Unlimited

### Rate Limit Headers

Each response includes rate limit information:

```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

**Headers:**
- `X-RateLimit-Limit`: Total requests allowed per hour
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

### Handling Rate Limits

```python
import time

response = requests.get(url, headers=headers)

remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

if remaining < 5:
    wait_seconds = reset_time - time.time()
    print(f"Approaching rate limit. {remaining} requests remaining.")
    print(f"Limit resets in {wait_seconds:.0f} seconds")
```

---

## Code Examples

### Complete Python Integration

```python
import requests
import time
import os

class PDPAutomationClient:
    def __init__(self, access_token, base_url="https://api.pdp-automation.com"):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {access_token}"
        }

    def upload_pdf(self, file_path, template_type, content_variant="standard"):
        """Upload a PDF and start processing."""
        url = f"{self.base_url}/api/v1/upload"

        files = {"file": open(file_path, "rb")}
        data = {
            "template_type": template_type,
            "content_variant": content_variant
        }

        response = requests.post(url, headers=self.headers, files=files, data=data)
        response.raise_for_status()

        result = response.json()
        return result["data"]["job_id"]

    def get_job_status(self, job_id):
        """Get current job status."""
        url = f"{self.base_url}/api/v1/jobs/{job_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()["data"]["job"]

    def wait_for_completion(self, job_id, poll_interval=5):
        """Poll job status until completion."""
        while True:
            job = self.get_job_status(job_id)

            status = job["status"]
            progress = job["progress"]

            print(f"Progress: {progress}% - {job['current_step']}")

            if status == "completed":
                return job["project_id"]
            elif status == "failed":
                raise Exception(f"Processing failed: {job.get('error', 'Unknown error')}")

            time.sleep(poll_interval)

    def get_project(self, project_id):
        """Get project data."""
        url = f"{self.base_url}/api/v1/projects/{project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()["data"]["project"]

    def download_assets(self, project_id, output_dir):
        """Download project assets (ZIP file)."""
        project = self.get_project(project_id)
        zip_url = project["zip_url"]

        response = requests.get(zip_url)
        response.raise_for_status()

        output_path = os.path.join(output_dir, f"{project['name']}_assets.zip")
        with open(output_path, "wb") as f:
            f.write(response.content)

        return output_path

# Usage
client = PDPAutomationClient("YOUR_ACCESS_TOKEN")

# Upload PDF
job_id = client.upload_pdf(
    "marina_heights.pdf",
    template_type="opr",
    content_variant="standard"
)
print(f"Upload started. Job ID: {job_id}")

# Wait for completion
project_id = client.wait_for_completion(job_id)
print(f"Processing complete! Project ID: {project_id}")

# Get project data
project = client.get_project(project_id)
print(f"Project: {project['name']}")
print(f"Meta Title: {project['meta_title']}")
print(f"Starting Price: {project['starting_price']} {project['currency']}")

# Download assets
zip_path = client.download_assets(project_id, "./downloads")
print(f"Assets downloaded to: {zip_path}")
```

### Complete JavaScript Integration

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class PDPAutomationClient {
  constructor(accessToken, baseUrl = 'https://api.pdp-automation.com') {
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${accessToken}`
    };
  }

  async uploadPdf(filePath, templateType, contentVariant = 'standard') {
    const url = `${this.baseUrl}/api/v1/upload`;

    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('template_type', templateType);
    form.append('content_variant', contentVariant);

    const response = await axios.post(url, form, {
      headers: {
        ...this.headers,
        ...form.getHeaders()
      }
    });

    return response.data.data.job_id;
  }

  async getJobStatus(jobId) {
    const url = `${this.baseUrl}/api/v1/jobs/${jobId}`;
    const response = await axios.get(url, { headers: this.headers });
    return response.data.data.job;
  }

  async waitForCompletion(jobId, pollInterval = 5000) {
    while (true) {
      const job = await this.getJobStatus(jobId);

      console.log(`Progress: ${job.progress}% - ${job.current_step}`);

      if (job.status === 'completed') {
        return job.project_id;
      } else if (job.status === 'failed') {
        throw new Error(`Processing failed: ${job.error || 'Unknown error'}`);
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }

  async getProject(projectId) {
    const url = `${this.baseUrl}/api/v1/projects/${projectId}`;
    const response = await axios.get(url, { headers: this.headers });
    return response.data.data.project;
  }

  async downloadAssets(projectId, outputDir) {
    const project = await this.getProject(projectId);
    const zipUrl = project.zip_url;

    const response = await axios.get(zipUrl, { responseType: 'arraybuffer' });
    const outputPath = `${outputDir}/${project.name}_assets.zip`;

    fs.writeFileSync(outputPath, response.data);
    return outputPath;
  }
}

// Usage
(async () => {
  const client = new PDPAutomationClient('YOUR_ACCESS_TOKEN');

  // Upload PDF
  const jobId = await client.uploadPdf(
    'marina_heights.pdf',
    'opr',
    'standard'
  );
  console.log(`Upload started. Job ID: ${jobId}`);

  // Wait for completion
  const projectId = await client.waitForCompletion(jobId);
  console.log(`Processing complete! Project ID: ${projectId}`);

  // Get project data
  const project = await client.getProject(projectId);
  console.log(`Project: ${project.name}`);
  console.log(`Meta Title: ${project.meta_title}`);
  console.log(`Starting Price: ${project.starting_price} ${project.currency}`);

  // Download assets
  const zipPath = await client.downloadAssets(projectId, './downloads');
  console.log(`Assets downloaded to: ${zipPath}`);
})();
```

---

## Testing in Sandbox

### Sandbox Environment

Use the sandbox for development:

```
Sandbox Base URL: https://sandbox-api.pdp-automation.com
```

**Sandbox features:**
- Separate database (no production data)
- Same API endpoints
- Test data pre-populated
- No cost for API usage (simulated)
- Rate limits relaxed (100 req/hour)

### Getting Sandbox Access

Contact support to request sandbox credentials:
- Email: pdp-support@your-domain.com
- Provide: Your name, email, use case

You'll receive sandbox OAuth credentials.

### Test Data

Sandbox includes pre-populated test projects:

```
Test Project 1: "Sandbox Towers"
Test Project 2: "Test Marina Heights"
Test Project 3: "Demo Villa Project"
```

Use these for testing without creating new projects.

---

## API Reference

### Endpoints Summary

**Authentication:**
```
POST /api/v1/auth/google          Authenticate with Google OAuth
POST /api/v1/auth/refresh         Refresh access token
```

**Upload:**
```
POST /api/v1/upload               Upload PDF and start processing
```

**Jobs:**
```
GET /api/v1/jobs/{job_id}         Get job status
```

**Projects:**
```
GET /api/v1/projects              List all projects
GET /api/v1/projects/{id}         Get single project
PUT /api/v1/projects/{id}         Update project (admin only)
DELETE /api/v1/projects/{id}      Delete project (admin only)
```

**Templates:**
```
GET /api/v1/templates             List available templates
```

**User:**
```
GET /api/v1/user                  Get current user info
```

Full API documentation available at:
```
https://api.pdp-automation.com/docs
```

---

## Best Practices

### 1. Use Environment Variables

Never hardcode credentials:

```python
import os

ACCESS_TOKEN = os.environ.get("PDP_ACCESS_TOKEN")
BASE_URL = os.environ.get("PDP_BASE_URL", "https://api.pdp-automation.com")
```

### 2. Implement Exponential Backoff

For retries:

```python
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            time.sleep(wait)
```

### 3. Log API Requests

For debugging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

response = requests.post(url, headers=headers, files=files, data=data)
logger.info(f"API Request: POST {url}")
logger.info(f"Response: {response.status_code} - {response.json()}")
```

### 4. Handle Token Expiration

Refresh tokens automatically:

```python
def api_request(url, headers):
    response = requests.get(url, headers=headers)

    if response.status_code == 401:  # Token expired
        new_token = refresh_access_token()
        headers["Authorization"] = f"Bearer {new_token}"
        response = requests.get(url, headers=headers)  # Retry

    return response
```

### 5. Validate Input

Before uploading:

```python
import os

def validate_pdf(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.endswith('.pdf'):
        raise ValueError("Only PDF files are supported")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > 50:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max 50MB)")
```

### 6. Use Webhooks When Available

Instead of polling (when webhooks launch):

```python
# Polling (current)
while status != 'completed':
    time.sleep(5)
    status = get_job_status(job_id)

# Webhooks (future - more efficient)
# System calls your webhook when job completes
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause:** Invalid or expired access token

**Solution:**
1. Verify token is correct
2. Check token expiration
3. Refresh token if expired
4. Re-authenticate if refresh fails

---

### Issue: 429 Rate Limit Exceeded

**Cause:** Too many requests

**Solution:**
1. Check `X-RateLimit-Reset` header
2. Wait until limit resets
3. Implement rate limit handling in code
4. Request higher rate limit (contact support)

---

### Issue: Upload Fails with 422 Error

**Cause:** Invalid parameters

**Solution:**
1. Check file is valid PDF
2. Verify file size under 50MB
3. Ensure `template_type` and `content_variant` are correct
4. Check error message for specific issue

---

### Issue: Job Stuck at "Processing"

**Cause:** May be a long PDF or system delay

**Solution:**
1. Wait at least 15 minutes (complex PDFs take longer)
2. Check job status for error
3. If truly stuck (> 30 min), contact support with job ID

---

## FAQs

**Q: Is there a cost to use the API?**

A: No direct cost for API usage. Anthropic/Gemini costs are covered by PDP Automation.

---

**Q: Can I upload multiple PDFs simultaneously?**

A: Yes, via multiple API calls. Each upload gets a unique job ID.

---

**Q: What's the maximum file size?**

A: 50MB per PDF. Contact support if you need larger limits.

---

**Q: How long does processing take?**

A: Typically 5-10 minutes. Complex PDFs may take up to 15 minutes.

---

**Q: Can I edit projects via API?**

A: Currently read-only for most users. Admins can update via API. Edit functionality coming soon.

---

**Q: Are there client libraries available?**

A: Official Python and JavaScript libraries are in development. For now, use code examples in this guide.

---

**Q: How do I report API issues?**

A: Email pdp-support@your-domain.com with details (endpoint, request/response, error message).

---

## Need Help?

**Documentation:**
- API Docs: https://api.pdp-automation.com/docs
- This guide
- Code examples repository (coming soon)

**Support:**
- Email: pdp-support@your-domain.com
- Slack: #pdp-automation-dev channel

**Updates:**
- API Changelog: https://api.pdp-automation.com/changelog
- Subscribe for email notifications

---

**Happy coding!** Build amazing integrations with PDP Automation. If you create something cool, let us know - we'd love to feature your integration.

*Last updated: January 15, 2026*
*API Version: v1*
