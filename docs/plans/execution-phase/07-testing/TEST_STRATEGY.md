# Test Strategy

**Version:** 1.0
**Last Updated:** 2025-01-15
**Owner:** QA Team

---

## Overview

This document defines the comprehensive testing strategy for the PDP Automation Platform, covering all aspects of quality assurance from unit tests to performance testing. Our strategy ensures reliability, maintainability, and confidence in system behavior across all components.

### Testing Philosophy

- **Shift-Left Approach:** Catch defects early in the development cycle
- **Test Pyramid:** Focus on fast, isolated unit tests with strategic integration and E2E tests
- **Automation First:** Automate all repeatable tests to enable CI/CD
- **Coverage-Driven:** Maintain high code coverage with meaningful tests
- **Performance-Aware:** Monitor and test performance continuously

---

## Testing Stack

### Backend Testing

**Core Framework:**
- **pytest 8.x** - Primary testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking and patching

**Integration Testing:**
- **httpx** - Async HTTP client for API tests
- **faker** - Test data generation
- **factory-boy** - Model factories

**Database Testing:**
- **pytest-postgresql** - Test database fixtures
- **SQLAlchemy** - ORM testing utilities

### Frontend Testing

**Component Testing:**
- **Vitest** - Fast unit test runner
- **React Testing Library** - Component testing utilities
- **@testing-library/user-event** - User interaction simulation

**E2E Testing:**
- **Playwright** - Cross-browser E2E tests
- **MSW (Mock Service Worker)** - API mocking

### Performance Testing

- **Locust** - Load and stress testing
- **Cloud Monitoring** - Production performance metrics

### Security Testing

- **OWASP ZAP** - Security vulnerability scanning
- **Safety** - Python dependency vulnerability checking
- **Snyk** - Comprehensive dependency scanning

---

## Test Pyramid

Our testing strategy follows the test pyramid approach to optimize test execution speed and maintenance:

```
        E2E (5%)
      ┌─────────┐
     Integration (15%)
    ┌───────────────┐
   Unit Tests (80%)
  ┌─────────────────────┐
```

### Distribution Rationale

**Unit Tests (80%):**
- Fast execution (< 100ms per test)
- Test individual functions and classes in isolation
- Mock external dependencies
- High code coverage with minimal maintenance

**Integration Tests (15%):**
- Medium execution time (< 5s per test)
- Test API endpoints and service interactions
- Use test database and mock external APIs
- Verify component integration

**E2E Tests (5%):**
- Slower execution (30s - 2min per test)
- Test critical user journeys end-to-end
- Use real browser and full stack
- Validate business workflows

---

## Coverage Targets

### Code Coverage Requirements

| Component | Minimum Coverage | Target Coverage | Critical Paths |
|-----------|-----------------|-----------------|----------------|
| **Services** | 85% | 90%+ | 100% |
| **API Routes** | 75% | 80%+ | 95% |
| **Models** | 90% | 95%+ | 100% |
| **Utils** | 80% | 85%+ | 95% |
| **Frontend Components** | 65% | 70%+ | 90% |

### Coverage Enforcement

```python
# pytest.ini
[pytest]
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
```

### Critical Path Definition

Critical paths must have 100% coverage:
- Authentication and authorization
- Payment processing (if applicable)
- Data persistence and retrieval
- External API integrations (Anthropic, Google)
- File upload and processing

---

## Testing Phases

### 1. Unit Tests (Every Commit)

**When:** On every git push
**Duration:** < 2 minutes
**Scope:** All unit tests

```bash
pytest tests/unit -v --cov=app --cov-report=term
```

**Pass Criteria:**
- All tests pass
- Coverage >= 85%
- No new linting errors

### 2. Integration Tests (PR Creation)

**When:** On pull request creation
**Duration:** < 10 minutes
**Scope:** Unit + Integration tests

```bash
pytest tests/unit tests/integration -v --cov=app
```

**Pass Criteria:**
- All unit and integration tests pass
- Coverage >= 80% for new code
- API contract tests pass

### 3. E2E Tests (Pre-Merge)

**When:** Before merging to main
**Duration:** < 30 minutes
**Scope:** Full test suite including E2E

```bash
pytest tests/ -v -m e2e
npx playwright test
```

**Pass Criteria:**
- All critical user journeys pass
- No browser console errors
- Accessibility tests pass

### 4. Performance Tests (Weekly on Staging)

**When:** Weekly scheduled run
**Duration:** 30 minutes - 2 hours
**Scope:** Load and stress tests

```bash
locust -f tests/performance/locustfile.py --host https://staging.pdp.your-domain.com
```

**Pass Criteria:**
- P95 response times meet SLAs
- No errors under expected load
- Resource utilization within limits

### 5. Security Tests (Monthly)

**When:** First Monday of each month
**Duration:** 2-4 hours
**Scope:** Security scans and penetration tests

```bash
safety check
zap-baseline.py -t https://staging.pdp.your-domain.com
```

**Pass Criteria:**
- No high-severity vulnerabilities
- All dependencies up-to-date
- OWASP Top 10 compliance

---

## Test Organization

### Directory Structure

```
backend/
├── tests/
│   ├── unit/                   # Unit tests (80%)
│   │   ├── services/
│   │   │   ├── test_pdf_processor.py
│   │   │   ├── test_image_classifier.py
│   │   │   ├── test_content_generator.py
│   │   │   └── test_job_manager.py
│   │   ├── api/
│   │   │   ├── test_upload_routes.py
│   │   │   ├── test_project_routes.py
│   │   │   └── test_qa_routes.py
│   │   ├── models/
│   │   │   ├── test_project_model.py
│   │   │   └── test_user_model.py
│   │   └── utils/
│   │       ├── test_validators.py
│   │       └── test_helpers.py
│   ├── integration/            # Integration tests (15%)
│   │   ├── test_api_upload.py
│   │   ├── test_api_projects.py
│   │   ├── test_api_qa.py
│   │   └── test_job_flow.py
│   ├── e2e/                    # E2E tests (5%)
│   │   ├── test_upload_flow.py
│   │   ├── test_approval_flow.py
│   │   └── test_publishing_flow.py
│   ├── performance/            # Performance tests
│   │   └── locustfile.py
│   ├── fixtures/               # Test data
│   │   ├── sample.pdf
│   │   ├── sample_encrypted.pdf
│   │   └── test_data.json
│   └── conftest.py             # Shared fixtures
│
frontend/
├── src/
│   └── __tests__/              # Component tests
│       ├── components/
│       ├── pages/
│       └── utils/
└── e2e/                        # Playwright E2E tests
    ├── upload.spec.ts
    ├── projects.spec.ts
    └── approval.spec.ts
```

---

## Naming Conventions

### Test Function Names

Follow the pattern: `test_<function>_<scenario>_<expected_result>`

```python
# Good examples
def test_extract_images_from_valid_pdf_returns_image_list():
    pass

def test_extract_images_from_encrypted_pdf_raises_value_error():
    pass

def test_classify_image_with_interior_returns_interior_category():
    pass

def test_create_project_with_valid_data_stores_in_database():
    pass

# Bad examples
def test_extract_images():  # Too vague
    pass

def test_1():  # Not descriptive
    pass

def test_pdf_processor_works():  # Unclear expectation
    pass
```

### Test File Names

- Prefix with `test_` for pytest discovery
- Match the module being tested
- Group related tests in subdirectories

```python
# Backend
app/services/pdf_processor.py    → tests/test_pdf_processor.py
app/api/routes/upload.py         → tests/unit/api/test_upload_routes.py

# Frontend
src/components/UploadForm.tsx    → src/__tests__/components/UploadForm.test.tsx
src/utils/validators.ts          → src/__tests__/utils/validators.test.ts
```

---

## Test Data Management

### Fixtures and Factories

```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_pdf():
    """Provide sample PDF for testing"""
    return Path(__file__).parent / "fixtures" / "sample.pdf"

@pytest.fixture
def project_factory():
    """Factory for creating test projects"""
    def _create_project(**kwargs):
        defaults = {
            "name": "Test Project",
            "developer": "Test Developer",
            "website": "opr",
            "status": "draft"
        }
        return Project(**{**defaults, **kwargs})
    return _create_project
```

### Test Data Principles

1. **Isolation:** Each test creates its own data
2. **Cleanup:** Remove test data after test completion
3. **Realism:** Use realistic data that mirrors production
4. **Anonymization:** Never use real user data in tests

---

## Mocking Strategy

### External Services to Mock

**Always Mock in Unit Tests:**
- Anthropic API calls
- Google Drive/Sheets API
- Cloud Storage operations
- Email notifications
- Third-party webhooks

**Use Real Services in Integration Tests:**
- Test database
- Local file system
- Application APIs

**Mock Example:**

```python
@pytest.mark.asyncio
async def test_classify_image_calls_anthropic_api(mocker):
    # Mock Anthropic client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="interior")]
    mock_client.messages.create.return_value = mock_response

    mocker.patch(
        'app.services.anthropic_service.AsyncAnthropic',
        return_value=mock_client
    )

    service = AnthropicService()
    result = await service.classify_image(b"image_bytes")

    assert result == "interior"
    mock_client.messages.create.assert_called_once()
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration -v

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: npx playwright install
      - name: Run E2E tests
        run: npx playwright test
```

---

## Test Environments

### Local Development

```bash
# Backend
export ENVIRONMENT=test
export DATABASE_URL=postgresql://test:test@localhost/pdp_test
pytest tests/

# Frontend
npm test
```

### CI/CD Pipeline

- Isolated test database per build
- Mock external services
- Parallel test execution
- Artifact storage for failed tests

### Staging Environment

- Weekly performance tests
- Monthly security scans
- Pre-production validation

---

## Quality Gates

### Pull Request Checklist

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage >= 85%
- [ ] No new linting errors
- [ ] No security vulnerabilities
- [ ] API documentation updated

### Release Checklist

- [ ] Full test suite passes
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Security scan clean
- [ ] Changelog updated
- [ ] Migration tests pass

---

## Monitoring and Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Test Metrics

Track weekly:
- Test count by type
- Test execution time
- Test failure rate
- Code coverage percentage
- Time to fix failing tests

### Dashboard Integration

- Codecov for coverage tracking
- GitHub Actions for CI status
- Slack notifications for failures

---

## Best Practices

### Do's

- Write tests before or during feature development
- Test both happy path and error cases
- Use descriptive test names
- Keep tests independent and isolated
- Mock external dependencies
- Clean up test data after execution
- Aim for fast test execution

### Don'ts

- Don't test external libraries (trust they work)
- Don't write tests that depend on execution order
- Don't use production data in tests
- Don't skip flaky tests (fix or remove them)
- Don't test implementation details
- Don't ignore test failures

---

## Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Locust Documentation](https://docs.locust.io/)

### Internal Resources
- `UNIT_TEST_PATTERNS.md` - Unit testing guide
- `INTEGRATION_TESTS.md` - Integration testing guide
- `E2E_TEST_SCENARIOS.md` - E2E testing guide
- `PERFORMANCE_TESTING.md` - Performance testing guide

---

## Appendix: Test Commands Reference

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_pdf_processor.py -v

# Run tests matching pattern
pytest tests/ -k "pdf" -v

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run tests in parallel
pytest tests/ -n auto

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v

# Run only E2E tests
pytest tests/e2e -v -m e2e

# Run with verbose output
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Run last failed tests
pytest tests/ --lf

# Frontend tests
npm test                    # Run all tests
npm test -- --coverage      # With coverage
npm test -- --watch         # Watch mode

# E2E tests
npx playwright test         # All E2E tests
npx playwright test --ui    # Interactive mode
npx playwright test --debug # Debug mode
```

---

**Next Steps:** Review `UNIT_TEST_PATTERNS.md` for detailed unit testing patterns and examples.
