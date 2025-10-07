"""
UploadService - Handles file upload and validation.

This module manages the upload workflow including file validation,
storage, and session creation.
"""

import os
import tempfile
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import HTTPException, UploadFile

from ..models.session import Session
from ..repositories.session_repository import SessionRepository


class UploadService:
    """
    Service for handling file uploads and session creation.

    Validates uploaded files, creates sessions, and dispatches background
    processing tasks.
    """

    MAX_FILE_COUNT = 100
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_MIME_TYPES = ["application/pdf"]

    def __init__(self, session_repo: SessionRepository):
        """
        Initialize upload service.

        Args:
            session_repo: SessionRepository instance
        """
        self.session_repo = session_repo

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

        # Save files to temporary storage
        temp_dir = await self._save_files_to_temp(session.id, validated_files)

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
