"""
Unit tests for AliasService business logic.

Tests verify alias creation, deletion, and employee resolution logic
without requiring full database integration.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from src.services.alias_service import AliasService
from src.models.employee_alias import EmployeeAlias
from src.models.employee import Employee


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_alias_repo():
    """Create mock AliasRepository."""
    return AsyncMock()


@pytest.fixture
def mock_employee_repo():
    """Create mock EmployeeRepository."""
    return AsyncMock()


@pytest.fixture
def alias_service(mock_db, mock_alias_repo, mock_employee_repo):
    """Create AliasService with mocked dependencies."""
    service = AliasService(mock_db)
    service.alias_repo = mock_alias_repo
    service.employee_repo = mock_employee_repo
    return service


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_alias_with_valid_data(alias_service, mock_employee_repo, mock_alias_repo, mock_db):
    """Test create_alias succeeds with valid employee ID."""
    employee_id = uuid.uuid4()
    extracted_name = "JOHNSMITH"

    # Mock employee exists
    mock_employee = MagicMock(spec=Employee)
    mock_employee.id = employee_id
    mock_employee_repo.get_employee_by_id.return_value = mock_employee

    # Mock alias creation
    mock_alias = MagicMock(spec=EmployeeAlias)
    mock_alias.id = uuid.uuid4()
    mock_alias.extracted_name = extracted_name
    mock_alias.employee_id = employee_id
    mock_alias_repo.create_alias.return_value = mock_alias

    # Call service
    result = await alias_service.create_alias(extracted_name, employee_id)

    # Verify employee was checked
    mock_employee_repo.get_employee_by_id.assert_called_once_with(employee_id)

    # Verify alias was created
    mock_alias_repo.create_alias.assert_called_once_with(extracted_name, employee_id)

    # Verify commit was called
    mock_db.commit.assert_called_once()

    # Verify result
    assert result.extracted_name == extracted_name
    assert result.employee_id == employee_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_alias_raises_404_on_invalid_employee_id(alias_service, mock_employee_repo):
    """Test create_alias raises 404 when employee doesn't exist."""
    employee_id = uuid.uuid4()
    extracted_name = "JOHNSMITH"

    # Mock employee not found
    mock_employee_repo.get_employee_by_id.return_value = None

    # Call service and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await alias_service.create_alias(extracted_name, employee_id)

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_alias_raises_400_on_duplicate(alias_service, mock_employee_repo, mock_alias_repo, mock_db):
    """Test create_alias raises 400 when extracted_name already exists."""
    from sqlalchemy.exc import IntegrityError

    employee_id = uuid.uuid4()
    extracted_name = "JOHNSMITH"

    # Mock employee exists
    mock_employee = MagicMock(spec=Employee)
    mock_employee.id = employee_id
    mock_employee_repo.get_employee_by_id.return_value = mock_employee

    # Mock IntegrityError for duplicate
    mock_alias_repo.create_alias.side_effect = IntegrityError(
        statement="INSERT INTO employee_aliases...",
        params={},
        orig=Exception("duplicate key value violates unique constraint")
    )

    # Call service and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await alias_service.create_alias(extracted_name, employee_id)

    # Verify exception details
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail.lower()

    # Verify rollback was called
    mock_db.rollback.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_employee_tries_exact_match_first(alias_service, mock_alias_repo):
    """Test resolve_employee tries exact match before alias lookup."""
    extracted_name = "JOHNSMITH"
    employee_id = uuid.uuid4()

    # Mock resolve_employee_id to return employee ID
    mock_alias_repo.resolve_employee_id.return_value = employee_id

    # Call service
    result = await alias_service.resolve_employee(extracted_name)

    # Verify repository method was called
    mock_alias_repo.resolve_employee_id.assert_called_once_with(extracted_name)

    # Verify result
    assert result == employee_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_employee_returns_none_when_not_found(alias_service, mock_alias_repo):
    """Test resolve_employee returns None when neither exact match nor alias found."""
    extracted_name = "UNKNOWN"

    # Mock no match found
    mock_alias_repo.resolve_employee_id.return_value = None

    # Call service
    result = await alias_service.resolve_employee(extracted_name)

    # Verify result is None
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_alias_raises_404_when_not_found(alias_service, mock_alias_repo):
    """Test delete_alias raises 404 when alias doesn't exist."""
    alias_id = uuid.uuid4()

    # Mock alias not found (delete returns False)
    mock_alias_repo.delete_alias.return_value = False

    # Call service and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await alias_service.delete_alias(alias_id)

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_alias_succeeds_when_found(alias_service, mock_alias_repo, mock_db):
    """Test delete_alias succeeds when alias exists."""
    alias_id = uuid.uuid4()

    # Mock alias found and deleted
    mock_alias_repo.delete_alias.return_value = True

    # Call service (should not raise)
    await alias_service.delete_alias(alias_id)

    # Verify repository method was called
    mock_alias_repo.delete_alias.assert_called_once_with(alias_id)

    # Verify commit was called
    mock_db.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_aliases_returns_list_with_employee_details(alias_service, mock_alias_repo):
    """Test get_all_aliases returns formatted list with employee data."""
    # Mock aliases with employee data
    mock_alias_1 = MagicMock(spec=EmployeeAlias)
    mock_alias_1.id = uuid.uuid4()
    mock_alias_1.extracted_name = "JOHNSMITH"
    mock_alias_1.employee_id = uuid.uuid4()
    mock_alias_1.created_at = MagicMock()
    mock_alias_1.created_at.isoformat.return_value = "2025-10-10T12:00:00Z"
    mock_alias_1.employee = MagicMock(spec=Employee)
    mock_alias_1.employee.name = "John Doe"
    mock_alias_1.employee.email = "john@example.com"

    mock_alias_repo.get_all_aliases.return_value = [mock_alias_1]

    # Call service
    result = await alias_service.get_all_aliases()

    # Verify result structure
    assert isinstance(result, list)
    assert len(result) == 1

    alias_dict = result[0]
    assert "id" in alias_dict
    assert "extractedName" in alias_dict
    assert "employeeId" in alias_dict
    assert "createdAt" in alias_dict
    assert "employee" in alias_dict

    assert alias_dict["extractedName"] == "JOHNSMITH"
    assert alias_dict["employee"]["name"] == "John Doe"
    assert alias_dict["employee"]["email"] == "john@example.com"
