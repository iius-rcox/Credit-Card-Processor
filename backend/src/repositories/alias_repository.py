"""
AliasRepository - Data access layer for EmployeeAlias entities.

This module provides CRUD operations and employee name resolution
for EmployeeAlias records.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.employee_alias import EmployeeAlias
from ..models.employee import Employee


class AliasRepository:
    """
    Repository for EmployeeAlias entity operations.

    Provides methods for creating, retrieving, deleting aliases and
    resolving employee IDs from extracted names.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_alias(self, extracted_name: str, employee_id: UUID) -> EmployeeAlias:
        """
        Create a new employee alias.

        Args:
            extracted_name: Employee name as it appears in PDF
            employee_id: UUID of the employee to map to

        Returns:
            Created EmployeeAlias instance

        Raises:
            IntegrityError: If extracted_name already exists (unique constraint)

        Example:
            alias = await repo.create_alias("JOHNSMITH", employee_id)
        """
        alias = EmployeeAlias(
            extracted_name=extracted_name,
            employee_id=employee_id
        )
        self.db.add(alias)
        await self.db.flush()
        await self.db.refresh(alias)
        return alias

    async def get_all_aliases(self) -> List[EmployeeAlias]:
        """
        Get all employee aliases with joined employee data.

        Returns:
            List of EmployeeAlias instances with employee relationship loaded

        Example:
            aliases = await repo.get_all_aliases()
            for alias in aliases:
                print(f"{alias.extracted_name} -> {alias.employee.name}")
        """
        stmt = (
            select(EmployeeAlias)
            .options(joinedload(EmployeeAlias.employee))
            .order_by(EmployeeAlias.extracted_name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_alias_by_extracted_name(self, name: str) -> Optional[EmployeeAlias]:
        """
        Lookup alias by extracted name.

        Args:
            name: Extracted employee name from PDF

        Returns:
            EmployeeAlias instance if found, None otherwise

        Example:
            alias = await repo.get_alias_by_extracted_name("JOHNSMITH")
            if alias:
                employee_id = alias.employee_id
        """
        stmt = select(EmployeeAlias).where(EmployeeAlias.extracted_name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_alias(self, alias_id: UUID) -> bool:
        """
        Delete an employee alias.

        Args:
            alias_id: UUID of the alias to delete

        Returns:
            True if alias was deleted, False if not found

        Example:
            deleted = await repo.delete_alias(alias_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Alias not found")
        """
        stmt = select(EmployeeAlias).where(EmployeeAlias.id == alias_id)
        result = await self.db.execute(stmt)
        alias = result.scalar_one_or_none()

        if alias is None:
            return False

        await self.db.delete(alias)
        await self.db.flush()
        return True

    async def resolve_employee_id(self, extracted_name: str) -> Optional[UUID]:
        """
        Resolve employee ID from extracted name.

        Tries exact match on employees.name first, then alias lookup.

        Args:
            extracted_name: Employee name from PDF

        Returns:
            Employee UUID if found (via direct match or alias), None otherwise

        Example:
            employee_id = await repo.resolve_employee_id("JOHNSMITH")
            if employee_id is None:
                # User needs to create an alias
        """
        # Step 1: Try exact match on Employee.name
        employee_stmt = select(Employee).where(Employee.name == extracted_name)
        employee_result = await self.db.execute(employee_stmt)
        employee = employee_result.scalar_one_or_none()

        if employee:
            return employee.id

        # Step 2: Try alias lookup
        alias_stmt = select(EmployeeAlias).where(EmployeeAlias.extracted_name == extracted_name)
        alias_result = await self.db.execute(alias_stmt)
        alias = alias_result.scalar_one_or_none()

        if alias:
            return alias.employee_id

        # Step 3: Not found
        return None
