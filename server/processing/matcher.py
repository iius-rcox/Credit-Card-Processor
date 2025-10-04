"""
Expense-to-receipt matching logic.

Implements the matching algorithm defined in the feature specification:
Match by employee_id + exact amount comparison.
"""

from typing import List
from decimal import Decimal

from api.models import Employee, ExpenseTransaction, ReceiptRecord, MatchingResult, MatchReason


def match_expenses_to_receipts(employees: List[Employee]) -> List[MatchingResult]:
    """
    Match expense transactions to receipt records for all employees.

    Algorithm (from spec clarification):
    For each expense, find receipts WHERE:
      - receipt.employee_id = expense.employee_id AND
      - receipt.amount = expense.transaction_amount (exact match)

    If 1 match:  exact_match, set has_gl_code from receipt
    If 0 matches: no_receipt_found
    If 2+ matches: multiple_matches (ambiguous, cannot auto-match)

    Args:
        employees: List of Employee objects with expenses and receipts

    Returns:
        List of MatchingResult objects for all expenses

    Side effects:
        Updates expense.has_receipt and expense.has_gl_code fields
    """
    all_matching_results = []

    for employee in employees:
        # Process each expense for this employee
        for expense in employee.expenses:
            # Find matching receipts by amount
            matching_receipts = [
                receipt
                for receipt in employee.receipts
                if receipt.amount == expense.transaction_amount
            ]

            # Determine match result based on count
            if len(matching_receipts) == 1:
                # Exact match - one receipt found
                matched_receipt = matching_receipts[0]

                expense.has_receipt = True

                # Check if receipt has GL or project code
                expense.has_gl_code = bool(matched_receipt.gl_code or matched_receipt.project_code)

                # If expense has its own gl_account, also consider that
                if expense.gl_account:
                    expense.has_gl_code = True

                matching_result = MatchingResult(
                    expense_transaction_id=expense.transaction_id,
                    matched_receipt_id=matched_receipt.receipt_id,
                    has_gl_code=expense.has_gl_code,
                    match_reason=MatchReason.EXACT_MATCH,
                )

            elif len(matching_receipts) == 0:
                # No receipt found
                expense.has_receipt = False

                # Check if expense itself has gl_account
                expense.has_gl_code = bool(expense.gl_account)

                matching_result = MatchingResult(
                    expense_transaction_id=expense.transaction_id,
                    matched_receipt_id=None,
                    has_gl_code=expense.has_gl_code,
                    match_reason=MatchReason.NO_RECEIPT_FOUND,
                )

            else:
                # Multiple matches - ambiguous
                expense.has_receipt = False  # Cannot auto-match
                expense.has_gl_code = bool(expense.gl_account)

                matching_result = MatchingResult(
                    expense_transaction_id=expense.transaction_id,
                    matched_receipt_id=None,
                    has_gl_code=expense.has_gl_code,
                    match_reason=MatchReason.MULTIPLE_MATCHES,
                )

            all_matching_results.append(matching_result)

    return all_matching_results


def find_matching_receipt(
    expense: ExpenseTransaction, receipts: List[ReceiptRecord]
) -> ReceiptRecord | None:
    """
    Find single matching receipt for an expense.

    Args:
        expense: ExpenseTransaction to match
        receipts: List of ReceiptRecords to search

    Returns:
        ReceiptRecord if exactly one match found, None otherwise
    """
    matching = [r for r in receipts if r.amount == expense.transaction_amount]

    return matching[0] if len(matching) == 1 else None


def has_ambiguous_match(expense: ExpenseTransaction, receipts: List[ReceiptRecord]) -> bool:
    """
    Check if expense has multiple matching receipts (ambiguous).

    Args:
        expense: ExpenseTransaction to check
        receipts: List of ReceiptRecords to search

    Returns:
        True if 2 or more receipts have the same amount
    """
    matching = [r for r in receipts if r.amount == expense.transaction_amount]

    return len(matching) > 1
