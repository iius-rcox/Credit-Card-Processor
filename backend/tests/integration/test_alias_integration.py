"""
Integration tests for employee alias mapping workflow.

Tests verify end-to-end workflow of creating aliases and using them
to resolve employee names during PDF extraction.
"""

import pytest
import asyncio
import io
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.employee import Employee
from src.models.transaction import Transaction


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_use_employee_alias(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify complete workflow of creating and using an alias.

    Tests that:
    1. PDF with unknown name "JOHNSMITH" creates transactions with NULL employee_id
    2. Creating alias maps "JOHNSMITH" to existing employee
    3. Re-uploading same PDF resolves employee_id via alias
    """
    # Step 1: Create test employee
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP001",
        name="John Smith",
        department="Engineering",
        cost_center="CC-123"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    # Step 2: Upload PDF with unresolved name "JOHNSMITH"
    pdf_content = b"%PDF-1.4\nJOHNSMITH\tMeals\t03/25/2025\t45.99\tRESTAURANT\t123 MAIN ST\tComplete\n%%EOF"
    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response1 = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response1.status_code == 202
    session_id_1 = response1.json()["id"]

    await asyncio.sleep(2)

    # Query first upload - should have NULL employee_id
    result1 = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id_1)
    )
    transactions_1 = result1.scalars().all()

    assert len(transactions_1) > 0, "Should extract transaction from first upload"
    assert transactions_1[0].employee_id is None, "First upload should have NULL employee_id (no alias yet)"

    # Step 3: Create alias
    alias_data = {
        "extractedName": "JOHNSMITH",
        "employeeId": str(employee.id)
    }

    alias_response = await test_client.post("/api/aliases", json=alias_data)
    assert alias_response.status_code == 201, "Alias creation should succeed"

    # Step 4: Re-upload same PDF
    pdf_file2 = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")
    response2 = await test_client.post("/api/upload", files={"files": pdf_file2})
    assert response2.status_code == 202
    session_id_2 = response2.json()["id"]

    await asyncio.sleep(2)

    # Query second upload - should have employee_id resolved via alias
    result2 = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id_2)
    )
    transactions_2 = result2.scalars().all()

    assert len(transactions_2) > 0, "Should extract transaction from second upload"
    assert transactions_2[0].employee_id is not None, "Second upload should resolve employee_id via alias"
    assert transactions_2[0].employee_id == employee.id, "Should match the aliased employee"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alias_used_automatically(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify alias is used automatically when already exists.

    Tests that:
    - Creating alias first
    - Then uploading PDF automatically resolves employee
    - No manual intervention needed
    """
    # Create test employee
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP002",
        name="Jane Doe",
        department="Sales",
        cost_center="CC-456"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    # Create alias FIRST
    alias_data = {
        "extractedName": "JANEDOE",
        "employeeId": str(employee.id)
    }

    alias_response = await test_client.post("/api/aliases", json=alias_data)
    assert alias_response.status_code == 201

    # Upload PDF with aliased name
    pdf_content = b"%PDF-1.4\nJANEDOE\tFuel\t03/26/2025\t55.00\tGAS STATION\t456 ELM ST\tComplete\n%%EOF"
    pdf_file = ("test_statement.pdf", io.BytesIO(pdf_content), "application/pdf")

    response = await test_client.post("/api/upload", files={"files": pdf_file})
    assert response.status_code == 202
    session_id = response.json()["id"]

    await asyncio.sleep(2)

    # Query transactions - should automatically resolve via alias
    result = await test_session.execute(
        select(Transaction).where(Transaction.session_id == session_id)
    )
    transactions = result.scalars().all()

    assert len(transactions) > 0, "Should extract transaction"
    assert transactions[0].employee_id is not None, "Should resolve employee automatically"
    assert transactions[0].employee_id == employee.id, "Should match aliased employee"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_aliases_for_same_employee(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify multiple aliases can point to same employee.

    Tests that:
    - Create multiple aliases for one employee
    - All variations resolve to same employee_id
    - Different name formats are handled
    """
    # Create test employee
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP003",
        name="Robert Johnson",
        department="IT",
        cost_center="CC-789"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    # Create multiple aliases for same employee
    aliases = [
        {"extractedName": "ROBERTJOHNSON", "employeeId": str(employee.id)},
        {"extractedName": "BOBJOHNSON", "employeeId": str(employee.id)},
        {"extractedName": "RJOHNSON", "employeeId": str(employee.id)},
    ]

    for alias_data in aliases:
        alias_response = await test_client.post("/api/aliases", json=alias_data)
        assert alias_response.status_code == 201, f"Should create alias for {alias_data['extractedName']}"

    # Upload PDF with all three name variations
    pdf_content = b"""%PDF-1.4
ROBERTJOHNSON\tMeals\t03/27/2025\t45.99\tREST1\t123 ST\tComplete
BOBJOHNSON\tFuel\t03/28/2025\t55.00\tGAS1\t456 ST\tComplete
RJOHNSON\tHotel\t03/29/2025\t200.00\tHOTEL1\t789 ST\tComplete
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

    assert len(transactions) >= 3, "Should extract all 3 transactions"

    # All should resolve to same employee
    for tx in transactions:
        assert tx.employee_id is not None, "All transactions should have employee_id"
        assert tx.employee_id == employee.id, "All should resolve to same employee via different aliases"
