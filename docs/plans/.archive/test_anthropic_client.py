"""
Quick test script to verify centralized Anthropic client integration.

Tests:
1. Import validation
2. Token counter utilities
3. Service initialization
4. Session usage tracking (without API calls)
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from app.integrations.anthropic_client import anthropic_service
        from app.utils.token_counter import (
            calculate_cost,
            estimate_text_tokens,
            estimate_image_tokens,
            format_cost
        )
        print("  All imports successful")
        return True
    except ImportError as e:
        print(f"  Import failed: {e}")
        return False


def test_token_counter():
    """Test token counter utilities."""
    print("\nTesting token counter utilities...")

    from app.utils.token_counter import (
        calculate_cost,
        estimate_text_tokens,
        estimate_image_tokens,
        format_cost
    )

    # Test text estimation
    text_tokens = estimate_text_tokens("Hello world! " * 100)
    print(f"  Text tokens estimate: {text_tokens}")

    # Test image estimation
    image_tokens = estimate_image_tokens(1024, 768)
    print(f"  Image tokens estimate: {image_tokens}")

    # Test cost calculation
    cost = calculate_cost(1000, 500)
    print(f"  Cost for 1000 in + 500 out: ${cost:.4f}")

    # Test cost formatting
    formatted = format_cost(1000, 500)
    print(f"  Formatted: {formatted}")

    return True


def test_service_initialization():
    """Test that service initializes correctly."""
    print("\nTesting service initialization...")

    from app.integrations.anthropic_client import anthropic_service

    # Check service attributes
    print(f"  Service initialized: {anthropic_service is not None}")
    print(f"  Has client: {hasattr(anthropic_service, 'client')}")
    print(f"  Has settings: {hasattr(anthropic_service, 'settings')}")

    # Check session stats
    stats = anthropic_service.get_session_usage()
    print(f"  Session stats: {stats}")

    return True


def test_refactored_services():
    """Test that refactored services import correctly."""
    print("\nTesting refactored services...")

    try:
        from app.services.content_generator import ContentGenerator
        from app.services.data_structurer import DataStructurer

        print("  ContentGenerator import: OK")
        print("  DataStructurer import: OK")

        # Test initialization (without actual API calls)
        # ContentGenerator requires brand context file, so we skip full init
        print("  Services can be imported successfully")

        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Anthropic Client Integration Test")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Token Counter", test_token_counter()))
    results.append(("Service Init", test_service_initialization()))
    results.append(("Refactored Services", test_refactored_services()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    all_passed = all(passed for _, passed in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
