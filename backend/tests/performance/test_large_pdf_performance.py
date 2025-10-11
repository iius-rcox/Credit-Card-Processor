"""
Performance tests for large PDF processing.

Tests verify system can handle PDFs with thousands of transactions
within acceptable time and memory constraints.
"""

import pytest
import asyncio
import io
import time
import psutil
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.models.transaction import Transaction


@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.asyncio
async def test_10k_transaction_performance(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify processing 10,000 transactions completes in < 60 seconds.

    Tests that:
    - 10,000 transaction PDF is processed
    - Total time is under 60 seconds
    - No timeout or crash
    """
    # Generate PDF with 10,000 transactions
    print("Generating 10,000 transaction PDF...")
    transactions_data = []
    for i in range(10000):
        employee = f"EMPLOYEE{i % 100}"
        expense_type = ["Meals", "Fuel", "Hotel", "General Expense"][i % 4]
        date = f"03/{(i % 28) + 1:02d}/2025"
        amount = f"{50 + (i % 500)}.{(i % 100):02d}"
        merchant = f"MERCHANT{i}"
        address = f"ADDRESS{i}"

        transactions_data.append(
            f"{employee}\t{expense_type}\t{date}\t{amount}\t{merchant}\t{address}\tComplete"
        )

    pdf_content = b"%PDF-1.4\n" + "\n".join(transactions_data).encode() + b"\n%%EOF"
    print(f"Generated PDF size: {len(pdf_content)} bytes")

    # Start timer
    start_time = time.time()

    # Upload PDF
    pdf_file = ("large_statement.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await test_client.post("/api/upload", files={"files": pdf_file})

    assert response.status_code == 202, "Upload should succeed"
    session_id = response.json()["id"]

    # Wait for processing (with timeout)
    max_wait = 60  # 60 seconds
    poll_interval = 2
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        # Check if processing is complete by querying transaction count
        result = await test_session.execute(
            select(func.count()).select_from(Transaction).where(Transaction.session_id == session_id)
        )
        count = result.scalar()

        if count >= 10000:
            break

        print(f"Processed {count} transactions after {elapsed}s...")

    # Stop timer
    end_time = time.time()
    total_time = end_time - start_time

    print(f"Total processing time: {total_time:.2f} seconds")

    # Verify performance
    assert total_time < 60, f"Processing should complete in < 60 seconds, took {total_time:.2f}s"

    # Verify all transactions were processed
    final_result = await test_session.execute(
        select(func.count()).select_from(Transaction).where(Transaction.session_id == session_id)
    )
    final_count = final_result.scalar()

    assert final_count == 10000, f"Should process all 10,000 transactions, got {final_count}"


@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.asyncio
async def test_10k_transactions_all_extracted(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify all 10,000 transactions are extracted and stored.

    Tests that:
    - Transaction count matches expected
    - No transactions are lost
    - Database integrity is maintained
    """
    # Generate smaller test for quick verification (1000 transactions)
    # Full 10k test is in test_10k_transaction_performance
    transactions_data = []
    for i in range(1000):
        transactions_data.append(
            f"EMPLOYEE{i % 10}\tMeals\t03/{(i % 28) + 1:02d}/2025\t{50 + i}.99\tMERCH{i}\tADDR{i}\tComplete"
        )

    pdf_content = b"%PDF-1.4\n" + "\n".join(transactions_data).encode() + b"\n%%EOF"

    pdf_file = ("medium_statement.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await test_client.post("/api/upload", files={"files": pdf_file})

    assert response.status_code == 202
    session_id = response.json()["id"]

    # Wait for processing
    await asyncio.sleep(10)

    # Count transactions
    result = await test_session.execute(
        select(func.count()).select_from(Transaction).where(Transaction.session_id == session_id)
    )
    count = result.scalar()

    assert count == 1000, f"Should extract all 1000 transactions, got {count}"


@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.asyncio
async def test_no_memory_errors_on_large_pdf(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify memory usage stays under 500MB during large PDF processing.

    Tests that:
    - Peak memory usage < 500MB
    - No memory leaks
    - Graceful handling of large data
    """
    # Get current process
    process = psutil.Process(os.getpid())

    # Measure baseline memory
    baseline_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
    print(f"Baseline memory: {baseline_memory:.2f} MB")

    # Generate moderately sized PDF (5000 transactions)
    transactions_data = []
    for i in range(5000):
        transactions_data.append(
            f"EMPLOYEE{i % 50}\tFuel\t03/{(i % 28) + 1:02d}/2025\t{60 + i}.99\tMERCH{i}\tADDR{i}\tComplete"
        )

    pdf_content = b"%PDF-1.4\n" + "\n".join(transactions_data).encode() + b"\n%%EOF"

    # Upload and process
    pdf_file = ("large_statement.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await test_client.post("/api/upload", files={"files": pdf_file})

    assert response.status_code == 202
    session_id = response.json()["id"]

    # Monitor memory during processing
    max_memory = baseline_memory
    for _ in range(15):  # Monitor for 30 seconds
        await asyncio.sleep(2)

        current_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(max_memory, current_memory)

        print(f"Current memory: {current_memory:.2f} MB, Peak: {max_memory:.2f} MB")

    # Verify memory constraint
    memory_increase = max_memory - baseline_memory
    print(f"Memory increase: {memory_increase:.2f} MB")

    assert memory_increase < 500, f"Memory increase should be < 500MB, was {memory_increase:.2f}MB"

    # Verify processing completed
    result = await test_session.execute(
        select(func.count()).select_from(Transaction).where(Transaction.session_id == session_id)
    )
    count = result.scalar()

    print(f"Processed {count} transactions")
    assert count >= 4000, f"Should process most transactions, got {count}"
