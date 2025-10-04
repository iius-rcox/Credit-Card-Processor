"""
Unit tests for validation utilities (T049).

Tests all validator functions with valid and invalid inputs.
"""

import pytest
from processing.validator import (
    validate_employee_id,
    validate_uuid,
    validate_card_number,
    validate_amount,
)


class TestEmployeeIdValidator:
    """Test validate_employee_id function."""

    def test_valid_employee_ids(self):
        """Test valid employee ID patterns."""
        valid_ids = [
            "EMP123",
            "emp456",  # Case insensitive
            "EMP_001",  # With underscore
            "EMP-002",  # With hyphen
            "E001",  # 4 chars minimum
            "EMP789",  # 6 chars maximum
            "A1B2C3",  # Mix of letters and numbers
        ]

        for emp_id in valid_ids:
            assert validate_employee_id(emp_id), f"{emp_id} should be valid"

    def test_invalid_employee_ids(self):
        """Test invalid employee ID patterns."""
        invalid_ids = [
            "",  # Empty
            "EMP",  # Too short (< 4 chars)
            "EMPLOYEE1234",  # Too long (> 6 chars)
            "EMP@123",  # Invalid character (@)
            "EMP 123",  # Contains space
            "EMP.123",  # Invalid character (.)
            None,  # None
        ]

        for emp_id in invalid_ids:
            assert not validate_employee_id(emp_id), f"{emp_id} should be invalid"


class TestUUIDValidator:
    """Test validate_uuid function."""

    def test_valid_uuids(self):
        """Test valid UUID formats."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",  # Lowercase
            "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
            "12345678-1234-1234-1234-123456789012",  # Different values
        ]

        for uuid_str in valid_uuids:
            assert validate_uuid(uuid_str), f"{uuid_str} should be valid"

    def test_invalid_uuids(self):
        """Test invalid UUID formats."""
        invalid_uuids = [
            "",  # Empty
            "not-a-uuid",  # Invalid format
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "550e8400e29b41d4a716446655440000",  # No hyphens
            "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character (g)
            None,  # None
        ]

        for uuid_str in invalid_uuids:
            assert not validate_uuid(uuid_str), f"{uuid_str} should be invalid"


class TestCardNumberValidator:
    """Test validate_card_number function."""

    def test_valid_16_digit_format(self):
        """Test valid 16 consecutive digit card numbers."""
        valid_cards = [
            "1234567890123456",
            "4111111111111111",  # Visa test card
            "5500000000000004",  # Mastercard test card
        ]

        for card in valid_cards:
            assert validate_card_number(card), f"{card} should be valid"

    def test_valid_4_4_4_4_format(self):
        """Test valid 4-4-4-4 hyphenated format."""
        valid_cards = [
            "1234-5678-9012-3456",
            "4111-1111-1111-1111",
            "5500-0000-0000-0004",
        ]

        for card in valid_cards:
            assert validate_card_number(card), f"{card} should be valid"

    def test_valid_masked_format(self):
        """Test valid masked format (12 asterisks + 4 digits)."""
        valid_cards = [
            "************1234",
            "************0000",
            "************9999",
        ]

        for card in valid_cards:
            assert validate_card_number(card), f"{card} should be valid"

    def test_invalid_card_numbers(self):
        """Test invalid card number formats."""
        invalid_cards = [
            "",  # Empty
            "123456789012345",  # 15 digits (too short)
            "12345678901234567",  # 17 digits (too long)
            "1234-5678-9012-345",  # Wrong format (last group only 3)
            "***********1234",  # 11 asterisks (need 12)
            "*************1234",  # 13 asterisks (too many)
            "abcd-efgh-ijkl-mnop",  # Letters instead of digits
            "1234 5678 9012 3456",  # Spaces instead of hyphens
            None,  # None
        ]

        for card in invalid_cards:
            assert not validate_card_number(card), f"{card} should be invalid"


class TestAmountValidator:
    """Test validate_amount function."""

    def test_valid_amounts_with_two_decimals(self):
        """Test valid amounts with exactly 2 decimal places."""
        valid_amounts = [
            125.50,
            0.01,  # Minimum positive
            999999.99,  # Large amount
            "125.50",  # String format
            "$125.50",  # With dollar sign
            "1,250.50",  # With comma
        ]

        for amount in valid_amounts:
            assert validate_amount(amount), f"{amount} should be valid"

    def test_invalid_amounts_wrong_decimals(self):
        """Test amounts with wrong number of decimal places."""
        # With require_two_decimals=True (default)
        invalid_amounts = [
            125.5,  # Only 1 decimal
            125,  # No decimals
            "125.500",  # 3 decimals
            "125.5",  # 1 decimal as string
        ]

        for amount in invalid_amounts:
            assert not validate_amount(amount), f"{amount} should be invalid (needs 2 decimals)"

    def test_invalid_amounts_negative_or_zero(self):
        """Test negative or zero amounts."""
        invalid_amounts = [
            0.00,
            -125.50,
            "-125.50",
        ]

        for amount in invalid_amounts:
            assert not validate_amount(amount), f"{amount} should be invalid (must be positive)"

    def test_amount_without_decimal_requirement(self):
        """Test amounts when decimal requirement is disabled."""
        valid_amounts = [
            125,
            125.5,
            "125",
            "$125",
        ]

        for amount in valid_amounts:
            assert validate_amount(amount, require_two_decimals=False), (
                f"{amount} should be valid without decimal requirement"
            )

    def test_invalid_amount_formats(self):
        """Test completely invalid amount formats."""
        invalid_amounts = [
            "",
            "abc",
            "12.34.56",
            None,
        ]

        for amount in invalid_amounts:
            assert not validate_amount(amount), f"{amount} should be invalid"
