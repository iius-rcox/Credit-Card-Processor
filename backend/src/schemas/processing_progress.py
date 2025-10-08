"""
ProcessingProgress Pydantic schema for better status updates.

This module defines the top-level progress tracking schema that is stored
in the Session model's processing_progress JSONB field.
"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field

from .phase_progress import PhaseProgress, ErrorContext


class ProcessingProgress(BaseModel):
    """
    Complete progress state snapshot for a processing session.

    This is stored as JSONB in the sessions.processing_progress column.
    """

    overall_percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Aggregate progress across all phases (0-100)"
    )

    current_phase: str = Field(
        description="Currently active phase name"
    )

    phases: Dict[str, PhaseProgress] = Field(
        description="Progress details for each processing phase"
    )

    last_update: datetime = Field(
        description="Timestamp of last progress update"
    )

    status_message: str = Field(
        description="Human-readable status (e.g., 'Processing File 2 of 3: Page 5/12')"
    )

    error: Optional[ErrorContext] = Field(
        default=None,
        description="Error details if processing failed"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "overall_percentage": 45,
                "current_phase": "processing",
                "phases": {
                    "upload": {
                        "status": "completed",
                        "percentage": 100,
                        "completed_at": "2025-10-08T14:23:15Z"
                    },
                    "processing": {
                        "status": "in_progress",
                        "percentage": 35,
                        "total_files": 3,
                        "current_file_index": 1,
                        "current_file": {
                            "name": "statement_002.pdf",
                            "total_pages": 12,
                            "current_page": 5,
                            "regex_matches_found": 23
                        }
                    },
                    "matching": {
                        "status": "pending",
                        "percentage": 0
                    },
                    "report_generation": {
                        "status": "pending",
                        "percentage": 0
                    }
                },
                "last_update": "2025-10-08T14:25:42Z",
                "status_message": "Processing File 2 of 3: Page 5/12"
            }
        }

    def model_post_init(self, __context) -> None:
        """Validate that current_phase exists in phases dict."""
        if self.current_phase and self.current_phase not in self.phases:
            # If current_phase is not in phases, add it as pending
            from .phase_progress import PhaseProgress
            self.phases[self.current_phase] = PhaseProgress(
                status="pending",
                percentage=0
            )