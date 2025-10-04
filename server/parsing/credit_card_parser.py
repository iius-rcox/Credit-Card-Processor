"""
Credit Card Statement PDF parser.

Extracts employee information and transaction data from credit card statements
using regex patterns specified in the feature requirements.
"""

import re
from typing import List
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

from api.models import Employee, ExpenseTransaction
from parsing.pdf_parser import extract_text_from_pdf


# Regex Patterns (as specified in user requirements)

# Employee Header Pattern: Captures Employee ID (4-6 digits), name, and card number
# Handles 16-digit, 4-4-4-4 formatted, and masked card numbers
EMPLOYEE_HEADER_PATTERN = re.compile(
    r"""
    (?P<employee_id>[A-Z0-9_-]{4,6})        # 4-6 alphanumeric + hyphens/underscores
    \s+                                      # Whitespace
    (?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)  # Name (First Last, handles middle names)
    \s+                                      # Whitespace
    (?P<card_number>
        \d{16}                               # 16 consecutive digits, OR
        |\d{4}-\d{4}-\d{4}-\d{4}             # 4-4-4-4 format, OR
        |\*{12}\d{4}                         # Masked format (12 asterisks + 4 digits)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Totals Marker Pattern: Matches "Totals For Card Nbr:" or "Totals For:"
TOTALS_MARKER_PATTERN = re.compile(
    r"Totals\s+For(?:\s+Card\s+Nbr)?:", re.IGNORECASE
)

# Transaction Totals Pattern: Captures dollar amounts
TRANSACTION_TOTALS_PATTERN = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")


def parse_credit_card_statement(pdf_path: str) -> List[Employee]:
    """
    Parse Credit Card Statement PDF to extract employees and their expense transactions.

    Args:
        pdf_path: Path to credit card statement PDF file

    Returns:
        List of Employee objects with expense transactions.
        Empty list if parsing fails.

    Algorithm:
        1. Extract text from all pages
        2. Find employee headers using EMPLOYEE_HEADER_PATTERN
        3. Extract transactions for each employee until next employee or totals
        4. Parse transaction amounts using TRANSACTION_TOTALS_PATTERN
        5. Return list of Employee objects

    Note:
        This is a simplified parser. Production implementation would need
        more sophisticated table extraction and transaction line parsing.
    """
    employees = []

    try:
        # Extract text from all pages
        page_texts = extract_text_from_pdf(pdf_path)

        if not page_texts:
            print(f"Failed to extract text from {pdf_path}")
            return []

        # Combine all pages for easier processing (handles multi-page tables)
        full_text = "\n".join(page_texts)

        # Find all employee headers
        employee_matches = list(EMPLOYEE_HEADER_PATTERN.finditer(full_text))

        if not employee_matches:
            print("No employees found in credit card statement")
            return []

        # Process each employee
        for i, match in enumerate(employee_matches):
            employee_id = match.group("employee_id").upper()
            name = match.group("name").strip()
            card_number = match.group("card_number")

            # Determine section boundaries
            section_start = match.end()

            # Find next employee or totals marker
            next_employee_pos = (
                employee_matches[i + 1].start() if i + 1 < len(employee_matches) else len(full_text)
            )

            # Find totals marker for this employee
            totals_match = TOTALS_MARKER_PATTERN.search(full_text, section_start, next_employee_pos)
            section_end = totals_match.start() if totals_match else next_employee_pos

            # Extract transaction section
            transaction_section = full_text[section_start:section_end]

            # Parse transactions (simplified - extract amounts for now)
            expenses = self._parse_transactions(transaction_section, employee_id)

            # Create Employee object
            employee = Employee(
                employee_id=employee_id,
                name=name,
                card_number=card_number,
                expenses=expenses,
                receipts=[],  # Receipts come from expense report, not CC statement
            )

            employees.append(employee)

        return employees

    except Exception as e:
        print(f"Error parsing credit card statement {pdf_path}: {e}")
        return []


def _parse_transactions(transaction_text: str, employee_id: str) -> List[ExpenseTransaction]:
    """
    Parse transaction lines from credit card statement section.

    This is a simplified implementation. Production version would:
    - Parse transaction dates
    - Extract merchant names
    - Handle transaction descriptions
    - Parse amounts more robustly

    Args:
        transaction_text: Text section containing transactions
        employee_id: Employee who owns these transactions

    Returns:
        List of ExpenseTransaction objects
    """
    expenses = []

    # For now, extract just the amounts as a placeholder
    # Production implementation would parse full transaction tables
    amount_matches = TRANSACTION_TOTALS_PATTERN.findall(transaction_text)

    for amount_str in amount_matches:
        # Clean amount string
        amount_clean = amount_str.replace(",", "").replace("$", "").strip()

        try:
            amount = Decimal(amount_clean)

            if amount > 0:
                # Create expense transaction
                # Note: Using placeholder data for fields not parsed yet
                expense = ExpenseTransaction(
                    transaction_id=uuid4(),
                    employee_id=employee_id,
                    transaction_date=datetime.now().date(),  # Placeholder
                    transaction_amount=amount,
                    transaction_name="Parsed Transaction",  # Placeholder
                    has_receipt=False,  # Will be set during matching
                    has_gl_code=False,  # Will be set during matching
                )

                expenses.append(expense)

        except (ValueError, ArithmeticError):
            # Skip invalid amounts
            continue

    return expenses


# Module-level function to avoid _parse_transactions being a method
def self._parse_transactions(transaction_text: str, employee_id: str) -> List[ExpenseTransaction]:
    """Wrapper to maintain compatibility."""
    return _parse_transactions(transaction_text, employee_id)
