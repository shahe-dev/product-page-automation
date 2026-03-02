"""
Runtime validation for API routes
Tests import resolution, async patterns, and type hints
"""

import sys
import os
import asyncio
from typing import List, Tuple

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# Test results
results = {
    "import_test": "FAIL",
    "app_startup": "FAIL",
    "reserved_names": "PASS",
    "async_patterns": "PASS",
    "type_hints": "PASS",
    "errors": []
}


def test_imports():
    """Test that all route modules can be imported."""
    print("\n=== Testing Imports ===")

    modules_to_test = [
        ("app.api.routes.upload", ["router"]),
        ("app.api.routes.content", ["router"]),
        ("app.api.routes.qa", ["router"]),
        ("app.api.routes.prompts", ["router"]),
        ("app.api.routes.templates", ["router"]),
        ("app.api.routes.workflow", ["router"]),
        ("app.api.routes.auth", ["router"]),
        ("app.api.routes.projects", ["router"]),
        ("app.api.routes.jobs", ["router"]),
        ("app.middleware.auth", ["get_current_user"]),
        ("app.main", ["app"]),
    ]

    failed = []

    for module_name, exports in modules_to_test:
        try:
            module = __import__(module_name, fromlist=exports)
            for export in exports:
                if not hasattr(module, export):
                    failed.append(f"{module_name}.{export} not found")
                    print(f"  FAIL: {module_name}.{export} - Not found")
                else:
                    print(f"  PASS: {module_name}.{export}")
        except Exception as e:
            failed.append(f"{module_name}: {str(e)}")
            print(f"  FAIL: {module_name} - {str(e)}")

    if not failed:
        results["import_test"] = "PASS"
    else:
        results["errors"].extend(failed)

    return len(failed) == 0


def test_app_startup():
    """Test that the FastAPI app can be instantiated."""
    print("\n=== Testing App Startup ===")

    try:
        from app.main import app

        # Check routes are registered
        routes = [route.path for route in app.routes]
        print(f"  Total routes registered: {len(routes)}")

        # Check for expected route prefixes
        required_prefixes = ["/api/auth", "/api/v1/projects", "/api/v1/jobs", "/api/v1/upload"]
        missing = []

        for prefix in required_prefixes:
            matching = [r for r in routes if r.startswith(prefix)]
            if matching:
                print(f"  PASS: Found routes with prefix {prefix} ({len(matching)} routes)")
            else:
                missing.append(prefix)
                print(f"  FAIL: No routes found with prefix {prefix}")

        if not missing:
            results["app_startup"] = "PASS"
        else:
            results["errors"].append(f"Missing route prefixes: {missing}")

        return len(missing) == 0

    except Exception as e:
        print(f"  FAIL: {str(e)}")
        results["errors"].append(f"App startup failed: {str(e)}")
        return False


def check_reserved_names():
    """Check for Pydantic reserved names in request/response models."""
    print("\n=== Checking Reserved Names ===")

    reserved = [
        "model_config", "model_fields", "model_computed_fields",
        "model_extra", "model_fields_set", "dict", "json", "copy",
        "parse_obj", "parse_raw", "schema", "schema_json",
        "construct", "from_orm", "validate"
    ]

    issues = []

    # This is a basic check - would need full AST parsing for complete validation
    files_to_check = [
        "backend/app/api/routes/upload.py",
        "backend/app/api/routes/content.py",
        "backend/app/api/routes/qa.py",
        "backend/app/api/routes/prompts.py",
        "backend/app/api/routes/templates.py",
        "backend/app/api/routes/workflow.py",
        "backend/app/api/routes/auth.py",
        "backend/app/api/routes/projects.py",
        "backend/app/api/routes/jobs.py",
    ]

    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for name in reserved:
                    # Simple check for field definitions
                    if f": {name} =" in content or f'"{name}":' in content:
                        issues.append(f"{filepath} may use reserved name: {name}")

    if issues:
        results["reserved_names"] = "WARN"
        results["errors"].extend(issues)
        for issue in issues:
            print(f"  WARN: {issue}")
    else:
        print("  PASS: No reserved names detected")

    return len(issues) == 0


def check_async_patterns():
    """Check for sync-blocking calls in async route handlers."""
    print("\n=== Checking Async Patterns ===")

    # Look for common blocking patterns
    blocking_patterns = [
        "time.sleep(",
        "requests.get(",
        "requests.post(",
        "open(",  # Should use aiofiles
    ]

    issues = []

    files_to_check = [
        "backend/app/api/routes/upload.py",
        "backend/app/api/routes/content.py",
        "backend/app/api/routes/qa.py",
        "backend/app/api/routes/prompts.py",
        "backend/app/api/routes/templates.py",
        "backend/app/api/routes/workflow.py",
    ]

    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    for pattern in blocking_patterns:
                        if pattern in line and not line.strip().startswith("#"):
                            issues.append(f"{filepath}:{i} - Potential blocking call: {pattern}")

    if issues:
        results["async_patterns"] = "WARN"
        results["errors"].extend(issues)
        for issue in issues:
            print(f"  WARN: {issue}")
    else:
        print("  PASS: No blocking patterns detected")

    return len(issues) == 0


def check_type_hints():
    """Check for proper type hints in route handlers."""
    print("\n=== Checking Type Hints ===")

    # Basic check for function definitions without type hints
    issues = []

    files_to_check = [
        "backend/app/api/routes/upload.py",
        "backend/app/api/routes/content.py",
        "backend/app/api/routes/qa.py",
        "backend/app/api/routes/prompts.py",
        "backend/app/api/routes/templates.py",
        "backend/app/api/routes/workflow.py",
    ]

    for filepath in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), filepath)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    # Check for async def without return type
                    if line.strip().startswith("async def ") and "->" not in line:
                        # Check if it's a decorator line continuation
                        if i > 1 and not lines[i-2].strip().startswith("@"):
                            issues.append(f"{filepath}:{i} - Missing return type annotation")

    if issues:
        results["type_hints"] = "WARN"
        results["errors"].extend(issues)
        for issue in issues[:5]:  # Limit output
            print(f"  WARN: {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    else:
        print("  PASS: Type hints look good")

    return len(issues) == 0


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("API ROUTES RUNTIME VALIDATION")
    print("=" * 60)

    # Run tests
    import_ok = test_imports()
    app_ok = test_app_startup()
    reserved_ok = check_reserved_names()
    async_ok = check_async_patterns()
    type_ok = check_type_hints()

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Import Test:       {results['import_test']}")
    print(f"App Startup:       {results['app_startup']}")
    print(f"Reserved Names:    {results['reserved_names']}")
    print(f"Async Patterns:    {results['async_patterns']}")
    print(f"Type Hints:        {results['type_hints']}")

    if results["errors"]:
        print(f"\nTotal Issues: {len(results['errors'])}")

    # Return exit code
    all_pass = all([
        results['import_test'] == 'PASS',
        results['app_startup'] == 'PASS',
    ])

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
