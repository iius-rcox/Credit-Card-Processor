"""
Integration test: Excel Status column accuracy (T015).

Verifies that Excel report Status column contains correct values
and has proper conditional formatting.
This test MUST FAIL until Excel generator is implemented (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestExcelStatusColumn:
    """Test Excel report Status column accuracy."""

    def test_status_column_missing_receipt(self):
        """Verify Status = 'Missing Receipt' for expense without receipt."""
        # TODO: Implement after Excel generator exists
        pytest.fail("Excel generator not implemented yet - TDD")

    def test_status_column_missing_gl_code(self):
        """Verify Status = 'Missing GL Code' for expense without GL code."""
        pytest.fail("Excel generator not implemented yet - TDD")

    def test_status_column_missing_both(self):
        """Verify Status = 'Missing Both' for expense missing both."""
        pytest.fail("Excel generator not implemented yet - TDD")

    def test_conditional_formatting_applied(self):
        """Verify conditional formatting: red, yellow, orange backgrounds."""
        pytest.fail("Excel generator not implemented yet - TDD")
