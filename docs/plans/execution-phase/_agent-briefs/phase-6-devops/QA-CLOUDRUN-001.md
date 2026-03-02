# Agent Brief: QA-CLOUDRUN-001

**Agent ID:** QA-CLOUDRUN-001
**Agent Name:** Cloud Run QA
**Type:** QA
**Phase:** 6 - DevOps
**Paired Dev Agent:** DEV-CLOUDRUN-001

---

## Validation Checklist

- [ ] Backend service deploys successfully
- [ ] Frontend service deploys successfully
- [ ] Auto-scaling works correctly
- [ ] Min instances maintained
- [ ] Max instances respected
- [ ] Secret Manager integration works
- [ ] VPC connector allows DB access
- [ ] Custom domain works
- [ ] SSL certificate valid
- [ ] Deploy script works

---

## Test Cases

1. Deploy backend to staging
2. Deploy frontend to staging
3. Verify health endpoint
4. Test auto-scale up
5. Test auto-scale down
6. Verify secrets loaded
7. Test DB connectivity
8. Custom domain resolution
9. SSL certificate valid
10. Canary deployment
11. Rollback deployment
12. Cold start time

---

## Performance Tests

- Cold start: <5 seconds
- Response time: <200ms p95
- Scale up time: <30 seconds
- Concurrent request handling

---

## Security Tests

- No public environment variables
- Secrets from Secret Manager only
- VPC connector secured
- IAM permissions minimal

---

## Cost Tests

- Min instances cost acceptable
- Scale-to-zero works (staging)
- No runaway scaling

---

**Begin review.**
