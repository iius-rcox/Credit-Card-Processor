"""
ProgressTracker service for time-based batching of progress updates.

This module implements a tracker that batches progress updates to avoid
overwhelming the UI and database with too frequent updates.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from ..schemas.phase_progress import FileProgress, PhaseProgress
from ..schemas.processing_progress import ProcessingProgress


class ProgressTracker:
    """
    Tracks progress with time-based batching (2.5 second intervals).

    This class batches progress updates to reduce database writes and UI updates.
    Updates are emitted when:
    - 2.5 seconds have elapsed since last update
    - A phase boundary is reached (first or last page)
    - A phase completes
    """

    # Batch interval in seconds
    BATCH_INTERVAL = 2.5

    def __init__(
        self,
        session_id: UUID,
        update_callback: Optional[Callable[[UUID, ProcessingProgress], asyncio.Future]] = None
    ):
        """
        Initialize the progress tracker.

        Args:
            session_id: The session being tracked
            update_callback: Async function to persist progress updates
        """
        self.session_id = session_id
        self.update_callback = update_callback
        self.last_update_time = 0.0
        self.pending_progress: Optional[ProcessingProgress] = None
        self.phase_weights = {
            "upload": 0.1,        # 10% of overall
            "processing": 0.6,    # 60% of overall
            "matching": 0.2,      # 20% of overall
            "report_generation": 0.1  # 10% of overall
        }

    async def update_progress(
        self,
        current_phase: str,
        phase_details: Dict[str, Any],
        force_update: bool = False
    ) -> None:
        """
        Update progress with time-based batching.

        Args:
            current_phase: Name of the current phase
            phase_details: Phase-specific progress details
            force_update: Force immediate update regardless of batching
        """
        # Create or update the progress object
        progress = self._create_progress_snapshot(current_phase, phase_details)

        # Store as pending
        self.pending_progress = progress

        # Check if we should emit this update
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        should_update = (
            force_update or
            elapsed >= self.BATCH_INTERVAL or
            self._is_boundary_update(phase_details)
        )

        if should_update and self.update_callback:
            await self.update_callback(self.session_id, progress)
            self.last_update_time = current_time
            self.pending_progress = None

    def _create_progress_snapshot(
        self,
        current_phase: str,
        phase_details: Dict[str, Any]
    ) -> ProcessingProgress:
        """
        Create a complete progress snapshot.

        Args:
            current_phase: Name of the current phase
            phase_details: Phase-specific details

        Returns:
            Complete ProcessingProgress object
        """
        # Build phases dictionary
        phases = self._build_phases_dict(current_phase, phase_details)

        # Calculate overall percentage
        overall_percentage = self._calculate_overall_percentage(phases)

        # Generate status message
        status_message = self._generate_status_message(current_phase, phase_details)

        return ProcessingProgress(
            overall_percentage=overall_percentage,
            current_phase=current_phase,
            phases=phases,
            last_update=datetime.utcnow(),
            status_message=status_message,
            error=phase_details.get("error")
        )

    def _build_phases_dict(
        self,
        current_phase: str,
        phase_details: Dict[str, Any]
    ) -> Dict[str, PhaseProgress]:
        """
        Build the phases dictionary with progress for each phase.

        Args:
            current_phase: Currently active phase
            phase_details: Details for the current phase

        Returns:
            Dictionary of phase names to PhaseProgress objects
        """
        phases = {}

        # Define phase order
        phase_order = ["upload", "processing", "matching", "report_generation"]

        # Handle terminal states (completed/failed)
        if current_phase in ["completed", "failed"]:
            # Mark all phases as completed
            for phase in phase_order:
                phases[phase] = PhaseProgress(
                    status="completed",
                    percentage=100,
                    completed_at=datetime.utcnow()
                )
        else:
            # Normal phase progression
            for phase in phase_order:
                if phase == current_phase:
                    # Current phase - use provided details
                    phases[phase] = self._create_phase_progress(phase, phase_details)
                elif phase_order.index(phase) < phase_order.index(current_phase):
                    # Completed phase
                    phases[phase] = PhaseProgress(
                        status="completed",
                        percentage=100,
                        completed_at=datetime.utcnow()
                    )
                else:
                    # Pending phase
                    phases[phase] = PhaseProgress(
                        status="pending",
                        percentage=0
                    )

        return phases

    def _create_phase_progress(
        self,
        phase: str,
        details: Dict[str, Any]
    ) -> PhaseProgress:
        """
        Create a PhaseProgress object for a specific phase.

        Args:
            phase: Phase name
            details: Phase-specific details

        Returns:
            PhaseProgress object
        """
        # Base fields
        progress = PhaseProgress(
            status=details.get("status", "in_progress"),
            percentage=details.get("percentage", 0),
            started_at=details.get("started_at", datetime.utcnow())
        )

        # Add phase-specific fields
        if phase == "upload":
            progress.files_uploaded = details.get("files_uploaded")
            progress.bytes_uploaded = details.get("bytes_uploaded")
        elif phase == "processing":
            progress.total_files = details.get("total_files")
            progress.current_file_index = details.get("current_file_index")
            if "current_file" in details:
                file_info = details["current_file"]
                progress.current_file = FileProgress(
                    name=file_info["name"],
                    total_pages=file_info["total_pages"],
                    current_page=file_info["current_page"],
                    regex_matches_found=file_info.get("regex_matches_found", 0),
                    started_at=file_info.get("started_at", datetime.utcnow())
                )
        elif phase == "matching":
            progress.matches_found = details.get("matches_found")
            progress.unmatched_count = details.get("unmatched_count")
        elif phase == "report_generation":
            progress.report_type = details.get("report_type")
            progress.records_written = details.get("records_written")

        return progress

    def _calculate_overall_percentage(
        self,
        phases: Dict[str, PhaseProgress]
    ) -> int:
        """
        Calculate weighted overall progress across all phases.

        Args:
            phases: Dictionary of phase progress

        Returns:
            Overall percentage (0-100)
        """
        overall = 0.0
        for phase_name, phase_progress in phases.items():
            if phase_name in self.phase_weights:
                weight = self.phase_weights[phase_name]
                overall += weight * phase_progress.percentage

        return min(100, int(round(overall)))

    def _generate_status_message(
        self,
        current_phase: str,
        phase_details: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable status message.

        Args:
            current_phase: Currently active phase
            phase_details: Phase-specific details

        Returns:
            Status message string
        """
        if current_phase == "upload":
            files = phase_details.get("files_uploaded", 0)
            return f"Uploading files: {files} uploaded"

        elif current_phase == "processing":
            total_files = phase_details.get("total_files", 0)
            current_file_idx = phase_details.get("current_file_index", 0)
            if "current_file" in phase_details:
                file_info = phase_details["current_file"]
                current_page = file_info.get("current_page", 0)
                total_pages = file_info.get("total_pages", 0)
                return f"Processing File {current_file_idx} of {total_files}: Page {current_page}/{total_pages}"
            return f"Processing File {current_file_idx} of {total_files}"

        elif current_phase == "matching":
            matches = phase_details.get("matches_found", 0)
            return f"Matching transactions: {matches} matches found"

        elif current_phase == "report_generation":
            records = phase_details.get("records_written", 0)
            return f"Generating report: {records} records written"

        return f"Current phase: {current_phase}"

    def _is_boundary_update(self, phase_details: Dict[str, Any]) -> bool:
        """
        Check if this is a boundary update that should be forced.

        Boundary updates include:
        - First page of a file
        - Last page of a file
        - Phase completion

        Args:
            phase_details: Phase-specific details

        Returns:
            True if this is a boundary update
        """
        # Check for phase completion
        if phase_details.get("status") in ["completed", "failed"]:
            return True

        # Check for file boundaries in processing phase
        if "current_file" in phase_details:
            file_info = phase_details["current_file"]
            current_page = file_info.get("current_page", 0)
            total_pages = file_info.get("total_pages", 0)

            # First or last page
            if current_page == 1 or current_page == total_pages:
                return True

        return False

    async def flush_pending(self) -> None:
        """
        Force emit any pending progress update.

        This should be called when processing completes or fails
        to ensure the final state is persisted.
        """
        if self.pending_progress and self.update_callback:
            await self.update_callback(self.session_id, self.pending_progress)
            self.pending_progress = None
            self.last_update_time = time.time()