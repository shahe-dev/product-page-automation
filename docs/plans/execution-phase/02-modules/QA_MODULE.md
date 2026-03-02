# Module: QA Module

**Module Number:** 5
**Category:** Quality Assurance
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [QA Checkpoints](#qa-checkpoints)
7. [API Endpoints](#api-endpoints)
8. [Services](#services)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **QA Module** provides multi-stage quality assurance throughout the entire PDP automation pipeline. It implements four critical checkpoints: after text extraction, after content generation, after sheet population, and after publication. Each checkpoint validates accuracy, completeness, and compliance with specifications.

**Position in System:** Cross-cutting module that gates progression at critical stages throughout the workflow.

---

## Purpose & Goals

### Primary Purpose

Ensure data accuracy, content quality, and process compliance at every stage of the automation pipeline through systematic validation checkpoints and AI-powered quality verification.

### Goals

1. **Data Accuracy:** Verify extracted data matches source PDFs
2. **Content Quality:** Validate generated content is factually correct and SEO-compliant
3. **Mapping Accuracy:** Confirm Google Sheets populated correctly
4. **Publication Verification:** Ensure published pages match approved content
5. **Early Error Detection:** Catch issues before they propagate downstream
6. **Audit Trail:** Maintain complete QA history for compliance
7. **User Override:** Allow manual approval when automated QA flags false positives

---

## Key Features

### Core Capabilities

- ✅ **Multi-Stage Checkpoints** - QA at extraction, generation, sheets, and publication
- ✅ **AI-Powered Validation** - Claude Sonnet 4.5 fact-checking and comparison
- ✅ **Automated Blocking** - Prevent progression when critical issues detected
- ✅ **Issue Categorization** - Classify by type and severity (critical, major, minor)
- ✅ **User Override** - Manual approval for acceptable deviations
- ✅ **Comparison Reports** - Detailed diff reports showing discrepancies
- ✅ **Historical Tracking** - Complete QA history per project
- ✅ **Pass/Fail Metrics** - QA success rates and trend analysis
- ✅ **Regression Detection** - Compare against previous versions

### QA Checkpoint Summary

**Checkpoint #1: After Text Extraction**
- Verify extraction completeness
- Check confidence scores
- Flag missing critical fields

**Checkpoint #2: After Content Generation**
- Factual accuracy (content vs PDF)
- Prompt compliance (character limits, required fields)
- Consistency check (no contradictions)

**Checkpoint #3: After Sheet Population**
- Cell mapping verification
- Content integrity check
- Formula validation

**Checkpoint #4: After Publication**
- Published page vs approved sheet comparison
- SEO element verification
- Asset completeness check

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • QACheckpointPanel.tsx      - Checkpoint status       │
│ • QAIssuesViewer.tsx         - Issue list with details │
│ • QAComparisonViewer.tsx     - Side-by-side diff       │
│ • QAOverrideDialog.tsx       - Manual approval         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/qa/validate-extraction    - Checkpoint #1       │
│ • /api/qa/validate-content       - Checkpoint #2       │
│ • /api/qa/validate-sheet         - Checkpoint #3       │
│ • /api/qa/validate-publication   - Checkpoint #4       │
│ • /api/qa/override               - Manual approval     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • ExtractionQAService        - Validate extraction     │
│ • ContentQAService           - Validate generation     │
│ • SheetQAService             - Validate sheet mapping  │
│ • PublicationQAService       - Validate published page │
│ • ComparisonEngine           - AI-powered diff         │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ • qa_checkpoints             - Checkpoint results      │
│ • qa_issues                  - Identified issues       │
│ • qa_comparisons             - Comparison data         │
│ • qa_overrides               - Manual approvals        │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `qa_checkpoints`

**Purpose:** Record all QA checkpoint executions and results

```sql
CREATE TABLE qa_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Checkpoint Information
    checkpoint_type VARCHAR(50) NOT NULL,
    -- Types: 'extraction', 'content_generation', 'sheet_population', 'publication'

    checkpoint_number INTEGER NOT NULL,  -- 1, 2, 3, 4

    -- Result
    status VARCHAR(50) NOT NULL,
    -- Status: 'passed', 'failed', 'warning', 'skipped', 'overridden'

    overall_score DECIMAL(3, 2),  -- 0.00 to 1.00

    -- Issue Summary
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    major_issues INTEGER DEFAULT 0,
    minor_issues INTEGER DEFAULT 0,

    -- Comparison Data
    comparison_id UUID REFERENCES qa_comparisons(id),

    -- User Actions
    is_overridden BOOLEAN DEFAULT false,
    overridden_by UUID REFERENCES users(id),
    overridden_at TIMESTAMP,
    override_reason TEXT,

    -- Metadata
    execution_duration_ms INTEGER,
    ai_model_used VARCHAR(50),  -- 'claude-sonnet-4-5-20241022'
    tokens_used INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_checkpoint_type CHECK (checkpoint_type IN (
        'extraction', 'content_generation', 'sheet_population', 'publication'
    )),
    CONSTRAINT valid_status CHECK (status IN (
        'passed', 'failed', 'warning', 'skipped', 'overridden'
    )),
    CONSTRAINT valid_score CHECK (overall_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_qa_checkpoints_project ON qa_checkpoints(project_id);
CREATE INDEX idx_qa_checkpoints_type ON qa_checkpoints(checkpoint_type);
CREATE INDEX idx_qa_checkpoints_status ON qa_checkpoints(status);
CREATE INDEX idx_qa_checkpoints_created ON qa_checkpoints(created_at DESC);
```

---

### Table: `qa_issues`

**Purpose:** Store individual QA issues identified at each checkpoint

```sql
CREATE TABLE qa_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id UUID REFERENCES qa_checkpoints(id) ON DELETE CASCADE,

    -- Issue Classification
    issue_type VARCHAR(50) NOT NULL,
    -- Types: 'missing_field', 'factual_error', 'formatting_error',
    --        'char_limit_violation', 'seo_issue', 'mapping_error',
    --        'content_mismatch', 'asset_missing'

    severity VARCHAR(20) NOT NULL,  -- 'critical', 'major', 'minor', 'info'

    -- Issue Details
    field_name VARCHAR(100),  -- Affected field
    expected_value TEXT,
    actual_value TEXT,
    description TEXT NOT NULL,

    -- Location Context
    source_location TEXT,  -- Page number in PDF, sheet cell, HTML element
    target_location TEXT,

    -- AI Explanation
    ai_reasoning TEXT,  -- Why this was flagged as an issue
    confidence_score DECIMAL(3, 2),

    -- Resolution
    is_resolved BOOLEAN DEFAULT false,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_checkpoint FOREIGN KEY (checkpoint_id) REFERENCES qa_checkpoints(id),
    CONSTRAINT valid_severity CHECK (severity IN ('critical', 'major', 'minor', 'info')),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_qa_issues_checkpoint ON qa_issues(checkpoint_id);
CREATE INDEX idx_qa_issues_severity ON qa_issues(severity);
CREATE INDEX idx_qa_issues_type ON qa_issues(issue_type);
CREATE INDEX idx_qa_issues_unresolved ON qa_issues(is_resolved) WHERE is_resolved = false;
```

---

### Table: `qa_comparisons`

**Purpose:** Store detailed comparison data for auditing

```sql
CREATE TABLE qa_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Comparison Type
    comparison_type VARCHAR(50) NOT NULL,
    -- Types: 'pdf_vs_extraction', 'extraction_vs_content',
    --        'content_vs_sheet', 'sheet_vs_published'

    -- Input Data
    source_data JSONB NOT NULL,     -- Original/expected data
    target_data JSONB NOT NULL,     -- Generated/actual data

    -- Comparison Results
    differences JSONB,
    -- [
    --   {
    --     "field": "starting_price",
    --     "source": "1,200,000 AED",
    --     "target": "1,500,000 AED",
    --     "match": false,
    --     "issue_severity": "critical"
    --   }
    -- ]

    similarity_score DECIMAL(5, 2),  -- Overall similarity (0-100%)
    match_percentage DECIMAL(5, 2),  -- Exact match percentage

    -- AI Analysis
    ai_summary TEXT,
    ai_model VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_qa_comparisons_project ON qa_comparisons(project_id);
CREATE INDEX idx_qa_comparisons_type ON qa_comparisons(comparison_type);
```

---

### Table: `qa_overrides`

**Purpose:** Track manual QA approvals and justifications

```sql
CREATE TABLE qa_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id UUID REFERENCES qa_checkpoints(id) ON DELETE CASCADE,

    -- Override Details
    override_reason VARCHAR(50) NOT NULL,
    -- Reasons: 'acceptable_deviation', 'false_positive', 'manual_verification',
    --          'business_decision', 'technical_limitation'

    justification TEXT NOT NULL,

    -- Issues Overridden
    overridden_issues JSONB,  -- Array of issue IDs and acceptance notes

    -- Approver
    approved_by UUID REFERENCES users(id),
    approver_role VARCHAR(50),
    approved_at TIMESTAMP DEFAULT NOW(),

    -- Risk Assessment
    risk_level VARCHAR(20),  -- 'low', 'medium', 'high'
    risk_notes TEXT,

    CONSTRAINT fk_checkpoint FOREIGN KEY (checkpoint_id) REFERENCES qa_checkpoints(id)
);

CREATE INDEX idx_qa_overrides_checkpoint ON qa_overrides(checkpoint_id);
CREATE INDEX idx_qa_overrides_approved_by ON qa_overrides(approved_by);
```

---

## QA Checkpoints

### Checkpoint #1: Text Extraction Validation

**Timing:** After pymupdf4llm extraction and Claude Sonnet 4.5 structuring

**Validation Criteria:**
1. **Completeness Score:** Minimum 70% of required fields populated
2. **Confidence Score:** Minimum 80% average confidence
3. **Critical Fields:** All mandatory fields must have values
4. **Data Format:** Dates, prices, numbers properly formatted

**Example Checks:**
```python
required_fields = [
    'project_name',
    'developer',
    'location',
    'starting_price',
    'handover_date',
    'property_types'
]

for field in required_fields:
    if not extracted_data.get(field):
        add_issue(
            type='missing_field',
            severity='critical',
            field=field,
            description=f'Required field "{field}" is missing'
        )
```

**Pass Criteria:**
- No critical issues
- Completeness score >= 70%
- Confidence score >= 80%

**Action on Fail:**
- Block progression to content generation
- Notify user to review PDF or manually input missing data

---

### Checkpoint #2: Content Generation Validation

**Timing:** After Claude Sonnet 4.5 content generation, before Google Sheets push

**Validation Criteria:**
1. **Factual Accuracy:** Generated content matches extracted data
2. **Prompt Compliance:** Character limits respected, required fields present
3. **Consistency:** No internal contradictions
4. **SEO Quality:** Meta tags, URL slug properly formatted

**AI-Powered Fact Checking:**
```python
async def check_factual_accuracy(
    source_data: dict,
    generated_content: dict
) -> ValidationResult:
    """
    Use Claude Sonnet 4.5 to compare generated content against source

    Prompt:
    "Compare the following generated content against the source data.
    Identify any factual errors, hallucinations, or contradictions.
    For each discrepancy, explain the issue and severity."
    """
```

**Example Checks:**
- Starting price in content matches extracted price
- Developer name consistent across all fields
- Amenities listed match extracted amenities
- Meta description length <= 160 characters
- URL slug follows pattern: `{project-name}-{developer}`

**Pass Criteria:**
- No critical factual errors
- All character limits respected
- Consistency score >= 85%

**Action on Fail:**
- Show issues to user
- Option to regenerate or manually edit
- Cannot push to sheets until passed or overridden

---

### Checkpoint #3: Sheet Population Validation

**Timing:** After Google Sheets API push

**Validation Criteria:**
1. **Mapping Accuracy:** All fields mapped to correct cells
2. **Content Integrity:** No data corruption during transfer
3. **Formula Validation:** Sheet formulas working correctly
4. **Completeness:** All required cells populated

**Validation Process:**
```python
async def validate_sheet_population(
    sheet_url: str,
    expected_content: dict
) -> ValidationResult:
    """
    Read back sheet contents via API and compare
    """
    # Read sheet
    actual_content = await sheets_api.read_values(sheet_url)

    # Compare field by field
    differences = []
    for field, expected_value in expected_content.items():
        cell_address = FIELD_MAPPING[field]
        actual_value = actual_content.get(cell_address)

        if actual_value != expected_value:
            differences.append({
                'field': field,
                'cell': cell_address,
                'expected': expected_value,
                'actual': actual_value
            })

    return ValidationResult(
        passed=len(differences) == 0,
        differences=differences
    )
```

**Pass Criteria:**
- 100% mapping accuracy
- No data corruption
- All formulas valid

**Action on Fail:**
- Re-push to sheet
- If persistent, flag for manual review

---

### Checkpoint #4: Publication Validation

**Timing:** After page published, before final approval

**Validation Criteria:**
1. **Content Matching:** Published page matches approved Google Sheet
2. **Asset Completeness:** All images and floor plans present
3. **SEO Elements:** Meta tags, URL slug correctly implemented
4. **Functionality:** Page loads, no broken links

**Validation Process:**
```python
async def validate_published_page(
    page_url: str,
    approved_sheet_content: dict
) -> ValidationResult:
    """
    Scrape published page and compare against approved content
    """
    # Fetch page
    page_html = await scraper.fetch_page(page_url)

    # Extract content
    published_content = {
        'meta_title': extract_meta_title(page_html),
        'meta_description': extract_meta_description(page_html),
        'h1': extract_h1(page_html),
        'overview': extract_overview(page_html),
        'images': count_images(page_html),
        'floor_plans': count_floor_plans(page_html)
    }

    # Compare using Claude Sonnet 4.5
    comparison = await ai_compare(approved_sheet_content, published_content)

    return comparison
```

**Comparison Report Format:**
```json
{
  "matches": [
    {
      "field": "meta_title",
      "status": "exact_match"
    }
  ],
  "differences": [
    {
      "field": "starting_price",
      "approved": "1,200,000 AED",
      "published": "1.2M AED",
      "severity": "minor",
      "note": "Formatting difference, value is correct"
    }
  ],
  "missing": [
    {
      "field": "floor_plan_3",
      "severity": "major",
      "note": "Floor plan for 3BR unit not found on page"
    }
  ],
  "extra": [
    {
      "content": "Additional paragraph about financing",
      "severity": "info",
      "note": "Content added by publisher, not in sheet"
    }
  ]
}
```

**Pass Criteria:**
- No critical mismatches
- All major elements present
- Minor differences acceptable (formatting, etc.)

**Action on Fail:**
- Generate detailed report
- Publisher reviews and fixes issues
- Re-validate after fixes

---

## API Endpoints

### Checkpoint Execution

#### `POST /api/qa/validate-extraction`

**Description:** Execute Checkpoint #1

**Request Body:**
```json
{
  "project_id": "uuid",
  "extracted_data_id": "uuid"
}
```

**Response:**
```json
{
  "checkpoint_id": "uuid",
  "status": "passed",
  "overall_score": 0.92,
  "completeness_score": 0.95,
  "confidence_score": 0.89,
  "total_issues": 2,
  "critical_issues": 0,
  "major_issues": 0,
  "minor_issues": 2,
  "issues": [
    {
      "issue_type": "missing_field",
      "severity": "minor",
      "field_name": "total_units",
      "description": "Optional field 'total_units' is missing"
    }
  ],
  "can_proceed": true
}
```

---

#### `POST /api/qa/validate-content`

**Description:** Execute Checkpoint #2

**Request Body:**
```json
{
  "project_id": "uuid",
  "generated_content_id": "uuid"
}
```

**Response:**
```json
{
  "checkpoint_id": "uuid",
  "status": "failed",
  "overall_score": 0.65,
  "total_issues": 3,
  "critical_issues": 1,
  "major_issues": 2,
  "issues": [
    {
      "issue_type": "factual_error",
      "severity": "critical",
      "field_name": "starting_price",
      "expected_value": "1,200,000 AED",
      "actual_value": "1,500,000 AED",
      "description": "Starting price in generated content doesn't match extracted data",
      "ai_reasoning": "The overview paragraph states '...starting from 1.5 million AED' but the extracted price from PDF is 1.2 million AED. This is a significant discrepancy."
    }
  ],
  "can_proceed": false,
  "recommendation": "Fix critical issues and regenerate content"
}
```

---

#### `POST /api/qa/override`

**Description:** Manually approve despite QA failures

**Request Body:**
```json
{
  "checkpoint_id": "uuid",
  "override_reason": "acceptable_deviation",
  "justification": "The price difference is due to a recent update from the developer. PDF is outdated. Confirmed with sales team.",
  "risk_level": "low",
  "overridden_issues": ["issue_id_1", "issue_id_2"]
}
```

**Response:**
```json
{
  "success": true,
  "checkpoint_id": "uuid",
  "status": "overridden",
  "override_id": "uuid",
  "approved_by": "user@your-domain.com",
  "approved_at": "2025-01-15T15:00:00Z"
}
```

---

## Services

### ComparisonEngine

**Purpose:** AI-powered content comparison

**Location:** `backend/app/services/comparison_engine.py`

**Key Methods:**
```python
class ComparisonEngine:
    async def compare_with_ai(
        self,
        source: dict,
        target: dict,
        comparison_type: str
    ) -> ComparisonResult:
        """
        Use Claude Sonnet 4.5 to intelligently compare content

        Handles:
        - Semantic equivalence (1.2M vs 1,200,000)
        - Formatting differences
        - Paraphrasing
        - Additions/omissions
        """

    async def generate_diff_report(
        self,
        source: dict,
        target: dict
    ) -> DiffReport:
        """Generate detailed side-by-side comparison"""
```

---

## Code Examples

### Backend: Content QA Service

```python
# backend/app/services/content_qa_service.py
from typing import Dict, List
from app.services.comparison_engine import ComparisonEngine
from app.models.qa_checkpoint import QACheckpoint
from app.models.qa_issue import QAIssue

class ContentQAService:
    def __init__(self, db):
        self.db = db
        self.comparison_engine = ComparisonEngine()

    async def validate_before_push(
        self,
        extracted_data: dict,
        generated_content: dict,
        prompt_spec: dict
    ) -> QAResult:
        """Checkpoint #2: Validate generated content"""

        issues = []

        # 1. Factual Accuracy Check
        factual_issues = await self._check_factual_accuracy(
            extracted_data,
            generated_content
        )
        issues.extend(factual_issues)

        # 2. Prompt Compliance Check
        compliance_issues = self._check_prompt_compliance(
            generated_content,
            prompt_spec
        )
        issues.extend(compliance_issues)

        # 3. Consistency Check
        consistency_issues = await self._check_consistency(
            generated_content
        )
        issues.extend(consistency_issues)

        # Calculate scores
        critical_count = len([i for i in issues if i.severity == 'critical'])
        major_count = len([i for i in issues if i.severity == 'major'])

        # Determine pass/fail
        status = 'passed'
        if critical_count > 0:
            status = 'failed'
        elif major_count > 2:
            status = 'warning'

        # Save checkpoint
        checkpoint = QACheckpoint(
            checkpoint_type='content_generation',
            status=status,
            total_issues=len(issues),
            critical_issues=critical_count,
            major_issues=major_count
        )
        self.db.add(checkpoint)

        # Save issues
        for issue_data in issues:
            issue = QAIssue(
                checkpoint_id=checkpoint.id,
                **issue_data
            )
            self.db.add(issue)

        await self.db.commit()

        return QAResult(
            passed=(status == 'passed'),
            status=status,
            issues=issues,
            checkpoint_id=checkpoint.id
        )

    async def _check_factual_accuracy(
        self,
        source: dict,
        generated: dict
    ) -> List[dict]:
        """Use AI to check factual accuracy"""

        comparison = await self.comparison_engine.compare_with_ai(
            source,
            generated,
            comparison_type='factual_accuracy'
        )

        return comparison.issues
```

---

## Configuration

### Environment Variables

```bash
# QA Settings
ENABLE_QA_CHECKPOINTS=true
QA_FACTUAL_ACCURACY_THRESHOLD=0.85
QA_MIN_COMPLETENESS_SCORE=0.70
QA_MIN_CONFIDENCE_SCORE=0.80

# AI Configuration
QA_AI_MODEL=claude-sonnet-4-5-20241022
QA_AI_TEMPERATURE=0.2
QA_AI_MAX_TOKENS=2000

# Blocking Behavior
BLOCK_ON_CRITICAL_ISSUES=true
ALLOW_MANUAL_OVERRIDE=true
REQUIRE_OVERRIDE_JUSTIFICATION=true
```

---

## Related Documentation

### Core Documentation
- [Modules > Content Generation](./CONTENT_GENERATION.md) - Content validation
- [Modules > Approval Workflow](./APPROVAL_WORKFLOW.md) - Pre-approval QA
- [Modules > Publishing Workflow](./PUBLISHING_WORKFLOW.md) - Post-publication QA

### Integration Points
- [Integrations > Anthropic](../05-integrations/ANTHROPIC_API_INTEGRATION.md) - AI comparison
- [Integrations > Google Sheets](../05-integrations/GOOGLE_SHEETS_INTEGRATION.md) - Sheet validation

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
