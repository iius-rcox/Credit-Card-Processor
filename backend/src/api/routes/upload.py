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
    1. Files are validated (PDF format, size, count)
    2. PDFs are extracted inline (no temporary storage)
    3. Session status transitions: extracting → matching
    4. Background matching task is queued automatically
    5. Session ID is returned for status polling

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
        # Process upload: validation + inline extraction + queue matching task
        # Note: process_upload() now handles extraction inline and queues match_session_task
        session = await upload_service.process_upload(files)
        logger.info(f"✓ Upload completed: session {session.id}, status={session.status}")
        logger.info(f"  Uploaded: {session.upload_count} file(s)")
        logger.info(f"  Extracted: {session.total_transactions} transaction(s)")
        logger.info(f"  Matching task queued automatically by upload_service")

        # Create response
        logger.info(f"→ Creating SessionResponse for session {session.id}...")
        try:
            response = SessionResponse(
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
            logger.info(f"✓ SessionResponse created successfully for session {session.id}")
            logger.info(f"  Response: {response.model_dump_json()}")
            return response
        except Exception as response_error:
            logger.error(f"✗ FAILED to create SessionResponse!", exc_info=True)
            logger.error(f"  Error type: {type(response_error).__name__}")
            logger.error(f"  Error message: {str(response_error)}")
            raise

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        logger.warning(f"HTTP exception during upload processing", exc_info=True)
        raise

    except Exception as e:
        # Catch unexpected errors
        logger.error(f"✗ Unexpected error during upload processing!", exc_info=True)
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )
