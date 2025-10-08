"""
Unit tests for ProgressTracker service.

Tests time-based batching logic, boundary detection, and progress update
mechanisms.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.progress_tracker import ProgressTracker
from src.schemas.processing_progress import ProcessingProgress
from src.schemas.phase_progress import PhaseProgress, ErrorContext


class TestProgressTracker:
    """Test suite for ProgressTracker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_id = uuid4()
        self.update_callback = AsyncMock()
        self.tracker = ProgressTracker(
            session_id=self.session_id,
            update_callback=self.update_callback
        )

    @pytest.mark.asyncio
    async def test_init(self):
        """Test tracker initialization."""
        assert self.tracker.session_id == self.session_id
        assert self.tracker.update_callback == self.update_callback
        assert self.tracker.last_update_time == 0.0
        assert self.tracker.pending_progress is None
        assert self.tracker.BATCH_INTERVAL == 2.5

    @pytest.mark.asyncio
    async def test_update_progress_first_update(self):
        """Test first progress update (should always emit)."""
        phase_details = {
            "status": "in_progress",
            "percentage": 10
        }

        await self.tracker.update_progress("processing", phase_details)

        # First update should always be emitted
        assert self.update_callback.called
        assert self.tracker.last_update_time > 0
        assert self.tracker.pending_progress is None

    @pytest.mark.asyncio
    async def test_update_progress_batching(self):
        """Test that updates are batched within interval."""
        # First update
        await self.tracker.update_progress("processing", {"percentage": 10})
        self.update_callback.reset_mock()

        # Immediate second update (should be batched)
        await self.tracker.update_progress("processing", {"percentage": 20})

        # Should not emit due to batching
        assert not self.update_callback.called
        assert self.tracker.pending_progress is not None
        assert self.tracker.pending_progress.overall_percentage == 12  # 20% * 0.6 weight

    @pytest.mark.asyncio
    async def test_update_progress_after_interval(self):
        """Test that updates emit after batch interval."""
        # First update
        await self.tracker.update_progress("processing", {"percentage": 10})
        first_time = self.tracker.last_update_time
        self.update_callback.reset_mock()

        # Mock time to simulate interval passing
        with patch('time.time', return_value=first_time + 3.0):
            await self.tracker.update_progress("processing", {"percentage": 50})

        # Should emit after interval
        assert self.update_callback.called
        assert self.tracker.last_update_time > first_time

    @pytest.mark.asyncio
    async def test_force_update(self):
        """Test forced update bypasses batching."""
        # First update
        await self.tracker.update_progress("processing", {"percentage": 10})
        self.update_callback.reset_mock()

        # Immediate forced update
        await self.tracker.update_progress(
            "processing",
            {"percentage": 20},
            force_update=True
        )

        # Should emit despite batching interval
        assert self.update_callback.called

    @pytest.mark.asyncio
    async def test_boundary_detection_first_page(self):
        """Test boundary detection for first page."""
        phase_details = {
            "current_file": {
                "name": "test.pdf",
                "current_page": 1,
                "total_pages": 100,
                "regex_matches_found": 0,
                "started_at": datetime.utcnow()
            }
        }

        # First update
        await self.tracker.update_progress("processing", phase_details)
        self.update_callback.reset_mock()

        # First page should force update even within batch interval
        await self.tracker.update_progress("processing", phase_details)
        assert self.update_callback.called

    @pytest.mark.asyncio
    async def test_boundary_detection_last_page(self):
        """Test boundary detection for last page."""
        phase_details = {
            "current_file": {
                "name": "test.pdf",
                "current_page": 100,
                "total_pages": 100,
                "regex_matches_found": 500,
                "started_at": datetime.utcnow()
            }
        }

        # First update
        await self.tracker.update_progress("processing", {"percentage": 50})
        self.update_callback.reset_mock()

        # Last page should force update
        await self.tracker.update_progress("processing", phase_details)
        assert self.update_callback.called

    @pytest.mark.asyncio
    async def test_boundary_detection_phase_complete(self):
        """Test boundary detection for phase completion."""
        # First update
        await self.tracker.update_progress("processing", {"percentage": 50})
        self.update_callback.reset_mock()

        # Phase completion should force update
        phase_details = {
            "status": "completed",
            "percentage": 100
        }
        await self.tracker.update_progress("processing", phase_details)
        assert self.update_callback.called

    @pytest.mark.asyncio
    async def test_boundary_detection_phase_failed(self):
        """Test boundary detection for phase failure."""
        # First update
        await self.tracker.update_progress("processing", {"percentage": 50})
        self.update_callback.reset_mock()

        # Phase failure should force update
        phase_details = {
            "status": "failed",
            "percentage": 50,
            "error": ErrorContext(
                type="TestError",
                message="Test failure",
                context={},
                timestamp=datetime.utcnow()
            )
        }
        await self.tracker.update_progress("processing", phase_details)
        assert self.update_callback.called

    @pytest.mark.asyncio
    async def test_phase_weights(self):
        """Test phase weight calculations."""
        # Upload phase (10% weight)
        await self.tracker.update_progress("upload", {"percentage": 100})
        progress = self.tracker.pending_progress or self.update_callback.call_args[0][1]
        assert progress.overall_percentage == 10

        # Processing phase (60% weight)
        self.update_callback.reset_mock()
        await self.tracker.update_progress("processing", {"percentage": 50}, force_update=True)
        progress = self.update_callback.call_args[0][1]
        assert progress.overall_percentage == 30  # 50% of 60%

        # Matching phase (20% weight)
        self.update_callback.reset_mock()
        await self.tracker.update_progress("matching", {"percentage": 100}, force_update=True)
        progress = self.update_callback.call_args[0][1]
        assert progress.overall_percentage == 20  # 100% of 20%

    @pytest.mark.asyncio
    async def test_status_message_generation(self):
        """Test status message generation for different phases."""
        # Upload phase
        await self.tracker.update_progress(
            "upload",
            {"files_uploaded": 3},
            force_update=True
        )
        progress = self.update_callback.call_args[0][1]
        assert "Uploading files: 3 uploaded" in progress.status_message

        # Processing phase with file details
        self.update_callback.reset_mock()
        await self.tracker.update_progress(
            "processing",
            {
                "total_files": 5,
                "current_file_index": 2,
                "current_file": {
                    "name": "test.pdf",
                    "current_page": 10,
                    "total_pages": 50,
                    "regex_matches_found": 25,
                    "started_at": datetime.utcnow()
                }
            },
            force_update=True
        )
        progress = self.update_callback.call_args[0][1]
        assert "Processing File 2 of 5: Page 10/50" in progress.status_message

        # Matching phase
        self.update_callback.reset_mock()
        await self.tracker.update_progress(
            "matching",
            {"matches_found": 42},
            force_update=True
        )
        progress = self.update_callback.call_args[0][1]
        assert "42 matches found" in progress.status_message

    @pytest.mark.asyncio
    async def test_flush_pending(self):
        """Test flushing pending updates."""
        # Create pending update
        await self.tracker.update_progress("processing", {"percentage": 50})
        self.update_callback.reset_mock()

        # Add another update that gets batched
        await self.tracker.update_progress("processing", {"percentage": 60})
        assert not self.update_callback.called
        assert self.tracker.pending_progress is not None

        # Flush pending
        await self.tracker.flush_pending()
        assert self.update_callback.called
        assert self.tracker.pending_progress is None

    @pytest.mark.asyncio
    async def test_flush_pending_no_pending(self):
        """Test flushing when no pending updates."""
        await self.tracker.flush_pending()
        assert not self.update_callback.called

    @pytest.mark.asyncio
    async def test_no_callback(self):
        """Test tracker works without callback."""
        tracker = ProgressTracker(self.session_id, update_callback=None)

        # Should not raise errors
        await tracker.update_progress("processing", {"percentage": 50})
        await tracker.flush_pending()

    @pytest.mark.asyncio
    async def test_phase_progression(self):
        """Test correct phase progression tracking."""
        # Simulate complete workflow
        phases_data = [
            ("upload", {"percentage": 100, "status": "completed"}),
            ("processing", {"percentage": 100, "status": "completed"}),
            ("matching", {"percentage": 100, "status": "completed"}),
            ("report_generation", {"percentage": 100, "status": "completed"})
        ]

        for phase, details in phases_data:
            await self.tracker.update_progress(phase, details, force_update=True)
            progress = self.update_callback.call_args[0][1]

            # Check phase is marked correctly
            assert progress.current_phase == phase
            assert progress.phases[phase].status == "completed"
            assert progress.phases[phase].percentage == 100

    @pytest.mark.asyncio
    async def test_error_in_phase(self):
        """Test error handling in phase progress."""
        error_context = {
            "type": "ProcessingError",
            "message": "Failed to process PDF",
            "context": {"file": "test.pdf", "page": 5},
            "timestamp": datetime.utcnow()
        }

        phase_details = {
            "status": "failed",
            "percentage": 45,
            "error": error_context
        }

        await self.tracker.update_progress("processing", phase_details, force_update=True)
        progress = self.update_callback.call_args[0][1]

        assert progress.error == error_context
        assert progress.phases["processing"].status == "failed"

    @pytest.mark.asyncio
    async def test_multi_file_progress(self):
        """Test progress tracking across multiple files."""
        files = ["file1.pdf", "file2.pdf", "file3.pdf"]

        for idx, filename in enumerate(files, 1):
            for page in range(1, 11):  # 10 pages each
                phase_details = {
                    "total_files": len(files),
                    "current_file_index": idx,
                    "current_file": {
                        "name": filename,
                        "current_page": page,
                        "total_pages": 10,
                        "regex_matches_found": page * 5,
                        "started_at": datetime.utcnow()
                    }
                }

                # Force update on boundaries
                force = (page == 1 or page == 10)
                await self.tracker.update_progress(
                    "processing",
                    phase_details,
                    force_update=force
                )

        # Check final state
        assert self.update_callback.call_count >= 6  # At least first and last page of each file