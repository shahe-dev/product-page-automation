"""
Runtime validation script for QA-PROJECT-001.

Tests:
1. Import test - verify all modules load correctly
2. Reserved names check - ensure no conflicts
3. Async patterns check - verify async/await usage
"""

import sys
import ast
import os

sys.path.insert(0, "backend")

def test_imports():
    """Test that all project modules import successfully."""
    errors = []

    modules_to_test = [
        ("app.services.project_service", ["ProjectService"]),
        ("app.repositories.project_repository", ["ProjectRepository"]),
        ("app.api.routes.projects", ["router"]),
        ("app.models.schemas", ["ProjectCreate", "ProjectUpdate", "ProjectDetailSchema"]),
    ]

    for module_path, exports in modules_to_test:
        try:
            module = __import__(module_path, fromlist=exports)
            for export in exports:
                if not hasattr(module, export):
                    errors.append(f"FAIL: {module_path}.{export} not found")
        except ImportError as e:
            errors.append(f"FAIL: Cannot import {module_path} - {e}")
        except Exception as e:
            errors.append(f"FAIL: Error loading {module_path} - {e}")

    if errors:
        return "FAIL", errors
    return "PASS", ["All imports successful"]


def test_reserved_names():
    """Check for SQLAlchemy/Pydantic reserved name conflicts."""
    errors = []

    # Reserved names to check for
    sqlalchemy_reserved = {"metadata", "registry", "query", "c"}
    pydantic_reserved = {"model_config", "model_fields"}

    files_to_check = [
        ("backend/app/repositories/project_repository.py", sqlalchemy_reserved),
        ("backend/app/models/schemas.py", pydantic_reserved),
    ]

    for filepath, reserved in files_to_check:
        if not os.path.exists(filepath):
            errors.append(f"FAIL: File not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                # Check for field assignments
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id in reserved:
                                errors.append(
                                    f"FAIL: Reserved name '{target.id}' used in {filepath}"
                                )
        except Exception as e:
            errors.append(f"FAIL: Error parsing {filepath}: {e}")

    if errors:
        return "FAIL", errors
    return "PASS", ["No reserved name conflicts found"]


def test_async_patterns():
    """Check for improper sync operations in async functions."""
    errors = []

    files_to_check = [
        "backend/app/services/project_service.py",
        "backend/app/repositories/project_repository.py",
    ]

    for filepath in files_to_check:
        if not os.path.exists(filepath):
            errors.append(f"FAIL: File not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for blocking operations
        blocking_patterns = [
            ("time.sleep", "Should use asyncio.sleep() in async code"),
            ("open(", "Should use aiofiles for file operations in async code"),
        ]

        for pattern, message in blocking_patterns:
            if pattern in content:
                # Check if it's in an async function
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if pattern in line:
                        # Check if we're in an async function
                        in_async_func = False
                        for j in range(i, -1, -1):
                            if "async def" in lines[j]:
                                in_async_func = True
                                break
                            elif "def " in lines[j] and "async def" not in lines[j]:
                                break

                        if in_async_func:
                            errors.append(
                                f"FAIL: {filepath}:{i+1} - {message} (found '{pattern}')"
                            )

    if errors:
        return "FAIL", errors
    return "PASS", ["No blocking operations in async functions"]


def main():
    """Run all runtime validation tests."""
    print("=" * 70)
    print("QA-PROJECT-001 Runtime Validation")
    print("=" * 70)
    print()

    # Test imports
    print("1. Import Test")
    print("-" * 70)
    status, messages = test_imports()
    print(f"Status: {status}")
    for msg in messages:
        print(f"  {msg}")
    print()

    # Test reserved names
    print("2. Reserved Names Check")
    print("-" * 70)
    status2, messages2 = test_reserved_names()
    print(f"Status: {status2}")
    for msg in messages2:
        print(f"  {msg}")
    print()

    # Test async patterns
    print("3. Async Patterns Check")
    print("-" * 70)
    status3, messages3 = test_async_patterns()
    print(f"Status: {status3}")
    for msg in messages3:
        print(f"  {msg}")
    print()

    # Overall status
    print("=" * 70)
    overall = "PASS" if all(s == "PASS" for s in [status, status2, status3]) else "FAIL"
    print(f"Overall Runtime Validation: {overall}")
    print("=" * 70)

    return overall == "PASS"


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
