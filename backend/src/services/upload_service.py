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

from ..models.session import Session
from ..repositories.session_repository import SessionRepository
from ..repositories.progress_repository import ProgressRepository
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

    def __init__(self, session_repo: SessionRepository, progress_repo: Optional[ProgressRepository] = None):
        """
        Initialize upload service.

        Args:
            session_repo: SessionRepository instance
            progress_repo: Optional ProgressRepository for progress tracking
        """
        self.session_repo = session_repo
        self.progress_repo = progress_repo

    async def process_upload(
        self, files: List[UploadFile]
    ) -> Session:
        """
        Process uploaded files and create a new session.

        Args:
            files: List of uploaded PDF files

        Returns:
            Created Session instance with status='processing'

        Raises:
            HTTPException: If validation fails

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

        # Create session
        session = await self.session_repo.create_session({
            "status": "processing",
            "upload_count": len(validated_files)
        })

        # Initialize progress tracking for upload phase
        if self.progress_repo:
            await self._init_upload_progress(session.id, len(validated_files))

        # Save files to temporary storage with progress tracking
        temp_dir = await self._save_files_to_temp_with_progress(session.id, validated_files)

        # TODO: Dispatch background task for extraction
        # This would typically be done with Celery, Redis Queue, or FastAPI BackgroundTasks
        # For now, we just return the session - actual extraction implementation
        # will be added when ExtractionService is integrated

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

    async def _save_files_to_temp(
        self, session_id: UUID, files: List[UploadFile]
    ) -> Path:
        """
        Save uploaded files to temporary storage.

        Args:
            session_id: UUID of the session
            files: List of validated upload files

        Returns:
            Path to temporary directory containing saved files

        Note:
            Files are NOT stored permanently. They are discarded after extraction.
            This follows the spec requirement of temporary storage only.
        """
        # Create temporary directory for this session
        temp_dir = Path(tempfile.gettempdir()) / f"credit-card-session-{session_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Save each file
        for idx, file in enumerate(files):
            # Generate safe filename
            safe_filename = f"{idx:04d}_{self._sanitize_filename(file.filename)}"
            file_path = temp_dir / safe_filename

            # Write file content
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Reset file pointer
            await file.seek(0)

        return temp_dir

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other issues.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem storage
        """
        # Remove path components
        filename = os.path.basename(filename)

        # Replace potentially problematic characters
        for char in ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:195] + ext

        return filename

    async def _init_upload_progress(self, session_id: UUID, file_count: int) -> None:
        """
        Initialize progress tracking for upload phase.

        Args:
            session_id: UUID of the session
            file_count: Number of files being uploaded
        """
        progress = ProcessingProgress(
            overall_percentage=0,
            current_phase="upload",
            phases={
                "upload": PhaseProgress(
                    status="in_progress",
                    percentage=0,
                    started_at=datetime.utcnow(),
                    files_uploaded=0,
                    bytes_uploaded=0
                ),
                "processing": PhaseProgress(
                    status="pending",
                    percentage=0,
                    total_files=file_count
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
            status_message=f"Starting upload of {file_count} file(s)..."
        )

        await self.progress_repo.update_session_progress(session_id, progress)

    async def _save_files_to_temp_with_progress(
        self, session_id: UUID, files: List[UploadFile]
    ) -> Path:
        """
        Save uploaded files to temporary storage with progress tracking.

        Args:
            session_id: UUID of the session
            files: List of validated upload files

        Returns:
            Path to temporary directory containing saved files
        """
        # Create temporary directory for this session
        temp_dir = Path(tempfile.gettempdir()) / f"credit-card-session-{session_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        total_files = len(files)
        total_bytes_uploaded = 0

        # Save each file with progress updates
        for idx, file in enumerate(files):
            # Generate safe filename
            safe_filename = f"{idx:04d}_{self._sanitize_filename(file.filename)}"
            file_path = temp_dir / safe_filename

            # Write file content
            content = await file.read()
            file_size = len(content)
            with open(file_path, "wb") as f:
                f.write(content)

            # Reset file pointer
            await file.seek(0)

            # Update progress
            total_bytes_uploaded += file_size
            if self.progress_repo:
                await self._update_upload_progress(
                    session_id,
                    files_uploaded=idx + 1,
                    total_files=total_files,
                    bytes_uploaded=total_bytes_uploaded,
                    current_filename=file.filename or f"file_{idx}"
                )

        # Mark upload phase as complete
        if self.progress_repo:
            await self._complete_upload_progress(session_id, total_files, total_bytes_uploaded)

        return temp_dir

    async def _update_upload_progress(
        self,
        session_id: UUID,
        files_uploaded: int,
        total_files: int,
        bytes_uploaded: int,
        current_filename: str
    ) -> None:
        """
        Update progress during file upload.

        Args:
            session_id: Session ID
            files_uploaded: Number of files uploaded so far
            total_files: Total number of files to upload
            bytes_uploaded: Total bytes uploaded
            current_filename: Name of the current file
        """
        percentage = int((files_uploaded / total_files) * 100)

        progress = ProcessingProgress(
            overall_percentage=int(percentage * 0.1),  # Upload is 10% of overall
            current_phase="upload",
            phases={
                "upload": PhaseProgress(
                    status="in_progress",
                    percentage=percentage,
                    files_uploaded=files_uploaded,
                    bytes_uploaded=bytes_uploaded
                ),
                "processing": PhaseProgress(
                    status="pending",
                    percentage=0,
                    total_files=total_files
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
            status_message=f"Uploading file {files_uploaded}/{total_files}: {current_filename}"
        )

        await self.progress_repo.update_session_progress(session_id, progress)

    async def _complete_upload_progress(
        self,
        session_id: UUID,
        total_files: int,
        total_bytes: int
    ) -> None:
        """
        Mark upload phase as complete.

        Args:
            session_id: Session ID
            total_files: Total number of files uploaded
            total_bytes: Total bytes uploaded
        """
        progress = ProcessingProgress(
            overall_percentage=10,  # Upload complete = 10% overall
            current_phase="upload",
            phases={
                "upload": PhaseProgress(
                    status="completed",
                    percentage=100,
                    completed_at=datetime.utcnow(),
                    files_uploaded=total_files,
                    bytes_uploaded=total_bytes
                ),
                "processing": PhaseProgress(
                    status="pending",
                    percentage=0,
                    total_files=total_files
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
            status_message=f"Upload complete. {total_files} file(s) uploaded successfully."
        )

        await self.progress_repo.update_session_progress(session_id, progress)

    async def get_upload_temp_path(self, session_id: UUID) -> Path:
        """
        Get temporary storage path for a session.

        Args:
            session_id: UUID of the session

        Returns:
            Path to temporary directory
        """
        return Path(tempfile.gettempdir()) / f"credit-card-session-{session_id}"

    async def cleanup_temp_files(self, session_id: UUID) -> None:
        """
        Clean up temporary files for a session.

        Args:
            session_id: UUID of the session

        Note:
            This should be called after extraction is complete.
        """
        temp_dir = await self.get_upload_temp_path(session_id)

        if temp_dir.exists():
            # Remove all files in directory
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()

            # Remove directory
            temp_dir.rmdir()


async def process_session_background(
    session_id: UUID,
    extraction_service: "ExtractionService",
    matching_service: Optional["MatchingService"] = None
) -> None:
    """
    Background task to process uploaded files through extraction and matching.

    This function orchestrates the entire processing workflow:
    1. Get temp directory path
    2. Run extraction with progress tracking
    3. Run matching (if service provided)
    4. Clean up temp files
    5. Mark session as completed

    Args:
        session_id: UUID of the session to process
        extraction_service: ExtractionService instance
        matching_service: Optional MatchingService instance

    Note:
        This function is designed to be run as a FastAPI BackgroundTask.
        Errors are caught and logged, with session status updated to 'failed'.
    """
    temp_dir = Path(tempfile.gettempdir()) / f"credit-card-session-{session_id}"

    try:
        logger.info(f"Starting background processing for session {session_id}")

        # Initialize progress tracker in extraction service
        await extraction_service.initialize_progress_tracker(session_id)

        # Phase 1: Extraction with progress tracking
        logger.info(f"Starting extraction phase for session {session_id}")
        await extraction_service.process_session_files_with_progress(
            session_id, temp_dir
        )

        # Phase 2: Matching (if matching service provided)
        if matching_service:
            logger.info(f"Starting matching phase for session {session_id}")
            # TODO: Implement matching with progress tracking
            # For now, matching service doesn't have progress tracking integrated
            # This will be added in future iterations
            pass

        # Mark session as completed
        await extraction_service.session_repo.update_session_status(
            session_id, "completed"
        )

        # Update final progress state
        if extraction_service.progress_tracker:
            await extraction_service.progress_tracker.update_progress(
                current_phase="completed",
                phase_details={
                    "status": "completed",
                    "percentage": 100
                },
                force_update=True
            )
            await extraction_service.progress_tracker.flush_pending()

        logger.info(f"Processing completed successfully for session {session_id}")

    except Exception as e:
        logger.error(
            f"Background processing failed for session {session_id}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )

        # Mark session as failed
        try:
            await extraction_service.session_repo.update_session_status(
                session_id, "failed"
            )

            # Update progress with error
            if extraction_service.progress_tracker:
                from ..schemas.phase_progress import ErrorContext
                error_context = ErrorContext(
                    type=type(e).__name__,
                    message=str(e),
                    context={"session_id": str(session_id)},
                    timestamp=datetime.utcnow()
                )
                await extraction_service.progress_tracker.update_progress(
                    current_phase="processing",
                    phase_details={
                        "status": "failed",
                        "error": error_context
                    },
                    force_update=True
                )
                await extraction_service.progress_tracker.flush_pending()
        except Exception as cleanup_error:
            logger.error(
                f"Failed to update session status after error: {cleanup_error}",
                exc_info=True
            )

    finally:
        # Always clean up temp files
        try:
            if temp_dir.exists():
                for file_path in temp_dir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                temp_dir.rmdir()
                logger.info(f"Cleaned up temp files for session {session_id}")
        except Exception as cleanup_error:
            logger.error(
                f"Failed to cleanup temp files for session {session_id}: {cleanup_error}",
                exc_info=True
            )
