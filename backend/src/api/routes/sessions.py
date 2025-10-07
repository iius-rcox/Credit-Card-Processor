"""
Sessions API endpoints.

GET /api/sessions - List all sessions (paginated, 90-day window)
GET /api/sessions/{id} - Get session details with all related data
DELETE /api/sessions/{id} - Delete a session
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import (
    get_employee_repository,
    get_match_result_repository,
    get_receipt_repository,
    get_session_repository,
    get_transaction_repository
)
from ..schemas import (
    PaginatedSessionsResponse,
    SessionDetailResponse,
    SessionResponse
)
from ...repositories.employee_repository import EmployeeRepository
from ...repositories.match_result_repository import MatchResultRepository
from ...repositories.receipt_repository import ReceiptRepository
from ...repositories.session_repository import SessionRepository
from ...repositories.transaction_repository import TransactionRepository


router = APIRouter(tags=["sessions"])


@router.get(
    "/sessions",
    response_model=PaginatedSessionsResponse,
    summary="List all sessions",
    description="""
    List all reconciliation sessions within 90-day window.

    **Features:**
    - Automatic 90-day TTL filtering (only shows non-expired sessions)
    - Pagination support (default 50 per page, max 100)
    - Sorted by creation date (newest first)

    **Response:**
    - 200 OK: Sessions list with pagination metadata
    - 500 Internal Server Error: Database error
    """
)
async def list_sessions(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    session_repo: SessionRepository = Depends(get_session_repository)
) -> PaginatedSessionsResponse:
    """
    List sessions with pagination and 90-day window filtering.

    Args:
        page: Page number (1-based)
        page_size: Items per page (max 100)
        session_repo: Injected SessionRepository

    Returns:
        PaginatedSessionsResponse with sessions and pagination metadata

    Raises:
        HTTPException 500: If database error occurs
    """
    try:
        sessions, total = await session_repo.list_sessions(page, page_size)

        return PaginatedSessionsResponse.create(
            sessions=sessions,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sessions: {str(e)}"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details",
    description="""
    Get detailed session information with all related data.

    **Includes:**
    - Session metadata (status, counts, dates)
    - All employees
    - All transactions
    - All receipts
    - All match results

    **Response:**
    - 200 OK: Session details
    - 404 Not Found: Session not found or expired
    - 500 Internal Server Error: Database error
    """
)
async def get_session(
    session_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repository),
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    receipt_repo: ReceiptRepository = Depends(get_receipt_repository),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repository)
) -> SessionDetailResponse:
    """
    Get session details with all related data.

    Args:
        session_id: UUID of the session
        session_repo: Injected SessionRepository
        employee_repo: Injected EmployeeRepository
        transaction_repo: Injected TransactionRepository
        receipt_repo: Injected ReceiptRepository
        match_result_repo: Injected MatchResultRepository

    Returns:
        SessionDetailResponse with all nested data

    Raises:
        HTTPException 404: If session not found or expired
        HTTPException 500: If database error occurs
    """
    try:
        # Get session with 90-day check
        session = await session_repo.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found or has expired"
            )

        # Get related data
        employees = await employee_repo.get_employees_by_session(session_id)
        transactions = await transaction_repo.get_transactions_by_session(session_id)
        receipts = await receipt_repo.get_receipts_by_session(session_id)
        match_results = await match_result_repo.get_match_results_by_session(session_id)

        # Build response
        return SessionDetailResponse(
            id=session.id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            updated_at=session.updated_at,
            status=session.status,
            upload_count=session.upload_count,
            total_transactions=session.total_transactions,
            total_receipts=session.total_receipts,
            matched_count=session.matched_count,
            employees=employees,
            transactions=transactions,
            receipts=receipts,
            match_results=match_results
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session details: {str(e)}"
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete session",
    description="""
    Delete a reconciliation session.

    **Behavior:**
    - Cascade deletes all related records (employees, transactions, receipts, match results)
    - Idempotent (returns 404 if session already deleted)

    **Response:**
    - 204 No Content: Session deleted successfully
    - 404 Not Found: Session not found
    - 500 Internal Server Error: Database error
    """
)
async def delete_session(
    session_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repository)
) -> None:
    """
    Delete a session and all related records.

    Args:
        session_id: UUID of the session to delete
        session_repo: Injected SessionRepository

    Raises:
        HTTPException 404: If session not found
        HTTPException 500: If database error occurs
    """
    try:
        deleted = await session_repo.delete_session(session_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        # No content response (204)
        return

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )
