"""
Integration test: Multiple expenses with identical amounts (T016).

Verifies ambiguous matching when employee has duplicate expense amounts.
This test MUST FAIL until matcher is implemented (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


class TestDuplicateAmounts:
    """Test matching behavior with duplicate expense amounts."""

    def test_two_expenses_same_amount_one_receipt(self):
        """
        Employee has 2 expenses both $50.00, only 1 receipt for $50.00.
        Expected: Both expenses marked 'Missing Receipt' (ambiguous match).
        """
        pytest.fail("Matcher not implemented yet - TDD")

    def test_match_reason_multiple_matches(self):
        """Verify match_reason = 'multiple_matches' for ambiguous cases."""
        pytest.fail("Matcher not implemented yet - TDD")
