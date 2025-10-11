"""
Unit tests for PDF extraction regex patterns.

Tests verify that individual regex patterns correctly match expected
employee names, dates, amounts, and other transaction fields.
"""

import pytest
import re
from decimal import Decimal

from src.services.extraction_service import ExtractionService
from src.repositories.session_repository import SessionRepository
from src.repositories.employee_repository import EmployeeRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.receipt_repository import ReceiptRepository
from src.repositories.alias_repository import AliasRepository


@pytest.fixture
def extraction_service():
    """Create ExtractionService instance for testing patterns."""
    # Create service with None repositories (we're only testing pattern matching)
    service = ExtractionService(
        session_repo=None,  # type: ignore
        employee_repo=None,  # type: ignore
        transaction_repo=None,  # type: ignore
        receipt_repo=None,  # type: ignore
        progress_repo=None,
        alias_repo=None
    )
    return service


@pytest.mark.unit
def test_employee_name_pattern_single_word(extraction_service):
    """Test employee name pattern matches single-word names."""
    pattern = extraction_service.employee_pattern

    # Test single-word all-caps name
    text = "JOHNSMITH\tMeals\t03/24/2025"
    match = pattern.search(text)

    assert match is not None, "Should match single-word employee name"
    assert match.group(1) == "JOHNSMITH", f"Should extract 'JOHNSMITH', got '{match.group(1)}'"


@pytest.mark.unit
def test_employee_name_pattern_multi_word(extraction_service):
    """Test employee name pattern matches multi-word names."""
    pattern = extraction_service.employee_pattern

    # Test multi-word all-caps name
    text = "RICHARD BREEDLOVE\tFuel\t03/24/2025"
    match = pattern.search(text)

    assert match is not None, "Should match multi-word employee name"
    assert match.group(1).strip() == "RICHARD BREEDLOVE", f"Should extract full name, got '{match.group(1)}'"


@pytest.mark.unit
def test_date_pattern_with_leading_zeros(extraction_service):
    """Test date pattern matches MM/DD/YYYY format with leading zeros."""
    pattern = extraction_service.date_pattern

    test_dates = [
        "03/24/2025",
        "12/31/2025",
        "01/01/2025",
    ]

    for date_str in test_dates:
        match = pattern.search(date_str)
        assert match is not None, f"Should match date '{date_str}'"
        assert match.group(1) == date_str, f"Should extract '{date_str}', got '{match.group(1)}'"


@pytest.mark.unit
def test_date_pattern_without_leading_zeros(extraction_service):
    """Test date pattern matches M/D/YYYY format without leading zeros."""
    pattern = extraction_service.date_pattern

    test_dates = [
        "3/5/2025",
        "12/1/2025",
        "1/15/2025",
    ]

    for date_str in test_dates:
        match = pattern.search(date_str)
        assert match is not None, f"Should match date '{date_str}'"
        assert match.group(1) == date_str, f"Should extract '{date_str}', got '{match.group(1)}'"


@pytest.mark.unit
def test_amount_pattern_simple_decimal(extraction_service):
    """Test amount pattern matches simple decimal amounts."""
    pattern = extraction_service.amount_pattern

    test_amounts = [
        "77.37",
        "100.00",
        "1.50",
    ]

    for amount_str in test_amounts:
        match = pattern.search(amount_str)
        assert match is not None, f"Should match amount '{amount_str}'"
        assert match.group(1) == amount_str, f"Should extract '{amount_str}', got '{match.group(1)}'"


@pytest.mark.unit
def test_amount_pattern_with_commas(extraction_service):
    """Test amount pattern matches amounts with comma separators."""
    pattern = extraction_service.amount_pattern

    test_amounts = [
        "1,234.56",
        "23,456.78",
        "999,999.99",
    ]

    for amount_str in test_amounts:
        match = pattern.search(amount_str)
        assert match is not None, f"Should match amount '{amount_str}'"
        assert match.group(1) == amount_str, f"Should extract '{amount_str}', got '{match.group(1)}'"


@pytest.mark.unit
def test_amount_pattern_negative(extraction_service):
    """Test amount pattern matches negative amounts (credits/refunds)."""
    pattern = extraction_service.amount_pattern

    test_amounts = [
        "-15.50",
        "-1,234.56",
        "-100.00",
    ]

    for amount_str in test_amounts:
        match = pattern.search(amount_str)
        assert match is not None, f"Should match negative amount '{amount_str}'"
        assert match.group(1) == amount_str, f"Should extract '{amount_str}', got '{match.group(1)}'"


@pytest.mark.unit
def test_amount_pattern_with_dollar_sign(extraction_service):
    """Test amount pattern matches amounts with dollar sign."""
    pattern = extraction_service.amount_pattern

    test_cases = [
        ("$77.37", "$77.37"),
        ("$1,234.56", "$1,234.56"),
        ("-$15.50", "-$15.50"),
    ]

    for amount_str, expected in test_cases:
        match = pattern.search(amount_str)
        assert match is not None, f"Should match amount '{amount_str}'"
        assert match.group(1) == expected, f"Should extract '{expected}', got '{match.group(1)}'"


@pytest.mark.unit
def test_expense_type_pattern_all_categories(extraction_service):
    """Test expense type pattern matches all expected categories."""
    pattern = extraction_service.expense_type_pattern

    expected_types = [
        "Fuel",
        "Meals",
        "General Expense",
        "Hotel",
        "Legal",
        "Maintenance",
        "Misc. Transportation",
        "Business Services",
    ]

    for expense_type in expected_types:
        match = pattern.search(expense_type)
        assert match is not None, f"Should match expense type '{expense_type}'"
        assert match.group(1) == expense_type, f"Should extract '{expense_type}', got '{match.group(1)}'"


@pytest.mark.unit
def test_transaction_pattern_complete_line(extraction_service):
    """Test master transaction pattern matches complete transaction line."""
    pattern = extraction_service.transaction_pattern

    # Tab-separated transaction line
    transaction_line = "RICHARDBREEDLOVE\tFuel\t03/24/2025\t77.37\tCHEVRON 0308017\t27952 WALKER SOUTH\tComplete"

    match = pattern.search(transaction_line)

    assert match is not None, "Should match complete transaction line"

    # Verify all groups are captured
    assert match.group(1).strip() == "RICHARDBREEDLOVE", "Should extract employee name"
    assert match.group(2).strip() == "Fuel", "Should extract expense type"
    assert match.group(3).strip() == "03/24/2025", "Should extract date"
    assert match.group(4).strip() == "77.37", "Should extract amount"
    assert match.group(5).strip() == "CHEVRON 0308017", "Should extract merchant name"
    assert match.group(6).strip() == "27952 WALKER SOUTH", "Should extract merchant address"
    assert match.group(7).strip() == "Complete", "Should extract status"


@pytest.mark.unit
def test_transaction_pattern_with_negative_amount(extraction_service):
    """Test transaction pattern matches lines with negative amounts."""
    pattern = extraction_service.transaction_pattern

    transaction_line = "JOHNSMITH\tGeneral Expense\t03/26/2025\t-25.50\tAMAZON REFUND\t123 MAIN ST\tComplete"

    match = pattern.search(transaction_line)

    assert match is not None, "Should match transaction with negative amount"
    assert match.group(4).strip() == "-25.50", "Should extract negative amount"


@pytest.mark.unit
def test_parse_date_helper_with_leading_zeros(extraction_service):
    """Test _parse_date helper method with leading zeros."""
    test_cases = [
        ("03/24/2025", (2025, 3, 24)),
        ("12/31/2025", (2025, 12, 31)),
        ("01/01/2026", (2026, 1, 1)),
    ]

    for date_str, (year, month, day) in test_cases:
        result = extraction_service._parse_date(date_str)
        assert result is not None, f"Should parse date '{date_str}'"
        assert result.year == year, f"Year should be {year}"
        assert result.month == month, f"Month should be {month}"
        assert result.day == day, f"Day should be {day}"


@pytest.mark.unit
def test_parse_date_helper_without_leading_zeros(extraction_service):
    """Test _parse_date helper method without leading zeros."""
    test_cases = [
        ("3/5/2025", (2025, 3, 5)),
        ("12/1/2025", (2025, 12, 1)),
        ("1/15/2025", (2025, 1, 15)),
    ]

    for date_str, (year, month, day) in test_cases:
        result = extraction_service._parse_date(date_str)
        assert result is not None, f"Should parse date '{date_str}'"
        assert result.year == year, f"Year should be {year}"
        assert result.month == month, f"Month should be {month}"
        assert result.day == day, f"Day should be {day}"


@pytest.mark.unit
def test_parse_date_helper_returns_none_for_invalid(extraction_service):
    """Test _parse_date returns None for invalid dates."""
    invalid_dates = [
        "invalid",
        "13/32/2025",  # Invalid month/day
        "",
        None,
    ]

    for date_str in invalid_dates:
        result = extraction_service._parse_date(date_str)
        assert result is None, f"Should return None for invalid date '{date_str}'"


@pytest.mark.unit
def test_parse_amount_helper_simple(extraction_service):
    """Test _parse_amount helper with simple amounts."""
    test_cases = [
        ("77.37", Decimal("77.37")),
        ("100.00", Decimal("100.00")),
        ("1.50", Decimal("1.50")),
    ]

    for amount_str, expected in test_cases:
        result = extraction_service._parse_amount(amount_str)
        assert result is not None, f"Should parse amount '{amount_str}'"
        assert result == expected, f"Should be {expected}, got {result}"


@pytest.mark.unit
def test_parse_amount_helper_with_commas(extraction_service):
    """Test _parse_amount helper removes commas correctly."""
    test_cases = [
        ("1,234.56", Decimal("1234.56")),
        ("23,456.78", Decimal("23456.78")),
        ("999,999.99", Decimal("999999.99")),
    ]

    for amount_str, expected in test_cases:
        result = extraction_service._parse_amount(amount_str)
        assert result is not None, f"Should parse amount '{amount_str}'"
        assert result == expected, f"Should be {expected}, got {result}"


@pytest.mark.unit
def test_parse_amount_helper_negative(extraction_service):
    """Test _parse_amount helper with negative amounts."""
    test_cases = [
        ("-15.50", Decimal("-15.50")),
        ("-1,234.56", Decimal("-1234.56")),
        ("-$25.00", Decimal("-25.00")),
    ]

    for amount_str, expected in test_cases:
        result = extraction_service._parse_amount(amount_str)
        assert result is not None, f"Should parse negative amount '{amount_str}'"
        assert result == expected, f"Should be {expected}, got {result}"


@pytest.mark.unit
def test_parse_amount_helper_with_dollar_sign(extraction_service):
    """Test _parse_amount helper removes dollar signs."""
    test_cases = [
        ("$77.37", Decimal("77.37")),
        ("$1,234.56", Decimal("1234.56")),
    ]

    for amount_str, expected in test_cases:
        result = extraction_service._parse_amount(amount_str)
        assert result is not None, f"Should parse amount '{amount_str}'"
        assert result == expected, f"Should be {expected}, got {result}"


@pytest.mark.unit
def test_parse_amount_helper_returns_none_for_invalid(extraction_service):
    """Test _parse_amount returns None for invalid amounts."""
    invalid_amounts = [
        "invalid",
        "abc.def",
        "",
        None,
    ]

    for amount_str in invalid_amounts:
        result = extraction_service._parse_amount(amount_str)
        assert result is None, f"Should return None for invalid amount '{amount_str}'"
