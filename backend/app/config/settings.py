"""
Configuration management for PDP Automation v.3

Loads settings from environment variables or GCP Secret Manager (in production).
Uses Pydantic for validation and type safety.
"""

from functools import lru_cache
from typing import Any
import logging
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment Configuration
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Database Configuration
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=300, description="Connection recycle time (seconds). 300s suits Cloud Run; increase for long-lived servers.")
    DATABASE_ECHO: bool = Field(default=False, description="Log SQL statements")

    # Authentication Configuration
    JWT_SECRET: str = Field(..., description="JWT signing secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRY_HOURS: int = Field(default=1, description="Access token expiry hours")
    REFRESH_TOKEN_EXPIRY_DAYS: int = Field(default=7, description="Refresh token expiry days")
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = Field(..., description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:5174/auth/callback",
        description="OAuth redirect URI"
    )
    GOOGLE_TOKEN_URI: str = Field(
        default="https://oauth2.googleapis.com/token",
        description="Google token endpoint"
    )
    GOOGLE_AUTH_URI: str = Field(
        default="https://accounts.google.com/o/oauth2/auth",
        description="Google auth endpoint"
    )

    # Google Cloud Platform Configuration (required -- no hardcoded defaults)
    GCP_PROJECT_ID: str = Field(
        ...,
        description="GCP project ID (e.g. 'my-project-123')"
    )
    GCS_BUCKET_NAME: str = Field(
        ...,
        description="Google Cloud Storage bucket name (e.g. 'my-bucket-dev')"
    )
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        default=None,
        description="Path to GCP service account key file"
    )

    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(
        default="claude-sonnet-4-5-20250514",
        description="Anthropic model identifier"
    )
    ANTHROPIC_MAX_TOKENS: int = Field(default=4096, description="Max tokens per request")
    ANTHROPIC_TEMPERATURE: float = Field(default=0.0, description="Model temperature")
    ANTHROPIC_TIMEOUT: int = Field(default=300, description="API timeout in seconds")

    # Google Sheets Template Configuration (6 Templates)
    TEMPLATE_SHEET_ID_AGGREGATORS: str = Field(
        ...,
        description="Template sheet ID for Aggregators"
    )
    TEMPLATE_SHEET_ID_OPR: str = Field(
        ...,
        description="Template sheet ID for OPR"
    )
    TEMPLATE_SHEET_ID_MPP: str = Field(
        ...,
        description="Template sheet ID for MPP"
    )
    TEMPLATE_SHEET_ID_ADOP: str = Field(
        ...,
        description="Template sheet ID for Ad Operations"
    )
    TEMPLATE_SHEET_ID_ADRE: str = Field(
        ...,
        description="Template sheet ID for Ad Revenue"
    )
    TEMPLATE_SHEET_ID_COMMERCIAL: str = Field(
        ...,
        description="Template sheet ID for Commercial"
    )

    # Google Drive Configuration
    GOOGLE_DRIVE_ROOT_FOLDER_ID: str = Field(
        ...,
        description="Root folder ID for document generation"
    )
    GOOGLE_DRIVE_API_VERSION: str = Field(
        default="v3",
        description="Google Drive API version"
    )
    GOOGLE_SHARED_DRIVE_ID: str | None = Field(
        default=None,
        description="Shared Drive ID (overrides hardcoded default in drive_client.py)"
    )

    # Internal API Key (required -- no default to prevent accidental exposure)
    INTERNAL_API_KEY: str = Field(
        ...,
        description="Internal API authentication key for Cloud Tasks callbacks"
    )

    # Application Configuration
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version prefix"
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5174"],
        description="CORS allowed origins"
    )
    ALLOWED_EMAIL_DOMAIN: str = Field(
        default="your-domain.com",
        description="Allowed email domain for authentication"
    )
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=50,
        description="Maximum file upload size in MB"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="API rate limit per minute per user"
    )

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    WORKERS: int = Field(default=1, description="Number of worker processes")
    RELOAD: bool = Field(default=False, description="Enable auto-reload")

    # Feature Flags
    ENABLE_REGISTRATION: bool = Field(
        default=False,
        description="Allow new user registration"
    )
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    ENABLE_AUDIT_LOG: bool = Field(
        default=True,
        description="Enable audit logging"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate and normalize DATABASE_URL to async driver format."""
        if not v:
            raise ValueError("DATABASE_URL is required")

        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )

        # Auto-convert to async driver if plain postgresql:// is provided (P3-19)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate ENVIRONMENT is one of allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate LOG_LEVEL is valid."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT_SECRET has minimum length."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @field_validator("ANTHROPIC_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("ANTHROPIC_TEMPERATURE must be between 0.0 and 1.0")
        return v

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_origins(cls, v: list[str] | str) -> list[str]:
        """Parse ALLOWED_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("GOOGLE_CLIENT_ID")
    @classmethod
    def validate_google_client_id(cls, v: str) -> str:
        """Validate Google OAuth client ID format."""
        if not v:
            raise ValueError("GOOGLE_CLIENT_ID is required")
        if not v.endswith(".apps.googleusercontent.com"):
            raise ValueError(
                "GOOGLE_CLIENT_ID must end with '.apps.googleusercontent.com'"
            )
        return v

    @field_validator("GOOGLE_CLIENT_SECRET")
    @classmethod
    def validate_google_client_secret(cls, v: str) -> str:
        """Validate Google OAuth client secret has minimum length."""
        if not v:
            raise ValueError("GOOGLE_CLIENT_SECRET is required")
        if len(v) < 10:
            raise ValueError("GOOGLE_CLIENT_SECRET appears invalid (too short)")
        return v

    @field_validator(
        "TEMPLATE_SHEET_ID_AGGREGATORS",
        "TEMPLATE_SHEET_ID_OPR",
        "TEMPLATE_SHEET_ID_MPP",
        "TEMPLATE_SHEET_ID_ADOP",
        "TEMPLATE_SHEET_ID_ADRE",
        "TEMPLATE_SHEET_ID_COMMERCIAL",
    )
    @classmethod
    def validate_sheet_id(cls, v: str) -> str:
        """Validate Google Sheets ID format."""
        if not v:
            raise ValueError("Template sheet ID is required")
        # Google Sheets IDs are typically 44 alphanumeric characters with hyphens/underscores
        if len(v) < 20:
            raise ValueError(
                f"Template sheet ID '{v}' appears invalid (too short). "
                "Get the ID from: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
            )
        # Check for placeholder values
        if v.startswith("your-") or v == "example":
            raise ValueError(
                f"Template sheet ID '{v}' is a placeholder. "
                "Please provide an actual Google Sheets ID."
            )
        return v

    @field_validator("GOOGLE_DRIVE_ROOT_FOLDER_ID")
    @classmethod
    def validate_drive_folder_id(cls, v: str) -> str:
        """Validate Google Drive folder ID format."""
        if not v:
            raise ValueError("GOOGLE_DRIVE_ROOT_FOLDER_ID is required")
        # Shared Drive IDs can be 19 characters, regular folder IDs are longer
        if len(v) < 15:
            raise ValueError(
                f"Drive folder ID '{v}' appears invalid (too short). "
                "Get the ID from: https://drive.google.com/drive/folders/{FOLDER_ID}"
            )
        if v.startswith("your-") or v == "example":
            raise ValueError(
                f"Drive folder ID '{v}' is a placeholder. "
                "Please provide an actual Google Drive folder ID."
            )
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    def get_template_sheet_id(self, template_name: str) -> str:
        """Get template sheet ID by name."""
        template_map = {
            "aggregators": self.TEMPLATE_SHEET_ID_AGGREGATORS,
            "opr": self.TEMPLATE_SHEET_ID_OPR,
            "mpp": self.TEMPLATE_SHEET_ID_MPP,
            "adop": self.TEMPLATE_SHEET_ID_ADOP,
            "adre": self.TEMPLATE_SHEET_ID_ADRE,
            "commercial": self.TEMPLATE_SHEET_ID_COMMERCIAL,
        }

        template_key = template_name.lower()
        if template_key not in template_map:
            raise ValueError(
                f"Unknown template: {template_name}. "
                f"Valid templates: {list(template_map.keys())}"
            )

        return template_map[template_key]

    def log_configuration(self) -> None:
        """Log configuration (excluding secrets) at startup."""
        safe_config = {
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "log_level": self.LOG_LEVEL,
            "api_prefix": self.API_V1_PREFIX,
            "allowed_origins": self.ALLOWED_ORIGINS,
            "gcp_project": self.GCP_PROJECT_ID,
            "gcs_bucket": self.GCS_BUCKET_NAME,
            "anthropic_model": self.ANTHROPIC_MODEL,
            "database_pool_size": self.DATABASE_POOL_SIZE,
            "jwt_expiry_hours": self.JWT_EXPIRY_HOURS,
            "features": {
                "registration": self.ENABLE_REGISTRATION,
                "metrics": self.ENABLE_METRICS,
                "audit_log": self.ENABLE_AUDIT_LOG,
            }
        }

        logger.info("Application configuration loaded", extra={"config": safe_config})


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded once and reused.
    Call this function to access application settings.
    """
    settings = Settings()
    settings.log_configuration()
    return settings
