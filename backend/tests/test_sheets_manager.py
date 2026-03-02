"""
Comprehensive test suite for Google Sheets Manager service.

Tests cover:
- SheetsManager initialization and credential validation
- Template sheet copying and creation
- Content population with batch updates
- Read-back validation and data integrity
- Permission management (sharing)
- Rate limiting and retry logic
- Field mapping for all 6 template types
- Error handling for API errors and edge cases

Target coverage: 85%+
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from dataclasses import asdict

from gspread.exceptions import APIError, SpreadsheetNotFound

from app.services.sheets_manager import (
    SheetsManager,
    SheetResult,
    PopulateResult,
    ValidationResult,
    CredentialsError,
    TemplateNotFoundError,
    SheetOperationError,
    RateLimitError,
    COMMON_FIELD_MAPPING,
)
from app.models.enums import TemplateType


# Fixtures
@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.services.sheets_manager.get_settings') as mock:
        settings = Mock()
        settings.GOOGLE_APPLICATION_CREDENTIALS = "/path/to/credentials.json"
        settings.GCP_PROJECT_ID = "test-project"
        settings.GOOGLE_DRIVE_ROOT_FOLDER_ID = "test-folder-id"
        settings.TEMPLATE_SHEET_ID_AGGREGATORS = "template-id-aggregators"
        settings.TEMPLATE_SHEET_ID_OPR = "template-id-opr"
        settings.TEMPLATE_SHEET_ID_MPP = "template-id-mpp"
        settings.TEMPLATE_SHEET_ID_ADOP = "template-id-adop"
        settings.TEMPLATE_SHEET_ID_ADRE = "template-id-adre"
        settings.TEMPLATE_SHEET_ID_COMMERCIAL = "template-id-commercial"

        def get_template_sheet_id(template_name: str) -> str:
            template_map = {
                "aggregators": settings.TEMPLATE_SHEET_ID_AGGREGATORS,
                "opr": settings.TEMPLATE_SHEET_ID_OPR,
                "mpp": settings.TEMPLATE_SHEET_ID_MPP,
                "adop": settings.TEMPLATE_SHEET_ID_ADOP,
                "adre": settings.TEMPLATE_SHEET_ID_ADRE,
                "commercial": settings.TEMPLATE_SHEET_ID_COMMERCIAL,
            }
            if template_name.lower() not in template_map:
                raise ValueError(f"Unknown template: {template_name}")
            return template_map[template_name.lower()]

        settings.get_template_sheet_id = get_template_sheet_id
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_gspread_client():
    """Mock gspread client."""
    client = Mock()
    client.open_by_key = Mock()
    client.copy = Mock()
    return client


@pytest.fixture
def sheets_manager(mock_settings, mock_gspread_client):
    """Sheets manager instance with mocked dependencies."""
    with patch('app.services.sheets_manager.gspread.authorize') as mock_auth:
        with patch('app.services.sheets_manager.Credentials.from_service_account_file'):
            mock_auth.return_value = mock_gspread_client
            manager = SheetsManager()
            manager.client = mock_gspread_client
            return manager


# Test Initialization
class TestInitialization:
    """Test sheets manager initialization."""

    def test_init_success(self, mock_settings):
        """Test successful initialization."""
        with patch('app.services.sheets_manager.gspread.authorize') as mock_auth:
            with patch('app.services.sheets_manager.Credentials.from_service_account_file') as mock_creds:
                mock_auth.return_value = Mock()
                mock_creds.return_value = Mock()

                manager = SheetsManager()

                assert manager.client is not None
                assert manager.settings == mock_settings
                mock_creds.assert_called_once()

    def test_init_no_credentials(self, mock_settings):
        """Test initialization fails without credentials."""
        mock_settings.GOOGLE_APPLICATION_CREDENTIALS = None

        with pytest.raises(CredentialsError, match="not configured"):
            SheetsManager()

    def test_init_credentials_file_not_found(self, mock_settings):
        """Test initialization fails when credentials file missing."""
        with patch('app.services.sheets_manager.Credentials.from_service_account_file') as mock_creds:
            mock_creds.side_effect = FileNotFoundError("File not found")

            with pytest.raises(CredentialsError, match="not found"):
                SheetsManager()


# Test Field Mapping
class TestFieldMapping:
    """Test field to cell mapping."""

    def test_get_field_mapping_aggregators(self, sheets_manager):
        """Test field mapping for aggregators template."""
        mapping = sheets_manager._get_field_mapping("aggregators")

        assert mapping == COMMON_FIELD_MAPPING
        assert "meta_title" in mapping
        assert mapping["meta_title"] == "B2"
        assert "project_name" in mapping
        assert mapping["project_name"] == "B12"

    def test_get_field_mapping_all_templates(self, sheets_manager):
        """Test field mapping works for all template types."""
        for template in TemplateType:
            mapping = sheets_manager._get_field_mapping(template.value)
            assert mapping == COMMON_FIELD_MAPPING

    def test_get_field_mapping_invalid_template(self, sheets_manager):
        """Test field mapping rejects invalid template."""
        with pytest.raises(ValueError, match="Invalid template type"):
            sheets_manager._get_field_mapping("invalid_template")


# Test Sheet Creation
class TestSheetCreation:
    """Test sheet creation from templates."""

    @pytest.mark.asyncio
    async def test_create_project_sheet_success(self, sheets_manager, mock_gspread_client):
        """Test successful sheet creation."""
        # Mock template sheet
        mock_template = Mock()
        mock_gspread_client.open_by_key.return_value = mock_template

        # Mock copy operation
        mock_gspread_client.copy.return_value = {
            'id': 'new-sheet-id',
            'name': 'Test Project'
        }

        result = await sheets_manager.create_project_sheet(
            project_name="Test Project",
            template_type="aggregators"
        )

        assert isinstance(result, SheetResult)
        assert result.sheet_id == "new-sheet-id"
        assert result.title == "Test Project"
        assert result.template_type == "aggregators"
        assert "https://docs.google.com/spreadsheets/d/new-sheet-id/edit" in result.sheet_url
        assert result.created_at is not None

        mock_gspread_client.copy.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_sheet_template_not_found(self, sheets_manager, mock_gspread_client):
        """Test sheet creation fails when template not found."""
        mock_gspread_client.open_by_key.side_effect = SpreadsheetNotFound("Not found")

        with pytest.raises(TemplateNotFoundError, match="Template sheet not found"):
            await sheets_manager.create_project_sheet(
                project_name="Test Project",
                template_type="aggregators"
            )

    @pytest.mark.asyncio
    async def test_create_project_sheet_invalid_template_type(self, sheets_manager):
        """Test sheet creation fails with invalid template type."""
        with pytest.raises(SheetOperationError, match="Unknown template"):
            await sheets_manager.create_project_sheet(
                project_name="Test Project",
                template_type="invalid"
            )


# Test Sheet Population
class TestSheetPopulation:
    """Test sheet content population."""

    @pytest.mark.asyncio
    async def test_populate_sheet_success(self, sheets_manager, mock_gspread_client):
        """Test successful sheet population."""
        # Mock spreadsheet and worksheet
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "meta_description": "Test Description",
            "project_name": "Test Project",
            "developer": "Test Developer"
        }

        result = await sheets_manager.populate_sheet(
            sheet_id="test-sheet-id",
            content=content,
            template_type="aggregators"
        )

        assert isinstance(result, PopulateResult)
        assert result.sheet_id == "test-sheet-id"
        assert result.fields_written == 4
        assert result.fields_failed == 0
        assert len(result.failures) == 0

        mock_worksheet.batch_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_populate_sheet_skips_empty_values(self, sheets_manager, mock_gspread_client):
        """Test population skips None and empty values."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "meta_description": None,  # Should be skipped
            "project_name": "",  # Should be skipped
            "developer": "Test Developer"
        }

        result = await sheets_manager.populate_sheet(
            sheet_id="test-sheet-id",
            content=content,
            template_type="aggregators"
        )

        assert result.fields_written == 2  # Only non-empty values

    @pytest.mark.asyncio
    async def test_populate_sheet_not_found(self, sheets_manager, mock_gspread_client):
        """Test population fails when sheet not found."""
        mock_gspread_client.open_by_key.side_effect = SpreadsheetNotFound("Not found")

        with pytest.raises(SheetOperationError, match="Sheet not found"):
            await sheets_manager.populate_sheet(
                sheet_id="nonexistent-sheet",
                content={"meta_title": "Test"},
                template_type="aggregators"
            )


# Test Validation
class TestValidation:
    """Test read-back validation."""

    @pytest.mark.asyncio
    async def test_read_back_validate_all_match(self, sheets_manager, mock_gspread_client):
        """Test validation when all values match."""
        # Mock worksheet
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            if cell_ref == "B2":
                cell.value = "Test Title"
            elif cell_ref == "B12":
                cell.value = "Test Project"
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "project_name": "Test Project"
        }

        result = await sheets_manager.read_back_validate(
            sheet_id="test-sheet-id",
            content=content,
            template_type="aggregators"
        )

        assert isinstance(result, ValidationResult)
        assert result.matches == 2
        assert result.mismatches == 0
        assert len(result.details) == 2

    @pytest.mark.asyncio
    async def test_read_back_validate_mismatches(self, sheets_manager, mock_gspread_client):
        """Test validation when values mismatch."""
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            if cell_ref == "B2":
                cell.value = "Wrong Title"  # Mismatch
            elif cell_ref == "B12":
                cell.value = "Test Project"  # Match
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "project_name": "Test Project"
        }

        result = await sheets_manager.read_back_validate(
            sheet_id="test-sheet-id",
            content=content,
            template_type="aggregators"
        )

        assert result.matches == 1
        assert result.mismatches == 1
        assert not result.details[0]['match']  # First is mismatch
        assert result.details[1]['match']  # Second is match


# Test Sharing
class TestSharing:
    """Test sheet sharing functionality."""

    @pytest.mark.asyncio
    async def test_share_sheet_success(self, sheets_manager, mock_gspread_client):
        """Test successful sheet sharing."""
        mock_spreadsheet = Mock()
        mock_spreadsheet.share = Mock()
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        result = await sheets_manager.share_sheet(
            sheet_id="test-sheet-id",
            email="user@example.com",
            role="writer"
        )

        assert result is True
        mock_spreadsheet.share.assert_called_once_with(
            "user@example.com",
            perm_type='user',
            role='writer'
        )

    @pytest.mark.asyncio
    async def test_share_sheet_invalid_role(self, sheets_manager, mock_gspread_client):
        """Test sharing fails with invalid role."""
        mock_spreadsheet = Mock()
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        with pytest.raises(SheetOperationError, match="Invalid role"):
            await sheets_manager.share_sheet(
                sheet_id="test-sheet-id",
                email="user@example.com",
                role="invalid_role"
            )

    @pytest.mark.asyncio
    async def test_share_sheet_not_found(self, sheets_manager, mock_gspread_client):
        """Test sharing fails when sheet not found."""
        mock_gspread_client.open_by_key.side_effect = SpreadsheetNotFound("Not found")

        with pytest.raises(SheetOperationError, match="Sheet not found"):
            await sheets_manager.share_sheet(
                sheet_id="nonexistent-sheet",
                email="user@example.com",
                role="writer"
            )


# Test Rate Limiting
class TestRateLimiting:
    """Test rate limiting and retry logic."""

    def test_exponential_backoff_calculation(self, sheets_manager):
        """Test exponential backoff delay calculation."""
        # attempt 0: 1.0 * 2^0 = 1.0
        assert sheets_manager._exponential_backoff(0, 1.0) == 1.0

        # attempt 1: 1.0 * 2^1 = 2.0
        assert sheets_manager._exponential_backoff(1, 1.0) == 2.0

        # attempt 2: 1.0 * 2^2 = 4.0
        assert sheets_manager._exponential_backoff(2, 1.0) == 4.0

        # attempt 10: should be capped at MAX_RETRY_DELAY
        assert sheets_manager._exponential_backoff(10, 1.0) == sheets_manager.MAX_RETRY_DELAY

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, sheets_manager, mock_gspread_client):
        """Test retry logic on rate limit error."""
        # Create a mock response for 429 error
        mock_response = Mock()
        mock_response.status_code = 429

        # Mock API error
        api_error = APIError(mock_response)
        api_error.response = mock_response

        # First call fails with 429, second succeeds
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock(side_effect=[api_error, None])
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        with patch('time.sleep'):  # Don't actually sleep in tests
            result = await sheets_manager.populate_sheet(
                sheet_id="test-sheet-id",
                content={"meta_title": "Test"},
                template_type="aggregators"
            )

        assert result.fields_written > 0
        assert mock_worksheet.batch_update.call_count == 2


# Test Error Handling
class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_template_type_in_operations(self, sheets_manager):
        """Test operations reject invalid template types."""
        with pytest.raises(SheetOperationError, match="Invalid template type"):
            await sheets_manager.populate_sheet(
                sheet_id="test-sheet-id",
                content={"meta_title": "Test"},
                template_type="invalid_template"
            )

    @pytest.mark.asyncio
    async def test_sheet_operation_error_on_generic_failure(self, sheets_manager, mock_gspread_client):
        """Test generic errors are wrapped in SheetOperationError."""
        mock_gspread_client.open_by_key.side_effect = Exception("Unexpected error")

        with pytest.raises(SheetOperationError, match="Failed to populate sheet"):
            await sheets_manager.populate_sheet(
                sheet_id="test-sheet-id",
                content={"meta_title": "Test"},
                template_type="aggregators"
            )


# Integration Test (requires actual credentials)
@pytest.mark.skip(reason="Integration test - requires real credentials")
class TestIntegration:
    """Integration tests with real Google Sheets API."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: create, populate, validate, share."""
        manager = SheetsManager()

        # Create sheet
        sheet_result = await manager.create_project_sheet(
            project_name="Integration Test Project",
            template_type="aggregators"
        )

        assert sheet_result.sheet_id is not None

        # Populate sheet
        content = {
            "meta_title": "Test Title",
            "meta_description": "Test Description",
            "project_name": "Integration Test Project",
        }

        populate_result = await manager.populate_sheet(
            sheet_id=sheet_result.sheet_id,
            content=content,
            template_type="aggregators"
        )

        assert populate_result.fields_written > 0

        # Validate
        validation_result = await manager.read_back_validate(
            sheet_id=sheet_result.sheet_id,
            content=content,
            template_type="aggregators"
        )

        assert validation_result.matches == populate_result.fields_written

        # Share
        share_result = await manager.share_sheet(
            sheet_id=sheet_result.sheet_id,
            email="test@your-domain.com",
            role="reader"
        )

        assert share_result is True


# ============================================================================
# Additional Tests for 85%+ Coverage
# ============================================================================


# Test Field Mapping Details
class TestFieldMappingDetails:
    """Additional field mapping tests."""

    def test_common_field_mapping_has_all_content_fields(self):
        """Test that COMMON_FIELD_MAPPING contains all expected content fields."""
        expected_fields = [
            # SEO fields
            "meta_title",
            "meta_description",
            "h1",
            "url_slug",
            # Content fields
            "short_description",
            "long_description",
            "location_description",
            "amenities_description",
            "payment_plan_description",
            "investment_highlights",
            # Project data fields
            "project_name",
            "developer",
            "location",
            "starting_price",
            "bedrooms",
            "completion_date",
            "property_type",
        ]

        for field in expected_fields:
            assert field in COMMON_FIELD_MAPPING, f"Missing field: {field}"

    def test_field_mapping_cells_valid_format(self):
        """Test that all cell references match valid format like B2."""
        import re

        cell_pattern = re.compile(r'^[A-Z]+\d+$')

        for field, cell in COMMON_FIELD_MAPPING.items():
            assert cell_pattern.match(cell), f"Invalid cell format for {field}: {cell}"

    def test_field_mapping_returns_copy(self, sheets_manager):
        """Test that _get_field_mapping returns a copy, not the original."""
        mapping1 = sheets_manager._get_field_mapping("aggregators")
        mapping2 = sheets_manager._get_field_mapping("aggregators")

        # Modify one mapping
        mapping1['new_field'] = 'Z99'

        # Other should not be affected
        assert 'new_field' not in mapping2

    def test_get_field_mapping_returns_dict(self, sheets_manager):
        """Test that _get_field_mapping returns dict for valid template type."""
        mapping = sheets_manager._get_field_mapping("aggregators")

        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        assert "meta_title" in mapping


# Test Sheet Creation Details
class TestSheetCreationDetails:
    """Additional sheet creation tests."""

    @pytest.mark.asyncio
    async def test_create_project_sheet_sets_correct_folder(self, sheets_manager, mock_gspread_client):
        """Test that sheet is created in correct folder."""
        mock_gspread_client.open_by_key.return_value = Mock()
        mock_gspread_client.copy.return_value = {'id': 'new-id', 'name': 'Test'}

        await sheets_manager.create_project_sheet("Test Project", "aggregators")

        call_kwargs = mock_gspread_client.copy.call_args[1]
        assert call_kwargs['folder_id'] == "test-folder-id"

    @pytest.mark.asyncio
    async def test_create_sheet_generates_correct_url_format(self, sheets_manager, mock_gspread_client):
        """Test that sheet URL is generated in correct format."""
        mock_gspread_client.open_by_key.return_value = Mock()
        mock_gspread_client.copy.return_value = {'id': 'abc123xyz', 'name': 'Test'}

        result = await sheets_manager.create_project_sheet("Test", "aggregators")

        assert result.sheet_url == "https://docs.google.com/spreadsheets/d/abc123xyz/edit"

    @pytest.mark.asyncio
    async def test_create_project_sheet_all_six_template_types(self, sheets_manager, mock_gspread_client):
        """Test that all 6 template types are supported."""
        mock_gspread_client.open_by_key.return_value = Mock()
        mock_gspread_client.copy.return_value = {'id': 'new-id', 'name': 'Test'}

        template_types = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]

        for template_type in template_types:
            result = await sheets_manager.create_project_sheet("Test", template_type)
            assert result.template_type == template_type

    @pytest.mark.asyncio
    async def test_create_project_sheet_handles_api_error(self, sheets_manager, mock_gspread_client):
        """Test that API errors during creation are handled."""
        mock_gspread_client.open_by_key.return_value = Mock()

        # Mock APIError that's not a rate limit
        error = APIError(Mock(status_code=500, text="Internal Server Error"))
        mock_gspread_client.copy.side_effect = error

        with pytest.raises(SheetOperationError, match="Failed to create project sheet"):
            await sheets_manager.create_project_sheet("Test Project", "aggregators")


# Test Population Details
class TestPopulationDetails:
    """Additional population tests."""

    @pytest.mark.asyncio
    async def test_populate_sheet_maps_fields_correctly(self, sheets_manager, mock_gspread_client):
        """Test that field mapping is correct (meta_title -> B2, etc)."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "meta_description": "Test Description",
            "h1": "Test H1",
        }

        await sheets_manager.populate_sheet("sheet-id", content, "aggregators")

        call_args = mock_worksheet.batch_update.call_args[0][0]

        # Find the updates for our fields
        updates_dict = {u['range']: u['values'][0][0] for u in call_args}

        assert updates_dict['B2'] == "Test Title"
        assert updates_dict['B3'] == "Test Description"
        assert updates_dict['B4'] == "Test H1"

    @pytest.mark.asyncio
    async def test_populate_sheet_skips_unmapped_fields(self, sheets_manager, mock_gspread_client):
        """Test that fields not in mapping are ignored."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
            "unknown_field": "Should be ignored",
            "another_unknown": "Also ignored",
        }

        result = await sheets_manager.populate_sheet("sheet-id", content, "aggregators")

        # Only meta_title should be written
        assert result.fields_written == 1

    @pytest.mark.asyncio
    async def test_populate_converts_non_string_values_to_string(self, sheets_manager, mock_gspread_client):
        """Test that non-string values are converted to strings."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": 12345,  # Integer
            "starting_price": 1500000,  # Integer
        }

        await sheets_manager.populate_sheet("sheet-id", content, "aggregators")

        call_args = mock_worksheet.batch_update.call_args[0][0]
        updates_dict = {u['range']: u['values'][0][0] for u in call_args}

        # Should be converted to strings
        assert updates_dict['B2'] == "12345"
        assert updates_dict['B15'] == "1500000"

    @pytest.mark.asyncio
    async def test_populate_no_updates_if_empty_content(self, sheets_manager, mock_gspread_client):
        """Test that batch_update is not called if no valid content."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        # All values are None or empty
        content = {
            "meta_title": None,
            "meta_description": "",
            "h1": None,
        }

        result = await sheets_manager.populate_sheet("sheet-id", content, "aggregators")

        assert result.fields_written == 0
        assert not mock_worksheet.batch_update.called

    @pytest.mark.asyncio
    async def test_populate_empty_content_dict(self, sheets_manager, mock_gspread_client):
        """Test that populating with empty dict succeeds but writes nothing."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        result = await sheets_manager.populate_sheet("sheet-id", {}, "aggregators")

        assert result.fields_written == 0
        assert not mock_worksheet.batch_update.called


# Test Validation Details
class TestValidationDetails:
    """Additional validation tests."""

    @pytest.mark.asyncio
    async def test_validate_returns_details(self, sheets_manager, mock_gspread_client):
        """Test that validation returns per-field match/mismatch details."""
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            if cell_ref == "B2":
                cell.value = "Expected"
            elif cell_ref == "B3":
                cell.value = "Wrong Value"
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Expected",
            "meta_description": "Also Expected",
        }

        result = await sheets_manager.read_back_validate("sheet-id", content, "aggregators")

        assert len(result.details) == 2

        # Check first detail (match)
        detail_0 = result.details[0]
        assert detail_0['field'] == "meta_title"
        assert detail_0['cell'] == "B2"
        assert detail_0['expected'] == "Expected"
        assert detail_0['actual'] == "Expected"
        assert detail_0['match'] is True

        # Check second detail (mismatch)
        detail_1 = result.details[1]
        assert detail_1['field'] == "meta_description"
        assert detail_1['cell'] == "B3"
        assert detail_1['expected'] == "Also Expected"
        assert detail_1['actual'] == "Wrong Value"
        assert detail_1['match'] is False

    @pytest.mark.asyncio
    async def test_validate_handles_cell_error(self, sheets_manager, mock_gspread_client):
        """Test that cell read errors are recorded as mismatches."""
        mock_worksheet = Mock()
        mock_worksheet.acell.side_effect = Exception("Cell read error")
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test",
        }

        result = await sheets_manager.read_back_validate("sheet-id", content, "aggregators")

        assert result.mismatches == 1
        assert result.matches == 0
        assert "ERROR:" in result.details[0]['actual']

    @pytest.mark.asyncio
    async def test_validate_skips_empty_expected_values(self, sheets_manager, mock_gspread_client):
        """Test that fields with empty expected values are skipped."""
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            cell.value = "Test"
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test",
            "meta_description": "",
            "h1": None,
        }

        result = await sheets_manager.read_back_validate("sheet-id", content, "aggregators")

        # Only meta_title should be checked
        assert result.total_checked == 1

    @pytest.mark.asyncio
    async def test_validate_strips_whitespace(self, sheets_manager, mock_gspread_client):
        """Test that whitespace is stripped when comparing values."""
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            cell.value = "  Test Title  "
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test Title",
        }

        result = await sheets_manager.read_back_validate("sheet-id", content, "aggregators")

        # Should match despite whitespace
        assert result.matches == 1
        assert result.mismatches == 0

    @pytest.mark.asyncio
    async def test_validate_handles_none_cell_value(self, sheets_manager, mock_gspread_client):
        """Test that None cell values are treated as empty strings."""
        mock_worksheet = Mock()

        def mock_acell(cell_ref):
            cell = Mock()
            cell.value = None
            return cell

        mock_worksheet.acell = mock_acell
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        content = {
            "meta_title": "Test",
        }

        result = await sheets_manager.read_back_validate("sheet-id", content, "aggregators")

        # Should be mismatch (expected "Test", got "")
        assert result.mismatches == 1

    @pytest.mark.asyncio
    async def test_validate_empty_content_dict(self, sheets_manager, mock_gspread_client):
        """Test that validating with empty dict succeeds but checks nothing."""
        mock_worksheet = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        result = await sheets_manager.read_back_validate("sheet-id", {}, "aggregators")

        assert result.total_checked == 0
        assert result.matches == 0
        assert result.mismatches == 0


# Test Sharing Details
class TestSharingDetails:
    """Additional sharing tests."""

    @pytest.mark.asyncio
    async def test_share_with_different_roles(self, sheets_manager, mock_gspread_client):
        """Test sharing with reader, writer, and owner roles."""
        mock_spreadsheet = Mock()
        mock_spreadsheet.share = Mock()
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        roles = ["reader", "writer", "owner"]

        for role in roles:
            result = await sheets_manager.share_sheet("sheet-id", "user@example.com", role)
            assert result is True

            call_args = mock_spreadsheet.share.call_args
            assert call_args[1]['role'] == role

    @pytest.mark.asyncio
    async def test_share_handles_permission_error(self, sheets_manager, mock_gspread_client):
        """Test that permission errors during share are raised."""
        mock_spreadsheet = Mock()
        mock_spreadsheet.share.side_effect = Exception("Permission denied")
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        with pytest.raises(SheetOperationError, match="Failed to share sheet"):
            await sheets_manager.share_sheet("sheet-id", "user@example.com")


# Test Rate Limiting Details
class TestRateLimitingDetails:
    """Additional rate limiting tests."""

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self, sheets_manager, mock_gspread_client):
        """Test that RateLimitError is raised after max retries."""
        # Always return 429 error
        mock_response = Mock()
        mock_response.status_code = 429
        error_429 = APIError(mock_response)
        error_429.response = mock_response

        mock_gspread_client.open_by_key.side_effect = error_429

        with patch('time.sleep'):  # Don't actually sleep in tests
            with pytest.raises(SheetOperationError, match="Failed to populate sheet"):
                await sheets_manager.populate_sheet("sheet-id", {"meta_title": "Test"}, "aggregators")

        # Should have tried MAX_RETRIES times
        assert mock_gspread_client.open_by_key.call_count == sheets_manager.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, sheets_manager):
        """Test that exponential backoff increases delay correctly."""
        # Test backoff calculation
        delay_0 = sheets_manager._exponential_backoff(0)
        delay_1 = sheets_manager._exponential_backoff(1)
        delay_2 = sheets_manager._exponential_backoff(2)

        assert delay_0 == 1.0
        assert delay_1 == 2.0
        assert delay_2 == 4.0

        # Test max cap
        delay_10 = sheets_manager._exponential_backoff(10)
        assert delay_10 == sheets_manager.MAX_RETRY_DELAY

    @pytest.mark.asyncio
    async def test_non_rate_limit_api_error_retries_as_generic_error(self, sheets_manager, mock_gspread_client):
        """Test that non-429 API errors are treated as generic errors and retried."""
        # Create mock 500 error (not rate limit)
        mock_response = Mock()
        mock_response.status_code = 500
        error_500 = APIError(mock_response)
        error_500.response = mock_response

        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock(side_effect=error_500)
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet
        mock_gspread_client.open_by_key.return_value = mock_spreadsheet

        with patch('time.sleep'):  # Don't actually sleep in tests
            with pytest.raises(SheetOperationError, match="Failed to populate sheet"):
                await sheets_manager.populate_sheet("sheet-id", {"meta_title": "Test"}, "aggregators")

        # Non-429 API errors from within the function are treated as generic exceptions
        # and retried up to MAX_RETRIES times
        assert mock_worksheet.batch_update.call_count == sheets_manager.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_operation_with_transient_error(self, sheets_manager, mock_gspread_client):
        """Test that transient non-API errors are retried."""
        mock_worksheet = Mock()
        mock_worksheet.batch_update = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.sheet1 = mock_worksheet

        # First call fails with generic exception, second succeeds
        mock_gspread_client.open_by_key.side_effect = [
            Exception("Transient network error"),
            mock_spreadsheet
        ]

        with patch('time.sleep'):  # Don't actually sleep in tests
            result = await sheets_manager.populate_sheet("sheet-id", {"meta_title": "Test"}, "aggregators")

        assert isinstance(result, PopulateResult)
        assert mock_gspread_client.open_by_key.call_count == 2


# Test Data Classes
class TestDataClasses:
    """Test data class structures."""

    def test_sheet_result_dataclass(self):
        """Test SheetResult dataclass creation."""
        result = SheetResult(
            sheet_id="test-id",
            sheet_url="https://example.com",
            title="Test Sheet",
            template_type="aggregators",
            created_at="2026-01-27T12:00:00Z"
        )

        assert result.sheet_id == "test-id"
        assert result.sheet_url == "https://example.com"
        assert result.title == "Test Sheet"
        assert result.template_type == "aggregators"
        assert result.created_at == "2026-01-27T12:00:00Z"

    def test_populate_result_dataclass(self):
        """Test PopulateResult dataclass with default failures list."""
        result = PopulateResult(
            sheet_id="test-id",
            total_fields=10,
            fields_written=8,
            fields_failed=2
        )

        assert result.sheet_id == "test-id"
        assert result.total_fields == 10
        assert result.fields_written == 8
        assert result.fields_failed == 2
        assert result.failures == []

        # Test with failures
        result2 = PopulateResult(
            sheet_id="test-id",
            total_fields=10,
            fields_written=8,
            fields_failed=2,
            failures=[{"field": "test", "error": "error"}]
        )

        assert len(result2.failures) == 1

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass with default details list."""
        result = ValidationResult(
            sheet_id="test-id",
            total_checked=10,
            matches=8,
            mismatches=2
        )

        assert result.sheet_id == "test-id"
        assert result.total_checked == 10
        assert result.matches == 8
        assert result.mismatches == 2
        assert result.details == []

    def test_populate_result_independent_failures_lists(self):
        """Test that failures lists are independent instances."""
        result1 = PopulateResult(
            sheet_id="id1",
            total_fields=10,
            fields_written=10,
            fields_failed=0
        )

        result2 = PopulateResult(
            sheet_id="id2",
            total_fields=10,
            fields_written=10,
            fields_failed=0
        )

        result1.failures.append({"field": "test", "error": "error"})

        assert len(result1.failures) == 1
        assert len(result2.failures) == 0


# Test Exception Classes
class TestExceptionClasses:
    """Test custom exception classes."""

    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from SheetsManagerError."""
        from app.services.sheets_manager import SheetsManagerError

        assert issubclass(CredentialsError, SheetsManagerError)
        assert issubclass(TemplateNotFoundError, SheetsManagerError)
        assert issubclass(SheetOperationError, SheetsManagerError)
        assert issubclass(RateLimitError, SheetsManagerError)

    def test_exceptions_can_be_raised(self):
        """Test that custom exceptions can be raised with messages."""
        with pytest.raises(CredentialsError, match="Test credentials error"):
            raise CredentialsError("Test credentials error")

        with pytest.raises(TemplateNotFoundError, match="Template not found"):
            raise TemplateNotFoundError("Template not found")

        with pytest.raises(SheetOperationError, match="Operation failed"):
            raise SheetOperationError("Operation failed")

        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            raise RateLimitError("Rate limit exceeded")


# ============================================================================
# Risk Mitigation Tests - Template Validation
# ============================================================================


class TestTemplateValidation:
    """Tests for startup template accessibility validation."""

    @pytest.mark.asyncio
    async def test_validate_templates_all_accessible(self, mock_settings, mock_gspread_client):
        """Test validation when all templates are accessible."""
        with patch("app.services.sheets_manager.gspread.authorize", return_value=mock_gspread_client):
            with patch("app.services.sheets_manager.Credentials.from_service_account_file"):
                manager = SheetsManager()
                mock_gspread_client.open_by_key = Mock(return_value=Mock())

                results = await manager.validate_templates()

        assert len(results) == 6
        assert all(v is True for v in results.values())
        expected_types = {"aggregators", "opr", "mpp", "adop", "adre", "commercial"}
        assert set(results.keys()) == expected_types

    @pytest.mark.asyncio
    async def test_validate_templates_some_missing(self, mock_settings, mock_gspread_client):
        """Test validation when some templates are not accessible."""
        with patch("app.services.sheets_manager.gspread.authorize", return_value=mock_gspread_client):
            with patch("app.services.sheets_manager.Credentials.from_service_account_file"):
                manager = SheetsManager()

                call_count = 0

                def open_by_key_side_effect(key):
                    nonlocal call_count
                    call_count += 1
                    # Fail on 3rd and 5th template
                    if call_count in (3, 5):
                        raise SpreadsheetNotFound("Not found")
                    return Mock()

                mock_gspread_client.open_by_key = Mock(side_effect=open_by_key_side_effect)

                results = await manager.validate_templates()

        assert len(results) == 6
        accessible = sum(1 for v in results.values() if v)
        missing = sum(1 for v in results.values() if not v)
        assert accessible == 4
        assert missing == 2

    @pytest.mark.asyncio
    async def test_validate_templates_all_missing(self, mock_settings, mock_gspread_client):
        """Test validation when all templates are inaccessible."""
        with patch("app.services.sheets_manager.gspread.authorize", return_value=mock_gspread_client):
            with patch("app.services.sheets_manager.Credentials.from_service_account_file"):
                manager = SheetsManager()
                mock_gspread_client.open_by_key = Mock(
                    side_effect=SpreadsheetNotFound("Not found")
                )

                results = await manager.validate_templates()

        assert len(results) == 6
        assert all(v is False for v in results.values())
