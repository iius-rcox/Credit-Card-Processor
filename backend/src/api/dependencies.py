"""
FastAPI dependency injection for repositories and services.

This module provides dependency functions that FastAPI uses to inject
repositories and services into endpoint handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories.alias_repository import AliasRepository
from ..repositories.employee_repository import EmployeeRepository
from ..repositories.match_result_repository import MatchResultRepository
from ..repositories.progress_repository import ProgressRepository
from ..repositories.receipt_repository import ReceiptRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.transaction_repository import TransactionRepository
from ..services.extraction_service import ExtractionService
from ..services.matching_service import MatchingService
from ..services.report_service import ReportService
from ..services.upload_service import UploadService


# Repository dependencies
def get_session_repository(db: AsyncSession = Depends(get_db)) -> SessionRepository:
    """Get SessionRepository instance."""
    return SessionRepository(db)


def get_employee_repository(db: AsyncSession = Depends(get_db)) -> EmployeeRepository:
    """Get EmployeeRepository instance."""
    return EmployeeRepository(db)


def get_transaction_repository(db: AsyncSession = Depends(get_db)) -> TransactionRepository:
    """Get TransactionRepository instance."""
    return TransactionRepository(db)


def get_receipt_repository(db: AsyncSession = Depends(get_db)) -> ReceiptRepository:
    """Get ReceiptRepository instance."""
    return ReceiptRepository(db)


def get_match_result_repository(db: AsyncSession = Depends(get_db)) -> MatchResultRepository:
    """Get MatchResultRepository instance."""
    return MatchResultRepository(db)


def get_progress_repository(db: AsyncSession = Depends(get_db)) -> ProgressRepository:
    """Get ProgressRepository instance."""
    return ProgressRepository(db)


def get_alias_repository(db: AsyncSession = Depends(get_db)) -> AliasRepository:
    """Get AliasRepository instance."""
    return AliasRepository(db)


# Service dependencies
def get_upload_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    progress_repo: ProgressRepository = Depends(get_progress_repository)
) -> UploadService:
    """Get UploadService instance."""
    return UploadService(session_repo, progress_repo)


def get_extraction_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    receipt_repo: ReceiptRepository = Depends(get_receipt_repository),
    progress_repo: ProgressRepository = Depends(get_progress_repository),
    alias_repo: AliasRepository = Depends(get_alias_repository)
) -> ExtractionService:
    """Get ExtractionService instance."""
    return ExtractionService(
        session_repo, employee_repo, transaction_repo, receipt_repo, progress_repo, alias_repo
    )


def get_matching_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    receipt_repo: ReceiptRepository = Depends(get_receipt_repository),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repository)
) -> MatchingService:
    """Get MatchingService instance."""
    return MatchingService(
        session_repo, transaction_repo, receipt_repo, match_result_repo
    )


def get_report_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    employee_repo: EmployeeRepository = Depends(get_employee_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    receipt_repo: ReceiptRepository = Depends(get_receipt_repository),
    match_result_repo: MatchResultRepository = Depends(get_match_result_repository)
) -> ReportService:
    """Get ReportService instance."""
    return ReportService(
        session_repo,
        employee_repo,
        transaction_repo,
        receipt_repo,
        match_result_repo
    )
