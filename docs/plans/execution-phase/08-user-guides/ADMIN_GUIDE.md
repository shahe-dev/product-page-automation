# Admin Guide

**PDP Automation v.3**
*Your complete guide to system administration and management*

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Management](#user-management)
4. [Monitoring System Health](#monitoring-system-health)
5. [Viewing Audit Logs](#viewing-audit-logs)
6. [Managing Prompts](#managing-prompts)
7. [Troubleshooting Failed Jobs](#troubleshooting-failed-jobs)
8. [Managing Custom Fields](#managing-custom-fields)
9. [Export & Reports](#export--reports)
10. [Cost Tracking](#cost-tracking)
11. [Security & Access Control](#security--access-control)
12. [System Configuration](#system-configuration)
13. [Backup & Recovery](#backup--recovery)
14. [Best Practices](#best-practices)
15. [Common Issues & Solutions](#common-issues--solutions)
16. [FAQs](#faqs)

---

## Introduction

### Who Is This Guide For?

This guide is for **System Administrators** who are responsible for:
- Managing user accounts and permissions
- Monitoring system health and performance
- Troubleshooting failed jobs and errors
- Managing AI prompts and templates
- Tracking costs and usage
- Ensuring system security
- Maintaining audit trails

You're the keeper of the system, ensuring smooth operation for all users.

### What You'll Learn

By the end of this guide, you'll be able to:
- Add, modify, and deactivate user accounts
- Monitor system metrics and health indicators
- Troubleshoot and resolve failed processing jobs
- Update AI prompts for content generation
- Generate reports and exports
- Track API costs (Anthropic, Google Gemini)
- Maintain security and access controls
- Perform system backups and recovery

---

## Getting Started

### Admin Dashboard Overview

As an admin, you have access to the Admin Dashboard:

```
╔════════════════════════════════════════════════════════════╗
║ Admin Dashboard                          Last updated: Now ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ System Health                                      ✓ Good  ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ Uptime: 99.8% (30 days)                         ✓     │║
║ │ Active Users: 12                                       │║
║ │ Projects This Week: 47                                 │║
║ │ Failed Jobs: 2 (requires attention)             ⚠     │║
║ │ API Cost This Month: $245.30                           │║
║ │ Database Size: 2.3 GB                                  │║
║ │ Storage Usage: 45.2 GB / 500 GB                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ Quick Actions                                              ║
║ [Add User] [View Failed Jobs] [Export Data] [View Logs]  ║
║                                                            ║
║ Recent Activity                                            ║
║ • Sarah Chen uploaded PDF "Marina Heights"         2m ago ║
║ • Jessica Adams approved "Palm Gardens"            15m ago║
║ • System: Anthropic API quota at 75%                  1h ago ║
║ • Mike Johnson published "Downtown Views"          2h ago ║
║                                                            ║
║ Alerts (3)                                                 ║
║ ⚠ 2 failed jobs need attention                            ║
║ ⚠ Anthropic API quota above 75%                              ║
║ ⚠ 1 user account locked (failed logins)                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Admin Permissions

As an admin, you can:
- ✓ View all projects (regardless of creator)
- ✓ Edit any project
- ✓ Delete projects
- ✓ Manage users
- ✓ Access audit logs
- ✓ Modify prompts
- ✓ Configure system settings
- ✓ Export data
- ✓ View cost reports

Regular users cannot access these functions.

---

## User Management

### Viewing All Users

Navigate to **Admin > Users**:

```
╔════════════════════════════════════════════════════════════╗
║ User Management                      [+ Add User]          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Active Users (12)                                          ║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ Sarah Chen                              sarah@your-domain.com   │║
║ │ Role: User | Last Login: 2 hours ago                   │║
║ │ Projects: 23 | Joined: Dec 1, 2025                     │║
║ │ [Edit] [Deactivate] [View Activity]                    │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ Jessica Adams                        jessica@your-domain.com    │║
║ │ Role: User | Last Login: 1 hour ago                    │║
║ │ Projects: 0 (Marketing Manager) | Joined: Dec 1, 2025  │║
║ │ [Edit] [Deactivate] [View Activity]                    │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ Ahmed Al-Mansoori                    ahmed@your-domain.com      │║
║ │ Role: Admin | Last Login: 10 minutes ago               │║
║ │ Projects: N/A (Admin) | Joined: Nov 15, 2025           │║
║ │ [Edit] [View Activity]                                 │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ Inactive Users (2)                                         ║
║ [Show Inactive Users]                                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Adding a New User

**Step 1:** Click **"+ Add User"**

**Step 2:** Enter user email:

```
┌──────────────────────────────────────────────────────────┐
│ Add New User                                             │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Email Address:                                           │
│ [john.doe@your-domain.com                                      ]  │
│                                                          │
│ ⚠ User must have @your-domain.com email address                   │
│ ⚠ User must sign in with Google OAuth to activate        │
│                                                          │
│ Assign Role:                                             │
│ ( ) Admin - Full system access                           │
│ (•) User - Standard access                               │
│                                                          │
│ Send Welcome Email:                                      │
│ [✓] Yes, send onboarding email with login link           │
│                                                          │
│ [Cancel]  [Add User]                                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Click **"Add User"**

**Step 4:** User receives email:
```
Subject: Welcome to PDP Automation v.3

Hi John,

You've been granted access to PDP Automation v.3!

Click here to sign in: https://pdp-automation.your-domain.com

Use your @your-domain.com Google account to log in.

Need help? Check out the user guides or contact support.

Best,
PDP Automation Team
```

**Step 5:** User signs in with Google OAuth - account activated

### User Roles

**Admin Role:**
- Full system access
- Can manage users
- Can delete projects
- Can modify prompts
- Can access audit logs
- Can configure settings

**User Role:**
- Can create projects
- Can edit own projects
- Can view own projects
- Cannot delete projects
- Cannot access admin functions

### Editing User Details

**Step 1:** Click **"Edit"** on any user

**Step 2:** Modify details:

```
┌──────────────────────────────────────────────────────────┐
│ Edit User - Sarah Chen                                   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Email: sarah@your-domain.com (cannot change)                      │
│                                                          │
│ Display Name:                                            │
│ [Sarah Chen                                           ]  │
│                                                          │
│ Role:                                                    │
│ (•) User                                                 │
│ ( ) Admin                                                │
│                                                          │
│ Status:                                                  │
│ (•) Active                                               │
│ ( ) Inactive                                             │
│                                                          │
│ Permissions (Advanced):                                  │
│ [✓] Can upload PDFs                                      │
│ [✓] Can edit projects                                    │
│ [✓] Can submit for approval                              │
│ [ ] Can approve projects (Marketing Manager)             │
│ [ ] Can publish projects (Publisher)                     │
│                                                          │
│ [Cancel]  [Save Changes]                                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Deactivating a User

**When to deactivate:**
- Employee leaves company
- User no longer needs access
- Security concern

**Step 1:** Click **"Deactivate"** on user

**Step 2:** Confirm deactivation:

```
┌──────────────────────────────────────────────────────────┐
│ Deactivate User                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Are you sure you want to deactivate Sarah Chen?         │
│                                                          │
│ What happens:                                            │
│ • User loses access immediately                          │
│ • Cannot log in                                          │
│ • Projects remain in system (not deleted)                │
│ • Can be reactivated later if needed                     │
│                                                          │
│ Reason for deactivation (optional):                      │
│ [Left company                                         ]  │
│                                                          │
│ [Cancel]  [Deactivate User]                              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** User deactivated - moved to "Inactive Users" list

**Note:** User's projects remain in system. Reassign projects to other users if needed.

### Viewing User Activity

Click **"View Activity"** to see user's history:

```
╔════════════════════════════════════════════════════════════╗
║ User Activity - Sarah Chen                                ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Account Created: Dec 1, 2025                               ║
║ Last Login: 2 hours ago (Jan 15, 2026 at 8:00 AM)         ║
║ Total Logins: 145                                          ║
║ Projects Created: 23                                       ║
║                                                            ║
║ Recent Activity:                                           ║
║ • Jan 15, 8:00 AM - Logged in                              ║
║ • Jan 15, 8:05 AM - Uploaded "Marina Heights" PDF          ║
║ • Jan 15, 9:15 AM - Submitted "Marina Heights" for approval║
║ • Jan 14, 3:30 PM - Edited "Palm Gardens"                  ║
║ • Jan 14, 2:00 PM - Created project "Downtown Views"       ║
║                                                            ║
║ Projects:                                                  ║
║ • Marina Heights (In Approval)                             ║
║ • Palm Gardens (Processing)                                ║
║ • Downtown Views (Published)                               ║
║ • [View All 23 Projects]                                   ║
║                                                            ║
║ Performance Metrics:                                       ║
║ • Avg. Processing Time: 8.2 minutes                        ║
║ • Approval Rate: 95% (22/23 approved on first try)         ║
║ • Avg. Time to Approval: 4.5 hours                         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Monitoring System Health

### Dashboard Metrics

Key metrics to monitor daily:

```
╔════════════════════════════════════════════════════════════╗
║ System Health Dashboard                                   ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Server Status                                      ✓ Good  ║
║ ├─ API Server: Online (99.9% uptime)                      ║
║ ├─ Database: Connected (5ms latency)                      ║
║ ├─ Redis Cache: Active (12.5k keys)                       ║
║ └─ Worker Processes: 4/4 running                          ║
║                                                            ║
║ Processing Queue                                   ✓ Good  ║
║ ├─ Active Jobs: 3                                         ║
║ ├─ Pending Jobs: 2                                        ║
║ ├─ Failed Jobs: 2 ⚠                                       ║
║ └─ Avg. Queue Time: 45 seconds                            ║
║                                                            ║
║ API Usage (Last 24h)                              ✓ Normal ║
║ ├─ Anthropic API Calls: 145 ($12.30)                         ║
║ ├─ Google Gemini Calls: 87 ($3.25)                        ║
║ ├─ Cloud Storage: 2.3 GB uploaded                         ║
║ └─ Total API Cost: $15.55                                 ║
║                                                            ║
║ Database                                           ✓ Good  ║
║ ├─ Size: 2.3 GB / 10 GB                                   ║
║ ├─ Connection Pool: 8/20 used                             ║
║ ├─ Slow Queries: 0                                        ║
║ └─ Last Backup: 2 hours ago                               ║
║                                                            ║
║ Storage                                            ✓ Good  ║
║ ├─ Total: 45.2 GB / 500 GB (9% used)                      ║
║ ├─ PDFs: 12.1 GB                                          ║
║ ├─ Images: 28.6 GB                                        ║
║ └─ Exports: 4.5 GB                                        ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Alert Notifications

System sends alerts for:

**Critical Alerts (immediate action required):**
- ✗ Database connection lost
- ✗ API server down
- ✗ Storage quota exceeded (> 90%)
- ✗ Failed job rate > 25%

**Warning Alerts (monitor closely):**
- ⚠ Anthropic API quota > 80%
- ⚠ Failed jobs present
- ⚠ Slow query detected (> 5 seconds)
- ⚠ Storage quota > 75%

**Info Alerts (informational):**
- ℹ New user registered
- ℹ High traffic detected
- ℹ Backup completed

### Health Check Endpoints

For external monitoring tools:

```
GET /api/health
Response:
{
  "status": "healthy",
  "uptime": 2592000,
  "database": "connected",
  "redis": "connected",
  "workers": 4
}
```

```
GET /api/health/detailed
Response:
{
  "status": "healthy",
  "components": {
    "api": { "status": "up", "latency": 12 },
    "database": { "status": "up", "latency": 5 },
    "redis": { "status": "up", "latency": 1 },
    "workers": { "running": 4, "failed": 0 }
  },
  "metrics": {
    "active_jobs": 3,
    "pending_jobs": 2,
    "failed_jobs": 2
  }
}
```

---

## Viewing Audit Logs

Audit logs track all system activity for security and compliance.

### Accessing Audit Logs

Navigate to **Admin > Audit Logs**:

```
╔════════════════════════════════════════════════════════════╗
║ Audit Logs                    Date: [Last 7 Days ▼]       ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Filter: [All Events ▼] [All Users ▼]        🔍 Search     ║
║                                                            ║
║ Jan 15, 2026 - 9:15 AM                                     ║
║ USER_ACTION | Sarah Chen submitted project for approval   ║
║ Project: Marina Heights | IP: 192.168.1.45                 ║
║ [View Details]                                             ║
║                                                            ║
║ Jan 15, 2026 - 8:05 AM                                     ║
║ FILE_UPLOAD | Sarah Chen uploaded PDF                      ║
║ File: marina_heights_brochure.pdf (12.3 MB)                ║
║ [View Details]                                             ║
║                                                            ║
║ Jan 15, 2026 - 8:00 AM                                     ║
║ USER_LOGIN | Sarah Chen logged in                          ║
║ Method: Google OAuth | IP: 192.168.1.45                    ║
║ [View Details]                                             ║
║                                                            ║
║ Jan 15, 2026 - 7:45 AM                                     ║
║ ADMIN_ACTION | Ahmed Al-Mansoori updated prompt            ║
║ Prompt: OPR Meta Description (v3 → v4)                     ║
║ [View Details] [View Changes]                              ║
║                                                            ║
║ Jan 14, 2026 - 6:30 PM                                     ║
║ USER_FAILED_LOGIN | unknown@example.com                    ║
║ Reason: Email not whitelisted | IP: 203.45.67.89           ║
║ [View Details] [Block IP]                                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Event Types Logged

**User Events:**
- USER_LOGIN
- USER_LOGOUT
- USER_FAILED_LOGIN
- USER_CREATED
- USER_DEACTIVATED

**Project Events:**
- PROJECT_CREATED
- PROJECT_UPDATED
- PROJECT_DELETED
- PROJECT_SUBMITTED
- PROJECT_APPROVED
- PROJECT_REJECTED
- PROJECT_PUBLISHED

**File Events:**
- FILE_UPLOAD
- FILE_DOWNLOAD
- FILE_DELETED

**Admin Events:**
- ADMIN_ACTION
- PROMPT_UPDATED
- SETTINGS_CHANGED
- USER_ROLE_CHANGED

**System Events:**
- SYSTEM_ERROR
- API_QUOTA_WARNING
- BACKUP_COMPLETED

### Detailed Log View

Click **"View Details"** on any log entry:

```
╔════════════════════════════════════════════════════════════╗
║ Audit Log Detail                                           ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Event Type: USER_ACTION                                    ║
║ Action: Submitted project for approval                     ║
║                                                            ║
║ User: Sarah Chen (sarah@your-domain.com)                            ║
║ Role: User                                                 ║
║                                                            ║
║ Timestamp: Jan 15, 2026 at 9:15:32 AM UTC                  ║
║ IP Address: 192.168.1.45                                   ║
║ User Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...   ║
║                                                            ║
║ Project Details:                                           ║
║ • Project ID: proj_abc123                                  ║
║ • Project Name: Marina Heights                             ║
║ • Website: OPR                                             ║
║                                                            ║
║ Additional Data:                                           ║
║ {                                                          ║
║   "submission_notes": "PDF pricing verified with sales",   ║
║   "qa_score": 98,                                          ║
║   "previous_status": "review",                             ║
║   "new_status": "in_approval"                              ║
║ }                                                          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Exporting Audit Logs

For compliance or analysis:

**Step 1:** Click **"Export Logs"**

**Step 2:** Select export options:

```
┌──────────────────────────────────────────────────────────┐
│ Export Audit Logs                                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Date Range:                                              │
│ From: [Jan 1, 2026  ▼]  To: [Jan 15, 2026 ▼]            │
│                                                          │
│ Event Types:                                             │
│ [✓] User Events                                          │
│ [✓] Project Events                                       │
│ [✓] Admin Events                                         │
│ [ ] System Events                                        │
│                                                          │
│ Format:                                                  │
│ (•) CSV                                                  │
│ ( ) JSON                                                 │
│ ( ) Excel                                                │
│                                                          │
│ [Cancel]  [Export]                                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Download exported file

---

## Managing Prompts

AI prompts control how content is generated. You can view, edit, and version prompts.

### Accessing Prompt Management

Navigate to **Admin > Prompts**:

```
╔════════════════════════════════════════════════════════════╗
║ Prompt Management                                          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Website: [All ▼] | Category: [All ▼]                      ║
║                                                            ║
║ OPR Prompts                                                ║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ OPR Meta Title                             Version: 3  │║
║ │ Generates SEO-optimized meta titles                    │║
║ │ Last updated: Jan 10, 2026 by Ahmed                    │║
║ │ [View] [Edit] [Version History]                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ OPR Meta Description                       Version: 4  │║
║ │ Generates compelling meta descriptions                 │║
║ │ Last updated: Jan 15, 2026 by Ahmed                    │║
║ │ [View] [Edit] [Version History]                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ OPR Overview Content                       Version: 2  │║
║ │ Generates 500-1000 word property overviews             │║
║ │ Last updated: Dec 20, 2025 by Ahmed                    │║
║ │ [View] [Edit] [Version History]                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Viewing a Prompt

Click **"View"** to see prompt details:

```
╔════════════════════════════════════════════════════════════╗
║ Prompt: OPR Meta Description (v4)                         ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Name: OPR Meta Description                                 ║
║ Category: SEO Content                                      ║
║ Website: Off-Plan Residences                               ║
║ Version: 4 (current)                                       ║
║                                                            ║
║ Prompt Text:                                               ║
║ ┌────────────────────────────────────────────────────────┐ ║
║ │ You are an expert SEO copywriter for luxury Dubai real │ ║
║ │ estate. Generate a compelling meta description for the │ ║
║ │ following property.                                    │ ║
║ │                                                        │ ║
║ │ Requirements:                                          │ ║
║ │ - Maximum 160 characters                               │ ║
║ │ - Include project name and location                    │ ║
║ │ - Include starting price if available                  │ ║
║ │ - Mention key selling points (waterfront, luxury, etc.)│ ║
║ │ - Use action-oriented language ("Discover", "Explore") │ ║
║ │ - Be compelling and click-worthy                       │ ║
║ │                                                        │ ║
║ │ Property details:                                      │ ║
║ │ {{PROPERTY_DATA}}                                      │ ║
║ └────────────────────────────────────────────────────────┘ ║
║                                                            ║
║ Variables Used:                                            ║
║ • {{PROPERTY_DATA}} - Extracted property information       ║
║                                                            ║
║ Performance:                                               ║
║ • Used in: 147 projects                                    ║
║ • Avg. Character Count: 148/160                            ║
║ • Revision Rate: 8% (12/147 needed manual editing)         ║
║                                                            ║
║ [Edit Prompt] [Create New Version] [Test Prompt]          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Editing a Prompt

**Important:** Editing a prompt creates a new version. Old projects retain old prompt version.

**Step 1:** Click **"Edit Prompt"**

**Step 2:** Modify prompt text:

```
┌──────────────────────────────────────────────────────────┐
│ Edit Prompt: OPR Meta Description                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Prompt Text:                                             │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [Edit the prompt text here...]                       │ │
│ │                                                      │ │
│ │                                                      │ │
│ │                                                      │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Change Reason (required):                                │
│ [Improved clarity and added specific instructions       │
│  for handling waterfront properties]                     │
│                                                          │
│ Test Before Saving:                                      │
│ [Test with Sample Data]                                  │
│                                                          │
│ This will create version 5.                              │
│ New projects will use v5. Old projects remain on v4.     │
│                                                          │
│ [Cancel]  [Save New Version]                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Click **"Test with Sample Data"** (recommended)

**Step 4:** Review test output

**Step 5:** Click **"Save New Version"**

New version becomes active for all new projects.

### Version History

Click **"Version History"** to see all prompt versions:

```
╔════════════════════════════════════════════════════════════╗
║ Version History: OPR Meta Description                     ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ v4 (Current) - Jan 15, 2026 by Ahmed                       ║
║ "Improved clarity and added waterfront instructions"      ║
║ [View] [Compare with v3]                                   ║
║                                                            ║
║ v3 - Jan 10, 2026 by Ahmed                                 ║
║ "Added character count enforcement"                        ║
║ [View] [Revert to This Version]                            ║
║                                                            ║
║ v2 - Dec 15, 2025 by Ahmed                                 ║
║ "Improved tone for luxury properties"                      ║
║ [View] [Revert to This Version]                            ║
║                                                            ║
║ v1 - Nov 20, 2025 by Ahmed                                 ║
║ "Initial prompt"                                           ║
║ [View]                                                     ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Testing Prompts

Before deploying a new prompt version, test it:

**Step 1:** Click **"Test Prompt"**

**Step 2:** Enter sample data:

```
┌──────────────────────────────────────────────────────────┐
│ Test Prompt                                              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Sample Property Data:                                    │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ {                                                    │ │
│ │   "name": "Marina Heights",                          │ │
│ │   "location": "Dubai Marina",                        │ │
│ │   "developer": "Emaar Properties",                   │ │
│ │   "starting_price": "AED 1,200,000",                 │ │
│ │   "unit_types": "1, 2, 3 BR",                        │ │
│ │   "features": ["Waterfront", "Luxury", "Pool"]       │ │
│ │ }                                                    │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ [Run Test]                                               │
│                                                          │
│ Generated Output:                                        │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Discover luxury waterfront living at Marina Heights  │ │
│ │ with stunning 1, 2 & 3 bedroom apartments. Starting │ │
│ │ from AED 1.2M in the heart of Dubai Marina.          │ │
│ │                                                      │ │
│ │ Character count: 152/160 ✓                           │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ [Re-run] [Save This Version]                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Verify output meets requirements

**Step 4:** If good, save new version

---

## Troubleshooting Failed Jobs

When processing fails, you need to diagnose and resolve the issue.

### Viewing Failed Jobs

Navigate to **Admin > Failed Jobs**:

```
╔════════════════════════════════════════════════════════════╗
║ Failed Jobs                                        (2)    ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ ✗ Palm Residences PDF Processing                      │║
║ │ Failed: Jan 15, 2026 at 8:30 AM                        │║
║ │ User: Sarah Chen                                       │║
║ │ Error: PDF encrypted - cannot extract text             │║
║ │ [View Details] [Retry] [Cancel Job]                    │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ ✗ Downtown Towers Image Extraction                    │║
║ │ Failed: Jan 14, 2026 at 3:45 PM                        │║
║ │ User: Mike Johnson                                     │║
║ │ Error: Anthropic API quota exceeded                       │║
║ │ [View Details] [Retry] [Cancel Job]                    │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Common Failure Reasons

**PDF Issues:**
- **Encrypted PDF:** Password-protected or encrypted
- **Corrupted PDF:** File damaged or incomplete
- **Invalid PDF:** Not a valid PDF file
- **Too Large:** Exceeds 50MB limit

**API Issues:**
- **Anthropic Quota Exceeded:** API rate limit reached
- **Gemini Quota Exceeded:** Google Gemini rate limit reached
- **API Timeout:** API request took too long
- **API Error:** Unexpected API response

**System Issues:**
- **Out of Memory:** Processing requires too much RAM
- **Storage Full:** No space for uploaded files
- **Database Error:** Connection or query failed

### Detailed Error View

Click **"View Details"** on failed job:

```
╔════════════════════════════════════════════════════════════╗
║ Failed Job Details                                         ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Job ID: job_xyz789                                         ║
║ Project: Palm Residences                                   ║
║ User: Sarah Chen (sarah@your-domain.com)                            ║
║                                                            ║
║ Status: Failed                                             ║
║ Started: Jan 15, 2026 at 8:28 AM                           ║
║ Failed: Jan 15, 2026 at 8:30 AM                            ║
║ Duration: 2 minutes                                        ║
║                                                            ║
║ Error Code: PDF_ENCRYPTED                                  ║
║ Error Message:                                             ║
║ "The uploaded PDF is encrypted and cannot be processed.    ║
║  Please provide an unencrypted version of the PDF."        ║
║                                                            ║
║ Stack Trace:                                               ║
║ ┌────────────────────────────────────────────────────────┐ ║
║ │ at PDFExtractor.extractText (pdf-extractor.js:45)      │ ║
║ │ at ProcessingPipeline.step2 (pipeline.js:120)          │ ║
║ │ at ProcessingPipeline.run (pipeline.js:80)             │ ║
║ └────────────────────────────────────────────────────────┘ ║
║                                                            ║
║ File Info:                                                 ║
║ • Filename: palm_residences_brochure.pdf                   ║
║ • Size: 15.2 MB                                            ║
║ • Upload Time: Jan 15, 2026 at 8:27 AM                     ║
║                                                            ║
║ Actions:                                                   ║
║ [Download PDF] [Retry Job] [Cancel Job] [Notify User]     ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Resolving Failed Jobs

#### Scenario 1: Encrypted PDF

**Error:** "PDF encrypted - cannot extract text"

**Solution:**
1. Click **"Notify User"**
2. Send message: "PDF is encrypted. Please provide unencrypted version."
3. User uploads new PDF
4. Click **"Cancel Job"** (old job)
5. User re-uploads

#### Scenario 2: API Quota Exceeded

**Error:** "Anthropic API quota exceeded"

**Solution:**
1. Check current quota usage
2. Option A: Wait for quota to reset (1 hour)
3. Option B: Increase quota limit (contact Anthropic)
4. Click **"Retry Job"** after quota available

#### Scenario 3: Corrupted PDF

**Error:** "Invalid PDF structure"

**Solution:**
1. Click **"Download PDF"** and attempt to open it
2. If corrupted, notify user: "PDF corrupted, please re-upload"
3. Click **"Cancel Job"**
4. User re-uploads

#### Scenario 4: System Error

**Error:** "Database connection lost"

**Solution:**
1. Check database health in System Health dashboard
2. Restart database connection if needed
3. Click **"Retry Job"**

### Bulk Retry

If multiple jobs failed due to temporary issue (e.g., API outage):

**Step 1:** Select multiple failed jobs

**Step 2:** Click **"Bulk Retry"**

All selected jobs re-queued for processing.

---

## Managing Custom Fields

Custom fields allow flexible data capture for different property types.

### Viewing Custom Fields

Navigate to **Admin > Custom Fields**:

```
╔════════════════════════════════════════════════════════════╗
║ Custom Fields                          [+ Add Field]       ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Standard Fields (Always Present)                           ║
║ • Developer Name (Text)                                    ║
║ • Starting Price (Currency)                                ║
║ • Handover Date (Date)                                     ║
║ • Payment Plan (Text)                                      ║
║                                                            ║
║ Custom Fields (Optional)                                   ║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ Service Charge                                         │║
║ │ Type: Currency | Required: No                          │║
║ │ Templates: OPR, MPP, ADRE                              │║
║ │ [Edit] [Delete]                                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
║ ┌────────────────────────────────────────────────────────┐║
║ │ ROI Percentage                                         │║
║ │ Type: Number (%) | Required: No                        │║
║ │ Templates: Aggregators, Commercial                     │║
║ │ [Edit] [Delete]                                        │║
║ └────────────────────────────────────────────────────────┘║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Adding Custom Field

**Step 1:** Click **"+ Add Field"**

**Step 2:** Configure field:

```
┌──────────────────────────────────────────────────────────┐
│ Add Custom Field                                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Field Name:                                              │
│ [Rental Yield                                         ]  │
│                                                          │
│ Field Type:                                              │
│ ( ) Text                                                 │
│ ( ) Number                                               │
│ (•) Percentage                                           │
│ ( ) Currency                                             │
│ ( ) Date                                                 │
│ ( ) Yes/No                                               │
│                                                          │
│ Required:                                                │
│ ( ) Yes  (•) No                                          │
│                                                          │
│ Applies to Templates:                                    │
│ [ ] Aggregators                                          │
│ [ ] OPR                                                  │
│ [ ] MPP                                                  │
│ [ ] ADOP                                                 │
│ [ ] ADRE                                                 │
│ [✓] Commercial                                           │
│                                                          │
│ Help Text (shown to users):                              │
│ [Expected annual rental return as percentage          ]  │
│                                                          │
│ [Cancel]  [Add Field]                                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Click **"Add Field"**

Field now appears in project forms for selected templates.

---

## Export & Reports

### Available Reports

Navigate to **Admin > Reports**:

```
╔════════════════════════════════════════════════════════════╗
║ Reports & Exports                                          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Standard Reports                                           ║
║                                                            ║
║ • Project Summary Report                                   ║
║   All projects with status, dates, users                   ║
║   [Generate CSV] [Generate Excel]                          ║
║                                                            ║
║ • User Activity Report                                     ║
║   User logins, projects created, performance metrics       ║
║   [Generate CSV] [Generate Excel]                          ║
║                                                            ║
║ • API Cost Report                                          ║
║   Anthropic & Gemini usage and costs by day/week/month        ║
║   [Generate CSV] [Generate Excel]                          ║
║                                                            ║
║ • Failed Jobs Report                                       ║
║   All failed jobs with error details                       ║
║   [Generate CSV] [Generate Excel]                          ║
║                                                            ║
║ • Audit Log Export                                         ║
║   Complete audit trail for compliance                      ║
║   [Generate CSV] [Generate JSON]                           ║
║                                                            ║
║ Custom Reports                                             ║
║ [Create Custom Report]                                     ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Generating Reports

**Step 1:** Click report type (e.g., "Generate CSV" for Project Summary)

**Step 2:** Select date range and filters:

```
┌──────────────────────────────────────────────────────────┐
│ Generate Project Summary Report                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Date Range:                                              │
│ From: [Jan 1, 2026  ▼]  To: [Jan 15, 2026 ▼]            │
│                                                          │
│ Filters:                                                 │
│ Website: [All ▼]                                         │
│ Status: [All ▼]                                          │
│ User: [All ▼]                                            │
│                                                          │
│ Include Columns:                                         │
│ [✓] Project Name                                         │
│ [✓] Developer                                            │
│ [✓] Starting Price                                       │
│ [✓] Status                                               │
│ [✓] Created Date                                         │
│ [✓] Creator                                              │
│ [ ] Detailed Content (large file size)                   │
│                                                          │
│ [Cancel]  [Generate Report]                              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Step 3:** Click **"Generate Report"**

**Step 4:** Download CSV/Excel file

---

## Cost Tracking

Monitor API usage and costs.

### Cost Dashboard

Navigate to **Admin > Cost Tracking**:

```
╔════════════════════════════════════════════════════════════╗
║ Cost Tracking                     Month: [January 2026 ▼] ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║ Total Cost This Month: $245.30                             ║
║                                                            ║
║ Anthropic API                                        $198.50  ║
║ ├─ Claude Sonnet 4.5 Calls: 1,245 ($185.20)                          ║
║ ├─ Claude Sonnet 4.5-mini Calls: 3,567 ($13.30)                      ║
║ └─ Quota Used: 75% of monthly limit ⚠                     ║
║                                                            ║
║ Google Gemini API                                  $46.80  ║
║ ├─ Gemini 1.5 Pro: 487 calls ($41.50)                     ║
║ ├─ Gemini 1.5 Flash: 1,234 calls ($5.30)                  ║
║ └─ Quota Used: 42% of monthly limit ✓                     ║
║                                                            ║
║ Cloud Storage (Google Cloud)                       $15.00  ║
║ ├─ Storage: 45.2 GB ($9.00)                               ║
║ ├─ Bandwidth: 120 GB ($6.00)                              ║
║                                                            ║
║ Cost by Project:                                           ║
║ • Marina Heights: $5.20                                    ║
║ • Palm Gardens: $4.80                                      ║
║ • Downtown Views: $6.10                                    ║
║ [View All Projects]                                        ║
║                                                            ║
║ Estimated Month-End Total: $315.00                         ║
║                                                            ║
║ [Download Cost Report] [Set Budget Alerts]                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

### Setting Budget Alerts

**Step 1:** Click **"Set Budget Alerts"**

**Step 2:** Configure thresholds:

```
┌──────────────────────────────────────────────────────────┐
│ Budget Alert Configuration                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Monthly Budget: [$500                                 ]  │
│                                                          │
│ Alert Thresholds:                                        │
│ [✓] 75% of budget ($375) - Warning                       │
│ [✓] 90% of budget ($450) - Critical                      │
│ [✓] 100% of budget ($500) - Stop processing              │
│                                                          │
│ Notification Recipients:                                 │
│ [ahmed@your-domain.com, finance@your-domain.com                         ]  │
│                                                          │
│ [Cancel]  [Save Alert Settings]                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Security & Access Control

### IP Whitelisting

Restrict access to specific IP addresses:

**Admin > Security > IP Whitelist**

```
Whitelisted IPs:
• 192.168.1.0/24 (Office network)
• 203.45.67.89 (Remote worker)

[Add IP Range]
```

### Session Management

View active sessions:

```
Active Sessions (15)
• Sarah Chen - 192.168.1.45 - 2h ago
• Ahmed Al-Mansoori - 192.168.1.10 - 5m ago
[Revoke] next to each session
```

### Two-Factor Authentication

Enable 2FA for admin accounts (recommended):

```
Admin > Security > Two-Factor Authentication
[Enable 2FA for All Admins]
```

---

## Best Practices

1. **Daily Health Check:** Review dashboard every morning
2. **Monitor Failed Jobs:** Resolve within 24 hours
3. **Audit Log Review:** Weekly review for suspicious activity
4. **Prompt Testing:** Always test before deploying new prompt versions
5. **Cost Monitoring:** Set budget alerts to avoid surprises
6. **Regular Backups:** Verify backups are running daily
7. **User Cleanup:** Deactivate users who leave company immediately
8. **Documentation:** Document all major changes (prompts, settings, etc.)

---

## Common Issues & Solutions

**Issue:** System slow

**Solution:** Check database connection pool, clear Redis cache, restart workers

---

**Issue:** High API costs

**Solution:** Review prompt efficiency, check for retry loops, optimize prompts

---

**Issue:** Users can't log in

**Solution:** Verify email whitelisted, check Google OAuth configuration

---

## FAQs

**Q: How do I add a new website?**
A: Contact development team - requires code changes.

---

**Q: Can I restore deleted projects?**
A: Yes, from database backup within 30 days.

---

**Q: How long are audit logs retained?**
A: 12 months, then archived to cold storage.

---

*Last updated: January 15, 2026*
