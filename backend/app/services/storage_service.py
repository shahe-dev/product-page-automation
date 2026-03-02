"""
Google Cloud Storage service for PDP Automation v.3

Provides async-compatible interface to GCS for file management:
- Upload/download operations (direct and resumable)
- Signed URL generation
- File and folder management
- Lifecycle-aware folder structure

Folder structure:
  uploads/{job_id}/original.pdf
  processed/{project_id}/images/{category}/img_001.jpg
  processed/{project_id}/floor_plans/fp_001.jpg
  processed/{project_id}/output.zip
  temp/{job_id}/extracted_pages/
  temp/{job_id}/intermediate_files/
"""

import asyncio
import logging
import mimetypes
import os
import shutil
from datetime import timedelta
import threading
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound
from google.cloud.storage import Blob, Bucket

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# File size threshold for resumable upload (5MB)
RESUMABLE_UPLOAD_THRESHOLD = 5 * 1024 * 1024

# Default signed URL expiry (60 minutes)
DEFAULT_SIGNED_URL_EXPIRY = 60


class StorageService:
    """
    Google Cloud Storage service with async compatibility.

    Wraps the synchronous GCS Python SDK with async/await interface
    using run_in_executor for non-blocking I/O.
    """

    def __init__(self):
        """Initialize storage service (lazy-loaded)."""
        self._client: Optional[storage.Client] = None
        self._bucket: Optional[Bucket] = None
        self._client_lock = threading.Lock()
        self._bucket_lock = threading.Lock()
        self._settings = get_settings()
        logger.info(
            "StorageService initialized (lazy-load): bucket=%s, project=%s",
            self._settings.GCS_BUCKET_NAME,
            self._settings.GCP_PROJECT_ID,
        )

    @property
    def client(self) -> Optional[storage.Client]:
        """Get or create GCS client (lazy initialization). Returns None if not available."""
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    try:
                        self._client = storage.Client(
                            project=self._settings.GCP_PROJECT_ID
                        )
                        logger.info(
                            "GCS client initialized for project: %s",
                            self._settings.GCP_PROJECT_ID,
                        )
                    except Exception as e:
                        logger.warning(
                            "GCS client not available (will use local fallback): %s",
                            str(e),
                        )
                        return None  # Don't cache None -- retry on next access

        return self._client

    @property
    def bucket(self) -> Bucket:
        """Get or create bucket reference (lazy initialization, thread-safe)."""
        if self._bucket is None:
            with self._bucket_lock:
                if self._bucket is None:
                    if self.client is None:
                        raise RuntimeError(
                            "GCS client not available; cannot access bucket"
                        )
                    bucket_name = self._settings.GCS_BUCKET_NAME
                    self._bucket = self.client.bucket(bucket_name)
                    # Skip exists() check - it requires storage.buckets.get permission
                    # which Storage Object Admin doesn't have. Errors will surface
                    # on actual object operations instead.
                    logger.info("GCS bucket reference created: %s", bucket_name)

        return self._bucket

    def _get_blob(self, blob_path: str) -> Blob:
        """Get blob reference for a given path."""
        return self.bucket.blob(blob_path)

    def _detect_content_type(self, file_path: str) -> str:
        """
        Detect MIME type from file extension.

        Args:
            file_path: File path or name

        Returns:
            MIME type string (defaults to 'application/octet-stream')
        """
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or "application/octet-stream"

    async def upload_file(
        self,
        source_file: str | Path | bytes | BinaryIO,
        destination_blob_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Upload file to GCS (auto-selects direct vs resumable based on size).
        Falls back to local filesystem if GCS is not available.

        Args:
            source_file: Local file path, bytes, or file-like object
            destination_blob_path: Destination path in bucket (e.g., 'uploads/job_123/file.pdf')
            content_type: MIME type (auto-detected if None)
            metadata: Custom metadata dict

        Returns:
            GCS blob path or local file path (with file:// prefix for local)

        Raises:
            GoogleCloudError: On upload failure
        """
        # Local fallback if GCS not available
        if self.client is None:
            return await self._upload_local(source_file, destination_blob_path)

        loop = asyncio.get_running_loop()

        def _upload():
            blob = self._get_blob(destination_blob_path)

            # Auto-detect content type if not provided
            if content_type is None:
                if isinstance(source_file, (str, Path)):
                    detected_type = self._detect_content_type(str(source_file))
                else:
                    detected_type = "application/octet-stream"
            else:
                detected_type = content_type

            # Set metadata
            if metadata:
                blob.metadata = metadata

            # Upload from different source types
            if isinstance(source_file, bytes):
                # Direct upload from bytes
                blob.upload_from_string(
                    source_file,
                    content_type=detected_type,
                    timeout=300,
                )
                logger.info(
                    "Uploaded bytes to GCS: %s (%d bytes)",
                    destination_blob_path,
                    len(source_file),
                )
            elif isinstance(source_file, (str, Path)):
                # Upload from file path
                file_path = Path(source_file)
                file_size = file_path.stat().st_size

                # Use resumable upload for large files
                if file_size > RESUMABLE_UPLOAD_THRESHOLD:
                    blob.upload_from_filename(
                        str(file_path),
                        content_type=detected_type,
                        timeout=600,
                    )
                    logger.info(
                        "Uploaded file (resumable) to GCS: %s (%d bytes)",
                        destination_blob_path,
                        file_size,
                    )
                else:
                    blob.upload_from_filename(
                        str(file_path),
                        content_type=detected_type,
                        timeout=120,
                    )
                    logger.info(
                        "Uploaded file (direct) to GCS: %s (%d bytes)",
                        destination_blob_path,
                        file_size,
                    )
            else:
                # Upload from file-like object
                blob.upload_from_file(
                    source_file,
                    content_type=detected_type,
                    timeout=600,
                )
                logger.info(
                    "Uploaded file-like object to GCS: %s",
                    destination_blob_path,
                )

            return destination_blob_path

        try:
            return await loop.run_in_executor(None, _upload)
        except (GoogleCloudError, ConnectionError, TimeoutError, OSError) as e:
            logger.error(
                "Failed to upload to GCS: %s - %s",
                destination_blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def _upload_local(
        self,
        source_file: str | Path | bytes | BinaryIO,
        destination_blob_path: str,
    ) -> str:
        """
        Upload file to local filesystem as fallback when GCS unavailable.

        Args:
            source_file: Local file path, bytes, or file-like object
            destination_blob_path: Destination path (e.g., 'uploads/job_123/file.pdf')

        Returns:
            Local file path with file:// prefix
        """
        loop = asyncio.get_running_loop()

        def _upload():
            # Create local path
            local_path = Path("./uploads") / destination_blob_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Handle different source types
            if isinstance(source_file, bytes):
                local_path.write_bytes(source_file)
                file_size = len(source_file)
            elif isinstance(source_file, (str, Path)):
                shutil.copy(str(source_file), str(local_path))
                file_size = Path(source_file).stat().st_size
            else:
                # File-like object
                with open(local_path, 'wb') as f:
                    shutil.copyfileobj(source_file, f)
                file_size = local_path.stat().st_size

            logger.warning(
                "Uploaded to local filesystem (GCS unavailable): %s (%d bytes)",
                local_path,
                file_size
            )
            return f"file://{local_path.absolute()}"

        return await loop.run_in_executor(None, _upload)

    async def download_file(
        self,
        blob_path: str,
        destination_file: Optional[str | Path] = None,
    ) -> bytes | None:
        """
        Download file from GCS.

        Args:
            blob_path: Source blob path in bucket
            destination_file: Local destination path (if None, returns bytes)

        Returns:
            File bytes if destination_file is None, otherwise None

        Raises:
            NotFound: If blob does not exist
            GoogleCloudError: On download failure
        """
        loop = asyncio.get_running_loop()

        def _download():
            blob = self._get_blob(blob_path)

            if not blob.exists():
                logger.warning("Blob not found: %s", blob_path)
                raise NotFound(f"Blob not found: {blob_path}")

            if destination_file:
                # Download to file
                dest_path = Path(destination_file)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(
                    str(dest_path),
                )
                logger.info(
                    "Downloaded from GCS to file: %s -> %s",
                    blob_path,
                    dest_path,
                )
                return None
            else:
                # Download to bytes
                file_bytes = blob.download_as_bytes()
                logger.info(
                    "Downloaded from GCS as bytes: %s (%d bytes)",
                    blob_path,
                    len(file_bytes),
                )
                return file_bytes

        try:
            return await loop.run_in_executor(None, _download)
        except NotFound:
            raise
        except GoogleCloudError as e:
            logger.error(
                "Failed to download from GCS: %s - %s",
                blob_path,
                str(e),
                exc_info=True,
            )
            raise

    # Maximum signed URL expiry: 7 days (GCS V4 limit)
    MAX_SIGNED_URL_EXPIRY_MINUTES = 10080

    async def generate_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int = DEFAULT_SIGNED_URL_EXPIRY,
        method: str = "GET",
    ) -> str:
        """
        Generate signed URL for temporary access to blob.

        Args:
            blob_path: Blob path in bucket
            expiration_minutes: URL validity period (default: 60 minutes, max: 10080 / 7 days)
            method: HTTP method (GET, PUT, etc.)

        Returns:
            Signed URL string

        Raises:
            ValueError: If expiration_minutes is out of valid range
            NotFound: If blob does not exist
            GoogleCloudError: On URL generation failure
        """
        if expiration_minutes <= 0 or expiration_minutes > self.MAX_SIGNED_URL_EXPIRY_MINUTES:
            raise ValueError(
                f"expiration_minutes must be between 1 and {self.MAX_SIGNED_URL_EXPIRY_MINUTES}, "
                f"got {expiration_minutes}"
            )

        loop = asyncio.get_running_loop()

        def _generate_url():
            blob = self._get_blob(blob_path)

            if not blob.exists():
                logger.warning("Blob not found for signed URL: %s", blob_path)
                raise NotFound(f"Blob not found: {blob_path}")

            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method=method,
            )
            logger.info(
                "Generated signed URL: %s (expires in %d minutes)",
                blob_path,
                expiration_minutes,
            )
            return url

        try:
            return await loop.run_in_executor(None, _generate_url)
        except NotFound:
            raise
        except GoogleCloudError as e:
            logger.error(
                "Failed to generate signed URL: %s - %s",
                blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete a file from GCS.

        Args:
            blob_path: Blob path to delete

        Returns:
            True if deleted, False if not found

        Raises:
            GoogleCloudError: On deletion failure (except NotFound)
        """
        loop = asyncio.get_running_loop()

        def _delete():
            blob = self._get_blob(blob_path)
            try:
                blob.delete()
                logger.info("Deleted blob: %s", blob_path)
                return True
            except NotFound:
                logger.warning("Blob not found for deletion: %s", blob_path)
                return False

        try:
            return await loop.run_in_executor(None, _delete)
        except GoogleCloudError as e:
            logger.error(
                "Failed to delete blob: %s - %s",
                blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def delete_folder(self, prefix: str) -> int:
        """
        Delete all blobs with a given prefix (folder deletion).

        Args:
            prefix: Folder prefix (e.g., 'temp/job_123/')

        Returns:
            Number of blobs deleted

        Raises:
            GoogleCloudError: On deletion failure
        """
        loop = asyncio.get_running_loop()

        def _delete_folder():
            # Ensure prefix ends with /
            folder_prefix = prefix if prefix.endswith("/") else f"{prefix}/"

            blobs = list(self.bucket.list_blobs(prefix=folder_prefix))
            count = 0

            for blob in blobs:
                try:
                    blob.delete()
                    count += 1
                except NotFound:
                    logger.warning("Blob already deleted: %s", blob.name)
                except GoogleCloudError as e:
                    logger.error(
                        "Failed to delete blob %s: %s",
                        blob.name,
                        str(e),
                    )
                    raise

            logger.info(
                "Deleted folder: %s (%d blobs)",
                folder_prefix,
                count,
            )
            return count

        try:
            return await loop.run_in_executor(None, _delete_folder)
        except GoogleCloudError as e:
            logger.error(
                "Failed to delete folder: %s - %s",
                prefix,
                str(e),
                exc_info=True,
            )
            raise

    async def list_files(
        self,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
    ) -> List[str]:
        """
        List files in bucket with optional prefix filter.

        Args:
            prefix: Filter by prefix (e.g., 'uploads/job_123/')
            delimiter: Delimiter for directory-like listing (e.g., '/')

        Returns:
            List of blob paths
        """
        loop = asyncio.get_running_loop()

        def _list():
            blobs = self.bucket.list_blobs(prefix=prefix, delimiter=delimiter)
            blob_names = [blob.name for blob in blobs]
            logger.info(
                "Listed files: prefix=%s, count=%d",
                prefix or "(all)",
                len(blob_names),
            )
            return blob_names

        try:
            return await loop.run_in_executor(None, _list)
        except GoogleCloudError as e:
            logger.error(
                "Failed to list files: prefix=%s - %s",
                prefix,
                str(e),
                exc_info=True,
            )
            raise

    async def file_exists(self, blob_path: str) -> bool:
        """
        Check if a file exists in GCS.

        Args:
            blob_path: Blob path to check

        Returns:
            True if exists, False otherwise
        """
        loop = asyncio.get_running_loop()

        def _exists():
            blob = self._get_blob(blob_path)
            exists = blob.exists()
            logger.debug("Blob exists check: %s = %s", blob_path, exists)
            return exists

        try:
            return await loop.run_in_executor(None, _exists)
        except GoogleCloudError as e:
            logger.error(
                "Failed to check blob existence: %s - %s",
                blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def get_metadata(self, blob_path: str) -> Dict[str, Any]:
        """
        Get blob metadata.

        Args:
            blob_path: Blob path

        Returns:
            Metadata dict with keys: name, size, content_type, created, updated, metadata

        Raises:
            NotFound: If blob does not exist
        """
        loop = asyncio.get_running_loop()

        def _get_metadata():
            blob = self._get_blob(blob_path)
            blob.reload()  # Fetch latest metadata from GCS

            metadata = {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "metadata": blob.metadata or {},
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
            }
            logger.debug("Retrieved metadata for blob: %s", blob_path)
            return metadata

        try:
            return await loop.run_in_executor(None, _get_metadata)
        except NotFound:
            logger.warning("Blob not found for metadata: %s", blob_path)
            raise
        except GoogleCloudError as e:
            logger.error(
                "Failed to get metadata: %s - %s",
                blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def copy_file(
        self,
        source_blob_path: str,
        destination_blob_path: str,
    ) -> str:
        """
        Copy a blob within the same bucket.

        Args:
            source_blob_path: Source blob path
            destination_blob_path: Destination blob path

        Returns:
            Destination blob path

        Raises:
            NotFound: If source blob does not exist
            GoogleCloudError: On copy failure
        """
        loop = asyncio.get_running_loop()

        def _copy():
            source_blob = self._get_blob(source_blob_path)
            destination_blob = self.bucket.blob(destination_blob_path)

            # Copy blob
            token = None
            while True:
                token, bytes_rewritten, total_bytes = destination_blob.rewrite(
                    source_blob, token=token
                )
                if token is None:
                    break

            logger.info(
                "Copied blob: %s -> %s",
                source_blob_path,
                destination_blob_path,
            )
            return destination_blob_path

        try:
            return await loop.run_in_executor(None, _copy)
        except NotFound:
            logger.warning("Source blob not found for copy: %s", source_blob_path)
            raise
        except GoogleCloudError as e:
            logger.error(
                "Failed to copy blob: %s -> %s - %s",
                source_blob_path,
                destination_blob_path,
                str(e),
                exc_info=True,
            )
            raise

    async def move_file(
        self,
        source_blob_path: str,
        destination_blob_path: str,
    ) -> str:
        """
        Move a blob within the same bucket (copy + delete).

        Args:
            source_blob_path: Source blob path
            destination_blob_path: Destination blob path

        Returns:
            Destination blob path

        Raises:
            NotFound: If source blob does not exist
            GoogleCloudError: On move failure
        """
        try:
            # Copy to new location
            await self.copy_file(source_blob_path, destination_blob_path)

            # Delete original
            await self.delete_file(source_blob_path)

            logger.info(
                "Moved blob: %s -> %s",
                source_blob_path,
                destination_blob_path,
            )
            return destination_blob_path
        except Exception as e:
            logger.error(
                "Failed to move blob: %s -> %s - %s",
                source_blob_path,
                destination_blob_path,
                str(e),
                exc_info=True,
            )
            raise

    # Lifecycle-aware path builders

    def get_upload_path(self, job_id: str, filename: str) -> str:
        """
        Get path for uploaded file.

        Args:
            job_id: Job identifier
            filename: Original filename

        Returns:
            Blob path: uploads/{job_id}/{filename}
        """
        return f"uploads/{job_id}/{filename}"

    def get_temp_path(self, job_id: str, subpath: str) -> str:
        """
        Get path for temporary file.

        Args:
            job_id: Job identifier
            subpath: Relative path within temp folder

        Returns:
            Blob path: temp/{job_id}/{subpath}
        """
        return f"temp/{job_id}/{subpath}"

    def get_processed_path(self, project_id: str, subpath: str) -> str:
        """
        Get path for processed/archived file.

        Args:
            project_id: Project identifier
            subpath: Relative path within processed folder

        Returns:
            Blob path: processed/{project_id}/{subpath}
        """
        return f"processed/{project_id}/{subpath}"

    def get_image_path(
        self,
        project_id: str,
        category: str,
        filename: str,
    ) -> str:
        """
        Get path for classified image.

        Args:
            project_id: Project identifier
            category: Image category (e.g., 'floor_plans', 'exteriors')
            filename: Image filename

        Returns:
            Blob path: processed/{project_id}/images/{category}/{filename}
        """
        return f"processed/{project_id}/images/{category}/{filename}"

    def get_floor_plan_path(self, project_id: str, filename: str) -> str:
        """
        Get path for floor plan image.

        Args:
            project_id: Project identifier
            filename: Floor plan filename

        Returns:
            Blob path: processed/{project_id}/floor_plans/{filename}
        """
        return f"processed/{project_id}/floor_plans/{filename}"


# Module-level singleton
storage_service = StorageService()
