"""
Upload API endpoint.

POST /api/upload - Upload PDF files and create a reconciliation session.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..dependencies import get_upload_service
from ..schemas import SessionResponse
from ...services.upload_service import UploadService
from ...tasks import process_session_task

logger = logging.getLogger(__name__)


router = APIRouter(tags=["upload"])


@router.post(
    "/upload",
    response_model=SessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload PDF files for reconciliation",
    description="""
    Upload credit card statements and receipts for reconciliation.

    **Requirements:**
    - Files must be PDF format
    - Maximum 100 files per upload
    - Maximum 300MB per file

    **Process:**
    1. Files are validated and saved to temporary storage
    2. A new session is created with status='processing'
    3. Background extraction and matching is triggered
    4. Session ID is returned for status polling

    **Response:**
    - 202 Accepted: Files accepted, processing started
    - 400 Bad Request: Validation failed (file type, size, count)
    - 500 Internal Server Error: Server error during processing
    """
)
async def upload_files(
    files: List[UploadFile] = File(..., description="List of PDF files to upload"),
    upload_service: UploadService = Depends(get_upload_service)
) -> SessionResponse:
    """
    Upload PDF files and create reconciliation session.

    Args:
        files: List of uploaded PDF files
        upload_service: Injected UploadService instance

    Returns:
        SessionResponse with session ID and initial status

    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If server error occurs
    """
    try:
        # Process upload (validation + session creation)
        session = await upload_service.process_upload(files)
        logger.info(f"Session created: {session.id}, dispatching Celery task...")

        # Queue background processing task using Celery
        # This dispatches to Redis queue and returns immediately
        task = process_session_task.delay(str(session.id))
        logger.info(f"Celery task dispatched: {task.id} for session {session.id}")

        # Convert to dict first to avoid greenlet issues with computed columns
        return SessionResponse(
            id=session.id,
            status=session.status,
            upload_count=session.upload_count,
            total_transactions=session.total_transactions,
            total_receipts=session.total_receipts,
            matched_count=session.matched_count,
            created_at=session.created_at,
            expires_at=session.expires_at,
            updated_at=session.updated_at
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )
