"""
Database Enums for PDP Automation v.3

This module defines all enumeration types used throughout the database schema.
These enums ensure data consistency and type safety across the application.
"""

import enum


class UserRole(str, enum.Enum):
    """User role enumeration for access control."""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class ProjectStatus(str, enum.Enum):
    """Project lifecycle status (legacy field, mostly replaced by WorkflowStatus)."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkflowStatus(str, enum.Enum):
    """
    Project workflow status through approval and publication pipeline.

    Flow:
    draft -> pending_approval -> approved -> publishing -> published -> qa_verified -> complete
                              -> revision_requested -> draft
    """
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    QA_VERIFIED = "qa_verified"
    COMPLETE = "complete"


class JobStatus(str, enum.Enum):
    """
    Background job status.

    Flow:
    pending -> processing -> completed
                          -> failed
                          -> cancelled
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStepStatus(str, enum.Enum):
    """Individual job step status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ImageCategory(str, enum.Enum):
    """Image categorization for project images."""
    INTERIOR = "interior"
    EXTERIOR = "exterior"
    AMENITY = "amenity"
    LOGO = "logo"
    FLOOR_PLAN = "floor_plan"
    LOCATION_MAP = "location_map"
    MASTER_PLAN = "master_plan"
    OTHER = "other"


class NotificationType(str, enum.Enum):
    """Notification type for in-app notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    APPROVAL = "approval"
    MENTION = "mention"


class ApprovalAction(str, enum.Enum):
    """Approval workflow action types."""
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class TemplateType(str, enum.Enum):
    """Website template types for content generation."""
    AGGREGATORS = "aggregators"
    OPR = "opr"
    MPP = "mpp"
    ADOP = "adop"
    ADRE = "adre"
    COMMERCIAL = "commercial"


class ContentVariant(str, enum.Enum):
    """Content style variant for generated content."""
    STANDARD = "standard"
    LUXURY = "luxury"


class JobType(str, enum.Enum):
    """Job type for pipeline execution path."""
    EXTRACTION = "extraction"  # Steps 1-10 only, produces MaterialPackage
    GENERATION = "generation"  # Steps 11-14 only, consumes MaterialPackage


class MaterialPackageStatus(str, enum.Enum):
    """Status of a MaterialPackage."""
    PENDING = "pending"    # Extraction in progress
    READY = "ready"        # Available for generation
    EXPIRED = "expired"    # Past TTL, scheduled for cleanup
    ERROR = "error"        # Extraction failed


class GenerationRunStatus(str, enum.Enum):
    """Status of a generation run for a specific template."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QACheckpointType(str, enum.Enum):
    """QA checkpoint types for validation stages."""
    EXTRACTION = "extraction"
    GENERATION = "generation"
    PUBLICATION = "publication"
    CONTENT = "content"
    IMAGE = "image"
    FINAL = "final"


class QACheckpointStatus(str, enum.Enum):
    """QA checkpoint status."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class QAIssueSeverity(str, enum.Enum):
    """Severity level for QA issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QAOverrideType(str, enum.Enum):
    """QA override decision types."""
    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"


class ExtractionType(str, enum.Enum):
    """Extracted data type from PDF processing."""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    METADATA = "metadata"


class ContentQACheckType(str, enum.Enum):
    """Content-specific QA check types."""
    BRAND_COMPLIANCE = "brand_compliance"
    SEO_SCORE = "seo_score"
    READABILITY = "readability"
    FACTUAL_ACCURACY = "factual_accuracy"
