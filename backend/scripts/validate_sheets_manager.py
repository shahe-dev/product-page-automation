"""
Validation script for SheetsManager implementation

This script validates the SheetsManager service without requiring
actual Google credentials. It checks:
- Import success
- Class structure
- Method signatures
- Data class definitions
- Error handling
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def validate_imports():
    """Validate all imports work correctly."""
    print("Validating imports...")
    try:
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
        print("  - All imports successful")
        return True
    except ImportError as e:
        print(f"  - Import failed: {e}")
        return False


def validate_data_classes():
    """Validate data class structure."""
    print("\nValidating data classes...")
    from app.services.sheets_manager import (
        SheetResult,
        PopulateResult,
        ValidationResult,
    )

    # SheetResult
    result = SheetResult(
        sheet_id="test-id",
        sheet_url="https://example.com",
        title="Test",
        template_type="aggregators",
        created_at="2024-01-01T00:00:00Z"
    )
    assert result.sheet_id == "test-id"
    print("  - SheetResult: OK")

    # PopulateResult
    populate = PopulateResult(
        sheet_id="test-id",
        total_fields=10,
        fields_written=8,
        fields_failed=2,
        failures=[{"field": "test", "error": "error"}]
    )
    assert populate.fields_written == 8
    print("  - PopulateResult: OK")

    # ValidationResult
    validation = ValidationResult(
        sheet_id="test-id",
        total_checked=5,
        matches=3,
        mismatches=2,
        details=[{"field": "test", "match": True}]
    )
    assert validation.matches == 3
    print("  - ValidationResult: OK")

    return True


def validate_exceptions():
    """Validate exception hierarchy."""
    print("\nValidating exceptions...")
    from app.services.sheets_manager import (
        SheetsManagerError,
        CredentialsError,
        TemplateNotFoundError,
        SheetOperationError,
        RateLimitError,
    )

    # Check inheritance
    assert issubclass(CredentialsError, SheetsManagerError)
    assert issubclass(TemplateNotFoundError, SheetsManagerError)
    assert issubclass(SheetOperationError, SheetsManagerError)
    assert issubclass(RateLimitError, SheetsManagerError)
    print("  - Exception hierarchy: OK")

    # Test raising
    try:
        raise CredentialsError("Test error")
    except SheetsManagerError as e:
        assert str(e) == "Test error"
        print("  - Exception raising: OK")

    return True


def validate_field_mapping():
    """Validate field mapping structure."""
    print("\nValidating field mapping...")
    from app.services.sheets_manager import COMMON_FIELD_MAPPING

    # Check required fields exist
    required_fields = [
        "meta_title",
        "meta_description",
        "h1",
        "url_slug",
        "short_description",
        "long_description",
        "project_name",
        "developer",
        "location",
    ]

    for field in required_fields:
        assert field in COMMON_FIELD_MAPPING, f"Missing field: {field}"

    # Check cell references format (should be like "B2", "B12", etc.)
    for field, cell in COMMON_FIELD_MAPPING.items():
        assert len(cell) >= 2, f"Invalid cell reference: {cell}"
        assert cell[0].isalpha(), f"Invalid cell column: {cell}"
        assert cell[1:].isdigit(), f"Invalid cell row: {cell}"

    print(f"  - Field mapping: OK ({len(COMMON_FIELD_MAPPING)} fields)")
    return True


def validate_class_structure():
    """Validate SheetsManager class structure."""
    print("\nValidating class structure...")
    from app.services.sheets_manager import SheetsManager
    from unittest.mock import Mock, patch

    # Check class attributes
    assert hasattr(SheetsManager, 'MAX_RETRIES')
    assert hasattr(SheetsManager, 'INITIAL_RETRY_DELAY')
    assert hasattr(SheetsManager, 'MAX_RETRY_DELAY')
    print("  - Class constants: OK")

    # Check required methods exist
    required_methods = [
        '__init__',
        'create_project_sheet',
        'populate_sheet',
        'read_back_validate',
        'share_sheet',
        '_get_field_mapping',
        '_retry_operation',
        '_exponential_backoff',
    ]

    for method in required_methods:
        assert hasattr(SheetsManager, method), f"Missing method: {method}"

    print("  - Required methods: OK")
    return True


def validate_template_types():
    """Validate template type handling."""
    print("\nValidating template types...")
    from app.models.enums import TemplateType
    from app.services.sheets_manager import SheetsManager
    from unittest.mock import Mock, patch

    # Mock settings
    with patch('app.services.sheets_manager.get_settings') as mock_settings:
        with patch('app.services.sheets_manager.gspread.authorize'):
            with patch('app.services.sheets_manager.Credentials.from_service_account_file'):
                settings = Mock()
                settings.GOOGLE_APPLICATION_CREDENTIALS = "/fake/path.json"
                settings.get_template_sheet_id = Mock(return_value="fake-id")
                mock_settings.return_value = settings

                manager = SheetsManager()

                # Test all template types
                for template in TemplateType:
                    mapping = manager._get_field_mapping(template.value)
                    assert len(mapping) > 0, f"Empty mapping for {template.value}"

                print(f"  - Template types: OK ({len(TemplateType)} templates)")

    return True


def validate_exponential_backoff():
    """Validate exponential backoff calculation."""
    print("\nValidating exponential backoff...")
    from app.services.sheets_manager import SheetsManager
    from unittest.mock import Mock, patch

    with patch('app.services.sheets_manager.get_settings'):
        with patch('app.services.sheets_manager.gspread.authorize'):
            with patch('app.services.sheets_manager.Credentials.from_service_account_file'):
                manager = SheetsManager()

                # Test backoff calculations
                assert manager._exponential_backoff(0, 1.0) == 1.0
                assert manager._exponential_backoff(1, 1.0) == 2.0
                assert manager._exponential_backoff(2, 1.0) == 4.0
                assert manager._exponential_backoff(3, 1.0) == 8.0
                assert manager._exponential_backoff(4, 1.0) == 16.0

                # Test capping
                assert manager._exponential_backoff(10, 1.0) == manager.MAX_RETRY_DELAY

                print("  - Exponential backoff: OK")

    return True


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("SheetsManager Validation Script")
    print("=" * 60)

    checks = [
        ("Imports", validate_imports),
        ("Data Classes", validate_data_classes),
        ("Exceptions", validate_exceptions),
        ("Field Mapping", validate_field_mapping),
        ("Class Structure", validate_class_structure),
        ("Template Types", validate_template_types),
        ("Exponential Backoff", validate_exponential_backoff),
    ]

    results = []
    for name, check_func in checks:
        try:
            success = check_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n  ERROR: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{name:.<40} {status}")
        if not success:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\nAll validations passed!")
        return 0
    else:
        print("\nSome validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
