# Agent Brief: QA-MONITORING-001

**Agent ID:** QA-MONITORING-001
**Agent Name:** Monitoring QA
**Type:** QA
**Phase:** 6 - DevOps
**Paired Dev Agent:** DEV-MONITORING-001

---

## Validation Checklist

- [ ] Structured logging works
- [ ] Logs appear in Cloud Logging
- [ ] Correlation IDs present
- [ ] PII redacted from logs
- [ ] Metrics collected correctly
- [ ] Dashboards load correctly
- [ ] Alerts trigger correctly
- [ ] Notifications delivered
- [ ] Log retention policies applied
- [ ] Cost monitoring accurate

---

## Test Cases

1. Verify log format (JSON)
2. Verify correlation ID propagation
3. Verify PII redaction
4. Check metric collection
5. View dashboard data
6. Trigger high error rate alert
7. Trigger latency alert
8. Verify Slack notification
9. Verify email notification
10. Check log retention
11. Query historical logs
12. Cost alert threshold

---

## Alert Tests

- Simulate high error rate
- Simulate high latency
- Simulate service down
- Verify alert fires
- Verify notification received
- Verify alert resolves

---

## Dashboard Tests

- All panels load data
- Time range selector works
- Filters work correctly
- Data is accurate

---

## Log Tests

- Logs searchable
- Stack traces captured
- Request/response logged
- Sensitive data masked

---

**Begin review.**
