"""
Integration test: Employee exclusion from CSV export (T018).

Verifies that employees with ANY incomplete expense are FULLY excluded from CSV.
This test MUST FAIL until CSV generator is implemented (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


class TestCSVExclusion:
    """Test employee exclusion logic for CSV export."""

    def test_exclude_all_expenses_from_incomplete_employee(self):
        """
        Employee A: 10/10 expenses complete → ALL 10 in CSV
        Employee B: 9/10 expenses complete → NONE of B's 10 in CSV

        This is CRITICAL business logic for pvault format.
        """
        pytest.fail("CSV generator not implemented yet - TDD")

    def test_partial_employee_fully_excluded(self):
        """Verify even complete expenses excluded if employee has any incomplete."""
        pytest.fail("CSV generator not implemented yet - TDD")
