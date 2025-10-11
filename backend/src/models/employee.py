"""
Employee model - Employee master data associated with a reconciliation session.

This module defines the Employee SQLAlchemy model representing employee information
extracted from credit card statements.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class Employee(Base):
    """
    Employee model representing employee master data.

    Each employee record is associated with a session and contains identifying
    information extracted from credit card statements. Employee numbers must
    be unique within a session.

    Attributes:
        id: Unique employee record identifier (UUID)
        session_id: Parent session reference (FK)
        employee_number: Employee identifier from source system
        name: Employee full name
        department: Department name (optional)
        cost_center: Cost center code (optional)
        created_at: Record creation timestamp
    """

    __tablename__ = "employees"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Foreign key to session
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Employee data
    employee_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    cost_center: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="employees"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="employee",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    aliases: Mapped[list["EmployeeAlias"]] = relationship(
        "EmployeeAlias",
        back_populates="employee",
        cascade="all, delete",
        passive_deletes=True
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "employee_number",
            name="uq_employees_session_employee"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.id}, employee_number={self.employee_number}, "
            f"name={self.name})>"
        )
