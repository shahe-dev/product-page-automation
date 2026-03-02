# Google Drive Integration

## Overview

PDP Automation v.3 integrates with Google Drive to automatically upload and organize processed images and floor plans. Files are shared organization-wide with @your-domain.com users, eliminating manual file distribution and enabling seamless access for content managers and publishers.

**Key Features:**
- Automatic upload of processed images and floor plans
- Organization-wide sharing with @your-domain.com domain
- Structured folder hierarchy by project
- Batch upload for efficiency
- Shareable links for easy access
- Integration with existing Google Workspace ecosystem

## Why Google Drive?

1. **Seamless Access**: Content managers already use Google Workspace
2. **Organization Sharing**: Automatic sharing with entire @your-domain.com domain
3. **No Manual Distribution**: Files instantly available to all team members
4. **Version Control**: Google Drive handles file versioning automatically
5. **Zero Additional Cost**: Included in Google Workspace subscription

## Prerequisites

1. **Google Workspace Account** (@your-domain.com domain)
2. **Service Account** added as member to Shared Drive
3. **Google Drive API** enabled
4. **Shared Drive** configured (ID: `0AOEEIstP54k2Uk9PVA`)
5. **Python 3.11+** with Google Drive libraries

> **Note:** This integration uses a Shared Drive instead of domain-wide delegation, which simplifies setup and avoids the need for Google Workspace admin approval. All files are stored in the Shared Drive and automatically accessible to team members.

## Google Cloud Setup

### Enable Google Drive API

```bash
# Enable Drive API
gcloud services enable drive.googleapis.com \
  --project=YOUR-GCP-PROJECT-ID

# Verify API is enabled
gcloud services list --enabled --filter="drive" \
  --project=YOUR-GCP-PROJECT-ID
```

### Configure Service Account for Drive

```bash
# Use existing service account or create new one
# Grant Drive permissions to pdp-automation-sa

# Download service account key (if not already done)
gcloud iam service-accounts keys create drive-credentials.json \
  --iam-account=pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com \
  --project=YOUR-GCP-PROJECT-ID

# Store credentials in Secret Manager
gcloud secrets create google-drive-credentials \
  --data-file=drive-credentials.json \
  --replication-policy="automatic" \
  --project=YOUR-GCP-PROJECT-ID

# Grant access to service account
gcloud secrets add-iam-policy-binding google-drive-credentials \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR-GCP-PROJECT-ID

# Clean up local credentials
rm drive-credentials.json
```

### Configure Shared Drive Access

Instead of domain-wide delegation, we use a Shared Drive which provides simpler access management and better team collaboration.

**Shared Drive ID:** `0AOEEIstP54k2Uk9PVA`

**Steps to add service account to Shared Drive:**

1. Go to [Google Drive](https://drive.google.com)
2. Navigate to **Shared drives** in the left sidebar
3. Right-click on the PDP Automation Shared Drive
4. Click **Manage members**
5. Add the service account email: `pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com`
6. Set role to **Content Manager** (can add/edit/move files and folders)
7. Click **Send**

**Benefits of Shared Drive approach:**
- No Google Workspace admin approval required
- All files are owned by the Shared Drive (not individual users)
- Files remain accessible even if original uploader leaves
- Simpler permission management via Shared Drive membership
- Service account can create, edit, and organize files directly
- Team members automatically have access through the Shared Drive

## Shared Drive Structure

The Shared Drive serves as the root folder for all PDP Automation assets:

```
PDP Automation (Shared Drive: 0AOEEIstP54k2Uk9PVA)
├── Projects/
│   ├── Project Alpha/
│   │   ├── Images/
│   │   └── Floor Plans/
│   └── Project Beta/
├── Templates/
└── Archive/
```

## Installation and Configuration

### Install Dependencies

```bash
# Install Google Drive API client
pip install google-api-python-client>=2.0.0
pip install google-auth>=2.0.0
pip install google-auth-oauthlib>=1.0.0
pip install google-auth-httplib2>=0.1.0
```

### Backend Configuration

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Google Drive Configuration
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = "credentials/drive-credentials.json"
    GOOGLE_WORKSPACE_DOMAIN: str = "your-domain.com"

    # Shared Drive Configuration
    GOOGLE_SHARED_DRIVE_ID: str = "0AOEEIstP54k2Uk9PVA"

    # Upload settings (auto-share not needed for Shared Drive - members have access)
    DRIVE_DEFAULT_SHARE_ROLE: str = "reader"
    DRIVE_AUTO_SHARE: bool = False  # Not needed for Shared Drive

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## Drive Service Implementation

```python
# backend/app/services/drive_service.py
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional
import io
import asyncio
from app.core.config import settings
from app.core.logging import logger

class DriveService:
    """Service for Google Drive operations"""

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self):
        self._service = None
        self._credentials = None

    @property
    def service(self):
        """Get or create Drive API service"""
        if self._service is None:
            self._credentials = Credentials.from_service_account_file(
                settings.GOOGLE_DRIVE_CREDENTIALS_PATH,
                scopes=self.SCOPES
            )
            self._service = build('drive', 'v3', credentials=self._credentials)
        return self._service

    async def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> str:
        """
        Create a new folder in Google Drive (Shared Drive).

        Args:
            folder_name: Name of the folder
            parent_folder_id: Parent folder ID (uses Shared Drive root if None)

        Returns:
            Folder ID
        """
        parent_id = parent_folder_id or settings.GOOGLE_SHARED_DRIVE_ID

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }

        try:
            loop = asyncio.get_event_loop()
            folder = await loop.run_in_executor(
                None,
                lambda: self.service.files().create(
                    body=file_metadata,
                    fields='id, webViewLink'
                ).execute()
            )

            folder_id = folder.get('id')
            logger.info(f"Created folder: {folder_name} ({folder_id})")

            # Note: Auto-sharing not needed for Shared Drive
            # All Shared Drive members automatically have access

            return folder_id

        except Exception as e:
            logger.error(f"Failed to create folder: {e}")
            raise

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        folder_id: str,
        mime_type: str = 'image/jpeg'
    ) -> Dict[str, str]:
        """
        Upload file to Google Drive.

        Args:
            file_bytes: File content as bytes
            filename: Name for the file
            folder_id: Parent folder ID
            mime_type: MIME type of the file

        Returns:
            Dict with file_id and web_view_link
        """
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }

        media = MediaIoBaseUpload(
            io.BytesIO(file_bytes),
            mimetype=mime_type,
            resumable=True
        )

        try:
            loop = asyncio.get_event_loop()
            file = await loop.run_in_executor(
                None,
                lambda: self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink, webContentLink'
                ).execute()
            )

            logger.info(f"Uploaded file: {filename} ({file.get('id')})")

            return {
                'file_id': file.get('id'),
                'web_view_link': file.get('webViewLink'),
                'web_content_link': file.get('webContentLink')
            }

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def upload_files_batch(
        self,
        files: List[tuple[bytes, str]],
        folder_id: str,
        mime_type: str = 'image/jpeg'
    ) -> List[Dict[str, str]]:
        """
        Upload multiple files concurrently.

        Args:
            files: List of (file_bytes, filename) tuples
            folder_id: Parent folder ID
            mime_type: MIME type of files

        Returns:
            List of file info dicts
        """
        tasks = [
            self.upload_file(file_bytes, filename, folder_id, mime_type)
            for file_bytes, filename in files
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        successful_uploads = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to upload file {files[i][1]}: {result}")
            else:
                successful_uploads.append(result)

        return successful_uploads

    async def create_project_structure(
        self,
        project_name: str,
        images: List[bytes],
        floor_plans: List[bytes]
    ) -> Dict[str, Any]:
        """
        Create complete project folder structure and upload all files.

        Args:
            project_name: Name of the project
            images: List of image bytes
            floor_plans: List of floor plan bytes

        Returns:
            Dict with folder URLs and file links
        """
        try:
            # Create main project folder
            project_folder_id = await self.create_folder(project_name)

            # Create subfolders
            images_folder_id = await self.create_folder('Images', project_folder_id)
            floor_plans_folder_id = await self.create_folder('Floor Plans', project_folder_id)

            # Upload images
            image_files = [
                (img_bytes, f'image_{i+1}.jpg')
                for i, img_bytes in enumerate(images)
            ]
            image_results = await self.upload_files_batch(
                image_files,
                images_folder_id,
                'image/jpeg'
            )

            # Upload floor plans
            floor_plan_files = [
                (fp_bytes, f'floor_plan_{i+1}.jpg')
                for i, fp_bytes in enumerate(floor_plans)
            ]
            floor_plan_results = await self.upload_files_batch(
                floor_plan_files,
                floor_plans_folder_id,
                'image/jpeg'
            )

            logger.info(f"Successfully created project structure for: {project_name}")

            return {
                'project_folder_url': f'https://drive.google.com/drive/folders/{project_folder_id}',
                'images_folder_url': f'https://drive.google.com/drive/folders/{images_folder_id}',
                'floor_plans_folder_url': f'https://drive.google.com/drive/folders/{floor_plans_folder_id}',
                'image_links': [r['web_view_link'] for r in image_results],
                'floor_plan_links': [r['web_view_link'] for r in floor_plan_results]
            }

        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            raise

    async def share_with_domain(
        self,
        file_id: str,
        domain: str,
        role: str = 'reader'
    ) -> None:
        """
        Share file/folder with entire domain.

        Args:
            file_id: File or folder ID
            domain: Domain to share with (e.g., "your-domain.com")
            role: Permission level ('reader', 'writer', 'commenter')
        """
        permission = {
            'type': 'domain',
            'role': role,
            'domain': domain
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id'
                ).execute()
            )

            logger.info(f"Shared {file_id} with domain {domain}")

        except Exception as e:
            logger.error(f"Failed to share with domain: {e}")
            raise

    async def share_with_user(
        self,
        file_id: str,
        email: str,
        role: str = 'reader',
        notify: bool = True
    ) -> None:
        """
        Share file/folder with specific user.

        Args:
            file_id: File or folder ID
            email: User email address
            role: Permission level ('reader', 'writer', 'commenter', 'owner')
            notify: Send email notification
        """
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id',
                    sendNotificationEmail=notify,
                    emailMessage='PDP Automation has shared processed assets with you.'
                ).execute()
            )

            logger.info(f"Shared {file_id} with {email}")

        except Exception as e:
            logger.error(f"Failed to share with user: {e}")
            raise

    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get file/folder information.

        Args:
            file_id: File or folder ID

        Returns:
            File metadata dict
        """
        try:
            loop = asyncio.get_event_loop()
            file = await loop.run_in_executor(
                None,
                lambda: self.service.files().get(
                    fileId=file_id,
                    fields='id, name, mimeType, webViewLink, size, createdTime, modifiedTime'
                ).execute()
            )

            return file

        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise

    async def delete_file(self, file_id: str) -> None:
        """
        Delete file/folder from Drive.

        Args:
            file_id: File or folder ID
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.service.files().delete(fileId=file_id).execute()
            )

            logger.info(f"Deleted file: {file_id}")

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise

# Singleton instance
drive_service = DriveService()
```

## API Endpoint Implementation

```python
# backend/app/api/routes/drive.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.drive_service import drive_service
from app.core.logging import logger
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/api/drive", tags=["drive"])

class CreateProjectFolderRequest(BaseModel):
    project_name: str = Field(..., description="Project name")

class CreateProjectFolderResponse(BaseModel):
    folder_id: str
    folder_url: str
    success: bool

class UploadProjectAssetsRequest(BaseModel):
    project_name: str = Field(..., description="Project name")

class UploadProjectAssetsResponse(BaseModel):
    project_folder_url: str
    images_folder_url: str
    floor_plans_folder_url: str
    image_links: List[str]
    floor_plan_links: List[str]
    success: bool

@router.post("/create-folder", response_model=CreateProjectFolderResponse)
async def create_project_folder(
    request: CreateProjectFolderRequest,
    current_user = Depends(get_current_user)
):
    """
    Create a new project folder in Google Drive.
    """
    try:
        folder_id = await drive_service.create_folder(request.project_name)
        folder_url = f'https://drive.google.com/drive/folders/{folder_id}'

        return CreateProjectFolderResponse(
            folder_id=folder_id,
            folder_url=folder_url,
            success=True
        )

    except Exception as e:
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-project-assets", response_model=UploadProjectAssetsResponse)
async def upload_project_assets(
    project_name: str,
    images: List[UploadFile] = File(...),
    floor_plans: List[UploadFile] = File(...),
    current_user = Depends(get_current_user)
):
    """
    Upload all project assets (images and floor plans) to Google Drive.
    """
    try:
        # Read image files
        image_bytes_list = []
        for img in images:
            content = await img.read()
            image_bytes_list.append(content)

        # Read floor plan files
        floor_plan_bytes_list = []
        for fp in floor_plans:
            content = await fp.read()
            floor_plan_bytes_list.append(content)

        # Create project structure and upload
        result = await drive_service.create_project_structure(
            project_name=project_name,
            images=image_bytes_list,
            floor_plans=floor_plan_bytes_list
        )

        return UploadProjectAssetsResponse(
            **result,
            success=True
        )

    except Exception as e:
        logger.error(f"Failed to upload project assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file-info/{file_id}")
async def get_file_info(
    file_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get information about a file or folder.
    """
    try:
        info = await drive_service.get_file_info(file_id)
        return info

    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Frontend Integration

```typescript
// frontend/src/services/driveService.ts
import { apiClient } from './apiClient';

export interface CreateProjectFolderResponse {
  folder_id: string;
  folder_url: string;
  success: boolean;
}

export interface UploadProjectAssetsResponse {
  project_folder_url: string;
  images_folder_url: string;
  floor_plans_folder_url: string;
  image_links: string[];
  floor_plan_links: string[];
  success: boolean;
}

export class DriveService {
  /**
   * Create project folder in Google Drive
   */
  async createProjectFolder(projectName: string): Promise<CreateProjectFolderResponse> {
    const response = await apiClient.post<CreateProjectFolderResponse>(
      '/api/drive/create-folder',
      { project_name: projectName }
    );
    return response.data;
  }

  /**
   * Upload project assets to Google Drive
   */
  async uploadProjectAssets(
    projectName: string,
    images: File[],
    floorPlans: File[]
  ): Promise<UploadProjectAssetsResponse> {
    const formData = new FormData();
    formData.append('project_name', projectName);

    images.forEach((img) => {
      formData.append('images', img);
    });

    floorPlans.forEach((fp) => {
      formData.append('floor_plans', fp);
    });

    const response = await apiClient.post<UploadProjectAssetsResponse>(
      '/api/drive/upload-project-assets',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Open Drive folder in new tab
   */
  openFolder(folderId: string): void {
    const url = `https://drive.google.com/drive/folders/${folderId}`;
    window.open(url, '_blank');
  }
}

export const driveService = new DriveService();
```

## Folder Structure Pattern

```
PDP Automation - Processed Assets/
├── Project Alpha Downtown/
│   ├── Images/
│   │   ├── image_1.jpg
│   │   ├── image_2.jpg
│   │   └── ...
│   └── Floor Plans/
│       ├── floor_plan_1.jpg
│       ├── floor_plan_2.jpg
│       └── ...
├── Project Beta Marina/
│   ├── Images/
│   └── Floor Plans/
└── ...
```

## Rate Limiting and Quotas

### Google Drive API Quotas

- **Queries per 100 seconds per user:** 1,000
- **Queries per 100 seconds per project:** 10,000
- **File upload size limit:** 5 TB

### Best Practices

1. **Use Batch Upload**
   ```python
   # Upload multiple files concurrently
   await drive_service.upload_files_batch(files, folder_id)
   ```

2. **Implement Retry Logic**
   ```python
   from googleapiclient.errors import HttpError
   import time

   async def upload_with_retry(file_bytes, filename, folder_id, max_retries=3):
       for i in range(max_retries):
           try:
               return await drive_service.upload_file(file_bytes, filename, folder_id)
           except HttpError as e:
               if e.resp.status == 429:  # Rate limit
                   wait = (2 ** i) + random.random()
                   await asyncio.sleep(wait)
               else:
                   raise
   ```

## Error Handling

```python
# backend/app/services/drive_error_handler.py
from googleapiclient.errors import HttpError
from app.core.logging import logger

async def handle_drive_error(func, *args, **kwargs):
    """Handle Google Drive API errors"""
    try:
        return await func(*args, **kwargs)

    except HttpError as error:
        status_code = error.resp.status

        if status_code == 403:
            logger.error("Drive permission denied")
            raise ValueError("Insufficient permissions to access Google Drive")

        elif status_code == 404:
            logger.error("Drive file/folder not found")
            raise ValueError("Requested file or folder does not exist")

        elif status_code == 429:
            logger.warning("Drive rate limit exceeded")
            raise ValueError("Too many requests. Please try again later.")

        elif status_code == 500:
            logger.error("Drive internal server error")
            raise ValueError("Google Drive service error. Please try again.")

        else:
            logger.error(f"Drive API error: {error}")
            raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

## Security Considerations

1. **Service Account Permissions**
   - Add service account to Shared Drive with Content Manager role
   - Only grant `drive.file` scope (not `drive` full access)

2. **Folder Permissions**
   - Share root folder with organization as Viewer
   - Grant service account Editor access
   - Individual project folders inherit permissions

3. **File Validation**
   - Validate file types before upload
   - Check file sizes to prevent abuse
   - Scan for malware (optional)

4. **Access Logging**
   - Log all uploads and folder creations
   - Monitor unusual activity
   - Regular permission audits

## Cost Optimization

Google Drive storage is **included in Google Workspace**:
- Business Starter: 30 GB per user
- Business Standard: 2 TB per user
- Business Plus: 5 TB per user

**Tips:**
1. Compress images before upload (maintain quality)
2. Delete old project folders periodically
3. Use organization-wide sharing to avoid duplicate uploads

## Troubleshooting

### Issue: "Permission denied" on folder creation

```python
# Verify service account is a member of the Shared Drive:
# 1. Go to Google Drive > Shared drives
# 2. Right-click on PDP Automation Shared Drive > Manage members
# 3. Verify pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com is listed
# 4. Ensure role is "Content Manager" or higher

# For API operations on Shared Drive, ensure supportsAllDrives=True is set
```

### Issue: Upload fails silently

```python
# Add detailed error logging
try:
    result = await drive_service.upload_file(...)
except Exception as e:
    logger.error(f"Upload failed: {type(e).__name__}: {str(e)}")
    raise
```

### Issue: Folder not visible to organization

```python
# Verify domain sharing
await drive_service.share_with_domain(
    folder_id,
    'your-domain.com',
    role='reader'
)

# Check sharing settings in Drive UI
```

## Next Steps

- Configure [Google Sheets Integration](GOOGLE_SHEETS_INTEGRATION.md) for content export
- Set up [Cloud Storage Patterns](CLOUD_STORAGE_PATTERNS.md) for efficient file handling
- Review [Google OAuth Setup](GOOGLE_OAUTH_SETUP.md) for user authentication

## References

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Google Drive Python Quickstart](https://developers.google.com/drive/api/v3/quickstart/python)
- [Drive API Sharing Files](https://developers.google.com/drive/api/v3/about-sharing)
