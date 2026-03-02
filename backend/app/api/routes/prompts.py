"""
Prompt management API endpoints.

Provides prompt management functionality:
- GET  /api/v1/prompts             - List prompts
- POST /api/v1/prompts             - Create prompt
- GET  /api/v1/prompts/{id}        - Get prompt
- PUT  /api/v1/prompts/{id}        - Update prompt
- GET  /api/v1/prompts/{id}/versions - Get prompt versions
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# TODO(P1-12): Standardize all route files to import from app.api.dependencies
from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.middleware.permissions import require_admin
from app.models.database import User, Prompt
from app.models.database import PromptVersion as PromptVersionDB
from app.services.template_fields import (
    get_fields_for_template,
    get_sections_for_template,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["prompts"])


# Request/Response Models


class PromptCreate(BaseModel):
    """Request to create a prompt."""

    name: str = Field(..., min_length=1, max_length=255, description="Prompt name")
    template_type: str = Field(..., description="Template type")
    content_variant: str = Field(default="standard", description="Content variant")
    content: str = Field(..., min_length=1, description="Prompt content")
    character_limit: Optional[int] = Field(
        None, ge=0, description="Character limit for output"
    )


class PromptUpdate(BaseModel):
    """Request to update a prompt."""

    content: str = Field(..., min_length=1, description="Updated prompt content")
    change_reason: Optional[str] = Field(None, description="Reason for change")


class PromptResponse(BaseModel):
    """Prompt response."""

    id: UUID
    name: str
    template_type: str
    content_variant: str
    content: str
    character_limit: Optional[int]
    version: int
    is_active: bool
    created_at: str
    updated_at: str
    updated_by: Optional[Dict[str, Any]] = None


class PromptListItem(BaseModel):
    """Prompt list item (compact view)."""

    id: UUID
    name: str
    template_type: str
    content_variant: str
    version: int
    is_active: bool
    character_limit: Optional[int]
    updated_at: str
    updated_by: Optional[Dict[str, str]] = None


class PromptVersion(BaseModel):
    """Prompt version history item."""

    version: int
    content: str
    change_reason: Optional[str]
    created_at: str
    created_by: Dict[str, str]


class GroupedFieldItem(BaseModel):
    """Field item within a section for grouped prompts response."""

    field_name: str
    row: int
    character_limit: Optional[int]
    required: bool
    field_type: str
    has_prompt: bool
    prompt_id: Optional[UUID] = None
    version: Optional[int] = None
    content_preview: Optional[str] = None


class GroupedSectionItem(BaseModel):
    """Section with its fields for grouped prompts response."""

    section: str
    field_count: int
    prompts_defined: int
    fields: List[GroupedFieldItem]


class GroupedPromptsResponse(BaseModel):
    """Response model for grouped prompts endpoint."""

    template_type: str
    total_fields: int
    promptable_fields: int
    total_prompts_defined: int
    coverage_percent: float
    sections: List[GroupedSectionItem]


@router.get(
    "/grouped",
    status_code=status.HTTP_200_OK,
    response_model=GroupedPromptsResponse,
    summary="List prompts grouped by section",
    description="List prompts for a template grouped by section with coverage stats",
)
async def list_prompts_grouped(
    template_type: str = Query(..., description="Template type to get prompts for"),
    content_variant: str = Query(default="standard", description="Content variant"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List prompts grouped by section with coverage statistics.

    Args:
        template_type: Template type (aggregators, opr, mpp, adop, adre, commercial)
        content_variant: Content variant (standard, luxury)
        current_user: Authenticated user
        db: Database session

    Returns:
        Grouped prompts with field metadata and coverage stats

    Raises:
        400: Invalid template type
    """
    valid_templates = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]
    if template_type not in valid_templates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TEMPLATE_TYPE",
                "message": f"Invalid template type: {template_type}",
                "details": {"allowed": valid_templates},
            },
        )

    try:
        # Get field definitions from template_fields
        fields = get_fields_for_template(template_type)
        sections = get_sections_for_template(template_type)

        # Query all active prompts for this template
        query = select(Prompt).where(
            and_(
                Prompt.template_type == template_type,
                Prompt.content_variant == content_variant,
                Prompt.is_active.is_(True),
            )
        )
        result = await db.execute(query)
        prompts_db = result.scalars().all()

        # Build lookup by name
        prompts_by_name: Dict[str, Prompt] = {p.name: p for p in prompts_db}

        # Build response
        total_fields = len(fields)
        total_prompts_defined = 0
        section_items: List[GroupedSectionItem] = []

        for section_name, field_names in sections.items():
            section_fields: List[GroupedFieldItem] = []
            section_prompts_defined = 0

            for field_name in field_names:
                field_def = fields[field_name]
                prompt = prompts_by_name.get(field_name)
                has_prompt = prompt is not None

                if has_prompt and field_def.field_type.value in ("GENERATED", "HYBRID"):
                    section_prompts_defined += 1
                    total_prompts_defined += 1

                section_fields.append(
                    GroupedFieldItem(
                        field_name=field_name,
                        row=field_def.row,
                        character_limit=field_def.char_limit,
                        required=field_def.required,
                        field_type=field_def.field_type.value,
                        has_prompt=has_prompt,
                        prompt_id=prompt.id if prompt else None,
                        version=prompt.version if prompt else None,
                        content_preview=prompt.content[:100] if prompt else None,
                    )
                )

            section_items.append(
                GroupedSectionItem(
                    section=section_name,
                    field_count=len(field_names),
                    prompts_defined=section_prompts_defined,
                    fields=section_fields,
                )
            )

        # Count only GENERATED and HYBRID fields for coverage
        promptable_fields = sum(
            1 for f in fields.values()
            if f.field_type.value in ("GENERATED", "HYBRID")
        )

        coverage_percent = (
            round(total_prompts_defined / promptable_fields * 100, 1)
            if promptable_fields > 0
            else 0.0
        )

        logger.debug(
            f"Grouped prompts requested by {current_user.email} "
            f"(template={template_type}, variant={content_variant}) - "
            f"{total_prompts_defined}/{promptable_fields} prompts defined "
            f"({total_fields} total fields)"
        )

        return GroupedPromptsResponse(
            template_type=template_type,
            total_fields=total_fields,
            promptable_fields=promptable_fields,
            total_prompts_defined=total_prompts_defined,
            coverage_percent=coverage_percent,
            sections=section_items,
        )

    except ValueError as e:
        # get_fields_for_template raises ValueError for unknown templates
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_TEMPLATE_TYPE",
                "message": str(e),
                "details": {},
            },
        )
    except Exception as e:
        logger.exception(f"Error getting grouped prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to get grouped prompts",
                "details": {},
            },
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List prompts",
    description="List all prompts with optional filtering",
)
async def list_prompts(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    content_variant: Optional[str] = Query(
        None, description="Filter by content variant"
    ),
    search: Optional[str] = Query(None, description="Search prompt names"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List prompts with filtering.

    Args:
        template_type: Filter by template (aggregators, opr, mpp, etc.)
        content_variant: Filter by variant (standard, luxury)
        search: Search query for prompt names
        is_active: Filter by active status
        current_user: Authenticated user
        db: Database session

    Returns:
        List of prompts

    Raises:
        None
    """
    try:
        # Build query with filters
        query = select(Prompt).options(selectinload(Prompt.updater))

        # Apply filters
        if template_type:
            query = query.where(Prompt.template_type == template_type)
        if content_variant:
            query = query.where(Prompt.content_variant == content_variant)
        if search:
            escaped = (
                search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            query = query.where(Prompt.name.ilike(f"%{escaped}%", escape="\\"))
        if is_active is not None:
            query = query.where(Prompt.is_active == is_active)

        # Sort by template_type, name
        query = query.order_by(Prompt.template_type, Prompt.name)

        # Get total count before pagination
        from sqlalchemy import func as sa_func

        count_query = select(sa_func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        prompts_db = result.scalars().all()

        logger.debug(
            f"Prompts list requested by {current_user.email} "
            f"(template={template_type}, variant={content_variant}) - found {total} prompts"
        )

        # Convert to response format
        prompts = [
            PromptListItem(
                id=prompt.id,
                name=prompt.name,
                template_type=prompt.template_type,
                content_variant=prompt.content_variant,
                version=prompt.version,
                is_active=prompt.is_active,
                character_limit=prompt.character_limit,
                updated_at=prompt.updated_at.isoformat(),
                updated_by={"name": prompt.updater.name} if prompt.updater else None,
            )
            for prompt in prompts_db
        ]

        return {"items": prompts, "total": total, "limit": limit, "offset": offset}

    except Exception as e:
        logger.exception(f"Error listing prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to list prompts",
                "details": {},
            },
        )


@router.get(
    "/{prompt_id}",
    status_code=status.HTTP_200_OK,
    response_model=PromptResponse,
    summary="Get prompt",
    description="Get detailed prompt information",
)
async def get_prompt(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get prompt detail.

    Args:
        prompt_id: Prompt UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Prompt with full content and metadata

    Raises:
        404: Prompt not found
    """
    try:
        # Fetch prompt from database
        query = (
            select(Prompt)
            .options(selectinload(Prompt.updater))
            .where(Prompt.id == prompt_id)
        )

        result = await db.execute(query)
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PROMPT_NOT_FOUND",
                    "message": f"Prompt {prompt_id} not found",
                    "details": {},
                },
            )

        logger.debug(f"Prompt {prompt_id} requested by {current_user.email}")

        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            template_type=prompt.template_type,
            content_variant=prompt.content_variant,
            content=prompt.content,
            character_limit=prompt.character_limit,
            version=prompt.version,
            is_active=prompt.is_active,
            created_at=prompt.created_at.isoformat(),
            updated_at=prompt.updated_at.isoformat(),
            updated_by={"id": str(prompt.updater.id), "name": prompt.updater.name}
            if prompt.updater
            else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to get prompt",
                "details": {},
            },
        )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PromptResponse,
    summary="Create prompt",
    description="Create a new prompt (admin only)",
)
@require_admin
async def create_prompt(
    request: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Create a new prompt.

    Requires admin role.

    Args:
        request: Prompt creation data
        current_user: Authenticated user (admin)
        db: Database session

    Returns:
        Created prompt

    Raises:
        403: User not admin
        422: Validation error
    """
    try:
        # Validate template type
        valid_templates = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]
        if request.template_type not in valid_templates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid template type",
                    "details": {
                        "provided": request.template_type,
                        "allowed": valid_templates,
                    },
                },
            )

        # Validate content variant
        valid_variants = ["standard", "luxury"]
        if request.content_variant not in valid_variants:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid content variant",
                    "details": {
                        "provided": request.content_variant,
                        "allowed": valid_variants,
                    },
                },
            )

        # Create prompt in database
        new_prompt = Prompt(
            name=request.name,
            template_type=request.template_type,
            content_variant=request.content_variant,
            content=request.content,
            character_limit=request.character_limit,
            version=1,
            is_active=True,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        db.add(new_prompt)
        await db.commit()
        await db.refresh(new_prompt)

        # Create initial version record
        initial_version = PromptVersionDB(
            prompt_id=new_prompt.id,
            version=1,
            content=request.content,
            character_limit=request.character_limit,
            change_reason="Initial creation",
            created_by=current_user.id,
        )
        db.add(initial_version)
        await db.commit()

        logger.info(
            f"Prompt created: {request.name} ({request.template_type}/"
            f"{request.content_variant}) by user {current_user.email}"
        )

        return PromptResponse(
            id=new_prompt.id,
            name=new_prompt.name,
            template_type=new_prompt.template_type,
            content_variant=new_prompt.content_variant,
            content=new_prompt.content,
            character_limit=new_prompt.character_limit,
            version=new_prompt.version,
            is_active=new_prompt.is_active,
            created_at=new_prompt.created_at.isoformat(),
            updated_at=new_prompt.updated_at.isoformat(),
            updated_by={"id": str(current_user.id), "name": current_user.name},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creating prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to create prompt",
                "details": {},
            },
        )


@router.put(
    "/{prompt_id}",
    status_code=status.HTTP_200_OK,
    response_model=PromptResponse,
    summary="Update prompt",
    description="Update prompt (creates new version, admin only)",
)
@require_admin
async def update_prompt(
    prompt_id: UUID,
    request: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update prompt content.

    Creates a new version while preserving history.
    Requires admin role.

    Args:
        prompt_id: Prompt UUID
        request: Updated content and reason
        current_user: Authenticated user (admin)
        db: Database session

    Returns:
        Updated prompt with new version number

    Raises:
        403: User not admin
        404: Prompt not found
    """
    try:
        # Fetch current prompt
        query = select(Prompt).where(Prompt.id == prompt_id)
        result = await db.execute(query)
        prompt = result.scalar_one_or_none()

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PROMPT_NOT_FOUND",
                    "message": f"Prompt {prompt_id} not found",
                    "details": {},
                },
            )

        # Increment version number
        new_version = prompt.version + 1

        # Create new version record
        version_record = PromptVersionDB(
            prompt_id=prompt.id,
            version=new_version,
            content=request.content,
            character_limit=prompt.character_limit,
            change_reason=request.change_reason,
            created_by=current_user.id,
        )
        db.add(version_record)

        # Update current prompt
        prompt.content = request.content
        prompt.version = new_version
        prompt.updated_by = current_user.id

        await db.commit()
        await db.refresh(prompt)

        logger.info(
            f"Prompt {prompt_id} updated to version {new_version} by user {current_user.email}"
        )

        return PromptResponse(
            id=prompt.id,
            name=prompt.name,
            template_type=prompt.template_type,
            content_variant=prompt.content_variant,
            content=prompt.content,
            character_limit=prompt.character_limit,
            version=prompt.version,
            is_active=prompt.is_active,
            created_at=prompt.created_at.isoformat(),
            updated_at=prompt.updated_at.isoformat(),
            updated_by={"id": str(current_user.id), "name": current_user.name},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to update prompt",
                "details": {},
            },
        )


@router.get(
    "/{prompt_id}/versions",
    status_code=status.HTTP_200_OK,
    summary="Get prompt versions",
    description="Get version history for a prompt",
)
async def get_prompt_versions(
    prompt_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get prompt version history.

    Args:
        prompt_id: Prompt UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        List of prompt versions

    Raises:
        404: Prompt not found
    """
    try:
        # Fetch prompt versions from database
        query = (
            select(PromptVersionDB)
            .options(selectinload(PromptVersionDB.creator))
            .where(PromptVersionDB.prompt_id == prompt_id)
            .order_by(PromptVersionDB.version.desc())
        )

        result = await db.execute(query)
        versions_db = result.scalars().all()

        if not versions_db:
            # Check if prompt exists
            prompt_query = select(Prompt).where(Prompt.id == prompt_id)
            prompt_result = await db.execute(prompt_query)
            if not prompt_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "PROMPT_NOT_FOUND",
                        "message": f"Prompt {prompt_id} not found",
                        "details": {},
                    },
                )

        logger.debug(
            f"Prompt versions requested for {prompt_id} by {current_user.email} - found {len(versions_db)} versions"
        )

        # Convert to response format
        versions = [
            PromptVersion(
                version=version.version,
                content=version.content,
                change_reason=version.change_reason,
                created_at=version.created_at.isoformat(),
                created_by={
                    "id": str(version.creator.id),
                    "name": version.creator.name,
                },
            )
            for version in versions_db
        ]

        return {"items": versions}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting prompt versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to get prompt versions",
                "details": {},
            },
        )
