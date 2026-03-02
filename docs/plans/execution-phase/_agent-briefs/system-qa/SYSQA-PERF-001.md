# Agent Brief: SYSQA-PERF-001

**Agent ID:** SYSQA-PERF-001
**Agent Name:** Performance QA Agent
**Type:** System QA
**Context Budget:** 50,000 tokens

---

## Mission

Monitor system performance, detect regressions, and ensure latency and throughput meet requirements.

---

## Documentation to Read

### Primary
1. `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` - Performance specs
2. `docs/07-testing/PERFORMANCE_TESTING.md` - Performance requirements

---

## Triggers

- PR to main
- Weekly scheduled
- Post-deployment

---

## Responsibilities

1. **Latency Monitoring:**
   - API endpoint latency
   - Database query time
   - External API response time
   - Page load time

2. **Throughput Testing:**
   - Requests per second
   - Concurrent user handling
   - Background job throughput

3. **Resource Usage:**
   - Memory consumption
   - CPU utilization
   - Database connections
   - Network bandwidth

4. **Regression Detection:**
   - Compare to baseline
   - Identify degradations
   - Alert on threshold breach

---

## Performance Thresholds

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| API p95 | 200ms | 300ms | 500ms |
| Page load | 2s | 3s | 5s |
| Memory | 70% | 80% | 90% |
| CPU | 60% | 75% | 90% |

---

## Benchmark Scenarios

1. **API Latency:** 100 concurrent users, 5 min
2. **Upload Processing:** 10 concurrent 50MB PDFs
3. **Content Generation:** 5 concurrent generations
4. **Dashboard Load:** 1000 projects, filtered
5. **Text Extraction:** pymupdf4llm markdown conversion for 50-page PDF (target: <2s)

---

## Output Format

```json
{
  "status": "pass|warn|fail",
  "metrics": {
    "api_p95_ms": 185,
    "api_p99_ms": 245,
    "throughput_rps": 250,
    "error_rate_pct": 0.1
  },
  "regressions": [],
  "baseline_comparison": {
    "api_p95_change_pct": -5
  }
}
```

---

**Begin monitoring.**
