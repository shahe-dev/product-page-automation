# QA Multi-Agent System

**Version:** 1.0
**Last Updated:** 2026-01-15
**Owner:** QA Team
**Status:** Core Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Multi-Agent Architecture](#multi-agent-architecture)
4. [Agent Specifications](#agent-specifications)
   - [Code Quality Agent](#1-code-quality-agent)
   - [Security Agent](#2-security-agent)
   - [Integration Agent](#3-integration-agent)
   - [Performance Agent](#4-performance-agent)
   - [Documentation Agent](#5-documentation-agent)
   - [Escalation Agent](#6-escalation-agent)
   - [Dependency Agent](#7-dependency-agent)
5. [Agent Orchestration](#agent-orchestration)
6. [CI/CD Integration](#cicd-integration)
7. [Quality Gates](#quality-gates)
8. [Communication Protocol](#communication-protocol)
9. [Escalation Procedures](#escalation-procedures)
10. [Metrics & Reporting](#metrics--reporting)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The QA Multi-Agent System provides **autonomous, continuous quality enforcement** across all phases of the PDP Automation v.3 development lifecycle. Rather than relying solely on manual code reviews and human QA checkpoints, this system deploys specialized agents that monitor, validate, and enforce quality standards at every stage.

Each agent operates independently but communicates through a centralized orchestration layer, enabling coordinated responses to quality issues and preventing cascading failures from reaching production.

The system integrates directly with the CI/CD pipeline, GitHub workflows, and the existing 4-checkpoint QA module to provide defense-in-depth quality assurance.

---

## Purpose & Goals

### Primary Purpose

Establish an automated, multi-layered quality assurance system that catches issues early, enforces standards consistently, and reduces manual review bottlenecks while maintaining the highest code quality standards.

### Goals

1. **Zero Critical Defects in Production** - Catch all critical issues before merge to main
2. **Consistent Code Quality** - Enforce standards across all contributors automatically
3. **Fast Feedback Loops** - Provide quality feedback within minutes, not hours
4. **Reduced Manual Review Burden** - Automate repetitive quality checks
5. **Continuous Security Posture** - Scan every commit for vulnerabilities
6. **Performance Regression Prevention** - Detect slowdowns before they reach users
7. **Complete Audit Trail** - Document all quality decisions for compliance

---

## Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QA ORCHESTRATION LAYER                               │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Message    │  │    Agent     │  │   Quality    │  │   Metrics    │    │
│  │    Queue     │  │   Registry   │  │    Gates     │  │  Aggregator  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AGENT LAYER                                       │
│                                                                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │   Code     │ │  Security  │ │Integration │ │Performance │ │    Doc     ││
│  │  Quality   │ │   Agent    │ │   Agent    │ │   Agent    │ │   Agent    ││
│  │   Agent    │ │            │ │            │ │            │ │            ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
│                                                                              │
│  ┌────────────┐ ┌────────────┐                                              │
│  │ Escalation │ │ Dependency │                                              │
│  │   Agent    │ │   Agent    │                                              │
│  └────────────┘ └────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATION LAYER                                    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    GitHub    │  │   CI/CD      │  │   Slack/     │  │   Sentry/    │    │
│  │   Webhooks   │  │  Pipeline    │  │   Email      │  │   Logging    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Specifications

### 1. Code Quality Agent

**Agent ID:** `qa-code-quality-001`
**Trigger Events:** Every commit, PR creation, PR update
**Priority:** P1 - Critical (blocks merge)

#### Responsibilities

| Check | Tool | Threshold | Action on Failure |
|-------|------|-----------|-------------------|
| Python Linting | Ruff | 0 errors | Block PR |
| Python Formatting | Black | 100% formatted | Auto-fix + commit |
| TypeScript Linting | ESLint | 0 errors | Block PR |
| TypeScript Formatting | Prettier | 100% formatted | Auto-fix + commit |
| Type Checking | mypy / tsc | 0 errors | Block PR |
| Complexity Analysis | radon | CC < 10 | Warning at 10, Block at 15 |
| Dead Code Detection | vulture | 0 unused | Warning |
| Import Sorting | isort | Sorted | Auto-fix + commit |
| Docstring Coverage | interrogate | > 80% public | Warning |

#### Configuration

```yaml
# .github/workflows/code-quality-agent.yml
name: Code Quality Agent

on:
  push:
    branches: [main, staging, develop]
  pull_request:
    branches: [main, staging]

jobs:
  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python Quality Checks
        run: |
          pip install ruff black mypy radon vulture isort interrogate
          ruff check . --output-format=github
          black --check .
          mypy backend/ --strict
          radon cc backend/ -a -nc

      - name: TypeScript Quality Checks
        run: |
          npm ci
          npm run lint
          npm run type-check
          npx prettier --check "frontend/src/**/*.{ts,tsx}"

      - name: Complexity Report
        run: |
          radon cc backend/ -a -j > complexity-report.json
          python scripts/check_complexity.py complexity-report.json
```

#### Quality Metrics Produced

```json
{
  "agent": "code-quality",
  "timestamp": "2026-01-15T10:30:00Z",
  "commit": "abc123",
  "metrics": {
    "lint_errors": 0,
    "format_issues": 0,
    "type_errors": 0,
    "avg_complexity": 4.2,
    "max_complexity": 8,
    "docstring_coverage": 85.5,
    "dead_code_items": 0
  },
  "status": "PASS",
  "duration_ms": 45000
}
```

---

### 2. Security Agent

**Agent ID:** `qa-security-001`
**Trigger Events:** Every commit, PR creation, daily scheduled scan
**Priority:** P1 - Critical (blocks merge for HIGH/CRITICAL)

#### Responsibilities

| Check | Tool | Severity Threshold | Action on Failure |
|-------|------|-------------------|-------------------|
| SAST (Python) | Bandit | No HIGH/CRITICAL | Block PR |
| SAST (TypeScript) | ESLint Security Plugin | No HIGH | Block PR |
| Dependency Vulnerabilities | Safety + Snyk | No HIGH/CRITICAL | Block PR |
| Secret Detection | Gitleaks | Any secret | Block PR + Alert |
| OWASP Top 10 | Semgrep | No matches | Block PR |
| License Compliance | pip-licenses | No GPL in prod | Warning |
| Container Scanning | Trivy | No CRITICAL | Block deploy |

#### Configuration

```yaml
# .github/workflows/security-agent.yml
name: Security Agent

on:
  push:
    branches: [main, staging, develop]
  pull_request:
    branches: [main, staging]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for secret scanning

      - name: Secret Detection
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Python SAST
        run: |
          pip install bandit safety semgrep
          bandit -r backend/ -f json -o bandit-report.json
          safety check --json > safety-report.json
          semgrep --config=p/owasp-top-ten backend/

      - name: Dependency Audit
        run: |
          pip install pip-audit
          pip-audit --strict --desc on

      - name: TypeScript Security
        run: |
          npm audit --audit-level=high
          npx eslint frontend/src --ext .ts,.tsx --config .eslintrc.security.js

      - name: Container Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'gcr.io/${{ env.PROJECT_ID }}/pdp-backend:${{ github.sha }}'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

#### Secret Detection Rules

```toml
# .gitleaks.toml
title = "PDP Automation Secret Detection"

[[rules]]
id = "google-api-key"
description = "Google API Key"
regex = '''AIza[0-9A-Za-z\-_]{35}'''
tags = ["key", "google"]

[[rules]]
id = "anthropic-api-key"
description = "Anthropic API Key"
regex = '''sk-ant-[a-zA-Z0-9\-_]{90,}'''
tags = ["key", "anthropic"]

[[rules]]
id = "jwt-token"
description = "JWT Token"
regex = '''eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'''
tags = ["token", "jwt"]

[allowlist]
paths = [
  '''\.env\.example$''',
  '''tests/fixtures/.*'''
]
```

#### Security Metrics Produced

```json
{
  "agent": "security",
  "timestamp": "2026-01-15T10:35:00Z",
  "commit": "abc123",
  "metrics": {
    "sast_critical": 0,
    "sast_high": 0,
    "sast_medium": 2,
    "dependency_vulnerabilities": 0,
    "secrets_detected": 0,
    "license_issues": 0,
    "container_vulnerabilities": 0
  },
  "status": "PASS",
  "duration_ms": 120000
}
```

---

### 3. Integration Agent

**Agent ID:** `qa-integration-001`
**Trigger Events:** PR creation, PR update, merge to staging
**Priority:** P1 - Critical (blocks merge)

#### Responsibilities

| Check | Scope | Threshold | Action on Failure |
|-------|-------|-----------|-------------------|
| API Contract Tests | All endpoints | 100% pass | Block PR |
| Schema Validation | OpenAPI spec | Valid | Block PR |
| Backwards Compatibility | Breaking changes | None allowed | Block PR + Review |
| Database Migration | Up/down scripts | Reversible | Block PR |
| Service Integration | External APIs | Mock pass | Block PR |
| Cross-Service Communication | Internal APIs | 100% pass | Block PR |

#### Configuration

```yaml
# .github/workflows/integration-agent.yml
name: Integration Agent

on:
  pull_request:
    branches: [main, staging]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: pdp_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: API Contract Validation
        run: |
          pip install schemathesis
          schemathesis run backend/openapi.yaml --base-url http://localhost:8000

      - name: Backwards Compatibility Check
        run: |
          pip install openapi-diff
          openapi-diff main:backend/openapi.yaml HEAD:backend/openapi.yaml --fail-on-breaking

      - name: Database Migration Test
        run: |
          alembic upgrade head
          alembic downgrade -1
          alembic upgrade head

      - name: Integration Test Suite
        run: |
          pytest tests/integration/ -v --tb=short \
            --junitxml=integration-results.xml \
            -m "not slow"

      - name: Service Mock Tests
        run: |
          pytest tests/integration/external/ -v \
            --mock-anthropic \
            --mock-google-sheets \
            --mock-cloud-storage
```

#### API Contract Schema

```python
# tests/contracts/test_api_contracts.py
import schemathesis
from hypothesis import settings, Phase

schema = schemathesis.from_path("backend/openapi.yaml")

@schema.parametrize()
@settings(max_examples=50, phases=[Phase.explicit, Phase.generate])
def test_api_contract(case):
    """Validate all API endpoints match OpenAPI specification."""
    response = case.call()
    case.validate_response(response)
```

#### Integration Metrics Produced

```json
{
  "agent": "integration",
  "timestamp": "2026-01-15T10:40:00Z",
  "commit": "abc123",
  "metrics": {
    "contract_tests_passed": 156,
    "contract_tests_failed": 0,
    "schema_valid": true,
    "breaking_changes": 0,
    "migration_reversible": true,
    "external_api_mocks_passed": 24,
    "coverage_integration": 82.5
  },
  "status": "PASS",
  "duration_ms": 300000
}
```

---

### 4. Performance Agent

**Agent ID:** `qa-performance-001`
**Trigger Events:** PR to main, weekly scheduled, pre-release
**Priority:** P2 - High (blocks release, warns on PR)

#### Responsibilities

| Check | Baseline | Threshold | Action on Failure |
|-------|----------|-----------|-------------------|
| API Response Time (P95) | 200ms | +20% regression | Block release |
| PDF Processing Time | 30s/page | +25% regression | Warning |
| Memory Usage | 512MB | +50% increase | Warning |
| Database Query Time | 50ms avg | +30% regression | Block release |
| Frontend Bundle Size | 500KB | +10% increase | Warning |
| Lighthouse Score | 90 | -5 points | Warning |

#### Configuration

```yaml
# .github/workflows/performance-agent.yml
name: Performance Agent

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Weekly Sunday 2 AM

jobs:
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Load Baseline Metrics
        run: |
          gsutil cp gs://pdp-metrics/baseline/performance.json ./baseline.json

      - name: API Performance Tests
        run: |
          pip install locust pytest-benchmark
          locust -f tests/performance/locustfile.py \
            --headless \
            --users 50 \
            --spawn-rate 10 \
            --run-time 5m \
            --json > api-perf.json

      - name: Database Performance
        run: |
          pytest tests/performance/test_db_queries.py \
            --benchmark-json=db-perf.json \
            --benchmark-compare=baseline.json

      - name: Frontend Bundle Analysis
        run: |
          cd frontend
          npm run build
          npx bundlesize

      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v10
        with:
          configPath: './lighthouserc.json'
          uploadArtifacts: true

      - name: Compare Against Baseline
        run: |
          python scripts/performance_regression.py \
            --baseline baseline.json \
            --current api-perf.json \
            --threshold 0.20
```

#### Performance Baseline Definition

```json
{
  "baselines": {
    "api_endpoints": {
      "/api/v1/projects": {"p50": 45, "p95": 120, "p99": 200},
      "/api/v1/pdp/generate": {"p50": 5000, "p95": 15000, "p99": 30000},
      "/api/v1/sheets/push": {"p50": 800, "p95": 2000, "p99": 5000}
    },
    "pdf_processing": {
      "extraction_per_page_ms": 3000,
      "content_generation_ms": 8000
    },
    "database": {
      "avg_query_ms": 25,
      "p95_query_ms": 50
    },
    "frontend": {
      "bundle_size_kb": 485,
      "lighthouse_performance": 92
    }
  },
  "last_updated": "2026-01-15",
  "environment": "staging"
}
```

#### Performance Metrics Produced

```json
{
  "agent": "performance",
  "timestamp": "2026-01-15T10:50:00Z",
  "commit": "abc123",
  "metrics": {
    "api_p95_ms": 115,
    "api_p95_regression_pct": -4.2,
    "pdf_extraction_ms": 2850,
    "db_avg_query_ms": 23,
    "frontend_bundle_kb": 492,
    "lighthouse_score": 91
  },
  "status": "PASS",
  "regressions": [],
  "duration_ms": 600000
}
```

---

### 5. Documentation Agent

**Agent ID:** `qa-documentation-001`
**Trigger Events:** PR with code changes, weekly audit
**Priority:** P3 - Medium (warning only)

#### Responsibilities

| Check | Scope | Threshold | Action on Failure |
|-------|-------|-----------|-------------------|
| API Doc Sync | OpenAPI vs code | 100% match | Warning |
| Changelog Updated | CHANGELOG.md | Entry for PR | Warning |
| README Accuracy | Links, examples | Valid | Warning |
| Docstring Coverage | Public functions | > 80% | Warning |
| Broken Links | All .md files | 0 broken | Warning |

#### Configuration

```yaml
# .github/workflows/documentation-agent.yml
name: Documentation Agent

on:
  pull_request:
    branches: [main, staging]
  schedule:
    - cron: '0 8 * * 1'  # Weekly Monday 8 AM

jobs:
  doc-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check Broken Links
        uses: lycheeverse/lychee-action@v1
        with:
          args: --verbose --no-progress './docs/**/*.md' './README.md'
          fail: false

      - name: Changelog Entry Check
        run: |
          if git diff --name-only origin/main | grep -qE '\.(py|ts|tsx)$'; then
            if ! git diff origin/main -- CHANGELOG.md | grep -q '^+'; then
              echo "::warning::No CHANGELOG entry for code changes"
            fi
          fi

      - name: OpenAPI Sync Check
        run: |
          pip install openapi-spec-validator
          python scripts/validate_openapi_sync.py

      - name: Docstring Coverage
        run: |
          pip install interrogate
          interrogate backend/ -v -f 80 --fail-under 80 || echo "::warning::Docstring coverage below 80%"
```

---

### 6. Escalation Agent

**Agent ID:** `qa-escalation-001`
**Trigger Events:** Any agent failure, QA checkpoint failure, timeout
**Priority:** P1 - Critical (manages all escalations)

#### Responsibilities

| Trigger | Initial Action | Escalation Path | Timeout |
|---------|---------------|-----------------|---------|
| Agent Failure | Retry 3x | Notify dev → Lead → Manager | 30 min |
| Critical Security | Block + Alert | Security Lead → CTO | Immediate |
| Performance Regression | Warning | Performance Lead → Architect | 2 hours |
| QA Checkpoint Fail | Retry + Log | QA Lead → Product Owner | 1 hour |
| Deploy Failure | Rollback | DevOps → Lead → On-call | 15 min |

#### Escalation Matrix

```yaml
# config/escalation-matrix.yaml
escalation_policies:
  security_critical:
    severity: P0
    initial_wait: 0
    escalation_chain:
      - channel: slack
        target: "#security-alerts"
        wait: 0
      - channel: pagerduty
        target: security-oncall
        wait: 5m
      - channel: email
        target: cto@your-domain.com
        wait: 15m
    actions:
      - block_deploy
      - create_incident
      - notify_stakeholders

  test_failure:
    severity: P1
    initial_wait: 0
    escalation_chain:
      - channel: slack
        target: "#dev-alerts"
        wait: 0
      - channel: slack
        target: "@pr-author"
        wait: 5m
      - channel: email
        target: tech-lead@your-domain.com
        wait: 30m
    actions:
      - block_merge
      - add_pr_comment

  performance_regression:
    severity: P2
    initial_wait: 0
    escalation_chain:
      - channel: slack
        target: "#performance-alerts"
        wait: 0
      - channel: slack
        target: "@performance-lead"
        wait: 1h
    actions:
      - add_warning_label
      - request_review

  qa_checkpoint_failure:
    severity: P1
    initial_wait: 0
    escalation_chain:
      - channel: slack
        target: "#qa-alerts"
        wait: 0
      - channel: email
        target: qa-team@your-domain.com
        wait: 15m
      - channel: pagerduty
        target: qa-oncall
        wait: 30m
    actions:
      - retry_checkpoint
      - log_failure
      - notify_user
```

#### Escalation Agent Implementation

```python
# backend/agents/escalation_agent.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import asyncio

class Severity(Enum):
    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_MEDIUM = 2
    P3_LOW = 3

@dataclass
class EscalationEvent:
    agent_id: str
    event_type: str
    severity: Severity
    message: str
    context: dict
    timestamp: str

class EscalationAgent:
    """
    Manages escalation workflows for all QA agent failures.
    """

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.active_escalations: dict = {}

    async def handle_failure(self, event: EscalationEvent) -> None:
        """Process a failure event and initiate escalation."""

        # Determine escalation policy
        policy = self._get_policy(event.event_type, event.severity)

        # Execute initial actions
        for action in policy.actions:
            await self._execute_action(action, event)

        # Start escalation chain
        escalation_id = f"{event.agent_id}-{event.timestamp}"
        self.active_escalations[escalation_id] = {
            "event": event,
            "policy": policy,
            "current_level": 0,
            "acknowledged": False
        }

        # Begin escalation loop
        asyncio.create_task(self._escalation_loop(escalation_id))

    async def acknowledge(self, escalation_id: str, responder: str) -> None:
        """Acknowledge an escalation to stop further escalation."""
        if escalation_id in self.active_escalations:
            self.active_escalations[escalation_id]["acknowledged"] = True
            await self._notify_acknowledgment(escalation_id, responder)

    async def _escalation_loop(self, escalation_id: str) -> None:
        """Progress through escalation chain until acknowledged."""
        escalation = self.active_escalations[escalation_id]
        chain = escalation["policy"].escalation_chain

        for level, step in enumerate(chain):
            if escalation["acknowledged"]:
                break

            await self._notify(step.channel, step.target, escalation["event"])
            escalation["current_level"] = level

            await asyncio.sleep(step.wait.total_seconds())

        # Final escalation if not acknowledged
        if not escalation["acknowledged"]:
            await self._final_escalation(escalation_id)
```

---

### 7. Dependency Agent

**Agent ID:** `qa-dependency-001`
**Trigger Events:** Daily scheduled, PR with dependency changes
**Priority:** P2 - High (blocks on critical vulnerabilities)

#### Responsibilities

| Check | Scope | Threshold | Action on Failure |
|-------|-------|-----------|-------------------|
| Vulnerability Scan | All deps | No CRITICAL/HIGH | Block PR |
| Version Currency | Major versions | < 2 versions behind | Warning |
| EOL Tracking | Python/Node/deps | > 6 months to EOL | Warning |
| License Compliance | Production deps | No GPL/AGPL | Block PR |
| Compatibility Matrix | Key deps | Tested combinations | Warning |

#### Configuration

```yaml
# .github/workflows/dependency-agent.yml
name: Dependency Agent

on:
  pull_request:
    paths:
      - 'requirements*.txt'
      - 'pyproject.toml'
      - 'package*.json'
  schedule:
    - cron: '0 4 * * *'  # Daily 4 AM

jobs:
  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python Dependency Audit
        run: |
          pip install pip-audit safety pip-licenses
          pip-audit --strict --desc on -r requirements.txt
          safety check -r requirements.txt --json > safety-report.json
          pip-licenses --format=json > licenses.json
          python scripts/check_licenses.py licenses.json

      - name: Node Dependency Audit
        run: |
          cd frontend
          npm audit --audit-level=high
          npx license-checker --production --json > licenses.json

      - name: EOL Check
        run: |
          pip install endoflife
          python scripts/check_eol.py

      - name: Dependency Freshness
        uses: renovatebot/github-action@v40
        with:
          configurationFile: renovate.json
          token: ${{ secrets.GITHUB_TOKEN }}
```

#### Dependency Compatibility Matrix

```json
{
  "compatibility_matrix": {
    "python": {
      "version": "3.11",
      "min_supported": "3.10",
      "max_tested": "3.12"
    },
    "node": {
      "version": "18",
      "min_supported": "18",
      "max_tested": "20"
    },
    "key_dependencies": {
      "fastapi": {"min": "0.100.0", "max": "0.110.x", "tested": "0.109.0"},
      "sqlalchemy": {"min": "2.0.0", "max": "2.x", "tested": "2.0.25"},
      "react": {"min": "18.2.0", "max": "18.x", "tested": "18.2.0"},
      "anthropic": {"min": "0.30.0", "max": "0.x", "tested": "0.42.0"}
    }
  },
  "last_updated": "2026-01-15"
}
```

---

## Agent Orchestration

### Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│                     PR CREATED / COMMIT PUSHED                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: IMMEDIATE (Parallel)                    [< 2 min]     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Code Quality│  │  Security   │  │ Dependency  │              │
│  │    Agent    │  │   Agent     │  │   Agent     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                    All Phase 1 Pass?
                              │
              ┌───────────────┴───────────────┐
              │ NO                            │ YES
              ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│   ESCALATION AGENT      │   │  PHASE 2: INTEGRATION [< 10 min]│
│   - Block PR            │   │  ┌─────────────┐                │
│   - Notify author       │   │  │ Integration │                │
│   - Log failure         │   │  │   Agent     │                │
└─────────────────────────┘   │  └─────────────┘                │
                              └─────────────────────────────────┘
                                              │
                                    Integration Pass?
                                              │
                              ┌───────────────┴───────────────┐
                              │ NO                            │ YES
                              ▼                               ▼
                ┌─────────────────────────┐   ┌─────────────────────────────────┐
                │   ESCALATION AGENT      │   │  PHASE 3: QUALITY [< 15 min]   │
                │   - Block PR            │   │  ┌─────────────┐ ┌───────────┐ │
                │   - Request changes     │   │  │ Performance │ │    Doc    │ │
                └─────────────────────────┘   │  │   Agent     │ │  Agent    │ │
                                              │  └─────────────┘ └───────────┘ │
                                              └─────────────────────────────────┘
                                                              │
                                                              ▼
                                              ┌─────────────────────────────────┐
                                              │  QUALITY GATE DECISION          │
                                              │  - All P1 agents pass: APPROVE  │
                                              │  - P2/P3 warnings: APPROVE+WARN │
                                              │  - Any P1 fail: BLOCK           │
                                              └─────────────────────────────────┘
```

### Parallel Execution Rules

```yaml
# config/agent-orchestration.yaml
orchestration:
  phases:
    - name: immediate
      parallel: true
      timeout: 120s
      agents:
        - code-quality
        - security
        - dependency
      gate: all_must_pass

    - name: integration
      parallel: false
      timeout: 600s
      agents:
        - integration
      gate: must_pass
      depends_on: immediate

    - name: quality
      parallel: true
      timeout: 900s
      agents:
        - performance
        - documentation
      gate: warnings_allowed
      depends_on: integration

  failure_handling:
    retry_count: 3
    retry_delay: 30s
    escalate_on_retry_exhausted: true
```

---

## CI/CD Integration

### GitHub Actions Integration

```yaml
# .github/workflows/qa-multi-agent.yml
name: QA Multi-Agent System

on:
  push:
    branches: [main, staging, develop]
  pull_request:
    branches: [main, staging]

concurrency:
  group: qa-${{ github.ref }}
  cancel-in-progress: true

jobs:
  # Phase 1: Immediate Checks (Parallel)
  code-quality:
    uses: ./.github/workflows/code-quality-agent.yml

  security:
    uses: ./.github/workflows/security-agent.yml

  dependency:
    uses: ./.github/workflows/dependency-agent.yml

  # Gate 1: All immediate checks must pass
  gate-1:
    needs: [code-quality, security, dependency]
    runs-on: ubuntu-latest
    steps:
      - name: Verify Phase 1
        run: echo "Phase 1 passed"

  # Phase 2: Integration Tests
  integration:
    needs: gate-1
    uses: ./.github/workflows/integration-agent.yml

  # Gate 2: Integration must pass
  gate-2:
    needs: integration
    runs-on: ubuntu-latest
    steps:
      - name: Verify Phase 2
        run: echo "Phase 2 passed"

  # Phase 3: Quality Checks (Parallel, warnings allowed)
  performance:
    needs: gate-2
    uses: ./.github/workflows/performance-agent.yml
    continue-on-error: true

  documentation:
    needs: gate-2
    uses: ./.github/workflows/documentation-agent.yml
    continue-on-error: true

  # Final Gate: Aggregate results
  final-gate:
    needs: [gate-2, performance, documentation]
    runs-on: ubuntu-latest
    steps:
      - name: Aggregate Results
        run: |
          echo "All critical checks passed"
          if [ "${{ needs.performance.result }}" == "failure" ]; then
            echo "::warning::Performance checks had warnings"
          fi
          if [ "${{ needs.documentation.result }}" == "failure" ]; then
            echo "::warning::Documentation checks had warnings"
          fi

      - name: Update PR Status
        uses: actions/github-script@v7
        with:
          script: |
            const { data: checks } = await github.rest.checks.listForRef({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha
            });

            const summary = checks.check_runs.map(c =>
              `${c.conclusion === 'success' ? '✅' : '⚠️'} ${c.name}`
            ).join('\n');

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## QA Multi-Agent Report\n\n${summary}`
            });
```

### Cloud Build Integration

```yaml
# cloudbuild-qa.yaml
steps:
  # Phase 1: Parallel immediate checks
  - id: 'code-quality'
    name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install ruff black mypy
        ruff check . --output-format=github
        black --check .
        mypy backend/ --strict
    waitFor: ['-']

  - id: 'security'
    name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install bandit safety
        bandit -r backend/ -ll
        safety check -r requirements.txt
    waitFor: ['-']

  - id: 'dependency'
    name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install pip-audit
        pip-audit -r requirements.txt
    waitFor: ['-']

  # Phase 2: Integration (after Phase 1)
  - id: 'integration'
    name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install -r requirements.txt
        pytest tests/integration/ -v
    waitFor: ['code-quality', 'security', 'dependency']

  # Phase 3: Performance (after Phase 2)
  - id: 'performance'
    name: 'python:3.11'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        pip install locust pytest-benchmark
        pytest tests/performance/ --benchmark-only
    waitFor: ['integration']

options:
  logging: CLOUD_LOGGING_ONLY
```

---

## Quality Gates

### Gate Definitions

| Gate | Required Agents | Pass Criteria | Block Level |
|------|----------------|---------------|-------------|
| **PR Merge Gate** | Code Quality, Security, Integration | All P1 pass, P2 warn only | Block merge |
| **Staging Deploy Gate** | All agents | All P1 pass | Block deploy |
| **Production Deploy Gate** | All agents + manual approval | All pass, no warnings | Block deploy |
| **Release Gate** | All agents + performance baseline | No regressions | Block release |

### Gate Implementation

```python
# backend/qa/quality_gates.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

class GateResult(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"

@dataclass
class AgentResult:
    agent_id: str
    status: GateResult
    priority: int  # 1 = critical, 2 = high, 3 = medium
    metrics: Dict
    messages: List[str]

class QualityGate:
    """Evaluates agent results against gate criteria."""

    def __init__(self, gate_name: str, config: dict):
        self.name = gate_name
        self.required_agents = config["required_agents"]
        self.block_on_p1_fail = config.get("block_on_p1_fail", True)
        self.block_on_p2_fail = config.get("block_on_p2_fail", False)

    def evaluate(self, results: List[AgentResult]) -> GateResult:
        """Evaluate all agent results and determine gate status."""

        # Check all required agents reported
        reported = {r.agent_id for r in results}
        missing = set(self.required_agents) - reported
        if missing:
            return GateResult.FAIL

        # Evaluate by priority
        p1_failures = [r for r in results if r.priority == 1 and r.status == GateResult.FAIL]
        p2_failures = [r for r in results if r.priority == 2 and r.status == GateResult.FAIL]
        warnings = [r for r in results if r.status == GateResult.WARN]

        if p1_failures and self.block_on_p1_fail:
            return GateResult.FAIL

        if p2_failures and self.block_on_p2_fail:
            return GateResult.FAIL

        if warnings or p2_failures:
            return GateResult.WARN

        return GateResult.PASS
```

---

## Communication Protocol

### Agent-to-Orchestrator Messages

```json
{
  "message_type": "agent_result",
  "agent_id": "qa-code-quality-001",
  "correlation_id": "pr-123-commit-abc",
  "timestamp": "2026-01-15T10:30:00Z",
  "payload": {
    "status": "PASS",
    "priority": 1,
    "duration_ms": 45000,
    "metrics": {
      "lint_errors": 0,
      "type_errors": 0
    },
    "issues": [],
    "artifacts": [
      "gs://pdp-qa-artifacts/pr-123/lint-report.json"
    ]
  }
}
```

### Orchestrator-to-Agent Messages

```json
{
  "message_type": "agent_trigger",
  "target_agent": "qa-security-001",
  "correlation_id": "pr-123-commit-abc",
  "timestamp": "2026-01-15T10:30:00Z",
  "payload": {
    "event_type": "pull_request",
    "repository": "mpd-ae/pdp-automation",
    "ref": "refs/pull/123/head",
    "commit_sha": "abc123",
    "changed_files": [
      "backend/services/extraction.py",
      "frontend/src/components/PDPForm.tsx"
    ],
    "config_overrides": {}
  }
}
```

### Notification Templates

```yaml
# config/notification-templates.yaml
templates:
  pr_blocked:
    slack:
      color: "danger"
      title: "PR Blocked by QA Agent"
      fields:
        - title: "PR"
          value: "{{pr_url}}"
        - title: "Agent"
          value: "{{agent_id}}"
        - title: "Reason"
          value: "{{failure_reason}}"
      actions:
        - text: "View Details"
          url: "{{details_url}}"

  security_alert:
    slack:
      color: "danger"
      title: "🚨 Security Vulnerability Detected"
      fields:
        - title: "Severity"
          value: "{{severity}}"
        - title: "CVE"
          value: "{{cve_id}}"
        - title: "Package"
          value: "{{package_name}}"
      mentions:
        - "@security-team"

  performance_regression:
    slack:
      color: "warning"
      title: "⚠️ Performance Regression Detected"
      fields:
        - title: "Metric"
          value: "{{metric_name}}"
        - title: "Baseline"
          value: "{{baseline_value}}"
        - title: "Current"
          value: "{{current_value}}"
        - title: "Regression"
          value: "{{regression_pct}}%"
```

---

## Metrics & Reporting

### Dashboard Metrics

```sql
-- QA Agent Performance Dashboard Queries

-- Agent Success Rate (Last 7 Days)
SELECT
    agent_id,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) as passes,
    ROUND(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM qa_agent_results
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY agent_id
ORDER BY success_rate ASC;

-- Average Gate Time by Phase
SELECT
    phase_name,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms
FROM qa_gate_timings
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY phase_name;

-- Top Failure Reasons
SELECT
    failure_category,
    COUNT(*) as occurrences,
    array_agg(DISTINCT agent_id) as affected_agents
FROM qa_failures
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY failure_category
ORDER BY occurrences DESC
LIMIT 10;

-- PR Cycle Time (First commit to merge)
SELECT
    DATE_TRUNC('week', merged_at) as week,
    AVG(EXTRACT(EPOCH FROM (merged_at - first_commit_at)) / 3600) as avg_hours_to_merge,
    COUNT(*) as prs_merged
FROM pull_requests
WHERE merged_at > NOW() - INTERVAL '90 days'
GROUP BY week
ORDER BY week;
```

### Weekly Report Template

```markdown
# QA Multi-Agent Weekly Report

**Period:** {{start_date}} - {{end_date}}
**Generated:** {{generated_at}}

## Executive Summary

| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| PRs Processed | {{prs_this_week}} | {{prs_last_week}} | {{pr_trend}} |
| Gate Pass Rate | {{pass_rate}}% | {{last_pass_rate}}% | {{pass_trend}} |
| Avg Time to Merge | {{avg_merge_hours}}h | {{last_avg_merge}}h | {{merge_trend}} |
| Security Issues Found | {{security_issues}} | {{last_security}} | {{security_trend}} |

## Agent Performance

{{#each agents}}
### {{name}}
- **Runs:** {{runs}}
- **Pass Rate:** {{pass_rate}}%
- **Avg Duration:** {{avg_duration}}s
- **Top Issue:** {{top_issue}}
{{/each}}

## Blocked PRs

{{#each blocked_prs}}
- **PR #{{number}}:** {{title}}
  - **Reason:** {{reason}}
  - **Agent:** {{agent}}
  - **Resolution:** {{resolution}}
{{/each}}

## Recommendations

{{#each recommendations}}
- {{this}}
{{/each}}
```

---

## Configuration

### Environment Variables

```bash
# QA Multi-Agent System Configuration

# Agent Registry
QA_AGENT_REGISTRY_URL=https://qa-registry.pdp.internal
QA_AGENT_TIMEOUT_DEFAULT=300000

# Quality Gates
QA_GATE_PR_MERGE_STRICT=true
QA_GATE_STAGING_DEPLOY_STRICT=true
QA_GATE_PROD_DEPLOY_STRICT=true

# Escalation
QA_ESCALATION_ENABLED=true
QA_ESCALATION_SLACK_WEBHOOK=https://hooks.slack.com/services/xxx
QA_ESCALATION_PAGERDUTY_KEY=xxx

# Metrics
QA_METRICS_ENABLED=true
QA_METRICS_EXPORT_INTERVAL=60

# Thresholds
QA_COVERAGE_MIN=85
QA_COMPLEXITY_MAX=15
QA_PERFORMANCE_REGRESSION_THRESHOLD=20
QA_SECURITY_BLOCK_SEVERITY=HIGH
```

### Agent Configuration File

```yaml
# config/qa-agents.yaml
agents:
  code-quality:
    enabled: true
    priority: 1
    timeout: 120s
    retry_count: 3
    tools:
      python:
        linter: ruff
        formatter: black
        type_checker: mypy
      typescript:
        linter: eslint
        formatter: prettier
        type_checker: tsc
    thresholds:
      complexity_warning: 10
      complexity_block: 15
      coverage_min: 85

  security:
    enabled: true
    priority: 1
    timeout: 180s
    retry_count: 2
    tools:
      sast: [bandit, semgrep]
      dependency: [safety, pip-audit, npm-audit]
      secrets: gitleaks
    thresholds:
      block_severity: HIGH
      warn_severity: MEDIUM

  integration:
    enabled: true
    priority: 1
    timeout: 600s
    retry_count: 2
    test_patterns:
      - "tests/integration/**/*.py"
    coverage_threshold: 75

  performance:
    enabled: true
    priority: 2
    timeout: 900s
    retry_count: 1
    baseline_file: "gs://pdp-metrics/baseline/performance.json"
    regression_threshold: 20

  documentation:
    enabled: true
    priority: 3
    timeout: 120s
    retry_count: 1
    check_links: true
    check_changelog: true

  dependency:
    enabled: true
    priority: 2
    timeout: 120s
    retry_count: 2
    check_vulnerabilities: true
    check_licenses: true
    check_eol: true

  escalation:
    enabled: true
    config_file: "config/escalation-matrix.yaml"
```

---

## Related Documentation

### Core Documentation
- [TEST_STRATEGY.md](./TEST_STRATEGY.md) - Overall testing approach and standards
- [INTEGRATION_TESTS.md](./INTEGRATION_TESTS.md) - Integration test implementation
- [E2E_TEST_SCENARIOS.md](./E2E_TEST_SCENARIOS.md) - End-to-end test scenarios
- [PERFORMANCE_TESTING.md](./PERFORMANCE_TESTING.md) - Performance test procedures

### Module Documentation
- [QA_MODULE.md](../02-modules/QA_MODULE.md) - Functional QA checkpoints in pipeline

### DevOps Documentation
- [CICD_PIPELINE.md](../06-devops/CICD_PIPELINE.md) - CI/CD pipeline configuration
- [MONITORING_SETUP.md](../06-devops/MONITORING_SETUP.md) - Monitoring and alerting

### Architecture Documentation
- [SECURITY_ARCHITECTURE.md](../01-architecture/SECURITY_ARCHITECTURE.md) - Security design

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** QA Team
**Contact:** qa-team@your-domain.com
