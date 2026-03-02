# Module: Approval Workflow

**Module Number:** 3
**Category:** Workflow Management
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Workflow States](#workflow-states)
7. [API Endpoints](#api-endpoints)
8. [UI Components](#ui-components)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Approval Workflow Module** manages the formal handoff process between Content Creators, Marketing Managers, and Publishers. It enforces a structured review process ensuring all content meets quality standards before publication, with clear state transitions, notification triggers, and audit trails.

**Position in System:** Post-content-generation workflow that gates progression from draft to published state.

---

## Purpose & Goals

### Primary Purpose

Provide a formal, trackable approval process that ensures quality control between departments and maintains clear accountability for content sign-off before publication.

### Goals

1. **Quality Gate:** Prevent low-quality content from reaching publication
2. **Clear Handoff:** Define explicit transitions between Content → Marketing → Publishing
3. **Accountability:** Track who approved what and when
4. **Transparency:** Visible status for all stakeholders
5. **Efficiency:** Bulk approval capabilities for high-volume workflows
6. **Revision Management:** Structured feedback loop for content improvements

---

## Key Features

### Core Capabilities

- ✅ **Multi-Stage Approval** - Content Creator → Marketing Manager → Publisher workflow
- ✅ **Status Tracking** - Clear state machine with defined transitions
- ✅ **Approval Actions** - Approve, Request Revision, Reject with comments
- ✅ **Bulk Operations** - Approve multiple projects simultaneously
- ✅ **Comment System** - Required feedback for rejections and revision requests
- ✅ **Notification Integration** - Automatic alerts on status changes
- ✅ **Approval Queue** - Dedicated views for Marketing Manager and Publisher roles
- ✅ **Deadline Tracking** - Monitor approval SLAs and approaching deadlines
- ✅ **Audit Trail** - Complete history of all approval decisions
- ✅ **Override Capability** - Admin override for exceptional cases

### Workflow Participants

**Content Creator:**
- Submits projects for approval
- Receives revision requests
- Updates and resubmits content

**Marketing Manager:**
- Reviews submitted projects
- Approves or requests revisions
- Provides feedback comments

**Publisher:**
- Receives approved projects
- Manages publication process
- Marks projects as published

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • ApprovalQueuePage.tsx      - Marketing Manager view  │
│ • PublishQueuePage.tsx       - Publisher view          │
│ • ProjectStatusBadge.tsx     - Status visualization    │
│ • ApprovalComments.tsx       - Feedback interface      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/approvals/submit      - Submit for review       │
│ • /api/approvals/approve     - Approve project         │
│ • /api/approvals/reject      - Reject project          │
│ • /api/approvals/revise      - Request revision        │
│ • /api/approvals/queue       - Get approval queue      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • ApprovalService            - Business logic          │
│ • WorkflowEngine             - State transitions       │
│ • NotificationService        - Alert stakeholders      │
│ • DeadlineMonitor            - Track SLAs              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ • project_approvals          - Approval records        │
│ • approval_comments          - Feedback comments       │
│ • workflow_history           - State transition log    │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `project_approvals`

**Purpose:** Track approval status and decisions

```sql
CREATE TABLE project_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Current Status
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Status values:
    -- 'draft', 'pending_approval', 'approved', 'rejected',
    -- 'revision_requested', 'publishing', 'published'

    -- Submission
    submitted_by UUID REFERENCES users(id),
    submitted_at TIMESTAMP,

    -- Marketing Review
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    review_decision VARCHAR(50),  -- 'approved', 'rejected', 'revision_requested'
    review_comments TEXT,

    -- Publisher
    publisher_id UUID REFERENCES users(id),
    publishing_started_at TIMESTAMP,
    published_at TIMESTAMP,

    -- Deadlines
    approval_deadline TIMESTAMP,
    publication_deadline TIMESTAMP,
    is_overdue BOOLEAN DEFAULT false,

    -- Metadata
    revision_count INTEGER DEFAULT 0,
    current_revision_number INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT valid_status CHECK (status IN (
        'draft', 'pending_approval', 'approved', 'rejected',
        'revision_requested', 'publishing', 'published'
    ))
);

CREATE INDEX idx_approvals_project ON project_approvals(project_id);
CREATE INDEX idx_approvals_status ON project_approvals(status);
CREATE INDEX idx_approvals_submitted ON project_approvals(submitted_at DESC);
CREATE INDEX idx_approvals_deadline ON project_approvals(approval_deadline)
    WHERE status = 'pending_approval';
```

---

### Table: `approval_comments`

**Purpose:** Store feedback and revision requests

```sql
CREATE TABLE approval_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id UUID REFERENCES project_approvals(id) ON DELETE CASCADE,

    -- Comment Details
    comment_type VARCHAR(50) NOT NULL,
    -- Types: 'revision_request', 'rejection_reason', 'approval_note', 'general'

    comment TEXT NOT NULL,

    -- Categorization
    category VARCHAR(50),
    -- Categories: 'content_quality', 'factual_error', 'seo_issue',
    --             'formatting', 'brand_guidelines', 'other'

    severity VARCHAR(20),  -- 'critical', 'major', 'minor', 'info'

    -- Referenced Field (optional)
    field_name VARCHAR(100),  -- e.g., 'meta_description', 'overview'

    -- Status
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),

    -- User Attribution
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_approval FOREIGN KEY (approval_id) REFERENCES project_approvals(id)
);

CREATE INDEX idx_comments_approval ON approval_comments(approval_id);
CREATE INDEX idx_comments_type ON approval_comments(comment_type);
CREATE INDEX idx_comments_unresolved ON approval_comments(is_resolved)
    WHERE is_resolved = false;
```

---

### Table: `workflow_history`

**Purpose:** Complete audit trail of state transitions

```sql
CREATE TABLE workflow_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    approval_id UUID REFERENCES project_approvals(id),

    -- Transition Details
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    transition_type VARCHAR(50),  -- 'submit', 'approve', 'reject', 'revise', 'publish'

    -- User Attribution
    performed_by UUID REFERENCES users(id),
    user_email VARCHAR(255),
    user_role VARCHAR(50),  -- 'content_creator', 'marketing_manager', 'publisher'

    -- Context
    comment TEXT,
    metadata JSONB,  -- Additional context data

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_approval FOREIGN KEY (approval_id) REFERENCES project_approvals(id)
);

CREATE INDEX idx_workflow_history_project ON workflow_history(project_id);
CREATE INDEX idx_workflow_history_approval ON workflow_history(approval_id);
CREATE INDEX idx_workflow_history_created ON workflow_history(created_at DESC);
```

---

## Workflow States

### State Machine

```
                    ┌─────────┐
                    │  DRAFT  │
                    └────┬────┘
                         │
                         │ submit_for_approval()
                         ▼
              ┌──────────────────────┐
              │  PENDING_APPROVAL    │
              └──────────┬───────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        │ approve()      │ request_       │ reject()
        │                │ revision()     │
        ▼                ▼                ▼
   ┌─────────┐   ┌──────────────┐   ┌──────────┐
   │APPROVED │   │REVISION      │   │REJECTED  │
   └────┬────┘   │REQUESTED     │   └──────────┘
        │        └──────┬───────┘         │
        │               │                 │
        │               │ resubmit()      │
        │               └─────────────────┘
        │                       │
        │                       ▼
        │              ┌──────────────────┐
        │              │ PENDING_APPROVAL │
        │              └──────────────────┘
        │
        │ start_publishing()
        ▼
   ┌──────────────┐
   │ PUBLISHING   │
   └──────┬───────┘
          │
          │ mark_as_published()
          ▼
   ┌──────────────┐
   │  PUBLISHED   │
   └──────────────┘
```

### State Descriptions

**DRAFT**
- Initial state for all projects
- Content Creator can edit freely
- Not visible to Marketing Manager

**PENDING_APPROVAL**
- Submitted for Marketing Manager review
- Content Creator cannot edit
- Marketing Manager can approve, reject, or request revision

**REVISION_REQUESTED**
- Marketing Manager identified issues
- Content Creator must address feedback
- Can be resubmitted to PENDING_APPROVAL

**APPROVED**
- Marketing Manager approved content
- Ready for Publisher
- Visible in Publisher queue

**REJECTED**
- Marketing Manager rejected content
- Cannot proceed to publishing
- Requires major rework

**PUBLISHING**
- Publisher working on publication
- Assets being uploaded, pages created
- Publisher can mark as published

**PUBLISHED**
- Live on website
- URL recorded
- Ready for QA verification

---

## API Endpoints

### Submission

#### `POST /api/approvals/submit`

**Description:** Submit project for Marketing Manager approval

**Request Body:**
```json
{
  "project_id": "uuid",
  "message": "Ready for review - all content generated and validated"
}
```

**Response:**
```json
{
  "approval_id": "uuid",
  "status": "pending_approval",
  "submitted_by": "creator@your-domain.com",
  "submitted_at": "2025-01-15T10:00:00Z",
  "assigned_to": "marketing@your-domain.com",
  "approval_deadline": "2025-01-17T10:00:00Z"
}
```

---

### Review Actions

#### `POST /api/approvals/{approval_id}/approve`

**Description:** Approve project (Marketing Manager)

**Request Body:**
```json
{
  "comments": "Content looks great, approved for publishing"
}
```

**Response:**
```json
{
  "approval_id": "uuid",
  "status": "approved",
  "reviewed_by": "marketing@your-domain.com",
  "reviewed_at": "2025-01-15T14:30:00Z",
  "notification_sent_to": ["creator@your-domain.com", "publisher@your-domain.com"]
}
```

---

#### `POST /api/approvals/{approval_id}/request-revision`

**Description:** Request content revision (Marketing Manager)

**Request Body:**
```json
{
  "comments": [
    {
      "type": "revision_request",
      "category": "content_quality",
      "severity": "major",
      "field_name": "meta_description",
      "comment": "Meta description exceeds 160 characters. Please shorten while maintaining key selling points."
    },
    {
      "type": "revision_request",
      "category": "factual_error",
      "severity": "critical",
      "field_name": "starting_price",
      "comment": "Starting price should be 1.2M AED, not 1.5M AED as stated in overview."
    }
  ]
}
```

**Response:**
```json
{
  "approval_id": "uuid",
  "status": "revision_requested",
  "revision_count": 1,
  "issues_raised": 2,
  "critical_issues": 1,
  "notification_sent_to": ["creator@your-domain.com"]
}
```

---

#### `POST /api/approvals/{approval_id}/reject`

**Description:** Reject project (Marketing Manager)

**Request Body:**
```json
{
  "reason": "rejection_reason",
  "comments": "Content does not align with brand guidelines. Multiple factual errors identified. Requires complete regeneration.",
  "category": "brand_guidelines"
}
```

**Response:**
```json
{
  "approval_id": "uuid",
  "status": "rejected",
  "reviewed_by": "marketing@your-domain.com",
  "reviewed_at": "2025-01-15T14:30:00Z",
  "notification_sent_to": ["creator@your-domain.com"]
}
```

---

### Queue Management

#### `GET /api/approvals/queue`

**Description:** Get approval queue (filtered by role)

**Query Parameters:**
```typescript
{
  role: 'marketing_manager' | 'publisher';
  status?: string;
  overdue?: boolean;
  sort_by?: 'deadline' | 'submitted_at';
}
```

**Response:**
```json
{
  "queue": [
    {
      "approval_id": "uuid",
      "project_id": "uuid",
      "project_name": "Downtown Elite Residence",
      "status": "pending_approval",
      "submitted_by": "creator@your-domain.com",
      "submitted_at": "2025-01-15T10:00:00Z",
      "approval_deadline": "2025-01-17T10:00:00Z",
      "hours_until_deadline": 42,
      "is_overdue": false,
      "priority": "normal"
    }
  ],
  "summary": {
    "total": 15,
    "pending": 8,
    "overdue": 2,
    "due_today": 3
  }
}
```

---

### Bulk Operations

#### `POST /api/approvals/bulk-approve`

**Description:** Approve multiple projects at once

**Request Body:**
```json
{
  "approval_ids": ["uuid1", "uuid2", "uuid3"],
  "comments": "Batch approval - all projects meet quality standards"
}
```

**Response:**
```json
{
  "success": true,
  "approved_count": 3,
  "results": [
    {
      "approval_id": "uuid1",
      "status": "approved"
    }
  ]
}
```

---

## UI Components

### ApprovalQueuePage.tsx

**Location:** `frontend/src/pages/ApprovalQueuePage.tsx`

**Features:**
- Filterable table of pending approvals
- Sort by deadline, submission date, priority
- Highlight overdue projects
- Quick actions: Approve, Request Revision, Reject
- Bulk selection for batch approvals

---

### ProjectDetailApprovalSection.tsx

**Location:** `frontend/src/components/ProjectDetailApprovalSection.tsx`

**Features:**
- Current approval status display
- Submit for Approval button (Content Creator)
- Approval action buttons (Marketing Manager)
- Comment history timeline
- Revision request form

---

### ApprovalCommentsPanel.tsx

**Location:** `frontend/src/components/ApprovalCommentsPanel.tsx`

**Features:**
- Display all feedback comments
- Categorized by severity (critical, major, minor)
- Field-specific comments highlighted
- Mark as resolved functionality
- Add new comments

---

## Workflow Diagrams

### Approval Workflow (Full Process)

```
Content Creator                Marketing Manager              Publisher
       |                              |                            |
       | 1. Create content            |                            |
       | 2. Validate with QA          |                            |
       |                              |                            |
       | 3. Submit for Approval       |                            |
       |----------------------------->|                            |
       |                              |                            |
       |                              | 4. Review Content          |
       |                              | - Check quality            |
       |                              | - Verify accuracy          |
       |                              | - Assess SEO               |
       |                              |                            |
       |                              | 5. Decision Point          |
       |                              |                            |
       |            ┌─────────────────┼──────────────┐             |
       |            │                 │              │             |
       |            ▼                 ▼              ▼             |
       |        APPROVE          REQUEST         REJECT            |
       |                        REVISION                           |
       |            │                 │              │             |
       |<-----------┘                 │              └------------>|
       | Notification              │                 Notification  |
       |                              ▼                            |
       |                     Issues identified                     |
       |<-----------------------------|                            |
       | Notification + Feedback      |                            |
       |                              |                            |
       | 6. Address issues            |                            |
       | 7. Resubmit                  |                            |
       |----------------------------->|                            |
       |                              |                            |
       |                              | 8. Re-review               |
       |                              |                            |
       |                              | 9. Approve                 |
       |                              |--------------------------->|
       |                              |                            |
       |                              |                            | 10. Download Assets
       |                              |                            | 11. Create Page
       |                              |                            | 12. Upload Images
       |                              |                            | 13. Verify SEO
       |                              |                            |
       |                              |                            | 14. Mark as Published
       |                              |                            | (with URL)
       |                              |                            |
       |<----------------------------------------------------------|
       |              Notification: Project Published              |
       |<----------------------------------------------------------|
       |                                                           |
```

---

### Deadline Monitoring

```
┌──────────────────────────────────────┐
│   Deadline Monitor Service           │
│   (Runs every hour)                  │
└──────────────────┬───────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Check all pending    │
        │ approvals            │
        └──────┬───────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ Calculate time until     │
    │ deadline                 │
    └──────┬───────────────────┘
           │
           ▼
    ┌─────────────────┐
    │ Is overdue?     │
    └────┬────────┬───┘
         │        │
        Yes       No
         │        │
         ▼        ▼
    ┌────────┐  ┌──────────────────┐
    │ Mark   │  │ Within 24 hours? │
    │overdue │  └────┬────────┬────┘
    │        │       │        │
    │ Send   │      Yes       No
    │ alert  │       │        │
    └────────┘       ▼        ▼
              ┌──────────┐  ┌──────┐
              │ Send     │  │ No   │
              │ reminder │  │action│
              └──────────┘  └──────┘
```

---

## Code Examples

### Backend: Approval Service

```python
# backend/app/services/approval_service.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project_approval import ProjectApproval
from app.models.approval_comment import ApprovalComment
from app.services.notification_service import NotificationService

class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def submit_for_approval(
        self,
        project_id: UUID,
        user_id: UUID,
        message: Optional[str] = None
    ) -> ProjectApproval:
        """Submit project for Marketing Manager approval"""

        # Create or update approval record
        approval = ProjectApproval(
            project_id=project_id,
            status='pending_approval',
            submitted_by=user_id,
            submitted_at=datetime.utcnow(),
            approval_deadline=datetime.utcnow() + timedelta(days=2)  # 2-day SLA
        )

        self.db.add(approval)
        await self.db.commit()
        await self.db.refresh(approval)

        # Record workflow transition
        await self._record_workflow_history(
            project_id=project_id,
            approval_id=approval.id,
            from_status='draft',
            to_status='pending_approval',
            transition_type='submit',
            performed_by=user_id,
            comment=message
        )

        # Notify Marketing Manager
        await self.notification_service.send_notification(
            event_type='project.pending_approval',
            project_id=project_id,
            recipients=['marketing_manager']
        )

        return approval

    async def approve(
        self,
        approval_id: UUID,
        reviewer_id: UUID,
        comments: Optional[str] = None
    ) -> ProjectApproval:
        """Approve project (Marketing Manager action)"""

        approval = await self._get_approval(approval_id)

        if approval.status != 'pending_approval':
            raise ValueError(f"Cannot approve project in status: {approval.status}")

        # Update approval
        approval.status = 'approved'
        approval.reviewed_by = reviewer_id
        approval.reviewed_at = datetime.utcnow()
        approval.review_decision = 'approved'
        approval.review_comments = comments

        await self.db.commit()
        await self.db.refresh(approval)

        # Record workflow transition
        await self._record_workflow_history(
            project_id=approval.project_id,
            approval_id=approval.id,
            from_status='pending_approval',
            to_status='approved',
            transition_type='approve',
            performed_by=reviewer_id,
            comment=comments
        )

        # Notify Content Creator and Publisher
        await self.notification_service.send_notification(
            event_type='project.approved',
            project_id=approval.project_id,
            recipients=['content_creator', 'publisher']
        )

        return approval

    async def request_revision(
        self,
        approval_id: UUID,
        reviewer_id: UUID,
        comments: List[dict]
    ) -> ProjectApproval:
        """Request content revision (Marketing Manager action)"""

        approval = await self._get_approval(approval_id)

        # Update approval status
        approval.status = 'revision_requested'
        approval.reviewed_by = reviewer_id
        approval.reviewed_at = datetime.utcnow()
        approval.review_decision = 'revision_requested'
        approval.revision_count += 1

        # Add comments
        for comment_data in comments:
            comment = ApprovalComment(
                approval_id=approval.id,
                comment_type='revision_request',
                category=comment_data.get('category'),
                severity=comment_data.get('severity'),
                field_name=comment_data.get('field_name'),
                comment=comment_data['comment'],
                created_by=reviewer_id
            )
            self.db.add(comment)

        await self.db.commit()

        # Record workflow transition
        await self._record_workflow_history(
            project_id=approval.project_id,
            approval_id=approval.id,
            from_status='pending_approval',
            to_status='revision_requested',
            transition_type='revise',
            performed_by=reviewer_id,
            comment=f"{len(comments)} issues identified"
        )

        # Notify Content Creator
        await self.notification_service.send_notification(
            event_type='project.revision_requested',
            project_id=approval.project_id,
            recipients=['content_creator'],
            metadata={'issues_count': len(comments)}
        )

        return approval

    async def get_approval_queue(
        self,
        role: str,
        filters: dict = None
    ) -> List[dict]:
        """Get approval queue for specific role"""

        # Build query based on role
        if role == 'marketing_manager':
            status_filter = ['pending_approval']
        elif role == 'publisher':
            status_filter = ['approved', 'publishing']
        else:
            raise ValueError(f"Invalid role: {role}")

        # Execute query and return results
        # (Implementation details omitted for brevity)
        pass
```

---

## Configuration

### Environment Variables

```bash
# Approval Settings
APPROVAL_SLA_DAYS=2
PUBLISHING_SLA_DAYS=3
ENABLE_BULK_APPROVAL=true
MAX_BULK_APPROVAL_COUNT=20

# Deadline Monitoring
ENABLE_DEADLINE_MONITORING=true
DEADLINE_CHECK_INTERVAL_HOURS=1
DEADLINE_WARNING_HOURS=24

# Notifications
NOTIFY_ON_SUBMISSION=true
NOTIFY_ON_APPROVAL=true
NOTIFY_ON_REVISION_REQUEST=true
NOTIFY_ON_DEADLINE_APPROACHING=true
NOTIFY_ON_OVERDUE=true
```

---

## Related Documentation

### Core Documentation
- [Architecture > Workflow Engine](../01-architecture/WORKFLOW_ENGINE.md) - State machine design
- [Modules > Notifications](./NOTIFICATIONS.md) - Alert system
- [Modules > Project Database](./PROJECT_DATABASE.md) - Status storage

### Integration Points
- [Modules > Publishing Workflow](./PUBLISHING_WORKFLOW.md) - Next stage after approval
- [Modules > QA Module](./QA_MODULE.md) - Quality validation before approval

### Frontend
- [Frontend > Pages](../03-frontend/PAGES.md) - UI implementation
- [Frontend > Role-Based Access](../03-frontend/RBAC.md) - Permission controls

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
