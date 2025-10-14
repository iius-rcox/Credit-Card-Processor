"""
UploadService - Handles file upload and validation.

This module manages the upload workflow including file validation,
storage, and session creation.
"""

import asyncio
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, UploadFile

from ..config import settings
from ..models.session import Session
from ..repositories.session_repository import SessionRepository
from ..repositories.progress_repository import ProgressRepository
from ..repositories.transaction_repository import TransactionRepository
from ..repositories.receipt_repository import ReceiptRepository
from ..schemas.processing_progress import ProcessingProgress
from ..schemas.phase_progress import PhaseProgress
from .progress_tracker import ProgressTracker

if TYPE_CHECKING:
    from .extraction_service import ExtractionService
    from .matching_service import MatchingService

logger = logging.getLogger(__name__)


class UploadService:
    """
    Service for handling file uploads and session creation.

    Validates uploaded files, creates sessions, and dispatches background
    processing tasks.
    """

    MAX_FILE_COUNT = 100
    MAX_FILE_SIZE = 300 * 1024 * 1024  # 300MB in bytes
    ALLOWED_MIME_TYPES = ["application/pdf"]

    def __init__(
        self,
        session_repo: SessionRepository,
        transaction_repo: TransactionRepository,
        receipt_repo: ReceiptRepository,
        extraction_service: Optional['ExtractionService'] = None,
        progress_repo: Optional[ProgressRepository] = None
    ):
        """
        Initialize upload service.

        Args:
            session_repo: SessionRepository instance
            transaction_repo: TransactionRepository instance
            receipt_repo: ReceiptRepository instance
            extraction_service: Optional ExtractionService for inline extraction
            progress_repo: Optional ProgressRepository for progress tracking
        """
        self.session_repo = session_repo
        self.transaction_repo = transaction_repo
        self.receipt_repo = receipt_repo
        self.extraction_service = extraction_service
        self.progress_repo = progress_repo

    async def process_upload(
        self, files: List[UploadFile]
    ) -> Session:
        """
        Process uploaded files and extract data immediately.

        Args:
            files: List of uploaded PDF files

        Returns:
            Created Session instance with status='matching' (extraction complete)

        Raises:
            HTTPException: If validation fails or extraction fails

        Note:
            PDFs are processed in-memory. No temporary storage is used.
            Extraction happens synchronously during the upload request.

        Example:
            session = await service.process_upload(files)
        """
        # Validate file count
        if len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files uploaded. Please upload at least one PDF file."
            )

        if len(files) > self.MAX_FILE_COUNT:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum {self.MAX_FILE_COUNT} files allowed, got {len(files)}."
            )

        # Validate each file
        validated_files = []
        for file in files:
            await self._validate_file(file)
            validated_files.append(file)

        # Create session with extracting status
        session = await self.session_repo.create_session({
            "status": "extracting",
            "upload_count": len(validated_files)
        })

        # Initialize progress tracking for extraction phase
        if self.progress_repo:
            await self._init_extraction_progress(session.id, len(validated_files))

        # Extract data from PDFs immediately (no temp storage!)
        all_transactions = []
        all_receipts = []

        for idx, file in enumerate(validated_files):
            # Update progress: extracting file X of Y
            if self.progress_repo:
                await self._update_extraction_progress(
                    session.id,
                    files_processed=idx,
                    total_files=len(validated_files),
                    current_filename=file.filename or f"file_{idx}",
                    transactions_found=len(all_transactions)
                )

            # Extract directly from file stream (no disk write!)
            if self.extraction_service:
                try:
                    file_transactions, file_receipts = await self.extraction_service.extract_from_upload_file(
                        file, session.id
                    )
                    all_transactions.extend(file_transactions)
                    all_receipts.extend(file_receipts)

                    logger.info(f"[UPLOAD] Extracted {len(file_transactions)} transactions from {file.filename}")
                except Exception as e:
                    logger.error(f"[UPLOAD] Failed to extract from {file.filename}: {e}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to extract data from {file.filename}: {str(e)}"
                    )

        # Bulk insert transactions and receipts
        if all_transactions:
            await self.transaction_repo.bulk_create_transactions(all_transactions)
            logger.info(f"[UPLOAD] Saved {len(all_transactions)} transactions to database")

        if all_receipts:
            await self.receipt_repo.bulk_create_receipts(all_receipts)
            logger.info(f"[UPLOAD] Saved {len(all_receipts)} receipts to database")

        # Update session with counts and transition to matching status
        await self.session_repo.update_session_status(session.id, "matching")
        await self.session_repo.update_session_counts(session.id)

        # Complete extraction progress
        if self.progress_repo:
            await self._complete_extraction_progress(
                session.id,
                len(validated_files),
                len(all_transactions)
            )

        # Queue lightweight matching task (only session ID needed)
        from ..tasks import match_session_task
        match_session_task.delay(str(session.id))

        return session

    async def _validate_file(self, file: UploadFile) -> None:
        """
        Validate a single uploaded file.

        Args:
            file: FastAPI UploadFile instance

        Raises:
            HTTPException: If validation fails
        """
        # Check file type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{file.content_type}' for file '{file.filename}'. Only PDF files are allowed."
            )

        # Check file extension
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension for '{file.filename}'. Only .pdf files are allowed."
            )

        # Check file size
        # Note: For large files, we should read in chunks to avoid memory issues
        file_content = await file.read()
        file_size = len(file_content)

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' is empty."
            )

        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File '{file.filename}' is too large ({actual_mb:.2f}MB). Maximum size is {max_mb}MB."
            )

        # Reset file pointer for later reading
        await file.seek(0)


    async def _init_extraction_progress(self, session_id: UUID, file_count: int) -> None:
        """
        Initialize progress tracking for extraction phase.

        Args:
            session_id: UUID of the session
            file_count: Number of files being extracted
        """
        progress = ProcessingProgress(
            overall_percentage=0,
            current_phase="extracting",
            phases={
                "upload": PhaseProgress(
                    status="completed",
                    percentage=100,
                    completed_at=datetime.utcnow()
                ),
                "extracting": PhaseProgress(
                    status="in_progress",
                    percentage=0,
                    started_at=datetime.utcnow(),
                    total_files=file_count,
                    files_processed=0,
                    transactions_found=0
                ),
                "matching": PhaseProgress(
                    status="pending",
                    percentage=0
                ),
                "report_generation": PhaseProgress(
                    status="pending",
                    percentage=0
                )
            },
            last_update=datetime.utcnow(),
            status_message=f"Starting extraction of {file_count} file(s)..."
        )

        await self.progress_repo.update_session_progress(session_id, progress)

    async def _update_extraction_progress(
        self,
        session_id: UUID,
        files_processed: int,
        total_files: int,
        current_filename: str,
        transactions_found: int = 0
    ) -> None:
        """
        Update progress during PDF extraction.

        Args:
            session_id: Session ID
            files_processed: Number of files processed so far
            total_files: Total number of files to extract
            current_filename: Name of the current file
            transactions_found: Total transactions found so far
        """
        percentage = int((files_processed / total_files) * 100) if total_files > 0 else 0

        progress = ProcessingProgress(
            overall_percentage=int(percentage * 0.6),  # Extraction is 60% of overall
            current_phase="extracting",
            phases={
                "upload": PhaseProgress(
                    status="completed",
                    percentage=100
                ),
                "extracting": PhaseProgress(
                    status="in_progress",
                    percentage=percentage,
                    files_processed=files_processed,
                    total_files=total_files,
                    transactions_found=transactions_found
                ),
                "matching": PhaseProgress(
                    status="pending",
                    percentage=0
                ),
                "report_generation": PhaseProgress(
                    status="pending",
                    percentage=0
                )
            },
            last_update=datetime.utcnow(),
            status_message=f"Extracting data from {current_filename}... ({files_processed}/{total_files})"
        )

        await self.progress_repo.update_session_progress(session_id, progress)

    async def _complete_extraction_progress(
        self,
        session_id: UUID,
        total_files: int,
        total_transactions: int
    ) -> None:
        """
        Mark extraction phase as complete.

        Args:
            session_id: Session ID
            total_files: Total number of files extracted
            total_transactions: Total transactions extracted
        """
        progress = ProcessingProgress(
            overall_percentage=60,  # Extraction complete = 60% overall
            current_phase="extracting",
            phases={
                "upload": PhaseProgress(
                    status="completed",
                    percentage=100
                ),
                "extracting": PhaseProgress(
                    status="completed",
                    percentage=100,
                    completed_at=datetime.utcnow(),
                    files_processed=total_files,
                    total_files=total_files,
                    transactions_found=total_transactions
                ),
                "matching": PhaseProgress(
                    status="pending",
                    percentage=0
                ),
                "report_generation": PhaseProgress(
                    status="pending",
                    percentage=0
                )
            },
            last_update=datetime.utcnow(),
            status_message=f"Extraction complete. {total_transactions} transaction(s) extracted from {total_files} file(s)."
        )

        await self.progress_repo.update_session_progress(session_id, progress)




def process_session_background_sync(session_id: UUID) -> None:
    """
    Synchronous wrapper for background task processing.

    FastAPI's BackgroundTasks runs in a thread pool, so we need to
    get the current event loop or create a new one.
    """
    import asyncio
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running (shouldn't happen in background thread), create task
            asyncio.create_task(process_session_background(session_id))
        else:
            # Run in the existing loop
            loop.run_until_complete(process_session_background(session_id))
    except RuntimeError:
        # No event loop exists, create a new one
        asyncio.run(process_session_background(session_id))


async def process_session_background(
    session_id: UUID
) -> None:
    """
    DEPRECATED: This function is deprecated after the PDF extraction refactor.

    Previously handled full extraction + matching workflow using temp storage.
    Now replaced by:
    - Inline extraction during upload (in process_upload)
    - match_session_task for matching only

    This function is kept to prevent import errors but should not be called.
    If called by old Celery tasks, it will fail gracefully and mark session as failed.

    Args:
        session_id: UUID of the session to process
    """
    logger.error(
        f"DEPRECATED FUNCTION CALLED: process_session_background for session {session_id}. "
        "This function is deprecated after the PDF extraction refactor (008). "
        "Use inline extraction + match_session_task instead."
    )

    # Fail the session gracefully
    from urllib.parse import quote_plus
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from ..config import settings
    from ..repositories.session_repository import SessionRepository

    database_url = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    worker_engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        connect_args={"server_settings": {"jit": "off"}}
    )

    WorkerSessionLocal = async_sessionmaker(
        worker_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    try:
        async with WorkerSessionLocal() as db:
            session_repo = SessionRepository(db)
            await session_repo.update_session_status(session_id, "failed")
            await db.commit()
            logger.info(f"Marked session {session_id} as failed (deprecated function called)")
    finally:
        await worker_engine.dispose()
