"""
Employee Alias API endpoints.

Provides REST API for managing employee name aliases used during
PDF extraction to resolve employee names.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.dependencies import get_db
from ...api.schemas import (
    EmployeeAliasCreate,
    EmployeeAliasResponse,
    AliasListResponse,
    EmployeeAliasWithEmployee,
    EmployeeInfo
)
from ...services.alias_service import AliasService
from ...models.employee_alias import EmployeeAlias

router = APIRouter(prefix="/api/aliases", tags=["aliases"])


@router.post(
    "",
    response_model=EmployeeAliasResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee alias",
    description="Maps an extracted employee name from PDF to an existing employee record"
)
async def create_alias(
    alias_data: EmployeeAliasCreate,
    db: AsyncSession = Depends(get_db)
) -> EmployeeAliasResponse:
    """
    Create a new employee alias.

    Args:
        alias_data: Alias creation data (extractedName, employeeId)
        db: Database session

    Returns:
        Created alias with id and createdAt

    Raises:
        HTTPException 400: If alias with extractedName already exists
        HTTPException 404: If employeeId not found
    """
    service = AliasService(db)

    try:
        alias = await service.create_alias(
            extracted_name=alias_data.extractedName,
            employee_id=alias_data.employeeId
        )

        return EmployeeAliasResponse(
            id=alias.id,
            extractedName=alias.extracted_name,
            employeeId=alias.employee_id,
            createdAt=alias.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alias: {str(e)}"
        )


@router.get(
    "",
    response_model=AliasListResponse,
    summary="List all employee aliases",
    description="Returns all employee name aliases with their associated employee details"
)
async def get_aliases(
    db: AsyncSession = Depends(get_db)
) -> AliasListResponse:
    """
    Get all employee aliases.

    Args:
        db: Database session

    Returns:
        List of aliases with employee details
    """
    service = AliasService(db)

    try:
        aliases_data = await service.get_all_aliases()

        # Convert to EmployeeAliasWithEmployee objects
        aliases = [
            EmployeeAliasWithEmployee(
                id=UUID(alias_dict["id"]),
                extractedName=alias_dict["extractedName"],
                employeeId=UUID(alias_dict["employeeId"]),
                createdAt=datetime.fromisoformat(alias_dict["createdAt"]),
                employee=EmployeeInfo(**alias_dict["employee"])
            )
            for alias_dict in aliases_data
        ]

        return AliasListResponse(aliases=aliases)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve aliases: {str(e)}"
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee alias",
    description="Removes an employee alias mapping"
)
async def delete_alias(
    id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an employee alias.

    Args:
        id: UUID of the alias to delete
        db: Database session

    Raises:
        HTTPException 404: If alias not found
    """
    service = AliasService(db)

    try:
        await service.delete_alias(id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alias: {str(e)}"
        )
