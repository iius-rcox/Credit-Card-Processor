"""
Unit tests for CSV generator (T052).

Tests pvault CSV format compliance and employee exclusion logic.
"""

import pytest
import os
import csv
from decimal import Decimal
from datetime import date

from api.models import Session, Employee, ExpenseTransaction
from generation.csv_generator import generate_csv_export, validate_csv_format, PVAULT_HEADERS


class TestCSVGenerator:
    """Test pvault CSV export generation."""

    def test_exactly_18_columns(self):
        """Verify CSV has exactly 18 columns in correct order."""
        # Create complete employee
        expense = ExpenseTransaction(
            employee_id="EMP001",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("125.50"),
            transaction_name="Test",
            has_receipt=True,
            has_gl_code=True,
        )

        employee = Employee(
            employee_id="EMP001",
            name="Test User",
            card_number="1234567890123456",
            expenses=[expense],
        )

        session = Session(
            credit_card_pdf_path="test.pdf", expense_report_pdf_path="test2.pdf", employees=[employee]
        )

        file_path = generate_csv_export(session, output_dir="server/tests/unit/temp")

        # Read CSV and check columns
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)

            assert len(header) == 18, f"Expected 18 columns, got {len(header)}"
            assert header == PVAULT_HEADERS, "Column headers don't match pvault format"

        os.remove(file_path)

    def test_only_complete_employees_included(self):
        """
        CRITICAL: Verify only employees with completion_status='complete' are in CSV.

        Employee A: 100% complete → ALL expenses in CSV
        Employee B: 90% complete → NONE of expenses in CSV
        """
        # Employee A: All expenses complete
        emp_a_exp = ExpenseTransaction(
            employee_id="EMPA",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("100.00"),
            transaction_name="Complete",
            has_receipt=True,
            has_gl_code=True,
        )

        emp_a = Employee(
            employee_id="EMPA",
            name="Complete Employee",
            card_number="1111111111111111",
            expenses=[emp_a_exp],
        )

        # Employee B: Has incomplete expense
        emp_b_complete = ExpenseTransaction(
            employee_id="EMPB",
            transaction_date=date(2025, 9, 15),
            transaction_amount=Decimal("50.00"),
            transaction_name="Complete",
            has_receipt=True,
            has_gl_code=True,
        )

        emp_b_incomplete = ExpenseTransaction(
            employee_id="EMPB",
            transaction_date=date(2025, 9, 16),
            transaction_amount=Decimal("25.00"),
            transaction_name="Incomplete",
            has_receipt=False,
            has_gl_code=False,
        )

        emp_b = Employee(
            employee_id="EMPB",
            name="Incomplete Employee",
            card_number="2222222222222222",
            expenses=[emp_b_complete, emp_b_incomplete],
        )

        session = Session(
            credit_card_pdf_path="test.pdf", expense_report_pdf_path="test2.pdf", employees=[emp_a, emp_b]
        )

        file_path = generate_csv_export(session, output_dir="server/tests/unit/temp")

        # Read CSV
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            rows = list(reader)

            # Should have 1 row (only Employee A's 1 expense)
            assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"

            # Verify it's Employee A's expense
            assert "EMPA" in rows[0][0] or "Complete Employee" in rows[0][15]  # Card Holder column

        os.remove(file_path)

    def test_csv_format_validation(self):
        """Test validate_csv_format function."""
        pytest.skip("TODO: Test UTF-8 encoding, CRLF line endings, QUOTE_MINIMAL")

    def test_amounts_formatted_correctly(self):
        """Test amounts have 2 decimals, no $ symbols."""
        pytest.skip("TODO: Verify amount formatting")

    def test_dates_yyyy_mm_dd_format(self):
        """Test dates in YYYY-MM-DD format."""
        pytest.skip("TODO: Verify date formatting")
