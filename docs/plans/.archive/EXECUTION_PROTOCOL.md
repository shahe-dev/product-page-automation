# Execution Protocol

**Version:** 1.1
**Last Updated:** 2026-01-26
**Status:** Master Protocol

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Execution Checklist](#pre-execution-checklist)
3. [Pre-Phase Audit](#pre-phase-audit) **(NEW v1.1)**
4. [How to Read the Manifest](#how-to-read-the-manifest)
5. [Agent Execution Workflow](#agent-execution-workflow)
6. [Phase Execution Protocol](#phase-execution-protocol)
7. [Context Injection Protocol](#context-injection-protocol)
8. [QA Validation Protocol](#qa-validation-protocol) **(Updated v1.1 - Runtime Validation)**
9. [Quality Gate Protocol](#quality-gate-protocol)
10. [Handoff Protocol](#handoff-protocol)
11. [Escalation Protocol](#escalation-protocol)
12. [Artifact Management](#artifact-management)
13. [Example Execution Walkthrough](#example-execution-walkthrough)
14. [Troubleshooting](#troubleshooting)
15. [Post-Phase Integration Verification](#post-phase-integration-verification) **(NEW v1.1)**

---

## Overview

This protocol defines **exactly how to execute the multi-agent implementation plan** using the `EXECUTION_MANIFEST.json` as the single source of truth. Every agent, every phase, and every quality gate is defined in the manifest.

### Key Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| **Execution Manifest** | `docs/EXECUTION_MANIFEST.json` | Master registry of all agents, phases, dependencies, and documentation mappings |
| **Agent Briefs** | `docs/_agent-briefs/{phase}/` | Individual agent instructions |
| **Agent Outputs** | `docs/_agent-outputs/{agent-id}/` | Completed artifacts from agents |
| **Implementation Docs** | `docs/00-09/` | Source documentation for context injection |

### Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. LOAD MANIFEST                                                            │
│     └── Read docs/EXECUTION_MANIFEST.json                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  2. SELECT PHASE                                                             │
│     └── Identify current phase and its agents                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  3. CHECK DEPENDENCIES                                                       │
│     └── Verify all upstream dependencies are complete                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  4. LOAD AGENT BRIEF                                                         │
│     └── Read from docs/_agent-briefs/{phase}/{AGENT_ID}.md                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  5. INJECT CONTEXT                                                           │
│     └── Load documentation files listed in manifest                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  6. EXECUTE AGENT                                                            │
│     └── Agent produces outputs per acceptance criteria                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  7. QA VALIDATION                                                            │
│     └── Paired QA agent validates outputs                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  8. STORE ARTIFACTS                                                          │
│     └── Save to docs/_agent-outputs/{agent-id}/                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  9. QUALITY GATE                                                             │
│     └── When all phase agents complete, verify gate criteria                │
├─────────────────────────────────────────────────────────────────────────────┤
│  10. NEXT PHASE                                                              │
│      └── Proceed to dependent phases                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pre-Execution Checklist

Before starting any phase, verify:

- [ ] `EXECUTION_MANIFEST.json` is loaded and parsed
- [ ] All documentation files referenced in manifest exist
- [ ] Agent brief files exist for all agents in the phase
- [ ] Output directories exist: `docs/_agent-outputs/`
- [ ] Previous phase quality gates have passed (if applicable)
- [ ] No blocking issues from previous phases

---

## Pre-Phase Audit

**Purpose:** Prevent scope gaps discovered during integration testing.

Before launching any phase's agents, the orchestrator MUST audit agent briefs for completeness:

### 1. Deliverable Completeness Check

For each DEV agent in the phase:

```
FOR each agent IN phase.agents WHERE agent.type == "dev":
    expected_outputs = agent.outputs

    # Check for implicit dependencies
    IF agent creates migrations:
        VERIFY agent.outputs includes "alembic.ini" OR another agent creates it
        VERIFY agent.outputs includes "alembic/env.py" OR another agent creates it

    IF agent creates Python packages:
        VERIFY agent.outputs includes "__init__.py" files

    IF agent creates configuration:
        VERIFY agent.outputs includes all config files needed to RUN the code

    # Flag gaps
    IF gaps_found:
        EITHER update agent brief before execution
        OR document as orchestrator responsibility
END FOR
```

### 2. Runtime Dependency Check

Verify that agents produce everything needed to actually RUN their code:

| Code Type | Required Supporting Files |
|-----------|--------------------------|
| SQLAlchemy models | `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` |
| Python packages | `__init__.py` in each directory |
| FastAPI app | `main.py` with app factory |
| Configuration | `.env.example` with ALL variables |
| Docker services | `docker-compose.yml`, `Dockerfile` |

### 3. Gap Resolution Options

When gaps are found:

| Option | When to Use |
|--------|-------------|
| Update agent brief | Gap is within agent's domain |
| Create new agent | Gap requires specialized skills |
| Orchestrator task | Simple setup/config task |
| Document as manual | Requires credentials/secrets |

### 4. Pre-Phase Audit Report

Before launching agents, produce:

```markdown
## Pre-Phase Audit: {phase_name}

### Agents Reviewed
- [ ] {agent_id}: Deliverables complete
- [ ] {agent_id}: Missing {file} - Resolution: {action}

### Orchestrator Tasks Identified
1. {task}: {description}

### Audit Status: PASS / NEEDS_REMEDIATION
```

---

## How to Read the Manifest

### Manifest Structure

```json
{
  "documentation_registry": {
    "01-architecture": ["docs/01-architecture/SYSTEM_ARCHITECTURE.md", ...]
  },
  "orchestrators": [...],
  "phases": [
    {
      "id": "phase-0",
      "agents": [
        {
          "id": "DEV-DB-001",
          "brief": "docs/_agent-briefs/phase-0-foundation/DEV-DB-001.md",
          "documentation": {
            "primary": [...],
            "secondary": [...],
            "reference": [...]
          },
          "dependencies": [],
          "outputs": [...],
          "acceptance_criteria": [...]
        }
      ],
      "quality_gate": {...}
    }
  ]
}
```

### Finding an Agent's Information

To execute agent `DEV-AUTH-001`:

1. **Find the agent in the manifest:**
   ```
   phases → find phase where agents contains "DEV-AUTH-001"
   ```

2. **Get the brief location:**
   ```
   agent.brief = "docs/_agent-briefs/phase-1-backend-core/DEV-AUTH-001.md"
   ```

3. **Get documentation to inject:**
   ```
   agent.documentation.primary = [
     "docs/05-integrations/GOOGLE_OAUTH_SETUP.md",
     "docs/01-architecture/SECURITY_ARCHITECTURE.md"
   ]
   agent.documentation.secondary = [
     "docs/04-backend/API_ENDPOINTS.md",
     "docs/04-backend/ERROR_HANDLING.md"
   ]
   ```

4. **Get dependencies to verify:**
   ```
   agent.dependencies = ["DEV-DB-001", "DEV-CONFIG-001"]
   ```

5. **Get expected outputs:**
   ```
   agent.outputs = [
     "backend/app/services/auth_service.py",
     "backend/app/services/user_service.py",
     ...
   ]
   ```

---

## Agent Execution Workflow

### Step 1: Verify Dependencies

Before executing any agent, verify all dependencies are complete:

```
FOR each dependency_id IN agent.dependencies:
    IF NOT artifact_exists(dependency_id):
        BLOCK execution
        REPORT: "Dependency {dependency_id} not complete"
    END IF
END FOR
```

### Step 2: Load Agent Brief

Read the agent brief file:

```
brief_path = manifest.phases[phase].agents[agent].brief
brief_content = read_file(brief_path)
```

### Step 3: Inject Context

Compile the context package for the agent:

```markdown
# CONTEXT PACKAGE FOR {AGENT_ID}

## Part 1: Agent Brief
{brief_content}

## Part 2: Primary Documentation
{FOR EACH doc IN agent.documentation.primary:
    read_file(doc)
END FOR}

## Part 3: Secondary Documentation
{FOR EACH doc IN agent.documentation.secondary:
    read_file(doc)
END FOR}

## Part 4: Reference Documentation (if needed)
{FOR EACH doc IN agent.documentation.reference:
    read_file(doc)
END FOR}

## Part 5: Upstream Artifacts
{FOR EACH dep IN agent.dependencies:
    read_artifact(dep)
END FOR}
```

### Step 4: Execute Agent

Provide the context package to the agent and instruct:

```
You are {AGENT_ID}: {agent.name}

Your mission is defined in the brief above.

You must produce the following outputs:
{agent.outputs}

Your work will be validated against these criteria:
{agent.acceptance_criteria}

Begin execution.
```

### Step 5: Collect Outputs

After agent completes, collect all outputs:

```
FOR each output_path IN agent.outputs:
    IF file_exists(output_path):
        COPY to docs/_agent-outputs/{agent.id}/
    ELSE:
        FLAG as incomplete
    END IF
END FOR
```

---

## Phase Execution Protocol

### Phase Execution Order

```
Phase 0: Foundation
    └── DEV-DB-001 (parallel)
    └── DEV-CONFIG-001 (parallel)
    └── [QA agents validate]
    └── Quality Gate 0

Phase 1: Backend Core (depends on Phase 0)
    └── DEV-AUTH-001 (parallel)
    └── DEV-PROJECT-001 (parallel)
    └── DEV-JOB-001 (parallel)
    └── DEV-API-001 (depends on above)
    └── [QA agents validate]
    └── Quality Gate 1

Phase 2: Material Preparation (depends on Phase 1)
    └── DEV-PDF-001
    └── DEV-IMGCLASS-001 (depends on PDF)
    └── DEV-WATERMARK-001 (depends on IMGCLASS)
    └── DEV-FLOORPLAN-001 (depends on IMGCLASS; data dep on PDF's page_text_map)
    └── DEV-IMGOPT-001 (depends on WATERMARK, FLOORPLAN)
    └── [QA agents validate]
    └── Quality Gate 2

Phase 3: Content Generation (depends on Phase 1)
    └── DEV-EXTRACT-001
    └── DEV-STRUCT-001 (depends on EXTRACT)
    └── DEV-CONTENT-001 (depends on STRUCT)
    └── DEV-SHEETS-001 (depends on CONTENT)
    └── [QA agents validate]
    └── Quality Gate 3

Phase 4: Frontend (depends on Phase 1, parallel with 2 & 3)
    └── DEV-FESETUP-001
    └── DEV-AUTHUI-001 (depends on FESETUP)
    └── [Other frontend agents in parallel]
    └── [QA agents validate]
    └── Quality Gate 4

Phase 5: Integrations (depends on Phase 1)
    └── DEV-GCS-001 (parallel)
    └── DEV-GSHEETS-001 (parallel)
    └── DEV-DRIVE-001 (parallel)
    └── DEV-ANTHROPIC-001 (parallel)
    └── DEV-OAUTH-001 (parallel)
    └── [QA agents validate]
    └── Quality Gate 5

Phase 6: DevOps (depends on Phases 2-5)
    └── DEV-DOCKER-001
    └── DEV-CICD-001 (depends on DOCKER)
    └── DEV-CLOUDRUN-001 (depends on CICD)
    └── DEV-MONITORING-001 (depends on CLOUDRUN)
    └── [QA agents validate]
    └── Quality Gate 6

Testing Phase (depends on Phase 6)
    └── [All test agents in parallel]
    └── Final Quality Gate
```

### Parallel Execution Rules

Within a phase, agents can run in parallel if:
1. They have no dependencies on each other
2. Their combined context doesn't exceed memory limits
3. They don't produce conflicting outputs

```
Maximum parallel agents: 5 (configurable in manifest.execution_config)
```

---

## Context Injection Protocol

### Documentation Mapping Reference

| Domain | Documentation Files | Used By Agents |
|--------|--------------------|--------------------|
| **Prerequisites** | `docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md` | DEV-CONFIG-001 |
| | `docs/00-prerequisites/MULTI_AGENT_IMPLEMENTATION_PLAN.md` | All orchestrators |
| **Architecture** | `docs/01-architecture/SYSTEM_ARCHITECTURE.md` | All orchestrators, DEV-API-001 |
| | `docs/01-architecture/DATABASE_SCHEMA.md` | DEV-DB-001, DEV-PROJECT-001 |
| | `docs/01-architecture/API_DESIGN.md` | DEV-API-001, QA-API-001 |
| | `docs/01-architecture/SECURITY_ARCHITECTURE.md` | DEV-AUTH-001, DEV-OAUTH-001 |
| | `docs/01-architecture/DATA_FLOW.md` | DEV-JOB-001, DEV-PDF-001 |
| | `docs/01-architecture/INFRASTRUCTURE.md` | DEV-CLOUDRUN-001, DEV-MONITORING-001 |
| **Modules** | `docs/02-modules/PROJECT_DATABASE.md` | DEV-DB-001, DEV-PROJECT-001 |
| | `docs/02-modules/MATERIAL_PREPARATION.md` | DEV-PDF-001 through DEV-IMGOPT-001 |
| | `docs/02-modules/CONTENT_GENERATION.md` | DEV-EXTRACT-001 through DEV-SHEETS-001 |
| | `docs/02-modules/QA_MODULE.md` | DEV-CONTENT-001, DEV-QAPAGE-001 |
| | `docs/02-modules/APPROVAL_WORKFLOW.md` | DEV-WORKFLOW-001 |
| | `docs/02-modules/PUBLISHING_WORKFLOW.md` | DEV-WORKFLOW-001 |
| | `docs/02-modules/NOTIFICATIONS.md` | DEV-NOTIFY-001 |
| | `docs/02-modules/PROMPT_LIBRARY.md` | DEV-CONTENT-001, DEV-PROMPTS-001 |
| **Frontend** | `docs/03-frontend/COMPONENT_LIBRARY.md` | DEV-FESETUP-001, DEV-COMPONENTS-001 |
| | `docs/03-frontend/PAGE_SPECIFICATIONS.md` | All frontend page agents |
| | `docs/03-frontend/STATE_MANAGEMENT.md` | DEV-STATE-001, DEV-AUTHUI-001 |
| | `docs/03-frontend/ROUTING.md` | DEV-FESETUP-001 |
| | `docs/03-frontend/ACCESSIBILITY.md` | DEV-COMPONENTS-001, All QA-*-001 |
| **Backend** | `docs/04-backend/SERVICE_LAYER.md` | DEV-PROJECT-001, DEV-JOB-001 |
| | `docs/04-backend/API_ENDPOINTS.md` | DEV-API-001, All frontend agents |
| | `docs/04-backend/ERROR_HANDLING.md` | DEV-AUTH-001, DEV-API-001 |
| | `docs/04-backend/BACKGROUND_JOBS.md` | DEV-JOB-001 |
| | `docs/04-backend/CACHING_STRATEGY.md` | DEV-API-001 |
| **Integrations** | `docs/05-integrations/GOOGLE_CLOUD_SETUP.md` | DEV-GCS-001, DEV-CONFIG-001 |
| | `docs/05-integrations/GOOGLE_SHEETS_INTEGRATION.md` | DEV-SHEETS-001, DEV-GSHEETS-001 |
| | `docs/05-integrations/GOOGLE_OAUTH_SETUP.md` | DEV-AUTH-001, DEV-OAUTH-001 |
| | `docs/05-integrations/GOOGLE_DRIVE_INTEGRATION.md` | DEV-DRIVE-001 |
| | `docs/05-integrations/CLOUD_STORAGE_PATTERNS.md` | DEV-GCS-001, DEV-IMGOPT-001 |
| | `docs/05-integrations/ANTHROPIC_API_INTEGRATION.md` | DEV-ANTHROPIC-001, DEV-IMGCLASS-001, DEV-CONTENT-001 |
| **DevOps** | `docs/06-devops/LOCAL_DEVELOPMENT.md` | DEV-CONFIG-001, DEV-DOCKER-001 |
| | `docs/06-devops/CICD_PIPELINE.md` | DEV-CICD-001 |
| | `docs/06-devops/DEPLOYMENT_GUIDE.md` | DEV-CLOUDRUN-001 |
| | `docs/06-devops/MONITORING_SETUP.md` | DEV-MONITORING-001 |
| | `docs/06-devops/BACKUP_RECOVERY.md` | DEV-MONITORING-001 |
| **Testing** | `docs/07-testing/TEST_STRATEGY.md` | All TEST-* agents |
| | `docs/07-testing/UNIT_TEST_PATTERNS.md` | TEST-BACKEND-UNIT-001, TEST-FRONTEND-UNIT-001 |
| | `docs/07-testing/INTEGRATION_TESTS.md` | TEST-API-INT-001, TEST-FE-INT-001 |
| | `docs/07-testing/E2E_TEST_SCENARIOS.md` | TEST-E2E-001 |
| | `docs/07-testing/PERFORMANCE_TESTING.md` | TEST-PERF-001 |
| | `docs/07-testing/QA_MULTI_AGENT_SYSTEM.md` | All SYSQA-* agents, All QA-* agents |
| **User Guides** | `docs/08-user-guides/CONTENT_CREATOR_GUIDE.md` | DEV-UPLOAD-001, DEV-DASHBOARD-001 |
| | `docs/08-user-guides/MARKETING_MANAGER_GUIDE.md` | DEV-WORKFLOW-001, DEV-QAPAGE-001 |
| | `docs/08-user-guides/PUBLISHER_GUIDE.md` | DEV-WORKFLOW-001 |
| | `docs/08-user-guides/ADMIN_GUIDE.md` | DEV-PROMPTS-001 |
| | `docs/08-user-guides/DEVELOPER_GUIDE.md` | DEV-FESETUP-001 |
| **Reference** | `docs/09-reference/GLOSSARY.md` | All agents (as needed) |
| | `docs/09-reference/CHANGELOG.md` | DEV-CICD-001 |
| | `docs/09-reference/TROUBLESHOOTING.md` | DEV-MONITORING-001 |
| | `docs/09-reference/FAQ.md` | Documentation agents |

### Context Size Guidelines

```
Primary Documentation:   MUST READ    (~15,000-20,000 tokens)
Secondary Documentation: SHOULD READ  (~5,000-10,000 tokens)
Reference Documentation: MAY READ     (~2,000-5,000 tokens)
Upstream Artifacts:      MUST READ    (variable)
```

---

## QA Validation Protocol

### QA Agent Execution

After each development agent completes:

1. **Identify QA Pair:**
   ```
   qa_agent_id = dev_agent.qa_pair  // e.g., "QA-DB-001"
   ```

2. **Load QA Brief:**
   ```
   qa_brief = read_file(qa_agent.brief)
   ```

3. **Inject QA Context:**
   ```markdown
   # QA CONTEXT FOR {QA_AGENT_ID}

   ## QA Brief
   {qa_brief}

   ## Artifacts to Review
   {FOR EACH output IN dev_agent.outputs:
       read_file(output)
   END FOR}

   ## Validation Checklist
   {qa_agent.validation_checklist}

   ## Standards Reference
   {qa_agent.documentation}
   ```

4. **Execute QA Agent:**
   ```
   Review the artifacts above.
   Validate against the checklist.
   Return a QA report in the specified format.
   ```

5. **Collect QA Report:**
   ```json
   {
     "agent_id": "QA-DB-001",
     "reviewed_agent": "DEV-DB-001",
     "passed": true,
     "score": 92,
     "issues": [],
     "summary": "Schema meets all requirements..."
   }
   ```

### Runtime Validation Requirements

**IMPORTANT:** QA agents MUST perform runtime validation, not just structural review.

All QA agents must include these checks:

#### 1. Import Validation
```python
# QA agent must attempt:
try:
    from {module} import {exports}
    print("PASS: Imports resolve")
except ImportError as e:
    print(f"FAIL: Import error - {e}")
```

#### 2. Reserved Keyword Check
```python
# Check for SQLAlchemy/Pydantic reserved names
RESERVED_NAMES = ["metadata", "registry", "dict", "json", "schema"]
for model in models:
    for field in model.fields:
        if field.name in RESERVED_NAMES:
            report_issue("CRITICAL", f"{model}.{field} uses reserved name")
```

#### 3. Configuration Load Test
```python
# If agent produces configuration:
try:
    settings = Settings()  # or get_settings()
    print("PASS: Configuration loads")
except ValidationError as e:
    print(f"FAIL: Configuration validation - {e}")
```

#### 4. Async Engine Compatibility
```python
# If agent produces database code:
# Verify pool classes are async-compatible
# Verify no sync-only patterns used with async engine
```

#### 5. Migration Executability
```python
# If agent produces Alembic migrations:
# Verify alembic.ini exists
# Verify env.py exists and imports correctly
# Verify migration can be parsed (not necessarily executed)
```

### QA Validation Checklist Addendum

Every QA brief MUST include this section:

```markdown
## Runtime Validation (REQUIRED)

- [ ] All Python files import without errors
- [ ] No reserved keyword conflicts in models/schemas
- [ ] Configuration loads with test values
- [ ] Type hints are valid (mypy --ignore-missing-imports passes)
- [ ] No circular import issues
- [ ] Async patterns used correctly (no sync calls in async functions)
```

### QA Pass/Fail Criteria

| Severity | Pass Threshold |
|----------|---------------|
| Critical Issues | 0 allowed |
| High Issues | 0 allowed |
| Medium Issues | ≤ 3 allowed |
| Low Issues | ≤ 10 allowed |
| QA Score | ≥ 85% |
| **Runtime Validation** | **MUST PASS** |

---

## Quality Gate Protocol

### Gate Evaluation Process

When all agents in a phase complete:

1. **Collect All QA Reports:**
   ```
   qa_reports = []
   FOR EACH agent IN phase.agents:
       IF agent.type == "qa":
           qa_reports.append(agent.report)
       END IF
   END FOR
   ```

2. **Calculate Aggregate Score:**
   ```
   total_score = average(report.score FOR report IN qa_reports)
   total_critical = sum(report.critical_issues FOR report IN qa_reports)
   total_high = sum(report.high_issues FOR report IN qa_reports)
   ```

3. **Evaluate Against Gate Criteria:**
   ```
   gate_passed = (
       total_score >= phase.quality_gate.qa_score_minimum AND
       total_critical <= phase.quality_gate.blocking_issues_allowed.critical AND
       total_high <= phase.quality_gate.blocking_issues_allowed.high
   )
   ```

4. **Gate Decision:**
   ```
   IF gate_passed:
       UNLOCK next phase(s)
       NOTIFY: "Phase {phase.id} complete. Proceeding to {next_phases}"
   ELSE:
       BLOCK next phase(s)
       TRIGGER escalation
       NOTIFY: "Phase {phase.id} blocked. Issues: {issues}"
   END IF
   ```

### Gate Requirements by Phase

| Phase | Min QA Score | Critical | High | Test Coverage |
|-------|-------------|----------|------|---------------|
| Phase 0 | 85% | 0 | 0 | N/A |
| Phase 1 | 85% | 0 | 0 | 80% |
| Phase 2 | 85% | 0 | 0 | 80% |
| Phase 3 | 90% | 0 | 0 | 85% |
| Phase 4 | 85% | 0 | 0 | 70% |
| Phase 5 | 90% | 0 | 0 | 85% |
| Phase 6 | 90% | 0 | 0 | 75% |
| Testing | 95% | 0 | 0 | 80% |

---

## Handoff Protocol

### Development → QA Handoff

```yaml
handoff_package:
  from_agent: "DEV-DB-001"
  to_agent: "QA-DB-001"
  timestamp: "2026-01-15T10:30:00Z"
  artifacts:
    - path: "backend/alembic/versions/001_initial_schema.py"
      type: "migration"
      checksum: "sha256:abc123..."
    - path: "backend/app/models/database.py"
      type: "code"
      checksum: "sha256:def456..."
  completion_status: "complete"
  notes: "All 22 tables created. Migration tested up/down."
```

### Phase → Phase Handoff

```yaml
phase_handoff:
  from_phase: "phase-0"
  to_phases: ["phase-1"]
  timestamp: "2026-01-15T12:00:00Z"
  gate_status: "passed"
  gate_score: 91
  artifacts_produced:
    - "backend/alembic/versions/001_initial_schema.py"
    - "backend/app/models/database.py"
    - "backend/app/models/enums.py"
    - "backend/app/config/settings.py"
    - "backend/app/config/database.py"
    - "backend/.env.example"
    - "frontend/.env.local.example"
  interfaces_exported:
    - name: "Database Models"
      location: "backend/app/models/database.py"
      exports: ["User", "Project", "Job", "..."]
    - name: "Configuration"
      location: "backend/app/config/settings.py"
      exports: ["Settings", "get_settings"]
```

---

## Escalation Protocol

### Escalation Triggers

| Trigger | Severity | Action |
|---------|----------|--------|
| Agent fails after 3 retries | High | Notify Domain Orchestrator |
| Critical security issue | Critical | Immediate block + notify Master |
| Quality gate failure | High | Block phase + notify Master |
| Dependency timeout (>24h) | Medium | Escalate to Master |
| Resource contention | Low | Notify Domain Orchestrator |

### Escalation Path

```
Agent Failure
    ↓
Domain Orchestrator (15 min response)
    ↓
Master Orchestrator (30 min response)
    ↓
Human Intervention (as needed)
```

### Escalation Report Format

```json
{
  "escalation_id": "ESC-2026-001",
  "timestamp": "2026-01-15T14:30:00Z",
  "severity": "high",
  "source_agent": "DEV-AUTH-001",
  "source_phase": "phase-1",
  "issue": "Unable to implement OAuth flow - missing client credentials",
  "impact": "Blocks all downstream agents requiring authentication",
  "attempted_resolutions": [
    "Checked environment configuration",
    "Verified Secret Manager access"
  ],
  "recommended_action": "Verify Google Cloud Console OAuth setup per docs/00-prerequisites/EXTERNAL_SETUP_CHECKLIST.md",
  "blocking": true
}
```

---

## Artifact Management

### Directory Structure

```
docs/
├── _agent-briefs/
│   ├── phase-0-foundation/
│   │   ├── DEV-DB-001.md
│   │   ├── QA-DB-001.md
│   │   ├── DEV-CONFIG-001.md
│   │   └── QA-CONFIG-001.md
│   ├── phase-1-backend-core/
│   │   ├── DEV-AUTH-001.md
│   │   ├── QA-AUTH-001.md
│   │   └── ...
│   ├── phase-2-material-prep/
│   ├── phase-3-content-gen/
│   ├── phase-4-frontend/
│   ├── phase-5-integrations/
│   ├── phase-6-devops/
│   ├── testing/
│   ├── orchestrators/
│   └── system-qa/
│
├── _agent-outputs/
│   ├── DEV-DB-001/
│   │   ├── output-manifest.json
│   │   ├── 001_initial_schema.py
│   │   └── qa-report.json
│   ├── DEV-CONFIG-001/
│   └── ...
│
└── EXECUTION_MANIFEST.json
```

### Output Manifest Format

Each agent's output directory contains an `output-manifest.json`:

```json
{
  "agent_id": "DEV-DB-001",
  "execution_timestamp": "2026-01-15T10:30:00Z",
  "status": "complete",
  "outputs": [
    {
      "file": "001_initial_schema.py",
      "target": "backend/alembic/versions/001_initial_schema.py",
      "checksum": "sha256:abc123..."
    }
  ],
  "qa_status": {
    "reviewed_by": "QA-DB-001",
    "passed": true,
    "score": 92,
    "report": "qa-report.json"
  }
}
```

---

## Example Execution Walkthrough

### Executing Phase 0

**Step 1: Load Manifest**
```javascript
const manifest = JSON.parse(fs.readFileSync('docs/EXECUTION_MANIFEST.json'));
const phase0 = manifest.phases.find(p => p.id === 'phase-0');
```

**Step 2: Identify Agents**
```
Agents in Phase 0:
- DEV-DB-001 (dependencies: none)
- QA-DB-001 (dependencies: DEV-DB-001)
- DEV-CONFIG-001 (dependencies: none)
- QA-CONFIG-001 (dependencies: DEV-CONFIG-001)
```

**Step 3: Execute DEV-DB-001**
```
1. Load brief: docs/_agent-briefs/phase-0-foundation/DEV-DB-001.md
2. Load primary docs:
   - docs/01-architecture/DATABASE_SCHEMA.md
3. Load secondary docs:
   - docs/02-modules/PROJECT_DATABASE.md
   - docs/01-architecture/DATA_FLOW.md
   - docs/04-backend/SERVICE_LAYER.md
4. Execute agent with compiled context
5. Collect outputs to docs/_agent-outputs/DEV-DB-001/
```

**Step 4: Execute QA-DB-001**
```
1. Load brief: docs/_agent-briefs/phase-0-foundation/QA-DB-001.md
2. Load artifacts from DEV-DB-001
3. Load QA standards: docs/07-testing/QA_MULTI_AGENT_SYSTEM.md
4. Execute QA validation
5. Collect QA report
```

**Step 5: (Parallel) Execute DEV-CONFIG-001 and QA-CONFIG-001**

**Step 6: Quality Gate Evaluation**
```
Collect QA reports from QA-DB-001 and QA-CONFIG-001
Calculate aggregate score
Verify against phase.quality_gate
If passed: Unlock Phase 1
If failed: Escalate
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Agent can't find documentation | Path mismatch | Verify paths in manifest match actual file locations |
| Dependency not found | Previous agent incomplete | Check _agent-outputs for dependency artifacts |
| QA score too low | Multiple validation failures | Review QA report, fix issues, re-run dev agent |
| Context overflow | Too much documentation | Prioritize primary docs, summarize secondary |
| Quality gate blocked | Critical issues found | Resolve all critical/high issues before retry |

### Debugging Commands

**Verify manifest paths:**
```bash
# Check all documentation files exist
cat docs/EXECUTION_MANIFEST.json | jq -r '.phases[].agents[].documentation.primary[]' | while read path; do
  [ -f "$path" ] && echo "OK: $path" || echo "MISSING: $path"
done
```

**Check agent brief existence:**
```bash
# Verify all agent briefs exist
cat docs/EXECUTION_MANIFEST.json | jq -r '.phases[].agents[].brief' | while read path; do
  [ -f "$path" ] && echo "OK: $path" || echo "MISSING: $path"
done
```

**View phase status:**
```bash
# List all phases and their agents
cat docs/EXECUTION_MANIFEST.json | jq '.phases[] | {id, name, agent_count: .agents | length}'
```

---

## Quick Reference Card

### Agent Execution Checklist

```
[ ] 1. Find agent in EXECUTION_MANIFEST.json
[ ] 2. Verify all dependencies complete
[ ] 3. Load agent brief from docs/_agent-briefs/{phase}/{agent-id}.md
[ ] 4. Load documentation from agent.documentation.primary[]
[ ] 5. Load secondary documentation if needed
[ ] 6. Load upstream artifacts from dependencies
[ ] 7. Compile context package
[ ] 8. Execute agent
[ ] 9. Collect outputs
[ ] 10. Trigger paired QA agent
[ ] 11. Collect QA report
[ ] 12. Store artifacts in docs/_agent-outputs/{agent-id}/
[ ] 13. Update execution status
```

### Phase Completion Checklist

```
[ ] All dev agents in phase complete
[ ] All QA agents validated outputs (including runtime validation)
[ ] All QA reports collected
[ ] Aggregate QA score calculated
[ ] Quality gate criteria met
[ ] Artifacts stored and documented
[ ] Handoff package prepared
[ ] Next phase(s) unlocked
```

---

## Post-Phase Integration Verification

**Purpose:** Verify that phase outputs actually work before proceeding.

After quality gate passes but BEFORE unlocking next phase, the orchestrator performs integration verification.

### Responsibility Matrix

| Task Type | Responsible Party | Example |
|-----------|-------------------|---------|
| Code creation | DEV Agent | Create `settings.py` |
| Code validation | QA Agent | Verify imports, no reserved keywords |
| Environment setup | Orchestrator | Create `.env`, install dependencies |
| Integration test | Orchestrator | Start server, verify endpoints |
| Credential management | Manual/User | Provide API keys, secrets |

### Integration Verification Steps

#### Phase 0 Verification
```bash
# 1. Environment setup (Orchestrator)
cd backend
python -m venv venv
pip install -r requirements.txt

# 2. Create .env from .env.example (Orchestrator + User for secrets)
cp .env.example .env
# User provides actual credentials

# 3. Database setup (Orchestrator)
docker-compose up -d  # Start PostgreSQL
alembic upgrade head  # Run migrations

# 4. Smoke test (Orchestrator)
python -c "from app.config.settings import get_settings; get_settings()"
python -c "from app.models.database import Base, User, Project"
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
curl http://127.0.0.1:8000/health
```

#### Phase 1 Verification
```bash
# 1. Import verification
python -c "from app.services.auth_service import AuthService"
python -c "from app.services.project_service import ProjectService"

# 2. API route verification
curl http://127.0.0.1:8000/api/v1/auth/login
curl http://127.0.0.1:8000/api/v1/projects

# 3. Run tests
pytest tests/ -v
```

### Integration Verification Report

```markdown
## Integration Verification: {phase_name}

### Environment Setup
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Environment variables configured

### Smoke Tests
- [ ] Configuration loads without errors
- [ ] Database connection successful
- [ ] Server starts without errors
- [ ] Health endpoint responds

### Issues Found During Integration
| Issue | Severity | Resolution |
|-------|----------|------------|
| {description} | {critical/high/medium/low} | {fix applied} |

### Verification Status: PASS / FAIL
```

### When Integration Fails

If integration verification finds issues:

1. **Categorize the issue:**
   - QA gap (should have been caught) -> Update QA brief
   - Missing deliverable (not in agent scope) -> Update DEV brief or add orchestrator task
   - Environment issue (credentials, setup) -> Document as manual step

2. **Fix and document:**
   - Apply fix
   - Update relevant documentation
   - Add to "lessons learned" for future phases

3. **Re-verify:**
   - Run integration verification again
   - Only proceed when all checks pass

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Development Team
**Contact:** dev-team@your-domain.com
