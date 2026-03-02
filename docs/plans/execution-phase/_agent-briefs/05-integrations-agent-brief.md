# Agent Briefing: Integrations Documentation Agent

**Agent ID:** integrations-docs-agent
**Batch:** 2 (Features)
**Priority:** P1 - External Systems
**Est. Context Usage:** 39,000 tokens

---

## Your Mission

Create **6 integration documentation files** explaining how PDP Automation v.3 connects with external services (Google Cloud, Anthropic API, Sheets, Drive, OAuth).

**Your Output Directory:** `c:/Users/shahe/PDP Automation v.3/docs/05-integrations/`

---

## Files You Must Create

1. `GOOGLE_CLOUD_SETUP.md` (400-500 lines) - Complete GCP project configuration
2. `ANTHROPIC_API_INTEGRATION.md` (500-600 lines) - Claude Sonnet 4.5 usage patterns
3. `GOOGLE_SHEETS_INTEGRATION.md` (350-400 lines) - Sheets API patterns
4. `GOOGLE_OAUTH_SETUP.md` (300-350 lines) - Workspace auth configuration
5. `GOOGLE_DRIVE_INTEGRATION.md` (300-350 lines) - Drive API for file sharing with organization
6. `CLOUD_STORAGE_PATTERNS.md` (300-350 lines) - GCS upload/download patterns

**Total Output:** ~2,150-2,550 lines across 6 files

---

## 1. Google Cloud Setup

**Services to Configure:**
- Cloud Run (backend + frontend)
- Cloud Storage (files)
- Cloud Tasks (job queue)
- Secret Manager (credentials including Anthropic API key)
- Cloud Monitoring + Logging
- Cloud Build (CI/CD)
- IAM (service accounts, permissions)
- Neon PostgreSQL (external, managed separately)

**Step-by-Step Setup:**
1. Create GCP project
2. Enable APIs
3. Create service accounts
4. Configure IAM roles
5. Create Cloud Storage bucket
6. Configure Secret Manager (including Anthropic API key)
7. Configure Cloud Run services
8. Set up Cloud Tasks queue
9. Set up monitoring and logging
10. Configure Neon PostgreSQL connection (external)

**Example Commands:**
```bash
# Create project
gcloud projects create pdp-automation-prod --name="PDP Automation"

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  cloudtasks.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

# Create service account
gcloud iam service-accounts create pdp-automation-sa \
  --display-name="PDP Automation Service Account"

# Grant roles (examples)
gcloud projects add-iam-policy-binding pdp-automation-prod \
  --member="serviceAccount:pdp-automation-sa@pdp-automation-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Store Anthropic API key in Secret Manager
echo -n "your-anthropic-api-key" | gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic"
```

---

## 2. Anthropic API Integration

**Model Selection:**
- **Claude Turbo** for text extraction and content generation (128K context)
- **Claudeo** for vision tasks (multimodal)

**Use Cases:**
1. **Text Extraction from PDF** (Claudeo vision)
2. **Image Classification** (Claudeo vision)
3. **Watermark Detection** (Claudeo vision)
4. **Floor Plan Data Extraction** (Claudeo vision)
5. **Content Generation** (Claude Turbo text)
6. **QA Validation** (Claude Turbo text)

**API Patterns:**

```python
# Text extraction from PDF pages using Claude Vision
import anthropic
import base64

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# Convert PDF pages to base64 images
image_content = []
for page_bytes in pdf_pages:
    base64_image = base64.b64encode(page_bytes).decode('utf-8')
    image_content.append({
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": base64_image
        }
    })

image_content.append({
    "type": "text",
    "text": "Extract project name, developer, location, starting price, amenities..."
})

response = await client.messages.create(
    model="claude-sonnet-4-5-20241022",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": image_content
        }
    ]
)

extracted_data = json.loads(response.content[0].text)
```

**Content Generation:**
```python
# Generate SEO content from extracted data
response = await client.messages.create(
    model="claude-sonnet-4-5-20241022",
    max_tokens=2048,
    system="You are an expert real estate content writer...",
    messages=[
        {
            "role": "user",
            "content": f"Generate content for: {json.dumps(extracted_data)}"
        }
    ]
)

content = response.content[0].text
```

**Cost Optimization:**
- Use Claude Turbo for text-only tasks (cheaper than Claudeo)
- Set appropriate `max_tokens` limits
- Batch similar requests together
- Cache responses for duplicate requests
- Use `detail: "low"` for simple image classification

**Rate Limiting:**
- Tier-based rate limits (depends on your API usage tier)
- Implement exponential backoff on 429 errors
- Queue requests via Cloud Tasks for reliability

**Error Handling:**
```python
from anthropic import RateLimitError, APIError, APITimeoutError

try:
    response = await client.messages.create(...)
except RateLimitError:
    # Rate limit exceeded, retry after delay
    await asyncio.sleep(60)
    # Retry with exponential backoff
except APITimeoutError:
    # Request timed out, retry
    logger.warning("Anthropic request timeout, retrying...")
except APIError as e:
    # API error, log and handle
    logger.error(f"Anthropic API error: {e}")
```

---

## 3. Google Sheets Integration

**Purpose:** Populate content into Google Sheets templates

**Authentication:**
- Service account with domain-wide delegation
- OAuth scopes: `https://www.googleapis.com/auth/spreadsheets`

**Library:** `gspread` 6.x

**Operations:**

1. **Create Sheet from Template**
```python
import gspread

gc = gspread.service_account(filename='credentials.json')

# Copy template
template = gc.open_by_key(template_id)
new_sheet = gc.copy(template.id, title=f"Project: {project_name}")
```

2. **Batch Update Cells** (Efficient)
```python
# BAD: Individual cell updates (100+ API calls)
worksheet.update_acell('B1', 'Project Name')
worksheet.update_acell('B2', 'Developer')

# GOOD: Batch update (1 API call)
updates = [
    {'range': 'B1', 'values': [['Project Name']]},
    {'range': 'B2', 'values': [['Developer']]},
    {'range': 'B3:B6', 'values': [
        ['Overview line 1'],
        ['Overview line 2'],
        ['Overview line 3']
    ]}
]
worksheet.batch_update(updates)
```

3. **Field Mapping**
```json
{
  "project_name": "B1",
  "meta_title": "B2",
  "meta_description": "B3",
  "url_slug": "B4",
  "h1": "B5",
  "starting_price": "B6",
  "overview": "B10:B15"  // Range for multi-line
}
```

**Rate Limits:**
- 100 requests per 100 seconds per user
- Use `batch_update` to minimize requests

---

## 4. Google OAuth Setup

**Purpose:** Authenticate users via Google Workspace

**Configuration:**

1. **Create OAuth Consent Screen**
   - Application type: Internal
   - Authorized domains: your-domain.com

2. **Create OAuth Client ID**
   - Application type: Web application
   - Authorized redirect URIs: `https://your-app.com/api/auth/callback`

3. **Domain Restriction**
```python
# In backend auth service
async def check_domain_restriction(email: str) -> bool:
    allowed_domain = "your-domain.com"
    return email.endswith(f"@{allowed_domain}")
```

4. **JWT Token Generation**
```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user: User) -> str:
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
```

5. **Frontend Integration**
```typescript
// src/lib/auth.ts
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google'

const login = useGoogleLogin({
  onSuccess: async (tokenResponse) => {
    const { data } = await api.post('/api/auth/google', {
      token: tokenResponse.access_token
    })
    localStorage.setItem('token', data.access_token)
    navigate('/')
  }
})
```

**Security:**
- HTTPS only
- HttpOnly cookies for refresh tokens
- CSRF protection
- Token rotation every 7 days

---

## 5. Google Drive Integration

**Purpose:** Upload processed images and floor plans to a shared Google Drive folder, automatically shared with the @your-domain.com organization.

**Why Google Drive?**
- Content managers and publishers need seamless access to processed files
- Organization-wide sharing eliminates manual file distribution
- Integration with existing Google Workspace ecosystem
- Automatic file organization by project

**Setup:**

1. **Create Shared Drive Folder**
   - Create folder in Google Drive: "PDP Automation - Processed Assets"
   - Share with "Anyone at the company with the link" (Can view)
   - Add service account as Editor: `pdp-automation-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com`
   - Note the folder ID from the URL

2. **Enable Domain-Wide Delegation**
   - Go to Google Workspace Admin Console
   - Navigate to Security > API Controls > Domain-wide Delegation
   - Add service account client ID
   - Add OAuth scope: `https://www.googleapis.com/auth/drive.file`

3. **Upload Pattern**
```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

# Initialize Drive API client
SCOPES = ['https://www.googleapis.com/auth/drive.file']
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

async def upload_to_drive(
    file_bytes: bytes,
    filename: str,
    folder_id: str,
    mime_type: str = 'image/jpeg'
) -> str:
    """Upload file to Google Drive folder"""

    file_metadata = {
        'name': filename,
        'parents': [folder_id]  # Parent folder ID
    }

    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mime_type,
        resumable=True
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink, webContentLink'
    ).execute()

    return file.get('webViewLink')  # Returns shareable link
```

4. **Folder Structure Pattern**
```python
async def create_project_folder(project_name: str, parent_folder_id: str) -> str:
    """Create subfolder for project"""

    folder_metadata = {
        'name': project_name,
        'parents': [parent_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    return folder.get('id')

async def organize_project_files(project_name: str, images: List[bytes], floor_plans: List[bytes]):
    """Upload and organize all project files"""

    # Create project folder
    project_folder_id = await create_project_folder(
        project_name,
        settings.GOOGLE_DRIVE_FOLDER_ID
    )

    # Create subfolders
    images_folder = await create_project_folder('Images', project_folder_id)
    floor_plans_folder = await create_project_folder('Floor Plans', project_folder_id)

    # Upload images
    image_urls = []
    for i, img_bytes in enumerate(images):
        url = await upload_to_drive(
            img_bytes,
            f'image_{i+1}.jpg',
            images_folder,
            'image/jpeg'
        )
        image_urls.append(url)

    # Upload floor plans
    floor_plan_urls = []
    for i, fp_bytes in enumerate(floor_plans):
        url = await upload_to_drive(
            fp_bytes,
            f'floor_plan_{i+1}.jpg',
            floor_plans_folder,
            'image/jpeg'
        )
        floor_plan_urls.append(url)

    return {
        'project_folder_url': f'https://drive.google.com/drive/folders/{project_folder_id}',
        'image_urls': image_urls,
        'floor_plan_urls': floor_plan_urls
    }
```

5. **Batch Upload (Efficient)**
```python
async def batch_upload_images(images: List[tuple[bytes, str]], folder_id: str):
    """Batch upload multiple images efficiently"""

    from googleapiclient.http import MediaIoBaseUpload
    import asyncio

    async def upload_one(img_bytes: bytes, filename: str):
        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(img_bytes), mimetype='image/jpeg')

        return drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

    # Upload all images concurrently
    tasks = [upload_one(img, name) for img, name in images]
    results = await asyncio.gather(*tasks)

    return [r.get('webViewLink') for r in results]
```

6. **Permission Management**
```python
async def share_folder_with_organization(folder_id: str):
    """Share folder with everyone in the organization"""

    permission = {
        'type': 'domain',
        'role': 'reader',
        'domain': 'your-domain.com'
    }

    drive_service.permissions().create(
        fileId=folder_id,
        body=permission,
        fields='id'
    ).execute()
```

**Rate Limits:**
- 1,000 requests per 100 seconds per user
- 10,000 requests per 100 seconds per project
- Use batch operations to minimize requests

**Error Handling:**
```python
from googleapiclient.errors import HttpError

try:
    file = await upload_to_drive(...)
except HttpError as error:
    if error.resp.status == 403:
        # Permission denied
        logger.error(f"Drive permission denied: {error}")
    elif error.resp.status == 404:
        # Folder not found
        logger.error(f"Drive folder not found: {error}")
    elif error.resp.status == 429:
        # Rate limit exceeded
        await asyncio.sleep(60)
        # Retry with exponential backoff
```

**Cost:** Free (Google Drive included in Workspace)

---

## 6. Cloud Storage Patterns

**Bucket Structure:**
```
pdp-automation-assets/
├── uploads/
│   └── {job_id}/
│       └── original.pdf
├── processed/
│   └── {project_id}/
│       ├── images/
│       │   ├── interior/
│       │   ├── exterior/
│       │   ├── amenity/
│       │   └── logo/
│       ├── floor_plans/
│       └── output.zip
└── temp/
    └── {job_id}/  (auto-deleted after 24h)
```

**Upload Pattern (Stream to GCS):**
```python
from google.cloud import storage

async def upload_to_gcs(
    file_bytes: bytes,
    blob_path: str,
    content_type: str
) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(blob_path)

    blob.upload_from_string(
        file_bytes,
        content_type=content_type
    )

    # Make public (optional)
    blob.make_public()

    return blob.public_url
```

**Download Pattern:**
```python
async def download_from_gcs(blob_path: str) -> bytes:
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(blob_path)

    return blob.download_as_bytes()
```

**Signed URLs (Temporary Access):**
```python
from datetime import timedelta

def generate_signed_url(blob_path: str, expiration_minutes: int) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET"
    )

    return url
```

**Lifecycle Policy (Auto-Cleanup):**
```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 365,
          "matchesPrefix": ["uploads/"]
        }
      },
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 1,
          "matchesPrefix": ["temp/"]
        }
      }
    ]
  }
}
```

---

## Environment Variables

```bash
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxxxx.neon.tech/neondb?sslmode=require

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-5-20241022

# Google Cloud
GOOGLE_CLOUD_PROJECT=pdp-automation-prod
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCS_BUCKET_NAME=pdp-automation-assets

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS=/path/to/sheets-credentials.json
TEMPLATE_SHEET_ID=your-template-sheet-id

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx
ALLOWED_EMAIL_DOMAIN=your-domain.com

# Google Drive
GOOGLE_DRIVE_FOLDER_ID=your-root-folder-id
```

---

## Document Standards

Each integration document must include:
1. Purpose and overview
2. Prerequisites (accounts, credentials)
3. Step-by-step setup instructions
4. Code examples (Python for backend, TypeScript for frontend)
5. Authentication patterns
6. Error handling
7. Rate limiting and quotas
8. Cost optimization tips
9. Security considerations
10. Troubleshooting section

---

## Quality Checklist

- ✅ All 6 files created
- ✅ Setup steps clear and complete
- ✅ Code examples in Python
- ✅ Authentication explained
- ✅ Rate limits documented
- ✅ Error handling patterns
- ✅ Security considerations
- ✅ Environment variables listed

Begin with `GOOGLE_CLOUD_SETUP.md`.