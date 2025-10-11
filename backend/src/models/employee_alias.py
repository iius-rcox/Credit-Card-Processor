"""
EmployeeAlias model for mapping extracted PDF names to employees.

This model stores mappings between employee names as they appear in PDFs
and their corresponding employee records in the database.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .session import Base


class EmployeeAlias(Base):
    """
    Maps extracted employee names from PDFs to employee records.

    Attributes:
        id: Unique identifier (UUID)
        extracted_name: Employee name as it appears in PDF (unique)
        employee_id: Foreign key to employees table
        created_at: Timestamp when alias was created
        employee: Relationship to Employee model
    """

    __tablename__ = "employee_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extracted_name = Column(String(255), unique=True, nullable=False, index=True)
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationship to Employee
    employee = relationship("Employee", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<EmployeeAlias(id={self.id}, extracted_name='{self.extracted_name}', employee_id={self.employee_id})>"
