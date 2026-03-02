"""
Google Drive API client for PDP Automation.

Provides async wrappers for Google Drive operations with Shared Drive support.
Uses service account authentication for server-to-server access.

Key Features:
- Service account authentication via GOOGLE_APPLICATION_CREDENTIALS
- Shared Drive support (supportsAllDrives=True)
- Async wrappers around sync Google API SDK
- Exponential backoff with jitter on retries
- File upload/download/copy/move/delete
- Folder creation and traversal
- Permission management
- Search and export operations

Usage:
    from app.integrations.drive_client import drive_client

    # Upload file
    file_id = await drive_client.upload_file(
        file_path="/path/to/file.pdf",
        folder_id="parent_folder_id",
        mime_type="application/pdf"
    )

    # Create project structure
    structure = await drive_client.create_project_structure("My Project")
"""

import asyncio
import io
import logging
import os
import random
import threading
from typing import Any, BinaryIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# Google Drive MIME types
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME_TYPE = "application/vnd.google-apps.document"

# Files <= 5MB use simple upload (1 request). Larger files use resumable (2-request
# handshake but recoverable). Google recommends simple upload for files under 5MB.
RESUMABLE_THRESHOLD = 5 * 1024 * 1024  # 5 MB
GOOGLE_SHEET_MIME_TYPE = "application/vnd.google-apps.spreadsheet"
PDF_MIME_TYPE = "application/pdf"
CSV_MIME_TYPE = "text/csv"
EXCEL_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Shared Drive ID -- default value; override via GOOGLE_SHARED_DRIVE_ID env var.
# Loaded lazily to avoid import-time settings resolution.
_SHARED_DRIVE_ID_CACHE: str | None = None


def get_shared_drive_id() -> str:
    """Get Shared Drive ID (lazy, cached)."""
    global _SHARED_DRIVE_ID_CACHE
    if _SHARED_DRIVE_ID_CACHE is None:
        _SHARED_DRIVE_ID_CACHE = getattr(
            get_settings(), "GOOGLE_SHARED_DRIVE_ID", "0AOEEIstP54k2Uk9PVA"
        )
    return _SHARED_DRIVE_ID_CACHE


# Module-level constant kept for backward compatibility; prefer get_shared_drive_id()
SHARED_DRIVE_ID = "0AOEEIstP54k2Uk9PVA"

# Retry configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1
MAX_BACKOFF_SECONDS = 32

# HTTP timeout for large uploads (seconds)
HTTP_TIMEOUT = 600  # 10 minutes


class DriveClient:
    """
    Google Drive API client with async support and Shared Drive compatibility.

    All operations include supportsAllDrives=True for Shared Drive access.
    Uses service account authentication for server-to-server access.
    """

    def __init__(self):
        """Initialize DriveClient with lazy service initialization."""
        self._service = None
        self._credentials = None
        self._request_lock = threading.Lock()
        self.settings = get_settings()

    @property
    def service(self):
        """Lazy-initialize Google Drive service."""
        if self._service is None:
            self._service = self._create_service()
        return self._service

    def _create_service(self):
        """Create Google Drive service with service account credentials."""
        credentials_path = self.settings.GOOGLE_APPLICATION_CREDENTIALS

        if not credentials_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS not set. "
                "Service account credentials required for Drive API access."
            )

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                "Service account credentials file not found at: %s" % credentials_path
            )

        # Full Drive scope required for Shared Drive operations and
        # moving files created by other clients (e.g. gspread).
        scopes = ["https://www.googleapis.com/auth/drive"]

        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes
            )
            self._credentials = credentials

            service = build(
                "drive",
                self.settings.GOOGLE_DRIVE_API_VERSION,
                credentials=credentials,
                cache_discovery=False
            )

            # Increase socket timeout for large file uploads.
            # build() creates AuthorizedHttp wrapping httplib2.Http internally;
            # the default timeout is too short for multi-MB uploads.
            inner_http = getattr(service._http, "http", service._http)
            inner_http.timeout = HTTP_TIMEOUT

            logger.info(
                "Google Drive service initialized with service account from: %s",
                credentials_path
            )
            return service

        except Exception as e:
            logger.error(
                "Failed to initialize Google Drive service: %s",
                str(e),
                exc_info=True
            )
            raise

    async def _execute_with_retry(self, request, operation_name: str) -> Any:
        """
        Execute Google API request with exponential backoff retry.

        Retries on 429 (rate limit) and 5xx (server errors) with jitter.

        Args:
            request: Google API request object
            operation_name: Name of operation for logging

        Returns:
            API response

        Raises:
            HttpError: If all retries fail
        """
        loop = asyncio.get_running_loop()
        lock = self._request_lock

        for attempt in range(MAX_RETRIES):
            try:
                # Serialize through lock -- httplib2.Http connection pool
                # is not thread-safe; concurrent run_in_executor calls
                # corrupt SSL state and cause WRONG_VERSION_NUMBER errors.
                def _locked_execute():
                    with lock:
                        return request.execute()

                response = await loop.run_in_executor(None, _locked_execute)
                return response

            except HttpError as e:
                status_code = e.resp.status

                # Retry on rate limit or server errors
                if status_code in (429, 500, 502, 503, 504):
                    if attempt < MAX_RETRIES - 1:
                        # Exponential backoff with jitter
                        backoff = min(
                            BASE_BACKOFF_SECONDS * (2 ** attempt),
                            MAX_BACKOFF_SECONDS
                        )
                        jitter = random.uniform(0, backoff * 0.1)
                        sleep_time = backoff + jitter

                        logger.warning(
                            "Drive API %s failed with status %s (attempt %s/%s). "
                            "Retrying in %.2fs",
                            operation_name,
                            status_code,
                            attempt + 1,
                            MAX_RETRIES,
                            sleep_time
                        )

                        await asyncio.sleep(sleep_time)
                        continue

                # Non-retryable error or max retries reached
                logger.error(
                    "Drive API %s failed: %s",
                    operation_name,
                    str(e),
                    exc_info=True
                )
                raise

    async def upload_file(
        self,
        file_path: str,
        folder_id: str | None = None,
        file_name: str | None = None,
        mime_type: str | None = None,
        resumable: bool = True
    ) -> str:
        """
        Upload file to Google Drive.

        Args:
            file_path: Local file path to upload
            folder_id: Parent folder ID (defaults to Shared Drive root)
            file_name: Name for uploaded file (defaults to basename)
            mime_type: MIME type of file (auto-detected if None)
            resumable: Use resumable upload for large files

        Returns:
            Uploaded file ID

        Raises:
            FileNotFoundError: If file_path does not exist
            HttpError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError("File not found: %s" % file_path)

        file_name = file_name or os.path.basename(file_path)
        parent_id = folder_id or SHARED_DRIVE_ID

        file_metadata = {
            "name": file_name,
            "parents": [parent_id]
        }

        # Auto-detect: simple upload for small files, resumable for large
        try:
            file_size = os.path.getsize(file_path)
            use_resumable = resumable and file_size > RESUMABLE_THRESHOLD
        except OSError:
            use_resumable = resumable

        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=use_resumable
        )

        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,mimeType,size",
            supportsAllDrives=True
        )

        file = await self._execute_with_retry(request, "upload_file")

        logger.info(
            "Uploaded file '%s' (ID: %s, Size: %s bytes) to folder %s",
            file["name"],
            file["id"],
            file.get("size", "unknown"),
            parent_id
        )

        return file["id"]

    async def upload_file_bytes(
        self,
        file_bytes: bytes | BinaryIO,
        file_name: str,
        folder_id: str | None = None,
        mime_type: str = "application/octet-stream",
        resumable: bool = True
    ) -> str:
        """
        Upload file from bytes or file-like object to Google Drive.

        Args:
            file_bytes: File content as bytes or file-like object
            file_name: Name for uploaded file
            folder_id: Parent folder ID (defaults to Shared Drive root)
            mime_type: MIME type of file
            resumable: Use resumable upload for large files

        Returns:
            Uploaded file ID

        Raises:
            HttpError: If upload fails
        """
        parent_id = folder_id or SHARED_DRIVE_ID

        file_metadata = {
            "name": file_name,
            "parents": [parent_id]
        }

        # Wrap bytes in BytesIO if needed; detect size for resumable threshold
        if isinstance(file_bytes, bytes):
            use_resumable = resumable and len(file_bytes) > RESUMABLE_THRESHOLD
            file_bytes = io.BytesIO(file_bytes)
        else:
            # BinaryIO stream -- can't cheaply determine size, default to resumable
            use_resumable = resumable

        media = MediaIoBaseUpload(
            file_bytes,
            mimetype=mime_type,
            resumable=use_resumable
        )

        request = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,mimeType,size",
            supportsAllDrives=True
        )

        file = await self._execute_with_retry(request, "upload_file_bytes")

        logger.info(
            "Uploaded file '%s' (ID: %s, Size: %s bytes) to folder %s",
            file["name"],
            file["id"],
            file.get("size", "unknown"),
            parent_id
        )

        return file["id"]

    async def upload_files_batch(
        self,
        files: list[tuple[str, str | None, str | None]],
        folder_id: str | None = None,
        max_concurrent: int = 10,
    ) -> list[str]:
        """
        Upload multiple files with bounded concurrency.

        Args:
            files: List of (file_path, file_name, mime_type) tuples
            folder_id: Parent folder ID (defaults to Shared Drive root)
            max_concurrent: Maximum simultaneous uploads (default 10)

        Returns:
            List of uploaded file IDs

        Example:
            files = [
                ("/path/to/file1.pdf", "File 1.pdf", "application/pdf"),
                ("/path/to/file2.jpg", None, None),  # Use defaults
            ]
            file_ids = await drive_client.upload_files_batch(files, folder_id)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _upload_with_limit(file_path, file_name, mime_type):
            async with semaphore:
                return await self.upload_file(file_path, folder_id, file_name, mime_type)

        tasks = [
            _upload_with_limit(file_path, file_name, mime_type)
            for file_path, file_name, mime_type in files
        ]

        file_ids = await asyncio.gather(*tasks)

        logger.info(
            "Batch uploaded %s files to folder %s",
            len(file_ids),
            folder_id or SHARED_DRIVE_ID
        )

        return file_ids

    async def download_file(self, file_id: str) -> bytes:
        """
        Download file from Google Drive as bytes.

        Args:
            file_id: ID of file to download

        Returns:
            File content as bytes

        Raises:
            HttpError: If download fails
        """
        request = self.service.files().get_media(
            fileId=file_id,
            supportsAllDrives=True
        )

        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            loop = asyncio.get_running_loop()
            status, done = await loop.run_in_executor(None, downloader.next_chunk)

            if status:
                progress = int(status.progress() * 100)
                logger.debug("Download progress: %s%%", progress)

        file_bytes = file_io.getvalue()

        logger.info(
            "Downloaded file %s (%s bytes)",
            file_id,
            len(file_bytes)
        )

        return file_bytes

    async def get_file_metadata(self, file_id: str) -> dict[str, Any]:
        """
        Get file metadata from Google Drive.

        Args:
            file_id: ID of file

        Returns:
            File metadata dictionary with id, name, mimeType, size, etc.

        Raises:
            HttpError: If file not found or access denied
        """
        request = self.service.files().get(
            fileId=file_id,
            fields="id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink",
            supportsAllDrives=True
        )

        metadata = await self._execute_with_retry(request, "get_file_metadata")

        logger.debug("Retrieved metadata for file %s: %s", file_id, metadata["name"])

        return metadata

    async def copy_file(
        self,
        file_id: str,
        new_name: str,
        destination_folder_id: str | None = None
    ) -> str:
        """
        Copy file to new location.

        Args:
            file_id: ID of file to copy
            new_name: Name for copied file
            destination_folder_id: Destination folder ID (defaults to Shared Drive root)

        Returns:
            Copied file ID

        Raises:
            HttpError: If copy fails
        """
        body = {"name": new_name}

        if destination_folder_id:
            body["parents"] = [destination_folder_id]
        else:
            body["parents"] = [SHARED_DRIVE_ID]

        request = self.service.files().copy(
            fileId=file_id,
            body=body,
            fields="id,name",
            supportsAllDrives=True
        )

        copied_file = await self._execute_with_retry(request, "copy_file")

        logger.info(
            "Copied file %s to '%s' (ID: %s)",
            file_id,
            copied_file["name"],
            copied_file["id"]
        )

        return copied_file["id"]

    async def move_file(
        self,
        file_id: str,
        destination_folder_id: str
    ) -> dict[str, Any]:
        """
        Move file to different folder.

        Args:
            file_id: ID of file to move
            destination_folder_id: Destination folder ID

        Returns:
            Updated file metadata

        Raises:
            HttpError: If move fails
        """
        # Get current parents
        metadata = await self.get_file_metadata(file_id)
        current_parents = metadata.get("parents", [])

        # Remove from all current parents and add to new parent
        request = self.service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=",".join(current_parents) if current_parents else None,
            fields="id,name,parents",
            supportsAllDrives=True
        )

        updated_file = await self._execute_with_retry(request, "move_file")

        logger.info(
            "Moved file %s from %s to %s",
            file_id,
            current_parents,
            destination_folder_id
        )

        return updated_file

    async def delete_file(self, file_id: str) -> None:
        """
        Delete file from Google Drive.

        Args:
            file_id: ID of file to delete

        Raises:
            HttpError: If delete fails
        """
        request = self.service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        )

        await self._execute_with_retry(request, "delete_file")

        logger.info("Deleted file %s", file_id)

    async def create_folder(
        self,
        folder_name: str,
        parent_folder_id: str | None = None
    ) -> str:
        """
        Create folder in Google Drive.

        Args:
            folder_name: Name of folder to create
            parent_folder_id: Parent folder ID (defaults to Shared Drive root)

        Returns:
            Created folder ID

        Raises:
            HttpError: If folder creation fails
        """
        parent_id = parent_folder_id or SHARED_DRIVE_ID

        file_metadata = {
            "name": folder_name,
            "mimeType": FOLDER_MIME_TYPE,
            "parents": [parent_id]
        }

        request = self.service.files().create(
            body=file_metadata,
            fields="id,name",
            supportsAllDrives=True
        )

        folder = await self._execute_with_retry(request, "create_folder")

        logger.info(
            "Created folder '%s' (ID: %s) in parent %s",
            folder["name"],
            folder["id"],
            parent_id
        )

        return folder["id"]

    async def list_folder_contents(
        self,
        folder_id: str,
        page_size: int = 100
    ) -> list[dict[str, Any]]:
        """
        List contents of folder.

        Args:
            folder_id: ID of folder to list
            page_size: Number of items per page (max 1000)

        Returns:
            List of file/folder metadata dictionaries

        Raises:
            HttpError: If list fails
        """
        query = "'%s' in parents and trashed=false" % folder_id

        request = self.service.files().list(
            q=query,
            pageSize=page_size,
            fields="nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="drive",
            driveId=SHARED_DRIVE_ID
        )

        items = []
        page_token = None

        while True:
            if page_token:
                request = self.service.files().list(
                    q=query,
                    pageSize=page_size,
                    pageToken=page_token,
                    fields="nextPageToken,files(id,name,mimeType,size,createdTime,modifiedTime)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora="drive",
                    driveId=SHARED_DRIVE_ID
                )

            response = await self._execute_with_retry(request, "list_folder_contents")
            items.extend(response.get("files", []))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(
            "Listed %s items in folder %s",
            len(items),
            folder_id
        )

        return items

    async def get_folder_by_path(
        self,
        path: str,
        parent_folder_id: str | None = None,
        create_if_missing: bool = False
    ) -> str | None:
        """
        Get folder ID by path traversal.

        Args:
            path: Folder path (e.g., "Projects/MyProject/Source")
            parent_folder_id: Starting folder ID (defaults to Shared Drive root)
            create_if_missing: Create folders if they don't exist

        Returns:
            Folder ID if found/created, None if not found and create_if_missing=False

        Example:
            folder_id = await drive_client.get_folder_by_path(
                "Projects/MyProject/Source",
                create_if_missing=True
            )
        """
        parent_id = parent_folder_id or SHARED_DRIVE_ID

        # Split path and filter empty segments
        segments = [s.strip() for s in path.split("/") if s.strip()]

        if not segments:
            return parent_id

        current_folder_id = parent_id

        for segment in segments:
            # Search for folder with this name in current parent
            query = (
                "'%s' in parents and "
                "name='%s' and "
                "mimeType='%s' and "
                "trashed=false"
            ) % (current_folder_id, segment.replace("'", "\\'"), FOLDER_MIME_TYPE)

            request = self.service.files().list(
                q=query,
                pageSize=1,
                fields="files(id,name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora="drive",
                driveId=SHARED_DRIVE_ID
            )

            response = await self._execute_with_retry(request, "get_folder_by_path")
            files = response.get("files", [])

            if files:
                current_folder_id = files[0]["id"]
            elif create_if_missing:
                current_folder_id = await self.create_folder(segment, current_folder_id)
            else:
                logger.warning(
                    "Folder '%s' not found in path '%s'",
                    segment,
                    path
                )
                return None

        logger.info("Resolved path '%s' to folder ID: %s", path, current_folder_id)

        return current_folder_id

    async def create_project_structure(
        self,
        project_name: str,
        parent_folder_id: str | None = None
    ) -> dict[str, str]:
        """
        Create standard project folder structure.

        Creates:
        - Projects/{project_name}/
        - Projects/{project_name}/Source/
        - Projects/{project_name}/Images/
        - Projects/{project_name}/Raw Data/

        Args:
            project_name: Name of project
            parent_folder_id: Parent for Projects folder (defaults to Shared Drive root)

        Returns:
            Dictionary with folder IDs: {
                "project": folder_id,
                "source": folder_id,
                "images": folder_id,
                "raw_data": folder_id
            }

        Raises:
            HttpError: If folder creation fails
        """
        parent_id = parent_folder_id or SHARED_DRIVE_ID

        # Get or create Projects folder
        projects_folder_id = await self.get_folder_by_path(
            "Projects",
            parent_id,
            create_if_missing=True
        )

        # Create project folder
        project_folder_id = await self.create_folder(project_name, projects_folder_id)

        # Create subfolders concurrently
        source_task = self.create_folder("Source", project_folder_id)
        images_task = self.create_folder("Images", project_folder_id)
        raw_data_task = self.create_folder("Raw Data", project_folder_id)

        source_id, images_id, raw_data_id = await asyncio.gather(
            source_task,
            images_task,
            raw_data_task
        )

        structure = {
            "project": project_folder_id,
            "source": source_id,
            "images": images_id,
            "raw_data": raw_data_id
        }

        logger.info(
            "Created project structure for '%s': %s",
            project_name,
            structure
        )

        return structure

    async def upload_to_project(
        self,
        project_structure: dict[str, str],
        source_pdf: bytes | None = None,
        source_filename: str = "brochure.pdf",
        organized_images: list[tuple[str, bytes]] | None = None,
        raw_data_files: list[tuple[str, bytes]] | None = None,
    ) -> dict[str, Any]:
        """
        Upload files to project folder structure.

        Populates the project folders:
        - Source/ receives original PDF brochure
        - Images/ receives organized images with subfolder structure
        - Raw Data/ receives manifest.json, extracted_text.json, and floor plan data

        Args:
            project_structure: Dict from create_project_structure with folder IDs
            source_pdf: Original PDF bytes for Source folder
            source_filename: Filename for source PDF
            organized_images: List of (relative_path, bytes) for Images folder.
                             Paths like "original/interiors/001-interior.webp" create subfolders.
            raw_data_files: List of (relative_path, bytes) for Raw Data folder.
                           Paths like "floor_plans/fp_001.json" create subfolders.

        Returns:
            Dict of uploaded file IDs: {
                "source_pdf": id,
                "images_uploaded": count,
                "raw_data_uploaded": count
            }

        Raises:
            HttpError: If upload fails
        """
        uploaded: dict[str, Any] = {}

        # Upload source PDF to Source folder
        if source_pdf:
            file_id = await self.upload_file_bytes(
                source_pdf,
                source_filename,
                folder_id=project_structure["source"],
                mime_type=PDF_MIME_TYPE,
            )
            uploaded["source_pdf"] = file_id
            logger.info("Uploaded source PDF to Source folder: %s", file_id)

        # Upload organized images to Images folder with subfolder structure
        if organized_images:
            images_folder_id = project_structure["images"]
            upload_count = 0
            # Cache subfolder IDs to avoid repeated lookups
            subfolder_cache: dict[str, str] = {}

            for path, img_bytes in organized_images:
                parts = path.replace("\\", "/").split("/")

                if len(parts) > 1:
                    # Has subfolder(s) - e.g., "original/interiors/001-interior.webp"
                    subfolder_path = "/".join(parts[:-1])
                    filename = parts[-1]

                    if subfolder_path not in subfolder_cache:
                        # Get or create subfolder hierarchy
                        parent_id = images_folder_id
                        for folder_name in parts[:-1]:
                            existing = await self.get_folder_by_path(
                                folder_name,
                                parent_id,
                                create_if_missing=False
                            )
                            if existing:
                                parent_id = existing
                            else:
                                parent_id = await self.create_folder(
                                    folder_name, parent_id
                                )
                        subfolder_cache[subfolder_path] = parent_id

                    parent_id = subfolder_cache[subfolder_path]
                else:
                    # No subfolder - upload directly to Images/
                    parent_id = images_folder_id
                    filename = parts[0]

                # Detect MIME type from extension
                ext = filename.lower().split(".")[-1] if "." in filename else ""
                mime_type = {
                    "webp": "image/webp",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                }.get(ext, "application/octet-stream")

                await self.upload_file_bytes(
                    img_bytes,
                    filename,
                    folder_id=parent_id,
                    mime_type=mime_type,
                )
                upload_count += 1

            uploaded["images_uploaded"] = upload_count
            logger.info(
                "Uploaded %d images to Images folder structure",
                upload_count
            )

        # Upload raw data files to Raw Data folder with subfolder structure
        if raw_data_files:
            raw_data_folder_id = project_structure["raw_data"]
            raw_upload_count = 0
            subfolder_cache: dict[str, str] = {}

            for path, file_bytes in raw_data_files:
                parts = path.replace("\\", "/").split("/")

                if len(parts) > 1:
                    # Has subfolder(s) - e.g., "floor_plans/fp_001.json"
                    subfolder_path = "/".join(parts[:-1])
                    filename = parts[-1]

                    if subfolder_path not in subfolder_cache:
                        parent_id = raw_data_folder_id
                        for folder_name in parts[:-1]:
                            existing = await self.get_folder_by_path(
                                folder_name,
                                parent_id,
                                create_if_missing=False
                            )
                            if existing:
                                parent_id = existing
                            else:
                                parent_id = await self.create_folder(
                                    folder_name, parent_id
                                )
                        subfolder_cache[subfolder_path] = parent_id

                    parent_id = subfolder_cache[subfolder_path]
                else:
                    parent_id = raw_data_folder_id
                    filename = parts[0]

                # Detect MIME type
                ext = filename.lower().split(".")[-1] if "." in filename else ""
                mime_type = {
                    "json": "application/json",
                    "txt": "text/plain",
                    "md": "text/markdown",
                }.get(ext, "application/octet-stream")

                await self.upload_file_bytes(
                    file_bytes,
                    filename,
                    folder_id=parent_id,
                    mime_type=mime_type,
                )
                raw_upload_count += 1

            uploaded["raw_data_uploaded"] = raw_upload_count
            logger.info(
                "Uploaded %d files to Raw Data folder structure",
                raw_upload_count
            )

        return uploaded

    async def share_with_user(
        self,
        file_id: str,
        email: str,
        role: str = "reader"
    ) -> str:
        """
        Share file/folder with user by email.

        Args:
            file_id: ID of file/folder to share
            email: Email address of user
            role: Permission role (reader, writer, commenter, owner)

        Returns:
            Permission ID

        Raises:
            HttpError: If sharing fails
        """
        permission = {
            "type": "user",
            "role": role,
            "emailAddress": email
        }

        request = self.service.permissions().create(
            fileId=file_id,
            body=permission,
            fields="id",
            supportsAllDrives=True,
            sendNotificationEmail=False
        )

        result = await self._execute_with_retry(request, "share_with_user")

        logger.info(
            "Shared file %s with user %s (role: %s, permission ID: %s)",
            file_id,
            email,
            role,
            result["id"]
        )

        return result["id"]

    async def share_with_domain(
        self,
        file_id: str,
        domain: str,
        role: str = "reader"
    ) -> str:
        """
        Share file/folder with entire domain.

        Args:
            file_id: ID of file/folder to share
            domain: Domain name (e.g., "your-domain.com")
            role: Permission role (reader, writer, commenter)

        Returns:
            Permission ID

        Raises:
            HttpError: If sharing fails
        """
        permission = {
            "type": "domain",
            "role": role,
            "domain": domain
        }

        request = self.service.permissions().create(
            fileId=file_id,
            body=permission,
            fields="id",
            supportsAllDrives=True
        )

        result = await self._execute_with_retry(request, "share_with_domain")

        logger.info(
            "Shared file %s with domain %s (role: %s, permission ID: %s)",
            file_id,
            domain,
            role,
            result["id"]
        )

        return result["id"]

    async def remove_permission(
        self,
        file_id: str,
        permission_id: str
    ) -> None:
        """
        Remove permission from file/folder.

        Args:
            file_id: ID of file/folder
            permission_id: ID of permission to remove

        Raises:
            HttpError: If removal fails
        """
        request = self.service.permissions().delete(
            fileId=file_id,
            permissionId=permission_id,
            supportsAllDrives=True
        )

        await self._execute_with_retry(request, "remove_permission")

        logger.info(
            "Removed permission %s from file %s",
            permission_id,
            file_id
        )

    async def search_by_name(
        self,
        name: str,
        folder_id: str | None = None,
        exact_match: bool = False
    ) -> list[dict[str, Any]]:
        """
        Search for files/folders by name.

        Args:
            name: File/folder name to search for
            folder_id: Limit search to specific folder (None searches entire Shared Drive)
            exact_match: Use exact name match vs contains

        Returns:
            List of matching file/folder metadata

        Raises:
            HttpError: If search fails
        """
        # Escape both backslashes and single quotes for Google Drive API query syntax
        sanitized = name.replace("\\", "\\\\").replace("'", "\\'")
        if exact_match:
            name_query = "name='%s'" % sanitized
        else:
            name_query = "name contains '%s'" % sanitized

        if folder_id:
            query = "'%s' in parents and %s and trashed=false" % (folder_id, name_query)
        else:
            query = "%s and trashed=false" % name_query

        request = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id,name,mimeType,size,createdTime,modifiedTime,parents)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="drive",
            driveId=SHARED_DRIVE_ID
        )

        response = await self._execute_with_retry(request, "search_by_name")
        files = response.get("files", [])

        logger.info(
            "Search for name '%s' found %s results",
            name,
            len(files)
        )

        return files

    async def search_by_mime_type(
        self,
        mime_type: str,
        folder_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for files by MIME type.

        Args:
            mime_type: MIME type to search for (e.g., "application/pdf")
            folder_id: Limit search to specific folder (None searches entire Shared Drive)

        Returns:
            List of matching file metadata

        Raises:
            HttpError: If search fails
        """
        if folder_id:
            query = (
                "'%s' in parents and mimeType='%s' and trashed=false"
            ) % (folder_id, mime_type)
        else:
            query = "mimeType='%s' and trashed=false" % mime_type

        request = self.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id,name,mimeType,size,createdTime,modifiedTime,parents)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="drive",
            driveId=SHARED_DRIVE_ID
        )

        response = await self._execute_with_retry(request, "search_by_mime_type")
        files = response.get("files", [])

        logger.info(
            "Search for MIME type '%s' found %s results",
            mime_type,
            len(files)
        )

        return files

    async def export_google_doc_to_pdf(self, doc_id: str) -> bytes:
        """
        Export Google Doc to PDF format.

        Args:
            doc_id: ID of Google Doc to export

        Returns:
            PDF content as bytes

        Raises:
            HttpError: If export fails
        """
        request = self.service.files().export_media(
            fileId=doc_id,
            mimeType=PDF_MIME_TYPE
        )

        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            loop = asyncio.get_running_loop()
            status, done = await loop.run_in_executor(None, downloader.next_chunk)

        pdf_bytes = file_io.getvalue()

        logger.info(
            "Exported Google Doc %s to PDF (%s bytes)",
            doc_id,
            len(pdf_bytes)
        )

        return pdf_bytes

    async def export_google_sheet_to_csv(self, sheet_id: str, gid: int = 0) -> bytes:
        """
        Export Google Sheet to CSV format.

        Args:
            sheet_id: ID of Google Sheet to export
            gid: Sheet tab ID (default 0 for first tab)

        Returns:
            CSV content as bytes

        Raises:
            HttpError: If export fails
        """
        request = self.service.files().export_media(
            fileId=sheet_id,
            mimeType=CSV_MIME_TYPE
        )

        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            loop = asyncio.get_running_loop()
            status, done = await loop.run_in_executor(None, downloader.next_chunk)

        csv_bytes = file_io.getvalue()

        logger.info(
            "Exported Google Sheet %s to CSV (%s bytes)",
            sheet_id,
            len(csv_bytes)
        )

        return csv_bytes

    async def export_google_sheet_to_excel(self, sheet_id: str) -> bytes:
        """
        Export Google Sheet to Excel (XLSX) format.

        Args:
            sheet_id: ID of Google Sheet to export

        Returns:
            Excel content as bytes

        Raises:
            HttpError: If export fails
        """
        request = self.service.files().export_media(
            fileId=sheet_id,
            mimeType=EXCEL_MIME_TYPE
        )

        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, request)

        done = False
        while not done:
            loop = asyncio.get_running_loop()
            status, done = await loop.run_in_executor(None, downloader.next_chunk)

        excel_bytes = file_io.getvalue()

        logger.info(
            "Exported Google Sheet %s to Excel (%s bytes)",
            sheet_id,
            len(excel_bytes)
        )

        return excel_bytes


# Module-level singleton instance
drive_client = DriveClient()
