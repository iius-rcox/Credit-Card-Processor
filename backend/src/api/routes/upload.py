"""
Upload API endpoint.

POST /api/upload - Upload PDF files and create a reconciliation session.
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from ..dependencies import get_upload_service
from ..schemas import SessionResponse
from ...services.upload_service import UploadService, process_session_background_sync


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
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="List of PDF files to upload"),
    upload_service: UploadService = Depends(get_upload_service)
) -> SessionResponse:
    """
    Upload PDF files and create reconciliation session.

    Args:
        background_tasks: FastAPI BackgroundTasks for async processing
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

        # Add background task to process the files
        # Note: We only pass the session_id, not the services, because
        # the services contain DB sessions tied to this request context
        # We use the sync wrapper because FastAPI BackgroundTasks requires sync functions
        background_tasks.add_task(
            process_session_background_sync,
            session.id
        )

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
