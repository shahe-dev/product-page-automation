"""
Tests for the /upload/file endpoint.

This endpoint supports the multi-template pipeline by uploading files to GCS
and returning a gcs_url for use with /process/extract.
"""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_upload_file_returns_gcs_url(client, auth_headers):
    """Upload endpoint returns GCS URL for valid PDF."""
    # Create a minimal valid PDF (starts with %PDF)
    pdf_content = b"%PDF-1.4 fake pdf content for testing"

    with patch("app.api.routes.upload.StorageService") as MockStorage:
        mock_instance = MockStorage.return_value
        mock_instance.upload_file = AsyncMock(return_value="gs://test-bucket/uploads/test.pdf")

        response = await client.post(
            "/api/v1/upload/file",
            files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
            headers=auth_headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert "gcs_url" in data
    assert data["gcs_url"].startswith("gs://")
    assert "filename" in data
    assert "size" in data


@pytest.mark.asyncio
async def test_upload_file_rejects_non_pdf(client, auth_headers):
    """Upload endpoint rejects non-PDF files."""
    text_content = b"This is not a PDF file"

    response = await client.post(
        "/api/v1/upload/file",
        files={"file": ("test.txt", BytesIO(text_content), "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_file_requires_auth(client):
    """Upload endpoint requires authentication."""
    pdf_content = b"%PDF-1.4 fake pdf"

    response = await client.post(
        "/api/v1/upload/file",
        files={"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")},
        # No auth headers
    )

    # App returns 403 Forbidden for missing authentication
    assert response.status_code == 403
