"""
Contract tests for GET /api/session/{sessionId} endpoint.

These tests verify the API contract defined in contracts/get-session.yaml.
They MUST FAIL until the endpoint is implemented (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestSessionEndpoint:
    """Test suite for GET /api/session/{sessionId} endpoint contract."""

    def test_get_session_success(self):
        """
        Test retrieving session data with valid session_id.

        Expected: 200 status with complete session object including
        employees array, matching_results array, and all required fields
        """
        # Use a mock session_id
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/session/{session_id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Assert top-level required fields
        required_fields = [
            "session_id",
            "created_at",
            "updated_at",
            "processing_status",
            "employees",
            "matching_results",
        ]
        for field in required_fields:
            assert field in data, f"Response must contain '{field}' field"

        # Assert session_id matches request
        assert data["session_id"] == session_id

        # Assert processing_status is valid enum value
        assert data["processing_status"] in ["pending", "processing", "complete", "error"]

        # Assert employees is an array
        assert isinstance(data["employees"], list), "employees must be an array"

        # Assert matching_results is an array
        assert isinstance(data["matching_results"], list), "matching_results must be an array"

    def test_get_session_employee_structure(self):
        """
        Test that employee objects have correct structure.

        Expected employee fields:
        - employee_id, name, card_number, completion_status, expenses[], receipts[]
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/session/{session_id}")

        data = response.json()
        employees = data.get("employees", [])

        # If there are employees, verify structure
        if len(employees) > 0:
            employee = employees[0]

            required_employee_fields = [
                "employee_id",
                "name",
                "card_number",
                "completion_status",
                "expenses",
                "receipts",
            ]
            for field in required_employee_fields:
                assert field in employee, f"Employee must have '{field}' field"

            # Verify completion_status enum
            assert employee["completion_status"] in ["complete", "incomplete"]

            # Verify expenses and receipts are arrays
            assert isinstance(employee["expenses"], list)
            assert isinstance(employee["receipts"], list)

    def test_get_session_expense_structure(self):
        """
        Test that expense transaction objects have correct structure.

        Expected expense fields:
        - transaction_id, transaction_date, transaction_amount,
          transaction_name, has_receipt, has_gl_code, status
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/session/{session_id}")

        data = response.json()
        employees = data.get("employees", [])

        # Find an employee with expenses
        for employee in employees:
            if len(employee.get("expenses", [])) > 0:
                expense = employee["expenses"][0]

                required_expense_fields = [
                    "transaction_id",
                    "transaction_date",
                    "transaction_amount",
                    "transaction_name",
                    "has_receipt",
                    "has_gl_code",
                    "status",
                ]
                for field in required_expense_fields:
                    assert field in expense, f"Expense must have '{field}' field"

                # Verify status enum
                assert expense["status"] in [
                    "Missing Receipt",
                    "Missing GL Code",
                    "Missing Both",
                    "Complete",
                ]

                # Verify boolean fields
                assert isinstance(expense["has_receipt"], bool)
                assert isinstance(expense["has_gl_code"], bool)

                # Verify transaction_amount is number
                assert isinstance(expense["transaction_amount"], (int, float))

                break  # Only need to check one expense

    def test_get_session_receipt_structure(self):
        """
        Test that receipt record objects have correct structure.

        Expected receipt fields:
        - receipt_id, employee_id, amount, gl_code (nullable), project_code (nullable)
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/session/{session_id}")

        data = response.json()
        employees = data.get("employees", [])

        # Find an employee with receipts
        for employee in employees:
            if len(employee.get("receipts", [])) > 0:
                receipt = employee["receipts"][0]

                required_receipt_fields = ["receipt_id", "employee_id", "amount"]
                for field in required_receipt_fields:
                    assert field in receipt, f"Receipt must have '{field}' field"

                # gl_code and project_code are optional but should be present (nullable)
                assert "gl_code" in receipt or "project_code" in receipt, (
                    "Receipt should have at least gl_code or project_code field"
                )

                # Verify amount is number
                assert isinstance(receipt["amount"], (int, float))

                break

    def test_get_session_matching_results_structure(self):
        """
        Test that matching result objects have correct structure.

        Expected matching_result fields:
        - expense_transaction_id, matched_receipt_id (nullable),
          match_reason, has_gl_code
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/session/{session_id}")

        data = response.json()
        matching_results = data.get("matching_results", [])

        if len(matching_results) > 0:
            result = matching_results[0]

            required_fields = [
                "expense_transaction_id",
                "match_reason",
                "has_gl_code",
            ]
            for field in required_fields:
                assert field in result, f"MatchingResult must have '{field}' field"

            # matched_receipt_id is nullable, but field should exist
            assert "matched_receipt_id" in result

            # Verify match_reason enum
            assert result["match_reason"] in [
                "exact_match",
                "no_receipt_found",
                "multiple_matches",
            ]

            # Verify has_gl_code is boolean
            assert isinstance(result["has_gl_code"], bool)

    def test_get_session_not_found(self):
        """
        Test retrieving non-existent session.

        Expected: 404 status with error message
        """
        nonexistent_session_id = "99999999-9999-9999-9999-999999999999"

        response = client.get(f"/api/session/{nonexistent_session_id}")

        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"
        assert "not found" in data["error"].lower()

    def test_get_session_invalid_uuid_format(self):
        """
        Test retrieving session with invalid UUID format.

        Expected: 400 or 422 status with error message
        """
        invalid_session_id = "not-a-uuid"

        response = client.get(f"/api/session/{invalid_session_id}")

        # Accept either 400 or 422 for validation errors
        assert response.status_code in [400, 422, 404], (
            f"Expected 400/422/404 for invalid UUID, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data or "detail" in data
