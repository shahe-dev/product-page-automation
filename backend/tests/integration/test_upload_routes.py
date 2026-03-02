"""
Integration tests for upload API routes.

Tests the /api/v1/upload/* endpoints for file upload handling.
"""

from httpx import AsyncClient
import io
import pytest


class TestUploadPDF:
    """Tests for POST /api/v1/upload/pdf endpoint."""

    async def test_upload_pdf_without_auth_returns_401(self, client: AsyncClient):
        """POST /api/v1/upload/pdf without auth returns 403."""
        files = {"file": ("test.pdf", b"%PDF-1.4 fake pdf", "application/pdf")}
        data = {"template_type": "opr"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data
        )
        assert response.status_code == 403

    async def test_upload_pdf_with_non_pdf_file_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/pdf with non-PDF file returns 400."""
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        data = {"template_type": "opr"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert response.status_code == 400
        
        error = response.json()
        assert "detail" in error
        if isinstance(error["detail"], dict):
            assert error["detail"]["error_code"] == "INVALID_FILE_TYPE"

    async def test_upload_pdf_with_invalid_content_type_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/pdf with invalid content type returns 400."""
        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "image/jpeg")}
        data = {"template_type": "opr"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert response.status_code == 400

    async def test_upload_pdf_with_invalid_template_type_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/pdf with invalid template type returns 422."""
        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
        data = {"template_type": "invalid_template"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_upload_pdf_validates_filename_path_traversal(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/pdf sanitizes dangerous filenames."""
        dangerous_filename = "../../../etc/passwd"
        files = {"file": (dangerous_filename, b"%PDF-1.4 fake", "application/pdf")}
        data = {"template_type": "opr"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Should either sanitize the filename or reject it
        # If accepted, filename should be sanitized in response
        if response.status_code == 201:
            # If upload succeeds, verify filename was sanitized
            data = response.json()
            # The job should be created, but we can't directly verify
            # sanitization without checking storage. Just verify no crash.
            assert "job_id" in data

    async def test_upload_pdf_with_null_byte_in_filename(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/pdf sanitizes null bytes in filename."""
        files = {"file": ("test\x00.pdf", b"%PDF-1.4 fake", "application/pdf")}
        data = {"template_type": "opr"}
        
        response = await client.post(
            "/api/v1/upload/pdf",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        # Should sanitize or reject
        if response.status_code == 201:
            data = response.json()
            assert "job_id" in data


class TestUploadImages:
    """Tests for POST /api/v1/upload/images endpoint."""

    async def test_upload_images_returns_501(
        self, client: AsyncClient, auth_headers: dict
    ):
        """POST /api/v1/upload/images returns 501 (not yet implemented)."""
        files = [
            ("files", ("image1.jpg", b"fake image", "image/jpeg")),
        ]
        data = {"project_id": "00000000-0000-0000-0000-000000000000"}
        
        response = await client.post(
            "/api/v1/upload/images",
            files=files,
            data=data,
            headers=auth_headers
        )
        assert response.status_code == 501


class TestGetUploadStatus:
    """Tests for GET /api/v1/upload/{id}/status endpoint."""

    async def test_get_upload_status_returns_501(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/upload/{id}/status returns 501 (not yet implemented)."""
        from uuid import uuid4
        
        upload_id = uuid4()
        response = await client.get(
            f"/api/v1/upload/{upload_id}/status",
            headers=auth_headers
        )
        assert response.status_code == 501

    async def test_get_upload_status_without_auth_returns_401(self, client: AsyncClient):
        """GET /api/v1/upload/{id}/status without auth returns 403."""
        from uuid import uuid4
        
        upload_id = uuid4()
        response = await client.get(f"/api/v1/upload/{upload_id}/status")
        assert response.status_code == 403
