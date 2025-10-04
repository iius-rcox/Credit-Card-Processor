"""
Completion analysis utilities.

Analyzes employee expense completion status and computes summary statistics.
"""

from typing import Dict
from api.models import Employee, Session, CompletionStatus


def analyze_employee_completion(employee: Employee) -> str:
    """
    Analyze whether an employee has all expenses complete.

    Logic (from spec):
    Returns "complete" IFF all expenses have has_receipt=True AND has_gl_code=True.
    Otherwise returns "incomplete".

    Args:
        employee: Employee object with expenses

    Returns:
        "complete" or "incomplete"

    Note:
        This function returns the computed value. The Employee model
        has a @computed_field property that performs the same logic.
        This standalone function is useful for testing and explicit checks.
    """
    if not employee.expenses:
        # No expenses = incomplete (nothing to export)
        return CompletionStatus.INCOMPLETE.value

    # Check if ALL expenses are complete
    all_complete = all(
        expense.has_receipt and expense.has_gl_code for expense in employee.expenses
    )

    return CompletionStatus.COMPLETE.value if all_complete else CompletionStatus.INCOMPLETE.value


def compute_summary_stats(session: Session) -> Dict:
    """
    Compute summary statistics for a session.

    Returns:
        Dictionary with keys:
        - total_employees: int
        - complete_employees: int
        - incomplete_employees: int
        - total_expenses: int
        - complete_expenses: int
        - expenses_missing_receipts: int
        - expenses_missing_gl_codes: int
        - expenses_missing_both: int

    Example:
        >>> summary = compute_summary_stats(session)
        >>> print(f"{summary['complete_employees']} out of {summary['total_employees']} complete")
    """
    total_employees = len(session.employees)

    # Count complete employees
    complete_employees = sum(
        1 for emp in session.employees if emp.completion_status == CompletionStatus.COMPLETE
    )

    incomplete_employees = total_employees - complete_employees

    # Count all expenses across all employees
    all_expenses = []
    for employee in session.employees:
        all_expenses.extend(employee.expenses)

    total_expenses = len(all_expenses)

    # Count expenses by status
    complete_expenses = sum(1 for exp in all_expenses if exp.status.value == "Complete")

    expenses_missing_receipts = sum(
        1 for exp in all_expenses if exp.status.value == "Missing Receipt"
    )

    expenses_missing_gl_codes = sum(
        1 for exp in all_expenses if exp.status.value == "Missing GL Code"
    )

    expenses_missing_both = sum(1 for exp in all_expenses if exp.status.value == "Missing Both")

    return {
        "total_employees": total_employees,
        "complete_employees": complete_employees,
        "incomplete_employees": incomplete_employees,
        "total_expenses": total_expenses,
        "complete_expenses": complete_expenses,
        "expenses_missing_receipts": expenses_missing_receipts,
        "expenses_missing_gl_codes": expenses_missing_gl_codes,
        "expenses_missing_both": expenses_missing_both,
    }


def get_complete_employees(session: Session) -> List[Employee]:
    """
    Get list of employees with 100% complete expenses.

    These employees are eligible for CSV export.

    Args:
        session: Session object

    Returns:
        List of Employee objects where completion_status = "complete"
    """
    return [emp for emp in session.employees if emp.completion_status == CompletionStatus.COMPLETE]


def get_incomplete_expenses(session: Session) -> List[ExpenseTransaction]:
    """
    Get all expenses that are not complete.

    These expenses appear in the Excel report.

    Args:
        session: Session object

    Returns:
        List of ExpenseTransaction objects where status != "Complete"
    """
    incomplete = []

    for employee in session.employees:
        for expense in employee.expenses:
            if expense.status.value != "Complete":
                incomplete.append(expense)

    return incomplete


def count_employees_by_completion(session: Session) -> Dict[str, int]:
    """
    Count employees grouped by completion status.

    Args:
        session: Session object

    Returns:
        Dictionary with "complete" and "incomplete" counts
    """
    complete_count = sum(
        1 for emp in session.employees if emp.completion_status == CompletionStatus.COMPLETE
    )

    incomplete_count = len(session.employees) - complete_count

    return {"complete": complete_count, "incomplete": incomplete_count}
