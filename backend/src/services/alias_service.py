"""
AliasService - Business logic for employee alias management.

This service handles creation, retrieval, deletion of employee aliases
and employee name resolution during PDF extraction.
"""

from typing import Optional, List, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.alias_repository import AliasRepository
from ..repositories.employee_repository import EmployeeRepository
from ..models.employee_alias import EmployeeAlias


class AliasService:
    """
    Service for managing employee aliases.

    Provides business logic for alias CRUD operations and employee resolution.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.alias_repo = AliasRepository(db)
        self.employee_repo = EmployeeRepository(db)

    async def create_alias(self, extracted_name: str, employee_id: UUID) -> EmployeeAlias:
        """
        Create a new employee alias.

        Args:
            extracted_name: Employee name as it appears in PDF
            employee_id: UUID of existing employee to map to

        Returns:
            Created EmployeeAlias instance

        Raises:
            HTTPException 404: If employee_id doesn't exist
            HTTPException 400: If extracted_name already exists (duplicate)

        Example:
            alias = await service.create_alias("JOHNSMITH", employee_uuid)
        """
        # Validate employee exists
        employee = await self.employee_repo.get_employee_by_id(employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail=f"Employee with ID {employee_id} not found")

        # Create alias (handle duplicates)
        try:
            alias = await self.alias_repo.create_alias(extracted_name, employee_id)
            await self.db.commit()
            return alias
        except IntegrityError as e:
            await self.db.rollback()
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Alias with extracted name '{extracted_name}' already exists"
                )
            raise

    async def get_all_aliases(self) -> List[Dict]:
        """
        Get all employee aliases with employee details.

        Returns:
            List of alias dictionaries with employee information

        Example:
            aliases = await service.get_all_aliases()
            # Returns: [{"id": ..., "extractedName": ..., "employee": {...}}]
        """
        aliases = await self.alias_repo.get_all_aliases()

        # Convert to DTOs with employee details
        result = []
        for alias in aliases:
            alias_dict = {
                "id": str(alias.id),
                "extractedName": alias.extracted_name,
                "employeeId": str(alias.employee_id),
                "createdAt": alias.created_at.isoformat(),
                "employee": {
                    "name": alias.employee.name,
                    "email": getattr(alias.employee, 'email', None)
                }
            }
            result.append(alias_dict)

        return result

    async def delete_alias(self, alias_id: UUID) -> None:
        """
        Delete an employee alias.

        Args:
            alias_id: UUID of the alias to delete

        Raises:
            HTTPException 404: If alias not found

        Example:
            await service.delete_alias(alias_uuid)
        """
        deleted = await self.alias_repo.delete_alias(alias_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Alias with ID {alias_id} not found")

        await self.db.commit()

    async def resolve_employee(self, extracted_name: str) -> Optional[UUID]:
        """
        Resolve employee ID from extracted name.

        Tries exact match on employees table first, then alias lookup.

        Args:
            extracted_name: Employee name from PDF

        Returns:
            Employee UUID if found, None otherwise

        Example:
            employee_id = await service.resolve_employee("JOHNSMITH")
            if employee_id is None:
                # Need to create alias or mark as incomplete
        """
        return await self.alias_repo.resolve_employee_id(extracted_name)
