"""
Integration tests for incomplete transaction workflow.

Tests verify end-to-end handling of malformed or incomplete transactions,
ensuring graceful degradation and data preservation.
"""

import pytest
import asyncio
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.transaction import Transaction


@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_transaction_saved_as_incomplete(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify malformed transaction is saved with incomplete flag.

    Tests that:
    - Transaction with missing date is saved
    - incomplete_flag is set to True
    - transaction_date is NULL
    - Other fields are populated
    """
    # Create PDF with malformed transaction (missing date)
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tMeals\t\t45.99\tRESTAURANT\t123 MAIN ST\tIncomplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    # Query transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Malformed transaction should still be saved"

    tx = transactions[0]
    assert tx.incomplete_flag is True, "Should be marked as incomplete"
    assert tx.transaction_date is None, "Date should be NULL"
    assert tx.amount is not None, "Other fields should be populated"
    assert tx.merchant_name is not None, "Merchant should be extracted"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_incomplete_transactions_all_saved(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify multiple incomplete transactions are all saved.

    Tests that:
    - All 3 incomplete transactions are saved
    - Each has incomplete_flag = True
    - No transactions are skipped
    """
    # Create PDF with 3 incomplete transactions (various missing fields)
    pdf_content = b"""%PDF-1.4
JOHN\tMeals\t\t45.99\tREST1\t123 ST\tIncomplete
JANE\tFuel\t03/25/2025\t\tGAS1\t456 ST\tIncomplete
BOB\t\t03/26/2025\t55.00\tHOTEL1\t789 ST\tIncomplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    # Query all transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) >= 3, f"Should save all 3 incomplete transactions, got {len(transactions)}"

    # All should be marked incomplete
    incomplete_count = sum(1 for tx in transactions if tx.incomplete_flag)
    assert incomplete_count >= 3, f"All transactions should be incomplete, got {incomplete_count}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_and_incomplete_mixed(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify PDF with mix of complete and incomplete transactions.

    Tests that:
    - Complete transactions have incomplete_flag = False
    - Incomplete transactions have incomplete_flag = True
    - All transactions are saved
    - Correct count of each type
    """
    # Create PDF with mixed transactions
    pdf_content = b"""%PDF-1.4
JOHN\tMeals\t03/25/2025\t45.99\tREST1\t123 ST\tComplete
JANE\tFuel\t\t55.00\tGAS1\t456 ST\tIncomplete
BOB\tHotel\t03/26/2025\t75.00\tHOTEL1\t789 ST\tComplete
ALICE\tMeals\t03/27/2025\t\tREST2\t111 ST\tIncomplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    # Query all transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    all_transactions = result.scalars().all()

    assert len(all_transactions) >= 4, "Should save all 4 transactions"

    # Query complete transactions
    complete_result = await test_session.execute(
        select(Transaction).where(
            Transaction.session_id == session_id,
            Transaction.incomplete_flag == False
        )
    )
    complete_transactions = complete_result.scalars().all()

    # Query incomplete transactions
    incomplete_result = await test_session.execute(
        select(Transaction).where(
            Transaction.session_id == session_id,
            Transaction.incomplete_flag == True
        )
    )
    incomplete_transactions = incomplete_result.scalars().all()

    # Should have 2 complete and 2 incomplete
    assert len(complete_transactions) >= 2, f"Should have 2 complete transactions, got {len(complete_transactions)}"
    assert len(incomplete_transactions) >= 2, f"Should have 2 incomplete transactions, got {len(incomplete_transactions)}"

    # Verify complete transactions have all required fields
    for tx in complete_transactions:
        assert tx.transaction_date is not None, "Complete transactions should have date"
        assert tx.amount is not None, "Complete transactions should have amount"

    # Verify incomplete transactions have at least one NULL field
    for tx in incomplete_transactions:
        has_null_field = (
            tx.transaction_date is None or
            tx.amount is None or
            tx.employee_id is None or
            tx.merchant_name is None
        )
        assert has_null_field, "Incomplete transactions should have at least one NULL required field"
