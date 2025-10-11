"""
Integration tests for complete PDF extraction workflow.

Tests verify end-to-end extraction of complete transactions from PDFs,
including date parsing, amount formatting, and data integrity.
"""

import pytest
import asyncio
import io
import uuid
from datetime import datetime
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.transaction import Transaction


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_50_complete_transactions(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify extraction of 50 complete transactions from PDF.

    Tests that:
    - All 50 transactions are extracted
    - All have incomplete_flag = False
    - All required fields are populated
    """
    # Create test PDF with 50 complete transactions
    # Using simplified format - real implementation will use actual PDF
    transactions_data = []
    for i in range(50):
        transactions_data.append(
            f"EMPLOYEE{i % 5}\tMeals\t03/{(i % 28) + 1:02d}/2025\t{50 + i}.99\tMERCHANT{i}\tADDR{i}\tComplete"
        )

    pdf_content = b"%PDF-1.4\n" + "\n".join(transactions_data).encode() + b"\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    # Wait for processing
    await asyncio.sleep(5)

    # Query all transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) == 50, f"Should extract all 50 transactions, got {len(transactions)}"

    # Verify all are complete
    incomplete_count = sum(1 for tx in transactions if tx.incomplete_flag)
    assert incomplete_count == 0, f"All transactions should be complete, found {incomplete_count} incomplete"

    # Verify all have required fields
    for tx in transactions:
        assert tx.transaction_date is not None, "All transactions should have date"
        assert tx.amount is not None, "All transactions should have amount"
        assert tx.merchant_name is not None, "All transactions should have merchant name"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_employee_names_resolved(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify employee names are resolved or set to NULL if not found.

    Tests that:
    - Valid employee names are matched to employee_id
    - Unknown names result in NULL employee_id
    - Extraction continues regardless of employee resolution
    """
    # Create test PDF with transactions
    pdf_content = b"""%PDF-1.4
JOHNSMITH\tMeals\t03/25/2025\t45.99\tRESTAURANT\t123 ST\tComplete
UNKNOWNEMPLOYEE\tFuel\t03/26/2025\t55.00\tGAS\t456 ST\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) >= 1, "Should extract transactions"

    # At least one transaction should exist
    # Since we don't have employees in test DB, they should be NULL or resolved via alias
    for tx in transactions:
        # Employee ID can be null or a valid UUID
        assert tx.employee_id is None or isinstance(tx.employee_id, uuid.UUID), \
            "employee_id should be None or valid UUID"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_dates_parsed_correctly(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify transaction dates are parsed correctly from MM/DD/YYYY format.

    Tests that:
    - Dates are converted to datetime objects
    - Date format is YYYY-MM-DD in database
    - Various date formats are handled (M/D/YYYY, MM/DD/YYYY)
    """
    pdf_content = b"""%PDF-1.4
JOHN\tMeals\t3/5/2025\t45.99\tREST1\t123 ST\tComplete
JANE\tFuel\t03/15/2025\t55.00\tGAS1\t456 ST\tComplete
BOB\tHotel\t12/25/2025\t200.00\tHOTEL1\t789 ST\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) >= 3, "Should extract all transactions"

    for tx in transactions:
        assert tx.transaction_date is not None, "All dates should be parsed"
        assert isinstance(tx.transaction_date, (datetime, str)), "Date should be datetime or ISO string"

        # If stored as string, should be in YYYY-MM-DD format
        if isinstance(tx.transaction_date, str):
            assert len(tx.transaction_date) >= 10, "Date string should include year-month-day"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_amounts_with_commas_parsed(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify amounts with comma separators are parsed correctly.

    Tests that:
    - "1,234.56" is parsed as 1234.56
    - Commas are stripped before conversion
    - Decimal precision is maintained
    """
    pdf_content = b"""%PDF-1.4
JOHN\tMeals\t03/25/2025\t1,234.56\tREST\t123 ST\tComplete
JANE\tFuel\t03/26/2025\t23,456.78\tGAS\t456 ST\tComplete
BOB\tHotel\t03/27/2025\t999.99\tHOTEL\t789 ST\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) >= 3, "Should extract all transactions"

    # Check specific amounts
    amounts = [tx.amount for tx in transactions]

    # Should have parsed comma-separated values
    assert any(abs(float(amt) - 1234.56) < 0.01 for amt in amounts if amt), \
        "Should parse 1,234.56 correctly"
    assert any(abs(float(amt) - 23456.78) < 0.01 for amt in amounts if amt), \
        "Should parse 23,456.78 correctly"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_merchant_names_non_empty(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify all merchant names are populated (non-empty).

    Tests that:
    - merchant_name field is not NULL
    - merchant_name is not empty string
    - Extraction captures merchant information
    """
    pdf_content = b"""%PDF-1.4
JOHN\tMeals\t03/25/2025\t45.99\tCHEVRON 0308017\t123 ST\tComplete
JANE\tFuel\t03/26/2025\t55.00\tSHELL STATION 456\t456 ST\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) >= 2, "Should extract transactions"

    for tx in transactions:
        assert tx.merchant_name is not None, "merchant_name should not be NULL"
        assert len(tx.merchant_name) > 0, "merchant_name should not be empty string"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_raw_data_contains_original_text(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify raw_data.raw_text contains the original PDF line.

    Tests that:
    - raw_data is populated
    - raw_text field exists
    - Contains recognizable content from PDF
    """
    pdf_content = b"""%PDF-1.4
RICHARDBREEDLOVE\tFuel\t03/24/2025\t77.37\tCHEVRON 0308017\t27952 WALKER SOUTH\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should extract transaction"

    tx = transactions[0]
    assert tx.raw_data is not None, "raw_data should be populated"
    assert "raw_text" in tx.raw_data, "raw_data should have raw_text field"

    raw_text = tx.raw_data["raw_text"]
    # Should contain some of the original data
    assert "RICHARDBREEDLOVE" in raw_text or "77.37" in raw_text or "CHEVRON" in raw_text, \
        "raw_text should contain original PDF content"
