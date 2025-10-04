"""
Validation utilities for data integrity.

Implements regex validators specified in user requirements:
- Employee ID validation
- UUID validation
- Card number validation
"""

import re


# Validation Patterns

# Employee ID Validation: Alphanumeric with hyphens/underscores (case-insensitive), 4-6 chars
EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Z0-9_-]{4,6}$", re.IGNORECASE)

# UUID Validation: 8-4-4-4-12 hexadecimal format (case-insensitive)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)

# Card Number Patterns: 16-digit, 4-4-4-4, or masked
CARD_NUMBER_PATTERNS = [
    re.compile(r"^\d{16}$"),  # 16 consecutive digits
    re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$"),  # 4-4-4-4 format
    re.compile(r"^\*{12}\d{4}$"),  # Masked format
]


def validate_employee_id(employee_id: str) -> bool:
    """
    Validate employee ID format.

    As specified in requirements: Ensures employee IDs are alphanumeric
    with hyphens/underscores (case-insensitive).

    Args:
        employee_id: Employee ID string to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_employee_id("EMP123")
        True
        >>> validate_employee_id("emp_001")
        True
        >>> validate_employee_id("EMP-456")
        True
        >>> validate_employee_id("EMP@123")
        False
    """
    if not employee_id:
        return False

    return bool(EMPLOYEE_ID_PATTERN.match(employee_id))


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.

    As specified in requirements: Validates UUIDs using the 8-4-4-4-12
    hexadecimal format (case-insensitive).

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format, False otherwise

    Examples:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> validate_uuid("550E8400-E29B-41D4-A716-446655440000")
        True
        >>> validate_uuid("not-a-uuid")
        False
    """
    if not uuid_str:
        return False

    return bool(UUID_PATTERN.match(uuid_str))


def validate_card_number(card_number: str) -> bool:
    """
    Validate credit card number format.

    Accepts three formats:
    1. 16 consecutive digits
    2. 4-4-4-4 format with hyphens
    3. Masked format (12 asterisks + 4 digits)

    Args:
        card_number: Card number string to validate

    Returns:
        True if matches one of the three valid formats, False otherwise

    Examples:
        >>> validate_card_number("1234567890123456")
        True
        >>> validate_card_number("1234-5678-9012-3456")
        True
        >>> validate_card_number("************3456")
        True
        >>> validate_card_number("invalid")
        False
    """
    if not card_number:
        return False

    # Check against all three accepted patterns
    for pattern in CARD_NUMBER_PATTERNS:
        if pattern.match(card_number):
            return True

    return False


def validate_amount(amount: float | str, require_two_decimals: bool = True) -> bool:
    """
    Validate dollar amount format.

    Args:
        amount: Amount value (float, Decimal, or string)
        require_two_decimals: If True, requires exactly 2 decimal places

    Returns:
        True if valid amount, False otherwise

    Examples:
        >>> validate_amount(125.50)
        True
        >>> validate_amount("125.5")
        False  # Only 1 decimal place
        >>> validate_amount("125.5", require_two_decimals=False)
        True
    """
    try:
        # Convert to string to check decimal places
        amount_str = str(amount)

        # Remove $ if present
        amount_str = amount_str.replace("$", "").replace(",", "").strip()

        # Parse as float
        amount_val = float(amount_str)

        # Must be positive
        if amount_val <= 0:
            return False

        # Check decimal places if required
        if require_two_decimals:
            if "." in amount_str:
                decimal_part = amount_str.split(".")[1]
                if len(decimal_part) != 2:
                    return False

        return True

    except (ValueError, AttributeError):
        return False
