# E2E Test Scenarios

**Version:** 1.0
**Last Updated:** 2025-01-15
**Owner:** QA Team

---

## Overview

End-to-End (E2E) tests validate complete user journeys through the PDP Automation Platform, testing the entire system from the user interface through to the backend services and database. These tests ensure that all components work together seamlessly to deliver the expected user experience.

### What is an E2E Test?

An E2E test:
- Tests complete user workflows from start to finish
- Uses real browser (Playwright)
- Interacts with actual UI components
- Validates full stack integration (frontend + backend + database)
- Executes in 30 seconds to 2 minutes per test
- Represents 5% of our test pyramid (highest value, slowest execution)

### E2E Testing Goals

- **User Journey Validation:** Verify critical business workflows
- **Cross-Browser Compatibility:** Test on Chrome, Firefox, Safari
- **UI/UX Verification:** Ensure proper rendering and interactions
- **Real-World Scenarios:** Test as actual users would use the system
- **Regression Prevention:** Catch breaking changes before deployment

---

## Testing Framework Setup

### Playwright Installation

**Backend E2E Tests:**
```bash
pip install playwright pytest-playwright
playwright install
```

**Frontend E2E Tests:**
```bash
npm install -D @playwright/test
npx playwright install
```

### Playwright Configuration

**playwright.config.ts:**
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile browsers
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5174',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Python pytest Configuration

**conftest.py:**
```python
import pytest
from playwright.async_api import async_playwright

@pytest.fixture(scope="session")
async def browser():
    """Launch browser for E2E tests"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser):
    """Create new page for each test"""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await context.close()

@pytest.fixture
async def authenticated_page(page):
    """Create authenticated page with logged-in user"""
    # Navigate to login
    await page.goto("http://localhost:5174/login")

    # Mock OAuth flow (for testing)
    await page.evaluate("""
        localStorage.setItem('auth_token', 'test_token_123');
        localStorage.setItem('user', JSON.stringify({
            email: 'test@your-domain.com',
            name: 'Test User',
            role: 'user'
        }));
    """)

    await page.goto("http://localhost:5174/processing")
    yield page
```

---

## Critical User Journeys

### Journey 1: Content Creator - Upload and Process Brochure

**User Story:**
As a Content Creator, I want to upload a property brochure PDF, have it processed automatically, review the extracted content, and submit it for approval.

**Test Scenario:**

**tests/e2e/test_upload_flow.py:**
```python
import pytest
from playwright.async_api import Page, expect

@pytest.mark.e2e
async def test_content_creator_uploads_and_processes_brochure(authenticated_page: Page):
    """
    User Journey: Upload PDF → Process → Review Results → Submit for Approval

    Steps:
    1. Navigate to processing page
    2. Select website (OPR/DXB)
    3. Upload PDF file
    4. Wait for processing to complete
    5. Review extracted data
    6. Verify Google Sheet created
    7. Submit for approval
    """
    page = authenticated_page

    # Step 1: Navigate to processing page
    await page.goto("http://localhost:5174/processing")
    await expect(page.locator("h1")).to_contain_text("Content Processing")

    # Step 2: Select website
    await page.select_option("#website-select", "opr")

    # Step 3: Upload PDF file
    await page.set_input_files(
        'input[type="file"]',
        "tests/fixtures/sample_brochure.pdf"
    )

    # Step 4: Click Generate Content button
    await page.click('button:text("Generate Content")')

    # Step 5: Wait for upload confirmation
    await expect(page.locator(".upload-status")).to_contain_text(
        "Upload successful",
        timeout=10000
    )

    # Step 6: Wait for processing to complete (up to 2 minutes)
    await expect(page.locator(".processing-status")).to_contain_text(
        "Complete",
        timeout=120000
    )

    # Step 7: Verify progress indicators updated
    progress_items = page.locator(".progress-item")
    await expect(progress_items.nth(0)).to_have_class(/complete/)  # Extract Images
    await expect(progress_items.nth(1)).to_have_class(/complete/)  # Classify Images
    await expect(progress_items.nth(2)).to_have_class(/complete/)  # Generate Content
    await expect(progress_items.nth(3)).to_have_class(/complete/)  # Create Sheet

    # Step 8: Verify results section visible
    await expect(page.locator(".results-section")).to_be_visible()

    # Step 9: Verify Google Sheet link
    sheet_link = page.locator('a:text("View Google Sheet")')
    await expect(sheet_link).to_be_visible()
    await expect(sheet_link).to_have_attribute("href", /docs\.google\.com/)

    # Step 10: Verify download ZIP button
    await expect(page.locator('button:text("Download ZIP")')).to_be_visible()

    # Step 11: Navigate to projects page
    await page.click('nav a:text("Projects")')
    await page.wait_for_url("**/projects")

    # Step 12: Verify project appears in list
    project_row = page.locator(".project-row").first
    await expect(project_row).to_be_visible()

    # Step 13: Click on project to view details
    await project_row.click()

    # Step 14: Verify project details page
    await expect(page.locator("h1")).to_contain_text("Project Details")
    await expect(page.locator(".project-status")).to_contain_text("Draft")

    # Step 15: Submit for approval
    await page.click('button:text("Submit for Approval")')

    # Step 16: Verify confirmation dialog
    await expect(page.locator(".dialog")).to_be_visible()
    await page.click('button:text("Confirm")')

    # Step 17: Verify status updated
    await expect(page.locator(".project-status")).to_contain_text(
        "Pending Approval",
        timeout=5000
    )

    # Step 18: Verify success notification
    await expect(page.locator(".notification.success")).to_contain_text(
        "Submitted for approval"
    )
```

---

### Journey 2: Marketing Manager - Review and Approve Content

**User Story:**
As a Marketing Manager, I want to review submitted projects, provide feedback, request revisions if needed, or approve content for publication.

**Test Scenario:**

**tests/e2e/test_approval_flow.py:**
```python
import pytest
from playwright.async_api import Page, expect

@pytest.mark.e2e
async def test_manager_reviews_and_approves_content(manager_authenticated_page: Page):
    """
    User Journey: Review Pending Projects → Approve/Request Revision

    Steps:
    1. Navigate to approvals page
    2. View pending projects list
    3. Open project for review
    4. Review extracted content
    5. Approve project
    """
    page = manager_authenticated_page

    # Step 1: Navigate to approvals page
    await page.goto("http://localhost:5174/approvals")
    await expect(page.locator("h1")).to_contain_text("Pending Approvals")

    # Step 2: Verify pending projects list
    pending_projects = page.locator(".pending-project")
    await expect(pending_projects.first).to_be_visible()

    # Step 3: Click on first pending project
    await pending_projects.first.click()

    # Step 4: Verify project review page
    await expect(page.locator("h1")).to_contain_text("Review Project")
    await expect(page.locator(".project-status")).to_contain_text("Pending Approval")

    # Step 5: Review project details
    await expect(page.locator(".project-name")).to_be_visible()
    await expect(page.locator(".project-developer")).to_be_visible()
    await expect(page.locator(".project-location")).to_be_visible()

    # Step 6: Review extracted content tabs
    await page.click('button[role="tab"]:text("Overview")')
    await expect(page.locator(".overview-content")).to_be_visible()

    await page.click('button[role="tab"]:text("Amenities")')
    await expect(page.locator(".amenities-list")).to_be_visible()

    await page.click('button[role="tab"]:text("Images")')
    await expect(page.locator(".image-gallery")).to_be_visible()

    # Step 7: View Google Sheet
    await page.click('a:text("View Sheet")')
    # New tab opens - handle it
    async with page.context.expect_page() as new_page_info:
        pass
    sheet_page = await new_page_info.value
    await expect(sheet_page).to_have_url(/docs\.google\.com/)
    await sheet_page.close()

    # Step 8: Approve project
    await page.click('button:text("Approve")')

    # Step 9: Add approval comments
    await expect(page.locator(".approval-dialog")).to_be_visible()
    await page.fill('textarea[name="comments"]', "Looks great! Approved for publication.")

    # Step 10: Confirm approval
    await page.click('button:text("Confirm Approval")')

    # Step 11: Verify status updated
    await expect(page.locator(".project-status")).to_contain_text(
        "Approved",
        timeout=5000
    )

    # Step 12: Verify success notification
    await expect(page.locator(".notification.success")).to_contain_text(
        "Project approved"
    )

    # Step 13: Verify project removed from pending list
    await page.goto("http://localhost:5174/approvals")
    # Should not see the approved project anymore
    await expect(page.locator(".empty-state")).to_be_visible()


@pytest.mark.e2e
async def test_manager_requests_revision(manager_authenticated_page: Page):
    """
    User Journey: Review Project → Request Revision with Feedback

    Steps:
    1. Open pending project
    2. Identify issues
    3. Request revision with specific feedback
    4. Verify creator is notified
    """
    page = manager_authenticated_page

    # Navigate to project review
    await page.goto("http://localhost:5174/approvals")
    await page.locator(".pending-project").first.click()

    # Request revision
    await page.click('button:text("Request Revision")')

    # Fill revision form
    await expect(page.locator(".revision-dialog")).to_be_visible()

    # Select sections that need revision
    await page.check('input[type="checkbox"][value="amenities"]')
    await page.check('input[type="checkbox"][value="payment_plan"]')

    # Add detailed feedback
    await page.fill(
        'textarea[name="feedback"]',
        "Please update:\n1. Add missing gym facility\n2. Clarify payment terms"
    )

    # Submit revision request
    await page.click('button:text("Submit Revision Request")')

    # Verify status updated
    await expect(page.locator(".project-status")).to_contain_text(
        "Revision Requested",
        timeout=5000
    )

    # Verify feedback saved
    await expect(page.locator(".feedback-section")).to_contain_text("Add missing gym")
```

---

### Journey 3: Publisher - Download and Publish Content

**User Story:**
As a Publisher, I want to download approved content assets and mark projects as published after creating web pages.

**Test Scenario:**

**tests/e2e/test_publishing_flow.py:**
```python
import pytest
from playwright.async_api import Page, expect
import asyncio

@pytest.mark.e2e
async def test_publisher_downloads_and_publishes_content(
    publisher_authenticated_page: Page
):
    """
    User Journey: Download Assets → Create Page → Mark as Published

    Steps:
    1. Navigate to approved projects
    2. Filter for approved status
    3. Download assets ZIP
    4. Mark project as published with URL
    """
    page = publisher_authenticated_page

    # Step 1: Navigate to projects
    await page.goto("http://localhost:5174/projects")

    # Step 2: Filter for approved projects
    await page.select_option("#status-filter", "approved")
    await page.wait_for_timeout(1000)  # Wait for filter to apply

    # Step 3: Verify approved projects shown
    approved_projects = page.locator(".project-row[data-status='approved']")
    await expect(approved_projects.first).to_be_visible()

    # Step 4: Click on first approved project
    await approved_projects.first.click()

    # Step 5: Verify project details
    await expect(page.locator(".project-status")).to_contain_text("Approved")

    # Step 6: Download assets ZIP
    async with page.expect_download() as download_info:
        await page.click('button:text("Download ZIP")')
    download = await download_info.value

    # Verify download started
    assert download.suggested_filename.endswith('.zip')

    # Step 7: Click "Mark as Published"
    await page.click('button:text("Mark as Published")')

    # Step 8: Fill publication details
    await expect(page.locator(".publish-dialog")).to_be_visible()

    await page.fill('input[name="page_url"]', "https://opr.com/projects/test-project")
    await page.fill('input[name="published_date"]', "2025-01-15")

    # Step 9: Confirm publication
    await page.click('button:text("Confirm Publication")')

    # Step 10: Verify status updated
    await expect(page.locator(".project-status")).to_contain_text(
        "Published",
        timeout=5000
    )

    # Step 11: Verify publication details visible
    published_url = page.locator(".published-url")
    await expect(published_url).to_contain_text("https://opr.com")

    # Step 12: Verify published badge
    await expect(page.locator(".badge.published")).to_be_visible()
```

---

### Journey 4: Admin - User Management and Audit

**User Story:**
As an Admin, I want to manage users, view audit logs, and monitor system activity.

**Test Scenario:**

**tests/e2e/test_admin_flow.py:**
```python
import pytest
from playwright.async_api import Page, expect

@pytest.mark.e2e
async def test_admin_manages_users(admin_authenticated_page: Page):
    """
    User Journey: Manage Users → Update Roles → View Audit Log

    Steps:
    1. Navigate to admin panel
    2. View users list
    3. Update user role
    4. View audit log
    """
    page = admin_authenticated_page

    # Step 1: Navigate to admin panel
    await page.goto("http://localhost:5174/admin")
    await expect(page.locator("h1")).to_contain_text("Admin Panel")

    # Step 2: Navigate to users management
    await page.click('a:text("Users")')
    await expect(page.locator("h2")).to_contain_text("User Management")

    # Step 3: Verify users table
    users_table = page.locator(".users-table")
    await expect(users_table).to_be_visible()

    # Step 4: Search for specific user
    await page.fill('input[placeholder="Search users..."]', "test@your-domain.com")
    await page.wait_for_timeout(500)

    # Step 5: Click on user to edit
    user_row = page.locator('.user-row:has-text("test@your-domain.com")')
    await user_row.click('button:text("Edit")')

    # Step 6: Update user role
    await expect(page.locator(".edit-user-dialog")).to_be_visible()
    await page.select_option('select[name="role"]', "manager")

    # Step 7: Save changes
    await page.click('button:text("Save Changes")')

    # Step 8: Verify success notification
    await expect(page.locator(".notification.success")).to_contain_text(
        "User updated"
    )

    # Step 9: Verify role updated in table
    await expect(user_row.locator(".role-badge")).to_contain_text("Manager")

    # Step 10: Navigate to audit log
    await page.click('a:text("Audit Log")')
    await expect(page.locator("h2")).to_contain_text("Audit Log")

    # Step 11: Verify recent activity logged
    audit_entries = page.locator(".audit-entry")
    await expect(audit_entries.first).to_be_visible()

    # Step 12: Filter audit log by action
    await page.select_option("#action-filter", "user_role_updated")
    await page.wait_for_timeout(500)

    # Step 13: Verify filtered results
    await expect(audit_entries.first).to_contain_text("Role updated")

    # Step 14: Export audit log
    async with page.expect_download() as download_info:
        await page.click('button:text("Export CSV")')
    download = await download_info.value
    assert download.suggested_filename.endswith('.csv')
```

---

## Error Scenarios

### Test Error Handling

**tests/e2e/test_error_scenarios.py:**
```python
import pytest
from playwright.async_api import Page, expect

@pytest.mark.e2e
async def test_upload_invalid_file_shows_error(authenticated_page: Page):
    """Should show error when uploading non-PDF file"""
    page = authenticated_page

    await page.goto("http://localhost:5174/processing")

    # Try to upload non-PDF file
    await page.set_input_files('input[type="file"]', "tests/fixtures/image.jpg")

    # Verify error message
    await expect(page.locator(".error-message")).to_contain_text(
        "Please upload a PDF file"
    )

    # Verify upload button disabled
    await expect(page.locator('button:text("Generate Content")')).to_be_disabled()


@pytest.mark.e2e
async def test_network_error_shows_retry_option(authenticated_page: Page):
    """Should show retry option on network error"""
    page = authenticated_page

    # Simulate network failure
    await page.route("**/api/upload", lambda route: route.abort())

    await page.goto("http://localhost:5174/processing")
    await page.set_input_files('input[type="file"]', "tests/fixtures/sample.pdf")
    await page.click('button:text("Generate Content")')

    # Verify error message
    await expect(page.locator(".error-banner")).to_contain_text("Network error")

    # Verify retry button
    await expect(page.locator('button:text("Retry")')).to_be_visible()


@pytest.mark.e2e
async def test_unauthorized_access_redirects_to_login(page: Page):
    """Should redirect to login when accessing protected route"""
    # Try to access protected route without authentication
    await page.goto("http://localhost:5174/projects")

    # Should redirect to login
    await page.wait_for_url("**/login")
    await expect(page.locator("h1")).to_contain_text("Sign In")
```

---

## Accessibility Testing

**tests/e2e/test_accessibility.py:**
```python
import pytest
from playwright.async_api import Page

@pytest.mark.e2e
async def test_keyboard_navigation(authenticated_page: Page):
    """Should support keyboard navigation"""
    page = authenticated_page

    await page.goto("http://localhost:5174/processing")

    # Tab through form elements
    await page.keyboard.press("Tab")  # Website select
    await page.keyboard.press("Tab")  # File input
    await page.keyboard.press("Tab")  # Generate button

    # Verify focus on button
    focused_element = await page.evaluate("document.activeElement.textContent")
    assert "Generate" in focused_element


@pytest.mark.e2e
async def test_screen_reader_labels(authenticated_page: Page):
    """Should have proper ARIA labels"""
    page = authenticated_page

    await page.goto("http://localhost:5174/processing")

    # Verify ARIA labels
    file_input = page.locator('input[type="file"]')
    await expect(file_input).to_have_attribute("aria-label", "Upload PDF file")

    website_select = page.locator("#website-select")
    await expect(website_select).to_have_attribute("aria-label", "Select website")
```

---

## Cross-Browser Testing

### Browser-Specific Tests

**TypeScript/Playwright:**
```typescript
// e2e/cross-browser.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Cross-browser compatibility', () => {
  test('should work on Chrome', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Chrome-specific test');

    await page.goto('/processing');
    await expect(page.locator('h1')).toContainText('Content Processing');
  });

  test('should work on Firefox', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Firefox-specific test');

    await page.goto('/processing');
    await expect(page.locator('h1')).toContainText('Content Processing');
  });

  test('should work on Safari', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Safari-specific test');

    await page.goto('/processing');
    await expect(page.locator('h1')).toContainText('Content Processing');
  });
});
```

---

## Mobile Testing

**e2e/mobile.spec.ts:**
```typescript
import { test, expect, devices } from '@playwright/test';

test.use(devices['iPhone 12']);

test.describe('Mobile user experience', () => {
  test('should display mobile navigation', async ({ page }) => {
    await page.goto('/');

    // Verify hamburger menu visible
    const menuButton = page.locator('button[aria-label="Menu"]');
    await expect(menuButton).toBeVisible();

    // Open menu
    await menuButton.click();

    // Verify navigation links
    await expect(page.locator('nav a:text("Projects")')).toBeVisible();
  });

  test('should support touch gestures', async ({ page }) => {
    await page.goto('/projects');

    // Swipe to refresh (if implemented)
    await page.touchscreen.tap(100, 100);
    await page.touchscreen.tap(100, 300);
  });
});
```

---

## Performance Testing in E2E

**tests/e2e/test_performance.py:**
```python
import pytest
from playwright.async_api import Page

@pytest.mark.e2e
async def test_page_load_performance(page: Page):
    """Should load pages within performance budget"""

    # Start measuring
    await page.goto("http://localhost:5174/projects")

    # Get performance metrics
    metrics = await page.evaluate("""() => {
        const perf = performance.getEntriesByType('navigation')[0];
        return {
            domContentLoaded: perf.domContentLoadedEventEnd - perf.fetchStart,
            loadComplete: perf.loadEventEnd - perf.fetchStart
        };
    }""")

    # Assert performance budgets
    assert metrics['domContentLoaded'] < 2000  # < 2 seconds
    assert metrics['loadComplete'] < 4000  # < 4 seconds
```

---

## Running E2E Tests

### Basic Commands

```bash
# Run all E2E tests (Python)
pytest tests/e2e -v -m e2e

# Run all E2E tests (Playwright/TypeScript)
npx playwright test

# Run specific test file
npx playwright test e2e/upload-flow.spec.ts

# Run in headed mode (show browser)
npx playwright test --headed

# Run in debug mode
npx playwright test --debug

# Run on specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Run in UI mode (interactive)
npx playwright test --ui
```

### CI/CD Configuration

**GitHub Actions:**
```yaml
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: npm ci

    - name: Install Playwright browsers
      run: npx playwright install --with-deps

    - name: Start backend
      run: |
        cd backend
        pip install -r requirements.txt
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 10

    - name: Start frontend
      run: |
        npm run dev &
        sleep 10

    - name: Run E2E tests
      run: npx playwright test

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: playwright-report/
```

---

## Best Practices

### Do's

1. **Test Critical Paths Only**
   - Focus on high-value user journeys
   - Don't test every UI variation

2. **Use Page Object Model**
   ```typescript
   class LoginPage {
     constructor(private page: Page) {}

     async login(email: string, password: string) {
       await this.page.fill('#email', email);
       await this.page.fill('#password', password);
       await this.page.click('button:text("Sign in")');
     }
   }
   ```

3. **Wait for Elements Properly**
   ```typescript
   // Good - wait for element
   await expect(page.locator('.result')).toBeVisible();

   // Bad - arbitrary timeout
   await page.waitForTimeout(5000);
   ```

### Don'ts

1. **Don't Test Unit-Level Logic** in E2E tests
2. **Don't Make Tests Brittle** with specific selectors
3. **Don't Ignore Failures** - fix or remove flaky tests

---

## Debugging Tips

### Screenshot on Failure

```python
@pytest.fixture
async def page_with_screenshots(page):
    """Capture screenshot on test failure"""
    yield page

    # After test
    if hasattr(pytest, 'current_test_failed') and pytest.current_test_failed:
        await page.screenshot(path=f"screenshot_{test_name}.png")
```

### Video Recording

```typescript
// playwright.config.ts
use: {
  video: 'retain-on-failure',
  trace: 'on-first-retry',
}
```

---

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Python](https://playwright.dev/python/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)

**Next:** Review `PERFORMANCE_TESTING.md` for load testing strategies.
