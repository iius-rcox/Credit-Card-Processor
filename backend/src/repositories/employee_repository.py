"""
EmployeeRepository - Data access layer for Employee entities.

This module provides CRUD operations and queries for Employee records.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.employee import Employee


class EmployeeRepository:
    """
    Repository for Employee entity operations.

    Provides methods for creating, retrieving, and bulk operations on employees.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_employee(self, session_id: UUID, data: dict) -> Employee:
        """
        Create a new employee.

        Args:
            session_id: UUID of the parent session
            data: Dictionary with employee data (employee_number, name, etc.)

        Returns:
            Created Employee instance

        Example:
            employee = await repo.create_employee(
                session_id=uuid4(),
                data={
                    "employee_number": "E12345",
                    "name": "John Doe",
                    "department": "Engineering",
                    "cost_center": "CC-001"
                }
            )
        """
        employee_data = {"session_id": session_id, **data}
        employee = Employee(**employee_data)
        self.db.add(employee)
        await self.db.flush()
        await self.db.refresh(employee)
        return employee

    async def bulk_create_employees(
        self, session_id: UUID, employees: list[dict]
    ) -> list[Employee]:
        """
        Bulk create employees (batch insert).

        Args:
            session_id: UUID of the parent session
            employees: List of employee data dictionaries

        Returns:
            List of created Employee instances

        Example:
            employees = await repo.bulk_create_employees(
                session_id=uuid4(),
                employees=[
                    {"employee_number": "E001", "name": "Alice"},
                    {"employee_number": "E002", "name": "Bob"}
                ]
            )
        """
        employee_objects = [
            Employee(session_id=session_id, **emp_data)
            for emp_data in employees
        ]
        self.db.add_all(employee_objects)
        await self.db.flush()

        # Refresh all objects to get generated IDs
        for emp in employee_objects:
            await self.db.refresh(emp)

        return employee_objects

    async def get_employees_by_session(self, session_id: UUID) -> list[Employee]:
        """
        Get all employees for a session.

        Args:
            session_id: UUID of the session

        Returns:
            List of Employee instances

        Example:
            employees = await repo.get_employees_by_session(session_id)
        """
        stmt = (
            select(Employee)
            .where(Employee.session_id == session_id)
            .order_by(Employee.employee_number)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_employee_by_number(
        self, session_id: UUID, employee_number: str
    ) -> Optional[Employee]:
        """
        Get employee by unique employee number within a session.

        Args:
            session_id: UUID of the session
            employee_number: Employee identifier

        Returns:
            Employee instance if found, None otherwise

        Example:
            employee = await repo.get_employee_by_number(session_id, "E12345")
        """
        stmt = (
            select(Employee)
            .where(Employee.session_id == session_id)
            .where(Employee.employee_number == employee_number)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_employee_by_id(self, employee_id: UUID) -> Optional[Employee]:
        """
        Get employee by ID.

        Args:
            employee_id: UUID of the employee

        Returns:
            Employee instance if found, None otherwise
        """
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
