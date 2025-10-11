"""
Contract tests for PDF extraction functionality.

Tests verify that the extraction service correctly extracts transaction
data from PDFs (not placeholder data) and populates all required fields.
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
async def test_upload_extracts_real_transactions(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify transactions have actual data from PDF, not placeholders.

    This test ensures that:
    - Extraction returns real data from the PDF content
    - Data is NOT the hardcoded placeholder ("cc_tx_1", amount=150.00)
    - Required fields are populated with actual extracted values
    """
    # Create a realistic test PDF with transaction data
    # For now using mock content - will be replaced with actual PDF
    pdf_content = b"%PDF-1.4\nRICHARDBREEDLOVE\tFuel\t03/24/2025\t77.37\tCHEVRON 0308017\t27952 WALKER SOUTH\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    # Upload PDF
    response = await test_client.post(
        "/api/upload",
        files={"files": pdf_file}
    )

    assert response.status_code == 202
    session_id = response.json()["id"]

    # Wait for processing to complete (in real scenario, would poll status)
    await asyncio.sleep(2)

    # Query transactions from database
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    # Assert we have transactions
    assert len(transactions) > 0, "Should extract at least one transaction from PDF"

    # Assert NOT placeholder data
    first_tx = transactions[0]
    assert first_tx.merchant_name != "AMAZON MARKETPLACE", "Should not have placeholder merchant name"
    assert first_tx.amount != 150.00, "Should not have placeholder amount"
    assert str(first_tx.id) != "cc_tx_1", "Should not have placeholder ID"

    # Assert actual extracted fields exist
    assert first_tx.transaction_date is not None, "Should extract transaction date"
    assert first_tx.merchant_name is not None, "Should extract merchant name"
    assert first_tx.raw_data is not None, "Should preserve raw PDF data"
    assert "raw_text" in first_tx.raw_data, "raw_data should contain raw_text field"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_transaction_has_all_fields(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify all required fields are present in extracted transactions.

    Tests that extraction populates:
    - employee_id (or null if not resolved)
    - transaction_date
    - amount
    - merchant_name
    - merchant_address
    - expense_type
    - raw_data
    - incomplete_flag (new field)
    - is_credit (new field)
    """
    # Create test PDF with complete transaction
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tMeals\t03/25/2025\t45.99\tRESTAURANT\t123 MAIN ST\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()
    assert len(transactions) > 0

    tx = transactions[0]

    # Check all required fields exist (allow nulls for employee_id if not resolved)
    assert hasattr(tx, 'employee_id'), "Transaction should have employee_id field"
    assert hasattr(tx, 'transaction_date'), "Transaction should have transaction_date field"
    assert hasattr(tx, 'amount'), "Transaction should have amount field"
    assert hasattr(tx, 'merchant_name'), "Transaction should have merchant_name field"
    assert hasattr(tx, 'merchant_address'), "Transaction should have merchant_address field"
    assert hasattr(tx, 'expense_type'), "Transaction should have expense_type field"
    assert hasattr(tx, 'raw_data'), "Transaction should have raw_data field"
    assert hasattr(tx, 'incomplete_flag'), "Transaction should have incomplete_flag field (new)"
    assert hasattr(tx, 'is_credit'), "Transaction should have is_credit field (new)"

    # Check types and values
    assert tx.transaction_date is not None, "transaction_date should be populated"
    assert isinstance(tx.amount, (int, float)), "amount should be numeric"
    assert tx.merchant_name is not None and len(tx.merchant_name) > 0, "merchant_name should be populated"
    assert isinstance(tx.incomplete_flag, bool), "incomplete_flag should be boolean"
    assert isinstance(tx.is_credit, bool), "is_credit should be boolean"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_amount_can_be_negative(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify negative amounts are stored correctly (credits/refunds).

    Tests that:
    - Negative amounts are preserved (not converted to positive)
    - Database accepts negative amounts (constraint removed)
    """
    # Create test PDF with negative amount (refund)
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tGeneral Expense\t03/26/2025\t-25.50\tAMAZON REFUND\t123 MAIN ST\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should extract transaction with negative amount"

    tx = transactions[0]
    assert tx.amount < 0, f"Amount should be negative, got {tx.amount}"
    assert tx.amount == -25.50, f"Amount should be -25.50, got {tx.amount}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_raw_data_preserved(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify that raw PDF text is preserved in raw_data field.

    Tests that:
    - raw_data contains the original PDF line
    - raw_text field exists in raw_data
    - Can be used for debugging and audit purposes
    """
    # Create test PDF
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tFuel\t03/27/2025\t89.12\tSHELL STATION\t456 ELM ST\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0

    tx = transactions[0]
    assert tx.raw_data is not None, "raw_data should be present"
    assert isinstance(tx.raw_data, dict), "raw_data should be a dictionary"
    assert "raw_text" in tx.raw_data, "raw_data should contain raw_text key"
    assert len(tx.raw_data["raw_text"]) > 0, "raw_text should not be empty"

    # raw_text should contain extracted data
    raw_text = tx.raw_data["raw_text"]
    assert "JOHNSMITH" in raw_text or "89.12" in raw_text or "SHELL" in raw_text, \
        "raw_text should contain some of the original PDF data"
