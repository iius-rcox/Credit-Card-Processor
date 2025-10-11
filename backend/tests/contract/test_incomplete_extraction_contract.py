"""
Contract tests for incomplete transaction handling.

Tests verify that extraction gracefully handles malformed or incomplete
transactions by setting the incomplete_flag and preserving partial data.
"""

import pytest
import asyncio
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.transaction import Transaction


@pytest.mark.contract
@pytest.mark.asyncio
async def test_incomplete_flag_set_when_date_missing(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify incomplete_flag is set when date field is missing.

    Tests that:
    - Transaction is still saved (not skipped)
    - incomplete_flag is set to True
    - Other fields are populated correctly
    - transaction_date is NULL
    """
    # Create test PDF with malformed transaction (missing date)
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tMeals\t\t45.99\tRESTAURANT\t123 MAIN ST\tIncomplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    # Query all transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should save transaction even with missing date"

    tx = transactions[0]
    assert tx.incomplete_flag is True, f"incomplete_flag should be True, got {tx.incomplete_flag}"
    assert tx.transaction_date is None, "transaction_date should be NULL when missing"
    assert tx.amount is not None, "Other fields should still be populated"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_incomplete_flag_set_when_amount_missing(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify incomplete_flag is set when amount field is missing.

    Tests that:
    - Transaction is still saved
    - incomplete_flag is set to True
    - amount is NULL
    """
    # Create test PDF with missing amount
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tFuel\t03/25/2025\t\tSHELL STATION\t456 ELM ST\tIncomplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should save transaction even with missing amount"

    tx = transactions[0]
    assert tx.incomplete_flag is True, "incomplete_flag should be True when amount is missing"
    assert tx.amount is None, "amount should be NULL when missing"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_incomplete_flag_set_when_employee_missing(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify incomplete_flag is set when employee name cannot be extracted.

    Tests that:
    - Transaction is still saved
    - incomplete_flag is set to True
    - employee_id is NULL (not resolved)
    """
    # Create test PDF with missing/unresolved employee name
    pdf_content = b"%PDF-1.4\t\tMeals\t03/25/2025\t35.00\tDINER\t789 OAK ST\tIncomplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should save transaction even with missing employee"

    tx = transactions[0]
    assert tx.incomplete_flag is True, "incomplete_flag should be True when employee is missing"
    assert tx.employee_id is None, "employee_id should be NULL when employee name not extracted"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_partial_data_saved(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify that partial data is saved with NULL values for missing fields.

    Tests that:
    - Transaction is not skipped entirely
    - Available fields are populated
    - Missing fields are NULL (not empty strings or default values)
    - incomplete_flag is True
    """
    # Create test PDF with partially complete transaction
    pdf_content = b"%PDF-1.4\nJOHNSMITH\t\t03/26/2025\t\tUNKNOWN MERCHANT\t\tPartial\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should save transaction with partial data"

    tx = transactions[0]
    assert tx.incomplete_flag is True, "incomplete_flag should be True for partial data"

    # Check that available data is saved
    assert tx.transaction_date is not None, "Available fields should be populated"
    assert tx.merchant_name is not None, "Merchant name should be populated"

    # Check that missing fields are NULL (not empty strings)
    assert tx.amount is None, "Missing amount should be NULL, not 0 or empty string"
    assert tx.expense_type is None or tx.expense_type == "", "Missing expense_type should be NULL or empty"
