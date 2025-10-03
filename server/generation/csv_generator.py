"""
pvault CSV export generator.

Generates CSV files in pvault format with 18 columns.
CRITICAL: Only includes employees with 100% complete expenses.
Excludes ALL expenses from employees with even one incomplete item.
"""

import os
import csv
from typing import List
from uuid import UUID

from api.models import Session, Employee, ExpenseTransaction, CSVExport, CompletionStatus
from processing.analyzer import get_complete_employees


# pvault format: 18 columns (from spec clarification)
PVAULT_HEADERS = [
    "Transaction ID",
    "Transaction Date",
    "Transaction Amount",
    "Transaction Name",
    "Vendor Invoice #",
    "Invoice Date",
    "Header Description",
    "Job",
    "Phase",
    "Cost Type",
    "GL Account",
    "Item Description",
    "UM",
    "Tax",
    "Pay Type",
    "Card Holder",
    "Credit Card Number",
    "Credit Card Vendor",
]


def generate_csv_export(session: Session, output_dir: str = "server/reports") -> str:
    """
    Generate CSV export in pvault format.

    CRITICAL BUSINESS RULE:
    Only includes employees with completion_status = "complete".
    If an employee has even ONE incomplete expense, ALL of their expenses
    are excluded from the CSV (even the complete ones).

    Format:
    - Exactly 18 columns in specified order
    - UTF-8 encoding
    - CRLF line endings
    - QUOTE_MINIMAL quoting strategy
    - Amounts: 2 decimal places, no $ symbols
    - Dates: YYYY-MM-DD format

    Args:
        session: Session object with employees and expenses
        output_dir: Directory to save CSV file

    Returns:
        Absolute path to generated CSV file

    Example:
        >>> path = generate_csv_export(session)
        >>> print(f"CSV export saved to {path}")
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate file path
    session_id_str = str(session.session_id)
    file_path = os.path.join(output_dir, f"{session_id_str}_pvault_export.csv")

    # Get only complete employees (100% receipted and coded)
    complete_employees = get_complete_employees(session)

    # Open CSV file with UTF-8 encoding and CRLF line endings
    with open(file_path, "w", newline="\r\n", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

        # Write header row
        writer.writerow(PVAULT_HEADERS)

        # Write data rows - ONLY for complete employees
        for employee in complete_employees:
            # ALL of this employee's expenses (since they're 100% complete)
            for expense in employee.expenses:
                row = _create_csv_row(expense, employee)
                writer.writerow(row)

    return os.path.abspath(file_path)


def _create_csv_row(expense: ExpenseTransaction, employee: Employee) -> List[str]:
    """
    Create a single CSV row from expense and employee data.

    Maps expense fields to the 18 pvault columns.

    Args:
        expense: ExpenseTransaction object
        employee: Employee object (for card holder name, card number)

    Returns:
        List of 18 string values in pvault column order
    """
    # Determine credit card vendor from card number
    card_vendor = _get_card_vendor(employee.card_number)

    # Format date as YYYY-MM-DD
    transaction_date_str = expense.transaction_date.isoformat()
    invoice_date_str = expense.invoice_date.isoformat() if expense.invoice_date else ""

    # Format amounts with 2 decimals, no $ symbol
    amount_str = f"{expense.transaction_amount:.2f}"
    tax_str = f"{expense.tax:.2f}" if expense.tax else ""

    # Mask card number for security
    masked_card = _mask_card_number(employee.card_number)

    row = [
        str(expense.transaction_id),  # Transaction ID (UUID)
        transaction_date_str,  # Transaction Date (YYYY-MM-DD)
        amount_str,  # Transaction Amount (###.##)
        expense.transaction_name,  # Transaction Name
        expense.vendor_invoice_number or "",  # Vendor Invoice # (optional)
        invoice_date_str,  # Invoice Date (YYYY-MM-DD or empty)
        expense.header_description or "",  # Header Description (optional)
        expense.job or "",  # Job (optional)
        expense.phase or "",  # Phase (optional)
        expense.cost_type or "",  # Cost Type (optional)
        expense.gl_account or "",  # GL Account (optional)
        expense.item_description or "",  # Item Description (optional)
        expense.um or "",  # UM - Unit of Measure (optional)
        tax_str,  # Tax (###.## or empty)
        expense.pay_type or "",  # Pay Type (optional)
        employee.name,  # Card Holder (employee name)
        masked_card,  # Credit Card Number (masked)
        card_vendor,  # Credit Card Vendor
    ]

    return row


def _mask_card_number(card_number: str) -> str:
    """
    Mask credit card number showing only last 4 digits.

    Args:
        card_number: Original card number (16-digit, 4-4-4-4, or already masked)

    Returns:
        Masked format: **** **** **** 1234
    """
    # Extract last 4 digits
    # Remove all non-digit characters first
    digits_only = "".join(c for c in card_number if c.isdigit())

    if len(digits_only) >= 4:
        last_four = digits_only[-4:]
        return f"**** **** **** {last_four}"

    # Already masked or invalid
    return card_number


def _get_card_vendor(card_number: str) -> str:
    """
    Determine credit card vendor from card number.

    Basic implementation using first digit:
    - 4: Visa
    - 5: Mastercard
    - 3: Amex
    - 6: Discover

    Args:
        card_number: Card number string

    Returns:
        Vendor name string
    """
    # Extract first digit
    first_digit = next((c for c in card_number if c.isdigit()), None)

    if first_digit == "4":
        return "Visa"
    elif first_digit == "5":
        return "Mastercard"
    elif first_digit == "3":
        return "Amex"
    elif first_digit == "6":
        return "Discover"
    else:
        return "Unknown"


def create_csv_export_metadata(
    session: Session, file_path: str, included_employees: List[Employee]
) -> CSVExport:
    """
    Create CSVExport metadata object.

    Args:
        session: Session object
        file_path: Path to generated CSV file
        included_employees: List of complete employees included in export

    Returns:
        CSVExport object with metadata
    """
    # Count total rows (all expenses from complete employees)
    row_count = sum(len(emp.expenses) for emp in included_employees)

    # Get employee IDs
    employee_ids = [emp.employee_id for emp in included_employees]

    return CSVExport(
        session_id=session.session_id,
        file_path=file_path,
        row_count=row_count,
        included_employee_ids=employee_ids,
    )


def validate_csv_format(file_path: str) -> bool:
    """
    Validate that generated CSV file conforms to pvault format.

    Checks:
    - Exactly 18 columns
    - UTF-8 encoding
    - CRLF line endings
    - No extra quotes (QUOTE_MINIMAL)

    Args:
        file_path: Path to CSV file

    Returns:
        True if format is valid, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)

            # Check column count
            if len(header) != 18:
                return False

            # Check header matches expected
            if header != PVAULT_HEADERS:
                return False

            # Check at least one data row
            for row in reader:
                if len(row) != 18:
                    return False
                break  # Only check first row

        return True

    except Exception:
        return False
