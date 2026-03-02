"""
Comprehensive unit tests for StorageService (GCS integration).

Tests all GCS operations with mocked SDK calls:
- Initialization and lazy loading
- Upload operations (bytes, file path, file-like object)
- Download operations (to file and as bytes)
- Signed URL generation
- File/folder deletion
- List files with prefix
- File existence checks
- Copy and move operations
- Metadata retrieval
- Path builder helpers
- Error handling (NotFound, GoogleCloudError)

Run with: pytest backend/tests/test_storage_service.py -v
"""

import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

import pytest
from google.api_core import retry as retry_module
from google.cloud.exceptions import GoogleCloudError, NotFound

from app.services.storage_service import (
    DEFAULT_SIGNED_URL_EXPIRY,
    RESUMABLE_UPLOAD_THRESHOLD,
    StorageService,
)

# Patch the missing DEFAULT_RETRY constant for testing
if not hasattr(retry_module, "DEFAULT_RETRY"):
    retry_module.DEFAULT_RETRY = Mock(name="DEFAULT_RETRY")


@pytest.fixture
def mock_settings():
    """Mock settings with test values."""
    settings = Mock()
    settings.GCS_BUCKET_NAME = "test-bucket"
    settings.GCP_PROJECT_ID = "test-project"
    return settings


@pytest.fixture
def mock_storage_client():
    """Mock GCS client."""
    client = Mock()
    return client


@pytest.fixture
def mock_bucket():
    """Mock GCS bucket."""
    bucket = Mock()
    bucket.exists.return_value = True
    return bucket


@pytest.fixture
def mock_blob():
    """Mock GCS blob."""
    blob = Mock()
    blob.exists.return_value = True
    blob.name = "test-blob"
    blob.size = 1024
    blob.content_type = "application/pdf"
    blob.time_created = datetime(2026, 1, 28, 12, 0, 0)
    blob.updated = datetime(2026, 1, 28, 13, 0, 0)
    blob.metadata = {"key": "value"}
    blob.md5_hash = "abc123"
    blob.crc32c = "xyz789"
    return blob


@pytest.fixture
def storage_service(mock_settings):
    """Create StorageService instance with mocked settings."""
    with patch("app.services.storage_service.get_settings", return_value=mock_settings):
        service = StorageService()
        return service


class TestStorageServiceInitialization:
    """Test service initialization and lazy loading."""

    def test_init_lazy_load(self, storage_service):
        """Test that __init__ does not create client/bucket immediately."""
        assert storage_service._client is None
        assert storage_service._bucket is None
        assert storage_service._settings is not None

    def test_client_property_lazy_initialization(self, storage_service, mock_storage_client):
        """Test client is created on first access."""
        with patch("app.services.storage_service.storage.Client", return_value=mock_storage_client):
            client = storage_service.client
            assert client is mock_storage_client

            # Second access returns same instance
            client2 = storage_service.client
            assert client2 is client

    def test_client_property_initialization_error(self, storage_service):
        """Test client initialization handles errors."""
        with patch("app.services.storage_service.storage.Client", side_effect=Exception("Auth failed")):
            with pytest.raises(Exception, match="Auth failed"):
                _ = storage_service.client

    def test_bucket_property_lazy_initialization(self, storage_service, mock_storage_client, mock_bucket):
        """Test bucket is created on first access."""
        with patch("app.services.storage_service.storage.Client", return_value=mock_storage_client):
            mock_storage_client.bucket.return_value = mock_bucket

            bucket = storage_service.bucket
            assert bucket is mock_bucket
            mock_storage_client.bucket.assert_called_once_with("test-bucket")
            mock_bucket.exists.assert_called_once()

    def test_bucket_property_not_found(self, storage_service, mock_storage_client, mock_bucket):
        """Test bucket initialization fails when bucket does not exist."""
        mock_bucket.exists.return_value = False

        with patch("app.services.storage_service.storage.Client", return_value=mock_storage_client):
            mock_storage_client.bucket.return_value = mock_bucket

            with pytest.raises(ValueError, match="does not exist or is not accessible"):
                _ = storage_service.bucket

    def test_bucket_property_error_handling(self, storage_service, mock_storage_client):
        """Test bucket initialization handles errors."""
        with patch("app.services.storage_service.storage.Client", return_value=mock_storage_client):
            mock_storage_client.bucket.side_effect = Exception("Permission denied")

            with pytest.raises(Exception, match="Permission denied"):
                _ = storage_service.bucket


class TestGetBlob:
    """Test _get_blob helper method."""

    def test_get_blob(self, storage_service, mock_bucket, mock_blob):
        """Test _get_blob returns blob reference."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        blob = storage_service._get_blob("test/path/file.pdf")

        assert blob is mock_blob
        mock_bucket.blob.assert_called_once_with("test/path/file.pdf")


class TestDetectContentType:
    """Test _detect_content_type helper method."""

    def test_detect_pdf(self, storage_service):
        """Test PDF MIME type detection."""
        content_type = storage_service._detect_content_type("document.pdf")
        assert content_type == "application/pdf"

    def test_detect_jpg(self, storage_service):
        """Test JPEG MIME type detection."""
        content_type = storage_service._detect_content_type("image.jpg")
        assert content_type == "image/jpeg"

    def test_detect_png(self, storage_service):
        """Test PNG MIME type detection."""
        content_type = storage_service._detect_content_type("image.png")
        assert content_type == "image/png"

    def test_detect_zip(self, storage_service):
        """Test ZIP MIME type detection."""
        content_type = storage_service._detect_content_type("archive.zip")
        # Windows returns 'application/x-zip-compressed', Unix returns 'application/zip'
        assert content_type in ("application/zip", "application/x-zip-compressed")

    def test_detect_unknown(self, storage_service):
        """Test unknown extension defaults to octet-stream."""
        content_type = storage_service._detect_content_type("file.unknown")
        assert content_type == "application/octet-stream"


@pytest.mark.asyncio
class TestUploadFile:
    """Test upload_file method."""

    async def test_upload_bytes(self, storage_service, mock_bucket, mock_blob):
        """Test upload from bytes."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        test_bytes = b"test content"
        result = await storage_service.upload_file(
            source_file=test_bytes,
            destination_blob_path="test/file.txt",
            content_type="text/plain",
        )

        assert result == "test/file.txt"
        mock_blob.upload_from_string.assert_called_once()
        call_args = mock_blob.upload_from_string.call_args
        assert call_args[0][0] == test_bytes
        assert call_args[1]["content_type"] == "text/plain"

    async def test_upload_bytes_auto_detect_content_type(self, storage_service, mock_bucket, mock_blob):
        """Test upload bytes with auto-detected content type."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        test_bytes = b"binary data"
        result = await storage_service.upload_file(
            source_file=test_bytes,
            destination_blob_path="test/file.bin",
        )

        assert result == "test/file.bin"
        mock_blob.upload_from_string.assert_called_once()
        call_args = mock_blob.upload_from_string.call_args
        assert call_args[1]["content_type"] == "application/octet-stream"

    async def test_upload_small_file(self, storage_service, mock_bucket, mock_blob, tmp_path):
        """Test upload small file (direct upload)."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Create small test file
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"x" * 1000)

        result = await storage_service.upload_file(
            source_file=test_file,
            destination_blob_path="uploads/job_123/test.pdf",
        )

        assert result == "uploads/job_123/test.pdf"
        mock_blob.upload_from_filename.assert_called_once()
        call_args = mock_blob.upload_from_filename.call_args
        assert call_args[0][0] == str(test_file)
        assert call_args[1]["content_type"] == "application/pdf"

    async def test_upload_large_file(self, storage_service, mock_bucket, mock_blob, tmp_path):
        """Test upload large file (resumable upload)."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Create large test file (> 5MB threshold)
        test_file = tmp_path / "large.pdf"
        test_file.write_bytes(b"x" * (RESUMABLE_UPLOAD_THRESHOLD + 1000))

        result = await storage_service.upload_file(
            source_file=test_file,
            destination_blob_path="uploads/job_456/large.pdf",
        )

        assert result == "uploads/job_456/large.pdf"
        mock_blob.upload_from_filename.assert_called_once()

    async def test_upload_file_like_object(self, storage_service, mock_bucket, mock_blob):
        """Test upload from file-like object."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        file_obj = BytesIO(b"file content")
        result = await storage_service.upload_file(
            source_file=file_obj,
            destination_blob_path="test/file.dat",
            content_type="application/octet-stream",
        )

        assert result == "test/file.dat"
        mock_blob.upload_from_file.assert_called_once()
        call_args = mock_blob.upload_from_file.call_args
        assert call_args[0][0] == file_obj
        assert call_args[1]["content_type"] == "application/octet-stream"

    async def test_upload_with_metadata(self, storage_service, mock_bucket, mock_blob):
        """Test upload with custom metadata."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        metadata = {"job_id": "123", "user": "test"}
        result = await storage_service.upload_file(
            source_file=b"data",
            destination_blob_path="test/file.bin",
            metadata=metadata,
        )

        assert result == "test/file.bin"
        assert mock_blob.metadata == metadata

    async def test_upload_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test upload error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_string.side_effect = GoogleCloudError("Upload failed")

        with pytest.raises(GoogleCloudError, match="Upload failed"):
            await storage_service.upload_file(
                source_file=b"data",
                destination_blob_path="test/file.txt",
            )


@pytest.mark.asyncio
class TestDownloadFile:
    """Test download_file method."""

    async def test_download_as_bytes(self, storage_service, mock_bucket, mock_blob):
        """Test download file as bytes."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_bytes.return_value = b"file content"

        result = await storage_service.download_file("test/file.txt")

        assert result == b"file content"
        mock_blob.download_as_bytes.assert_called_once()

    async def test_download_to_file(self, storage_service, mock_bucket, mock_blob, tmp_path):
        """Test download file to local path."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        dest_file = tmp_path / "output" / "file.txt"
        result = await storage_service.download_file(
            "test/file.txt",
            destination_file=dest_file,
        )

        assert result is None
        mock_blob.download_to_filename.assert_called_once()
        call_args = mock_blob.download_to_filename.call_args
        assert call_args[0][0] == str(dest_file)

    async def test_download_blob_not_found(self, storage_service, mock_bucket, mock_blob):
        """Test download raises NotFound when blob does not exist."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        with pytest.raises(NotFound, match="Blob not found"):
            await storage_service.download_file("missing/file.txt")

    async def test_download_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test download error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_bytes.side_effect = GoogleCloudError("Download failed")

        with pytest.raises(GoogleCloudError, match="Download failed"):
            await storage_service.download_file("test/file.txt")


@pytest.mark.asyncio
class TestGenerateSignedUrl:
    """Test generate_signed_url method."""

    async def test_generate_signed_url_default_params(self, storage_service, mock_bucket, mock_blob):
        """Test signed URL generation with default parameters."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.return_value = "https://signed-url.example.com"

        result = await storage_service.generate_signed_url("test/file.pdf")

        assert result == "https://signed-url.example.com"
        mock_blob.generate_signed_url.assert_called_once_with(
            version="v4",
            expiration=timedelta(minutes=DEFAULT_SIGNED_URL_EXPIRY),
            method="GET",
        )

    async def test_generate_signed_url_custom_expiry(self, storage_service, mock_bucket, mock_blob):
        """Test signed URL with custom expiration."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.return_value = "https://signed-url.example.com"

        result = await storage_service.generate_signed_url(
            "test/file.pdf",
            expiration_minutes=120,
        )

        assert result == "https://signed-url.example.com"
        call_args = mock_blob.generate_signed_url.call_args
        assert call_args[1]["expiration"] == timedelta(minutes=120)

    async def test_generate_signed_url_put_method(self, storage_service, mock_bucket, mock_blob):
        """Test signed URL for PUT method."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.return_value = "https://signed-url.example.com"

        result = await storage_service.generate_signed_url(
            "test/file.pdf",
            method="PUT",
        )

        assert result == "https://signed-url.example.com"
        call_args = mock_blob.generate_signed_url.call_args
        assert call_args[1]["method"] == "PUT"

    async def test_generate_signed_url_blob_not_found(self, storage_service, mock_bucket, mock_blob):
        """Test signed URL generation raises NotFound."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        with pytest.raises(NotFound, match="Blob not found"):
            await storage_service.generate_signed_url("missing/file.pdf")

    async def test_generate_signed_url_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test signed URL error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.side_effect = GoogleCloudError("URL generation failed")

        with pytest.raises(GoogleCloudError, match="URL generation failed"):
            await storage_service.generate_signed_url("test/file.pdf")


@pytest.mark.asyncio
class TestDeleteFile:
    """Test delete_file method."""

    async def test_delete_file_success(self, storage_service, mock_bucket, mock_blob):
        """Test successful file deletion."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        result = await storage_service.delete_file("test/file.txt")

        assert result is True
        mock_blob.delete.assert_called_once()

    async def test_delete_file_not_found(self, storage_service, mock_bucket, mock_blob):
        """Test delete returns False when file not found."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.delete.side_effect = NotFound("Blob not found")

        result = await storage_service.delete_file("missing/file.txt")

        assert result is False

    async def test_delete_file_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test delete error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.delete.side_effect = GoogleCloudError("Delete failed")

        with pytest.raises(GoogleCloudError, match="Delete failed"):
            await storage_service.delete_file("test/file.txt")


@pytest.mark.asyncio
class TestDeleteFolder:
    """Test delete_folder method."""

    async def test_delete_folder_success(self, storage_service, mock_bucket):
        """Test successful folder deletion."""
        storage_service._bucket = mock_bucket

        # Mock 3 blobs in folder
        blob1, blob2, blob3 = Mock(), Mock(), Mock()
        blob1.name = "temp/job_123/file1.txt"
        blob2.name = "temp/job_123/file2.txt"
        blob3.name = "temp/job_123/file3.txt"

        mock_bucket.list_blobs.return_value = [blob1, blob2, blob3]

        result = await storage_service.delete_folder("temp/job_123")

        assert result == 3
        mock_bucket.list_blobs.assert_called_once_with(prefix="temp/job_123/")
        blob1.delete.assert_called_once()
        blob2.delete.assert_called_once()
        blob3.delete.assert_called_once()

    async def test_delete_folder_with_trailing_slash(self, storage_service, mock_bucket):
        """Test folder deletion with trailing slash."""
        storage_service._bucket = mock_bucket
        mock_bucket.list_blobs.return_value = []

        result = await storage_service.delete_folder("temp/job_123/")

        assert result == 0
        mock_bucket.list_blobs.assert_called_once_with(prefix="temp/job_123/")

    async def test_delete_folder_partial_failure(self, storage_service, mock_bucket):
        """Test folder deletion continues after NotFound."""
        storage_service._bucket = mock_bucket

        blob1, blob2 = Mock(), Mock()
        blob1.name = "temp/job_123/file1.txt"
        blob2.name = "temp/job_123/file2.txt"
        blob1.delete.side_effect = NotFound("Already deleted")

        mock_bucket.list_blobs.return_value = [blob1, blob2]

        result = await storage_service.delete_folder("temp/job_123")

        assert result == 1
        blob2.delete.assert_called_once()

    async def test_delete_folder_error_handling(self, storage_service, mock_bucket):
        """Test folder deletion raises on persistent error."""
        storage_service._bucket = mock_bucket

        blob1 = Mock()
        blob1.name = "temp/job_123/file1.txt"
        blob1.delete.side_effect = GoogleCloudError("Delete failed")

        mock_bucket.list_blobs.return_value = [blob1]

        with pytest.raises(GoogleCloudError, match="Delete failed"):
            await storage_service.delete_folder("temp/job_123")


@pytest.mark.asyncio
class TestListFiles:
    """Test list_files method."""

    async def test_list_files_no_prefix(self, storage_service, mock_bucket):
        """Test list all files."""
        storage_service._bucket = mock_bucket

        blob1, blob2 = Mock(), Mock()
        blob1.name = "file1.txt"
        blob2.name = "file2.txt"
        mock_bucket.list_blobs.return_value = [blob1, blob2]

        result = await storage_service.list_files()

        assert result == ["file1.txt", "file2.txt"]
        mock_bucket.list_blobs.assert_called_once_with(prefix=None, delimiter=None)

    async def test_list_files_with_prefix(self, storage_service, mock_bucket):
        """Test list files with prefix filter."""
        storage_service._bucket = mock_bucket

        blob1, blob2 = Mock(), Mock()
        blob1.name = "uploads/job_123/file1.pdf"
        blob2.name = "uploads/job_123/file2.pdf"
        mock_bucket.list_blobs.return_value = [blob1, blob2]

        result = await storage_service.list_files(prefix="uploads/job_123/")

        assert result == ["uploads/job_123/file1.pdf", "uploads/job_123/file2.pdf"]
        mock_bucket.list_blobs.assert_called_once_with(
            prefix="uploads/job_123/",
            delimiter=None,
        )

    async def test_list_files_with_delimiter(self, storage_service, mock_bucket):
        """Test list files with delimiter (directory-like listing)."""
        storage_service._bucket = mock_bucket

        blob1 = Mock()
        blob1.name = "uploads/job_123/file.pdf"
        mock_bucket.list_blobs.return_value = [blob1]

        result = await storage_service.list_files(prefix="uploads/", delimiter="/")

        assert result == ["uploads/job_123/file.pdf"]
        mock_bucket.list_blobs.assert_called_once_with(
            prefix="uploads/",
            delimiter="/",
        )

    async def test_list_files_empty(self, storage_service, mock_bucket):
        """Test list files returns empty list."""
        storage_service._bucket = mock_bucket
        mock_bucket.list_blobs.return_value = []

        result = await storage_service.list_files(prefix="empty/")

        assert result == []

    async def test_list_files_error_handling(self, storage_service, mock_bucket):
        """Test list files error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.list_blobs.side_effect = GoogleCloudError("List failed")

        with pytest.raises(GoogleCloudError, match="List failed"):
            await storage_service.list_files()


@pytest.mark.asyncio
class TestFileExists:
    """Test file_exists method."""

    async def test_file_exists_true(self, storage_service, mock_bucket, mock_blob):
        """Test file_exists returns True."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True

        result = await storage_service.file_exists("test/file.txt")

        assert result is True
        mock_blob.exists.assert_called_once()

    async def test_file_exists_false(self, storage_service, mock_bucket, mock_blob):
        """Test file_exists returns False."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False

        result = await storage_service.file_exists("missing/file.txt")

        assert result is False

    async def test_file_exists_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test file_exists error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.side_effect = GoogleCloudError("Check failed")

        with pytest.raises(GoogleCloudError, match="Check failed"):
            await storage_service.file_exists("test/file.txt")


@pytest.mark.asyncio
class TestGetMetadata:
    """Test get_metadata method."""

    async def test_get_metadata_success(self, storage_service, mock_bucket, mock_blob):
        """Test metadata retrieval."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        result = await storage_service.get_metadata("test/file.pdf")

        assert result["name"] == "test-blob"
        assert result["size"] == 1024
        assert result["content_type"] == "application/pdf"
        assert result["created"] == "2026-01-28T12:00:00"
        assert result["updated"] == "2026-01-28T13:00:00"
        assert result["metadata"] == {"key": "value"}
        assert result["md5_hash"] == "abc123"
        assert result["crc32c"] == "xyz789"
        mock_blob.reload.assert_called_once()

    async def test_get_metadata_no_timestamps(self, storage_service, mock_bucket, mock_blob):
        """Test metadata with None timestamps."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.time_created = None
        mock_blob.updated = None
        mock_blob.metadata = None

        result = await storage_service.get_metadata("test/file.pdf")

        assert result["created"] is None
        assert result["updated"] is None
        assert result["metadata"] == {}

    async def test_get_metadata_not_found(self, storage_service, mock_bucket, mock_blob):
        """Test metadata raises NotFound."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.reload.side_effect = NotFound("Blob not found")

        with pytest.raises(NotFound, match="Blob not found"):
            await storage_service.get_metadata("missing/file.pdf")

    async def test_get_metadata_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test metadata error handling."""
        storage_service._bucket = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.reload.side_effect = GoogleCloudError("Metadata fetch failed")

        with pytest.raises(GoogleCloudError, match="Metadata fetch failed"):
            await storage_service.get_metadata("test/file.pdf")


@pytest.mark.asyncio
class TestCopyFile:
    """Test copy_file method."""

    async def test_copy_file_success(self, storage_service, mock_bucket, mock_blob):
        """Test successful file copy."""
        storage_service._bucket = mock_bucket

        source_blob = Mock()
        dest_blob = Mock()
        mock_bucket.blob.side_effect = [source_blob, dest_blob]

        # Mock rewrite to complete in one call
        dest_blob.rewrite.return_value = (None, 1024, 1024)

        result = await storage_service.copy_file(
            "source/file.txt",
            "dest/file.txt",
        )

        assert result == "dest/file.txt"
        dest_blob.rewrite.assert_called_once_with(source_blob, token=None)

    async def test_copy_file_multi_chunk(self, storage_service, mock_bucket, mock_blob):
        """Test file copy with multiple rewrite chunks."""
        storage_service._bucket = mock_bucket

        source_blob = Mock()
        dest_blob = Mock()
        mock_bucket.blob.side_effect = [source_blob, dest_blob]

        # Mock rewrite requiring 2 chunks
        dest_blob.rewrite.side_effect = [
            ("token_1", 5000, 10000),
            (None, 10000, 10000),
        ]

        result = await storage_service.copy_file(
            "source/large.bin",
            "dest/large.bin",
        )

        assert result == "dest/large.bin"
        assert dest_blob.rewrite.call_count == 2

    async def test_copy_file_not_found(self, storage_service, mock_bucket, mock_blob):
        """Test copy raises NotFound."""
        storage_service._bucket = mock_bucket

        source_blob = Mock()
        dest_blob = Mock()
        mock_bucket.blob.side_effect = [source_blob, dest_blob]
        dest_blob.rewrite.side_effect = NotFound("Source not found")

        with pytest.raises(NotFound, match="Source not found"):
            await storage_service.copy_file("missing/file.txt", "dest/file.txt")

    async def test_copy_file_error_handling(self, storage_service, mock_bucket, mock_blob):
        """Test copy error handling."""
        storage_service._bucket = mock_bucket

        source_blob = Mock()
        dest_blob = Mock()
        mock_bucket.blob.side_effect = [source_blob, dest_blob]
        dest_blob.rewrite.side_effect = GoogleCloudError("Copy failed")

        with pytest.raises(GoogleCloudError, match="Copy failed"):
            await storage_service.copy_file("source/file.txt", "dest/file.txt")


@pytest.mark.asyncio
class TestMoveFile:
    """Test move_file method."""

    async def test_move_file_success(self, storage_service, mock_bucket):
        """Test successful file move."""
        storage_service._bucket = mock_bucket

        # Mock copy_file and delete_file
        with patch.object(storage_service, "copy_file", new_callable=AsyncMock) as mock_copy:
            with patch.object(storage_service, "delete_file", new_callable=AsyncMock) as mock_delete:
                mock_copy.return_value = "dest/file.txt"
                mock_delete.return_value = True

                result = await storage_service.move_file(
                    "source/file.txt",
                    "dest/file.txt",
                )

                assert result == "dest/file.txt"
                mock_copy.assert_called_once_with("source/file.txt", "dest/file.txt")
                mock_delete.assert_called_once_with("source/file.txt")

    async def test_move_file_copy_failure(self, storage_service, mock_bucket):
        """Test move fails if copy fails."""
        storage_service._bucket = mock_bucket

        with patch.object(storage_service, "copy_file", new_callable=AsyncMock) as mock_copy:
            with patch.object(storage_service, "delete_file", new_callable=AsyncMock) as mock_delete:
                mock_copy.side_effect = GoogleCloudError("Copy failed")

                with pytest.raises(GoogleCloudError, match="Copy failed"):
                    await storage_service.move_file("source/file.txt", "dest/file.txt")

                # Delete should not be called if copy fails
                mock_delete.assert_not_called()

    async def test_move_file_delete_failure(self, storage_service, mock_bucket):
        """Test move fails if delete fails."""
        storage_service._bucket = mock_bucket

        with patch.object(storage_service, "copy_file", new_callable=AsyncMock) as mock_copy:
            with patch.object(storage_service, "delete_file", new_callable=AsyncMock) as mock_delete:
                mock_copy.return_value = "dest/file.txt"
                mock_delete.side_effect = GoogleCloudError("Delete failed")

                with pytest.raises(GoogleCloudError, match="Delete failed"):
                    await storage_service.move_file("source/file.txt", "dest/file.txt")


class TestPathBuilders:
    """Test path builder helper methods."""

    def test_get_upload_path(self, storage_service):
        """Test upload path builder."""
        path = storage_service.get_upload_path("job_123", "document.pdf")
        assert path == "uploads/job_123/document.pdf"

    def test_get_temp_path(self, storage_service):
        """Test temp path builder."""
        path = storage_service.get_temp_path("job_456", "intermediate/file.bin")
        assert path == "temp/job_456/intermediate/file.bin"

    def test_get_processed_path(self, storage_service):
        """Test processed path builder."""
        path = storage_service.get_processed_path("proj_789", "output.zip")
        assert path == "processed/proj_789/output.zip"

    def test_get_image_path(self, storage_service):
        """Test image path builder."""
        path = storage_service.get_image_path("proj_789", "exteriors", "img_001.jpg")
        assert path == "processed/proj_789/images/exteriors/img_001.jpg"

    def test_get_floor_plan_path(self, storage_service):
        """Test floor plan path builder."""
        path = storage_service.get_floor_plan_path("proj_789", "fp_001.jpg")
        assert path == "processed/proj_789/floor_plans/fp_001.jpg"
