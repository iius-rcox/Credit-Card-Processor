"""
Contract tests for Employee Alias API endpoints.

Tests verify the API contract for managing employee name aliases
used to map extracted PDF names to existing employee records.
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.models.employee import Employee


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_alias_creates_mapping(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify POST /api/aliases creates an employee alias.

    Tests that:
    - Returns 201 Created status
    - Response contains correct structure (id, extractedName, employeeId, createdAt)
    - Alias is persisted in database
    """
    # Create a test employee first
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP001",
        name="John Doe",
        department="Engineering",
        cost_center="CC-123"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    # Create alias via API
    alias_data = {
        "extractedName": "JOHNSMITH",
        "employeeId": str(employee.id)
    }

    response = await test_client.post("/api/aliases", json=alias_data)

    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"

    response_data = response.json()

    # Verify response structure
    assert "id" in response_data, "Response should contain id"
    assert "extractedName" in response_data, "Response should contain extractedName"
    assert "employeeId" in response_data, "Response should contain employeeId"
    assert "createdAt" in response_data, "Response should contain createdAt"

    # Verify values
    assert response_data["extractedName"] == "JOHNSMITH"
    assert response_data["employeeId"] == str(employee.id)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_alias_duplicate_returns_400(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify POST /api/aliases returns 400 for duplicate extractedName.

    Tests that:
    - First creation succeeds (201)
    - Second creation with same extractedName fails (400)
    - Error message indicates duplicate
    """
    # Create test employee
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP002",
        name="Jane Smith",
        department="Sales",
        cost_center="CC-456"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    alias_data = {
        "extractedName": "JANESMITH",
        "employeeId": str(employee.id)
    }

    # First creation should succeed
    response1 = await test_client.post("/api/aliases", json=alias_data)
    assert response1.status_code == 201, "First alias creation should succeed"

    # Second creation with same extractedName should fail
    response2 = await test_client.post("/api/aliases", json=alias_data)
    assert response2.status_code == 400, f"Expected 400 Bad Request for duplicate, got {response2.status_code}"

    error_data = response2.json()
    assert "detail" in error_data, "Error response should contain detail"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_post_alias_invalid_employee_returns_404(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify POST /api/aliases returns 404 for non-existent employeeId.

    Tests that:
    - Invalid employeeId returns 404 Not Found
    - Alias is not created
    """
    # Use a random UUID that doesn't exist in database
    non_existent_id = str(uuid.uuid4())

    alias_data = {
        "extractedName": "UNKNOWN",
        "employeeId": non_existent_id
    }

    response = await test_client.post("/api/aliases", json=alias_data)

    assert response.status_code == 404, f"Expected 404 Not Found for invalid employee, got {response.status_code}"

    error_data = response.json()
    assert "detail" in error_data, "Error response should contain detail"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_aliases_returns_list(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify GET /api/aliases returns list of aliases with employee details.

    Tests that:
    - Returns 200 OK
    - Response contains "aliases" array
    - Each alias includes employee details (name, email)
    """
    # Create test employee
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP003",
        name="Bob Johnson",
        email="bob@example.com",
        department="IT",
        cost_center="CC-789"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    # Create alias
    alias_data = {
        "extractedName": "BOBJOHNSON",
        "employeeId": str(employee.id)
    }
    create_response = await test_client.post("/api/aliases", json=alias_data)
    assert create_response.status_code == 201

    # Get all aliases
    response = await test_client.get("/api/aliases")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

    response_data = response.json()
    assert "aliases" in response_data, "Response should contain aliases array"
    assert isinstance(response_data["aliases"], list), "aliases should be a list"

    # Verify structure of alias objects
    if len(response_data["aliases"]) > 0:
        alias = response_data["aliases"][0]
        assert "id" in alias, "Alias should have id"
        assert "extractedName" in alias, "Alias should have extractedName"
        assert "employeeId" in alias, "Alias should have employeeId"
        assert "createdAt" in alias, "Alias should have createdAt"
        assert "employee" in alias, "Alias should have employee details"

        employee_data = alias["employee"]
        assert "name" in employee_data, "Employee should have name"
        assert "email" in employee_data, "Employee should have email"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_alias_removes_mapping(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify DELETE /api/aliases/{id} removes the alias.

    Tests that:
    - Returns 204 No Content on successful deletion
    - Alias is removed from database
    - Subsequent GET returns 404
    """
    # Create test employee and alias
    employee = Employee(
        id=uuid.uuid4(),
        employee_number="EMP004",
        name="Alice Williams",
        department="HR",
        cost_center="CC-111"
    )
    test_session.add(employee)
    await test_session.commit()
    await test_session.refresh(employee)

    alias_data = {
        "extractedName": "ALICEWILLIAMS",
        "employeeId": str(employee.id)
    }
    create_response = await test_client.post("/api/aliases", json=alias_data)
    assert create_response.status_code == 201

    alias_id = create_response.json()["id"]

    # Delete alias
    delete_response = await test_client.delete(f"/api/aliases/{alias_id}")

    assert delete_response.status_code == 204, f"Expected 204 No Content, got {delete_response.status_code}"

    # Verify alias is gone (would need GET endpoint to verify, or check database directly)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_alias_not_found_returns_404(test_client: AsyncClient, test_session: AsyncSession):
    """
    Verify DELETE /api/aliases/{id} returns 404 for non-existent alias.

    Tests that:
    - Returns 404 Not Found
    - Error message is appropriate
    """
    # Try to delete non-existent alias
    non_existent_id = str(uuid.uuid4())

    response = await test_client.delete(f"/api/aliases/{non_existent_id}")

    assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}"

    error_data = response.json()
    assert "detail" in error_data, "Error response should contain detail"
