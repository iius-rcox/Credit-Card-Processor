"""
TransactionRepository - Data access layer for Transaction entities.

This module provides CRUD operations and queries for Transaction records.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.transaction import Transaction


class TransactionRepository:
    """
    Repository for Transaction entity operations.

    Provides methods for creating, retrieving, and querying transactions.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_transaction(
        self, session_id: UUID, employee_id: UUID, data: dict
    ) -> Transaction:
        """
        Create a new transaction.

        Args:
            session_id: UUID of the parent session
            employee_id: UUID of the employee
            data: Dictionary with transaction data

        Returns:
            Created Transaction instance

        Example:
            transaction = await repo.create_transaction(
                session_id=uuid4(),
                employee_id=uuid4(),
                data={
                    "transaction_date": date(2025, 10, 1),
                    "amount": Decimal("125.50"),
                    "merchant_name": "Office Depot",
                    "description": "Office supplies"
                }
            )
        """
        transaction_data = {
            "session_id": session_id,
            "employee_id": employee_id,
            **data
        }
        transaction = Transaction(**transaction_data)
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)
        return transaction

    async def bulk_create_transactions(
        self, transactions: list[dict]
    ) -> list[Transaction]:
        """
        Bulk create transactions (batch insert).

        Args:
            transactions: List of transaction data dictionaries
                         (must include session_id and employee_id)

        Returns:
            List of created Transaction instances

        Example:
            transactions = await repo.bulk_create_transactions([
                {
                    "session_id": uuid4(),
                    "employee_id": uuid4(),
                    "transaction_date": date(2025, 10, 1),
                    "amount": Decimal("100.00"),
                    "merchant_name": "Store A"
                },
                ...
            ])
        """
        transaction_objects = [Transaction(**trans_data) for trans_data in transactions]
        self.db.add_all(transaction_objects)
        await self.db.flush()

        # Refresh all objects
        for trans in transaction_objects:
            await self.db.refresh(trans)

        return transaction_objects

    async def get_transactions_by_session(
        self, session_id: UUID, order_by: str = "transaction_date"
    ) -> list[Transaction]:
        """
        Get all transactions for a session.

        Args:
            session_id: UUID of the session
            order_by: Field to order by (default: transaction_date)

        Returns:
            List of Transaction instances ordered by specified field

        Example:
            transactions = await repo.get_transactions_by_session(
                session_id,
                order_by="amount"
            )
        """
        stmt = select(Transaction).where(Transaction.session_id == session_id)

        # Apply ordering
        if order_by == "transaction_date":
            stmt = stmt.order_by(Transaction.transaction_date.desc())
        elif order_by == "amount":
            stmt = stmt.order_by(Transaction.amount.desc())
        elif order_by == "merchant_name":
            stmt = stmt.order_by(Transaction.merchant_name)
        else:
            stmt = stmt.order_by(Transaction.transaction_date.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_transactions_by_employee(
        self, employee_id: UUID
    ) -> list[Transaction]:
        """
        Get all transactions for an employee.

        Args:
            employee_id: UUID of the employee

        Returns:
            List of Transaction instances

        Example:
            transactions = await repo.get_transactions_by_employee(employee_id)
        """
        stmt = (
            select(Transaction)
            .where(Transaction.employee_id == employee_id)
            .order_by(Transaction.transaction_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unmatched_transactions(self, session_id: UUID) -> list[Transaction]:
        """
        Get transactions without match results (unmatched transactions).

        Args:
            session_id: UUID of the session

        Returns:
            List of Transaction instances that don't have match results

        Example:
            unmatched = await repo.get_unmatched_transactions(session_id)
        """
        from ..models.match_result import MatchResult

        # Use LEFT JOIN to find transactions without match results
        stmt = (
            select(Transaction)
            .outerjoin(MatchResult, Transaction.id == MatchResult.transaction_id)
            .where(Transaction.session_id == session_id)
            .where(MatchResult.id.is_(None))
            .order_by(Transaction.transaction_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_transaction_by_id(
        self, transaction_id: UUID
    ) -> Optional[Transaction]:
        """
        Get transaction by ID.

        Args:
            transaction_id: UUID of the transaction

        Returns:
            Transaction instance if found, None otherwise
        """
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_transaction_with_relations(
        self, transaction_id: UUID
    ) -> Optional[Transaction]:
        """
        Get transaction by ID with eager loading of relationships.

        Args:
            transaction_id: UUID of the transaction

        Returns:
            Transaction instance with employee and match_result loaded
        """
        stmt = (
            select(Transaction)
            .where(Transaction.id == transaction_id)
            .options(
                selectinload(Transaction.employee),
                selectinload(Transaction.match_result)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
