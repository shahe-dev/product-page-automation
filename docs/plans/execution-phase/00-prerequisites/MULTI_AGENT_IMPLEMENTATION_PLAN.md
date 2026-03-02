# Multi-Agent Implementation Plan

**Version:** 1.0
**Last Updated:** 2026-01-15
**Owner:** Development Team
**Status:** Master Plan

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Agent Architecture Philosophy](#agent-architecture-philosophy)
3. [Agent Taxonomy](#agent-taxonomy)
4. [Orchestration Hierarchy](#orchestration-hierarchy)
5. [Context Memory Optimization](#context-memory-optimization)
6. [Phase 0: Foundation Agents](#phase-0-foundation-agents)
7. [Phase 1: Backend Core Agents](#phase-1-backend-core-agents)
8. [Phase 2: Material Preparation Agents](#phase-2-material-preparation-agents)
9. [Phase 3: Content Generation Agents](#phase-3-content-generation-agents)
10. [Phase 4: Frontend Agents](#phase-4-frontend-agents)
11. [Phase 5: Integration Agents](#phase-5-integration-agents)
12. [Phase 6: DevOps Agents](#phase-6-devops-agents)
13. [QA Agent Layer](#qa-agent-layer)
14. [Testing Agent Layer](#testing-agent-layer)
15. [Orchestrator Agent Specifications](#orchestrator-agent-specifications)
16. [Inter-Agent Communication Protocol](#inter-agent-communication-protocol)
17. [Execution Timeline](#execution-timeline)
18. [Quality Gates & Checkpoints](#quality-gates--checkpoints)
19. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

This document defines a **hierarchical multi-agent system** for building PDP Automation v.3 with maximum efficiency, quality, and context utilization. The architecture employs:

- **42 Specialized Development Agents** - Domain experts for each component
- **14 QA Agents** - Quality enforcement at every layer
- **8 Testing Agents** - Comprehensive test coverage
- **6 Orchestrator Agents** - Coordination and oversight
- **1 Master Orchestrator** - System-wide coordination

**Total: 71 Agents** organized in a 4-tier hierarchy

### Key Design Principles

1. **Single Responsibility** - Each agent owns one domain completely
2. **Bounded Context** - Agents receive only relevant context (~50-80K tokens max)
3. **Layered QA** - Every development agent has a paired QA agent
4. **Hierarchical Orchestration** - Clear chain of command and escalation
5. **Parallel Execution** - Independent agents run concurrently
6. **Checkpoint Gates** - Quality verification before phase transitions

---

## Agent Architecture Philosophy

### Context Memory Optimization Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT ALLOCATION STRATEGY                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 1: Master Orchestrator (100K context)                                  │
│  ├── System-wide state awareness                                            │
│  ├── Phase transition decisions                                             │
│  ├── Cross-domain conflict resolution                                       │
│  └── Final quality gate approval                                            │
│                                                                              │
│  TIER 2: Domain Orchestrators (80K context each)                            │
│  ├── Backend Orchestrator                                                   │
│  ├── Frontend Orchestrator                                                  │
│  ├── Integration Orchestrator                                               │
│  ├── DevOps Orchestrator                                                    │
│  ├── QA Orchestrator                                                        │
│  └── Testing Orchestrator                                                   │
│                                                                              │
│  TIER 3: Specialized Development Agents (50-60K context each)               │
│  ├── Focused on single module/component                                     │
│  ├── Deep domain knowledge                                                  │
│  └── Paired with QA agent                                                   │
│                                                                              │
│  TIER 4: QA & Testing Agents (40-50K context each)                          │
│  ├── Review artifacts from development agents                               │
│  ├── Validation against standards                                           │
│  └── Report to orchestrators                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Optimal Agent Sizing

| Agent Type | Context Budget | Rationale |
|------------|---------------|-----------|
| Master Orchestrator | 100K tokens | Needs full system awareness |
| Domain Orchestrator | 80K tokens | Domain-wide coordination |
| Development Agent | 50-60K tokens | Deep focus on single component |
| QA Agent | 40-50K tokens | Review + standards comparison |
| Testing Agent | 40-50K tokens | Test specs + code under test |

### Context Injection Strategy

Each agent receives:
1. **Static Context** (~10K) - Project standards, conventions, architecture overview
2. **Domain Context** (~20K) - Relevant documentation for their domain
3. **Task Context** (~15K) - Specific files and dependencies for current task
4. **Working Space** (~15K) - Room for reasoning and output generation

---

## Agent Taxonomy

### Complete Agent Registry

```
MASTER_ORCHESTRATOR
│
├── BACKEND_ORCHESTRATOR
│   ├── DEV_AGENT: Database Schema Agent
│   │   └── QA_AGENT: Database Schema QA
│   ├── DEV_AGENT: Auth Service Agent
│   │   └── QA_AGENT: Auth QA
│   ├── DEV_AGENT: Project Service Agent
│   │   └── QA_AGENT: Project Service QA
│   ├── DEV_AGENT: Job Manager Agent
│   │   └── QA_AGENT: Job Manager QA
│   ├── DEV_AGENT: API Routes Agent
│   │   └── QA_AGENT: API Routes QA
│   ├── DEV_AGENT: PDF Processor Agent
│   │   └── QA_AGENT: PDF Processor QA
│   ├── DEV_AGENT: Image Classifier Agent
│   │   └── QA_AGENT: Image Classifier QA
│   ├── DEV_AGENT: Watermark Agent
│   │   └── QA_AGENT: Watermark QA
│   ├── DEV_AGENT: Floor Plan Agent
│   │   └── QA_AGENT: Floor Plan QA
│   ├── DEV_AGENT: Image Optimizer Agent
│   │   └── QA_AGENT: Image Optimizer QA
│   ├── DEV_AGENT: Content Generator Agent
│   │   └── QA_AGENT: Content Generator QA
│   ├── DEV_AGENT: Sheets Manager Agent
│   │   └── QA_AGENT: Sheets Manager QA
│   └── DEV_AGENT: Notification Agent
│       └── QA_AGENT: Notification QA
│
├── FRONTEND_ORCHESTRATOR
│   ├── DEV_AGENT: Project Setup Agent
│   │   └── QA_AGENT: Setup QA
│   ├── DEV_AGENT: Auth UI Agent
│   │   └── QA_AGENT: Auth UI QA
│   ├── DEV_AGENT: Dashboard Agent
│   │   └── QA_AGENT: Dashboard QA
│   ├── DEV_AGENT: Upload UI Agent
│   │   └── QA_AGENT: Upload UI QA
│   ├── DEV_AGENT: Project Detail Agent
│   │   └── QA_AGENT: Project Detail QA
│   ├── DEV_AGENT: QA Page Agent
│   │   └── QA_AGENT: QA Page QA
│   ├── DEV_AGENT: Prompts Page Agent
│   │   └── QA_AGENT: Prompts Page QA
│   ├── DEV_AGENT: Workflow Page Agent
│   │   └── QA_AGENT: Workflow Page QA
│   ├── DEV_AGENT: Shared Components Agent
│   │   └── QA_AGENT: Components QA
│   └── DEV_AGENT: State Management Agent
│       └── QA_AGENT: State QA
│
├── INTEGRATION_ORCHESTRATOR
│   ├── DEV_AGENT: GCS Integration Agent
│   │   └── QA_AGENT: GCS QA
│   ├── DEV_AGENT: Google Sheets Agent
│   │   └── QA_AGENT: Sheets QA
│   ├── DEV_AGENT: Google Drive Agent
│   │   └── QA_AGENT: Drive QA
│   ├── DEV_AGENT: Anthropic Integration Agent
│   │   └── QA_AGENT: Anthropic QA
│   └── DEV_AGENT: OAuth Integration Agent
│       └── QA_AGENT: OAuth QA
│
├── DEVOPS_ORCHESTRATOR
│   ├── DEV_AGENT: Docker Agent
│   │   └── QA_AGENT: Docker QA
│   ├── DEV_AGENT: CI/CD Agent
│   │   └── QA_AGENT: CI/CD QA
│   ├── DEV_AGENT: Cloud Run Agent
│   │   └── QA_AGENT: Deployment QA
│   └── DEV_AGENT: Monitoring Agent
│       └── QA_AGENT: Monitoring QA
│
├── QA_ORCHESTRATOR
│   ├── CODE_QA_AGENT: Code Quality Agent
│   ├── SECURITY_QA_AGENT: Security Agent
│   ├── INTEGRATION_QA_AGENT: Integration Agent
│   ├── PERFORMANCE_QA_AGENT: Performance Agent
│   ├── DOCUMENTATION_QA_AGENT: Documentation Agent
│   ├── DEPENDENCY_QA_AGENT: Dependency Agent
│   └── ESCALATION_AGENT: Escalation Agent
│
└── TESTING_ORCHESTRATOR
    ├── TEST_AGENT: Backend Unit Test Agent
    ├── TEST_AGENT: Frontend Unit Test Agent
    ├── TEST_AGENT: API Integration Test Agent
    ├── TEST_AGENT: Frontend Integration Test Agent
    ├── TEST_AGENT: E2E Test Agent
    ├── TEST_AGENT: Performance Test Agent
    ├── TEST_AGENT: Security Test Agent
    └── TEST_AGENT: Visual Regression Test Agent
```

---

## Orchestration Hierarchy

### Tier 1: Master Orchestrator

```yaml
MASTER_ORCHESTRATOR:
  id: "ORCH-MASTER-001"
  context_budget: 100000
  responsibilities:
    - System-wide coordination
    - Phase transition approval
    - Cross-domain conflict resolution
    - Final quality gate decisions
    - Resource allocation
    - Timeline management
    - Escalation handling

  inputs:
    - Phase completion reports from Domain Orchestrators
    - Quality gate results from QA Orchestrator
    - Test coverage reports from Testing Orchestrator
    - Risk assessments

  outputs:
    - Phase transition commands
    - Resource reallocation directives
    - Escalation resolutions
    - Final approvals

  decision_authority:
    - Approve phase transitions
    - Override quality gate failures (with justification)
    - Resolve inter-domain conflicts
    - Allocate additional agents to bottlenecks
```

### Tier 2: Domain Orchestrators

```yaml
BACKEND_ORCHESTRATOR:
  id: "ORCH-BACKEND-001"
  context_budget: 80000
  domain: "Backend Development"
  subordinate_agents: 13
  responsibilities:
    - Coordinate all backend development agents
    - Manage dependencies between backend components
    - Ensure API contract consistency
    - Monitor backend QA results
    - Report phase completion to Master

  context_injection:
    static:
      - docs/04-backend/BACKEND_OVERVIEW.md
      - docs/01-architecture/SYSTEM_ARCHITECTURE.md
      - docs/01-architecture/DATA_FLOW.md
    dynamic:
      - Current phase requirements
      - Dependency status from other domains
      - QA reports for backend agents

FRONTEND_ORCHESTRATOR:
  id: "ORCH-FRONTEND-001"
  context_budget: 80000
  domain: "Frontend Development"
  subordinate_agents: 10
  responsibilities:
    - Coordinate all frontend development agents
    - Ensure UI/UX consistency
    - Manage component dependencies
    - Monitor frontend QA results
    - Sync with Backend Orchestrator on API contracts

  context_injection:
    static:
      - docs/03-frontend/FRONTEND_OVERVIEW.md
      - docs/03-frontend/COMPONENT_LIBRARY.md
      - docs/03-frontend/STATE_MANAGEMENT.md
    dynamic:
      - API contract updates from Backend
      - Design system updates
      - QA reports for frontend agents

INTEGRATION_ORCHESTRATOR:
  id: "ORCH-INTEGRATION-001"
  context_budget: 80000
  domain: "External Integrations"
  subordinate_agents: 5
  responsibilities:
    - Coordinate external service integrations
    - Manage API rate limits and quotas
    - Ensure integration testing
    - Monitor external service health

  context_injection:
    static:
      - docs/05-integrations/GOOGLE_CLOUD_SETUP.md
      - docs/05-integrations/ANTHROPIC_API_INTEGRATION.md
      - docs/05-integrations/SHEETS_INTEGRATION.md
    dynamic:
      - API availability status
      - Rate limit usage
      - Integration test results

DEVOPS_ORCHESTRATOR:
  id: "ORCH-DEVOPS-001"
  context_budget: 80000
  domain: "DevOps & Deployment"
  subordinate_agents: 4
  responsibilities:
    - Coordinate infrastructure setup
    - Manage CI/CD pipeline
    - Oversee deployment processes
    - Monitor system health

  context_injection:
    static:
      - docs/06-devops/CICD_PIPELINE.md
      - docs/06-devops/DEPLOYMENT_GUIDE.md
      - docs/06-devops/MONITORING_SETUP.md
    dynamic:
      - Build status
      - Deployment logs
      - Health check results

QA_ORCHESTRATOR:
  id: "ORCH-QA-001"
  context_budget: 80000
  domain: "Quality Assurance"
  subordinate_agents: 7
  responsibilities:
    - Coordinate all QA agents
    - Aggregate quality metrics
    - Manage quality gates
    - Escalate critical issues

  context_injection:
    static:
      - docs/07-testing/QA_MULTI_AGENT_SYSTEM.md
      - docs/07-testing/TEST_STRATEGY.md
    dynamic:
      - Current QA results
      - Quality gate status
      - Escalation queue

TESTING_ORCHESTRATOR:
  id: "ORCH-TESTING-001"
  context_budget: 80000
  domain: "Testing"
  subordinate_agents: 8
  responsibilities:
    - Coordinate all testing agents
    - Manage test coverage targets
    - Aggregate test results
    - Report coverage gaps

  context_injection:
    static:
      - docs/07-testing/TEST_STRATEGY.md
      - docs/07-testing/UNIT_TEST_PATTERNS.md
      - docs/07-testing/INTEGRATION_TESTS.md
    dynamic:
      - Test execution status
      - Coverage reports
      - Failed test analysis
```

---

## Context Memory Optimization

### Agent Context Template

Each agent receives a standardized context package:

```markdown
# AGENT CONTEXT PACKAGE

## Section 1: Identity & Mission (500 tokens)
- Agent ID
- Role description
- Responsibilities
- Success criteria
- Reporting chain

## Section 2: Project Standards (2,000 tokens)
- Code style guide
- Naming conventions
- File structure
- Error handling patterns
- Documentation requirements

## Section 3: Domain Documentation (15,000-25,000 tokens)
- Relevant module docs
- API specifications
- Database schemas
- Integration guides

## Section 4: Dependencies (5,000 tokens)
- Upstream dependencies (what this agent needs)
- Downstream dependencies (what needs this agent's output)
- Interface contracts

## Section 5: Current Task (10,000-15,000 tokens)
- Specific files to create/modify
- Acceptance criteria
- Test requirements
- Related tickets/issues

## Section 6: Working Space (15,000-20,000 tokens)
- Reserved for agent reasoning
- Code generation
- Output artifacts
```

### Context Injection by Phase

```yaml
phase_0_foundation:
  agents: [Database_Agent, Config_Agent]
  shared_context:
    - docs/00-prerequisites/
    - docs/01-architecture/DATABASE_SCHEMA.md
  max_context_per_agent: 50000

phase_1_backend_core:
  agents: [Auth_Agent, Project_Agent, Job_Agent, API_Agent]
  shared_context:
    - docs/04-backend/
    - Phase 0 outputs (schema files, config)
  max_context_per_agent: 55000

phase_2_material_prep:
  agents: [PDF_Agent, Image_Agent, Watermark_Agent, FloorPlan_Agent, Optimizer_Agent]
  shared_context:
    - docs/02-modules/MATERIAL_PREPARATION.md
    - Phase 1 outputs (services interfaces)
  max_context_per_agent: 60000

phase_3_content_gen:
  agents: [Extractor_Agent, Structurer_Agent, Generator_Agent, Sheets_Agent]
  shared_context:
    - docs/02-modules/CONTENT_GENERATION.md
    - Brand guidelines context
  max_context_per_agent: 60000

phase_4_frontend:
  agents: [Setup_Agent, Auth_UI_Agent, Dashboard_Agent, ...]
  shared_context:
    - docs/03-frontend/
    - API contracts from Phase 1
  max_context_per_agent: 55000

phase_5_integration:
  agents: [GCS_Agent, Sheets_Agent, Drive_Agent, Anthropic_Agent, OAuth_Agent]
  shared_context:
    - docs/05-integrations/
    - Service interfaces from Phase 1-3
  max_context_per_agent: 50000

phase_6_devops:
  agents: [Docker_Agent, CICD_Agent, CloudRun_Agent, Monitoring_Agent]
  shared_context:
    - docs/06-devops/
    - Full codebase structure
  max_context_per_agent: 60000
```

---

## Phase 0: Foundation Agents

### 0.1 Database Schema Agent

```yaml
AGENT:
  id: "DEV-DB-001"
  name: "Database Schema Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Design and implement the complete PostgreSQL database schema
    including all 22 tables, indexes, constraints, and migrations.

  inputs:
    - docs/01-architecture/DATABASE_SCHEMA.md
    - docs/02-modules/*.md (data requirements)
    - docs/04-backend/MODELS_SCHEMAS.md

  outputs:
    - backend/alembic/versions/001_initial_schema.py
    - backend/app/models/database.py (SQLAlchemy models)
    - backend/app/models/enums.py
    - Database documentation

  acceptance_criteria:
    - All 22 tables created with correct columns
    - Foreign key relationships defined
    - Indexes for performance
    - JSONB fields for flexible data
    - Audit columns (created_at, updated_at)
    - Soft delete support (is_active)

  qa_pair: "QA-DB-001"

  dependencies:
    upstream: []
    downstream: [Auth_Agent, Project_Agent, Job_Agent]

QA_AGENT:
  id: "QA-DB-001"
  name: "Database Schema QA"
  type: "QA"
  context_budget: 40000

  mission: |
    Validate database schema against requirements, check for
    normalization issues, verify indexes, and ensure data integrity.

  validation_checklist:
    - Schema matches documentation requirements
    - All foreign keys have indexes
    - Naming conventions followed (snake_case)
    - Appropriate data types selected
    - Constraints properly defined
    - Migration is reversible
    - No N+1 query risks in relationships
```

### 0.2 Configuration Agent

```yaml
AGENT:
  id: "DEV-CONFIG-001"
  name: "Configuration Agent"
  type: "Development"
  context_budget: 45000

  mission: |
    Set up project configuration including environment variables,
    settings management, and secret handling.

  inputs:
    - docs/00-prerequisites/ENVIRONMENT_SETUP.md
    - docs/06-devops/LOCAL_DEVELOPMENT.md

  outputs:
    - backend/app/config/settings.py
    - backend/app/config/database.py
    - backend/.env.example
    - frontend/.env.local.example

  acceptance_criteria:
    - Pydantic BaseSettings for config
    - Secret Manager integration for production
    - Environment-specific configurations
    - Validation for required variables

  qa_pair: "QA-CONFIG-001"
```

---

## Phase 1: Backend Core Agents

### 1.1 Auth Service Agent

```yaml
AGENT:
  id: "DEV-AUTH-001"
  name: "Auth Service Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement complete authentication system including Google OAuth,
    JWT tokens, refresh tokens, and RBAC authorization.

  inputs:
    - docs/05-integrations/GOOGLE_OAUTH_SETUP.md
    - docs/01-architecture/SECURITY_ARCHITECTURE.md
    - docs/04-backend/API_ENDPOINTS.md (auth section)

  outputs:
    - backend/app/services/auth_service.py
    - backend/app/middleware/auth.py
    - backend/app/middleware/permissions.py
    - backend/app/api/routes/auth.py

  acceptance_criteria:
    - Google OAuth flow working
    - JWT generation and validation
    - Refresh token mechanism
    - Domain restriction (@your-domain.com only)
    - Role-based access control
    - Token blacklisting for logout

  qa_pair: "QA-AUTH-001"

  dependencies:
    upstream: [Database_Agent, Config_Agent]
    downstream: [All API routes]

QA_AGENT:
  id: "QA-AUTH-001"
  name: "Auth Service QA"
  type: "QA"
  context_budget: 45000

  validation_checklist:
    - OWASP authentication guidelines compliance
    - Token expiry correctly implemented
    - No hardcoded secrets
    - Domain validation working
    - Password/secret entropy requirements met
    - Rate limiting on auth endpoints
    - Audit logging for auth events
```

### 1.2 Project Service Agent

```yaml
AGENT:
  id: "DEV-PROJECT-001"
  name: "Project Service Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement complete project CRUD operations with search,
    filtering, pagination, revision tracking, and custom fields.

  inputs:
    - docs/02-modules/PROJECT_DATABASE.md
    - docs/04-backend/API_ENDPOINTS.md (projects section)
    - Database schema from Phase 0

  outputs:
    - backend/app/services/project_service.py
    - backend/app/repositories/project_repository.py
    - backend/app/api/routes/projects.py
    - backend/app/models/schemas.py (project schemas)

  acceptance_criteria:
    - Full CRUD operations
    - Search with full-text indexing
    - Multi-field filtering
    - Pagination with consistent format
    - Revision tracking (all changes logged)
    - Custom field support
    - Soft deletion

  qa_pair: "QA-PROJECT-001"
```

### 1.3 Job Manager Agent

```yaml
AGENT:
  id: "DEV-JOB-001"
  name: "Job Manager Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement async job processing system with progress tracking,
    error handling, retry logic, and Cloud Tasks integration.

  inputs:
    - docs/02-modules/WORKFLOW_ENGINE.md
    - docs/04-backend/BACKGROUND_TASKS.md
    - docs/05-integrations/CLOUD_TASKS_SETUP.md

  outputs:
    - backend/app/services/job_manager.py
    - backend/app/repositories/job_repository.py
    - backend/app/background/task_queue.py
    - backend/app/api/routes/jobs.py

  acceptance_criteria:
    - Job lifecycle management (pending → processing → completed/failed)
    - Progress tracking (steps completed, current step)
    - Error handling with retry (3 attempts, exponential backoff)
    - Cloud Tasks integration
    - Job cancellation support
    - Webhook callbacks (optional)

  qa_pair: "QA-JOB-001"
```

### 1.4 API Routes Agent

```yaml
AGENT:
  id: "DEV-API-001"
  name: "API Routes Agent"
  type: "Development"
  context_budget: 60000

  mission: |
    Implement all API route handlers with proper validation,
    error handling, and OpenAPI documentation.

  inputs:
    - docs/04-backend/API_ENDPOINTS.md
    - docs/04-backend/API_DESIGN.md
    - docs/09-reference/API_REFERENCE.md

  outputs:
    - backend/app/api/routes/*.py (all route files)
    - backend/app/api/dependencies.py
    - backend/app/models/schemas.py (request/response schemas)
    - OpenAPI documentation

  acceptance_criteria:
    - All endpoints from spec implemented
    - Pydantic validation on all inputs
    - Consistent error response format
    - OpenAPI/Swagger documentation
    - Rate limiting integration
    - Audit logging integration

  qa_pair: "QA-API-001"
```

---

## Phase 2: Material Preparation Agents

### 2.1 PDF Processor Agent

```yaml
AGENT:
  id: "DEV-PDF-001"
  name: "PDF Processor Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement PDF image extraction using PyMuPDF with
    high-quality preservation and efficient processing.

  inputs:
    - docs/02-modules/MATERIAL_PREPARATION.md
    - docs/02-modules/PDF_PROCESSING.md

  outputs:
    - backend/app/services/pdf_processor.py
    - backend/app/utils/pdf_helpers.py

  acceptance_criteria:
    - Extract all images from PDF
    - Preserve original resolution
    - Handle multi-page PDFs
    - Error handling for corrupted files
    - Memory-efficient streaming for large files
    - Return image metadata (page, format, dimensions)

  qa_pair: "QA-PDF-001"
```

### 2.2 Image Classifier Agent

```yaml
AGENT:
  id: "DEV-IMGCLASS-001"
  name: "Image Classifier Agent"
  type: "Development"
  context_budget: 60000

  mission: |
    Implement Claude Sonnet 4.5 vision-based image classification into
    5 categories with confidence scoring and alt text generation.

  inputs:
    - docs/02-modules/MATERIAL_PREPARATION.md (classification section)
    - docs/05-integrations/ANTHROPIC_API_INTEGRATION.md

  outputs:
    - backend/app/services/image_classifier.py

  acceptance_criteria:
    - Classify into: interior, exterior, amenity, logo, other
    - Confidence scores (0.0-1.0)
    - Classification reasoning
    - Batch processing (10-20 parallel)
    - SEO alt text generation
    - Apply category limits
    - Graceful error handling

  qa_pair: "QA-IMGCLASS-001"
```

### 2.3 Watermark Agent

```yaml
AGENT:
  id: "DEV-WATERMARK-001"
  name: "Watermark Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement watermark detection using Claude Sonnet 4.5 vision and
    removal using OpenCV inpainting.

  inputs:
    - docs/02-modules/MATERIAL_PREPARATION.md (watermark section)

  outputs:
    - backend/app/services/watermark_detector.py
    - backend/app/services/watermark_remover.py

  acceptance_criteria:
    - Detect watermark presence
    - Extract bounding box coordinates
    - OpenCV inpainting removal
    - Quality validation post-removal
    - Fallback to original if quality drops
    - Store quality metrics

  qa_pair: "QA-WATERMARK-001"
```

### 2.4 Floor Plan Agent

```yaml
AGENT:
  id: "DEV-FLOORPLAN-001"
  name: "Floor Plan Agent"
  type: "Development"
  context_budget: 60000

  mission: |
    Implement floor plan extraction, structured data parsing,
    and deduplication with perceptual hashing.

  inputs:
    - docs/02-modules/MATERIAL_PREPARATION.md (floor plan section)

  outputs:
    - backend/app/services/floor_plan_extractor.py
    - backend/app/services/deduplication_service.py

  acceptance_criteria:
    - Identify floor plan images
    - Extract: unit type, bedrooms, bathrooms, sqft, features
    - Perceptual hash calculation
    - Duplicate detection (95% similarity)
    - Select highest quality per unit type
    - Store in JSONB format

  qa_pair: "QA-FLOORPLAN-001"
```

### 2.5 Image Optimizer Agent

```yaml
AGENT:
  id: "DEV-IMGOPT-001"
  name: "Image Optimizer Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Implement image optimization including resizing, format
    conversion, compression, and quality validation.

  inputs:
    - docs/02-modules/MATERIAL_PREPARATION.md (optimization section)

  outputs:
    - backend/app/services/image_optimizer.py
    - backend/app/services/output_organizer.py

  acceptance_criteria:
    - Resize to max 2450x1400px (maintain aspect)
    - Set DPI to 300
    - Convert to WebP (85% quality)
    - Convert to JPG (90% fallback)
    - Dual-tier output: Tier 1 (original quality), Tier 2 (LLM-optimized 1568px max)
    - Batch parallel processing
    - Create organized ZIP structure

  qa_pair: "QA-IMGOPT-001"
```

---

## Phase 3: Content Generation Agents

### 3.1 Text Extractor Agent

```yaml
AGENT:
  id: "DEV-EXTRACT-001"
  name: "Text Extractor Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Implement cost-efficient text extraction from PDFs using
    pymupdf4llm with markdown preservation.

  inputs:
    - docs/02-modules/CONTENT_GENERATION.md (extraction section)

  outputs:
    - backend/app/services/pdf_extractor.py

  acceptance_criteria:
    - Use pymupdf4llm (90% cost savings)
    - Preserve markdown formatting
    - Handle PDFs up to 50MB
    - Streaming for large files
    - Error handling for corrupted PDFs
    - Return structured markdown

  qa_pair: "QA-EXTRACT-001"
```

### 3.2 Data Structurer Agent

```yaml
AGENT:
  id: "DEV-STRUCT-001"
  name: "Data Structurer Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement Claude Sonnet 4.5 data structuring to convert
    markdown text into validated JSON schema.

  inputs:
    - docs/02-modules/CONTENT_GENERATION.md (structuring section)
    - docs/02-modules/PROJECT_DATABASE.md (field requirements)

  outputs:
    - backend/app/services/data_structurer.py

  acceptance_criteria:
    - Extract all core fields from markdown
    - Generate confidence scores per field
    - Track missing/incomplete fields
    - Validate against required schema
    - Cost: ~$0.01-0.03 per PDF
    - Quality metrics calculation

  qa_pair: "QA-STRUCT-001"
```

### 3.3 Content Generator Agent

```yaml
AGENT:
  id: "DEV-CONTENT-001"
  name: "Content Generator Agent"
  type: "Development"
  context_budget: 65000

  mission: |
    Implement brand-aware content generation with character
    limits, SEO optimization, and multi-template support.

  inputs:
    - docs/02-modules/CONTENT_GENERATION.md
    - reference/company/brand-guidelines/brand-context-prompt.md
    - docs/02-modules/QA_MODULE.md

  outputs:
    - backend/app/services/content_generator.py
    - backend/app/services/content_qa_service.py
    - backend/app/services/prompt_manager.py

  acceptance_criteria:
    - Load brand context from reference file
    - Prepend brand context to all prompts
    - Field-by-field generation
    - Character limit enforcement
    - SEO optimization (title, description, H1, slug)
    - Support 6 templates (Aggregators, OPR, MPP, ADOP, ADRE, Commercial)
    - Version-controlled prompts
    - QA validation (factual, compliance, consistency)

  qa_pair: "QA-CONTENT-001"
```

### 3.4 Sheets Manager Agent

```yaml
AGENT:
  id: "DEV-SHEETS-001"
  name: "Sheets Manager Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement Google Sheets integration with template creation,
    field mapping, batch updates, and validation.

  inputs:
    - docs/05-integrations/SHEETS_INTEGRATION.md
    - docs/02-modules/GOOGLE_SHEETS_INTEGRATION.md

  outputs:
    - backend/app/services/sheets_manager.py

  acceptance_criteria:
    - Create sheets from templates
    - Map content fields to cells
    - Batch update API calls
    - Domain-wide delegation
    - Share with project creator
    - Read-back validation
    - Handle API rate limits

  qa_pair: "QA-SHEETS-001"
```

---

## Phase 4: Frontend Agents

### 4.1 Frontend Setup Agent

```yaml
AGENT:
  id: "DEV-FESETUP-001"
  name: "Frontend Setup Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Initialize React 19 + Vite + TypeScript project with
    Tailwind, shadcn/ui, and project structure.

  inputs:
    - docs/03-frontend/FRONTEND_OVERVIEW.md
    - docs/03-frontend/COMPONENT_LIBRARY.md

  outputs:
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/tsconfig.json
    - frontend/src/index.css
    - frontend/src/main.tsx
    - frontend/src/App.tsx
    - Directory structure

  acceptance_criteria:
    - React 19 with TypeScript strict mode
    - Vite configuration
    - Tailwind + shadcn/ui setup
    - ESLint + Prettier configuration
    - Path aliases configured
    - Source directory structure created

  qa_pair: "QA-FESETUP-001"
```

### 4.2 Auth UI Agent

```yaml
AGENT:
  id: "DEV-AUTHUI-001"
  name: "Auth UI Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Implement login page with Google OAuth, protected routes,
    and user session management.

  inputs:
    - docs/03-frontend/PAGES.md (login section)
    - docs/03-frontend/STATE_MANAGEMENT.md

  outputs:
    - frontend/src/pages/LoginPage.tsx
    - frontend/src/stores/auth-store.ts
    - frontend/src/lib/auth.ts
    - frontend/src/components/layout/ProtectedRoute.tsx

  acceptance_criteria:
    - Google OAuth login button
    - Token storage in memory
    - Protected route wrapper
    - Auto-redirect on auth state
    - User menu with logout
    - Session persistence

  qa_pair: "QA-AUTHUI-001"
```

### 4.3 Dashboard Agent

```yaml
AGENT:
  id: "DEV-DASHBOARD-001"
  name: "Dashboard Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement home page with project list, search, filtering,
    sorting, and pagination.

  inputs:
    - docs/03-frontend/PAGES.md (dashboard section)
    - docs/03-frontend/COMPONENT_LIBRARY.md

  outputs:
    - frontend/src/pages/HomePage.tsx
    - frontend/src/components/projects/ProjectList.tsx
    - frontend/src/components/projects/ProjectCard.tsx
    - frontend/src/components/projects/ProjectFilters.tsx
    - frontend/src/hooks/queries/use-projects.ts

  acceptance_criteria:
    - Project list with cards
    - Search by name/developer
    - Multi-field filtering
    - Column sorting
    - Pagination (50 per page)
    - Loading and empty states
    - Create project button

  qa_pair: "QA-DASHBOARD-001"
```

### 4.4 Upload UI Agent

```yaml
AGENT:
  id: "DEV-UPLOAD-001"
  name: "Upload UI Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement PDF upload page with drag-drop, progress tracking,
    and job monitoring.

  inputs:
    - docs/03-frontend/PAGES.md (upload section)
    - docs/08-user-guides/CONTENT_CREATOR_GUIDE.md

  outputs:
    - frontend/src/pages/ProcessingPage.tsx
    - frontend/src/components/upload/FileUpload.tsx
    - frontend/src/components/upload/ProgressTracker.tsx
    - frontend/src/components/upload/JobStatus.tsx
    - frontend/src/hooks/queries/use-jobs.ts

  acceptance_criteria:
    - Drag-drop file upload
    - Template selection (Aggregators/OPR/MPP/ADOP/ADRE/Commercial)
    - Upload progress indicator
    - Job status polling (2s intervals)
    - Step-by-step progress display
    - Cancel job button
    - Download results when complete

  qa_pair: "QA-UPLOAD-001"
```

### 4.5 Remaining Frontend Agents

```yaml
# Similar specifications for:
DEV-PROJDETAIL-001: "Project Detail Agent"
DEV-QAPAGE-001: "QA Page Agent"
DEV-PROMPTS-001: "Prompts Page Agent"
DEV-WORKFLOW-001: "Workflow Page Agent"
DEV-COMPONENTS-001: "Shared Components Agent"
DEV-STATE-001: "State Management Agent"

# Each with:
# - Specific inputs from docs/03-frontend/
# - Defined outputs (components, pages, stores)
# - Acceptance criteria
# - Paired QA agent
```

---

## Phase 5: Integration Agents

### 5.1 GCS Integration Agent

```yaml
AGENT:
  id: "DEV-GCS-001"
  name: "GCS Integration Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Implement Google Cloud Storage integration for file upload,
    download, and signed URL generation.

  inputs:
    - docs/05-integrations/GOOGLE_CLOUD_SETUP.md
    - docs/05-integrations/CLOUD_STORAGE.md

  outputs:
    - backend/app/services/storage_service.py

  acceptance_criteria:
    - Upload files to bucket
    - Download files
    - Generate signed URLs
    - Organize by project
    - Handle errors gracefully
    - Service account authentication

  qa_pair: "QA-GCS-001"
```

### 5.2 Anthropic Integration Agent

```yaml
AGENT:
  id: "DEV-ANTHROPIC-001"
  name: "Anthropic Integration Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement Anthropic API integration with rate limiting,
    error handling, cost tracking, and retry logic.

  inputs:
    - docs/05-integrations/ANTHROPIC_API_INTEGRATION.md

  outputs:
    - backend/app/services/anthropic_service.py
    - backend/app/utils/token_counter.py

  acceptance_criteria:
    - Claude Sonnet 4.5 for text
    - Claude Sonnet 4.5 for vision
    - Rate limiting with backoff
    - Token counting
    - Cost calculation
    - Error handling (timeout, quota)
    - Retry logic (3 attempts)

  qa_pair: "QA-ANTHROPIC-001"
```

---

## Phase 6: DevOps Agents

### 6.1 Docker Agent

```yaml
AGENT:
  id: "DEV-DOCKER-001"
  name: "Docker Agent"
  type: "Development"
  context_budget: 50000

  mission: |
    Create Docker configurations for backend, frontend,
    and local development environment.

  inputs:
    - docs/06-devops/DOCKER_CONFIG.md
    - docs/06-devops/LOCAL_DEVELOPMENT.md

  outputs:
    - backend/Dockerfile
    - frontend/Dockerfile
    - docker-compose.yml
    - docker-compose.dev.yml

  acceptance_criteria:
    - Multi-stage builds
    - Optimized image sizes
    - Health checks
    - Environment variable injection
    - Volume mounts for development
    - Network configuration

  qa_pair: "QA-DOCKER-001"
```

### 6.2 CI/CD Agent

```yaml
AGENT:
  id: "DEV-CICD-001"
  name: "CI/CD Agent"
  type: "Development"
  context_budget: 55000

  mission: |
    Implement CI/CD pipeline with Cloud Build including
    testing, building, and deployment stages.

  inputs:
    - docs/06-devops/CICD_PIPELINE.md

  outputs:
    - cloudbuild.yaml
    - .github/workflows/*.yml (if using GitHub Actions)

  acceptance_criteria:
    - Test stage (unit + integration)
    - Lint stage
    - Build stage (Docker images)
    - Deploy stage (Cloud Run)
    - Traffic splitting for canary
    - Rollback capability
    - Notifications on failure

  qa_pair: "QA-CICD-001"
```

---

## QA Agent Layer

### QA Agent Specifications

Each development agent has a paired QA agent. QA agents operate with a standardized validation framework:

```yaml
QA_AGENT_TEMPLATE:
  context_budget: 40000-50000

  standard_checks:
    code_quality:
      - Follows project style guide
      - No linting errors
      - Type annotations complete
      - Docstrings present
      - No hardcoded values
      - Error handling present

    security:
      - No secrets in code
      - Input validation present
      - Output encoding
      - SQL injection prevention
      - XSS prevention

    performance:
      - No N+1 queries
      - Efficient algorithms
      - Proper indexing
      - Connection pooling

    testing:
      - Unit tests present
      - Test coverage adequate
      - Edge cases covered
      - Error cases tested

    documentation:
      - README updated
      - API docs accurate
      - Comments for complex logic

  domain_specific_checks:
    # Added per agent type
```

### QA Orchestrator Role

```yaml
QA_ORCHESTRATOR:
  id: "ORCH-QA-001"

  responsibilities:
    - Aggregate QA results from all paired QA agents
    - Calculate overall quality score
    - Identify patterns in quality issues
    - Manage quality gates
    - Escalate critical issues
    - Report to Master Orchestrator

  quality_gates:
    phase_gate:
      required_score: 85%
      blocking_issues: 0 critical, 0 high

    release_gate:
      required_score: 95%
      blocking_issues: 0 critical, 0 high, 0 medium
      test_coverage: 80%+

  escalation_triggers:
    - Critical security vulnerability
    - Test coverage below threshold
    - Multiple agents failing same check
    - Quality score below 70%
```

---

## Testing Agent Layer

### 8.1 Backend Unit Test Agent

```yaml
AGENT:
  id: "TEST-BACKEND-UNIT-001"
  name: "Backend Unit Test Agent"
  type: "Testing"
  context_budget: 50000

  mission: |
    Write comprehensive unit tests for all backend services
    with 80%+ coverage target.

  inputs:
    - docs/07-testing/UNIT_TEST_PATTERNS.md
    - All backend service files

  outputs:
    - tests/unit/services/*.py
    - tests/unit/repositories/*.py
    - tests/unit/utils/*.py
    - pytest.ini configuration

  acceptance_criteria:
    - 80%+ line coverage
    - 100% critical path coverage
    - Mock all external dependencies
    - Test happy path and error cases
    - Use pytest fixtures
    - Follow naming conventions
```

### 8.2 API Integration Test Agent

```yaml
AGENT:
  id: "TEST-API-INT-001"
  name: "API Integration Test Agent"
  type: "Testing"
  context_budget: 55000

  mission: |
    Write integration tests for all API endpoints with
    database and external service integration.

  inputs:
    - docs/07-testing/INTEGRATION_TESTS.md
    - docs/04-backend/API_ENDPOINTS.md

  outputs:
    - tests/integration/api/*.py
    - tests/integration/conftest.py
    - Test fixtures and factories

  acceptance_criteria:
    - All endpoints tested
    - Auth flows tested
    - Database transactions tested
    - Error responses validated
    - Rate limiting tested
    - Contract validation
```

### 8.3 E2E Test Agent

```yaml
AGENT:
  id: "TEST-E2E-001"
  name: "E2E Test Agent"
  type: "Testing"
  context_budget: 55000

  mission: |
    Write end-to-end tests covering complete user workflows
    from upload to publication.

  inputs:
    - docs/07-testing/E2E_TEST_SCENARIOS.md
    - docs/08-user-guides/*.md

  outputs:
    - tests/e2e/scenarios/*.py
    - tests/e2e/fixtures/*
    - Playwright/Cypress configuration

  acceptance_criteria:
    - Complete workflow coverage
    - Multi-user scenarios
    - Error recovery scenarios
    - Performance under load
    - Cross-browser testing
```

### Testing Orchestrator Role

```yaml
TESTING_ORCHESTRATOR:
  id: "ORCH-TESTING-001"

  responsibilities:
    - Coordinate all testing agents
    - Aggregate test results
    - Calculate coverage metrics
    - Identify coverage gaps
    - Report test failures
    - Manage test infrastructure

  coverage_targets:
    backend_unit: 80%
    frontend_unit: 70%
    integration: 75%
    e2e_scenarios: 100% (defined scenarios)

  test_execution_order:
    1: Unit tests (parallel)
    2: Integration tests (sequential)
    3: E2E tests (sequential)
    4: Performance tests (scheduled)
```

---

## Orchestrator Agent Specifications

### Master Orchestrator

```yaml
MASTER_ORCHESTRATOR:
  id: "ORCH-MASTER-001"
  context_budget: 100000

  state_tracking:
    phases:
      - id: "phase_0"
        name: "Foundation"
        status: "pending|in_progress|blocked|completed"
        agents: [DB_Agent, Config_Agent]
        dependencies: []

      - id: "phase_1"
        name: "Backend Core"
        status: "pending"
        agents: [Auth_Agent, Project_Agent, Job_Agent, API_Agent]
        dependencies: [phase_0]

      # ... phases 2-6

    quality_metrics:
      overall_score: 0-100
      critical_issues: 0
      high_issues: 0
      test_coverage: 0%

    timeline:
      start_date: null
      estimated_completion: null
      current_phase: "phase_0"
      blockers: []

  decision_matrix:
    phase_transition:
      conditions:
        - All agents in phase completed
        - QA score >= 85%
        - No critical/high issues
        - Test coverage >= threshold
      actions:
        - Approve transition
        - Request remediation
        - Escalate to human

    resource_allocation:
      conditions:
        - Phase behind schedule
        - Multiple agents blocked
        - Quality score dropping
      actions:
        - Add parallel agents
        - Prioritize blockers
        - Adjust scope

    conflict_resolution:
      conditions:
        - Cross-domain dependency conflict
        - API contract mismatch
        - Resource contention
      actions:
        - Mediate between orchestrators
        - Establish priority
        - Create shared interface
```

### Inter-Orchestrator Communication

```yaml
communication_protocol:
  message_types:
    status_report:
      sender: Domain Orchestrator
      recipient: Master Orchestrator
      frequency: On agent completion, on blocking issue
      content:
        - Agent status updates
        - Quality metrics
        - Blockers identified
        - Dependencies needed

    dependency_request:
      sender: Domain Orchestrator
      recipient: Other Domain Orchestrator
      content:
        - Required artifact
        - Interface contract
        - Timeline needed

    phase_gate_request:
      sender: Master Orchestrator
      recipient: QA Orchestrator
      content:
        - Phase to validate
        - Artifacts to check
        - Quality thresholds

    escalation:
      sender: Any Orchestrator
      recipient: Master Orchestrator
      content:
        - Issue description
        - Impact assessment
        - Recommended actions

  handoff_protocol:
    on_agent_completion:
      1: Agent reports completion to Domain Orchestrator
      2: Domain Orchestrator triggers paired QA agent
      3: QA agent validates outputs
      4: Domain Orchestrator receives QA report
      5: If passed, Domain Orchestrator reports to Master
      6: Master updates system state
      7: Master triggers dependent agents
```

---

## Inter-Agent Communication Protocol

### Artifact Exchange Format

```json
{
  "artifact_id": "ART-2026-001",
  "producer_agent": "DEV-DB-001",
  "artifact_type": "code",
  "artifact_path": "backend/alembic/versions/001_initial_schema.py",
  "artifact_hash": "sha256:abc123...",
  "metadata": {
    "created_at": "2026-01-15T10:00:00Z",
    "version": "1.0.0",
    "dependencies": [],
    "exports": ["User", "Project", "Job", "..."]
  },
  "validation_status": {
    "qa_agent": "QA-DB-001",
    "passed": true,
    "score": 92,
    "issues": []
  }
}
```

### Dependency Declaration

```yaml
dependency_declaration:
  agent: "DEV-AUTH-001"
  requires:
    - artifact_type: "database_schema"
      producer: "DEV-DB-001"
      interface: "User model with email, role, created_at"
      blocking: true

    - artifact_type: "configuration"
      producer: "DEV-CONFIG-001"
      interface: "JWT_SECRET, GOOGLE_CLIENT_ID"
      blocking: true

  produces:
    - artifact_type: "auth_service"
      interface: "authenticate(), get_current_user(), require_role()"
      consumers: ["DEV-API-001", "DEV-PROJECT-001"]
```

---

## Execution Timeline

### Phase Gantt Chart

```
PHASE 0: Foundation (Week 1)
├── DEV-DB-001 ████████░░ + QA-DB-001 ██░░
├── DEV-CONFIG-001 ██████░░░░ + QA-CONFIG-001 █░░
└── Gate 0 ✓

PHASE 1: Backend Core (Weeks 2-3)
├── DEV-AUTH-001 ████████████░░ + QA-AUTH-001 ███░░
├── DEV-PROJECT-001 ████████████░░ + QA-PROJECT-001 ███░░
├── DEV-JOB-001 ██████████░░░░ + QA-JOB-001 ██░░
├── DEV-API-001 ████████████████░░ + QA-API-001 ████░░
└── Gate 1 ✓

PHASE 2: Material Preparation (Weeks 3-5)
├── DEV-PDF-001 ████████░░ + QA-PDF-001 ██░░
├── DEV-IMGCLASS-001 ██████████████░░ + QA-IMGCLASS-001 ███░░
├── DEV-WATERMARK-001 ████████████░░ + QA-WATERMARK-001 ███░░
├── DEV-FLOORPLAN-001 ██████████████░░ + QA-FLOORPLAN-001 ███░░
├── DEV-IMGOPT-001 ████████░░ + QA-IMGOPT-001 ██░░
└── Gate 2 ✓

PHASE 3: Content Generation (Weeks 4-6)
├── DEV-EXTRACT-001 ██████░░ + QA-EXTRACT-001 ██░░
├── DEV-STRUCT-001 ████████████░░ + QA-STRUCT-001 ███░░
├── DEV-CONTENT-001 ████████████████████░░ + QA-CONTENT-001 █████░░
├── DEV-SHEETS-001 ████████████░░ + QA-SHEETS-001 ███░░
└── Gate 3 ✓

PHASE 4: Frontend (Weeks 3-7) [Parallel with Backend]
├── DEV-FESETUP-001 ████░░ + QA-FESETUP-001 █░░
├── DEV-AUTHUI-001 ██████░░ + QA-AUTHUI-001 ██░░
├── DEV-DASHBOARD-001 ████████████░░ + QA-DASHBOARD-001 ███░░
├── DEV-UPLOAD-001 ██████████░░ + QA-UPLOAD-001 ███░░
├── DEV-PROJDETAIL-001 ████████████░░ + QA-PROJDETAIL-001 ███░░
├── DEV-QAPAGE-001 ████████░░ + QA-QAPAGE-001 ██░░
├── DEV-PROMPTS-001 ██████░░ + QA-PROMPTS-001 ██░░
├── DEV-WORKFLOW-001 ████████████░░ + QA-WORKFLOW-001 ███░░
├── DEV-COMPONENTS-001 ████████████████░░ + QA-COMPONENTS-001 ████░░
└── Gate 4 ✓

PHASE 5: Integrations (Weeks 5-7)
├── DEV-GCS-001 ████████░░ + QA-GCS-001 ██░░
├── DEV-SHEETS-001 ████████████░░ + QA-SHEETS-001 ███░░
├── DEV-DRIVE-001 ██████░░ + QA-DRIVE-001 ██░░
├── DEV-ANTHROPIC-001 ██████████░░ + QA-ANTHROPIC-001 ███░░
├── DEV-OAUTH-001 ████████░░ + QA-OAUTH-001 ██░░
└── Gate 5 ✓

PHASE 6: DevOps (Weeks 6-8)
├── DEV-DOCKER-001 ██████░░ + QA-DOCKER-001 ██░░
├── DEV-CICD-001 ████████████░░ + QA-CICD-001 ███░░
├── DEV-CLOUDRUN-001 ████████░░ + QA-CLOUDRUN-001 ██░░
├── DEV-MONITORING-001 ██████░░ + QA-MONITORING-001 ██░░
└── Gate 6 ✓

TESTING PHASE (Weeks 7-9)
├── TEST-BACKEND-UNIT-001 ████████████████░░
├── TEST-FRONTEND-UNIT-001 ████████████░░
├── TEST-API-INT-001 ██████████████░░
├── TEST-FE-INT-001 ██████████░░
├── TEST-E2E-001 ████████████████████░░
├── TEST-PERF-001 ████████░░
├── TEST-SECURITY-001 ██████░░
└── Final Gate ✓

RELEASE (Week 10)
└── Deployment to Production
```

### Parallel Execution Map

```
Week 1:  [Phase 0: DB + Config]
Week 2:  [Phase 1: Backend Core] ←──────────────────────────────────┐
Week 3:  [Phase 1 cont.] + [Phase 2: Material Prep starts]          │
Week 4:  [Phase 2 cont.] + [Phase 3: Content Gen starts]            │
Week 5:  [Phase 2 complete] + [Phase 3 cont.] + [Phase 5 starts]    │ PARALLEL
Week 6:  [Phase 3 cont.] + [Phase 5 cont.] + [Phase 6 starts]       │
Week 7:  [Phase 3 complete] + [Phase 5 complete] + [Phase 6 cont.]  │
Week 8:  [Phase 6 complete] + [Testing Phase]                       │
         ↓                                                          │
[Phase 4: Frontend runs parallel throughout Weeks 3-7] ─────────────┘
```

---

## Quality Gates & Checkpoints

### Gate Definitions

```yaml
quality_gates:
  gate_0_foundation:
    name: "Foundation Complete"
    required_agents: [DEV-DB-001, DEV-CONFIG-001]
    criteria:
      - All database tables created
      - Migrations reversible
      - Configuration loading works
      - Environment variables documented
    qa_threshold: 85%
    test_coverage: N/A (infrastructure)
    blocking: true

  gate_1_backend_core:
    name: "Backend Core Complete"
    required_agents: [DEV-AUTH-001, DEV-PROJECT-001, DEV-JOB-001, DEV-API-001]
    criteria:
      - Auth flow working end-to-end
      - CRUD operations functional
      - Job processing functional
      - All API endpoints responding
      - OpenAPI spec generated
    qa_threshold: 85%
    test_coverage: 80%
    blocking: true

  gate_2_material_prep:
    name: "Material Preparation Complete"
    required_agents: [DEV-PDF-001, DEV-IMGCLASS-001, DEV-WATERMARK-001, DEV-FLOORPLAN-001, DEV-IMGOPT-001]
    criteria:
      - PDF extraction working
      - Image classification accurate (>90%)
      - Watermark removal functional
      - Floor plan extraction working
      - Image optimization producing valid outputs
    qa_threshold: 85%
    test_coverage: 80%
    blocking: true

  gate_3_content_gen:
    name: "Content Generation Complete"
    required_agents: [DEV-EXTRACT-001, DEV-STRUCT-001, DEV-CONTENT-001, DEV-SHEETS-001]
    criteria:
      - Text extraction working
      - Data structuring accurate
      - Content generation with brand compliance
      - Sheets integration functional
    qa_threshold: 90%  # Higher for content quality
    test_coverage: 85%
    blocking: true

  gate_4_frontend:
    name: "Frontend Complete"
    required_agents: [All frontend agents]
    criteria:
      - All pages rendering
      - Auth flow working in UI
      - Upload and processing UI functional
      - All user workflows completable
      - Accessibility compliance
    qa_threshold: 85%
    test_coverage: 70%
    blocking: true

  gate_5_integrations:
    name: "Integrations Complete"
    required_agents: [DEV-GCS-001, DEV-SHEETS-001, DEV-DRIVE-001, DEV-ANTHROPIC-001, DEV-OAUTH-001]
    criteria:
      - All external services connected
      - Error handling for service failures
      - Rate limiting implemented
      - Retry logic working
    qa_threshold: 90%  # Critical for production
    test_coverage: 85%
    blocking: true

  gate_6_devops:
    name: "DevOps Complete"
    required_agents: [DEV-DOCKER-001, DEV-CICD-001, DEV-CLOUDRUN-001, DEV-MONITORING-001]
    criteria:
      - Containers building
      - CI/CD pipeline functional
      - Staging deployment working
      - Monitoring and alerting configured
    qa_threshold: 90%
    test_coverage: 75%
    blocking: true

  gate_final:
    name: "Release Ready"
    criteria:
      - All previous gates passed
      - E2E tests passing
      - Performance tests passing
      - Security scan clean
      - Documentation complete
    qa_threshold: 95%
    test_coverage: 80% overall
    blocking: true
```

---

## Risk Mitigation

### Identified Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Anthropic API rate limits | High | High | Implement queuing, exponential backoff, token budgeting |
| Context overflow in agents | Medium | High | Strict context budgets, chunking large tasks |
| Cross-domain dependency delays | Medium | Medium | Parallel development with interface contracts |
| QA bottleneck | Medium | Medium | Parallel QA agents, automated checks |
| Integration failures | Medium | High | Mock services, comprehensive error handling |
| Quality degradation under pressure | Low | High | Strict quality gates, no bypasses |

### Contingency Plans

```yaml
contingency_plans:
  agent_failure:
    detection: "Agent fails to produce valid output after 3 attempts"
    action:
      - Log failure details
      - Notify Domain Orchestrator
      - Attempt with fresh context
      - If still failing, escalate to Master Orchestrator
      - Consider human intervention

  quality_gate_failure:
    detection: "Phase fails quality gate criteria"
    action:
      - Identify failing checks
      - Route issues to responsible agents
      - Set deadline for remediation
      - Re-run gate after fixes
      - If repeated failure, escalate

  dependency_block:
    detection: "Agent blocked waiting for dependency >24h"
    action:
      - Escalate to orchestrators
      - Prioritize blocking agent
      - Consider stub/mock approach
      - Adjust timeline

  scope_creep:
    detection: "Agent producing artifacts outside defined scope"
    action:
      - Review agent instructions
      - Constrain context further
      - Add explicit boundaries
      - Re-run with corrections
```

---

## Appendix A: Full Agent Registry

### Summary Statistics

| Category | Count |
|----------|-------|
| Development Agents | 42 |
| QA Agents (paired) | 42 |
| Testing Agents | 8 |
| Orchestrator Agents | 7 |
| **Total Agents** | **99** |

### Agent ID Reference

```
ORCHESTRATORS (7):
  ORCH-MASTER-001     Master Orchestrator
  ORCH-BACKEND-001    Backend Orchestrator
  ORCH-FRONTEND-001   Frontend Orchestrator
  ORCH-INTEGRATION-001 Integration Orchestrator
  ORCH-DEVOPS-001     DevOps Orchestrator
  ORCH-QA-001         QA Orchestrator
  ORCH-TESTING-001    Testing Orchestrator

PHASE 0 - Foundation (4):
  DEV-DB-001          Database Schema Agent
  QA-DB-001           Database Schema QA
  DEV-CONFIG-001      Configuration Agent
  QA-CONFIG-001       Configuration QA

PHASE 1 - Backend Core (8):
  DEV-AUTH-001        Auth Service Agent
  QA-AUTH-001         Auth Service QA
  DEV-PROJECT-001     Project Service Agent
  QA-PROJECT-001      Project Service QA
  DEV-JOB-001         Job Manager Agent
  QA-JOB-001          Job Manager QA
  DEV-API-001         API Routes Agent
  QA-API-001          API Routes QA

PHASE 2 - Material Preparation (10):
  DEV-PDF-001         PDF Processor Agent
  QA-PDF-001          PDF Processor QA
  DEV-IMGCLASS-001    Image Classifier Agent
  QA-IMGCLASS-001     Image Classifier QA
  DEV-WATERMARK-001   Watermark Agent
  QA-WATERMARK-001    Watermark QA
  DEV-FLOORPLAN-001   Floor Plan Agent
  QA-FLOORPLAN-001    Floor Plan QA
  DEV-IMGOPT-001      Image Optimizer Agent
  QA-IMGOPT-001       Image Optimizer QA

PHASE 3 - Content Generation (8):
  DEV-EXTRACT-001     Text Extractor Agent
  QA-EXTRACT-001      Text Extractor QA
  DEV-STRUCT-001      Data Structurer Agent
  QA-STRUCT-001       Data Structurer QA
  DEV-CONTENT-001     Content Generator Agent
  QA-CONTENT-001      Content Generator QA
  DEV-SHEETS-001      Sheets Manager Agent
  QA-SHEETS-001       Sheets Manager QA

PHASE 4 - Frontend (20):
  DEV-FESETUP-001     Frontend Setup Agent
  QA-FESETUP-001      Frontend Setup QA
  DEV-AUTHUI-001      Auth UI Agent
  QA-AUTHUI-001       Auth UI QA
  DEV-DASHBOARD-001   Dashboard Agent
  QA-DASHBOARD-001    Dashboard QA
  DEV-UPLOAD-001      Upload UI Agent
  QA-UPLOAD-001       Upload UI QA
  DEV-PROJDETAIL-001  Project Detail Agent
  QA-PROJDETAIL-001   Project Detail QA
  DEV-QAPAGE-001      QA Page Agent
  QA-QAPAGE-001       QA Page QA
  DEV-PROMPTS-001     Prompts Page Agent
  QA-PROMPTS-001      Prompts Page QA
  DEV-WORKFLOW-001    Workflow Page Agent
  QA-WORKFLOW-001     Workflow Page QA
  DEV-COMPONENTS-001  Shared Components Agent
  QA-COMPONENTS-001   Shared Components QA
  DEV-STATE-001       State Management Agent
  QA-STATE-001        State Management QA

PHASE 5 - Integrations (10):
  DEV-GCS-001         GCS Integration Agent
  QA-GCS-001          GCS Integration QA
  DEV-GSHEETS-001     Google Sheets Agent
  QA-GSHEETS-001      Google Sheets QA
  DEV-DRIVE-001       Google Drive Agent
  QA-DRIVE-001        Google Drive QA
  DEV-ANTHROPIC-001      Anthropic Integration Agent
  QA-ANTHROPIC-001       Anthropic Integration QA
  DEV-OAUTH-001       OAuth Integration Agent
  QA-OAUTH-001        OAuth Integration QA

PHASE 6 - DevOps (8):
  DEV-DOCKER-001      Docker Agent
  QA-DOCKER-001       Docker QA
  DEV-CICD-001        CI/CD Agent
  QA-CICD-001         CI/CD QA
  DEV-CLOUDRUN-001    Cloud Run Agent
  QA-CLOUDRUN-001     Cloud Run QA
  DEV-MONITORING-001  Monitoring Agent
  QA-MONITORING-001   Monitoring QA

TESTING (8):
  TEST-BACKEND-UNIT-001   Backend Unit Test Agent
  TEST-FRONTEND-UNIT-001  Frontend Unit Test Agent
  TEST-API-INT-001        API Integration Test Agent
  TEST-FE-INT-001         Frontend Integration Test Agent
  TEST-E2E-001            E2E Test Agent
  TEST-PERF-001           Performance Test Agent
  TEST-SECURITY-001       Security Test Agent
  TEST-VISUAL-001         Visual Regression Test Agent

SYSTEM QA AGENTS (7):
  SYSQA-CODE-001      Code Quality Agent
  SYSQA-SECURITY-001  Security Agent
  SYSQA-INTEGRATION-001 Integration Agent
  SYSQA-PERF-001      Performance Agent
  SYSQA-DOCS-001      Documentation Agent
  SYSQA-DEPS-001      Dependency Agent
  SYSQA-ESCALATION-001 Escalation Agent
```

---

## Appendix B: Context Injection Templates

### Development Agent Context Template

```markdown
# AGENT BRIEF: {{AGENT_ID}}

## Identity
- **Agent ID:** {{AGENT_ID}}
- **Role:** {{ROLE_DESCRIPTION}}
- **Domain:** {{DOMAIN}}
- **Phase:** {{PHASE_NUMBER}}

## Mission
{{MISSION_STATEMENT}}

## Project Standards
{{PROJECT_STYLE_GUIDE}}
{{NAMING_CONVENTIONS}}
{{ERROR_HANDLING_PATTERNS}}

## Domain Documentation
{{RELEVANT_DOCS}}

## Dependencies
### Requires (Upstream)
{{UPSTREAM_DEPENDENCIES}}

### Produces (Downstream)
{{DOWNSTREAM_CONSUMERS}}

## Current Task
### Files to Create/Modify
{{FILE_LIST}}

### Acceptance Criteria
{{ACCEPTANCE_CRITERIA}}

### Test Requirements
{{TEST_REQUIREMENTS}}

## Output Format
{{OUTPUT_FORMAT_REQUIREMENTS}}

---
BEGIN WORK
```

### QA Agent Context Template

```markdown
# QA AGENT BRIEF: {{AGENT_ID}}

## Identity
- **Agent ID:** {{AGENT_ID}}
- **Paired Dev Agent:** {{DEV_AGENT_ID}}
- **Domain:** {{DOMAIN}}

## Mission
Validate outputs from {{DEV_AGENT_ID}} against quality standards.

## Artifacts to Review
{{ARTIFACT_LIST}}

## Validation Checklist

### Code Quality
- [ ] Follows project style guide
- [ ] No linting errors
- [ ] Type annotations complete
- [ ] Docstrings present
- [ ] Error handling present

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] XSS prevention

### Domain-Specific
{{DOMAIN_SPECIFIC_CHECKS}}

## Standards Reference
{{RELEVANT_STANDARDS}}

## Output Format
```json
{
  "agent_id": "{{AGENT_ID}}",
  "reviewed_agent": "{{DEV_AGENT_ID}}",
  "artifacts_reviewed": [...],
  "passed": true/false,
  "score": 0-100,
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "category": "code_quality|security|performance|testing|documentation",
      "file": "path/to/file",
      "line": 123,
      "description": "Issue description",
      "recommendation": "How to fix"
    }
  ],
  "summary": "Overall assessment"
}
```

---
BEGIN REVIEW
```

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Development Team
**Contact:** dev-team@your-domain.com
