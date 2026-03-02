"""
Template management API endpoints.

Provides template listing and field management:
- GET /api/v1/templates                              - List all templates
- GET /api/v1/templates/{id}                         - Get template by ID
- GET /api/v1/templates/{id}/fields                  - Get field mappings by ID
- GET /api/v1/templates/type/{template_type}/fields  - Get field definitions by type
- PUT /api/v1/templates/type/{template_type}/fields  - Replace all field definitions
- POST /api/v1/templates/type/{template_type}/fields/{field_name} - Add single field
- DELETE /api/v1/templates/type/{template_type}/fields/{field_name} - Soft-delete field
- PATCH /api/v1/templates/type/{template_type}/fields/{field_name} - Update single field
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_admin
from app.models.database import User, Template
from app.models.enums import TemplateType, ContentVariant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

# Valid field types for validation
VALID_FIELD_TYPES = {"GENERATED", "EXTRACTED", "HYBRID", "STATIC"}


# Response Models

class TemplateListItem(BaseModel):
    """Template list item."""
    id: UUID
    name: str
    template_type: str
    content_variant: str
    sheet_template_url: str
    field_mappings: Dict[str, str]
    is_active: bool


class TemplateDetail(BaseModel):
    """Detailed template information."""
    id: UUID
    name: str
    template_type: str
    content_variant: str
    description: Optional[str] = None
    sheet_template_url: str
    field_mappings: Dict[str, str]
    required_fields: list[str]
    optional_fields: list[str]
    is_active: bool
    created_at: str
    updated_at: str


class TemplateFieldMapping(BaseModel):
    """Template field mapping detail."""
    field_name: str
    sheet_cell: str
    field_type: str
    is_required: bool
    validation_rules: Optional[Dict[str, Any]] = None


# Field Definition Models (for dynamic field editor)

class FieldDefinition(BaseModel):
    """Single field definition with all properties."""
    row: int = Field(..., gt=0, description="Row number in Google Sheet (1-indexed)")
    section: str = Field(..., min_length=1, description="Section name (SEO, Hero, About, etc.)")
    char_limit: Optional[int] = Field(None, gt=0, description="Max characters, null = no limit")
    required: bool = Field(False, description="Whether field must have content")
    field_type: str = Field("GENERATED", description="GENERATED, EXTRACTED, HYBRID, or STATIC")
    is_active: bool = Field(True, description="Whether field is active (false = soft-deleted)")

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        if v not in VALID_FIELD_TYPES:
            raise ValueError(f"field_type must be one of: {', '.join(VALID_FIELD_TYPES)}")
        return v


class FieldDefinitionCreate(BaseModel):
    """Request body for creating a new field."""
    row: int = Field(..., gt=0)
    section: str = Field(..., min_length=1)
    char_limit: Optional[int] = Field(None, gt=0)
    required: bool = Field(False)
    field_type: str = Field("GENERATED")

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: str) -> str:
        if v not in VALID_FIELD_TYPES:
            raise ValueError(f"field_type must be one of: {', '.join(VALID_FIELD_TYPES)}")
        return v


class FieldDefinitionUpdate(BaseModel):
    """Request body for partial field update."""
    row: Optional[int] = Field(None, gt=0)
    section: Optional[str] = Field(None, min_length=1)
    char_limit: Optional[int] = Field(None)
    required: Optional[bool] = None
    field_type: Optional[str] = None

    @field_validator("field_type")
    @classmethod
    def validate_field_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_FIELD_TYPES:
            raise ValueError(f"field_type must be one of: {', '.join(VALID_FIELD_TYPES)}")
        return v


class FieldsUpdateRequest(BaseModel):
    """Request body for full fields replacement."""
    fields: Dict[str, FieldDefinition]


class FieldsResponse(BaseModel):
    """Response containing all field definitions for a template."""
    template_type: str
    field_count: int
    fields: Dict[str, FieldDefinition]


class FieldUpdateResponse(BaseModel):
    """Response after updating fields."""
    updated: bool
    field_count: int


class FieldDeleteResponse(BaseModel):
    """Response after deleting a field."""
    deleted: bool
    field_name: str


class FieldAddResponse(BaseModel):
    """Response after adding a field."""
    added: bool
    field_name: str


# Validation Helper

def validate_field_mappings(fields: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Validate field mappings and return list of errors.

    Checks:
    - Each field has a section
    - Row is a positive integer
    - field_type is valid enum value
    - char_limit is positive int or null
    - No duplicate row numbers (except bullet fields)

    Args:
        fields: Dict mapping field_name -> field definition dict

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    rows_seen: Dict[int, str] = {}

    for name, field in fields.items():
        # Check section
        if not field.get("section"):
            errors.append(f"{name}: missing section")

        # Check row
        row = field.get("row")
        if not isinstance(row, int) or row < 1:
            errors.append(f"{name}: row must be positive integer")
        else:
            # Check duplicate rows (allow for bullet fields)
            if row in rows_seen:
                existing_name = rows_seen[row]
                is_bullet_pair = "bullet" in name.lower() or "bullet" in existing_name.lower()
                if not is_bullet_pair:
                    errors.append(f"{name}: duplicate row {row} with {existing_name}")
            rows_seen[row] = name

        # Check field_type
        field_type = field.get("field_type")
        if field_type and field_type not in VALID_FIELD_TYPES:
            errors.append(f"{name}: invalid field_type '{field_type}'")

        # Check char_limit
        char_limit = field.get("char_limit")
        if char_limit is not None:
            if not isinstance(char_limit, int) or char_limit < 1:
                errors.append(f"{name}: char_limit must be positive integer or null")

    return errors


async def get_template_by_type(
    template_type: str,
    db: AsyncSession,
    content_variant: str = "standard"
) -> Template:
    """
    Get template by type and variant, raising 404 if not found.

    Args:
        template_type: Template type string (aggregators, opr, etc.)
        db: Database session
        content_variant: Content variant (standard, luxury)

    Returns:
        Template instance

    Raises:
        HTTPException: 404 if not found, 422 if invalid type
    """
    try:
        tt = TemplateType(template_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid template type",
                "details": {"provided": template_type, "allowed": [t.value for t in TemplateType]},
            },
        )

    try:
        cv = ContentVariant(content_variant.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid content variant",
                "details": {"provided": content_variant, "allowed": [v.value for v in ContentVariant]},
            },
        )

    result = await db.execute(
        select(Template)
        .where(Template.template_type == tt)
        .where(Template.content_variant == cv)
        .where(Template.is_active == True)
    )
    template = result.scalar_one_or_none()

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NOT_FOUND",
                "message": f"Template '{template_type}' with variant '{content_variant}' not found",
            },
        )

    return template


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List templates",
    description="List all available website templates"
)
async def list_templates(
    template_type: Optional[str] = None,
    content_variant: Optional[str] = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List available templates.

    Args:
        template_type: Optional filter by type
        content_variant: Optional filter by variant
        is_active: Filter by active status
        current_user: Authenticated user
        db: Database session

    Returns:
        List of templates
    """
    query = select(Template).where(Template.is_active == is_active)

    if template_type:
        try:
            tt = TemplateType(template_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid template type",
                    "details": {"provided": template_type, "allowed": [t.value for t in TemplateType]},
                },
            )
        query = query.where(Template.template_type == tt)

    if content_variant:
        try:
            cv = ContentVariant(content_variant)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid content variant",
                    "details": {"provided": content_variant, "allowed": [v.value for v in ContentVariant]},
                },
            )
        query = query.where(Template.content_variant == cv)

    query = query.order_by(Template.name)
    result = await db.execute(query)
    templates = result.scalars().all()

    items = [
        TemplateListItem(
            id=t.id,
            name=t.name,
            template_type=t.template_type.value,
            content_variant=t.content_variant.value,
            sheet_template_url=t.sheet_template_url,
            field_mappings=t.field_mappings,
            is_active=t.is_active,
        )
        for t in templates
    ]

    return {"items": items}


@router.get(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    response_model=TemplateDetail,
    summary="Get template",
    description="Get detailed template information"
)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get template detail.

    Args:
        template_id: Template UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Detailed template information

    Raises:
        404: Template not found
    """
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Template {template_id} not found"},
        )

    mappings = template.field_mappings or {}
    all_fields = list(mappings.keys())

    return TemplateDetail(
        id=template.id,
        name=template.name,
        template_type=template.template_type.value,
        content_variant=template.content_variant.value,
        description=None,
        sheet_template_url=template.sheet_template_url,
        field_mappings=mappings,
        required_fields=all_fields,
        optional_fields=[],
        is_active=template.is_active,
        created_at=template.created_at.isoformat() + "Z",
        updated_at=template.updated_at.isoformat() + "Z",
    )


@router.get(
    "/{template_id}/fields",
    status_code=status.HTTP_200_OK,
    summary="Get template field mappings",
    description="Get detailed field mapping information for a template"
)
async def get_template_fields(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get template field mappings.

    Args:
        template_id: Template UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of field mappings

    Raises:
        404: Template not found
    """
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Template {template_id} not found"},
        )

    mappings = template.field_mappings or {}

    fields = [
        TemplateFieldMapping(
            field_name=field_name,
            sheet_cell=cell,
            field_type="text",
            is_required=True,
            validation_rules=None,
        )
        for field_name, cell in mappings.items()
    ]

    return {"fields": fields}


# ============================================================================
# Field Definition CRUD by Template Type (for Dynamic Field Editor)
# ============================================================================


@router.get(
    "/type/{template_type}/fields",
    status_code=status.HTTP_200_OK,
    response_model=FieldsResponse,
    summary="Get field definitions by template type",
    description="Get all field definitions for a template type (for field editor)"
)
async def get_fields_by_type(
    template_type: str,
    content_variant: str = "standard",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all field definitions for a template type.

    Returns full field definitions including row, section, char_limit,
    required, field_type, and is_active status.
    """
    template = await get_template_by_type(template_type, db, content_variant)
    mappings = template.field_mappings or {}

    # Convert stored format to FieldDefinition format
    fields = {}
    for name, field_data in mappings.items():
        if isinstance(field_data, dict):
            fields[name] = FieldDefinition(
                row=field_data.get("row", 1),
                section=field_data.get("section", "Unknown"),
                char_limit=field_data.get("char_limit"),
                required=field_data.get("required", False),
                field_type=field_data.get("field_type", "GENERATED"),
                is_active=field_data.get("is_active", True),
            )
        else:
            # Legacy format: field_data is just a cell reference string
            # Extract row number from cell reference (e.g., "C4" -> 4)
            try:
                row = int("".join(c for c in str(field_data) if c.isdigit()))
            except ValueError:
                row = 1
            fields[name] = FieldDefinition(
                row=row,
                section="Unknown",
                char_limit=None,
                required=False,
                field_type="GENERATED",
                is_active=True,
            )

    return FieldsResponse(
        template_type=template_type,
        field_count=len(fields),
        fields=fields,
    )


@router.put(
    "/type/{template_type}/fields",
    status_code=status.HTTP_200_OK,
    response_model=FieldUpdateResponse,
    summary="Replace all field definitions",
    description="Replace all field definitions for a template (admin only)"
)
@require_admin
async def update_fields_by_type(
    template_type: str,
    request: FieldsUpdateRequest,
    content_variant: str = "standard",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Replace all field definitions for a template type.

    This is a full replacement - all existing fields are replaced
    with the provided fields.
    """
    template = await get_template_by_type(template_type, db, content_variant)

    # Convert to dict format for validation
    fields_dict = {
        name: field.model_dump()
        for name, field in request.fields.items()
    }

    # Validate
    errors = validate_field_mappings(fields_dict)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Field validation failed",
                "errors": errors,
            },
        )

    # Update template
    template.field_mappings = fields_dict
    await db.commit()

    logger.info(
        f"Updated {len(fields_dict)} fields for template {template_type} "
        f"by user {current_user.email}"
    )

    return FieldUpdateResponse(updated=True, field_count=len(fields_dict))


@router.post(
    "/type/{template_type}/fields/{field_name}",
    status_code=status.HTTP_201_CREATED,
    response_model=FieldAddResponse,
    summary="Add a new field",
    description="Add a single new field to a template (admin only)"
)
@require_admin
async def add_field(
    template_type: str,
    field_name: str,
    request: FieldDefinitionCreate,
    content_variant: str = "standard",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Add a new field to a template.

    The field_name must not already exist in the template.
    """
    template = await get_template_by_type(template_type, db, content_variant)
    mappings = dict(template.field_mappings or {})

    # Check field doesn't already exist
    if field_name in mappings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "CONFLICT",
                "message": f"Field '{field_name}' already exists",
            },
        )

    # Create new field
    new_field = {
        "row": request.row,
        "section": request.section,
        "char_limit": request.char_limit,
        "required": request.required,
        "field_type": request.field_type,
        "is_active": True,
    }

    # Validate against existing fields
    test_mappings = {**mappings, field_name: new_field}
    errors = validate_field_mappings(test_mappings)
    if errors:
        # Filter to only show errors for the new field
        new_field_errors = [e for e in errors if e.startswith(field_name)]
        if new_field_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Field validation failed",
                    "errors": new_field_errors,
                },
            )

    # Add field
    mappings[field_name] = new_field
    template.field_mappings = mappings
    await db.commit()

    logger.info(
        f"Added field '{field_name}' to template {template_type} "
        f"by user {current_user.email}"
    )

    return FieldAddResponse(added=True, field_name=field_name)


@router.delete(
    "/type/{template_type}/fields/{field_name}",
    status_code=status.HTTP_200_OK,
    response_model=FieldDeleteResponse,
    summary="Soft-delete a field",
    description="Mark a field as inactive (soft delete, admin only)"
)
@require_admin
async def delete_field(
    template_type: str,
    field_name: str,
    content_variant: str = "standard",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Soft-delete a field by marking it inactive.

    The field is not removed from the database but marked with is_active=false.
    This preserves historical data.
    """
    template = await get_template_by_type(template_type, db, content_variant)
    mappings = dict(template.field_mappings or {})

    # Check field exists
    if field_name not in mappings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NOT_FOUND",
                "message": f"Field '{field_name}' not found",
            },
        )

    # Soft delete by setting is_active=False
    field_data = mappings[field_name]
    if isinstance(field_data, dict):
        field_data["is_active"] = False
    else:
        # Legacy format - convert to dict
        try:
            row = int("".join(c for c in str(field_data) if c.isdigit()))
        except ValueError:
            row = 1
        mappings[field_name] = {
            "row": row,
            "section": "Unknown",
            "char_limit": None,
            "required": False,
            "field_type": "GENERATED",
            "is_active": False,
        }

    template.field_mappings = mappings
    await db.commit()

    logger.info(
        f"Soft-deleted field '{field_name}' from template {template_type} "
        f"by user {current_user.email}"
    )

    return FieldDeleteResponse(deleted=True, field_name=field_name)


@router.patch(
    "/type/{template_type}/fields/{field_name}",
    status_code=status.HTTP_200_OK,
    response_model=FieldUpdateResponse,
    summary="Update a field",
    description="Partially update a single field (admin only)"
)
@require_admin
async def update_field(
    template_type: str,
    field_name: str,
    request: FieldDefinitionUpdate,
    content_variant: str = "standard",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Partially update a single field.

    Only provided fields are updated; others remain unchanged.
    """
    template = await get_template_by_type(template_type, db, content_variant)
    mappings = dict(template.field_mappings or {})

    # Check field exists
    if field_name not in mappings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "NOT_FOUND",
                "message": f"Field '{field_name}' not found",
            },
        )

    # Get existing field data
    field_data = mappings[field_name]
    if isinstance(field_data, dict):
        updated_field = dict(field_data)
    else:
        # Legacy format - convert to dict
        try:
            row = int("".join(c for c in str(field_data) if c.isdigit()))
        except ValueError:
            row = 1
        updated_field = {
            "row": row,
            "section": "Unknown",
            "char_limit": None,
            "required": False,
            "field_type": "GENERATED",
            "is_active": True,
        }

    # Apply updates (only non-None values)
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None or key == "char_limit":
            updated_field[key] = value

    # Validate
    test_mappings = {**mappings, field_name: updated_field}
    errors = validate_field_mappings(test_mappings)
    if errors:
        field_errors = [e for e in errors if e.startswith(field_name)]
        if field_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Field validation failed",
                    "errors": field_errors,
                },
            )

    # Update
    mappings[field_name] = updated_field
    template.field_mappings = mappings
    await db.commit()

    logger.info(
        f"Updated field '{field_name}' in template {template_type} "
        f"by user {current_user.email}"
    )

    return FieldUpdateResponse(updated=True, field_count=1)
