"""
Integration tests for multi-file PDF processing with progress tracking

These tests verify end-to-end progress tracking across multiple PDF files
as described in specs/006-better-status-updates/quickstart.md

All tests are expected to FAIL until implementation is complete (TDD approach).
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import UUID
from typing import List
from pathlib import Path
import time


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_file_processing_tracks_progress_per_file(
    client: AsyncClient,
    sample_pdf_files: List[Path]
):
    """
    Integration Test: Multi-file processing with per-file progress tracking

    Given: 3 PDF files uploaded to a session
    When: Processing begins
    Then: Progress updates show current file, page counters, and aggregate percentage

    Validates: Quickstart Step 3 (Monitor Page-Level Progress)
    """
    # Step 1: Upload files
    files = {
        f"credit_card_{i}": open(pdf, "rb")
        for i, pdf in enumerate(sample_pdf_files)
    }

    upload_response = await client.post("/sessions/upload", files=files)
    assert upload_response.status_code == 200

    session_data = upload_response.json()
    session_id = session_data["session_id"]

    # Close file handles
    for file in files.values():
        file.close()

    # Step 2: Poll progress during processing
    progress_snapshots = []
    max_polls = 20
    poll_interval = 2.0  # seconds

    for _ in range(max_polls):
        await asyncio.sleep(poll_interval)

        progress_response = await client.get(f"/sessions/{session_id}/progress")
        assert progress_response.status_code == 200

        progress_data = progress_response.json()
        progress_snapshots.append(progress_data)

        # Check if processing completed
        if progress_data["current_phase"] == "completed":
            break

    # Step 3: Verify progress tracking characteristics
    assert len(progress_snapshots) > 0

    # Verify progress increases over time
    percentages = [snap["overall_percentage"] for snap in progress_snapshots]
    assert percentages[-1] >= percentages[0], "Progress should increase"

    # Verify file-level tracking
    processing_snapshots = [
        snap for snap in progress_snapshots
        if snap["current_phase"] == "processing"
    ]

    if processing_snapshots:
        for snapshot in processing_snapshots:
            phase_details = snapshot.get("phase_details", {})
            processing = phase_details.get("processing", {})

            # Should track total files
            assert "total_files" in processing
            assert processing["total_files"] == len(sample_pdf_files)

            # Should track current file
            if "current_file" in processing and processing["current_file"]:
                current_file = processing["current_file"]
                assert "name" in current_file
                assert "total_pages" in current_file
                assert "current_page" in current_file
                assert current_file["current_page"] <= current_file["total_pages"]

    # Verify final state
    final_snapshot = progress_snapshots[-1]
    assert final_snapshot["overall_percentage"] == 100
    assert final_snapshot["current_phase"] == "completed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_progress_updates_every_2_3_seconds(
    client: AsyncClient,
    sample_pdf_files: List[Path]
):
    """
    Integration Test: Progress updates occur at 2-3 second intervals

    Given: Files are being processed
    When: Polling progress endpoint
    Then: Updates occur approximately every 2-3 seconds (batching working)

    Validates: Quickstart Step 6 (Verify Update Frequency)
    """
    # Upload files
    files = {
        f"credit_card_{i}": open(pdf, "rb")
        for i, pdf in enumerate(sample_pdf_files)
    }

    upload_response = await client.post("/sessions/upload", files=files)
    session_id = upload_response.json()["session_id"]

    for file in files.values():
        file.close()

    # Track update timestamps
    update_times = []
    max_polls = 10

    for _ in range(max_polls):
        await asyncio.sleep(2.5)  # Poll every 2.5 seconds

        progress_response = await client.get(f"/sessions/{session_id}/progress")
        progress_data = progress_response.json()

        # Parse last_update timestamp
        last_update_str = progress_data["last_update"]
        update_times.append(last_update_str)

        if progress_data["current_phase"] == "completed":
            break

    # Verify updates changed (not stuck)
    unique_updates = set(update_times)
    assert len(unique_updates) > 1, "Progress should update over time"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_aggregate_progress_reflects_multi_file_completion(
    client: AsyncClient,
    sample_pdf_files: List[Path]
):
    """
    Integration Test: Aggregate percentage correctly reflects multi-file progress

    Given: 3 files with different page counts
    When: Processing files sequentially
    Then: Aggregate percentage reflects weighted progress

    Validates: Quickstart Step 4 (Verify Progress Advances Per File)
    """
    # Upload files
    files = {
        f"credit_card_{i}": open(pdf, "rb")
        for i, pdf in enumerate(sample_pdf_files)
    }

    upload_response = await client.post("/sessions/upload", files=files)
    session_id = upload_response.json()["session_id"]

    for file in files.values():
        file.close()

    # Track progress per file index
    file_transitions = []
    current_file_index = None

    max_polls = 30
    for _ in range(max_polls):
        await asyncio.sleep(2.0)

        progress_response = await client.get(f"/sessions/{session_id}/progress")
        progress_data = progress_response.json()

        if progress_data["current_phase"] == "processing":
            phase_details = progress_data.get("phase_details", {})
            processing = phase_details.get("processing", {})
            file_index = processing.get("current_file_index")

            # Detect file transition
            if file_index and file_index != current_file_index:
                file_transitions.append({
                    "file_index": file_index,
                    "overall_percentage": progress_data["overall_percentage"]
                })
                current_file_index = file_index

        if progress_data["current_phase"] == "completed":
            break

    # Verify progress increased with each file completion
    if len(file_transitions) >= 2:
        for i in range(1, len(file_transitions)):
            prev_pct = file_transitions[i-1]["overall_percentage"]
            curr_pct = file_transitions[i]["overall_percentage"]
            assert curr_pct > prev_pct, "Progress should increase with each file"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_progress_includes_descriptive_status_messages(
    client: AsyncClient,
    sample_pdf_files: List[Path]
):
    """
    Integration Test: Status messages are descriptive (not generic)

    Given: Files are being processed
    When: Polling progress
    Then: Status messages include file names and page counters

    Validates: FR-012, FR-018, FR-019 (descriptive messages)
    """
    # Upload files
    files = {
        f"credit_card_{i}": open(pdf, "rb")
        for i, pdf in enumerate(sample_pdf_files)
    }

    upload_response = await client.post("/sessions/upload", files=files)
    session_id = upload_response.json()["session_id"]

    for file in files.values():
        file.close()

    # Collect status messages
    status_messages = []

    max_polls = 15
    for _ in range(max_polls):
        await asyncio.sleep(2.0)

        progress_response = await client.get(f"/sessions/{session_id}/progress")
        progress_data = progress_response.json()

        status_message = progress_data["status_message"]
        status_messages.append(status_message)

        if progress_data["current_phase"] == "completed":
            break

    # Verify messages are not generic
    for message in status_messages:
        assert message.lower() not in [
            "processing",
            "processing...",
            "in progress"
        ], f"Status message too generic: {message}"

    # At least some messages should include numbers (page/file indicators)
    messages_with_numbers = [
        msg for msg in status_messages
        if any(char.isdigit() for char in msg)
    ]
    assert len(messages_with_numbers) > 0, "Status messages should include progress numbers"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_progress_handles_empty_pdf_gracefully(
    client: AsyncClient,
    empty_pdf_file: Path
):
    """
    Integration Test: Empty PDF (0 pages) handled gracefully

    Given: An empty PDF file
    When: Processing the file
    Then: Progress continues without error, file skipped with warning

    Validates: Error handling edge case from research.md
    """
    files = {"credit_card": open(empty_pdf_file, "rb")}

    upload_response = await client.post("/sessions/upload", files=files)
    session_id = upload_response.json()["session_id"]

    files["credit_card"].close()

    # Wait for processing
    await asyncio.sleep(3.0)

    progress_response = await client.get(f"/sessions/{session_id}/progress")
    progress_data = progress_response.json()

    # Should not crash, either skip or fail gracefully
    assert progress_response.status_code == 200
    assert progress_data["current_phase"] in ["processing", "completed", "failed"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_progress_tracks_regex_matches_found(
    client: AsyncClient,
    sample_pdf_with_transactions: Path
):
    """
    Integration Test: Progress tracks regex matches found during extraction

    Given: A PDF with credit card transactions
    When: Processing and extracting transactions
    Then: Progress shows regex_matches_found incrementing

    Validates: FR-007 (quantitative progress within phases)
    """
    files = {"credit_card": open(sample_pdf_with_transactions, "rb")}

    upload_response = await client.post("/sessions/upload", files=files)
    session_id = upload_response.json()["session_id"]

    files["credit_card"].close()

    # Track regex match counts
    match_counts = []

    max_polls = 15
    for _ in range(max_polls):
        await asyncio.sleep(2.0)

        progress_response = await client.get(f"/sessions/{session_id}/progress")
        progress_data = progress_response.json()

        if progress_data["current_phase"] == "processing":
            phase_details = progress_data.get("phase_details", {})
            processing = phase_details.get("processing", {})
            current_file = processing.get("current_file")

            if current_file:
                matches = current_file.get("regex_matches_found", 0)
                match_counts.append(matches)

        if progress_data["current_phase"] in ["completed", "failed"]:
            break

    # Verify match count increased
    if len(match_counts) > 1:
        # Should see matches accumulating
        final_count = match_counts[-1]
        initial_count = match_counts[0]
        assert final_count >= initial_count


# ============================================================================
# Test Fixtures (to be implemented in conftest.py)
# ============================================================================

"""
Required fixtures in backend/tests/conftest.py:

@pytest.fixture
def sample_pdf_files() -> List[Path]:
    # Return paths to 3 test PDF files with varying page counts
    pass

@pytest.fixture
def empty_pdf_file() -> Path:
    # Return path to empty/corrupted PDF
    pass

@pytest.fixture
def sample_pdf_with_transactions() -> Path:
    # Return path to PDF with credit card transactions
    pass
"""
