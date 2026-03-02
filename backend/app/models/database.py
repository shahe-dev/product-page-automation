"""
SQLAlchemy ORM Models for PDP Automation v.3

This module defines all database tables as SQLAlchemy async models.
Uses PostgreSQL 16+ with asyncpg driver via SQLAlchemy 2.0.

Architecture:
- 22 total tables (16 core + 3 QA + 3 content)
- UUID primary keys with gen_random_uuid()
- JSONB fields for flexible data storage
- Full-text search indexes
- Audit columns on all tables
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, Date, Numeric,
    CheckConstraint, Index, ForeignKey, UniqueConstraint, func, text,
    Enum as SQLAlchemyEnum
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .enums import (
    UserRole, WorkflowStatus, JobStatus, JobStepStatus, ImageCategory,
    NotificationType, ApprovalAction, TemplateType, ContentVariant,
    QACheckpointType, QACheckpointStatus, QAIssueSeverity, QAOverrideType,
    ExtractionType, ContentQACheckType, JobType, MaterialPackageStatus,
    GenerationRunStatus
)


def _enum_values(enum_class):
    """Return enum member values for SQLAlchemy Enum storage.

    Without this, SQLAlchemy Enum(native_enum=False) stores enum NAMES
    (e.g. 'USER') instead of VALUES (e.g. 'user'). Our check constraints
    expect lowercase values, so we must use values_callable.
    """
    return [m.value for m in enum_class]


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models with async support."""
    pass


class TimestampMixin:
    """Mixin for automatic timestamp management."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


# =====================================================================
# CORE TABLES (16)
# =====================================================================


class User(Base, TimestampMixin):
    """
    User accounts authenticated via Google OAuth.
    Email domain restricted to @your-domain.com.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture_url: Mapped[Optional[str]] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, native_enum=False, length=20, values_callable=_enum_values),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    projects_created: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="Project.created_by"
    )
    jobs: Mapped[List["Job"]] = relationship("Job", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "email ~ '@your-domain\\.com$'",
            name="check_email_domain"
        ),
        # P3-18: Removed idx_users_email and idx_users_google_id -- redundant
        # because unique=True on the column already creates a unique index.
        Index("idx_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class EmailAllowlist(Base):
    """
    Controls which email addresses are allowed to log in.
    Admin manages this list. Empty list = open access (bootstrap mode).
    """
    __tablename__ = "email_allowlist"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(UserRole, native_enum=False, length=20, values_callable=_enum_values),
        nullable=False,
        default=UserRole.USER,
    )
    added_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<EmailAllowlist(id={self.id}, email={self.email}, role={self.role})>"


class RefreshToken(Base):
    """
    Refresh token storage for session management.
    Stores hashed tokens for validation and revocation.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    # Client info for audit
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_token_hash", "token_hash"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class OAuthState(Base):
    """
    OAuth state parameter storage for CSRF protection.
    Short-lived state tokens for OAuth flow validation.
    """
    __tablename__ = "oauth_states"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    state: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    redirect_uri: Mapped[Optional[str]] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        Index("idx_oauth_states_state", "state"),
        Index("idx_oauth_states_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<OAuthState(id={self.id}, used={self.used})>"


class Project(Base, TimestampMixin):
    """
    Central repository for all project data.
    Stores extracted fields, JSONB flexible data, and workflow status.
    """
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Core extracted fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    developer: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    emirate: Mapped[Optional[str]] = mapped_column(String(100))
    starting_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    price_per_sqft: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    handover_date: Mapped[Optional[date]] = mapped_column(Date)
    payment_plan: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # JSONB fields for flexible data
    property_types: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )
    unit_sizes: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )
    amenities: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )
    features: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )

    # Numeric fields
    total_units: Mapped[Optional[int]] = mapped_column(Integer)
    floors: Mapped[Optional[int]] = mapped_column(Integer)
    buildings: Mapped[Optional[int]] = mapped_column(Integer)

    # Custom fields (user-added key-value pairs)
    custom_fields: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    # Media URLs
    original_pdf_url: Mapped[Optional[str]] = mapped_column(String(500))
    processed_zip_url: Mapped[Optional[str]] = mapped_column(String(500))
    sheet_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Generated content
    generated_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    # Template type
    template_type: Mapped[TemplateType] = mapped_column(
        SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=TemplateType.OPR,
        server_default=TemplateType.OPR.value
    )
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="SET NULL")
    )

    # Workflow status
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        SQLAlchemyEnum(WorkflowStatus, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=WorkflowStatus.DRAFT,
        server_default=WorkflowStatus.DRAFT.value
    )

    # Publication
    published_url: Mapped[Optional[str]] = mapped_column(String(500))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Soft delete support
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    # Foreign keys
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    last_modified_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    processing_job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL")
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="projects_created"
    )
    modifier: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[last_modified_by]
    )
    images: Mapped[List["ProjectImage"]] = relationship(
        "ProjectImage",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    floor_plans: Mapped[List["ProjectFloorPlan"]] = relationship(
        "ProjectFloorPlan",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    approvals: Mapped[List["ProjectApproval"]] = relationship(
        "ProjectApproval",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    revisions: Mapped[List["ProjectRevision"]] = relationship(
        "ProjectRevision",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    qa_checkpoints: Mapped[List["QACheckpoint"]] = relationship(
        "QACheckpoint",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    qa_issues: Mapped[List["QAIssue"]] = relationship(
        "QAIssue",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    extracted_data: Mapped[List["ExtractedData"]] = relationship(
        "ExtractedData",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    generated_contents: Mapped[List["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    workflow_items: Mapped[List["WorkflowItem"]] = relationship(
        "WorkflowItem",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    publication_checklists: Mapped[List["PublicationChecklist"]] = relationship(
        "PublicationChecklist",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    qa_comparisons: Mapped[List["QAComparison"]] = relationship(
        "QAComparison",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    material_packages: Mapped[List["MaterialPackage"]] = relationship(
        "MaterialPackage",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    generation_runs: Mapped[List["GenerationRun"]] = relationship(
        "GenerationRun",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_projects_name", "name"),
        Index("idx_projects_developer", "developer"),
        Index("idx_projects_emirate", "emirate"),
        Index("idx_projects_status", "workflow_status"),
        Index("idx_projects_created_at", "created_at", postgresql_using="btree", postgresql_ops={"created_at": "DESC"}),
        Index("idx_projects_created_by", "created_by"),
        Index("idx_projects_is_active", "is_active"),
        Index(
            "idx_projects_search",
            text("to_tsvector('english', coalesce(name, '') || ' ' || coalesce(developer, '') || ' ' || coalesce(location, '') || ' ' || coalesce(description, ''))"),
            postgresql_using="gin"
        ),
        Index("idx_projects_property_types", "property_types", postgresql_using="gin"),
        Index("idx_projects_amenities", "amenities", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.workflow_status})>"


class MaterialPackage(TimestampMixin, Base):
    """
    Stores extraction results from PDF processing for reuse across templates.

    The MaterialPackage is created after step 10 (structure_data) completes.
    Generation jobs consume this package to produce template-specific content.
    """
    __tablename__ = "material_packages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )
    source_job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    gcs_base_path: Mapped[str] = mapped_column(String(500), nullable=False)
    package_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="1.0",
        server_default="1.0"
    )
    extraction_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    structured_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    status: Mapped[MaterialPackageStatus] = mapped_column(
        SQLAlchemyEnum(
            MaterialPackageStatus,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False,
        default=MaterialPackageStatus.PENDING,
        server_default=MaterialPackageStatus.PENDING.value
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="material_packages",
        foreign_keys=[project_id]
    )
    source_job: Mapped[Optional["Job"]] = relationship(
        "Job",
        back_populates="material_package_created",
        foreign_keys=[source_job_id]
    )
    generation_runs: Mapped[List["GenerationRun"]] = relationship(
        "GenerationRun",
        back_populates="material_package",
        cascade="all, delete-orphan"
    )
    consuming_jobs: Mapped[List["Job"]] = relationship(
        "Job",
        back_populates="material_package",
        foreign_keys="[Job.material_package_id]"
    )

    __table_args__ = (
        Index("idx_material_packages_project_id", "project_id"),
        Index("idx_material_packages_status", "status"),
        Index("idx_material_packages_source_job", "source_job_id"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s.value) for s in MaterialPackageStatus)})",
            name="check_material_package_status"
        ),
    )

    def __repr__(self) -> str:
        return f"<MaterialPackage(id={self.id}, status={self.status}, project_id={self.project_id})>"


class GenerationRun(Base):
    """
    Tracks content generation for a specific template using a MaterialPackage.

    Each project can have one generation run per template type (enforced by
    unique constraint). Stores the generated content, sheet URL, and Drive folder.
    """
    __tablename__ = "generation_runs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    material_package_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("material_packages.id", ondelete="SET NULL"),
        nullable=True
    )
    template_type: Mapped[TemplateType] = mapped_column(
        SQLAlchemyEnum(
            TemplateType,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False
    )
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    generated_content: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict
    )
    sheet_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    drive_folder_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[GenerationRunStatus] = mapped_column(
        SQLAlchemyEnum(
            GenerationRunStatus,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False,
        default=GenerationRunStatus.PENDING,
        server_default=GenerationRunStatus.PENDING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="generation_runs"
    )
    material_package: Mapped[Optional["MaterialPackage"]] = relationship(
        "MaterialPackage",
        back_populates="generation_runs"
    )
    job: Mapped[Optional["Job"]] = relationship(
        "Job",
        back_populates="generation_run"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "template_type", name="uq_generation_runs_project_template"),
        Index("idx_generation_runs_project_id", "project_id"),
        Index("idx_generation_runs_status", "status"),
        Index("idx_generation_runs_template_type", "template_type"),
    )

    def __repr__(self) -> str:
        return f"<GenerationRun(id={self.id}, template_type={self.template_type}, status={self.status})>"


class ProjectImage(Base):
    """
    Categorized images for each project.
    Supports interior, exterior, amenity, logo, and floor_plan categories.
    """
    __tablename__ = "project_images"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Image details
    category: Mapped[ImageCategory] = mapped_column(SQLAlchemyEnum(ImageCategory, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Descriptive metadata from Vision classification
    alt_text: Mapped[Optional[str]] = mapped_column(String(500))
    filename: Mapped[Optional[str]] = mapped_column(String(255))

    # Image metadata
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)  # in bytes
    format: Mapped[Optional[str]] = mapped_column(String(10))  # jpg, png, webp

    # Display order
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="images")

    __table_args__ = (
        Index("idx_project_images_project_id", "project_id"),
        Index("idx_project_images_category", "category"),
        Index("idx_project_images_order", "project_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<ProjectImage(id={self.id}, category={self.category}, project_id={self.project_id})>"


class ProjectFloorPlan(Base):
    """
    Floor plan images with extracted data.
    Stores unit type, dimensions, and parsed data from floor plans.
    """
    __tablename__ = "project_floor_plans"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Floor plan details
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "1BR", "2BR", "3BR", "Studio"
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    total_sqft: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    balcony_sqft: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    builtup_sqft: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Parsed data from floor plan
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Image
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Display order
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="floor_plans")

    __table_args__ = (
        Index("idx_project_floor_plans_project_id", "project_id"),
        Index("idx_project_floor_plans_unit_type", "unit_type"),
        Index("idx_project_floor_plans_order", "project_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<ProjectFloorPlan(id={self.id}, unit_type={self.unit_type}, project_id={self.project_id})>"


class ProjectApproval(Base):
    """
    Track approval workflow actions.
    Records submitted, approved, rejected, and revision_requested actions.
    """
    __tablename__ = "project_approvals"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Approval action
    action: Mapped[ApprovalAction] = mapped_column(SQLAlchemyEnum(ApprovalAction, native_enum=False, length=50, values_callable=_enum_values), nullable=False)

    # Approver
    approver_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    comments: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="approvals")
    approver: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_project_approvals_project_id", "project_id"),
        Index("idx_project_approvals_approver_id", "approver_id"),
        Index("idx_project_approvals_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<ProjectApproval(id={self.id}, action={self.action}, project_id={self.project_id})>"


class ProjectRevision(Base):
    """
    Audit trail for all project field changes.
    Tracks field name, old value, new value, and change reason.
    """
    __tablename__ = "project_revisions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Change details
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)

    # Changed by
    changed_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    change_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="revisions")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_project_revisions_project_id", "project_id"),
        Index("idx_project_revisions_field", "field"),
        Index("idx_project_revisions_changed_by", "changed_by"),
        Index("idx_project_revisions_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<ProjectRevision(id={self.id}, field={self.field}, project_id={self.project_id})>"


class Job(Base, TimestampMixin):
    """
    Track background processing jobs.
    Manages PDF processing pipeline with status, progress, and retry logic.
    """
    __tablename__ = "jobs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Job configuration
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    template_type: Mapped[TemplateType] = mapped_column(SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("templates.id", ondelete="SET NULL")
    )
    processing_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Job type for pipeline execution path
    job_type: Mapped[JobType] = mapped_column(
        SQLAlchemyEnum(
            JobType,
            native_enum=False,
            length=50,
            values_callable=_enum_values
        ),
        nullable=False,
        default=JobType.EXTRACTION,
        server_default=JobType.EXTRACTION.value
    )
    # FK to MaterialPackage for GENERATION jobs
    material_package_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("material_packages.id", ondelete="SET NULL"),
        nullable=True
    )

    # Job status
    status: Mapped[JobStatus] = mapped_column(
        SQLAlchemyEnum(JobStatus, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=JobStatus.PENDING,
        server_default=JobStatus.PENDING.value
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0")
    )
    current_step: Mapped[Optional[str]] = mapped_column(String(100))
    progress_message: Mapped[Optional[str]] = mapped_column(String(500))  # Granular substep detail

    # Job result
    result: Mapped[Optional[dict]] = mapped_column(JSONB)  # {project_id, sheet_url, zip_url}
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # Cloud Tasks tracking
    cloud_task_name: Mapped[Optional[str]] = mapped_column(String(500))

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    template: Mapped[Optional["Template"]] = relationship("Template")
    steps: Mapped[List["JobStep"]] = relationship(
        "JobStep",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    extracted_data: Mapped[List["ExtractedData"]] = relationship(
        "ExtractedData",
        back_populates="job"
    )
    # MaterialPackage that this GENERATION job consumes
    material_package: Mapped[Optional["MaterialPackage"]] = relationship(
        "MaterialPackage",
        back_populates="consuming_jobs",
        foreign_keys=[material_package_id]
    )
    # MaterialPackage created by this EXTRACTION job
    material_package_created: Mapped[Optional["MaterialPackage"]] = relationship(
        "MaterialPackage",
        back_populates="source_job",
        foreign_keys="[MaterialPackage.source_job_id]"
    )
    # GenerationRun that this GENERATION job is executing
    generation_run: Mapped[Optional["GenerationRun"]] = relationship(
        "GenerationRun",
        back_populates="job"
    )

    __table_args__ = (
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="check_job_progress_range"
        ),
        CheckConstraint(
            f"job_type IN ({', '.join(repr(j.value) for j in JobType)})",
            name="check_job_type"
        ),
        Index("idx_jobs_user_id", "user_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_job_type", "job_type"),
        Index("idx_jobs_material_package_id", "material_package_id"),
        Index("idx_jobs_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_jobs_completed_at", "completed_at", postgresql_ops={"completed_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, status={self.status}, progress={self.progress}%)>"


class JobStep(Base):
    """
    Detailed step tracking for each job.
    Tracks individual pipeline steps like extract_text, classify_images, etc.
    """
    __tablename__ = "job_steps"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False
    )

    # Step details
    step_id: Mapped[str] = mapped_column(String(50), nullable=False)  # "upload", "extract_text", etc.
    label: Mapped[str] = mapped_column(String(100), nullable=False)    # "Upload PDF", "Extract text"
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))  # Execution order
    status: Mapped[JobStepStatus] = mapped_column(
        SQLAlchemyEnum(JobStepStatus, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=JobStepStatus.PENDING,
        server_default=JobStepStatus.PENDING.value
    )

    # Step result
    step_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="steps")

    __table_args__ = (
        Index("idx_job_steps_job_id", "job_id"),
        Index("idx_job_steps_step_id", "step_id"),
        Index("idx_job_steps_status", "status"),
        # P3-20: Composite index for common (job_id, step_id) lookup pattern
        Index("idx_job_steps_job_step", "job_id", "step_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<JobStep(id={self.id}, step_id={self.step_id}, status={self.status})>"


class Prompt(Base, TimestampMixin):
    """
    Version-controlled prompt library for AI content generation.
    One active prompt per (template_type, content_variant, name) combination.
    """
    __tablename__ = "prompts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Prompt identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Meta Description", "Intro Paragraph"
    template_type: Mapped[TemplateType] = mapped_column(SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    content_variant: Mapped[ContentVariant] = mapped_column(
        SQLAlchemyEnum(ContentVariant, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=ContentVariant.STANDARD,
        server_default=ContentVariant.STANDARD.value
    )

    # Prompt content (current version)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_limit: Mapped[Optional[int]] = mapped_column(Integer)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    # Foreign keys
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    updater: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by])
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_prompts_template_type", "template_type"),
        Index("idx_prompts_content_variant", "content_variant"),
        Index("idx_prompts_name", "name"),
        Index("idx_prompts_active", "is_active"),
        Index("idx_prompts_lookup", "template_type", "content_variant", "name", "is_active"),
        # Partial unique index: one active prompt per (template_type, content_variant, name)
        Index(
            "uq_prompts_active_per_type_variant_name",
            "template_type", "content_variant", "name",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Prompt(id={self.id}, name={self.name}, version={self.version}, active={self.is_active})>"


class PromptVersion(Base):
    """
    Complete history of prompt changes.
    Stores every version of a prompt with change tracking.
    """
    __tablename__ = "prompt_versions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    prompt_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Version details
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    character_limit: Mapped[Optional[int]] = mapped_column(Integer)

    # Change tracking
    change_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")
    creator: Mapped["User"] = relationship("User")
    generated_contents: Mapped[List["GeneratedContent"]] = relationship(
        "GeneratedContent",
        back_populates="prompt_version"
    )

    __table_args__ = (
        Index("idx_prompt_versions_prompt_id", "prompt_id"),
        Index("idx_prompt_versions_version", "prompt_id", "version", postgresql_ops={"version": "DESC"}),
        Index("idx_prompt_versions_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        UniqueConstraint("prompt_id", "version", name="uq_prompt_version_per_prompt"),
    )

    def __repr__(self) -> str:
        return f"<PromptVersion(id={self.id}, prompt_id={self.prompt_id}, version={self.version})>"


class Template(Base, TimestampMixin):
    """
    Website template configurations for Google Sheets.
    Defines field mappings for each template type and content variant.
    """
    __tablename__ = "templates"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Template identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    template_type: Mapped[TemplateType] = mapped_column(SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    content_variant: Mapped[ContentVariant] = mapped_column(
        SQLAlchemyEnum(ContentVariant, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=ContentVariant.STANDARD,
        server_default=ContentVariant.STANDARD.value
    )

    # Google Sheets template
    sheet_template_url: Mapped[str] = mapped_column(String(500), nullable=False)
    field_mappings: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))  # {"meta_title": "B2", "meta_description": "B3"}

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true")
    )

    __table_args__ = (
        Index("idx_templates_template_type", "template_type"),
        Index("idx_templates_active", "is_active"),
        Index("idx_templates_field_mappings", "field_mappings", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.name}, type={self.template_type})>"


class QAComparison(Base):
    """
    Store QA checkpoint results.
    Tracks extraction, generation, and publication validation results.
    """
    __tablename__ = "qa_comparisons"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Checkpoint type
    checkpoint_type: Mapped[QACheckpointType] = mapped_column(SQLAlchemyEnum(QACheckpointType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)

    # Comparison result
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # passed, failed
    matches: Mapped[Optional[int]] = mapped_column(Integer)
    differences: Mapped[Optional[int]] = mapped_column(Integer)
    missing: Mapped[Optional[int]] = mapped_column(Integer)
    extra: Mapped[Optional[int]] = mapped_column(Integer)

    # Detailed result
    result: Mapped[Optional[dict]] = mapped_column(JSONB)  # {differences: [...], missing: [...], extra: [...]}

    # Performed by
    performed_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="qa_comparisons")
    performer: Mapped["User"] = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "status IN ('passed', 'failed')",
            name="check_qa_comparison_status"
        ),
        Index("idx_qa_comparisons_project_id", "project_id"),
        Index("idx_qa_comparisons_checkpoint_type", "checkpoint_type"),
        Index("idx_qa_comparisons_status", "status"),
        Index("idx_qa_comparisons_performed_at", "performed_at", postgresql_ops={"performed_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<QAComparison(id={self.id}, type={self.checkpoint_type}, status={self.status})>"


class Notification(Base):
    """
    In-app notification system.
    Supports info, success, warning, error, approval, and mention types.
    """
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Notification details
    type: Mapped[NotificationType] = mapped_column(SQLAlchemyEnum(NotificationType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Related entity
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE")
    )

    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_is_read", "user_id", "is_read"),
        Index("idx_notifications_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_notifications_user_feed", "user_id", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.type}, read={self.is_read})>"


class WorkflowItem(Base, TimestampMixin):
    """
    Kanban board items for workflow management.
    Links projects to workflow board with assignment and display order.
    """
    __tablename__ = "workflow_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Display order in column
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="workflow_items")
    assignee: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_workflow_items_project_id", "project_id"),
        Index("idx_workflow_items_assigned_to", "assigned_to"),
        UniqueConstraint("project_id", name="uq_workflow_items_project_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkflowItem(id={self.id}, project_id={self.project_id})>"


class PublicationChecklist(Base, TimestampMixin):
    """
    Per-site publication tracking.
    Manages publication checklist items for each template type.
    """
    __tablename__ = "publication_checklists"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    # Publication template
    template_type: Mapped[TemplateType] = mapped_column(SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)

    # Checklist items
    items: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))  # [{task: "Upload images", completed: true}]

    # Status
    all_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false")
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="publication_checklists")

    __table_args__ = (
        Index("idx_publication_checklists_project_id", "project_id"),
        Index("idx_publication_checklists_template_type", "template_type"),
    )

    def __repr__(self) -> str:
        return f"<PublicationChecklist(id={self.id}, template={self.template_type}, completed={self.all_completed})>"


class ExecutionHistory(Base):
    """
    Complete audit log of all system actions.
    Tracks user actions, entity changes, and system events.
    """
    __tablename__ = "execution_history"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # "project.created", "job.completed"
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "project", "job", "prompt"
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    # User context
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    ip_address: Mapped[Optional[str]] = mapped_column(INET)

    # Action details
    details: Mapped[Optional[dict]] = mapped_column(JSONB)  # Full details of the action

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_execution_history_action", "action"),
        Index("idx_execution_history_entity", "entity_type", "entity_id"),
        Index("idx_execution_history_user_id", "user_id"),
        Index("idx_execution_history_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<ExecutionHistory(id={self.id}, action={self.action}, entity={self.entity_type})>"


# =====================================================================
# QA MODULE TABLES (3)
# =====================================================================


class QACheckpoint(Base):
    """
    Store QA checkpoint definitions and results.
    Tracks extraction, content, image, and final validation checkpoints.
    """
    __tablename__ = "qa_checkpoints"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    checkpoint_type: Mapped[QACheckpointType] = mapped_column(SQLAlchemyEnum(QACheckpointType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    status: Mapped[QACheckpointStatus] = mapped_column(
        SQLAlchemyEnum(QACheckpointStatus, native_enum=False, length=20, values_callable=_enum_values),
        nullable=False,
        default=QACheckpointStatus.PENDING,
        server_default=QACheckpointStatus.PENDING.value
    )
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # 0.00 to 100.00
    issues_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    checkpoint_metadata: Mapped[dict] = mapped_column(
        "metadata",  # Keep the DB column name as 'metadata'
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )
    checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    checked_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="qa_checkpoints")
    checker: Mapped[Optional["User"]] = relationship("User")
    issues: Mapped[List["QAIssue"]] = relationship(
        "QAIssue",
        back_populates="checkpoint",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_qa_checkpoints_project_id", "project_id"),
        Index("idx_qa_checkpoints_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<QACheckpoint(id={self.id}, type={self.checkpoint_type}, status={self.status})>"


class QAIssue(Base):
    """
    Track QA issues found during validation.
    Records severity, category, description, and resolution status.
    """
    __tablename__ = "qa_issues"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    checkpoint_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("qa_checkpoints.id", ondelete="CASCADE")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    severity: Mapped[QAIssueSeverity] = mapped_column(SQLAlchemyEnum(QAIssueSeverity, native_enum=False, length=20, values_callable=_enum_values), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 'missing_data', 'format_error', 'brand_violation', etc.
    field_name: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[Optional[str]] = mapped_column(Text)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    checkpoint: Mapped[Optional["QACheckpoint"]] = relationship("QACheckpoint", back_populates="issues")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="qa_issues")
    resolver: Mapped[Optional["User"]] = relationship("User")
    overrides: Mapped[List["QAOverride"]] = relationship(
        "QAOverride",
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_qa_issues_checkpoint_id", "checkpoint_id"),
        Index("idx_qa_issues_project_id", "project_id"),
        Index("idx_qa_issues_severity", "severity"),
        Index("idx_qa_issues_is_resolved", "is_resolved"),
        Index("idx_qa_issues_project_unresolved", "project_id", "is_resolved"),
    )

    def __repr__(self) -> str:
        return f"<QAIssue(id={self.id}, severity={self.severity}, resolved={self.is_resolved})>"


class QAOverride(Base):
    """
    Store manual QA override decisions.
    Tracks accept, reject, or defer decisions with justification.
    """
    __tablename__ = "qa_overrides"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    issue_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("qa_issues.id", ondelete="CASCADE"),
        nullable=False
    )
    override_type: Mapped[QAOverrideType] = mapped_column(SQLAlchemyEnum(QAOverrideType, native_enum=False, length=20, values_callable=_enum_values), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    overridden_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    issue: Mapped["QAIssue"] = relationship("QAIssue", back_populates="overrides")
    overrider: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index("idx_qa_overrides_issue_id", "issue_id"),
    )

    def __repr__(self) -> str:
        return f"<QAOverride(id={self.id}, type={self.override_type}, issue_id={self.issue_id})>"


# =====================================================================
# CONTENT MODULE TABLES (3)
# =====================================================================


class ExtractedData(Base):
    """
    Store raw extracted data from PDF processing.
    Tracks text, image, table, and metadata extraction with confidence scores.
    """
    __tablename__ = "extracted_data"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL")
    )
    extraction_type: Mapped[ExtractionType] = mapped_column(SQLAlchemyEnum(ExtractionType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    structured_content: Mapped[Optional[dict]] = mapped_column(JSONB)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))  # 0.0000 to 1.0000
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(50))  # 'anthropic_vision', 'pypdf', 'ocr'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="extracted_data")
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="extracted_data")

    __table_args__ = (
        Index("idx_extracted_data_project_id", "project_id"),
        Index("idx_extracted_data_job_id", "job_id"),
        Index("idx_extracted_data_type", "extraction_type"),
    )

    def __repr__(self) -> str:
        return f"<ExtractedData(id={self.id}, type={self.extraction_type}, project_id={self.project_id})>"


class GeneratedContent(Base):
    """
    Store AI-generated content with version history.
    Tracks field name, template type, content, and approval status.
    """
    __tablename__ = "generated_content"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)  # 'title', 'meta_description', 'body_text', etc.
    template_type: Mapped[TemplateType] = mapped_column(SQLAlchemyEnum(TemplateType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    content_variant: Mapped[ContentVariant] = mapped_column(
        SQLAlchemyEnum(ContentVariant, native_enum=False, length=50, values_callable=_enum_values),
        nullable=False,
        default=ContentVariant.STANDARD,
        server_default=ContentVariant.STANDARD.value
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("prompt_versions.id", ondelete="SET NULL")
    )
    generation_params: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="generated_contents")
    prompt_version: Mapped[Optional["PromptVersion"]] = relationship("PromptVersion", back_populates="generated_contents")
    approver: Mapped[Optional["User"]] = relationship("User")
    qa_results: Mapped[List["ContentQAResult"]] = relationship(
        "ContentQAResult",
        back_populates="generated_content",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_generated_content_project_id", "project_id"),
        Index("idx_generated_content_field", "field_name"),
        Index("idx_generated_content_template", "template_type"),
        Index("idx_generated_content_project_template", "project_id", "template_type", "content_variant"),
    )

    def __repr__(self) -> str:
        return f"<GeneratedContent(id={self.id}, field={self.field_name}, approved={self.is_approved})>"


class ContentQAResult(Base):
    """
    Store content-specific QA validation results.
    Tracks brand compliance, SEO score, readability, and factual accuracy.
    """
    __tablename__ = "content_qa_results"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    generated_content_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("generated_content.id", ondelete="CASCADE"),
        nullable=False
    )
    check_type: Mapped[ContentQACheckType] = mapped_column(SQLAlchemyEnum(ContentQACheckType, native_enum=False, length=50, values_callable=_enum_values), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    details: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    generated_content: Mapped["GeneratedContent"] = relationship("GeneratedContent", back_populates="qa_results")

    __table_args__ = (
        Index("idx_content_qa_results_content_id", "generated_content_id"),
        Index("idx_content_qa_results_check_type", "check_type"),
        Index("idx_content_qa_results_passed", "passed"),
    )

    def __repr__(self) -> str:
        return f"<ContentQAResult(id={self.id}, check={self.check_type}, passed={self.passed})>"
