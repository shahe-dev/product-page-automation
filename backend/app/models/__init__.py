"""
Database models package for PDP Automation v.3

Exports all ORM models and enums for use throughout the application.
"""

from .database import (
    Base,
    TimestampMixin,
    # Core tables
    User,
    Project,
    ProjectImage,
    ProjectFloorPlan,
    ProjectApproval,
    ProjectRevision,
    Job,
    JobStep,
    Prompt,
    PromptVersion,
    Template,
    QAComparison,
    Notification,
    WorkflowItem,
    PublicationChecklist,
    ExecutionHistory,
    # QA module tables
    QACheckpoint,
    QAIssue,
    QAOverride,
    # Content module tables
    ExtractedData,
    GeneratedContent,
    ContentQAResult,
)

from .enums import (
    UserRole,
    ProjectStatus,
    WorkflowStatus,
    JobStatus,
    JobStepStatus,
    ImageCategory,
    NotificationType,
    ApprovalAction,
    TemplateType,
    ContentVariant,
    QACheckpointType,
    QACheckpointStatus,
    QAIssueSeverity,
    QAOverrideType,
    ExtractionType,
    ContentQACheckType,
)

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    # Core tables
    "User",
    "Project",
    "ProjectImage",
    "ProjectFloorPlan",
    "ProjectApproval",
    "ProjectRevision",
    "Job",
    "JobStep",
    "Prompt",
    "PromptVersion",
    "Template",
    "QAComparison",
    "Notification",
    "WorkflowItem",
    "PublicationChecklist",
    "ExecutionHistory",
    # QA module tables
    "QACheckpoint",
    "QAIssue",
    "QAOverride",
    # Content module tables
    "ExtractedData",
    "GeneratedContent",
    "ContentQAResult",
    # Enums
    "UserRole",
    "ProjectStatus",
    "WorkflowStatus",
    "JobStatus",
    "JobStepStatus",
    "ImageCategory",
    "NotificationType",
    "ApprovalAction",
    "TemplateType",
    "ContentVariant",
    "QACheckpointType",
    "QACheckpointStatus",
    "QAIssueSeverity",
    "QAOverrideType",
    "ExtractionType",
    "ContentQACheckType",
]
