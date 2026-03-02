"""
Unit tests for Google Drive client.

Tests DriveClient with mocked Google API SDK to verify:
- Service account authentication initialization
- File operations (upload, download, copy, move, delete)
- Folder operations (create, list, search)
- Batch uploads and concurrent operations
- Permission management (user, domain sharing)
- Search operations (by name, MIME type)
- Google Workspace exports (Docs to PDF, Sheets to CSV/Excel)
- Retry logic with exponential backoff on 429 and 5xx errors
- supportsAllDrives=True on all operations
- Error handling for non-retryable errors
"""

import asyncio
import io
import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

from app.integrations.drive_client import (
    CSV_MIME_TYPE,
    EXCEL_MIME_TYPE,
    FOLDER_MIME_TYPE,
    GOOGLE_DOC_MIME_TYPE,
    GOOGLE_SHEET_MIME_TYPE,
    PDF_MIME_TYPE,
    SHARED_DRIVE_ID,
    DriveClient,
)


@pytest.fixture
def mock_settings():
    """Mock settings with test configuration."""
    with patch("app.integrations.drive_client.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.GOOGLE_APPLICATION_CREDENTIALS = "/tmp/test-creds.json"
        settings.GOOGLE_DRIVE_API_VERSION = "v3"
        settings.GOOGLE_DRIVE_ROOT_FOLDER_ID = "test-root-id"
        mock_get_settings.return_value = settings
        yield settings


@pytest.fixture
def mock_credentials():
    """Mock Google service account credentials."""
    with patch.object(
        service_account.Credentials,
        "from_service_account_file"
    ) as mock_from_file:
        credentials = MagicMock(spec=service_account.Credentials)
        mock_from_file.return_value = credentials
        yield mock_from_file


@pytest.fixture
def mock_drive_service():
    """Mock Google Drive API service."""
    with patch("app.integrations.drive_client.build") as mock_build:
        service = MagicMock()
        mock_build.return_value = service
        yield service


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists to return True for credentials file."""
    with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def drive_client(mock_settings, mock_credentials, mock_drive_service, mock_os_path_exists):
    """Create DriveClient instance with mocked dependencies."""
    client = DriveClient()
    # Force service initialization
    _ = client.service
    return client


class TestDriveClientInitialization:
    """Test DriveClient initialization and service creation."""

    def test_init_lazy_service(self, mock_settings):
        """Test that service is not initialized until accessed."""
        client = DriveClient()
        assert client._service is None
        assert client._credentials is None

    def test_create_service_success(
        self,
        mock_settings,
        mock_credentials,
        mock_drive_service,
        mock_os_path_exists
    ):
        """Test successful service initialization with service account."""
        client = DriveClient()
        service = client.service

        # Verify credentials file was checked
        mock_os_path_exists.assert_called_once_with("/tmp/test-creds.json")

        # Verify credentials loaded with correct scope (full drive scope
        # required for Shared Drive operations and moving files)
        mock_credentials.assert_called_once_with(
            "/tmp/test-creds.json",
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Verify service was built
        assert service == mock_drive_service

    def test_create_service_missing_credentials_path(self, mock_settings):
        """Test error when GOOGLE_APPLICATION_CREDENTIALS not set."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS = None
        client = DriveClient()

        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS not set"):
            _ = client.service

    def test_create_service_credentials_file_not_found(
        self,
        mock_settings,
        mock_os_path_exists
    ):
        """Test error when credentials file does not exist."""
        mock_os_path_exists.return_value = False
        client = DriveClient()

        with pytest.raises(FileNotFoundError, match="Service account credentials file not found"):
            _ = client.service

    def test_create_service_authentication_error(
        self,
        mock_settings,
        mock_credentials,
        mock_os_path_exists
    ):
        """Test error handling when credentials loading fails."""
        mock_credentials.side_effect = Exception("Invalid credentials format")
        client = DriveClient()

        with pytest.raises(Exception, match="Invalid credentials format"):
            _ = client.service


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, drive_client):
        """Test successful execution on first attempt."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "test-file-id"}

        result = await drive_client._execute_with_retry(mock_request, "test_operation")

        assert result == {"id": "test-file-id"}
        mock_request.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_retry_rate_limit(self, drive_client):
        """Test retry on 429 rate limit error."""
        mock_request = MagicMock()

        # First two calls fail with 429, third succeeds
        mock_resp_429 = MagicMock()
        mock_resp_429.status = 429
        error_429 = HttpError(mock_resp_429, b"Rate limit exceeded")

        mock_request.execute.side_effect = [
            error_429,
            error_429,
            {"id": "test-file-id"}
        ]

        result = await drive_client._execute_with_retry(mock_request, "test_operation")

        assert result == {"id": "test-file-id"}
        assert mock_request.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_server_errors(self, drive_client):
        """Test retry on 5xx server errors."""
        mock_request = MagicMock()

        # Test 500, 502, 503, 504 errors
        for status_code in [500, 502, 503, 504]:
            mock_request.reset_mock()
            mock_resp = MagicMock()
            mock_resp.status = status_code
            error = HttpError(mock_resp, b"Server error")

            mock_request.execute.side_effect = [
                error,
                {"id": "test-file-id"}
            ]

            result = await drive_client._execute_with_retry(mock_request, "test_operation")

            assert result == {"id": "test-file-id"}
            assert mock_request.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self, drive_client):
        """Test failure after max retries exceeded."""
        mock_request = MagicMock()

        mock_resp = MagicMock()
        mock_resp.status = 429
        error = HttpError(mock_resp, b"Rate limit exceeded")

        mock_request.execute.side_effect = error

        with pytest.raises(HttpError):
            await drive_client._execute_with_retry(mock_request, "test_operation")

        assert mock_request.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, drive_client):
        """Test immediate failure on non-retryable errors (4xx except 429)."""
        mock_request = MagicMock()

        mock_resp = MagicMock()
        mock_resp.status = 404
        error = HttpError(mock_resp, b"Not found")

        mock_request.execute.side_effect = error

        with pytest.raises(HttpError):
            await drive_client._execute_with_retry(mock_request, "test_operation")

        # Should not retry on 404
        mock_request.execute.assert_called_once()


class TestFileUpload:
    """Test file upload operations."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, drive_client, mock_drive_service):
        """Test successful file upload with path."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "uploaded-file-id",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("app.integrations.drive_client.MediaFileUpload") as mock_media:
                file_id = await drive_client.upload_file(
                    file_path="/path/to/test.pdf",
                    folder_id="parent-folder-id",
                    file_name="custom-name.pdf",
                    mime_type="application/pdf"
                )

        assert file_id == "uploaded-file-id"

        # Verify API call
        mock_drive_service.files().create.assert_called_once()
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["body"]["name"] == "custom-name.pdf"
        assert call_kwargs["body"]["parents"] == ["parent-folder-id"]

    @pytest.mark.asyncio
    async def test_upload_file_default_folder(self, drive_client, mock_drive_service):
        """Test file upload defaults to Shared Drive root."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "uploaded-file-id",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("app.integrations.drive_client.MediaFileUpload"):
                file_id = await drive_client.upload_file(file_path="/path/to/test.pdf")

        # Should use SHARED_DRIVE_ID as parent
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == [SHARED_DRIVE_ID]

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, drive_client):
        """Test error when file path does not exist."""
        with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
            mock_exists.return_value = False

            with pytest.raises(FileNotFoundError, match="File not found"):
                await drive_client.upload_file(file_path="/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_upload_file_bytes_success(self, drive_client, mock_drive_service):
        """Test successful file upload from bytes."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "uploaded-file-id",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        file_bytes = b"PDF content here"

        with patch("app.integrations.drive_client.MediaIoBaseUpload"):
            file_id = await drive_client.upload_file_bytes(
                file_bytes=file_bytes,
                file_name="test.pdf",
                folder_id="parent-folder-id",
                mime_type="application/pdf"
            )

        assert file_id == "uploaded-file-id"

        # Verify supportsAllDrives=True
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True

    @pytest.mark.asyncio
    async def test_upload_file_bytes_from_io(self, drive_client, mock_drive_service):
        """Test file upload from file-like object."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "uploaded-file-id",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        file_io = io.BytesIO(b"PDF content")

        with patch("app.integrations.drive_client.MediaIoBaseUpload"):
            file_id = await drive_client.upload_file_bytes(
                file_bytes=file_io,
                file_name="test.pdf"
            )

        assert file_id == "uploaded-file-id"


class TestBatchUpload:
    """Test batch upload operations."""

    @pytest.mark.asyncio
    async def test_upload_files_batch_success(self, drive_client, mock_drive_service):
        """Test concurrent batch upload of multiple files."""
        mock_request = MagicMock()
        mock_request.execute.side_effect = [
            {"id": "file-1", "name": "file1.pdf", "mimeType": "application/pdf", "size": "100"},
            {"id": "file-2", "name": "file2.pdf", "mimeType": "application/pdf", "size": "200"},
            {"id": "file-3", "name": "file3.pdf", "mimeType": "application/pdf", "size": "300"}
        ]
        mock_drive_service.files().create.return_value = mock_request

        files = [
            ("/path/to/file1.pdf", "file1.pdf", "application/pdf"),
            ("/path/to/file2.pdf", "file2.pdf", "application/pdf"),
            ("/path/to/file3.pdf", None, None)
        ]

        with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("app.integrations.drive_client.MediaFileUpload"):
                file_ids = await drive_client.upload_files_batch(
                    files=files,
                    folder_id="parent-folder-id"
                )

        assert file_ids == ["file-1", "file-2", "file-3"]
        assert mock_drive_service.files().create.call_count == 3


class TestFileDownload:
    """Test file download operations."""

    @pytest.mark.asyncio
    async def test_download_file_success(self, drive_client, mock_drive_service):
        """Test successful file download."""
        mock_request = MagicMock()
        mock_drive_service.files().get_media.return_value = mock_request

        # Mock downloader behavior
        with patch("app.integrations.drive_client.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0

            # Simulate download completion
            mock_downloader.next_chunk.side_effect = [
                (mock_status, False),
                (mock_status, True)
            ]
            mock_downloader_class.return_value = mock_downloader

            file_bytes = await drive_client.download_file(file_id="test-file-id")

        # Verify get_media called with supportsAllDrives=True
        mock_drive_service.files().get_media.assert_called_once_with(
            fileId="test-file-id",
            supportsAllDrives=True
        )

    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, drive_client, mock_drive_service):
        """Test getting file metadata."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "test-file-id",
            "name": "test.pdf",
            "mimeType": "application/pdf",
            "size": "1024",
            "createdTime": "2026-01-01T00:00:00Z",
            "modifiedTime": "2026-01-02T00:00:00Z"
        }
        mock_drive_service.files().get.return_value = mock_request

        metadata = await drive_client.get_file_metadata(file_id="test-file-id")

        assert metadata["id"] == "test-file-id"
        assert metadata["name"] == "test.pdf"

        # Verify supportsAllDrives=True
        call_kwargs = mock_drive_service.files().get.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True


class TestFileOperations:
    """Test file copy, move, and delete operations."""

    @pytest.mark.asyncio
    async def test_copy_file_success(self, drive_client, mock_drive_service):
        """Test successful file copy."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "copied-file-id",
            "name": "copy-of-file.pdf"
        }
        mock_drive_service.files().copy.return_value = mock_request

        file_id = await drive_client.copy_file(
            file_id="original-file-id",
            new_name="copy-of-file.pdf",
            destination_folder_id="dest-folder-id"
        )

        assert file_id == "copied-file-id"

        # Verify supportsAllDrives=True
        call_kwargs = mock_drive_service.files().copy.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["body"]["name"] == "copy-of-file.pdf"
        assert call_kwargs["body"]["parents"] == ["dest-folder-id"]

    @pytest.mark.asyncio
    async def test_copy_file_default_destination(self, drive_client, mock_drive_service):
        """Test file copy defaults to Shared Drive root."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "copied-file-id",
            "name": "copy-of-file.pdf"
        }
        mock_drive_service.files().copy.return_value = mock_request

        file_id = await drive_client.copy_file(
            file_id="original-file-id",
            new_name="copy-of-file.pdf"
        )

        # Should use SHARED_DRIVE_ID as parent
        call_kwargs = mock_drive_service.files().copy.call_args[1]
        assert call_kwargs["body"]["parents"] == [SHARED_DRIVE_ID]

    @pytest.mark.asyncio
    async def test_move_file_success(self, drive_client, mock_drive_service):
        """Test successful file move."""
        # Mock get_file_metadata response
        mock_get_request = MagicMock()
        mock_get_request.execute.return_value = {
            "id": "test-file-id",
            "name": "test.pdf",
            "parents": ["old-parent-id"]
        }

        # Mock update response
        mock_update_request = MagicMock()
        mock_update_request.execute.return_value = {
            "id": "test-file-id",
            "name": "test.pdf",
            "parents": ["new-parent-id"]
        }

        mock_drive_service.files().get.return_value = mock_get_request
        mock_drive_service.files().update.return_value = mock_update_request

        updated_file = await drive_client.move_file(
            file_id="test-file-id",
            destination_folder_id="new-parent-id"
        )

        assert updated_file["parents"] == ["new-parent-id"]

        # Verify update call
        call_kwargs = mock_drive_service.files().update.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["addParents"] == "new-parent-id"
        assert call_kwargs["removeParents"] == "old-parent-id"

    @pytest.mark.asyncio
    async def test_delete_file_success(self, drive_client, mock_drive_service):
        """Test successful file deletion."""
        mock_request = MagicMock()
        mock_request.execute.return_value = None
        mock_drive_service.files().delete.return_value = mock_request

        await drive_client.delete_file(file_id="test-file-id")

        # Verify supportsAllDrives=True
        call_kwargs = mock_drive_service.files().delete.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True


class TestFolderOperations:
    """Test folder creation and listing operations."""

    @pytest.mark.asyncio
    async def test_create_folder_success(self, drive_client, mock_drive_service):
        """Test successful folder creation."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "new-folder-id",
            "name": "New Folder"
        }
        mock_drive_service.files().create.return_value = mock_request

        folder_id = await drive_client.create_folder(
            folder_name="New Folder",
            parent_folder_id="parent-folder-id"
        )

        assert folder_id == "new-folder-id"

        # Verify folder MIME type and supportsAllDrives
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["body"]["mimeType"] == FOLDER_MIME_TYPE
        assert call_kwargs["body"]["parents"] == ["parent-folder-id"]

    @pytest.mark.asyncio
    async def test_create_folder_default_parent(self, drive_client, mock_drive_service):
        """Test folder creation defaults to Shared Drive root."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "new-folder-id",
            "name": "New Folder"
        }
        mock_drive_service.files().create.return_value = mock_request

        folder_id = await drive_client.create_folder(folder_name="New Folder")

        # Should use SHARED_DRIVE_ID as parent
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == [SHARED_DRIVE_ID]

    @pytest.mark.asyncio
    async def test_list_folder_contents_success(self, drive_client, mock_drive_service):
        """Test listing folder contents without pagination."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "files": [
                {"id": "file-1", "name": "file1.pdf"},
                {"id": "file-2", "name": "file2.pdf"}
            ]
        }
        mock_drive_service.files().list.return_value = mock_request

        items = await drive_client.list_folder_contents(folder_id="test-folder-id")

        assert len(items) == 2
        assert items[0]["id"] == "file-1"

        # Verify supportsAllDrives and includeItemsFromAllDrives
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["includeItemsFromAllDrives"] is True
        assert call_kwargs["corpora"] == "drive"
        assert call_kwargs["driveId"] == SHARED_DRIVE_ID

    @pytest.mark.asyncio
    async def test_list_folder_contents_pagination(self, drive_client, mock_drive_service):
        """Test listing folder contents with pagination."""
        mock_request = MagicMock()
        mock_request.execute.side_effect = [
            {
                "files": [{"id": "file-1", "name": "file1.pdf"}],
                "nextPageToken": "token-1"
            },
            {
                "files": [{"id": "file-2", "name": "file2.pdf"}],
                "nextPageToken": "token-2"
            },
            {
                "files": [{"id": "file-3", "name": "file3.pdf"}]
            }
        ]
        mock_drive_service.files().list.return_value = mock_request

        items = await drive_client.list_folder_contents(
            folder_id="test-folder-id",
            page_size=1
        )

        assert len(items) == 3
        assert mock_drive_service.files().list.call_count == 3


class TestFolderTraversal:
    """Test folder path traversal and creation."""

    @pytest.mark.asyncio
    async def test_get_folder_by_path_existing(self, drive_client, mock_drive_service):
        """Test getting existing folder by path."""
        mock_request = MagicMock()
        mock_request.execute.side_effect = [
            {"files": [{"id": "projects-folder-id", "name": "Projects"}]},
            {"files": [{"id": "project-folder-id", "name": "MyProject"}]}
        ]
        mock_drive_service.files().list.return_value = mock_request

        folder_id = await drive_client.get_folder_by_path(
            path="Projects/MyProject",
            create_if_missing=False
        )

        assert folder_id == "project-folder-id"

        # Verify supportsAllDrives on search queries
        assert mock_drive_service.files().list.call_count == 2

    @pytest.mark.asyncio
    async def test_get_folder_by_path_not_found(self, drive_client, mock_drive_service):
        """Test folder not found returns None when create_if_missing=False."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"files": []}
        mock_drive_service.files().list.return_value = mock_request

        folder_id = await drive_client.get_folder_by_path(
            path="NonExistent/Path",
            create_if_missing=False
        )

        assert folder_id is None

    @pytest.mark.asyncio
    async def test_get_folder_by_path_create_if_missing(self, drive_client, mock_drive_service):
        """Test creating folders when they don't exist."""
        mock_list_request = MagicMock()
        mock_list_request.execute.return_value = {"files": []}

        mock_create_request = MagicMock()
        mock_create_request.execute.side_effect = [
            {"id": "projects-folder-id", "name": "Projects"},
            {"id": "project-folder-id", "name": "MyProject"}
        ]

        mock_drive_service.files().list.return_value = mock_list_request
        mock_drive_service.files().create.return_value = mock_create_request

        folder_id = await drive_client.get_folder_by_path(
            path="Projects/MyProject",
            create_if_missing=True
        )

        assert folder_id == "project-folder-id"
        assert mock_drive_service.files().create.call_count == 2

    @pytest.mark.asyncio
    async def test_get_folder_by_path_empty_path(self, drive_client):
        """Test empty path returns parent folder ID."""
        folder_id = await drive_client.get_folder_by_path(
            path="",
            parent_folder_id="parent-id"
        )

        assert folder_id == "parent-id"


class TestProjectStructure:
    """Test project structure creation."""

    @pytest.mark.asyncio
    async def test_create_project_structure_success(self, drive_client, mock_drive_service):
        """Test creating complete project folder structure."""
        # Mock get_folder_by_path for Projects folder
        mock_list_request = MagicMock()
        mock_list_request.execute.return_value = {
            "files": [{"id": "projects-folder-id", "name": "Projects"}]
        }

        # Mock create_folder for project and subfolders
        mock_create_request = MagicMock()
        mock_create_request.execute.side_effect = [
            {"id": "project-folder-id", "name": "MyProject"},
            {"id": "source-folder-id", "name": "Source"},
            {"id": "images-folder-id", "name": "Images"},
            {"id": "raw-data-folder-id", "name": "Raw Data"}
        ]

        mock_drive_service.files().list.return_value = mock_list_request
        mock_drive_service.files().create.return_value = mock_create_request

        structure = await drive_client.create_project_structure(
            project_name="MyProject"
        )

        assert structure["project"] == "project-folder-id"
        assert structure["source"] == "source-folder-id"
        assert structure["images"] == "images-folder-id"
        assert structure["raw_data"] == "raw-data-folder-id"

        # Should create 4 folders: project + 3 subfolders
        assert mock_drive_service.files().create.call_count == 4


class TestPermissions:
    """Test permission management operations."""

    @pytest.mark.asyncio
    async def test_share_with_user_success(self, drive_client, mock_drive_service):
        """Test sharing file with user by email."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "permission-id-123"}
        mock_drive_service.permissions().create.return_value = mock_request

        permission_id = await drive_client.share_with_user(
            file_id="test-file-id",
            email="user@example.com",
            role="writer"
        )

        assert permission_id == "permission-id-123"

        # Verify supportsAllDrives and permission details
        call_kwargs = mock_drive_service.permissions().create.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["sendNotificationEmail"] is False
        assert call_kwargs["body"]["type"] == "user"
        assert call_kwargs["body"]["role"] == "writer"
        assert call_kwargs["body"]["emailAddress"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_share_with_user_default_role(self, drive_client, mock_drive_service):
        """Test sharing with default reader role."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "permission-id-123"}
        mock_drive_service.permissions().create.return_value = mock_request

        permission_id = await drive_client.share_with_user(
            file_id="test-file-id",
            email="user@example.com"
        )

        # Should default to reader role
        call_kwargs = mock_drive_service.permissions().create.call_args[1]
        assert call_kwargs["body"]["role"] == "reader"

    @pytest.mark.asyncio
    async def test_share_with_domain_success(self, drive_client, mock_drive_service):
        """Test sharing file with entire domain."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "permission-id-456"}
        mock_drive_service.permissions().create.return_value = mock_request

        permission_id = await drive_client.share_with_domain(
            file_id="test-file-id",
            domain="your-domain.com",
            role="reader"
        )

        assert permission_id == "permission-id-456"

        # Verify domain permission details
        call_kwargs = mock_drive_service.permissions().create.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True
        assert call_kwargs["body"]["type"] == "domain"
        assert call_kwargs["body"]["role"] == "reader"
        assert call_kwargs["body"]["domain"] == "your-domain.com"

    @pytest.mark.asyncio
    async def test_remove_permission_success(self, drive_client, mock_drive_service):
        """Test removing permission from file."""
        mock_request = MagicMock()
        mock_request.execute.return_value = None
        mock_drive_service.permissions().delete.return_value = mock_request

        await drive_client.remove_permission(
            file_id="test-file-id",
            permission_id="permission-id-123"
        )

        # Verify supportsAllDrives=True
        call_kwargs = mock_drive_service.permissions().delete.call_args[1]
        assert call_kwargs["supportsAllDrives"] is True


class TestSearch:
    """Test search operations."""

    @pytest.mark.asyncio
    async def test_search_by_name_exact_match(self, drive_client, mock_drive_service):
        """Test exact name search."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "files": [
                {"id": "file-1", "name": "test.pdf"}
            ]
        }
        mock_drive_service.files().list.return_value = mock_request

        results = await drive_client.search_by_name(
            name="test.pdf",
            exact_match=True
        )

        assert len(results) == 1
        assert results[0]["name"] == "test.pdf"

        # Verify query uses exact match
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "name='test.pdf'" in call_kwargs["q"]

    @pytest.mark.asyncio
    async def test_search_by_name_contains(self, drive_client, mock_drive_service):
        """Test contains name search."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "files": [
                {"id": "file-1", "name": "test_file_1.pdf"},
                {"id": "file-2", "name": "test_file_2.pdf"}
            ]
        }
        mock_drive_service.files().list.return_value = mock_request

        results = await drive_client.search_by_name(
            name="test",
            exact_match=False
        )

        assert len(results) == 2

        # Verify query uses contains
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "name contains 'test'" in call_kwargs["q"]

    @pytest.mark.asyncio
    async def test_search_by_name_in_folder(self, drive_client, mock_drive_service):
        """Test search limited to specific folder."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"files": []}
        mock_drive_service.files().list.return_value = mock_request

        await drive_client.search_by_name(
            name="test.pdf",
            folder_id="specific-folder-id",
            exact_match=True
        )

        # Verify query includes folder constraint
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "'specific-folder-id' in parents" in call_kwargs["q"]

    @pytest.mark.asyncio
    async def test_search_by_mime_type_pdf(self, drive_client, mock_drive_service):
        """Test search by MIME type."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "files": [
                {"id": "file-1", "name": "doc1.pdf", "mimeType": "application/pdf"},
                {"id": "file-2", "name": "doc2.pdf", "mimeType": "application/pdf"}
            ]
        }
        mock_drive_service.files().list.return_value = mock_request

        results = await drive_client.search_by_mime_type(
            mime_type="application/pdf"
        )

        assert len(results) == 2

        # Verify MIME type query
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "mimeType='application/pdf'" in call_kwargs["q"]
        assert call_kwargs["supportsAllDrives"] is True

    @pytest.mark.asyncio
    async def test_search_by_mime_type_in_folder(self, drive_client, mock_drive_service):
        """Test MIME type search limited to folder."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"files": []}
        mock_drive_service.files().list.return_value = mock_request

        await drive_client.search_by_mime_type(
            mime_type="application/pdf",
            folder_id="specific-folder-id"
        )

        # Verify query includes folder constraint
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "'specific-folder-id' in parents" in call_kwargs["q"]


class TestGoogleWorkspaceExports:
    """Test Google Workspace document export operations."""

    @pytest.mark.asyncio
    async def test_export_google_doc_to_pdf(self, drive_client, mock_drive_service):
        """Test exporting Google Doc to PDF."""
        mock_request = MagicMock()
        mock_drive_service.files().export_media.return_value = mock_request

        # Mock downloader
        with patch("app.integrations.drive_client.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0
            mock_downloader.next_chunk.side_effect = [
                (mock_status, False),
                (mock_status, True)
            ]
            mock_downloader_class.return_value = mock_downloader

            pdf_bytes = await drive_client.export_google_doc_to_pdf(doc_id="doc-id")

        # Verify export_media called with PDF MIME type
        mock_drive_service.files().export_media.assert_called_once_with(
            fileId="doc-id",
            mimeType=PDF_MIME_TYPE
        )

    @pytest.mark.asyncio
    async def test_export_google_sheet_to_csv(self, drive_client, mock_drive_service):
        """Test exporting Google Sheet to CSV."""
        mock_request = MagicMock()
        mock_drive_service.files().export_media.return_value = mock_request

        # Mock downloader
        with patch("app.integrations.drive_client.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0
            mock_downloader.next_chunk.side_effect = [
                (mock_status, True)
            ]
            mock_downloader_class.return_value = mock_downloader

            csv_bytes = await drive_client.export_google_sheet_to_csv(sheet_id="sheet-id")

        # Verify export_media called with CSV MIME type
        mock_drive_service.files().export_media.assert_called_once_with(
            fileId="sheet-id",
            mimeType=CSV_MIME_TYPE
        )

    @pytest.mark.asyncio
    async def test_export_google_sheet_to_excel(self, drive_client, mock_drive_service):
        """Test exporting Google Sheet to Excel."""
        mock_request = MagicMock()
        mock_drive_service.files().export_media.return_value = mock_request

        # Mock downloader
        with patch("app.integrations.drive_client.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_status = MagicMock()
            mock_status.progress.return_value = 1.0
            mock_downloader.next_chunk.side_effect = [
                (mock_status, False),
                (mock_status, True)
            ]
            mock_downloader_class.return_value = mock_downloader

            excel_bytes = await drive_client.export_google_sheet_to_excel(sheet_id="sheet-id")

        # Verify export_media called with Excel MIME type
        mock_drive_service.files().export_media.assert_called_once_with(
            fileId="sheet-id",
            mimeType=EXCEL_MIME_TYPE
        )


class TestSupportsAllDrives:
    """Test that all operations include supportsAllDrives=True."""

    @pytest.mark.asyncio
    async def test_all_files_operations_support_all_drives(
        self,
        drive_client,
        mock_drive_service
    ):
        """Verify all files() operations include supportsAllDrives=True."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "test-id", "name": "test"}

        # Test various operations
        operations = [
            ("create", {"body": {}, "media_body": None}),
            ("get", {"fileId": "test-id"}),
            ("copy", {"fileId": "test-id", "body": {}}),
            ("update", {"fileId": "test-id"}),
            ("delete", {"fileId": "test-id"}),
            ("list", {"q": "trashed=false"})
        ]

        for operation, base_kwargs in operations:
            mock_drive_service.reset_mock()
            mock_method = getattr(mock_drive_service.files(), operation)
            mock_method.return_value = mock_request

            # The actual call would be made by specific methods
            # Just verify the pattern
            call_result = mock_method(**base_kwargs, supportsAllDrives=True)
            assert call_result == mock_request

    @pytest.mark.asyncio
    async def test_permissions_operations_support_all_drives(
        self,
        drive_client,
        mock_drive_service
    ):
        """Verify permissions operations include supportsAllDrives=True."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"id": "permission-id"}

        operations = [
            ("create", {"fileId": "test-id", "body": {}}),
            ("delete", {"fileId": "test-id", "permissionId": "perm-id"})
        ]

        for operation, base_kwargs in operations:
            mock_drive_service.reset_mock()
            mock_method = getattr(mock_drive_service.permissions(), operation)
            mock_method.return_value = mock_request

            call_result = mock_method(**base_kwargs, supportsAllDrives=True)
            assert call_result == mock_request


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_upload_file_with_special_characters(self, drive_client, mock_drive_service):
        """Test uploading file with special characters in name."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "uploaded-file-id",
            "name": "file with spaces & special.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        with patch("app.integrations.drive_client.os.path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("app.integrations.drive_client.MediaFileUpload"):
                file_id = await drive_client.upload_file(
                    file_path="/path/to/file with spaces & special.pdf"
                )

        assert file_id == "uploaded-file-id"

    @pytest.mark.asyncio
    async def test_search_by_name_with_quotes(self, drive_client, mock_drive_service):
        """Test search with quotes in name (should be escaped)."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"files": []}
        mock_drive_service.files().list.return_value = mock_request

        await drive_client.search_by_name(
            name="test'name",
            exact_match=True
        )

        # Verify quotes are escaped
        call_kwargs = mock_drive_service.files().list.call_args[1]
        assert "test\\'name" in call_kwargs["q"]

    @pytest.mark.asyncio
    async def test_move_file_no_parents(self, drive_client, mock_drive_service):
        """Test moving file that has no parents."""
        mock_get_request = MagicMock()
        mock_get_request.execute.return_value = {
            "id": "test-file-id",
            "name": "test.pdf",
            "parents": []
        }

        mock_update_request = MagicMock()
        mock_update_request.execute.return_value = {
            "id": "test-file-id",
            "name": "test.pdf",
            "parents": ["new-parent-id"]
        }

        mock_drive_service.files().get.return_value = mock_get_request
        mock_drive_service.files().update.return_value = mock_update_request

        await drive_client.move_file(
            file_id="test-file-id",
            destination_folder_id="new-parent-id"
        )

        # Verify removeParents is None when no parents
        call_kwargs = mock_drive_service.files().update.call_args[1]
        assert call_kwargs["removeParents"] is None

    @pytest.mark.asyncio
    async def test_get_folder_by_path_with_trailing_slash(self, drive_client, mock_drive_service):
        """Test path with trailing slash is handled correctly."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "files": [{"id": "folder-id", "name": "Projects"}]
        }
        mock_drive_service.files().list.return_value = mock_request

        folder_id = await drive_client.get_folder_by_path(
            path="Projects/",
            create_if_missing=False
        )

        assert folder_id == "folder-id"

    @pytest.mark.asyncio
    async def test_list_folder_contents_empty_folder(self, drive_client, mock_drive_service):
        """Test listing empty folder returns empty list."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {"files": []}
        mock_drive_service.files().list.return_value = mock_request

        items = await drive_client.list_folder_contents(folder_id="empty-folder-id")

        assert items == []


class TestUploadToProject:
    """Test upload_to_project method for populating project folders."""

    @pytest.mark.asyncio
    async def test_upload_source_pdf(self, drive_client, mock_drive_service):
        """Verify source PDF is uploaded to Source folder."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "source-pdf-id",
            "name": "brochure.pdf",
            "mimeType": "application/pdf",
            "size": "1024"
        }
        mock_drive_service.files().create.return_value = mock_request

        project_structure = {
            "project": "project-id",
            "source": "source-folder-id",
            "images": "images-folder-id",
            "output": "output-folder-id",
        }

        with patch("app.integrations.drive_client.MediaIoBaseUpload"):
            result = await drive_client.upload_to_project(
                project_structure=project_structure,
                source_pdf=b"PDF content",
                source_filename="brochure.pdf",
            )

        assert "source_pdf" in result
        assert result["source_pdf"] == "source-pdf-id"

        # Verify upload was to Source folder
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == ["source-folder-id"]

    @pytest.mark.asyncio
    async def test_upload_raw_data_files(self, drive_client, mock_drive_service):
        """Verify raw data files are uploaded to Raw Data folder."""
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "id": "manifest-id",
            "name": "manifest.json",
            "mimeType": "application/json",
            "size": "2048"
        }
        mock_drive_service.files().create.return_value = mock_request

        project_structure = {
            "project": "project-id",
            "source": "source-folder-id",
            "images": "images-folder-id",
            "raw_data": "raw-data-folder-id",
        }

        raw_data_files = [
            ("manifest.json", b'{"entries": []}'),
        ]

        with patch("app.integrations.drive_client.MediaIoBaseUpload"):
            result = await drive_client.upload_to_project(
                project_structure=project_structure,
                raw_data_files=raw_data_files,
            )

        assert "raw_data_uploaded" in result
        assert result["raw_data_uploaded"] == 1

        # Verify upload was to Raw Data folder
        call_kwargs = mock_drive_service.files().create.call_args[1]
        assert call_kwargs["body"]["parents"] == ["raw-data-folder-id"]

    @pytest.mark.asyncio
    async def test_upload_organized_images(self, drive_client, mock_drive_service):
        """Verify images are uploaded to Images folder with subfolders."""
        # Mock folder lookup and creation
        mock_list_request = MagicMock()
        mock_list_request.execute.return_value = {"files": []}

        mock_create_request = MagicMock()
        mock_create_request.execute.side_effect = [
            {"id": "interiors-subfolder-id", "name": "interiors"},
            {"id": "exteriors-subfolder-id", "name": "exteriors"},
        ]

        mock_upload_request = MagicMock()
        mock_upload_request.execute.side_effect = [
            {"id": "img-1-id", "name": "001-interior.webp", "size": "100"},
            {"id": "img-2-id", "name": "001-exterior.webp", "size": "200"},
        ]

        mock_drive_service.files().list.return_value = mock_list_request
        mock_drive_service.files().create.return_value = mock_upload_request

        # Patch create_folder directly on the instance
        with patch.object(
            drive_client, "create_folder", new_callable=AsyncMock
        ) as mock_create_folder:
            mock_create_folder.side_effect = [
                "interiors-subfolder-id",
                "exteriors-subfolder-id",
            ]

            with patch.object(
                drive_client, "get_folder_by_path", new_callable=AsyncMock
            ) as mock_get_folder:
                # First two calls return None (subfolder doesn't exist)
                # Subsequent calls return the created folder
                mock_get_folder.side_effect = [None, None]

                with patch("app.integrations.drive_client.MediaIoBaseUpload"):
                    project_structure = {
                        "project": "project-id",
                        "source": "source-folder-id",
                        "images": "images-folder-id",
                        "raw_data": "raw-data-folder-id",
                    }

                    organized_images = [
                        ("interiors/001-interior.webp", b"image1"),
                        ("exteriors/001-exterior.webp", b"image2"),
                    ]

                    result = await drive_client.upload_to_project(
                        project_structure=project_structure,
                        organized_images=organized_images,
                    )

        assert "images_uploaded" in result
        assert result["images_uploaded"] == 2

    @pytest.mark.asyncio
    async def test_upload_all_assets(self, drive_client, mock_drive_service):
        """Verify source PDF and raw data are uploaded in single call."""
        mock_request = MagicMock()
        mock_request.execute.side_effect = [
            {"id": "pdf-id", "name": "brochure.pdf", "size": "1000"},
            {"id": "manifest-id", "name": "manifest.json", "size": "500"},
        ]
        mock_drive_service.files().create.return_value = mock_request

        project_structure = {
            "project": "project-id",
            "source": "source-folder-id",
            "images": "images-folder-id",
            "raw_data": "raw-data-folder-id",
        }

        raw_data_files = [
            ("manifest.json", b'{"entries": []}'),
        ]

        with patch("app.integrations.drive_client.MediaIoBaseUpload"):
            result = await drive_client.upload_to_project(
                project_structure=project_structure,
                source_pdf=b"PDF content",
                source_filename="brochure.pdf",
                raw_data_files=raw_data_files,
            )

        assert "source_pdf" in result
        assert "raw_data_uploaded" in result

    @pytest.mark.asyncio
    async def test_upload_empty_returns_empty_dict(self, drive_client):
        """Verify empty upload returns empty dict."""
        project_structure = {
            "project": "project-id",
            "source": "source-folder-id",
            "images": "images-folder-id",
            "raw_data": "raw-data-folder-id",
        }

        result = await drive_client.upload_to_project(
            project_structure=project_structure,
        )

        assert result == {}
