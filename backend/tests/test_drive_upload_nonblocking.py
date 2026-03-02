"""
Tests for GCS-first pipeline with background Drive sync.

Covers:
- Extraction pipeline has no Drive upload step
- Sheet export to GCS (.xlsx)
- Drive sync trigger logic (last-job detection, duplicate prevention)
- Background Drive sync (GCS -> Drive copy)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Test 1: Extraction steps have no Drive upload
# ---------------------------------------------------------------------------


class TestExtractionNoDriveUpload:
    def test_extraction_steps_has_no_upload_shared_assets(self):
        """EXTRACTION_STEPS does not include upload_shared_assets."""
        from app.services.job_manager import EXTRACTION_STEPS

        step_ids = [s["id"] for s in EXTRACTION_STEPS]
        assert "upload_shared_assets" not in step_ids
        assert step_ids[-1] == "materialize"

    def test_extraction_steps_count_is_12(self):
        """Extraction pipeline should have 12 steps after removing Drive upload."""
        from app.services.job_manager import EXTRACTION_STEPS

        assert len(EXTRACTION_STEPS) == 12

    def test_generation_steps_has_export_sheet(self):
        """GENERATION_STEPS includes export_sheet instead of upload_cloud_generation."""
        from app.services.job_manager import GENERATION_STEPS

        step_ids = [s["id"] for s in GENERATION_STEPS]
        assert "export_sheet" in step_ids
        assert "upload_cloud_generation" not in step_ids


# ---------------------------------------------------------------------------
# Test 2: Sheet export to GCS
# ---------------------------------------------------------------------------


class TestSheetExportToGCS:
    @pytest.mark.asyncio
    async def test_export_sheet_saves_xlsx_to_gcs(self):
        """_step_export_sheet exports Google Sheet as .xlsx and uploads to GCS."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        jm._material_package_service = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.template_type = MagicMock(value="opr")
        mock_job.material_package_id = uuid4()
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)

        mock_sheet_result = MagicMock()
        mock_sheet_result.sheet_id = "sheet_123"
        jm._pipeline_ctx[job_id] = {
            "sheet_result": mock_sheet_result,
            "material_package_gcs_path": "materials/proj-abc",
        }

        xlsx_bytes = b"fake_xlsx_content"

        mock_dc = AsyncMock()
        mock_dc.export_google_sheet_to_excel = AsyncMock(return_value=xlsx_bytes)

        # Point to the mock storage on _material_package_service
        mock_storage = AsyncMock()
        jm._material_package_service.storage = mock_storage

        with patch(
            "app.integrations.drive_client.drive_client", mock_dc
        ):
            result = await jm._step_export_sheet(job_id)

        # Verify export was called
        assert result["sheet_id"] == "sheet_123"
        assert "sheets/opr.xlsx" in result["gcs_xlsx_path"]
        assert result["xlsx_size_bytes"] == len(xlsx_bytes)

        # Verify GCS upload
        mock_storage.upload_file.assert_awaited_once()
        call_kwargs = mock_storage.upload_file.call_args.kwargs
        assert call_kwargs["destination_blob_path"] == "materials/proj-abc/sheets/opr.xlsx"

    @pytest.mark.asyncio
    async def test_export_sheet_no_sheet_skips(self):
        """If no sheet_result, step returns skipped."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)
        jm._pipeline_ctx[job_id] = {}

        result = await jm._step_export_sheet(job_id)
        assert result.get("status") == "skipped"

    @pytest.mark.asyncio
    async def test_export_sheet_handles_export_failure(self):
        """If Drive export fails, step returns export_failed without raising."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm._pipeline_ctx = {}
        jm.job_repo = AsyncMock()
        jm._material_package_service = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.template_type = MagicMock(value="adop")
        jm.job_repo.get_job = AsyncMock(return_value=mock_job)

        mock_sheet_result = MagicMock()
        mock_sheet_result.sheet_id = "sheet_fail"
        jm._pipeline_ctx[job_id] = {
            "sheet_result": mock_sheet_result,
            "material_package_gcs_path": "materials/proj-xyz",
        }

        with patch(
            "app.integrations.drive_client.drive_client"
        ) as mock_dc:
            mock_dc.export_google_sheet_to_excel = AsyncMock(
                side_effect=RuntimeError("API quota exceeded")
            )
            result = await jm._step_export_sheet(job_id)

        assert result["status"] == "export_failed"
        assert "API quota exceeded" in result["error"]


# ---------------------------------------------------------------------------
# Test 3: Drive sync trigger
# ---------------------------------------------------------------------------


class TestDriveSyncTrigger:
    @pytest.mark.asyncio
    async def test_last_generation_triggers_drive_sync(self):
        """When all generation jobs are complete, Drive sync is triggered."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm.job_repo = AsyncMock()

        pkg_id = uuid4()

        # Mock DB: no incomplete generation jobs
        mock_db = AsyncMock()
        # First execute: incomplete jobs query -> empty
        # Second execute: extraction_summary query -> no flag
        # Third execute: update extraction_summary
        mock_result_incomplete = MagicMock()
        mock_result_incomplete.all.return_value = []

        mock_result_summary = MagicMock()
        mock_result_summary.scalar_one_or_none.return_value = {}

        mock_db.execute = AsyncMock(
            side_effect=[mock_result_incomplete, mock_result_summary, None]
        )
        mock_db.commit = AsyncMock()
        jm.job_repo.db = mock_db

        with patch.object(jm, "_background_drive_sync", new_callable=AsyncMock):
            with patch("asyncio.create_task") as mock_create_task:
                await jm._check_and_trigger_drive_sync(pkg_id)
                # Verify create_task was called with the sync coroutine
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_incomplete_generations_no_sync(self):
        """When some generation jobs are still running, no sync triggered."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm.job_repo = AsyncMock()

        pkg_id = uuid4()

        # Mock DB: 1 incomplete generation job
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(uuid4(), "processing")]
        mock_db.execute = AsyncMock(return_value=mock_result)
        jm.job_repo.db = mock_db

        with patch("asyncio.create_task") as mock_create_task:
            await jm._check_and_trigger_drive_sync(pkg_id)
            mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_sync_prevented(self):
        """Atomic flag prevents duplicate sync triggers."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        jm.job_repo = AsyncMock()

        pkg_id = uuid4()

        # Mock DB: no incomplete jobs, but flag already set
        mock_db = AsyncMock()
        mock_result_incomplete = MagicMock()
        mock_result_incomplete.all.return_value = []

        mock_result_summary = MagicMock()
        mock_result_summary.scalar_one_or_none.return_value = {
            "drive_sync_triggered": True,
        }

        mock_db.execute = AsyncMock(
            side_effect=[mock_result_incomplete, mock_result_summary]
        )
        jm.job_repo.db = mock_db

        with patch("asyncio.create_task") as mock_create_task:
            await jm._check_and_trigger_drive_sync(pkg_id)
            mock_create_task.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: Background Drive sync
# ---------------------------------------------------------------------------


class TestBackgroundDriveSync:
    @pytest.mark.asyncio
    async def test_sync_creates_folder_uploads_files_moves_sheets(self):
        """Full sync: creates Drive folder, uploads from GCS, moves sheets."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        pkg_id = uuid4()

        # Mock package
        mock_pkg = MagicMock()
        mock_pkg.gcs_base_path = "materials/test-proj"
        mock_pkg.structured_data = {"project_name": "Test Project"}
        mock_pkg.extraction_summary = {"drive_sync_triggered": True}

        # Mock generation run
        mock_gen_run = MagicMock()
        mock_gen_run.generated_content = {"sheet_id": "sheet_xyz"}
        mock_gen_run.drive_folder_url = None

        # Mock DB session
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=mock_pkg)

        mock_gen_result = MagicMock()
        mock_gen_result.scalars.return_value.all.return_value = [mock_gen_run]
        mock_db.execute = AsyncMock(return_value=mock_gen_result)
        mock_db.commit = AsyncMock()

        # Mock storage
        mock_storage = MagicMock()
        mock_storage.list_files = AsyncMock(return_value=[
            "materials/test-proj/images/exterior_001.webp",
            "materials/test-proj/source/brochure.pdf",
            "materials/test-proj/structured_data.json",
            "materials/test-proj/sheets/opr.xlsx",
        ])
        mock_storage.download_file = AsyncMock(return_value=b"fake data")

        # Mock drive client
        mock_dc = AsyncMock()
        mock_dc.create_project_structure = AsyncMock(return_value={
            "project": "folder_abc",
            "images": "folder_images",
            "source": "folder_source",
            "raw_data": "folder_raw",
        })
        mock_dc.upload_file_bytes = AsyncMock()
        mock_dc.move_file = AsyncMock()
        mock_dc.get_folder_by_path = AsyncMock(return_value=None)
        mock_dc.create_folder = AsyncMock(return_value="subfolder_id")

        with patch("app.config.database.async_session_factory") as mock_factory:
            # Make async context manager return mock_db
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_factory.return_value = mock_ctx

            with patch("app.integrations.drive_client.drive_client", mock_dc):
                with patch("app.services.storage_service.StorageService", return_value=mock_storage):
                    with patch("sqlalchemy.orm.attributes.flag_modified"):
                        await jm._background_drive_sync(pkg_id)

        # Verify Drive folder was created
        mock_dc.create_project_structure.assert_awaited_once_with(
            project_name="Test Project"
        )

        # Verify files were uploaded to Drive
        assert mock_dc.upload_file_bytes.await_count >= 3  # image + pdf + json

        # Verify sheet was moved
        mock_dc.move_file.assert_awaited_once_with(
            file_id="sheet_xyz", destination_folder_id="folder_abc"
        )

        # Verify DB was committed
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_sync_failure_logged_not_raised(self):
        """Drive sync failure is logged but does not propagate (fire-and-forget)."""
        from app.services.job_manager import JobManager

        jm = JobManager.__new__(JobManager)
        pkg_id = uuid4()

        # Mock package for error recovery
        mock_pkg = MagicMock()
        mock_pkg.extraction_summary = {}

        mock_db_recovery = AsyncMock()
        mock_db_recovery.get = AsyncMock(return_value=mock_pkg)
        mock_db_recovery.commit = AsyncMock()

        with patch("app.config.database.async_session_factory") as mock_factory:
            # First call raises, second call (error recovery) succeeds
            call_count = 0

            class FakeCtx:
                async def __aenter__(self_inner):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise RuntimeError("Drive API down")
                    return mock_db_recovery

                async def __aexit__(self_inner, *args):
                    return False

            mock_factory.return_value = FakeCtx()

            with patch("sqlalchemy.orm.attributes.flag_modified"):
                # Should not raise
                await jm._background_drive_sync(pkg_id)

            # Error was recorded on package
            assert mock_pkg.extraction_summary.get("drive_sync_status") == "failed"


# ---------------------------------------------------------------------------
# Test 5: Source PDF in GCS
# ---------------------------------------------------------------------------


class TestSourcePDFInGCS:
    @pytest.mark.asyncio
    async def test_persist_to_gcs_uploads_source_pdf(self):
        """persist_to_gcs uploads source PDF when present in pipeline_ctx."""
        from app.services.material_package_service import MaterialPackageService

        mock_storage = AsyncMock()
        mock_repo = AsyncMock()
        service = MaterialPackageService(mock_storage, mock_repo)

        ctx = {
            "structured_data": {"project_name": "Test"},
            "extraction": {"page_text_map": {}},
            "floor_plans": {},
            "manifest": {},
            "pdf_bytes": b"%PDF-1.4 fake",
            "pdf_path": "file://C:/uploads/my_brochure.pdf",
        }

        project_id = uuid4()
        await service.persist_to_gcs(project_id, ctx)

        # Find source PDF upload
        found = False
        for call in mock_storage.upload_file.call_args_list:
            _, kwargs = call
            dest = kwargs.get("destination_blob_path", "")
            if "/source/" in dest:
                found = True
                assert dest.endswith("source/my_brochure.pdf")
                assert kwargs["content_type"] == "application/pdf"
                break

        assert found, "source PDF should have been uploaded to GCS"
