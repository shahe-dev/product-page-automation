# Agent Brief: DEV-CICD-001

**Agent ID:** DEV-CICD-001
**Agent Name:** CI/CD Agent
**Type:** Development
**Phase:** 6 - DevOps
**Context Budget:** 55,000 tokens

---

## Mission

Implement CI/CD pipelines using Cloud Build and GitHub Actions for testing, building, and deploying.

---

## Documentation to Read

### Primary
1. `docs/06-devops/CICD_PIPELINE.md` - Pipeline design

### Secondary
1. `docs/07-testing/TEST_STRATEGY.md` - Test requirements

---

## Dependencies

**Upstream:** DEV-DOCKER-001
**Downstream:** DEV-CLOUDRUN-001

---

## Outputs

### `cloudbuild.yaml`
### `.github/workflows/ci.yml`
### `.github/workflows/deploy.yml`

---

## Acceptance Criteria

1. **CI Pipeline (GitHub Actions):**
   - Trigger on PR and push to main
   - Backend tests (pytest)
   - Frontend tests (vitest)
   - Linting (ESLint, Ruff)
   - Type checking (TypeScript, mypy)
   - Security scanning
   - Build verification

2. **Cloud Build Pipeline:**
   - Build Docker images
   - Push to Artifact Registry
   - Deploy to Cloud Run
   - Environment-specific configs

3. **Deploy Pipeline:**
   - Staging auto-deploy from develop
   - Production manual approval from main
   - Rollback capability
   - Health check verification

4. **Quality Gates:**
   - Tests must pass
   - Coverage threshold (80%)
   - No critical security issues
   - Lint checks pass

5. **Notifications:**
   - Slack notification on failure
   - Email on deployment
   - PR status checks

---

## Pipeline Flow

```
PR Created → CI Pipeline
├── Lint
├── Type Check
├── Unit Tests
├── Integration Tests
├── Security Scan
└── Build Verify

Merge to main → Deploy Pipeline
├── Build Images
├── Push to Registry
├── Deploy to Staging
├── Run E2E Tests
├── Manual Approval
└── Deploy to Production
```

---

## QA Pair: QA-CICD-001

---

**Begin execution.**
