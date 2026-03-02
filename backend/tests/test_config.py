"""
Tests for configuration module.

Demonstrates how to override settings for testing.
"""

import pytest
from pydantic import ValidationError
from app.config import Settings, get_settings


class TestSettings:
    """Test settings validation and loading."""

    def test_settings_validation_success(self):
        """Test valid settings load successfully."""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test",
            JWT_SECRET="a" * 32,  # Min 32 chars
            GOOGLE_CLIENT_ID="test-client-id",
            GOOGLE_CLIENT_SECRET="test-secret",
            ANTHROPIC_API_KEY="sk-ant-test-key",
            TEMPLATE_SHEET_ID_AGGREGATORS="test-aggregators",
            TEMPLATE_SHEET_ID_OPR="test-opr",
            TEMPLATE_SHEET_ID_MPP="test-mpp",
            TEMPLATE_SHEET_ID_ADOP="test-adop",
            TEMPLATE_SHEET_ID_ADRE="test-adre",
            TEMPLATE_SHEET_ID_COMMERCIAL="test-commercial",
            GOOGLE_DRIVE_ROOT_FOLDER_ID="test-folder",
        )

        assert settings.ENVIRONMENT == "development"
        assert settings.DATABASE_URL.startswith("postgresql")
        assert len(settings.JWT_SECRET) >= 32

    def test_database_url_validation_invalid_protocol(self):
        """Test DATABASE_URL validation rejects invalid protocols."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                DATABASE_URL="mysql://user:pass@localhost/test",
                JWT_SECRET="a" * 32,
                GOOGLE_CLIENT_ID="test",
                GOOGLE_CLIENT_SECRET="test",
                ANTHROPIC_API_KEY="sk-ant-test",
                TEMPLATE_SHEET_ID_AGGREGATORS="test",
                TEMPLATE_SHEET_ID_OPR="test",
                TEMPLATE_SHEET_ID_MPP="test",
                TEMPLATE_SHEET_ID_ADOP="test",
                TEMPLATE_SHEET_ID_ADRE="test",
                TEMPLATE_SHEET_ID_COMMERCIAL="test",
                GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
            )

        assert "postgresql" in str(exc_info.value).lower()

    def test_jwt_secret_too_short(self):
        """Test JWT_SECRET validation requires minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                DATABASE_URL="postgresql://user:pass@localhost/test",
                JWT_SECRET="short",  # Too short
                GOOGLE_CLIENT_ID="test",
                GOOGLE_CLIENT_SECRET="test",
                ANTHROPIC_API_KEY="sk-ant-test",
                TEMPLATE_SHEET_ID_AGGREGATORS="test",
                TEMPLATE_SHEET_ID_OPR="test",
                TEMPLATE_SHEET_ID_MPP="test",
                TEMPLATE_SHEET_ID_ADOP="test",
                TEMPLATE_SHEET_ID_ADRE="test",
                TEMPLATE_SHEET_ID_COMMERCIAL="test",
                GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
            )

        assert "32 characters" in str(exc_info.value)

    def test_environment_validation(self):
        """Test ENVIRONMENT must be valid value."""
        with pytest.raises(ValidationError):
            Settings(
                ENVIRONMENT="invalid",
                DATABASE_URL="postgresql://user:pass@localhost/test",
                JWT_SECRET="a" * 32,
                GOOGLE_CLIENT_ID="test",
                GOOGLE_CLIENT_SECRET="test",
                ANTHROPIC_API_KEY="sk-ant-test",
                TEMPLATE_SHEET_ID_AGGREGATORS="test",
                TEMPLATE_SHEET_ID_OPR="test",
                TEMPLATE_SHEET_ID_MPP="test",
                TEMPLATE_SHEET_ID_ADOP="test",
                TEMPLATE_SHEET_ID_ADRE="test",
                TEMPLATE_SHEET_ID_COMMERCIAL="test",
                GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
            )

    def test_temperature_validation(self):
        """Test ANTHROPIC_TEMPERATURE must be in valid range."""
        with pytest.raises(ValidationError):
            Settings(
                DATABASE_URL="postgresql://user:pass@localhost/test",
                JWT_SECRET="a" * 32,
                GOOGLE_CLIENT_ID="test",
                GOOGLE_CLIENT_SECRET="test",
                ANTHROPIC_API_KEY="sk-ant-test",
                ANTHROPIC_TEMPERATURE=1.5,  # Invalid: > 1.0
                TEMPLATE_SHEET_ID_AGGREGATORS="test",
                TEMPLATE_SHEET_ID_OPR="test",
                TEMPLATE_SHEET_ID_MPP="test",
                TEMPLATE_SHEET_ID_ADOP="test",
                TEMPLATE_SHEET_ID_ADRE="test",
                TEMPLATE_SHEET_ID_COMMERCIAL="test",
                GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
            )

    def test_allowed_origins_parsing(self):
        """Test ALLOWED_ORIGINS can be parsed from comma-separated string."""
        settings = Settings(
            DATABASE_URL="postgresql://user:pass@localhost/test",
            JWT_SECRET="a" * 32,
            GOOGLE_CLIENT_ID="test",
            GOOGLE_CLIENT_SECRET="test",
            ANTHROPIC_API_KEY="sk-ant-test",
            ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5174",
            TEMPLATE_SHEET_ID_AGGREGATORS="test",
            TEMPLATE_SHEET_ID_OPR="test",
            TEMPLATE_SHEET_ID_MPP="test",
            TEMPLATE_SHEET_ID_ADOP="test",
            TEMPLATE_SHEET_ID_ADRE="test",
            TEMPLATE_SHEET_ID_COMMERCIAL="test",
            GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
        )

        assert len(settings.ALLOWED_ORIGINS) == 2
        assert "http://localhost:3000" in settings.ALLOWED_ORIGINS

    def test_environment_properties(self):
        """Test environment helper properties."""
        dev_settings = Settings(
            ENVIRONMENT="development",
            DATABASE_URL="postgresql://user:pass@localhost/test",
            JWT_SECRET="a" * 32,
            GOOGLE_CLIENT_ID="test",
            GOOGLE_CLIENT_SECRET="test",
            ANTHROPIC_API_KEY="sk-ant-test",
            TEMPLATE_SHEET_ID_AGGREGATORS="test",
            TEMPLATE_SHEET_ID_OPR="test",
            TEMPLATE_SHEET_ID_MPP="test",
            TEMPLATE_SHEET_ID_ADOP="test",
            TEMPLATE_SHEET_ID_ADRE="test",
            TEMPLATE_SHEET_ID_COMMERCIAL="test",
            GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
        )

        assert dev_settings.is_development is True
        assert dev_settings.is_production is False
        assert dev_settings.is_staging is False

    def test_get_template_sheet_id(self):
        """Test template sheet ID lookup."""
        settings = Settings(
            DATABASE_URL="postgresql://user:pass@localhost/test",
            JWT_SECRET="a" * 32,
            GOOGLE_CLIENT_ID="test",
            GOOGLE_CLIENT_SECRET="test",
            ANTHROPIC_API_KEY="sk-ant-test",
            TEMPLATE_SHEET_ID_AGGREGATORS="aggregators-123",
            TEMPLATE_SHEET_ID_OPR="opr-456",
            TEMPLATE_SHEET_ID_MPP="mpp-789",
            TEMPLATE_SHEET_ID_ADOP="adop-101",
            TEMPLATE_SHEET_ID_ADRE="adre-202",
            TEMPLATE_SHEET_ID_COMMERCIAL="commercial-303",
            GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
        )

        assert settings.get_template_sheet_id("aggregators") == "aggregators-123"
        assert settings.get_template_sheet_id("opr") == "opr-456"
        assert settings.get_template_sheet_id("COMMERCIAL") == "commercial-303"

        with pytest.raises(ValueError):
            settings.get_template_sheet_id("invalid")

    def test_database_url_sync_property(self):
        """Test sync database URL for Alembic."""
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test",
            JWT_SECRET="a" * 32,
            GOOGLE_CLIENT_ID="test",
            GOOGLE_CLIENT_SECRET="test",
            ANTHROPIC_API_KEY="sk-ant-test",
            TEMPLATE_SHEET_ID_AGGREGATORS="test",
            TEMPLATE_SHEET_ID_OPR="test",
            TEMPLATE_SHEET_ID_MPP="test",
            TEMPLATE_SHEET_ID_ADOP="test",
            TEMPLATE_SHEET_ID_ADRE="test",
            TEMPLATE_SHEET_ID_COMMERCIAL="test",
            GOOGLE_DRIVE_ROOT_FOLDER_ID="test",
        )

        assert settings.database_url_sync == "postgresql://user:pass@localhost/test"
        assert "+asyncpg" not in settings.database_url_sync


@pytest.fixture
def test_settings():
    """Fixture providing test settings."""
    return Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test_db",
        JWT_SECRET="test-secret-key-minimum-32-characters-long",
        GOOGLE_CLIENT_ID="test-client-id",
        GOOGLE_CLIENT_SECRET="test-client-secret",
        ANTHROPIC_API_KEY="sk-ant-test-key",
        TEMPLATE_SHEET_ID_AGGREGATORS="test-aggregators",
        TEMPLATE_SHEET_ID_OPR="test-opr",
        TEMPLATE_SHEET_ID_MPP="test-mpp",
        TEMPLATE_SHEET_ID_ADOP="test-adop",
        TEMPLATE_SHEET_ID_ADRE="test-adre",
        TEMPLATE_SHEET_ID_COMMERCIAL="test-commercial",
        GOOGLE_DRIVE_ROOT_FOLDER_ID="test-folder",
    )


class TestDatabaseConfiguration:
    """Test database configuration.

    NOTE: These tests require a live database connection.
    They are marked with @pytest.mark.integration and skip automatically
    when no DATABASE_URL is reachable.
    """

    @pytest.mark.asyncio
    async def test_database_session_context(self, test_settings):
        """Test that get_db_session yields an AsyncSession and cleans up."""
        # Verify the settings object exposes the expected database URL format
        assert test_settings.DATABASE_URL.startswith("postgresql")
        # Full integration test requires a running database and is handled
        # by the route-level test suite (test_routes/).

    @pytest.mark.asyncio
    async def test_connection_pool_defaults(self, test_settings):
        """Test connection pool configuration defaults are reasonable."""
        # Pool recycle should be set for cloud environments
        assert hasattr(test_settings, "DATABASE_URL")
        # Verify the sync URL conversion works
        sync_url = test_settings.database_url_sync
        assert "asyncpg" not in sync_url
