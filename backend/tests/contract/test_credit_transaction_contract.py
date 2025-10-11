"""
Contract tests for credit/refund transaction handling.

Tests verify that transactions with negative amounts (credits/refunds)
are correctly identified and flagged with is_credit = True.
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
async def test_is_credit_flag_set_for_negative_amounts(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify is_credit flag is set to True for negative amounts.

    Tests that:
    - Negative amount is preserved (not converted to positive)
    - is_credit flag is set to True
    - Transaction is saved successfully
    """
    # Create test PDF with negative amount (refund/credit)
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tGeneral Expense\t03/27/2025\t-45.99\tAMAZON REFUND\t123 MAIN ST\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    # Query transactions with is_credit=True
    result = await test_session.execute(
        select(Transaction).where(
            Transaction.session_id == session_id,
            Transaction.is_credit == True
        )
    )
    credits = result.scalars().all()

    assert len(credits) > 0, "Should identify credit/refund transaction"

    credit_tx = credits[0]
    assert credit_tx.amount < 0, f"Amount should be negative, got {credit_tx.amount}"
    assert credit_tx.is_credit is True, f"is_credit should be True, got {credit_tx.is_credit}"
    assert credit_tx.amount == -45.99, f"Should preserve exact negative amount, got {credit_tx.amount}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_is_credit_flag_false_for_positive_amounts(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify is_credit flag is False for positive amounts (regular charges).

    Tests that:
    - Positive amounts have is_credit = False
    - Normal transactions are not mistakenly flagged as credits
    """
    # Create test PDF with positive amount (regular charge)
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tMeals\t03/28/2025\t75.50\tRESTAURANT\t456 ELM ST\tComplete\n%%EOF"

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should extract regular transaction"

    tx = transactions[0]
    assert tx.amount > 0, f"Amount should be positive, got {tx.amount}"
    assert tx.is_credit is False, f"is_credit should be False for positive amounts, got {tx.is_credit}"
    assert tx.amount == 75.50, f"Should preserve exact positive amount, got {tx.amount}"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_multiple_credits_and_charges_mixed(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify correct handling of PDFs with both credits and charges.

    Tests that:
    - Each transaction is flagged correctly
    - Credits and charges can coexist in same session
    - Flags are independent for each transaction
    """
    # Create test PDF with both positive and negative amounts
    pdf_content = b"""%PDF-1.4
JOHNSMITH\tMeals\t03/29/2025\t55.00\tDINER\t123 ST\tComplete
JOHNSMITH\tGeneral Expense\t03/29/2025\t-15.00\tREFUND\t456 ST\tComplete
JOHNSMITH\tFuel\t03/29/2025\t80.00\tGAS STATION\t789 ST\tComplete
%%EOF"""

    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(3)  # Extra time for multiple transactions

    # Query all transactions
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    all_transactions = result.scalars().all()

    assert len(all_transactions) >= 2, "Should extract multiple transactions"

    # Query credits
    credits_result = await test_session.execute(
        select(Transaction).where(
            Transaction.session_id == session_id,
            Transaction.is_credit == True
        )
    )
    credits = credits_result.scalars().all()

    # Query charges
    charges_result = await test_session.execute(
        select(Transaction).where(
            Transaction.session_id == session_id,
            Transaction.is_credit == False
        )
    )
    charges = charges_result.scalars().all()

    # Verify we have both types
    assert len(credits) >= 1, "Should have at least one credit"
    assert len(charges) >= 2, "Should have at least two charges"

    # Verify credit has negative amount
    for credit in credits:
        assert credit.amount < 0, "Credits should have negative amounts"
        assert credit.is_credit is True, "Credits should have is_credit=True"

    # Verify charges have positive amounts
    for charge in charges:
        assert charge.amount > 0, "Charges should have positive amounts"
        assert charge.is_credit is False, "Charges should have is_credit=False"
