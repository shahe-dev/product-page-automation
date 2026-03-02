"""
QA-JOB-001 Import Validation Script
Tests that all job-related modules import successfully without errors.
"""

import sys
sys.path.insert(0, "backend")

def test_job_imports():
    errors = []
    successes = []

    modules_to_test = [
        ("app.services.job_manager", ["JobManager"]),
        ("app.repositories.job_repository", ["JobRepository"]),
        ("app.background.task_queue", ["TaskQueue"]),
        ("app.api.routes.jobs", ["router"]),
    ]

    for module_path, exports in modules_to_test:
        try:
            module = __import__(module_path, fromlist=exports)
            for export in exports:
                if not hasattr(module, export):
                    errors.append(f"FAIL: {module_path}.{export} not found")
                else:
                    successes.append(f"PASS: {module_path}.{export} imported successfully")
        except ImportError as e:
            errors.append(f"FAIL: Cannot import {module_path} - {e}")
        except Exception as e:
            errors.append(f"FAIL: Error loading {module_path} - {e}")

    return {
        "passed": len(errors) == 0,
        "successes": successes,
        "errors": errors if errors else []
    }

if __name__ == "__main__":
    result = test_job_imports()

    print("=" * 70)
    print("QA-JOB-001 Import Validation Results")
    print("=" * 70)

    for success in result["successes"]:
        print(success)

    if result["errors"]:
        print("\nERRORS:")
        for error in result["errors"]:
            print(error)

    print("\n" + "=" * 70)
    print(f"Import Test: {'PASS' if result['passed'] else 'FAIL'}")
    print("=" * 70)

    sys.exit(0 if result["passed"] else 1)
