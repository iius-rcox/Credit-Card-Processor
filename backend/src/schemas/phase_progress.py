"""
Phase-level and file-level progress schemas for better status updates.

This module defines the nested schemas used within ProcessingProgress
to track individual phases, files, and errors.
"""

from datetime import datetime
from typing import Literal, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class FileProgress(BaseModel):
    """
    Tracks progress for a single PDF file during processing phase.
    """

    name: str = Field(
        description="Filename being processed"
    )

    file_id: Optional[UUID] = Field(
        default=None,
        description="Reference to uploaded file (if tracked separately)"
    )

    total_pages: int = Field(
        gt=0,
        description="Total page count from PDF metadata"
    )

    current_page: int = Field(
        ge=1,
        description="Currently processing page number"
    )

    regex_matches_found: int = Field(
        default=0,
        ge=0,
        description="Count of regex matches extracted so far"
    )

    started_at: datetime = Field(
        description="When file processing began"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="When file processing finished"
    )

    @property
    def percentage(self) -> float:
        """Calculate file-level progress percentage."""
        return (self.current_page / self.total_pages) * 100

    @validator('current_page')
    def validate_current_page(cls, v, values):
        """Ensure current_page doesn't exceed total_pages."""
        if 'total_pages' in values and v > values['total_pages']:
            raise ValueError(f"current_page ({v}) cannot exceed total_pages ({values['total_pages']})")
        return v

    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        """Ensure completed_at is after started_at."""
        if v and 'started_at' in values and v < values['started_at']:
            raise ValueError("completed_at must be after started_at")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None,
            UUID: lambda v: str(v)
        }


class ErrorContext(BaseModel):
    """
    Captures error details when processing fails.
    """

    type: str = Field(
        description="Error class name (e.g., 'ExtractionError', 'ValidationError')"
    )

    message: str = Field(
        description="Human-readable error message"
    )

    context: Dict[str, Any] = Field(
        description="Error location details (phase, file, page, etc.)"
    )

    timestamp: datetime = Field(
        description="When error occurred"
    )

    traceback: Optional[str] = Field(
        default=None,
        description="Stack trace for debugging (not shown to user)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "type": "RegexExtractionError",
                "message": "Invalid regex pattern in transaction extraction",
                "context": {
                    "phase": "processing",
                    "file": "statement_002.pdf",
                    "page": 5
                },
                "timestamp": "2025-10-08T14:27:00Z"
            }
        }


class PhaseProgress(BaseModel):
    """
    Progress details for a single processing phase.
    """

    status: Literal['pending', 'in_progress', 'completed', 'failed'] = Field(
        description="Current status of this phase"
    )

    percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress within this phase (0-100)"
    )

    started_at: Optional[datetime] = Field(
        default=None,
        description="When phase began"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="When phase finished"
    )

    # Phase-specific fields (flexible, varies by phase)
    # Upload phase fields
    files_uploaded: Optional[int] = Field(
        default=None,
        description="Number of files uploaded (upload phase)"
    )

    bytes_uploaded: Optional[int] = Field(
        default=None,
        description="Total bytes uploaded (upload phase)"
    )

    # Processing phase fields
    total_files: Optional[int] = Field(
        default=None,
        description="Total number of files to process (processing phase)"
    )

    current_file_index: Optional[int] = Field(
        default=None,
        description="Index of currently processing file (processing phase)"
    )

    current_file: Optional[FileProgress] = Field(
        default=None,
        description="Progress of current file (processing phase)"
    )

    # Matching phase fields
    matches_found: Optional[int] = Field(
        default=None,
        description="Number of matches found (matching phase)"
    )

    unmatched_count: Optional[int] = Field(
        default=None,
        description="Number of unmatched items (matching phase)"
    )

    # Report generation fields
    report_type: Optional[str] = Field(
        default=None,
        description="Type of report being generated (report phase)"
    )

    records_written: Optional[int] = Field(
        default=None,
        description="Number of records written to report (report phase)"
    )

    @validator('percentage')
    def validate_percentage_with_status(cls, v, values):
        """Ensure completed status has 100% progress."""
        if 'status' in values and values['status'] == 'completed' and v != 100:
            raise ValueError("Completed phase must have 100% progress")
        return v

    @validator('started_at')
    def validate_started_at_with_status(cls, v, values):
        """Ensure in_progress status has started_at."""
        if 'status' in values and values['status'] == 'in_progress' and not v:
            raise ValueError("In-progress phase must have started_at timestamp")
        return v

    @validator('completed_at')
    def validate_completed_at(cls, v, values):
        """Ensure completed_at is after started_at."""
        if v and 'started_at' in values and values['started_at'] and v < values['started_at']:
            raise ValueError("completed_at must be after started_at")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }