"""
Content generation API endpoints.

Provides content generation and management:
- POST /api/v1/content/generate       - Generate content from project (501)
- GET  /api/v1/content/{project_id}   - Get generated content
- PUT  /api/v1/content/{id}/approve   - Approve content
- POST /api/v1/content/regenerate     - Regenerate specific field (501)
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.middleware.auth import get_current_user
from app.models.database import User, Project, GeneratedContent
from app.models.enums import TemplateType, ContentVariant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


# Request/Response Models

class ContentGenerateRequest(BaseModel):
    """Request to generate content for a project."""
    project_id: UUID = Field(..., description="Project ID to generate content for")
    template_type: str = Field(..., description="Template type")
    content_variant: str = Field(default="standard", description="Content variant: standard or luxury")
    fields: Optional[list[str]] = Field(None, description="Specific fields to generate (null = all)")


class ContentRegenerateRequest(BaseModel):
    """Request to regenerate specific content fields."""
    project_id: UUID = Field(..., description="Project ID")
    field_name: str = Field(..., description="Field name to regenerate")
    reason: Optional[str] = Field(None, description="Reason for regeneration")


class ContentApprovalRequest(BaseModel):
    """Request to approve content."""
    approved: bool = Field(..., description="Approval status")
    comments: Optional[str] = Field(None, description="Approval comments")


class ContentResponse(BaseModel):
    """Generated content response."""
    project_id: UUID
    generated_content: Dict[str, Any]
    template_type: str
    content_variant: str
    generated_at: str
    approved: bool = False


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    response_model=ContentResponse,
    summary="Generate content from project",
    description="Generate SEO content using Anthropic API based on project data"
)
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate content for a project using Anthropic API.

    This endpoint requires the full content generation pipeline
    (prompt loading, Anthropic API calls, result parsing) which
    is not yet wired into this route.
    """
    # Validate template type
    valid_templates = [t.value for t in TemplateType]
    if request.template_type not in valid_templates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid template type",
                "details": {"provided": request.template_type, "allowed": valid_templates},
            },
        )

    # Validate content variant
    valid_variants = [v.value for v in ContentVariant]
    if request.content_variant not in valid_variants:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid content variant",
                "details": {"provided": request.content_variant, "allowed": valid_variants},
            },
        )

    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {request.project_id} not found"},
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "NOT_IMPLEMENTED",
            "message": "Content generation pipeline is not yet wired into this endpoint. "
                       "Use the job processing pipeline to trigger content generation.",
        },
    )


@router.get(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ContentResponse,
    summary="Get generated content",
    description="Retrieve generated content for a project"
)
async def get_content(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get generated content for a project.

    Returns all generated content fields from the database.
    """
    # Verify project exists
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {project_id} not found"},
        )

    # Fetch generated content fields
    content_result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.project_id == project_id)
        .order_by(GeneratedContent.field_name)
    )
    fields = content_result.scalars().all()

    if not fields:
        # Fall back to project's JSONB generated_content field
        return ContentResponse(
            project_id=project_id,
            generated_content=project.generated_content or {},
            template_type="unknown",
            content_variant="standard",
            generated_at=project.updated_at.isoformat() + "Z",
            approved=False,
        )

    # Build response from individual field records
    content_dict: Dict[str, Any] = {}
    latest_at = project.updated_at
    all_approved = True
    template_type = "unknown"
    content_variant = "standard"

    for f in fields:
        content_dict[f.field_name] = f.content
        if f.created_at and f.created_at > latest_at:
            latest_at = f.created_at
        if not f.is_approved:
            all_approved = False
        template_type = f.template_type.value
        content_variant = f.content_variant.value

    return ContentResponse(
        project_id=project_id,
        generated_content=content_dict,
        template_type=template_type,
        content_variant=content_variant,
        generated_at=latest_at.isoformat() + "Z",
        approved=all_approved,
    )


@router.put(
    "/{content_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve content",
    description="Approve or reject generated content"
)
async def approve_content(
    content_id: UUID,
    request: ContentApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Approve or reject generated content."""
    result = await db.execute(
        select(GeneratedContent).where(GeneratedContent.id == content_id)
    )
    content = result.scalar_one_or_none()

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Content {content_id} not found"},
        )

    content.is_approved = request.approved
    content.approved_by = current_user.id if request.approved else None
    content.approved_at = datetime.now(timezone.utc) if request.approved else None
    await db.commit()
    await db.refresh(content)

    logger.info(
        "Content %s %s by user %s",
        content_id,
        "approved" if request.approved else "rejected",
        current_user.email,
    )

    return {
        "id": str(content.id),
        "approved": content.is_approved,
        "approved_by": {
            "id": str(current_user.id),
            "name": current_user.name,
        } if request.approved else None,
        "approved_at": content.approved_at.isoformat() + "Z" if content.approved_at else None,
        "comments": request.comments,
    }


@router.post(
    "/regenerate",
    status_code=status.HTTP_200_OK,
    summary="Regenerate specific field",
    description="Regenerate a specific content field using Anthropic API"
)
async def regenerate_field(
    request: ContentRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Regenerate a specific content field.

    This endpoint requires the Anthropic API pipeline which
    is not yet wired into this route.
    """
    # Verify project exists
    result = await db.execute(select(Project).where(Project.id == request.project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": f"Project {request.project_id} not found"},
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "NOT_IMPLEMENTED",
            "message": "Field regeneration requires the Anthropic API pipeline. "
                       "Use the job processing pipeline to regenerate content.",
        },
    )
