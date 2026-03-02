"""
Tests for the downloads endpoint (ZIP asset download).
"""

import io
import zipfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def test_project(test_db: AsyncSession, test_user):
    """Create a test project with images and floor plans."""
    from app.models.database import Project, ProjectFloorPlan, ProjectImage
    from app.models.enums import (
        ImageCategory,
        TemplateType,
        WorkflowStatus,
    )

    now = datetime.now(timezone.utc)
    project = Project(
        name="Test Download Project",
        developer="Test Dev",
        location="Dubai Marina",
        emirate="Dubai",
        template_type=TemplateType.OPR,
        workflow_status=WorkflowStatus.DRAFT,
        created_by=test_user.id,
        is_active=True,
        property_types=[],
        unit_sizes=[],
        amenities=[],
        features=[],
        custom_fields={},
        generated_content={},
        created_at=now,
        updated_at=now,
    )
    test_db.add(project)
    await test_db.flush()

    # Add images
    img1 = ProjectImage(
        project_id=project.id,
        category=ImageCategory.EXTERIOR,
        image_url=f"materials/{project.id}/images/exterior/img_001.webp",
        file_size=1024,
        format="webp",
        display_order=0,
        created_at=now,
    )
    img2 = ProjectImage(
        project_id=project.id,
        category=ImageCategory.INTERIOR,
        image_url=f"materials/{project.id}/images/interior/img_002.webp",
        file_size=2048,
        format="webp",
        display_order=0,
        created_at=now,
    )
    img3 = ProjectImage(
        project_id=project.id,
        category=ImageCategory.AMENITY,
        image_url=f"materials/{project.id}/images/amenity/img_003.webp",
        file_size=512,
        format="webp",
        display_order=0,
        created_at=now,
    )

    # Add floor plan
    fp1 = ProjectFloorPlan(
        project_id=project.id,
        unit_type="1BR",
        bedrooms=1,
        bathrooms=1,
        image_url=f"materials/{project.id}/floor_plans/fp_001.webp",
        display_order=0,
        created_at=now,
    )

    test_db.add_all([img1, img2, img3, fp1])
    await test_db.commit()
    await test_db.refresh(project)
    return project, [img1, img2, img3], [fp1]


def _mock_download(blob_path: str):
    """Return fake bytes for a given blob path."""
    return f"fake-content-for-{blob_path}".encode()


@pytest.mark.asyncio
async def test_download_all_assets(client: AsyncClient, auth_headers, test_project):
    """ZIP contains all images + floor plans when downloading all."""
    project, images, floor_plans = test_project

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_mock_download)
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers["content-disposition"]
    assert "Test_Download_Project" in resp.headers["content-disposition"]

    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    # 3 images + 1 floor plan = 4 files
    assert len(names) == 4
    assert any("images/exterior/" in n for n in names)
    assert any("images/interior/" in n for n in names)
    assert any("images/amenity/" in n for n in names)
    assert any("floor_plans/" in n for n in names)


@pytest.mark.asyncio
async def test_download_category_filter(client: AsyncClient, auth_headers, test_project):
    """ZIP contains only images from the requested category."""
    project, images, _ = test_project

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_mock_download)
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets?category=exterior",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) == 1
    assert "images/exterior/" in names[0]


@pytest.mark.asyncio
async def test_download_floor_plan_category(client: AsyncClient, auth_headers, test_project):
    """Floor plan category returns only floor plans."""
    project, _, floor_plans = test_project

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_mock_download)

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets?category=floor_plan",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) == 1
    assert "floor_plans/" in names[0]


@pytest.mark.asyncio
async def test_download_by_ids(client: AsyncClient, auth_headers, test_project):
    """IDs param selects specific files regardless of category."""
    project, images, floor_plans = test_project
    # Select first image and floor plan
    ids_param = f"{images[0].id},{floor_plans[0].id}"

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_mock_download)

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets?ids={ids_param}",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) == 2


@pytest.mark.asyncio
async def test_download_nonexistent_project(client: AsyncClient, auth_headers):
    """404 for a project that doesn't exist."""
    fake_id = uuid4()
    resp = await client.get(
        f"/api/v1/downloads/projects/{fake_id}/assets",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_empty_project(client: AsyncClient, auth_headers, test_db, test_user):
    """404 when project has no downloadable assets."""
    from app.models.database import Project
    from app.models.enums import TemplateType, WorkflowStatus

    now = datetime.now(timezone.utc)
    project = Project(
        name="Empty Project",
        developer="Dev",
        location="Location",
        emirate="Dubai",
        template_type=TemplateType.OPR,
        workflow_status=WorkflowStatus.DRAFT,
        created_by=test_user.id,
        is_active=True,
        property_types=[],
        unit_sizes=[],
        amenities=[],
        features=[],
        custom_fields={},
        generated_content={},
        created_at=now,
        updated_at=now,
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 404
    assert "No downloadable assets" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_download_size_guard(client: AsyncClient, auth_headers, test_db, test_user):
    """413 when total file size exceeds 200MB limit."""
    from app.models.database import Project, ProjectImage
    from app.models.enums import ImageCategory, TemplateType, WorkflowStatus

    now = datetime.now(timezone.utc)
    project = Project(
        name="Big Project",
        developer="Dev",
        location="Location",
        emirate="Dubai",
        template_type=TemplateType.OPR,
        workflow_status=WorkflowStatus.DRAFT,
        created_by=test_user.id,
        is_active=True,
        property_types=[],
        unit_sizes=[],
        amenities=[],
        features=[],
        custom_fields={},
        generated_content={},
        created_at=now,
        updated_at=now,
    )
    test_db.add(project)
    await test_db.flush()

    # Add image with size > 200MB
    big_img = ProjectImage(
        project_id=project.id,
        category=ImageCategory.EXTERIOR,
        image_url=f"materials/{project.id}/images/exterior/big.webp",
        file_size=201 * 1024 * 1024,
        format="webp",
        display_order=0,
        created_at=now,
    )
    test_db.add(big_img)
    await test_db.commit()

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 413
    assert "200 MB" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_download_skipped_files(client: AsyncClient, auth_headers, test_project):
    """Skipped files produce _skipped.txt in the ZIP."""
    project, images, floor_plans = test_project

    async def _download_some_fail(blob_path):
        # Fail on interior images
        if "interior" in blob_path:
            raise Exception("GCS unavailable")
        return f"data-{blob_path}".encode()

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_download_some_fail)
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert "_skipped.txt" in names
    # 2 images + 1 floor plan successful + 1 skipped manifest = 4 entries (interior skipped)
    assert len(names) == 4


@pytest.mark.asyncio
async def test_download_content_disposition(client: AsyncClient, auth_headers, test_project):
    """Content-Disposition header uses sanitized project name."""
    project, _, _ = test_project

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_mock_download)
        mock_storage.list_files = AsyncMock(return_value=[])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    cd = resp.headers["content-disposition"]
    assert 'filename="Test_Download_Project_assets.zip"' in cd


@pytest.mark.asyncio
async def test_download_includes_source_pdf(client: AsyncClient, auth_headers, test_project):
    """All-assets download includes source PDF from GCS."""
    project, _, _ = test_project
    source_path = f"materials/{project.id}/source/brochure.pdf"

    async def _download(blob_path):
        return f"content-{blob_path}".encode()

    with patch(
        "app.api.routes.downloads.storage_service"
    ) as mock_storage:
        mock_storage.download_file = AsyncMock(side_effect=_download)
        mock_storage.list_files = AsyncMock(return_value=[source_path])

        resp = await client.get(
            f"/api/v1/downloads/projects/{project.id}/assets",
            headers=auth_headers,
        )

    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    # 3 images + 1 floor plan + 1 source PDF = 5
    assert len(names) == 5
    assert any("source/brochure.pdf" in n for n in names)
