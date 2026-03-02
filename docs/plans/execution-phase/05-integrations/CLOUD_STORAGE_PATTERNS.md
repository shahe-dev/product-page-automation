# Cloud Storage Patterns

## Overview

This guide covers best practices and patterns for using Google Cloud Storage (GCS) in PDP Automation v.3. Learn how to efficiently store, retrieve, and manage files including PDFs, images, and processed assets.

**Bucket:** `gs://pdp-automation-assets-dev`
**Region:** `us-central1`

## Bucket Architecture

### Folder Structure

```
pdp-automation-assets-dev/
├── uploads/                    # Original PDF uploads
│   └── {job_id}/
│       └── original.pdf
├── processed/                  # Processed assets
│   └── {project_id}/
│       ├── images/
│       │   ├── interior/
│       │   │   ├── img_001.jpg
│       │   │   └── ...
│       │   ├── exterior/
│       │   │   ├── img_001.jpg
│       │   │   └── ...
│       │   ├── amenity/
│       │   └── logo/
│       ├── floor_plans/
│       │   ├── fp_001.jpg
│       │   └── ...
│       └── output.zip         # Downloadable package
└── temp/                      # Temporary files (auto-delete 24h)
    └── {job_id}/
        ├── extracted_pages/
        └── intermediate_files/
```

### Bucket Configuration

```bash
# Create bucket
gcloud storage buckets create gs://pdp-automation-assets-dev \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --project=YOUR-GCP-PROJECT-ID

# Set lifecycle policy
cat > lifecycle.json << 'EOF'
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
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["processed/"]
        }
      }
    ]
  }
}
EOF

gcloud storage buckets update gs://pdp-automation-assets-dev \
  --lifecycle-file=lifecycle.json
```

## Installation and Configuration

### Install Dependencies

```bash
pip install google-cloud-storage>=2.10.0
```

### Backend Configuration

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # GCS Configuration
    GOOGLE_CLOUD_PROJECT: str = "YOUR-GCP-PROJECT-ID"
    GCS_BUCKET_NAME: str = "pdp-automation-assets-dev"
    GCS_LOCATION: str = "us-central1"

    # Storage settings
    GCS_MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100 MB
    GCS_SIGNED_URL_EXPIRATION: int = 3600  # 1 hour
    GCS_CHUNK_SIZE: int = 5 * 1024 * 1024  # 5 MB

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## Storage Service Implementation

```python
# backend/app/services/storage_service.py
from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError
from datetime import timedelta
from typing import Optional, List, BinaryIO
import io
import asyncio
from app.core.config import settings
from app.core.logging import logger

class StorageService:
    """Service for Google Cloud Storage operations"""

    def __init__(self):
        self._client = None
        self._bucket = None

    @property
    def client(self) -> storage.Client:
        """Get or create storage client"""
        if self._client is None:
            self._client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
        return self._client

    @property
    def bucket(self) -> storage.Bucket:
        """Get bucket instance"""
        if self._bucket is None:
            self._bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
        return self._bucket

    async def upload_file(
        self,
        file_bytes: bytes,
        blob_path: str,
        content_type: str = 'application/octet-stream',
        make_public: bool = False
    ) -> str:
        """
        Upload file to GCS.

        Args:
            file_bytes: File content as bytes
            blob_path: Destination path in bucket (e.g., "uploads/job123/file.pdf")
            content_type: MIME type
            make_public: Whether to make file publicly accessible

        Returns:
            Public URL or signed URL
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.upload_from_string(
                    file_bytes,
                    content_type=content_type
                )
            )

            logger.info(f"Uploaded file to: gs://{settings.GCS_BUCKET_NAME}/{blob_path}")

            if make_public:
                blob.make_public()
                return blob.public_url
            else:
                return f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    async def upload_file_stream(
        self,
        file_stream: BinaryIO,
        blob_path: str,
        content_type: str = 'application/octet-stream',
        chunk_size: Optional[int] = None
    ) -> str:
        """
        Upload file from stream (memory efficient for large files).

        Args:
            file_stream: File-like object
            blob_path: Destination path
            content_type: MIME type
            chunk_size: Upload chunk size (default: 5MB)

        Returns:
            GCS path
        """
        blob = self.bucket.blob(blob_path)
        chunk_size = chunk_size or settings.GCS_CHUNK_SIZE

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.upload_from_file(
                    file_stream,
                    content_type=content_type,
                    size=chunk_size
                )
            )

            logger.info(f"Uploaded stream to: gs://{settings.GCS_BUCKET_NAME}/{blob_path}")
            return f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

        except Exception as e:
            logger.error(f"Failed to upload stream: {e}")
            raise

    async def download_file(self, blob_path: str) -> bytes:
        """
        Download file from GCS.

        Args:
            blob_path: Source path in bucket

        Returns:
            File content as bytes
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                blob.download_as_bytes
            )

            logger.info(f"Downloaded file from: gs://{settings.GCS_BUCKET_NAME}/{blob_path}")
            return content

        except NotFound:
            logger.error(f"File not found: {blob_path}")
            raise FileNotFoundError(f"File not found: {blob_path}")
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise

    async def download_file_stream(
        self,
        blob_path: str,
        destination_stream: BinaryIO
    ) -> None:
        """
        Download file to stream (memory efficient).

        Args:
            blob_path: Source path in bucket
            destination_stream: Writable file-like object
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.download_to_file(destination_stream)
            )

            logger.info(f"Downloaded stream from: gs://{settings.GCS_BUCKET_NAME}/{blob_path}")

        except NotFound:
            logger.error(f"File not found: {blob_path}")
            raise FileNotFoundError(f"File not found: {blob_path}")
        except Exception as e:
            logger.error(f"Failed to download stream: {e}")
            raise

    async def generate_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int = 60,
        method: str = "GET"
    ) -> str:
        """
        Generate signed URL for temporary access.

        Args:
            blob_path: Path to file in bucket
            expiration_minutes: URL validity in minutes
            method: HTTP method (GET, PUT, POST, DELETE)

        Returns:
            Signed URL
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                lambda: blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(minutes=expiration_minutes),
                    method=method
                )
            )

            logger.info(f"Generated signed URL for: {blob_path}")
            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise

    async def delete_file(self, blob_path: str) -> None:
        """
        Delete file from GCS.

        Args:
            blob_path: Path to file in bucket
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.delete)

            logger.info(f"Deleted file: gs://{settings.GCS_BUCKET_NAME}/{blob_path}")

        except NotFound:
            logger.warning(f"File not found for deletion: {blob_path}")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    async def delete_folder(self, folder_prefix: str) -> int:
        """
        Delete all files in a folder (prefix).

        Args:
            folder_prefix: Folder path (e.g., "temp/job123/")

        Returns:
            Number of files deleted
        """
        try:
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.bucket.list_blobs(prefix=folder_prefix))
            )

            delete_tasks = [
                loop.run_in_executor(None, blob.delete)
                for blob in blobs
            ]

            await asyncio.gather(*delete_tasks)

            logger.info(f"Deleted {len(blobs)} files from: {folder_prefix}")
            return len(blobs)

        except Exception as e:
            logger.error(f"Failed to delete folder: {e}")
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[dict]:
        """
        List files in bucket.

        Args:
            prefix: Filter by prefix (folder path)
            max_results: Maximum number of results

        Returns:
            List of file info dicts
        """
        try:
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.bucket.list_blobs(
                    prefix=prefix,
                    max_results=max_results
                ))
            )

            files = [
                {
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'public_url': blob.public_url if blob.public_url else None
                }
                for blob in blobs
            ]

            return files

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise

    async def file_exists(self, blob_path: str) -> bool:
        """
        Check if file exists in bucket.

        Args:
            blob_path: Path to file

        Returns:
            True if file exists
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, blob.exists)
            return exists

        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False

    async def copy_file(
        self,
        source_blob_path: str,
        destination_blob_path: str
    ) -> str:
        """
        Copy file within bucket.

        Args:
            source_blob_path: Source file path
            destination_blob_path: Destination file path

        Returns:
            Destination GCS path
        """
        source_blob = self.bucket.blob(source_blob_path)
        destination_blob = self.bucket.blob(destination_blob_path)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.bucket.copy_blob(
                    source_blob,
                    self.bucket,
                    destination_blob.name
                )
            )

            logger.info(f"Copied file: {source_blob_path} -> {destination_blob_path}")
            return f"gs://{settings.GCS_BUCKET_NAME}/{destination_blob_path}"

        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            raise

    async def move_file(
        self,
        source_blob_path: str,
        destination_blob_path: str
    ) -> str:
        """
        Move file within bucket (copy + delete).

        Args:
            source_blob_path: Source file path
            destination_blob_path: Destination file path

        Returns:
            Destination GCS path
        """
        # Copy file
        await self.copy_file(source_blob_path, destination_blob_path)

        # Delete source
        await self.delete_file(source_blob_path)

        logger.info(f"Moved file: {source_blob_path} -> {destination_blob_path}")
        return f"gs://{settings.GCS_BUCKET_NAME}/{destination_blob_path}"

    async def get_file_metadata(self, blob_path: str) -> dict:
        """
        Get file metadata.

        Args:
            blob_path: Path to file

        Returns:
            Metadata dict
        """
        blob = self.bucket.blob(blob_path)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.reload)

            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'storage_class': blob.storage_class,
                'metadata': blob.metadata
            }

        except NotFound:
            logger.error(f"File not found: {blob_path}")
            raise FileNotFoundError(f"File not found: {blob_path}")
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            raise

# Singleton instance
storage_service = StorageService()
```

## Common Use Cases

### 1. Upload PDF for Processing

```python
# backend/app/services/job_service.py
from app.services.storage_service import storage_service
import uuid

async def upload_pdf_for_job(pdf_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """
    Upload PDF and return job ID and GCS path.
    """
    job_id = str(uuid.uuid4())
    blob_path = f"uploads/{job_id}/original.pdf"

    gcs_path = await storage_service.upload_file(
        file_bytes=pdf_bytes,
        blob_path=blob_path,
        content_type='application/pdf'
    )

    return job_id, gcs_path
```

### 2. Store Processed Images by Category

```python
async def save_processed_images(
    project_id: str,
    images: dict[str, list[bytes]]  # category -> list of image bytes
) -> dict[str, list[str]]:
    """
    Save categorized images to GCS.

    Args:
        project_id: Project identifier
        images: Dict mapping category to list of image bytes

    Returns:
        Dict mapping category to list of GCS paths
    """
    results = {}

    for category, image_list in images.items():
        category_paths = []

        for i, img_bytes in enumerate(image_list):
            blob_path = f"processed/{project_id}/images/{category}/img_{i+1:03d}.jpg"

            gcs_path = await storage_service.upload_file(
                file_bytes=img_bytes,
                blob_path=blob_path,
                content_type='image/jpeg'
            )

            category_paths.append(gcs_path)

        results[category] = category_paths

    return results
```

### 3. Generate Temporary Download URL

```python
async def get_download_url_for_output(project_id: str) -> str:
    """
    Generate temporary download URL for output ZIP.
    """
    blob_path = f"processed/{project_id}/output.zip"

    # Generate 1-hour signed URL
    signed_url = await storage_service.generate_signed_url(
        blob_path=blob_path,
        expiration_minutes=60,
        method="GET"
    )

    return signed_url
```

### 4. Clean Up Temporary Files

```python
async def cleanup_temp_files(job_id: str) -> None:
    """
    Delete all temporary files for a job.
    """
    folder_prefix = f"temp/{job_id}/"

    deleted_count = await storage_service.delete_folder(folder_prefix)

    logger.info(f"Cleaned up {deleted_count} temp files for job {job_id}")
```

### 5. Stream Large File Upload

```python
from fastapi import UploadFile

async def handle_large_pdf_upload(file: UploadFile, job_id: str) -> str:
    """
    Handle large PDF upload using streaming.
    """
    blob_path = f"uploads/{job_id}/original.pdf"

    gcs_path = await storage_service.upload_file_stream(
        file_stream=file.file,
        blob_path=blob_path,
        content_type='application/pdf',
        chunk_size=10 * 1024 * 1024  # 10 MB chunks
    )

    return gcs_path
```

## Performance Optimization

### 1. Parallel Uploads

```python
async def upload_images_parallel(
    project_id: str,
    images: list[bytes],
    category: str
) -> list[str]:
    """
    Upload multiple images in parallel.
    """
    async def upload_one(img_bytes: bytes, index: int) -> str:
        blob_path = f"processed/{project_id}/images/{category}/img_{index+1:03d}.jpg"
        return await storage_service.upload_file(
            file_bytes=img_bytes,
            blob_path=blob_path,
            content_type='image/jpeg'
        )

    tasks = [upload_one(img, i) for i, img in enumerate(images)]
    results = await asyncio.gather(*tasks)

    return results
```

### 2. Batch Delete

```python
async def batch_delete_files(blob_paths: list[str]) -> int:
    """
    Delete multiple files concurrently.
    """
    tasks = [storage_service.delete_file(path) for path in blob_paths]
    await asyncio.gather(*tasks, return_exceptions=True)

    return len(blob_paths)
```

### 3. Caching File Metadata

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1000)
def get_cached_file_exists(blob_path: str, timestamp: int) -> bool:
    """
    Cache file existence checks for 5 minutes.
    timestamp is unix timestamp rounded to 5 minutes.
    """
    return asyncio.run(storage_service.file_exists(blob_path))

async def check_file_with_cache(blob_path: str) -> bool:
    """
    Check if file exists with 5-minute cache.
    """
    timestamp = int(datetime.now().timestamp() // 300)  # 5-minute buckets
    return get_cached_file_exists(blob_path, timestamp)
```

## Error Handling

```python
# backend/app/services/storage_error_handler.py
from google.cloud.exceptions import NotFound, GoogleCloudError, Forbidden
from app.core.logging import logger

async def handle_storage_error(func, *args, **kwargs):
    """Handle GCS errors with appropriate retry logic"""

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)

        except NotFound as e:
            logger.error(f"File not found: {e}")
            raise FileNotFoundError("Requested file does not exist")

        except Forbidden as e:
            logger.error(f"Permission denied: {e}")
            raise PermissionError("Insufficient permissions to access storage")

        except GoogleCloudError as e:
            if attempt == max_retries - 1:
                logger.error(f"GCS error after {max_retries} attempts: {e}")
                raise
            else:
                logger.warning(f"GCS error, retrying (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay * (attempt + 1))

        except Exception as e:
            logger.error(f"Unexpected storage error: {e}")
            raise
```

## Cost Optimization

### Storage Classes

| Class | Cost/GB/Month | Use Case |
|-------|---------------|----------|
| Standard | $0.020 | Frequently accessed files |
| Nearline | $0.010 | Monthly access |
| Coldline | $0.004 | Quarterly access |
| Archive | $0.0012 | Yearly access |

### Best Practices

1. **Use Lifecycle Policies**
   ```json
   {
     "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
     "condition": {"age": 90, "matchesPrefix": ["processed/"]}
   }
   ```

2. **Delete Temporary Files**
   ```python
   # Auto-delete temp files after 24 hours
   {"action": {"type": "Delete"}, "condition": {"age": 1, "matchesPrefix": ["temp/"]}}
   ```

3. **Compress Files**
   ```python
   import gzip

   async def upload_compressed(data: bytes, blob_path: str):
       compressed = gzip.compress(data)
       await storage_service.upload_file(
           file_bytes=compressed,
           blob_path=blob_path,
           content_type='application/gzip'
       )
   ```

4. **Use Regional Buckets**
   - Single region (us-central1) is cheaper than multi-region
   - Place bucket close to Cloud Run services

## Security Best Practices

1. **Uniform Bucket-Level Access**
   ```bash
   gcloud storage buckets update gs://pdp-automation-assets-dev \
     --uniform-bucket-level-access
   ```

2. **Use Signed URLs**
   ```python
   # Generate temporary access URL instead of making files public
   url = await storage_service.generate_signed_url(blob_path, expiration_minutes=60)
   ```

3. **Validate File Types**
   ```python
   ALLOWED_MIME_TYPES = {'application/pdf', 'image/jpeg', 'image/png'}

   def validate_file_type(content_type: str):
       if content_type not in ALLOWED_MIME_TYPES:
           raise ValueError(f"Invalid file type: {content_type}")
   ```

4. **Scan for Malware** (optional)
   ```python
   # Integrate with Cloud Security Scanner or third-party service
   async def scan_file(blob_path: str) -> bool:
       # Implement virus scanning
       pass
   ```

## Monitoring and Logging

```python
# Log all storage operations
import time

async def upload_with_logging(file_bytes: bytes, blob_path: str):
    start_time = time.time()

    try:
        result = await storage_service.upload_file(file_bytes, blob_path)

        elapsed = time.time() - start_time
        logger.info(f"Upload successful: {blob_path} ({len(file_bytes)} bytes in {elapsed:.2f}s)")

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Upload failed: {blob_path} after {elapsed:.2f}s - {e}")
        raise
```

## Troubleshooting

### Issue: Upload fails with "Permission denied"

```bash
# Verify service account has storage.objectAdmin role
gcloud projects add-iam-policy-binding YOUR-GCP-PROJECT-ID \
  --member="serviceAccount:pdp-automation-sa@YOUR-GCP-PROJECT-ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### Issue: Large file upload times out

```python
# Use streaming upload for files > 10 MB
await storage_service.upload_file_stream(
    file_stream=file.file,
    blob_path=blob_path,
    chunk_size=10 * 1024 * 1024  # 10 MB chunks
)
```

### Issue: File not found after upload

```python
# Add retry with exponential backoff
import asyncio

async def upload_with_retry(file_bytes: bytes, blob_path: str, max_retries=3):
    for i in range(max_retries):
        try:
            await storage_service.upload_file(file_bytes, blob_path)

            # Verify upload
            await asyncio.sleep(1)
            exists = await storage_service.file_exists(blob_path)

            if exists:
                return
            else:
                raise Exception("File not found after upload")

        except Exception as e:
            if i == max_retries - 1:
                raise
            await asyncio.sleep(2 ** i)
```

## Next Steps

- Configure [Google Drive Integration](GOOGLE_DRIVE_INTEGRATION.md) for organization-wide file sharing
- Review [Google Cloud Setup](GOOGLE_CLOUD_SETUP.md) for infrastructure configuration
- Set up [Anthropic API Integration](ANTHROPIC_API_INTEGRATION.md) for AI processing

## References

- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Python Client Library](https://googleapis.dev/python/storage/latest/index.html)
- [GCS Best Practices](https://cloud.google.com/storage/docs/best-practices)
- [Storage Pricing](https://cloud.google.com/storage/pricing)
