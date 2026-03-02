# Agent Brief: QA-CICD-001

**Agent ID:** QA-CICD-001
**Agent Name:** CI/CD QA
**Type:** QA
**Phase:** 6 - DevOps
**Paired Dev Agent:** DEV-CICD-001

---

## Validation Checklist

- [ ] CI triggers on PR
- [ ] CI triggers on push to main
- [ ] All test steps run
- [ ] Lint checks enforced
- [ ] Type checks enforced
- [ ] Security scan runs
- [ ] Build succeeds
- [ ] Cloud Build deploys correctly
- [ ] Staging auto-deploys
- [ ] Production requires approval

---

## Test Cases

1. Open PR triggers CI
2. CI fails on test failure
3. CI fails on lint error
4. CI fails on type error
5. Security scan detects issues
6. Merge triggers deploy
7. Staging deployment succeeds
8. E2E tests run on staging
9. Production approval workflow
10. Rollback on failure
11. Notifications sent
12. PR status checks update

---

## Pipeline Timing Tests

- CI completes in <10 minutes
- Deploy completes in <5 minutes
- Rollback completes in <2 minutes

---

## Security Tests

- Secrets not exposed in logs
- Service account minimal permissions
- Artifact Registry secure
- No public access to pipelines

---

## Failure Recovery Tests

- Retry on transient failure
- Manual retry available
- Rollback works correctly
- Alerts sent on failure

---

**Begin review.**
