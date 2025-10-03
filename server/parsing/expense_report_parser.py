"""
Expense Report PDF parser.

Extracts receipt records with GL/project codes from expense software reports.
"""

import re
from typing import Dict, List
from decimal import Decimal

from api.models import ReceiptRecord
from parsing.pdf_parser import extract_text_from_pdf


# Regex patterns for expense report parsing
RECEIPT_LINE_PATTERN = re.compile(
    r"""
    (?P<receipt_id>[A-Z0-9-]+)           # Receipt ID
    \s+
    (?P<employee_id>[A-Z0-9_-]{4,6})     # Employee ID
    \s+
    (?P<amount>\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)  # Amount
    \s*
    (?P<gl_code>[A-Z0-9-]+)?             # Optional GL code
    \s*
    (?P<project_code>[A-Z0-9-]+)?        # Optional project code
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_expense_report(pdf_path: str) -> Dict[str, List[ReceiptRecord]]:
    """
    Parse Expense Software Report PDF to extract receipt records.

    Args:
        pdf_path: Path to expense report PDF file

    Returns:
        Dictionary keyed by employee_id, values are lists of ReceiptRecords.
        Empty dict if parsing fails.

    Example:
        >>> receipts_by_employee = parse_expense_report("expense_report.pdf")
        >>> emp_receipts = receipts_by_employee.get("EMP123", [])
        >>> print(f"Employee EMP123 has {len(emp_receipts)} receipts")
    """
    receipts_by_employee: Dict[str, List[ReceiptRecord]] = {}

    try:
        # Extract text from all pages
        page_texts = extract_text_from_pdf(pdf_path)

        if not page_texts:
            print(f"Failed to extract text from {pdf_path}")
            return {}

        # Combine all pages
        full_text = "\n".join(page_texts)

        # Find all receipt lines
        receipt_matches = RECEIPT_LINE_PATTERN.finditer(full_text)

        for match in receipt_matches:
            receipt_id = match.group("receipt_id")
            employee_id = match.group("employee_id").upper()

            # Parse amount
            amount_str = match.group("amount").replace(",", "").replace("$", "").strip()

            try:
                amount = Decimal(amount_str)
            except (ValueError, ArithmeticError):
                # Skip invalid amounts
                continue

            # Extract codes (may be None)
            gl_code = match.group("gl_code")
            project_code = match.group("project_code")

            # Create ReceiptRecord
            receipt = ReceiptRecord(
                receipt_id=receipt_id,
                employee_id=employee_id,
                amount=amount,
                gl_code=gl_code if gl_code else None,
                project_code=project_code if project_code else None,
            )

            # Add to dictionary
            if employee_id not in receipts_by_employee:
                receipts_by_employee[employee_id] = []

            receipts_by_employee[employee_id].append(receipt)

        return receipts_by_employee

    except Exception as e:
        print(f"Error parsing expense report {pdf_path}: {e}")
        return {}


def has_gl_or_project_code(receipt: ReceiptRecord) -> bool:
    """
    Check if receipt has at least one code (GL or project).

    Args:
        receipt: ReceiptRecord to check

    Returns:
        True if receipt has gl_code or project_code
    """
    return bool(receipt.gl_code or receipt.project_code)
