"""
Pydantic schemas for project API requests and responses.

Defines validation models for:
- Project creation and updates
- Project responses with related data
- Filtering and pagination
- Revision history
- Custom fields
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.enums import TemplateType


# =====================================================================
# BASE SCHEMAS
# =====================================================================


class UserBasicSchema(BaseModel):
    """Basic user information for nested responses."""
    id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProjectImageSchema(BaseModel):
    """Project image schema for responses."""
    id: UUID
    category: str
    image_url: str
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class ProjectFloorPlanSchema(BaseModel):
    """Floor plan schema for responses."""
    id: UUID
    unit_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    total_sqft: Optional[Decimal] = None
    balcony_sqft: Optional[Decimal] = None
    builtup_sqft: Optional[Decimal] = None
    parsed_data: Optional[Dict[str, Any]] = None
    image_url: str
    display_order: int

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# PROJECT REQUEST SCHEMAS
# =====================================================================


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    developer: Optional[str] = Field(None, max_length=255, description="Developer name")
    location: Optional[str] = Field(None, max_length=255, description="Project location")
    emirate: Optional[str] = Field(None, max_length=100, description="Emirate")
    starting_price: Optional[Decimal] = Field(None, ge=0, description="Starting price")
    price_per_sqft: Optional[Decimal] = Field(None, ge=0, description="Price per square foot")
    handover_date: Optional[date] = Field(None, description="Expected handover date")
    payment_plan: Optional[str] = Field(None, description="Payment plan details")
    description: Optional[str] = Field(None, description="Project description")
    property_types: List[str] = Field(default_factory=list, description="Property types")
    unit_sizes: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="Unit size ranges")
    amenities: List[str] = Field(default_factory=list, description="Amenities list")
    features: List[str] = Field(default_factory=list, description="Features list")
    total_units: Optional[int] = Field(None, ge=0, description="Total number of units")
    floors: Optional[int] = Field(None, ge=0, description="Number of floors")
    buildings: Optional[int] = Field(None, ge=0, description="Number of buildings")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    original_pdf_url: Optional[str] = Field(None, description="Original PDF URL")
    processing_job_id: Optional[UUID] = Field(None, description="Processing job ID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project (partial updates allowed)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    developer: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    emirate: Optional[str] = Field(None, max_length=100)
    starting_price: Optional[Decimal] = Field(None, ge=0)
    price_per_sqft: Optional[Decimal] = Field(None, ge=0)
    handover_date: Optional[date] = None
    payment_plan: Optional[str] = None
    description: Optional[str] = None
    property_types: Optional[List[str]] = None
    unit_sizes: Optional[List[Union[str, Dict[str, Any]]]] = None
    amenities: Optional[List[str]] = None
    features: Optional[List[str]] = None
    total_units: Optional[int] = Field(None, ge=0)
    floors: Optional[int] = Field(None, ge=0)
    buildings: Optional[int] = Field(None, ge=0)
    custom_fields: Optional[Dict[str, Any]] = None
    generated_content: Optional[Dict[str, Any]] = None
    workflow_status: Optional[str] = None
    published_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Project name cannot be empty")
        return v.strip() if v else None


class CustomFieldCreate(BaseModel):
    """Schema for adding a custom field to a project."""
    field_name: str = Field(..., min_length=1, max_length=100, description="Field name")
    field_value: Any = Field(..., description="Field value (any JSON-serializable type)")

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Validate field name format."""
        # Disallow reserved field names
        reserved = {
            "id", "name", "developer", "location", "created_at", "updated_at",
            "created_by", "updated_by", "workflow_status", "is_active"
        }
        if v.lower() in reserved:
            raise ValueError(f"Field name '{v}' is reserved")
        return v


# =====================================================================
# PROJECT RESPONSE SCHEMAS
# =====================================================================


class ProjectListItemSchema(BaseModel):
    """Schema for project list items (compact view)."""
    id: UUID
    name: str
    developer: Optional[str] = None
    location: Optional[str] = None
    emirate: Optional[str] = None
    starting_price: Optional[Decimal] = None
    template_type: TemplateType
    workflow_status: str
    thumbnail: Optional[str] = Field(default=None, validation_alias="thumbnail_url")
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UserBasicSchema] = None
    image_count: int = 0
    floor_plan_count: int = 0

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class GenerationRunSummary(BaseModel):
    """Lightweight summary of a generation run for project detail display."""
    template_type: str
    status: str
    sheet_url: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailSchema(BaseModel):
    """Schema for detailed project response."""
    id: UUID
    name: str
    developer: Optional[str] = None
    location: Optional[str] = None
    emirate: Optional[str] = None
    template_type: TemplateType
    starting_price: Optional[Decimal] = None
    price_per_sqft: Optional[Decimal] = None
    handover_date: Optional[date] = None
    payment_plan: Optional[str] = None
    description: Optional[str] = None
    property_types: List[str] = Field(default_factory=list)
    unit_sizes: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    total_units: Optional[int] = None
    floors: Optional[int] = None
    buildings: Optional[int] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    original_pdf_url: Optional[str] = None
    processed_zip_url: Optional[str] = None
    sheet_url: Optional[str] = None
    thumbnail: Optional[str] = Field(default=None, validation_alias="thumbnail_url")
    generated_content: Dict[str, Any] = Field(default_factory=dict)
    workflow_status: str
    published_url: Optional[str] = None
    published_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UserBasicSchema] = Field(default=None, validation_alias="creator")
    last_modified_by: Optional[UserBasicSchema] = Field(default=None, validation_alias="modifier")
    images: List[ProjectImageSchema] = Field(default_factory=list)
    floor_plans: List[ProjectFloorPlanSchema] = Field(default_factory=list)
    material_package_id: Optional[UUID] = None
    generation_runs: List[GenerationRunSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# =====================================================================
# REVISION HISTORY SCHEMAS
# =====================================================================


class ProjectRevisionSchema(BaseModel):
    """Schema for project revision history."""
    id: UUID
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: UserBasicSchema
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# FILTERING AND PAGINATION SCHEMAS
# =====================================================================


class ProjectFilter(BaseModel):
    """Schema for filtering projects."""
    search: Optional[str] = Field(None, description="Full-text search query")
    developer: Optional[str] = Field(None, description="Filter by developer")
    emirate: Optional[str] = Field(None, description="Filter by emirate")
    location: Optional[str] = Field(None, description="Filter by location")
    workflow_status: Optional[str] = Field(None, description="Filter by workflow status")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum starting price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum starting price")
    created_after: Optional[datetime] = Field(None, description="Created after this date")
    created_before: Optional[datetime] = Field(None, description="Created before this date")
    is_active: bool = Field(default=True, description="Filter by active status")

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, v: Optional[Decimal], values) -> Optional[Decimal]:
        """Validate that max_price is greater than min_price."""
        if v is not None and "min_price" in values.data:
            min_price = values.data.get("min_price")
            if min_price is not None and v < min_price:
                raise ValueError("max_price must be greater than min_price")
        return v


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order is either asc or desc."""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()


class PaginatedResponse(BaseModel):
    """Generic paginated response schema."""
    items: List[Any]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""
    items: List[ProjectListItemSchema]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# EXPORT SCHEMAS
# =====================================================================


class ProjectExportRequest(BaseModel):
    """Schema for project export request."""
    project_ids: Optional[List[UUID]] = Field(None, description="Specific project IDs to export")
    filters: Optional[ProjectFilter] = Field(None, description="Filters to apply")
    format: str = Field(default="csv", description="Export format: csv or json")
    fields: Optional[List[str]] = Field(None, description="Fields to include in export")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format."""
        if v.lower() not in ["csv", "json"]:
            raise ValueError("format must be 'csv' or 'json'")
        return v.lower()


class ProjectExportResponse(BaseModel):
    """Schema for project export response."""
    export_url: str = Field(..., description="URL to download the export file")
    expires_at: datetime = Field(..., description="Expiration time of the download URL")
    project_count: int = Field(..., description="Number of projects exported")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# APPROVAL SCHEMAS
# =====================================================================


class ProjectApprovalRequest(BaseModel):
    """Schema for project approval action."""
    comments: Optional[str] = Field(None, description="Approval comments")


class ProjectApprovalResponse(BaseModel):
    """Schema for project approval response."""
    id: UUID
    workflow_status: str
    approval: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# ADMIN / ALLOWLIST SCHEMAS
# =====================================================================


class AllowlistEntryCreate(BaseModel):
    email: str
    role: str = "user"


class AllowlistEntryUpdate(BaseModel):
    role: str


class AllowlistEntryResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =====================================================================
# MATERIAL PACKAGE & GENERATION RUN SCHEMAS
# =====================================================================


class MaterialPackageResponse(BaseModel):
    """Response for a MaterialPackage."""
    id: UUID
    project_id: Optional[UUID] = None
    source_job_id: Optional[UUID] = None
    gcs_base_path: str
    package_version: str
    extraction_summary: Optional[Dict[str, Any]] = None
    structured_data: Optional[Dict[str, Any]] = None
    status: str
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_package(cls, pkg) -> "MaterialPackageResponse":
        """Convert MaterialPackage ORM to response."""
        return cls(
            id=pkg.id,
            project_id=pkg.project_id,
            source_job_id=pkg.source_job_id,
            gcs_base_path=pkg.gcs_base_path,
            package_version=pkg.package_version,
            extraction_summary=pkg.extraction_summary,
            structured_data=pkg.structured_data,
            status=pkg.status.value if hasattr(pkg.status, "value") else str(pkg.status),
            created_at=pkg.created_at.isoformat(),
            updated_at=pkg.updated_at.isoformat(),
            expires_at=pkg.expires_at.isoformat() if pkg.expires_at else None,
        )


class GenerationRunResponse(BaseModel):
    """Response for a GenerationRun."""
    id: UUID
    project_id: UUID
    material_package_id: Optional[UUID] = None
    template_type: str
    job_id: Optional[UUID] = None
    generated_content: Optional[Dict[str, Any]] = None
    sheet_url: Optional[str] = None
    drive_folder_url: Optional[str] = None
    status: str
    created_at: str
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_run(cls, run) -> "GenerationRunResponse":
        """Convert GenerationRun ORM to response."""
        return cls(
            id=run.id,
            project_id=run.project_id,
            material_package_id=run.material_package_id,
            template_type=run.template_type.value if hasattr(run.template_type, "value") else str(run.template_type),
            job_id=run.job_id,
            generated_content=run.generated_content,
            sheet_url=run.sheet_url,
            drive_folder_url=run.drive_folder_url,
            status=run.status.value if hasattr(run.status, "value") else str(run.status),
            created_at=run.created_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
