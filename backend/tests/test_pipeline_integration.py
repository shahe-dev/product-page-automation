"""
Integration tests for the full extraction pipeline (Phase 4).

Tests the complete flow from image input to organized output,
verifying all Phase 4 improvements:
- Semantic image filenames
- Separate original/optimized folder structure
- extracted_text.json inclusion
- Floor plan sidecar JSON files
- Drive folder population
"""

import io
import json
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.services.image_optimizer import ImageOptimizer, OptimizationResult
from app.services.output_organizer import OutputOrganizer


def create_test_image(
    width: int = 1000,
    height: int = 800,
    color: tuple = (255, 0, 0),
) -> bytes:
    """Create a test image with specified dimensions."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def optimizer():
    """Create ImageOptimizer."""
    return ImageOptimizer()


@pytest.fixture
def organizer():
    """Create OutputOrganizer."""
    return OutputOrganizer()


# =============================================================================
# Integration Test: Full Pipeline Output Structure
# =============================================================================


class TestPipelineOutputStructure:
    """Integration tests for complete pipeline output."""

    @pytest.mark.asyncio
    async def test_full_pipeline_produces_correct_structure(
        self, optimizer, organizer
    ):
        """Verify complete pipeline produces expected output structure."""
        # Create test images with alt_text for semantic naming
        images = [
            (create_test_image(2000, 1500), "interior", "Modern living room with views"),
            (create_test_image(1800, 1200), "exterior", "Building facade at sunset"),
            (create_test_image(1500, 1000), "amenity", "Infinity pool and deck"),
        ]

        # Stage 1: Optimize (includes semantic naming)
        opt_result = await optimizer.optimize_batch(images)

        # Verify semantic filenames
        assert opt_result.images[0].file_name == "001-interior-modern-living-room-with-views"
        assert opt_result.images[1].file_name == "001-exterior-building-facade-at-sunset"
        assert opt_result.images[2].file_name == "001-amenity-infinity-pool-and-deck"

        # Stage 2: Package with extracted text
        page_text_map = {
            1: "Page 1: Introduction to the project",
            2: "Page 2: Floor plans and specifications",
        }

        zip_bytes, manifest = organizer.create_package(
            opt_result,
            project_name="Integration Test Project",
            page_text_map=page_text_map,
        )

        # Verify output structure
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Required files
            assert "manifest.json" in names
            assert "extracted_text.json" in names

            # Original tier folders
            assert any(n.startswith("original/interiors/") for n in names)
            assert any(n.startswith("original/exteriors/") for n in names)
            assert any(n.startswith("original/amenities/") for n in names)

            # Optimized tier folders
            assert any(n.startswith("optimized/interiors/") for n in names)
            assert any(n.startswith("optimized/exteriors/") for n in names)
            assert any(n.startswith("optimized/amenities/") for n in names)

            # No old structure
            assert not any(n.startswith("llm/") for n in names)
            assert not any(n.startswith("interiors/") and not n.startswith("original/") for n in names)

            # Verify extracted_text.json content
            text_data = json.loads(zf.read("extracted_text.json"))
            assert len(text_data["pages"]) == 2
            assert text_data["pages"][0]["page"] == 1
            assert "Introduction" in text_data["pages"][0]["text"]

    @pytest.mark.asyncio
    async def test_semantic_filenames_in_zip(self, optimizer, organizer):
        """Verify semantic filenames appear correctly in ZIP archive."""
        images = [
            (create_test_image(), "interior", "Spacious bedroom with en-suite"),
        ]

        opt_result = await optimizer.optimize_batch(images)
        zip_bytes, _ = organizer.create_package(opt_result, project_name="test")

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Verify semantic filename in original tier
            assert any("001-interior-spacious-bedroom-with-en-suite.webp" in n for n in names)
            assert any("001-interior-spacious-bedroom-with-en-suite.jpg" in n for n in names)

            # Verify same filename in optimized tier
            optimized_names = [n for n in names if n.startswith("optimized/")]
            assert any("001-interior-spacious-bedroom-with-en-suite.webp" in n for n in optimized_names)

    @pytest.mark.asyncio
    async def test_manifest_reflects_new_structure(self, optimizer, organizer):
        """Verify manifest entries use new folder structure."""
        images = [
            (create_test_image(), "interior", "Test room"),
        ]

        opt_result = await optimizer.optimize_batch(images)
        zip_bytes, manifest = organizer.create_package(opt_result)

        # Check manifest entries have correct directories
        original_entries = [e for e in manifest.entries if e.tier == "original"]
        optimized_entries = [e for e in manifest.entries if e.tier == "llm_optimized"]

        assert all(e.directory.startswith("original/") for e in original_entries)
        assert all(e.directory.startswith("optimized/") for e in optimized_entries)

        # Verify tier counts
        assert manifest.tier1_count == 2  # WebP + JPG
        assert manifest.tier2_count == 2  # WebP + JPG


# =============================================================================
# Integration Test: Floor Plan Consolidation
# =============================================================================


class TestFloorPlanConsolidation:
    """Integration tests for floor plan data consolidation."""

    @pytest.mark.asyncio
    async def test_floor_plan_sidecar_files_created(self, organizer):
        """Verify floor plan images have sidecar JSON files."""
        # Create mock floor plan data with image references
        floor_plan_data = [
            {
                "image_filename": "001-floor-plan-2br-unit.webp",
                "unit_type": "2BR",
                "bedrooms": 2,
                "bathrooms": 2,
                "total_sqft": 1250,
                "balcony_sqft": 150,
            },
            {
                "image_filename": "002-floor-plan-3br-penthouse.webp",
                "unit_type": "3BR Penthouse",
                "bedrooms": 3,
                "bathrooms": 3.5,
                "total_sqft": 2800,
                "balcony_sqft": 400,
            },
        ]

        mock_result = OptimizationResult(images=[])
        zip_bytes, _ = organizer.create_package(
            mock_result,
            project_name="Floor Plan Test",
            floor_plan_data=floor_plan_data,
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Consolidated file
            assert "floor_plans/floor_plan_data.json" in names

            # Sidecar files
            assert "floor_plans/001-floor-plan-2br-unit.json" in names
            assert "floor_plans/002-floor-plan-3br-penthouse.json" in names

            # Verify sidecar content matches original data
            sidecar_1 = json.loads(zf.read("floor_plans/001-floor-plan-2br-unit.json"))
            assert sidecar_1["unit_type"] == "2BR"
            assert sidecar_1["bedrooms"] == 2
            assert sidecar_1["total_sqft"] == 1250

            sidecar_2 = json.loads(zf.read("floor_plans/002-floor-plan-3br-penthouse.json"))
            assert sidecar_2["unit_type"] == "3BR Penthouse"
            assert sidecar_2["bathrooms"] == 3.5

    @pytest.mark.asyncio
    async def test_floor_plan_data_without_images_no_sidecar(self, organizer):
        """Verify entries without image_filename don't get sidecar files."""
        floor_plan_data = [
            {
                "unit_type": "Studio",
                "bedrooms": 0,
                "total_sqft": 500,
            },  # No image_filename
            {
                "image_filename": "001-floor-plan-1br.webp",
                "unit_type": "1BR",
                "bedrooms": 1,
                "total_sqft": 750,
            },
        ]

        mock_result = OptimizationResult(images=[])
        zip_bytes, _ = organizer.create_package(
            mock_result,
            floor_plan_data=floor_plan_data,
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Consolidated file should have both entries
            consolidated = json.loads(zf.read("floor_plans/floor_plan_data.json"))
            assert len(consolidated) == 2

            # Only one sidecar file (the one with image_filename)
            sidecar_files = [n for n in names if n.startswith("floor_plans/") and n != "floor_plans/floor_plan_data.json"]
            assert len(sidecar_files) == 1
            assert "floor_plans/001-floor-plan-1br.json" in sidecar_files


# =============================================================================
# Integration Test: Complete Image Pipeline
# =============================================================================


class TestCompleteImagePipeline:
    """Integration tests for complete image processing pipeline."""

    @pytest.mark.asyncio
    async def test_all_category_types_processed(self, optimizer, organizer):
        """Verify all image categories are processed correctly."""
        images = [
            (create_test_image(), "interior", "Living room"),
            (create_test_image(), "exterior", "Facade"),
            (create_test_image(), "amenity", "Pool"),
            (create_test_image(), "logo", "Developer logo"),
            (create_test_image(), "floor_plan", "2BR layout"),
            (create_test_image(), "location_map", "Area map"),
            (create_test_image(), "master_plan", "Site plan"),
        ]

        opt_result = await optimizer.optimize_batch(images)
        zip_bytes, manifest = organizer.create_package(opt_result)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()

            # Verify all category directories exist
            expected_dirs = [
                "interiors", "exteriors", "amenities", "logos",
                "floor_plans", "location_maps", "master_plans"
            ]

            for dir_name in expected_dirs:
                assert any(f"original/{dir_name}/" in n for n in names), f"Missing original/{dir_name}/"
                assert any(f"optimized/{dir_name}/" in n for n in names), f"Missing optimized/{dir_name}/"

        # Verify manifest category counts
        assert manifest.total_images == 7
        assert manifest.categories["interior"] == 1
        assert manifest.categories["exterior"] == 1
        assert manifest.categories["amenity"] == 1
        assert manifest.categories["logo"] == 1
        assert manifest.categories["floor_plan"] == 1
        assert manifest.categories["location_map"] == 1
        assert manifest.categories["master_plan"] == 1

    @pytest.mark.asyncio
    async def test_category_counters_per_category(self, optimizer, organizer):
        """Verify sequential counters are maintained per category."""
        images = [
            (create_test_image(), "interior", "Room 1"),
            (create_test_image(), "interior", "Room 2"),
            (create_test_image(), "exterior", "Building 1"),
            (create_test_image(), "interior", "Room 3"),
            (create_test_image(), "exterior", "Building 2"),
        ]

        opt_result = await optimizer.optimize_batch(images)

        # Verify counters are per-category
        assert opt_result.images[0].file_name == "001-interior-room-1"
        assert opt_result.images[1].file_name == "002-interior-room-2"
        assert opt_result.images[2].file_name == "001-exterior-building-1"
        assert opt_result.images[3].file_name == "003-interior-room-3"
        assert opt_result.images[4].file_name == "002-exterior-building-2"

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, optimizer, organizer):
        """Test pipeline handles larger batches correctly."""
        # Create 20 images
        images = [
            (create_test_image(1000 + i * 10, 800 + i * 5), "interior", f"Room {i+1}")
            for i in range(20)
        ]

        opt_result = await optimizer.optimize_batch(images)
        zip_bytes, manifest = organizer.create_package(opt_result, project_name="Batch Test")

        assert manifest.total_images == 20
        # Each image produces 4 files (original webp/jpg + optimized webp/jpg)
        assert len(manifest.entries) == 80

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            # 80 image files + 1 manifest
            image_files = [n for n in names if n != "manifest.json"]
            assert len(image_files) == 80


# =============================================================================
# Integration Test: Error Handling
# =============================================================================


class TestPipelineErrorHandling:
    """Integration tests for error handling in pipeline."""

    @pytest.mark.asyncio
    async def test_empty_input_produces_valid_output(self, optimizer, organizer):
        """Verify empty input produces valid but empty output."""
        opt_result = await optimizer.optimize_batch([])
        zip_bytes, manifest = organizer.create_package(opt_result)

        assert manifest.total_images == 0
        assert manifest.tier1_count == 0
        assert manifest.tier2_count == 0

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            # Should only have manifest
            assert "manifest.json" in names

    @pytest.mark.asyncio
    async def test_no_extracted_text_when_empty(self, organizer):
        """Verify extracted_text.json is not created when page_text_map is empty."""
        mock_result = OptimizationResult(images=[])
        zip_bytes, _ = organizer.create_package(
            mock_result,
            page_text_map={},
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            assert "extracted_text.json" not in zf.namelist()

    @pytest.mark.asyncio
    async def test_no_floor_plan_files_when_empty(self, organizer):
        """Verify floor plan files are not created when data is empty."""
        mock_result = OptimizationResult(images=[])
        zip_bytes, _ = organizer.create_package(
            mock_result,
            floor_plan_data=[],
        )

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert not any(n.startswith("floor_plans/") for n in names)


# =============================================================================
# Integration Test: Drive Upload
# =============================================================================


class TestDriveUploadIntegration:
    """Integration tests for Drive upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_to_project_all_assets(self):
        """Verify upload_to_project handles all asset types."""
        from app.integrations.drive_client import DriveClient

        with patch.object(DriveClient, "_create_service"):
            client = DriveClient()

            # Mock upload_file_bytes
            with patch.object(
                client, "upload_file_bytes", new_callable=AsyncMock
            ) as mock_upload:
                mock_upload.side_effect = ["pdf-id", "zip-id", "img-1-id", "img-2-id"]

                # Mock folder operations
                with patch.object(
                    client, "get_folder_by_path", new_callable=AsyncMock
                ) as mock_get_folder:
                    mock_get_folder.return_value = None

                    with patch.object(
                        client, "create_folder", new_callable=AsyncMock
                    ) as mock_create_folder:
                        mock_create_folder.side_effect = ["subfolder-1", "subfolder-2"]

                        project_structure = {
                            "project": "project-id",
                            "source": "source-id",
                            "images": "images-id",
                            "output": "output-id",
                        }

                        result = await client.upload_to_project(
                            project_structure=project_structure,
                            source_pdf=b"PDF content",
                            source_filename="brochure.pdf",
                            output_zip=b"ZIP content",
                            output_filename="output.zip",
                            organized_images=[
                                ("interiors/001-interior.webp", b"img1"),
                                ("exteriors/001-exterior.webp", b"img2"),
                            ],
                        )

                        assert result["source_pdf"] == "pdf-id"
                        assert result["output_zip"] == "zip-id"
                        assert result["images_uploaded"] == 2

    @pytest.mark.asyncio
    async def test_upload_empty_returns_empty(self):
        """Verify empty upload returns empty dict."""
        from app.integrations.drive_client import DriveClient

        with patch.object(DriveClient, "_create_service"):
            client = DriveClient()

            project_structure = {
                "project": "project-id",
                "source": "source-id",
                "images": "images-id",
                "output": "output-id",
            }

            result = await client.upload_to_project(project_structure)
            assert result == {}
