#!/usr/bin/env python3
"""
Configuration validation script for PDP Automation v.3

Validates that all required configuration is present and correct.
Run this before deploying to catch configuration issues early.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Tuple
import asyncio


def validate_environment_variables() -> Tuple[bool, List[str]]:
    """
    Check if required environment variables are present.

    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []

    required_vars = [
        "DATABASE_URL",
        "JWT_SECRET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "ANTHROPIC_API_KEY",
        "TEMPLATE_SHEET_ID_AGGREGATORS",
        "TEMPLATE_SHEET_ID_OPR",
        "TEMPLATE_SHEET_ID_MPP",
        "TEMPLATE_SHEET_ID_ADOP",
        "TEMPLATE_SHEET_ID_ADRE",
        "TEMPLATE_SHEET_ID_COMMERCIAL",
        "GOOGLE_DRIVE_ROOT_FOLDER_ID",
    ]

    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")

    return len(errors) == 0, errors


def validate_settings() -> Tuple[bool, List[str]]:
    """
    Validate settings can be loaded and are valid.

    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []

    try:
        from app.config import get_settings

        settings = get_settings()

        # Check database URL format
        if not settings.DATABASE_URL.startswith(("postgresql://", "postgresql+asyncpg://")):
            errors.append(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )

        # Check JWT secret length
        if len(settings.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")

        # Check environment value
        if settings.ENVIRONMENT not in ["development", "staging", "production"]:
            errors.append(
                f"ENVIRONMENT must be one of: development, staging, production "
                f"(got: {settings.ENVIRONMENT})"
            )

        # Check temperature range
        if not 0.0 <= settings.ANTHROPIC_TEMPERATURE <= 1.0:
            errors.append(
                f"ANTHROPIC_TEMPERATURE must be between 0.0 and 1.0 "
                f"(got: {settings.ANTHROPIC_TEMPERATURE})"
            )

        # Check allowed origins
        if not settings.ALLOWED_ORIGINS:
            errors.append("ALLOWED_ORIGINS must not be empty")

        # Validate template sheet IDs are not example values
        template_fields = [
            "TEMPLATE_SHEET_ID_AGGREGATORS",
            "TEMPLATE_SHEET_ID_OPR",
            "TEMPLATE_SHEET_ID_MPP",
            "TEMPLATE_SHEET_ID_ADOP",
            "TEMPLATE_SHEET_ID_ADRE",
            "TEMPLATE_SHEET_ID_COMMERCIAL",
        ]

        for field in template_fields:
            value = getattr(settings, field)
            if value.startswith("your-") or value == "":
                errors.append(
                    f"{field} appears to be an example value, please set actual sheet ID"
                )

        # Check Google Drive folder ID
        if settings.GOOGLE_DRIVE_ROOT_FOLDER_ID.startswith("your-"):
            errors.append(
                "GOOGLE_DRIVE_ROOT_FOLDER_ID appears to be an example value"
            )

        # Check Anthropic API key format
        if not settings.ANTHROPIC_API_KEY.startswith("sk-ant-"):
            errors.append(
                "ANTHROPIC_API_KEY should start with 'sk-ant-' "
                "(this may be a test key)"
            )

    except Exception as e:
        errors.append(f"Failed to load settings: {str(e)}")

    return len(errors) == 0, errors


async def validate_database_connection() -> Tuple[bool, List[str]]:
    """
    Test database connectivity.

    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []

    try:
        from app.config import check_database_connection

        connected = await check_database_connection()
        if not connected:
            errors.append("Database connection failed")

    except Exception as e:
        errors.append(f"Database connection error: {str(e)}")

    return len(errors) == 0, errors


def validate_google_credentials() -> Tuple[bool, List[str]]:
    """
    Validate Google Cloud credentials are configured.

    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if creds_path:
        if not os.path.exists(creds_path):
            errors.append(
                f"GOOGLE_APPLICATION_CREDENTIALS path does not exist: {creds_path}"
            )
    else:
        # Check if default credentials are available
        try:
            import google.auth
            google.auth.default()
        except Exception as e:
            errors.append(
                "No Google credentials found. Set GOOGLE_APPLICATION_CREDENTIALS "
                f"or configure default credentials: {str(e)}"
            )

    return len(errors) == 0, errors


async def run_validation() -> int:
    """
    Run all validation checks.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    print("=" * 70)
    print("PDP Automation v.3 - Configuration Validation")
    print("=" * 70)
    print()

    all_success = True
    total_errors = []

    # Check environment variables
    print("[1/4] Checking environment variables...")
    success, errors = validate_environment_variables()
    if success:
        print("  OK - All required environment variables present")
    else:
        print(f"  FAILED - {len(errors)} error(s)")
        for error in errors:
            print(f"    - {error}")
        total_errors.extend(errors)
        all_success = False
    print()

    # Validate settings
    print("[2/4] Validating settings configuration...")
    success, errors = validate_settings()
    if success:
        print("  OK - Settings validated successfully")
    else:
        print(f"  FAILED - {len(errors)} error(s)")
        for error in errors:
            print(f"    - {error}")
        total_errors.extend(errors)
        all_success = False
    print()

    # Test database connection
    print("[3/4] Testing database connection...")
    success, errors = await validate_database_connection()
    if success:
        print("  OK - Database connection successful")
    else:
        print(f"  FAILED - {len(errors)} error(s)")
        for error in errors:
            print(f"    - {error}")
        total_errors.extend(errors)
        all_success = False
    print()

    # Validate Google credentials
    print("[4/4] Validating Google Cloud credentials...")
    success, errors = validate_google_credentials()
    if success:
        print("  OK - Google credentials configured")
    else:
        print(f"  WARNING - {len(errors)} warning(s)")
        for error in errors:
            print(f"    - {error}")
        # Don't fail on Google creds, just warn
    print()

    # Summary
    print("=" * 70)
    if all_success:
        print("VALIDATION PASSED")
        print("Configuration is valid and ready for use")
        return 0
    else:
        print("VALIDATION FAILED")
        print(f"Found {len(total_errors)} error(s) that must be fixed")
        print()
        print("Steps to fix:")
        print("1. Check your .env file exists and is in the backend directory")
        print("2. Copy .env.example to .env if missing")
        print("3. Fill in all required values in .env")
        print("4. Ensure database is running and accessible")
        print("5. Run this script again")
        return 1


def main():
    """Main entry point."""
    # Check if .env file exists
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("ERROR: .env file not found")
        print(f"Expected location: {env_path}")
        print()
        print("To fix:")
        print(f"  cp {env_path.parent}/.env.example {env_path}")
        print("  # Then edit .env with your configuration")
        return 1

    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        print("WARNING: python-dotenv not installed, relying on system environment")
    except Exception as e:
        print(f"ERROR: Failed to load .env file: {e}")
        return 1

    # Run validation
    try:
        exit_code = asyncio.run(run_validation())
        return exit_code
    except KeyboardInterrupt:
        print("\nValidation interrupted")
        return 130
    except Exception as e:
        print(f"\nUnexpected error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
