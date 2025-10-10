"""
Performance tests for progress update latency.

Tests that progress updates complete within acceptable time limits (<50ms).
"""

import asyncio
import time
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.services.progress_tracker import ProgressTracker
from src.services.progress_calculator import ProgressCalculator
from src.repositories.progress_repository import ProgressRepository
from src.schemas.processing_progress import ProcessingProgress
from src.schemas.phase_progress import PhaseProgress


class TestProgressLatency:
    """Performance tests for progress update operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_id = uuid4()
        self.calculator = ProgressCalculator()

    @pytest.mark.asyncio
    async def test_progress_tracker_update_latency(self):
        """Test that progress tracker updates complete within 50ms."""
        update_times = []

        async def mock_callback(session_id, progress):
            """Mock callback that measures time."""
            await asyncio.sleep(0.001)  # Simulate minimal DB write time

        tracker = ProgressTracker(self.session_id, mock_callback)

        # Test multiple updates
        for i in range(100):
            phase_details = {
                "percentage": i,
                "total_files": 10,
                "current_file_index": (i // 10) + 1,
                "current_file": {
                    "name": f"file_{i}.pdf",
                    "current_page": (i % 10) + 1,
                    "total_pages": 10,
                    "regex_matches_found": i * 5,
                    "started_at": datetime.utcnow()
                }
            }

            start_time = time.perf_counter()
            await tracker.update_progress("processing", phase_details, force_update=True)
            end_time = time.perf_counter()

            update_times.append((end_time - start_time) * 1000)  # Convert to ms

        # Check latency requirements
        avg_latency = sum(update_times) / len(update_times)
        max_latency = max(update_times)
        p95_latency = sorted(update_times)[int(len(update_times) * 0.95)]

        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")
        print(f"95th percentile: {p95_latency:.2f}ms")

        assert avg_latency < 50, f"Average latency {avg_latency:.2f}ms exceeds 50ms"
        assert p95_latency < 50, f"95th percentile latency {p95_latency:.2f}ms exceeds 50ms"

    def test_progress_calculator_latency(self):
        """Test that progress calculations complete quickly."""
        calculation_times = []

        # Test file progress calculations
        for i in range(1000):
            start_time = time.perf_counter()
            result = self.calculator.calculate_file_progress(i % 100 + 1, 100)
            end_time = time.perf_counter()
            calculation_times.append((end_time - start_time) * 1000)

        avg_time = sum(calculation_times) / len(calculation_times)
        assert avg_time < 1, f"File progress calculation avg {avg_time:.2f}ms exceeds 1ms"

        # Test multi-file progress calculations
        calculation_times.clear()
        for i in range(1000):
            start_time = time.perf_counter()
            result = self.calculator.calculate_multi_file_progress(
                (i % 10) + 1, 10, (i % 100) + 1, 100
            )
            end_time = time.perf_counter()
            calculation_times.append((end_time - start_time) * 1000)

        avg_time = sum(calculation_times) / len(calculation_times)
        assert avg_time < 1, f"Multi-file calculation avg {avg_time:.2f}ms exceeds 1ms"

    def test_weighted_calculation_latency(self):
        """Test that weighted calculations scale well."""
        # Create varying sizes of file lists
        test_sizes = [10, 50, 100, 500, 1000]

        for size in test_sizes:
            files = [
                {
                    "total_pages": (i + 1) * 10,
                    "current_page": (i + 1) * 5,
                    "completed": i % 3 == 0
                }
                for i in range(size)
            ]

            start_time = time.perf_counter()
            result = self.calculator.calculate_weighted_multi_file_progress(files)
            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            print(f"Weighted calc for {size} files: {latency_ms:.2f}ms")

            # Even with 1000 files, should be under 10ms
            assert latency_ms < 10, f"Weighted calc for {size} files took {latency_ms:.2f}ms"

    @pytest.mark.asyncio
    async def test_progress_snapshot_creation_latency(self):
        """Test that creating progress snapshots is fast."""
        tracker = ProgressTracker(self.session_id)

        snapshot_times = []

        for i in range(100):
            phase_details = {
                "status": "in_progress",
                "percentage": i,
                "total_files": 10,
                "current_file_index": (i // 10) + 1,
                "current_file": {
                    "name": f"file_{i}.pdf",
                    "current_page": (i % 10) + 1,
                    "total_pages": 10,
                    "regex_matches_found": i * 5,
                    "started_at": datetime.utcnow()
                }
            }

            start_time = time.perf_counter()
            snapshot = tracker._create_progress_snapshot("processing", phase_details)
            end_time = time.perf_counter()

            snapshot_times.append((end_time - start_time) * 1000)

        avg_time = sum(snapshot_times) / len(snapshot_times)
        max_time = max(snapshot_times)

        print(f"Snapshot creation avg: {avg_time:.2f}ms, max: {max_time:.2f}ms")

        assert avg_time < 5, f"Snapshot creation avg {avg_time:.2f}ms exceeds 5ms"
        assert max_time < 10, f"Snapshot creation max {max_time:.2f}ms exceeds 10ms"

    @pytest.mark.asyncio
    async def test_batching_reduces_load(self):
        """Test that batching effectively reduces update frequency."""
        update_count = 0

        async def counting_callback(session_id, progress):
            nonlocal update_count
            update_count += 1
            await asyncio.sleep(0.001)

        tracker = ProgressTracker(self.session_id, counting_callback)

        # Simulate rapid updates (like processing pages quickly)
        start_time = time.perf_counter()

        for i in range(100):
            await tracker.update_progress(
                "processing",
                {"percentage": i},
                force_update=False  # Allow batching
            )
            await asyncio.sleep(0.01)  # Simulate 10ms per page processing

        # Flush any pending
        await tracker.flush_pending()

        end_time = time.perf_counter()
        total_time = end_time - start_time

        print(f"100 progress updates resulted in {update_count} actual updates")
        print(f"Total time: {total_time:.2f}s")

        # With 2.5s batching interval, 100 updates over ~1s should result in far fewer actual updates
        assert update_count < 10, f"Too many updates ({update_count}) despite batching"

    @pytest.mark.asyncio
    async def test_concurrent_progress_updates(self):
        """Test that concurrent progress updates don't cause performance degradation."""
        trackers = []
        callbacks_executed = []

        async def mock_callback(session_id, progress):
            callbacks_executed.append(time.perf_counter())
            await asyncio.sleep(0.005)  # Simulate DB write

        # Create multiple trackers for different sessions
        for _ in range(10):
            tracker = ProgressTracker(uuid4(), mock_callback)
            trackers.append(tracker)

        # Run concurrent updates
        start_time = time.perf_counter()

        async def update_tracker(tracker, index):
            for i in range(10):
                await tracker.update_progress(
                    "processing",
                    {"percentage": i * 10},
                    force_update=True
                )
                await asyncio.sleep(0.001)

        tasks = [
            update_tracker(tracker, idx)
            for idx, tracker in enumerate(trackers)
        ]

        await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000

        print(f"Concurrent updates total time: {total_time:.2f}ms")
        print(f"Total callbacks executed: {len(callbacks_executed)}")

        # Even with 10 concurrent sessions, should complete reasonably fast
        assert total_time < 500, f"Concurrent updates took {total_time:.2f}ms"

    def test_phase_calculation_scales(self):
        """Test that phase calculations scale with number of phases."""
        # Test with varying number of phases
        for num_phases in [4, 10, 20, 50]:
            phases = {
                f"phase_{i}": {"percentage": (i * 100) // num_phases}
                for i in range(num_phases)
            }
            weights = {
                f"phase_{i}": 1.0 / num_phases
                for i in range(num_phases)
            }

            start_time = time.perf_counter()
            for _ in range(100):
                result = self.calculator.calculate_phase_weighted_overall(phases, weights)
            end_time = time.perf_counter()

            avg_time_ms = ((end_time - start_time) / 100) * 1000
            print(f"Phase calc with {num_phases} phases: {avg_time_ms:.3f}ms avg")

            assert avg_time_ms < 1, f"Phase calc with {num_phases} phases took {avg_time_ms:.3f}ms"

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test that progress tracking doesn't leak memory with many updates."""
        import sys

        tracker = ProgressTracker(self.session_id)

        # Baseline memory
        initial_size = sys.getsizeof(tracker.pending_progress) if tracker.pending_progress else 0

        # Perform many updates
        for i in range(1000):
            phase_details = {
                "percentage": i % 100,
                "current_file": {
                    "name": f"file_{i}.pdf",
                    "current_page": i,
                    "total_pages": 1000,
                    "regex_matches_found": i * 10,
                    "started_at": datetime.utcnow()
                }
            }
            await tracker.update_progress("processing", phase_details)

        # Check memory after updates
        if tracker.pending_progress:
            final_size = sys.getsizeof(tracker.pending_progress)
            # Progress object size shouldn't grow significantly
            assert final_size < initial_size + 10000, "Potential memory leak detected"