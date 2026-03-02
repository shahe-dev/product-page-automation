# Agent Brief: TEST-PERF-001

**Agent ID:** TEST-PERF-001
**Agent Name:** Performance Test Agent
**Type:** Testing
**Phase:** Testing
**Context Budget:** 50,000 tokens

---

## Mission

Implement performance tests and benchmarks to ensure system meets latency and throughput requirements.

---

## Documentation to Read

### Primary
1. `docs/07-testing/PERFORMANCE_TESTING.md` - Performance requirements

---

## Dependencies

**Upstream:** Phase 6 (deployed application)
**Downstream:** None

---

## Outputs

### `tests/performance/locustfile.py` - Load test scenarios
### `tests/performance/benchmarks/` - Benchmark tests

---

## Acceptance Criteria

1. **Load Testing (Locust):**
   - Simulate concurrent users
   - Ramp-up scenarios
   - Sustained load tests
   - Spike tests

2. **Performance Targets:**
   - API latency: <200ms p95
   - Page load: <3s
   - Upload processing: <60s for 50MB
   - Content generation: <30s

3. **Benchmark Tests:**
   - PDF extraction speed
   - Image processing throughput
   - Database query performance
   - API endpoint benchmarks

4. **Resource Monitoring:**
   - CPU usage under load
   - Memory usage patterns
   - Database connections
   - Network bandwidth

5. **Reporting:**
   - Latency percentiles
   - Throughput metrics
   - Error rates
   - Resource utilization

---

## Load Scenarios

```python
# locustfile.py
class ContentCreator(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/projects")

    @task(1)
    def upload_pdf(self):
        self.client.post("/api/upload", files=...)
```

---

## Performance Baselines

| Endpoint | Target P95 | Max RPS |
|----------|------------|---------|
| GET /projects | 200ms | 100 |
| POST /upload | 1000ms | 10 |
| GET /project/:id | 150ms | 200 |
| POST /content/generate | 5000ms | 5 |

---

**Begin execution.**
