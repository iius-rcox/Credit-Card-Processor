"""
Upload API endpoint.

POST /api/upload - Upload PDF files and create a reconciliation session.
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from ..dependencies import get_upload_service, get_extraction_service, get_matching_service
from ..schemas import SessionResponse
from ...services.upload_service import UploadService, process_session_background
from ...services.extraction_service import ExtractionService
from ...services.matching_service import MatchingService


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
    upload_service: UploadService = Depends(get_upload_service),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    matching_service: MatchingService = Depends(get_matching_service)
) -> SessionResponse:
    """
    Upload PDF files and create reconciliation session.

    Args:
        background_tasks: FastAPI BackgroundTasks for async processing
        files: List of uploaded PDF files
        upload_service: Injected UploadService instance
        extraction_service: Injected ExtractionService instance
        matching_service: Injected MatchingService instance

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
        background_tasks.add_task(
            process_session_background,
            session.id,
            extraction_service,
            matching_service
        )

        return SessionResponse.model_validate(session)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise

    except Exception as e:
        # Catch unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )
