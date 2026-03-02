# Module: Notifications

**Module Number:** 7
**Category:** Communication System
**Last Updated:** 2026-01-15
**Status:** Core Module

---

## Table of Contents

1. [Overview](#overview)
2. [Purpose & Goals](#purpose--goals)
3. [Key Features](#key-features)
4. [Architecture](#architecture)
5. [Database Schema](#database-schema)
6. [Notification Events](#notification-events)
7. [API Endpoints](#api-endpoints)
8. [UI Components](#ui-components)
9. [Workflow Diagrams](#workflow-diagrams)
10. [Code Examples](#code-examples)
11. [Configuration](#configuration)
12. [Related Documentation](#related-documentation)

---

## Overview

The **Notifications Module** provides real-time alerts and communication across all departments in the PDP automation system. It notifies users of status changes, approaching deadlines, QA issues, and workflow transitions, ensuring all stakeholders stay informed throughout the project lifecycle.

**Position in System:** Cross-cutting module that integrates with all workflow stages to provide timely alerts.

---

## Purpose & Goals

### Primary Purpose

Keep all team members informed of critical events, status changes, and deadlines through multi-channel notifications (in-app, email, future Slack integration).

### Goals

1. **Real-Time Alerts:** Instant notification of workflow events
2. **Multi-Channel Delivery:** In-app (required) + Email (optional) + Slack (future)
3. **Role-Based Routing:** Send notifications to relevant team members only
4. **Deadline Management:** Proactive alerts for approaching and missed deadlines
5. **User Control:** Per-user notification preferences
6. **Historical Record:** Maintain complete notification history
7. **Read/Unread Tracking:** Mark notifications as read
8. **Batch Notifications:** Group similar events to reduce noise

---

## Key Features

### Core Capabilities

- ✅ **In-App Notifications** - Bell icon with unread count
- ✅ **Email Notifications** - Optional per user preference
- ✅ **Event-Based Triggers** - Automatic on workflow transitions
- ✅ **Role-Based Delivery** - Target specific user roles
- ✅ **Notification Center** - View all notifications with filtering
- ✅ **Read/Unread Status** - Track which notifications have been seen
- ✅ **Mark All as Read** - Bulk status updates
- ✅ **Notification Preferences** - Per-user, per-event type settings
- ✅ **Deadline Alerts** - 24h warnings and overdue notifications
- ✅ **Batch Grouping** - Combine similar events
- ✅ **Future: Slack Integration** - Webhook-based Slack messages

### Notification Channels

**In-App (Required):**
- Bell icon in header
- Unread count badge
- Notification panel/page
- Real-time updates

**Email (Optional):**
- Configurable per user
- Per-event type preferences
- Daily digest option
- Unsubscribe capability

**Slack (Future):**
- Channel-based routing
- Thread-based discussions
- Webhook integration

---

## Architecture

### Components Involved

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND LAYER                             │
├─────────────────────────────────────────────────────────┤
│ • NotificationBell.tsx       - Header bell icon        │
│ • NotificationPanel.tsx      - Dropdown panel          │
│ • NotificationsPage.tsx      - Full notification view  │
│ • NotificationPreferences.tsx - User settings          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           API LAYER (FastAPI)                           │
├─────────────────────────────────────────────────────────┤
│ • /api/notifications         - List notifications      │
│ • /api/notifications/read    - Mark as read            │
│ • /api/notifications/prefs   - User preferences        │
│ • WebSocket /ws/notifications - Real-time updates      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│            SERVICE LAYER (Python)                       │
├─────────────────────────────────────────────────────────┤
│ • NotificationService        - Business logic          │
│ • EventDispatcher            - Trigger notifications   │
│ • EmailService               - Email delivery          │
│ • SlackService (future)      - Slack integration       │
│ • DeadlineMonitor            - Deadline tracking       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│         DATABASE (Neon PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│ • notifications              - Notification records    │
│ • notification_preferences   - User preferences        │
│ • notification_batches       - Grouped notifications   │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Table: `notifications`

**Purpose:** Store all notification records

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recipient
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_role VARCHAR(50),  -- 'content_creator', 'marketing_manager', 'publisher'

    -- Event Information
    event_type VARCHAR(50) NOT NULL,
    -- Types: 'project.created', 'project.pending_approval', 'project.approved',
    --        'project.rejected', 'project.published', 'qa.failed',
    --        'deadline.approaching', 'deadline.missed'

    -- Content
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT,  -- Link to relevant page
    action_label VARCHAR(50),  -- Button text, e.g., "View Project", "Review Now"

    -- Context
    reference_type VARCHAR(50),  -- 'project', 'approval', 'qa_checkpoint'
    reference_id UUID,           -- ID of referenced entity
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Priority
    priority VARCHAR(20) DEFAULT 'normal',
    -- Priority: 'low', 'normal', 'high', 'urgent'

    -- Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    is_sent_email BOOLEAN DEFAULT false,
    email_sent_at TIMESTAMP,
    is_sent_slack BOOLEAN DEFAULT false,
    slack_sent_at TIMESTAMP,

    -- Batching
    batch_id UUID REFERENCES notification_batches(id),

    -- Metadata
    metadata JSONB,  -- Additional context data

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Auto-archive old notifications

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read)
    WHERE is_read = false;
CREATE INDEX idx_notifications_type ON notifications(event_type);
CREATE INDEX idx_notifications_project ON notifications(project_id);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

---

### Table: `notification_preferences`

**Purpose:** User-specific notification settings

```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Channel Preferences
    enable_email_notifications BOOLEAN DEFAULT true,
    enable_slack_notifications BOOLEAN DEFAULT false,

    -- Event-Type Preferences (JSONB for flexibility)
    event_preferences JSONB DEFAULT '{}',
    -- Example:
    -- {
    --   "project.pending_approval": {"in_app": true, "email": true, "slack": false},
    --   "project.approved": {"in_app": true, "email": false, "slack": false},
    --   "deadline.approaching": {"in_app": true, "email": true, "slack": true}
    -- }

    -- Digest Settings
    enable_daily_digest BOOLEAN DEFAULT false,
    digest_time TIME DEFAULT '09:00:00',  -- When to send daily digest

    -- Quiet Hours
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,

    -- Email Settings
    email_address VARCHAR(255),  -- Override user's default email
    unsubscribe_token VARCHAR(255) UNIQUE,

    -- Slack Settings (future)
    slack_user_id VARCHAR(50),
    slack_channel VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_notification_prefs_user ON notification_preferences(user_id);
CREATE INDEX idx_notification_prefs_email ON notification_preferences(enable_email_notifications)
    WHERE enable_email_notifications = true;
```

---

### Table: `notification_batches`

**Purpose:** Group similar notifications to reduce noise

```sql
CREATE TABLE notification_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Batch Information
    batch_type VARCHAR(50) NOT NULL,
    -- Types: 'daily_digest', 'multiple_approvals', 'multiple_qa_issues'

    -- Summary
    summary_title VARCHAR(255),
    summary_message TEXT,

    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,

    -- Recipients
    user_id UUID REFERENCES users(id),

    -- Statistics
    notification_count INTEGER DEFAULT 0,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_notification_batches_user ON notification_batches(user_id);
CREATE INDEX idx_notification_batches_created ON notification_batches(created_at DESC);
```

---

## Notification Events

### Workflow Events

**project.created**
- **Trigger:** New project created
- **Recipients:** Content Creator (who created it)
- **Title:** "New project created: {project_name}"
- **Message:** "Your project '{project_name}' has been created. Start by extracting content and materials."
- **Action:** "View Project"

**project.pending_approval**
- **Trigger:** Project submitted for approval
- **Recipients:** Marketing Manager role
- **Title:** "New project awaiting approval: {project_name}"
- **Message:** "'{project_name}' has been submitted for your review by {creator_name}."
- **Action:** "Review Now"

**project.approved**
- **Trigger:** Marketing Manager approves project
- **Recipients:** Content Creator (submitter), Publisher role
- **Title:** "Project approved: {project_name}"
- **Message:** "'{project_name}' has been approved by {reviewer_name} and is ready for publishing."
- **Action:** "View Project"

**project.rejected**
- **Trigger:** Marketing Manager rejects project
- **Recipients:** Content Creator (submitter)
- **Title:** "Project rejected: {project_name}"
- **Message:** "'{project_name}' was rejected by {reviewer_name}. Reason: {reason}"
- **Action:** "View Feedback"
- **Priority:** high

**project.revision_requested**
- **Trigger:** Marketing Manager requests revision
- **Recipients:** Content Creator (submitter)
- **Title:** "Revision requested: {project_name}"
- **Message:** "{reviewer_name} requested {issue_count} changes to '{project_name}'."
- **Action:** "View Issues"
- **Priority:** high

**project.published**
- **Trigger:** Publisher marks project as published
- **Recipients:** Content Creator (submitter), Marketing Manager
- **Title:** "Project published: {project_name}"
- **Message:** "'{project_name}' is now live at {url}"
- **Action:** "View Page"

---

### QA Events

**qa.failed**
- **Trigger:** QA checkpoint fails with critical issues
- **Recipients:** Content Creator, Marketing Manager
- **Title:** "QA issues detected: {project_name}"
- **Message:** "{critical_count} critical issues found in {checkpoint_name}."
- **Action:** "View Issues"
- **Priority:** high

**qa.warning**
- **Trigger:** QA checkpoint has warnings
- **Recipients:** Content Creator
- **Title:** "QA warnings: {project_name}"
- **Message:** "{warning_count} warnings in {checkpoint_name}. Review recommended."
- **Action:** "View Warnings"
- **Priority:** normal

---

### Deadline Events

**deadline.approaching**
- **Trigger:** Deadline within 24 hours
- **Recipients:** Assigned user, their manager
- **Title:** "Deadline approaching: {project_name}"
- **Message:** "{task_type} deadline is in {hours} hours for '{project_name}'."
- **Action:** "View Project"
- **Priority:** high

**deadline.missed**
- **Trigger:** Deadline passed
- **Recipients:** Assigned user, their manager, admin
- **Title:** "OVERDUE: {project_name}"
- **Message:** "{task_type} for '{project_name}' is {days} days overdue."
- **Action:** "View Project"
- **Priority:** urgent

---

## API Endpoints

### Notification Management

#### `GET /api/notifications`

**Description:** Get user's notifications

**Query Parameters:**
```typescript
{
  is_read?: boolean;
  event_type?: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  limit?: number;
  offset?: number;
}
```

**Response:**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "event_type": "project.pending_approval",
      "title": "New project awaiting approval: Downtown Elite",
      "message": "'Downtown Elite Residence' has been submitted for your review by John Doe.",
      "action_url": "/projects/uuid/approval",
      "action_label": "Review Now",
      "priority": "normal",
      "is_read": false,
      "created_at": "2025-01-15T10:00:00Z",
      "project_id": "uuid"
    }
  ],
  "unread_count": 5,
  "total": 23
}
```

---

#### `PUT /api/notifications/{id}/read`

**Description:** Mark notification as read

**Response:**
```json
{
  "id": "uuid",
  "is_read": true,
  "read_at": "2025-01-15T15:00:00Z"
}
```

---

#### `POST /api/notifications/mark-all-read`

**Description:** Mark all user's notifications as read

**Response:**
```json
{
  "marked_count": 12,
  "success": true
}
```

---

#### `DELETE /api/notifications/{id}`

**Description:** Delete notification

**Response:** 204 No Content

---

### Preferences

#### `GET /api/notifications/preferences`

**Description:** Get user's notification preferences

**Response:**
```json
{
  "user_id": "uuid",
  "enable_email_notifications": true,
  "enable_slack_notifications": false,
  "event_preferences": {
    "project.pending_approval": {
      "in_app": true,
      "email": true,
      "slack": false
    },
    "project.approved": {
      "in_app": true,
      "email": false,
      "slack": false
    },
    "deadline.approaching": {
      "in_app": true,
      "email": true,
      "slack": false
    }
  },
  "enable_daily_digest": false
}
```

---

#### `PUT /api/notifications/preferences`

**Description:** Update notification preferences

**Request Body:**
```json
{
  "enable_email_notifications": true,
  "event_preferences": {
    "project.pending_approval": {
      "in_app": true,
      "email": true,
      "slack": false
    }
  }
}
```

---

### WebSocket Connection

#### `WS /ws/notifications`

**Description:** Real-time notification stream

**Client Connection:**
```typescript
const ws = new WebSocket('wss://api.pdp.com/ws/notifications?token=<auth_token>');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  // Update UI with new notification
  displayNotification(notification);
  updateUnreadCount();
};
```

**Server Message Format:**
```json
{
  "type": "new_notification",
  "notification": {
    "id": "uuid",
    "title": "New project awaiting approval",
    "message": "...",
    "priority": "normal"
  }
}
```

---

## UI Components

### NotificationBell.tsx

**Location:** `frontend/src/components/NotificationBell.tsx`

**Features:**
- Bell icon in header
- Unread count badge
- Click to open dropdown panel
- Real-time updates via WebSocket

---

### NotificationPanel.tsx

**Location:** `frontend/src/components/NotificationPanel.tsx`

**Features:**
- Dropdown showing recent 5 notifications
- Mark as read on view
- "View All" link to full page
- "Mark All as Read" button

---

### NotificationsPage.tsx

**Location:** `frontend/src/pages/NotificationsPage.tsx`

**Features:**
- Full list of all notifications
- Filter by read/unread, type, priority
- Bulk actions: Mark all as read, delete
- Pagination
- Search

---

### NotificationPreferences.tsx

**Location:** `frontend/src/pages/NotificationPreferences.tsx`

**Features:**
- Enable/disable email notifications
- Per-event type settings (in-app, email, Slack)
- Daily digest settings
- Quiet hours configuration
- Email address override

---

## Workflow Diagrams

### Notification Flow

```
EVENT TRIGGER
(e.g., project submitted for approval)
       │
       ▼
┌──────────────────────────────┐
│ EventDispatcher              │
│ - Identify event type        │
│ - Determine recipients       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Check User Preferences       │
│ - In-app enabled?            │
│ - Email enabled?             │
│ - Quiet hours active?        │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Create Notification Record   │
│ - Insert into database       │
│ - Set priority, content      │
└──────────┬───────────────────┘
           │
           ├─────────────┬─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ In-App   │  │  Email   │  │  Slack   │
    │          │  │          │  │ (future) │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │WebSocket │  │Send Email│  │Send Msg  │
  │broadcast │  │via SMTP  │  │to Webhook│
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │             │             │
       ▼             ▼             ▼
  User's Browser  User's Email  Slack Channel
```

---

## Code Examples

### Backend: Notification Service

```python
# backend/app/services/notification_service.py
from typing import List, Dict, Optional
from uuid import UUID
from app.models.notification import Notification
from app.models.notification_preferences import NotificationPreferences
from app.services.email_service import EmailService
from app.services.websocket_manager import WebSocketManager

class NotificationService:
    def __init__(self, db):
        self.db = db
        self.email_service = EmailService()
        self.ws_manager = WebSocketManager()

    async def send_notification(
        self,
        event_type: str,
        project_id: UUID,
        recipients: List[str],  # User IDs or roles
        metadata: dict = None
    ) -> List[Notification]:
        """Send notification to specified recipients"""

        notifications = []

        # Resolve recipients (convert roles to user IDs)
        user_ids = await self._resolve_recipients(recipients, project_id)

        # Get event template
        template = self._get_event_template(event_type, project_id, metadata)

        for user_id in user_ids:
            # Check user preferences
            prefs = await self._get_user_preferences(user_id)

            if not self._should_send(event_type, prefs):
                continue

            # Create notification record
            notification = Notification(
                user_id=user_id,
                event_type=event_type,
                title=template['title'],
                message=template['message'],
                action_url=template.get('action_url'),
                action_label=template.get('action_label'),
                priority=template.get('priority', 'normal'),
                project_id=project_id,
                metadata=metadata
            )
            self.db.add(notification)
            notifications.append(notification)

            # Send via channels based on preferences
            event_prefs = prefs.event_preferences.get(event_type, {})

            # In-app (always sent if notification created)
            await self.ws_manager.broadcast_to_user(
                user_id,
                {
                    'type': 'new_notification',
                    'notification': notification.to_dict()
                }
            )

            # Email (if enabled)
            if event_prefs.get('email', False) and prefs.enable_email_notifications:
                await self.email_service.send_notification_email(
                    user_id,
                    notification
                )
                notification.is_sent_email = True

        await self.db.commit()

        return notifications

    def _get_event_template(
        self,
        event_type: str,
        project_id: UUID,
        metadata: dict
    ) -> Dict:
        """Get notification template for event type"""

        # Fetch project details
        project = await self._get_project(project_id)

        templates = {
            'project.pending_approval': {
                'title': f"New project awaiting approval: {project.name}",
                'message': f"'{project.name}' has been submitted for your review.",
                'action_url': f"/projects/{project_id}/approval",
                'action_label': "Review Now",
                'priority': 'normal'
            },
            'project.approved': {
                'title': f"Project approved: {project.name}",
                'message': f"'{project.name}' has been approved and is ready for publishing.",
                'action_url': f"/projects/{project_id}",
                'action_label': "View Project",
                'priority': 'normal'
            },
            'deadline.approaching': {
                'title': f"Deadline approaching: {project.name}",
                'message': f"Approval deadline is in {metadata.get('hours')} hours.",
                'action_url': f"/projects/{project_id}",
                'action_label': "View Project",
                'priority': 'high'
            }
        }

        return templates.get(event_type, {
            'title': 'Notification',
            'message': event_type,
            'priority': 'normal'
        })

    async def _resolve_recipients(
        self,
        recipients: List[str],
        project_id: UUID
    ) -> List[UUID]:
        """Convert recipient specifiers to user IDs"""

        user_ids = []

        for recipient in recipients:
            if recipient in ['marketing_manager', 'publisher', 'content_creator']:
                # Resolve role to user IDs
                users = await self._get_users_by_role(recipient)
                user_ids.extend([u.id for u in users])
            else:
                # Assume it's a user ID
                user_ids.append(UUID(recipient))

        return list(set(user_ids))  # Remove duplicates
```

---

### Frontend: Notification Bell Component

```typescript
// frontend/src/components/NotificationBell.tsx
import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { notificationsApi } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';

export function NotificationBell() {
  const [showPanel, setShowPanel] = useState(false);

  // Fetch notifications
  const { data: notifications, refetch } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list({ limit: 5 })
  });

  // WebSocket for real-time updates
  const { lastMessage } = useWebSocket('/ws/notifications');

  useEffect(() => {
    if (lastMessage?.type === 'new_notification') {
      // Refetch notifications to update list
      refetch();

      // Show browser notification
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(lastMessage.notification.title, {
          body: lastMessage.notification.message,
          icon: '/logo.png'
        });
      }
    }
  }, [lastMessage]);

  const unreadCount = notifications?.unread_count || 0;

  return (
    <div className="relative">
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="relative p-2 hover:bg-gray-100 rounded-full"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showPanel && (
        <NotificationPanel
          notifications={notifications?.notifications || []}
          onClose={() => setShowPanel(false)}
        />
      )}
    </div>
  );
}
```

---

## Configuration

### Environment Variables

```bash
# Notification Settings
ENABLE_NOTIFICATIONS=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_SLACK_NOTIFICATIONS=false

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=notifications@your-domain.com
SMTP_PASSWORD=...
NOTIFICATION_FROM_EMAIL=notifications@your-domain.com

# WebSocket
WEBSOCKET_ENABLED=true
WEBSOCKET_PING_INTERVAL=30

# Slack (Future)
SLACK_WEBHOOK_URL=...
SLACK_BOT_TOKEN=...

# Cleanup
NOTIFICATION_RETENTION_DAYS=90
AUTO_ARCHIVE_READ_NOTIFICATIONS=true
```

---

## Related Documentation

### Core Documentation
- [Modules > Approval Workflow](./APPROVAL_WORKFLOW.md) - Workflow notifications
- [Modules > Publishing Workflow](./PUBLISHING_WORKFLOW.md) - Publication alerts
- [Modules > QA Module](./QA_MODULE.md) - QA issue notifications

### Integration Points
- [Backend > WebSocket](../04-backend/WEBSOCKET.md) - Real-time delivery
- [Integrations > Email](../05-integrations/EMAIL.md) - Email service
- [Integrations > Slack](../05-integrations/SLACK.md) - Slack integration (future)

---

**Document Status:** Complete
**Last Reviewed:** 2026-01-15
**Maintained By:** Backend Team
**Contact:** backend-team@your-domain.com
