"""
Unit tests for matcher logic (T050).

Tests expense-to-receipt matching algorithm with all scenarios.
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date

from api.models import Employee, ExpenseTransaction, ReceiptRecord, MatchReason
from processing.matcher import match_expenses_to_receipts, find_matching_receipt, has_ambiguous_match


class TestMatcherLogic:
    """Test expense-to-receipt matching algorithm."""

    def test_exact_match_scenario(self):
        """
        Test exact match: 1 employee, 1 expense, 1 matching receipt.

        Expected: expense.has_receipt=True, match_reason="exact_match"
        """
        # Create employee with one expense
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("125.50"),
            transaction_name="Amazon",
        )

        # Create matching receipt (same amount)
        receipt = ReceiptRecord(
            receipt_id="RCP001",
            employee_id="EMP001",
            amount=Decimal("125.50"),
            gl_code="5000-100",
        )

        employee = Employee(
            employee_id="EMP001",
            name="John Doe",
            card_number="1234567890123456",
            expenses=[expense],
            receipts=[receipt],
        )

        # Run matcher
        results = match_expenses_to_receipts([employee])

        assert len(results) == 1
        result = results[0]

        # Verify exact match
        assert result.match_reason == MatchReason.EXACT_MATCH
        assert result.matched_receipt_id == "RCP001"
        assert result.has_gl_code is True  # Receipt has GL code

        # Verify expense updated
        assert expense.has_receipt is True
        assert expense.has_gl_code is True
        assert expense.status.value == "Complete"

    def test_no_receipt_found_scenario(self):
        """
        Test no receipt found: expense with no matching receipt.

        Expected: expense.has_receipt=False, match_reason="no_receipt_found"
        """
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("125.50"),
            transaction_name="Amazon",
        )

        employee = Employee(
            employee_id="EMP001",
            name="John Doe",
            card_number="1234567890123456",
            expenses=[expense],
            receipts=[],  # No receipts
        )

        results = match_expenses_to_receipts([employee])

        assert len(results) == 1
        result = results[0]

        # Verify no receipt found
        assert result.match_reason == MatchReason.NO_RECEIPT_FOUND
        assert result.matched_receipt_id is None
        assert result.has_gl_code is False

        # Verify expense updated
        assert expense.has_receipt is False
        assert expense.has_gl_code is False
        assert expense.status.value == "Missing Both"

    def test_multiple_matches_scenario(self):
        """
        Test multiple matches: 2 receipts with same amount for same employee.

        Expected: expense.has_receipt=False, match_reason="multiple_matches" (ambiguous)
        """
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("50.00"),
            transaction_name="Gas Station",
        )

        # Two receipts with same amount (ambiguous)
        receipt1 = ReceiptRecord(
            receipt_id="RCP001",
            employee_id="EMP001",
            amount=Decimal("50.00"),
            gl_code="5000-100",
        )

        receipt2 = ReceiptRecord(
            receipt_id="RCP002",
            employee_id="EMP001",
            amount=Decimal("50.00"),
            gl_code="5000-200",
        )

        employee = Employee(
            employee_id="EMP001",
            name="John Doe",
            card_number="1234567890123456",
            expenses=[expense],
            receipts=[receipt1, receipt2],
        )

        results = match_expenses_to_receipts([employee])

        assert len(results) == 1
        result = results[0]

        # Verify multiple matches (ambiguous)
        assert result.match_reason == MatchReason.MULTIPLE_MATCHES
        assert result.matched_receipt_id is None  # Cannot auto-match
        assert expense.has_receipt is False  # Marked as no receipt due to ambiguity

    def test_gl_code_detection_from_receipt(self):
        """
        Test that GL code is detected from matched receipt.

        Expected: has_gl_code=True if receipt has gl_code or project_code
        """
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("75.00"),
            transaction_name="Office Supplies",
        )

        receipt_with_gl = ReceiptRecord(
            receipt_id="RCP001",
            employee_id="EMP001",
            amount=Decimal("75.00"),
            gl_code="5000-300",
        )

        employee = Employee(
            employee_id="EMP001",
            name="Jane Smith",
            card_number="1234-5678-9012-3456",
            expenses=[expense],
            receipts=[receipt_with_gl],
        )

        results = match_expenses_to_receipts([employee])

        # Verify GL code detected
        assert expense.has_gl_code is True
        assert expense.status.value == "Complete"

    def test_project_code_counts_as_gl_code(self):
        """Test that project_code also sets has_gl_code=True."""
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("100.00"),
            transaction_name="Materials",
        )

        receipt_with_project = ReceiptRecord(
            receipt_id="RCP001",
            employee_id="EMP001",
            amount=Decimal("100.00"),
            project_code="PROJ-2025-001",  # Has project code, no GL code
        )

        employee = Employee(
            employee_id="EMP001",
            name="Bob Johnson",
            card_number="************1234",
            expenses=[expense],
            receipts=[receipt_with_project],
        )

        results = match_expenses_to_receipts([employee])

        # Verify project code counts as GL code
        assert expense.has_gl_code is True
        assert expense.status.value == "Complete"

    def test_expense_with_own_gl_account(self):
        """Test expense that has its own gl_account field set."""
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("200.00"),
            transaction_name="Tools",
            gl_account="5000-400",  # Expense has own GL account
        )

        # No receipt exists
        employee = Employee(
            employee_id="EMP001",
            name="Alice Brown",
            card_number="1234567890123456",
            expenses=[expense],
            receipts=[],
        )

        results = match_expenses_to_receipts([employee])

        # Expense has GL account but no receipt
        assert expense.has_receipt is False
        assert expense.has_gl_code is True  # From expense.gl_account
        assert expense.status.value == "Missing Receipt"

    def test_multiple_employees(self):
        """Test matching across multiple employees."""
        # Employee 1
        exp1 = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("50.00"),
            transaction_name="Lunch",
        )

        rec1 = ReceiptRecord(receipt_id="RCP001", employee_id="EMP001", amount=Decimal("50.00"), gl_code="5000-500")

        emp1 = Employee(
            employee_id="EMP001",
            name="Alice",
            card_number="1111111111111111",
            expenses=[exp1],
            receipts=[rec1],
        )

        # Employee 2
        exp2 = ExpenseTransaction(
            employee_id="EMP002",
            transaction_date=date(2025, 9, 16),
            transaction_amount=Decimal("75.00"),
            transaction_name="Gas",
        )

        # No receipt for Employee 2
        emp2 = Employee(
            employee_id="EMP002",
            name="Bob",
            card_number="2222222222222222",
            expenses=[exp2],
            receipts=[],
        )

        results = match_expenses_to_receipts([emp1, emp2])

        assert len(results) == 2

        # Employee 1 should have exact match
        emp1_result = next(r for r in results if r.expense_transaction_id == exp1.transaction_id)
        assert emp1_result.match_reason == MatchReason.EXACT_MATCH
        assert exp1.has_receipt is True

        # Employee 2 should have no receipt
        emp2_result = next(r for r in results if r.expense_transaction_id == exp2.transaction_id)
        assert emp2_result.match_reason == MatchReason.NO_RECEIPT_FOUND
        assert exp2.has_receipt is False


class TestHelperFunctions:
    """Test helper functions."""

    def test_find_matching_receipt_single_match(self):
        """Test find_matching_receipt with single match."""
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("125.50"),
            transaction_name="Test",
        )

        receipt = ReceiptRecord(receipt_id="RCP001", employee_id="EMP001", amount=Decimal("125.50"))

        result = find_matching_receipt(expense, [receipt])

        assert result is not None
        assert result.receipt_id == "RCP001"

    def test_find_matching_receipt_no_match(self):
        """Test find_matching_receipt with no match."""
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("125.50"),
            transaction_name="Test",
        )

        receipt = ReceiptRecord(
            receipt_id="RCP001", employee_id="EMP001", amount=Decimal("99.99")  # Different amount
        )

        result = find_matching_receipt(expense, [receipt])

        assert result is None

    def test_has_ambiguous_match(self):
        """Test has_ambiguous_match detection."""
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("50.00"),
            transaction_name="Test",
        )

        # Two receipts with same amount
        receipts = [
            ReceiptRecord(receipt_id="RCP001", employee_id="EMP001", amount=Decimal("50.00")),
            ReceiptRecord(receipt_id="RCP002", employee_id="EMP001", amount=Decimal("50.00")),
        ]

        assert has_ambiguous_match(expense, receipts) is True

        # Single receipt
        assert has_ambiguous_match(expense, [receipts[0]]) is False

        # No match
        different_receipt = ReceiptRecord(receipt_id="RCP003", employee_id="EMP001", amount=Decimal("99.99"))
        assert has_ambiguous_match(expense, [different_receipt]) is False
