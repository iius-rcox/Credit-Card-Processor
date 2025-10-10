"""
Test script to simulate progress updates for the Credit Card Processor.

This script simulates the progress tracking system without requiring
a database connection or actual file processing.
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

# Add the backend src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.schemas.phase_progress import FileProgress, PhaseProgress
from src.schemas.processing_progress import ProcessingProgress
from src.services.progress_tracker import ProgressTracker


class SimulatedProgressCallback:
    """Simulates the callback that would normally persist to database."""

    def __init__(self, verbose: bool = True):
        self.updates = []
        self.verbose = verbose

    async def __call__(self, session_id: UUID, progress: ProcessingProgress):
        """Store and display progress update."""
        self.updates.append({
            "timestamp": datetime.utcnow(),
            "progress": progress
        })

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Progress Update #{len(self.updates)}")
            print(f"{'='*60}")
            print(f"Session: {session_id}")
            print(f"Overall: {progress.overall_percentage}%")
            print(f"Phase: {progress.current_phase}")
            print(f"Status: {progress.status_message}")

            if progress.phases:
                print("\nPhase Details:")
                for phase_name, phase_data in progress.phases.items():
                    print(f"  {phase_name:20s}: {phase_data.status:12s} - {phase_data.percentage:3d}%")

                    # Show current file details if processing
                    if phase_name == "processing" and phase_data.current_file:
                        file_info = phase_data.current_file
                        print(f"    Current File: {file_info.name}")
                        print(f"    Page: {file_info.current_page}/{file_info.total_pages}")
                        print(f"    Regex Matches: {file_info.regex_matches_found}")

            print(f"Last Update: {progress.last_update.isoformat()}")


async def simulate_upload_phase(tracker: ProgressTracker, total_files: int = 3):
    """Simulate the upload phase."""
    print("\n>>> Starting Upload Phase...")

    for i in range(1, total_files + 1):
        # Simulate file upload progress
        bytes_uploaded = i * 1024 * 1024 * random.randint(5, 20)  # Random file size
        phase_details = {
            "status": "in_progress",
            "percentage": int((i / total_files) * 100),
            "files_uploaded": i,
            "bytes_uploaded": bytes_uploaded,
            "started_at": datetime.utcnow()
        }

        await tracker.update_progress("upload", phase_details)
        await asyncio.sleep(0.8)  # Simulate upload time

    # Complete upload phase
    await tracker.update_progress("upload", {
        "status": "completed",
        "percentage": 100,
        "files_uploaded": total_files,
        "bytes_uploaded": total_files * 15 * 1024 * 1024
    }, force_update=True)


async def simulate_processing_phase(tracker: ProgressTracker, total_files: int = 3):
    """Simulate the processing phase with detailed page-by-page updates."""
    print("\n>>> Starting Processing Phase...")

    files = [
        {"name": "statement_jan_2025.pdf", "pages": 12},
        {"name": "statement_feb_2025.pdf", "pages": 8},
        {"name": "statement_mar_2025.pdf", "pages": 15}
    ]

    for file_idx, file_info in enumerate(files[:total_files], 1):
        file_name = file_info["name"]
        total_pages = file_info["pages"]

        print(f"\n  Processing file {file_idx}: {file_name} ({total_pages} pages)")

        for page in range(1, total_pages + 1):
            # Calculate phase percentage
            files_done = file_idx - 1
            current_file_progress = page / total_pages
            phase_percentage = int(((files_done + current_file_progress) / total_files) * 100)

            # Simulate finding regex matches
            matches_found = random.randint(0, 5) if random.random() > 0.7 else 0

            phase_details = {
                "status": "in_progress",
                "percentage": phase_percentage,
                "total_files": total_files,
                "current_file_index": file_idx,
                "current_file": {
                    "name": file_name,
                    "total_pages": total_pages,
                    "current_page": page,
                    "regex_matches_found": matches_found,
                    "started_at": datetime.utcnow()
                },
                "started_at": datetime.utcnow()
            }

            # Force update on first and last page (boundary updates)
            force = page == 1 or page == total_pages
            await tracker.update_progress("processing", phase_details, force_update=force)

            # Simulate page processing time
            await asyncio.sleep(0.3)

        print(f"    [DONE] Completed {file_name}")

    # Complete processing phase
    await tracker.update_progress("processing", {
        "status": "completed",
        "percentage": 100,
        "total_files": total_files,
        "current_file_index": total_files
    }, force_update=True)


async def simulate_matching_phase(tracker: ProgressTracker):
    """Simulate the matching phase."""
    print("\n>>> Starting Matching Phase...")

    total_transactions = 150

    for i in range(0, 101, 20):  # Progress in chunks
        matches = int(total_transactions * (i / 100) * 0.8)  # 80% match rate
        unmatched = int(total_transactions * (i / 100) * 0.2)  # 20% unmatched

        phase_details = {
            "status": "in_progress",
            "percentage": i,
            "matches_found": matches,
            "unmatched_count": unmatched,
            "started_at": datetime.utcnow()
        }

        await tracker.update_progress("matching", phase_details)
        await asyncio.sleep(0.5)

    # Complete matching
    await tracker.update_progress("matching", {
        "status": "completed",
        "percentage": 100,
        "matches_found": 120,
        "unmatched_count": 30
    }, force_update=True)


async def simulate_report_generation(tracker: ProgressTracker):
    """Simulate the report generation phase."""
    print("\n>>> Starting Report Generation...")

    total_records = 150

    for records_written in [0, 50, 100, 150]:
        percentage = int((records_written / total_records) * 100)

        phase_details = {
            "status": "in_progress",
            "percentage": percentage,
            "report_type": "xlsx",
            "records_written": records_written,
            "started_at": datetime.utcnow()
        }

        await tracker.update_progress("report_generation", phase_details)
        await asyncio.sleep(0.4)

    # Complete report generation
    await tracker.update_progress("report_generation", {
        "status": "completed",
        "percentage": 100,
        "report_type": "xlsx",
        "records_written": total_records
    }, force_update=True)


async def run_full_simulation():
    """Run a complete processing simulation."""
    print("\n" + "="*60)
    print("Credit Card Processor - Progress Tracking Simulation")
    print("="*60)

    # Create session ID
    session_id = uuid4()
    print(f"\nSession ID: {session_id}")

    # Create callback
    callback = SimulatedProgressCallback(verbose=True)

    # Create tracker
    tracker = ProgressTracker(session_id, callback)

    # Run through all phases
    start_time = time.time()

    await simulate_upload_phase(tracker, total_files=3)
    await simulate_processing_phase(tracker, total_files=3)
    await simulate_matching_phase(tracker)
    await simulate_report_generation(tracker)

    # Flush any pending updates
    await tracker.flush_pending()

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "="*60)
    print("Simulation Complete!")
    print("="*60)
    print(f"Total Time: {elapsed:.2f} seconds")
    print(f"Total Updates: {len(callback.updates)}")
    print(f"Average Update Interval: {elapsed/len(callback.updates):.2f} seconds")

    # Show update timing analysis
    print("\nUpdate Timing Analysis:")
    if len(callback.updates) > 1:
        intervals = []
        for i in range(1, len(callback.updates)):
            prev = callback.updates[i-1]["timestamp"]
            curr = callback.updates[i]["timestamp"]
            interval = (curr - prev).total_seconds()
            intervals.append(interval)

        print(f"  Min Interval: {min(intervals):.2f}s")
        print(f"  Max Interval: {max(intervals):.2f}s")
        print(f"  Avg Interval: {sum(intervals)/len(intervals):.2f}s")
        print(f"  Target Batch Interval: {tracker.BATCH_INTERVAL}s")

    return callback.updates


async def test_boundary_updates():
    """Test that boundary updates are forced immediately."""
    print("\n" + "="*60)
    print("Testing Boundary Updates")
    print("="*60)

    session_id = uuid4()
    callback = SimulatedProgressCallback(verbose=False)
    tracker = ProgressTracker(session_id, callback)

    # Test first page (should force update)
    await tracker.update_progress("processing", {
        "status": "in_progress",
        "percentage": 10,
        "current_file": {
            "name": "test.pdf",
            "total_pages": 10,
            "current_page": 1,  # First page - boundary
            "regex_matches_found": 0
        }
    })

    print(f"After first page: {len(callback.updates)} updates (expected: 1)")

    # Test middle pages (should batch)
    for page in range(2, 9):
        await tracker.update_progress("processing", {
            "status": "in_progress",
            "percentage": page * 10,
            "current_file": {
                "name": "test.pdf",
                "total_pages": 10,
                "current_page": page,
                "regex_matches_found": 0
            }
        })
        await asyncio.sleep(0.1)  # Small delay

    print(f"After middle pages: {len(callback.updates)} updates (should be batched)")

    # Test last page (should force update)
    await tracker.update_progress("processing", {
        "status": "in_progress",
        "percentage": 90,
        "current_file": {
            "name": "test.pdf",
            "total_pages": 10,
            "current_page": 10,  # Last page - boundary
            "regex_matches_found": 0
        }
    })

    print(f"After last page: {len(callback.updates)} updates")

    # Test phase completion (should force update)
    await tracker.update_progress("processing", {
        "status": "completed",
        "percentage": 100
    })

    print(f"After completion: {len(callback.updates)} updates")
    print("[DONE] Boundary update test complete")


async def main():
    """Main function to run all simulations."""
    # Run the full simulation
    await run_full_simulation()

    # Test boundary updates
    await test_boundary_updates()

    print("\n[SUCCESS] All simulations complete!")


if __name__ == "__main__":
    # Run the simulation
    asyncio.run(main())