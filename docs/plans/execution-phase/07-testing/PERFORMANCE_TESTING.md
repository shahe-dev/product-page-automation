# Performance Testing

**Version:** 1.0
**Last Updated:** 2025-01-15
**Owner:** QA Team

---

## Overview

Performance testing ensures the PDP Automation Platform can handle expected load, maintains acceptable response times, and scales efficiently. This document covers load testing, stress testing, performance monitoring, and optimization strategies.

### Performance Testing Goals

- **Validate Performance Requirements:** Ensure system meets SLAs
- **Identify Bottlenecks:** Find performance issues before production
- **Establish Baselines:** Measure and track performance over time
- **Test Scalability:** Verify system handles growth
- **Prevent Regressions:** Catch performance degradation early

### Performance Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Upload Response Time** | < 2s (p95) | < 5s (p99) |
| **List Projects** | < 500ms (p95) | < 1s (p99) |
| **Project Detail** | < 300ms (p95) | < 800ms (p99) |
| **PDF Processing** | < 5 min (avg) | < 10 min (p95) |
| **Concurrent Users** | 100 users | 200 users (peak) |
| **Error Rate** | < 0.1% | < 1% |
| **CPU Usage** | < 70% | < 90% |
| **Memory Usage** | < 80% | < 95% |

---

## Load Testing with Locust

### Locust Installation

```bash
pip install locust
```

### Basic Locust Configuration

**tests/performance/locustfile.py:**
```python
from locust import HttpUser, task, between, events
import random
import json

class PDPAutomationUser(HttpUser):
    """
    Simulates a user interacting with the PDP Automation Platform.

    This user performs typical operations:
    - List projects
    - View project details
    - Upload PDFs
    - Check job status
    """

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    # Store authentication token
    token = None

    def on_start(self):
        """
        Called once when a new user starts.
        Authenticates and stores token.
        """
        # Login and get token
        response = self.client.post("/api/auth/google", json={
            "token": "test_token_for_load_testing"
        })

        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            print(f"Authentication failed: {response.status_code}")

    @task(10)
    def list_projects(self):
        """
        List projects - highest weight (10).
        Most common operation in the system.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get(
            "/api/projects?page=1&limit=20",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(5)
    def get_project_detail(self):
        """
        View project details - medium weight (5).
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        # Simulate viewing a random project
        project_id = random.choice([
            "proj-123", "proj-456", "proj-789"
        ])

        with self.client.get(
            f"/api/projects/{project_id}",
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Expected for non-existent projects
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(3)
    def search_projects(self):
        """
        Search projects - medium weight (3).
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        search_terms = ["Dubai", "Marina", "Downtown", "Palm"]
        term = random.choice(search_terms)

        self.client.get(
            f"/api/projects?search={term}",
            headers=headers,
            name="/api/projects?search=[term]"
        )

    @task(1)
    def upload_pdf(self):
        """
        Upload PDF - lowest weight (1).
        Most resource-intensive operation.
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        # Read sample PDF
        with open("tests/fixtures/sample.pdf", "rb") as f:
            files = {
                "file": ("sample.pdf", f, "application/pdf")
            }
            data = {
                "website": random.choice(["opr", "dxb"]),
                "template_id": "template1"
            }

            with self.client.post(
                "/api/upload",
                files=files,
                data=data,
                headers=headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    job_id = response.json().get("job_id")
                    response.success()
                    # Track job for status checks
                    self.track_job(job_id)
                else:
                    response.failure(f"Upload failed: {response.status_code}")

    @task(2)
    def check_job_status(self):
        """
        Check job status - low weight (2).
        """
        headers = {"Authorization": f"Bearer {self.token}"}

        # Simulate checking random job
        job_id = f"job-{random.randint(1000, 9999)}"

        self.client.get(
            f"/api/jobs/{job_id}",
            headers=headers,
            name="/api/jobs/[id]"
        )

    def track_job(self, job_id: str):
        """Helper to track uploaded job"""
        # Could store in instance variable for polling
        pass


class ManagerUser(HttpUser):
    """
    Simulates a manager user with approval tasks.
    """
    wait_time = between(2, 5)
    token = None

    def on_start(self):
        """Authenticate as manager"""
        response = self.client.post("/api/auth/google", json={
            "token": "manager_test_token"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(5)
    def list_pending_approvals(self):
        """List projects pending approval"""
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get(
            "/api/projects?status=pending_approval",
            headers=headers
        )

    @task(2)
    def approve_project(self):
        """Approve a project"""
        headers = {"Authorization": f"Bearer {self.token}"}

        project_id = f"proj-{random.randint(100, 999)}"

        self.client.post(
            f"/api/projects/{project_id}/approve",
            headers=headers,
            json={"comments": "Approved via load test"},
            name="/api/projects/[id]/approve"
        )

    @task(1)
    def request_revision(self):
        """Request revision"""
        headers = {"Authorization": f"Bearer {self.token}"}

        project_id = f"proj-{random.randint(100, 999)}"

        self.client.post(
            f"/api/projects/{project_id}/request-revision",
            headers=headers,
            json={
                "feedback": "Please update amenities",
                "sections": ["amenities"]
            },
            name="/api/projects/[id]/request-revision"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("Load test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
```

---

## Advanced Load Testing Scenarios

### Spike Testing

**tests/performance/spike_test.py:**
```python
from locust import HttpUser, task, between, LoadTestShape

class SpikeLoadShape(LoadTestShape):
    """
    Spike test: Sudden increase in load to test system resilience.

    Timeline:
    - 0-2 min: 10 users (baseline)
    - 2-4 min: 200 users (spike)
    - 4-6 min: 10 users (recovery)
    """

    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 1},   # Baseline
        {"duration": 240, "users": 200, "spawn_rate": 50},  # Spike
        {"duration": 360, "users": 10, "spawn_rate": 10},   # Recovery
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None  # End test


class UserForSpikeTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def list_projects(self):
        self.client.get("/api/projects")
```

### Stress Testing

**tests/performance/stress_test.py:**
```python
from locust import HttpUser, task, LoadTestShape

class StressLoadShape(LoadTestShape):
    """
    Stress test: Gradually increase load until system breaks.

    Increases users by 20 every minute until failure.
    """

    def tick(self):
        run_time = self.get_run_time()

        # Increase by 20 users per minute
        users = int(run_time / 60) * 20 + 10

        # Cap at 500 users
        if users > 500:
            return None

        return (users, 5)
```

### Soak Testing (Endurance)

**tests/performance/soak_test.py:**
```python
from locust import HttpUser, task, constant

class SoakTestUser(HttpUser):
    """
    Soak test: Run at moderate load for extended period.

    Tests for:
    - Memory leaks
    - Resource exhaustion
    - Long-term stability
    """

    # Constant pacing for predictable load
    wait_time = constant(2)

    @task(10)
    def list_projects(self):
        self.client.get("/api/projects")

    @task(5)
    def get_project(self):
        self.client.get("/api/projects/test-id")

    @task(1)
    def upload_pdf(self):
        with open("tests/fixtures/sample.pdf", "rb") as f:
            self.client.post(
                "/api/upload",
                files={"file": ("sample.pdf", f, "application/pdf")}
            )

# Run for 4 hours with 50 concurrent users:
# locust -f soak_test.py --users 50 --spawn-rate 5 --run-time 4h
```

---

## Running Performance Tests

### Basic Load Test

```bash
# Start Locust web interface
locust -f tests/performance/locustfile.py --host http://localhost:8000

# Open browser to http://localhost:8089
# Configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Host: http://localhost:8000
```

### Headless Mode (CI/CD)

```bash
# Run without web UI
locust -f tests/performance/locustfile.py \
  --host http://staging.pdp.your-domain.com \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html report.html \
  --csv results
```

### Distributed Load Testing

**Master node:**
```bash
locust -f locustfile.py --master --expect-workers 4
```

**Worker nodes (x4):**
```bash
locust -f locustfile.py --worker --master-host <master-ip>
```

---

## Performance Monitoring

### Application Performance Monitoring

**Backend instrumentation (app/main.py):**
```python
from fastapi import FastAPI, Request
import time
import logging

app = FastAPI()

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request performance metrics"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.3f}s "
        f"with status {response.status_code}"
    )

    # Add custom header
    response.headers["X-Process-Time"] = str(process_time)

    return response
```

### Database Query Performance

**Slow query logging:**
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging
import time

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)

    # Log slow queries (> 1 second)
    if total > 1.0:
        logger.warning(
            f"Slow query detected ({total:.2f}s): {statement[:200]}"
        )
```

### Cloud Monitoring Integration

**Send metrics to Cloud Monitoring:**
```python
from google.cloud import monitoring_v3
import time

def record_api_latency(endpoint: str, latency_ms: float):
    """Record API endpoint latency to Cloud Monitoring"""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project_id}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/api/latency"
    series.metric.labels["endpoint"] = endpoint

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval(
        {"end_time": {"seconds": seconds, "nanos": nanos}}
    )

    point = monitoring_v3.Point({
        "interval": interval,
        "value": {"double_value": latency_ms}
    })
    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])
```

---

## Performance Optimization Strategies

### Backend Optimization

#### 1. Database Query Optimization

```python
# Bad - N+1 query problem
projects = await db.query(Project).all()
for project in projects:
    developer = await db.query(Developer).filter_by(id=project.developer_id).first()

# Good - Eager loading
projects = await db.query(Project).options(
    joinedload(Project.developer)
).all()
```

#### 2. Caching

```python
from functools import lru_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Initialize cache
@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="pdp-cache")

# Cache endpoint response
@app.get("/api/projects")
@cache(expire=300)  # Cache for 5 minutes
async def list_projects():
    return await project_service.list_all()

# Cache function result
@lru_cache(maxsize=128)
def get_template_config(template_id: str):
    """Cache template configuration"""
    return load_template_from_file(template_id)
```

#### 3. Async Operations

```python
import asyncio

# Bad - Sequential processing
async def process_images_sequentially(images: list[str]):
    results = []
    for image in images:
        result = await classify_image(image)
        results.append(result)
    return results

# Good - Concurrent processing
async def process_images_concurrently(images: list[str]):
    tasks = [classify_image(img) for img in images]
    results = await asyncio.gather(*tasks)
    return results
```

#### 4. Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks
):
    # Save file
    file_path = save_upload(file)

    # Create job
    job_id = create_job(file_path)

    # Process in background
    background_tasks.add_task(process_job, job_id)

    # Return immediately
    return {"job_id": job_id, "status": "pending"}
```

### Frontend Optimization

#### 1. Code Splitting

```typescript
// Lazy load routes
import { lazy, Suspense } from 'react';

const Projects = lazy(() => import('./pages/Projects'));
const Processing = lazy(() => import('./pages/Processing'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/projects" element={<Projects />} />
        <Route path="/processing" element={<Processing />} />
      </Routes>
    </Suspense>
  );
}
```

#### 2. React Query (Data Caching)

```typescript
import { useQuery } from '@tanstack/react-query';

function ProjectsList() {
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: fetchProjects,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  if (isLoading) return <LoadingSpinner />;

  return <ProjectsTable projects={data} />;
}
```

#### 3. Virtual Scrolling

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function LargeList({ items }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div key={virtualItem.index}>
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Performance Testing in CI/CD

### GitHub Actions Workflow

**.github/workflows/performance-test.yml:**
```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  performance-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install locust
          pip install -r requirements.txt

      - name: Run load test
        run: |
          locust -f tests/performance/locustfile.py \
            --host https://staging.pdp.your-domain.com \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html performance-report.html \
            --csv performance-results

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: |
            performance-report.html
            performance-results_*.csv

      - name: Check performance thresholds
        run: |
          python scripts/check_performance_thresholds.py \
            --results performance-results_stats.csv \
            --thresholds performance-thresholds.json
```

### Performance Threshold Validation

**scripts/check_performance_thresholds.py:**
```python
import csv
import json
import sys

def check_thresholds(results_file: str, thresholds_file: str):
    """Validate performance results against thresholds"""

    # Load thresholds
    with open(thresholds_file) as f:
        thresholds = json.load(f)

    # Load results
    with open(results_file) as f:
        reader = csv.DictReader(f)
        results = list(reader)

    failures = []

    for result in results:
        endpoint = result['Name']
        avg_response = float(result['Average Response Time'])
        p95_response = float(result['95%'])
        failure_rate = float(result['Failure Rate'])

        # Check if endpoint has thresholds
        if endpoint in thresholds:
            threshold = thresholds[endpoint]

            # Check response time
            if avg_response > threshold['avg_response_ms']:
                failures.append(
                    f"{endpoint}: Average response time {avg_response}ms "
                    f"exceeds threshold {threshold['avg_response_ms']}ms"
                )

            # Check p95
            if p95_response > threshold['p95_response_ms']:
                failures.append(
                    f"{endpoint}: P95 response time {p95_response}ms "
                    f"exceeds threshold {threshold['p95_response_ms']}ms"
                )

            # Check failure rate
            if failure_rate > threshold['max_failure_rate']:
                failures.append(
                    f"{endpoint}: Failure rate {failure_rate}% "
                    f"exceeds threshold {threshold['max_failure_rate']}%"
                )

    if failures:
        print("Performance test FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("Performance test PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--thresholds", required=True)
    args = parser.parse_args()

    check_thresholds(args.results, args.thresholds)
```

**performance-thresholds.json:**
```json
{
  "/api/projects": {
    "avg_response_ms": 500,
    "p95_response_ms": 1000,
    "max_failure_rate": 0.1
  },
  "/api/projects/[id]": {
    "avg_response_ms": 300,
    "p95_response_ms": 800,
    "max_failure_rate": 0.1
  },
  "/api/upload": {
    "avg_response_ms": 2000,
    "p95_response_ms": 5000,
    "max_failure_rate": 1.0
  }
}
```

---

## Performance Profiling

### Python Profiling

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    """Decorator to profile function execution"""
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        s = StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 slowest
        print(s.getvalue())

        return result
    return wrapper

@profile_function
def process_pdf(file_path: str):
    # Function to profile
    pass
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    """Profile memory usage"""
    large_list = [i for i in range(1000000)]
    # Process data
    return sum(large_list)
```

---

## Best Practices

### Performance Testing Best Practices

1. **Test on Staging Environment**
   - Never run load tests on production
   - Use production-like data and configuration

2. **Establish Baselines**
   - Measure current performance
   - Track metrics over time
   - Set realistic targets

3. **Test Incrementally**
   - Start with small load
   - Gradually increase
   - Identify breaking points

4. **Monitor System Resources**
   - CPU, memory, disk I/O
   - Database connections
   - Network bandwidth

5. **Analyze Results**
   - Look for trends and patterns
   - Investigate anomalies
   - Compare with previous runs

---

## Resources

### Tools
- [Locust Documentation](https://docs.locust.io/)
- [Google Cloud Monitoring](https://cloud.google.com/monitoring)
- [cProfile](https://docs.python.org/3/library/profile.html)

### Monitoring Dashboards
- Cloud Monitoring Dashboard
- Application Performance Monitoring (APM)
- Custom Grafana dashboards

---

## Appendix: Common Performance Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| **N+1 Queries** | Slow database operations | Use eager loading (joinedload) |
| **Missing Indexes** | Slow query execution | Add database indexes |
| **Large Payloads** | High network latency | Implement pagination, compression |
| **Synchronous I/O** | Blocked event loop | Use async/await |
| **Memory Leaks** | Increasing memory usage | Profile and fix leaks |
| **Unoptimized Images** | Slow page load | Optimize images, use CDN |

---

**Next Steps:**
1. Set up weekly performance tests on staging
2. Configure monitoring dashboards
3. Establish performance SLAs
4. Create alerting for performance degradation

**Related Documentation:**
- `TEST_STRATEGY.md` - Overall testing approach
- `INTEGRATION_TESTS.md` - API testing patterns
- Cloud Run documentation for scaling configuration
