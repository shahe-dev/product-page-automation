"""
Upload API endpoints for file handling.

Provides file upload functionality with streaming support:
- POST /api/v1/upload/pdf       - Upload PDF file for processing
- POST /api/v1/upload/images    - Upload additional images
- GET  /api/v1/upload/{id}/status - Get upload status
"""

import logging
import re
import tempfile
import os
from typing import Optional
from uuid import UUID
import uuid as uuid_mod

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.config.settings import get_settings
from app.middleware.auth import get_current_user
from app.models.database import User
from app.services.storage_service import StorageService
from app.services.job_manager import JobManager
from app.repositories.job_repository import JobRepository
from app.background.task_queue import TaskQueue

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


# Constants
MAX_PDF_SIZE_BYTES = 200 * 1024 * 1024  # 200MB
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming
ALLOWED_PDF_TYPES = ["application/pdf"]
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
VALID_TEMPLATES = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]


def sanitize_filename(filename: str) -> str:
    """Remove path separators and dangerous characters from filenames."""
    # Strip any path components -- only keep the base name
    name = os.path.basename(filename)
    # Remove null bytes and other dangerous characters
    name = name.replace("\x00", "")
    # Only allow word chars, hyphens, dots
    name = re.sub(r'[^\w\-.]', '_', name)
    if not name or name.startswith('.'):
        name = f"upload_{uuid_mod.uuid4().hex[:8]}"
    return name


async def stream_upload_to_temp(
    file: UploadFile,
    max_size_bytes: int,
    chunk_size: int = CHUNK_SIZE
) -> tuple[str, int]:
    """
    Stream upload file to a temporary file with size validation.

    Args:
        file: Uploaded file
        max_size_bytes: Maximum allowed file size
        chunk_size: Size of chunks to read

    Returns:
        Tuple of (temp_file_path, file_size_bytes)

    Raises:
        HTTPException: If file exceeds size limit
    """
    total_size = 0

    # Create temp file with sanitized extension
    safe_name = sanitize_filename(file.filename or "upload")
    temp_fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(safe_name)[1])

    try:
        with os.fdopen(temp_fd, "wb") as temp_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)

                # Check size limit during streaming
                if total_size > max_size_bytes:
                    # Clean up and raise error
                    os.unlink(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "error_code": "FILE_TOO_LARGE",
                            "message": f"File size exceeds {max_size_bytes // (1024*1024)}MB limit",
                            "details": {
                                "max_size_mb": max_size_bytes // (1024 * 1024)
                            }
                        }
                    )

                temp_file.write(chunk)

        return temp_path, total_size

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e


def validate_content_length(request: Request, max_size_bytes: int) -> Optional[int]:
    """
    Validate Content-Length header if present.

    Args:
        request: FastAPI request
        max_size_bytes: Maximum allowed size

    Returns:
        Content length if valid, None if not provided

    Raises:
        HTTPException: If content length exceeds limit
    """
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
            if length > max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error_code": "FILE_TOO_LARGE",
                        "message": f"File size exceeds {max_size_bytes // (1024*1024)}MB limit",
                        "details": {
                            "content_length_mb": length // (1024 * 1024),
                            "max_size_mb": max_size_bytes // (1024 * 1024)
                        }
                    }
                )
            return length
        except ValueError:
            pass
    return None


@router.post(
    "/file",
    status_code=status.HTTP_201_CREATED,
    summary="Upload file to GCS",
    description="Upload a file to GCS and return its URL for use with /process/extract"
)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload (PDF only)"),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a file to GCS for the multi-template pipeline.

    This endpoint uploads the file to GCS and returns the gcs_url.
    Use the returned URL with /process/extract to start processing.

    Args:
        request: FastAPI request
        file: PDF file (max 200MB)
        current_user: Authenticated user

    Returns:
        gcs_url: GCS path for use with /process/extract
        filename: Original filename
        size: File size in bytes

    Raises:
        400: Invalid file type
        413: File too large
    """
    temp_path = None

    try:
        # Validate content length early (fast fail)
        validate_content_length(request, MAX_PDF_SIZE_BYTES)

        # Validate file type
        if file.content_type not in ALLOWED_PDF_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "File must be a PDF",
                    "details": {
                        "provided_type": file.content_type,
                        "allowed_types": ALLOWED_PDF_TYPES
                    }
                }
            )

        # Stream upload to temp file (memory efficient)
        temp_path, file_size = await stream_upload_to_temp(file, MAX_PDF_SIZE_BYTES)

        # Validate actual file content (magic bytes) -- PDF must start with %PDF
        with open(temp_path, "rb") as fh:
            header = fh.read(5)
        if not header.startswith(b"%PDF"):
            os.unlink(temp_path)
            temp_path = None
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "Uploaded file is not a valid PDF",
                    "details": {}
                }
            )

        # Upload to GCS
        safe_filename = sanitize_filename(file.filename or "upload.pdf")
        import datetime
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        gcs_path = f"uploads/{current_user.id}/{timestamp}_{safe_filename}"

        storage_service = StorageService()
        gcs_url = await storage_service.upload_file(
            source_file=temp_path,
            destination_blob_path=gcs_path,
            content_type="application/pdf"
        )

        logger.info(
            f"File uploaded by user {current_user.email}: {safe_filename} "
            f"({file_size / (1024*1024):.2f}MB) -> {gcs_url}"
        )

        return {
            "gcs_url": gcs_url,
            "filename": safe_filename,
            "size": file_size,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to upload file",
                "details": {}
            }
        )
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post(
    "/pdf",
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF for processing",
    description="Upload a PDF file and create a processing job"
)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF file to upload"),
    template_type: str = Form(..., description="Template type: aggregators, opr, mpp, adop, adre, commercial"),
    template_id: Optional[str] = Form(None, description="Specific template ID to use"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload PDF file and create processing job.

    Uses streaming upload to avoid memory issues with large files.

    Args:
        request: FastAPI request
        file: PDF file (max 50MB)
        template_type: Website template type
        template_id: Optional specific template ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Job ID and status

    Raises:
        400: Invalid file type or size
        413: File too large
        422: Validation error
        429: Rate limit exceeded
    """
    temp_path = None

    try:
        # Validate content length early (fast fail)
        validate_content_length(request, MAX_PDF_SIZE_BYTES)

        # Validate file type (client-supplied header -- first-pass check)
        if file.content_type not in ALLOWED_PDF_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "File must be a PDF",
                    "details": {
                        "provided_type": file.content_type,
                        "allowed_types": ALLOWED_PDF_TYPES
                    }
                }
            )

        # Validate template type
        if template_type not in VALID_TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid template type",
                    "details": {
                        "provided": template_type,
                        "allowed": VALID_TEMPLATES
                    }
                }
            )

        # Stream upload to temp file (memory efficient)
        temp_path, file_size = await stream_upload_to_temp(file, MAX_PDF_SIZE_BYTES)
        file_size_mb = file_size / (1024 * 1024)

        # Validate actual file content (magic bytes) -- PDF must start with %PDF
        with open(temp_path, "rb") as fh:
            header = fh.read(5)
        if not header.startswith(b"%PDF"):
            os.unlink(temp_path)
            temp_path = None
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "Uploaded file is not a valid PDF",
                    "details": {}
                }
            )

        # 1. Upload temp file to Cloud Storage (sanitized filename)
        safe_filename = sanitize_filename(file.filename or "upload.pdf")
        storage_service = StorageService()
        pdf_url = await storage_service.upload_file(
            source_file=temp_path,
            destination_blob_path=f"{current_user.id}/{safe_filename}",
            content_type="application/pdf"
        )

        # 2. Create job and dispatch to task queue
        # This method handles transaction boundaries: commits the job before
        # dispatching to ensure it's visible to the async callback.
        job_repo = JobRepository(db)
        task_queue = TaskQueue()
        job_manager = JobManager(job_repo, task_queue)

        # Parse template_id if provided
        parsed_template_id = None
        if template_id:
            try:
                parsed_template_id = UUID(template_id)
            except ValueError:
                logger.warning(f"Invalid template_id format: {template_id}, ignoring")

        job, task_name = await job_manager.create_and_dispatch_job(
            user_id=current_user.id,
            template_type=template_type,
            pdf_path=pdf_url,
            template_id=parsed_template_id,
            processing_config={
                "pdf_url": pdf_url,
                "original_filename": safe_filename,
                "file_size_mb": round(file_size_mb, 2)
            }
        )

        logger.info(
            f"PDF uploaded by user {current_user.email}: {safe_filename} "
            f"({file_size_mb:.2f}MB, template={template_type}, job_id={job.id}, task={task_name})"
        )

        # Return real job info
        return {
            "job_id": str(job.id),
            "status": job.status.value,
            "template_type": template_type,
            "file_size_mb": round(file_size_mb, 2),
            "created_at": job.created_at.isoformat() + "Z"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error uploading PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "Failed to upload PDF",
                "details": {}
            }
        )
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post(
    "/images",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Upload additional images (not yet implemented)",
    description="Upload additional images for a project"
)
async def upload_images(
    request: Request,
    files: list[UploadFile] = File(..., description="Image files to upload"),
    project_id: str = Form(..., description="Project ID to attach images to"),
    category: Optional[str] = Form("general", description="Image category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload additional images for a project.

    Not yet implemented -- files are not persisted to Cloud Storage or the
    database.  Returns 501 until the full upload pipeline is wired.

    Raises:
        501: Not yet implemented
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "NOT_IMPLEMENTED",
            "message": "Image upload is not yet implemented. Files are not persisted.",
            "details": {"project_id": project_id}
        }
    )


@router.get(
    "/{upload_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Get upload status (not yet implemented)",
    description="Check the status of an upload operation"
)
async def get_upload_status(
    upload_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get upload status and progress.

    Not yet implemented -- returns 501.
    Use GET /jobs/{job_id}/status instead.

    Args:
        upload_id: Upload/job UUID
        current_user: Authenticated user
        db: Database session

    Raises:
        501: Not yet implemented
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error_code": "NOT_IMPLEMENTED",
            "message": "Upload status endpoint is not yet implemented. Use GET /jobs/{job_id}/status instead.",
            "details": {"upload_id": str(upload_id)}
        }
    )
