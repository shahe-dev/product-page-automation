# Agent Brief: TEST-E2E-001

**Agent ID:** TEST-E2E-001
**Agent Name:** E2E Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 55,000 tokens

---

## Mission

Implement end-to-end tests covering critical user journeys using Playwright against staging environment.

---

## Documentation to Read

### Primary
1. `docs/07-testing/E2E_TEST_SCENARIOS.md` - E2E scenarios
2. `docs/08-user-guides/CONTENT_CREATOR_GUIDE.md` - User workflows
3. `docs/08-user-guides/MARKETING_MANAGER_GUIDE.md` - Review workflows

---

## Dependencies

**Upstream:** Phase 6 (deployed application)
**Downstream:** None (final testing phase)

---

## Outputs

### `tests/e2e/scenarios/` - E2E test scenarios
### `playwright.config.ts` - Playwright configuration

---

## Acceptance Criteria

1. **Critical User Journeys:**
   - Complete upload-to-publish flow
   - Content creator workflow
   - Marketing manager review
   - Publisher workflow
   - Admin prompt management

2. **Test Scenarios:**
   - Login and navigation
   - PDF upload and processing
   - Content review and approval
   - Workflow state transitions
   - Export and download

3. **Test Configuration:**
   - Multiple browsers (Chrome, Firefox)
   - Mobile viewport
   - Network throttling
   - Screenshot on failure
   - Video recording

4. **Data Management:**
   - Test user accounts
   - Seed data before tests
   - Cleanup after tests
   - Isolated test runs

5. **CI/CD Integration:**
   - Run on staging deploy
   - Parallel execution
   - Retry on flaky tests
   - Report generation

6. **Accessibility (WCAG 2.1 AA) -- axe-core:**
   - Install `@axe-core/playwright` as dev dependency
   - Run axe-core checks on every page after navigation settles
   - Assert zero critical or serious axe violations (WCAG 2.1 AA ruleset)
   - Generate HTML accessibility report per test run
   - Cover all 10 application pages (login, dashboard, upload, project detail, QA, prompts, workflow, and 3 stub pages at minimum)
   - Validate color contrast, ARIA attributes, keyboard navigability, and landmark regions

---

## Test Scenarios

```
tests/e2e/scenarios/
├── content-creator-journey.spec.ts
├── marketing-manager-journey.spec.ts
├── publisher-journey.spec.ts
├── admin-journey.spec.ts
├── error-recovery.spec.ts
├── accessibility-audit.spec.ts
└── global-setup.ts
```

---

## Key User Journeys

1. **Content Creator:**
   Login → Upload PDF → Monitor Processing → Review Images → View Content

2. **Marketing Manager:**
   Login → Review Queue → QA Review → Approve/Reject → Add Comments

3. **Publisher:**
   Login → Ready to Publish → Export Sheet → Mark Published

4. **Admin:**
   Login → Prompt Management → Edit Prompt → Test Prompt → Deploy

---

**Begin execution.**
