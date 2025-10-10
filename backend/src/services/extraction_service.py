"""
ExtractionService - Handles PDF extraction and OCR processing.

This module extracts employee data, transactions, and receipt information
from uploaded PDF files.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

# Note: These imports would require installation of the libraries
# For now, we'll provide placeholder implementations that can be replaced
# with actual PDF parsing and OCR logic
# import PyPDF2
# import pdfplumber
# import pytesseract
# from PIL import Image

from ..repositories.employee_repository import EmployeeRepository
from ..repositories.progress_repository import ProgressRepository
from ..repositories.receipt_repository import ReceiptRepository
from ..repositories.transaction_repository import TransactionRepository
from ..repositories.session_repository import SessionRepository
from .progress_tracker import ProgressTracker
from .progress_calculator import ProgressCalculator


class ExtractionService:
    """
    Service for extracting data from PDF files.

    Provides methods for parsing employee lists, transaction statements,
    and receipt OCR data.
    """

    def __init__(
        self,
        session_repo: SessionRepository,
        employee_repo: EmployeeRepository,
        transaction_repo: TransactionRepository,
        receipt_repo: ReceiptRepository,
        progress_repo: Optional[ProgressRepository] = None
    ):
        """
        Initialize extraction service.

        Args:
            session_repo: SessionRepository instance
            employee_repo: EmployeeRepository instance
            transaction_repo: TransactionRepository instance
            receipt_repo: ReceiptRepository instance
            progress_repo: Optional ProgressRepository for tracking extraction progress
        """
        self.session_repo = session_repo
        self.employee_repo = employee_repo
        self.transaction_repo = transaction_repo
        self.receipt_repo = receipt_repo
        self.progress_repo = progress_repo
        self.progress_tracker: Optional[ProgressTracker] = None
        self.progress_calculator = ProgressCalculator()

    async def extract_employees(self, pdf_path: Path) -> List[Dict]:
        """
        Extract employee information from credit card statement PDF.

        Args:
            pdf_path: Path to PDF file containing employee data

        Returns:
            List of employee data dictionaries

        Example:
            employees = await service.extract_employees(Path("/tmp/statement.pdf"))
            # Returns: [
            #     {
            #         "employee_number": "E12345",
            #         "name": "John Doe",
            #         "department": "Engineering",
            #         "cost_center": "CC-001"
            #     },
            #     ...
            # ]

        Note:
            This is a placeholder implementation. Real implementation would use
            PyPDF2, pdfplumber, or similar library to parse PDF text.
        """
        employees = []

        # TODO: Implement actual PDF parsing
        # with open(pdf_path, 'rb') as f:
        #     pdf_reader = PyPDF2.PdfReader(f)
        #     for page in pdf_reader.pages:
        #         text = page.extract_text()
        #         employees.extend(self._parse_employee_text(text))

        # Placeholder: Return mock data for now
        employees.append({
            "employee_number": "PLACEHOLDER",
            "name": "Extracted Employee",
            "department": "PLACEHOLDER_DEPT",
            "cost_center": None
        })

        return employees

    async def extract_transactions(
        self, pdf_path: Path, session_id: UUID
    ) -> List[Dict]:
        """
        Extract transactions from credit card statement PDF.

        Args:
            pdf_path: Path to PDF file containing transactions
            session_id: UUID of the session

        Returns:
            List of transaction data dictionaries

        Example:
            transactions = await service.extract_transactions(
                Path("/tmp/statement.pdf"),
                session_id
            )
            # Returns: [
            #     {
            #         "transaction_date": date(2025, 10, 1),
            #         "amount": Decimal("125.50"),
            #         "merchant_name": "Office Depot",
            #         "description": "Office supplies",
            #         "card_last_four": "1234"
            #     },
            #     ...
            # ]

        Note:
            This is a placeholder implementation. Real implementation would
            parse transaction lines from credit card statement PDFs.
        """
        transactions = []

        # TODO: Implement actual PDF parsing
        # with open(pdf_path, 'rb') as f:
        #     pdf_reader = PyPDF2.PdfReader(f)
        #     for page in pdf_reader.pages:
        #         text = page.extract_text()
        #         transactions.extend(self._parse_transaction_text(text))

        # Placeholder: Return mock data for now
        transactions.append({
            "transaction_date": date.today(),
            "amount": Decimal("100.00"),
            "merchant_name": "PLACEHOLDER_MERCHANT",
            "description": "Extracted from PDF",
            "card_last_four": "0000"
        })

        return transactions

    async def extract_receipts(
        self, pdf_paths: List[Path], session_id: UUID
    ) -> List[Dict]:
        """
        Extract receipt data from PDF files using OCR.

        Args:
            pdf_paths: List of paths to receipt PDF files
            session_id: UUID of the session

        Returns:
            List of receipt data dictionaries

        Example:
            receipts = await service.extract_receipts(
                [Path("/tmp/receipt1.pdf"), Path("/tmp/receipt2.pdf")],
                session_id
            )
            # Returns: [
            #     {
            #         "receipt_date": date(2025, 10, 1),
            #         "amount": Decimal("125.50"),
            #         "vendor_name": "Office Depot",
            #         "file_name": "receipt1.pdf",
            #         "file_path": "/tmp/receipt1.pdf",
            #         "file_size": 102400,
            #         "mime_type": "application/pdf",
            #         "ocr_confidence": 0.95,
            #         "extracted_data": {
            #             "vendor": "Office Depot",
            #             "date": "2025-10-01",
            #             "total": 125.50,
            #             "items": []
            #         }
            #     },
            #     ...
            # ]

        Note:
            This is a placeholder implementation. Real implementation would use
            pytesseract or cloud OCR services (Azure Computer Vision, AWS Textract).
        """
        receipts = []

        for pdf_path in pdf_paths:
            # TODO: Implement actual OCR processing
            # 1. Convert PDF to images (if needed)
            # 2. Run OCR on images
            # 3. Parse OCR text to extract structured data

            file_size = pdf_path.stat().st_size

            receipt_data = {
                "receipt_date": date.today(),
                "amount": Decimal("50.00"),
                "vendor_name": "PLACEHOLDER_VENDOR",
                "file_name": pdf_path.name,
                "file_path": str(pdf_path),
                "file_size": file_size,
                "mime_type": "application/pdf",
                "ocr_confidence": 0.0,  # Placeholder
                "extracted_data": {
                    "vendor": "PLACEHOLDER_VENDOR",
                    "date": date.today().isoformat(),
                    "total": 50.00,
                    "items": []
                },
                "processing_status": "completed"
            }

            receipts.append(receipt_data)

        return receipts

    def _parse_employee_text(self, text: str) -> List[Dict]:
        """
        Parse employee information from extracted PDF text.

        Args:
            text: Extracted text from PDF

        Returns:
            List of employee data dictionaries

        Note:
            This would contain regex patterns and logic specific to your
            credit card statement format.
        """
        employees = []

        # Example pattern (adjust based on actual PDF format):
        # Employee ID: E12345  Name: John Doe  Dept: Engineering
        pattern = r'Employee ID:\s*(\w+)\s+Name:\s*([^\t]+)\s+Dept:\s*([^\n]+)'
        matches = re.finditer(pattern, text)

        for match in matches:
            employees.append({
                "employee_number": match.group(1).strip(),
                "name": match.group(2).strip(),
                "department": match.group(3).strip(),
                "cost_center": None
            })

        return employees

    def _parse_transaction_text(self, text: str) -> List[Dict]:
        """
        Parse transaction information from extracted PDF text.

        Args:
            text: Extracted text from PDF

        Returns:
            List of transaction data dictionaries

        Note:
            This would contain regex patterns and logic specific to your
            credit card statement format.
        """
        transactions = []

        # Example pattern (adjust based on actual PDF format):
        # 10/01/2025  Office Depot  $125.50
        pattern = r'(\d{2}/\d{2}/\d{4})\s+([^\$]+)\s+\$?([\d,]+\.\d{2})'
        matches = re.finditer(pattern, text)

        for match in matches:
            date_str = match.group(1).strip()
            merchant = match.group(2).strip()
            amount_str = match.group(3).strip().replace(',', '')

            try:
                trans_date = datetime.strptime(date_str, '%m/%d/%Y').date()
                amount = Decimal(amount_str)

                transactions.append({
                    "transaction_date": trans_date,
                    "amount": amount,
                    "merchant_name": merchant,
                    "description": None,
                    "card_last_four": None
                })
            except (ValueError, Exception):
                # Skip invalid entries
                continue

        return transactions

    async def process_session_files(
        self, session_id: UUID, temp_dir: Path
    ) -> None:
        """
        Process all files for a session (main extraction workflow).

        Args:
            session_id: UUID of the session
            temp_dir: Path to temporary directory containing uploaded files

        Note:
            This method orchestrates the entire extraction process:
            1. Extract employees
            2. Extract transactions
            3. Extract receipts
            4. Update session status
        """
        try:
            # Update session status
            await self.session_repo.update_session_status(session_id, "extracting")

            # Get all PDF files in temp directory
            pdf_files = list(temp_dir.glob("*.pdf"))

            # Placeholder: In real implementation, you'd identify which PDFs
            # are statements vs receipts based on content or naming convention

            # For now, treat first file as statement, rest as receipts
            if len(pdf_files) > 0:
                statement_pdf = pdf_files[0]
                receipt_pdfs = pdf_files[1:] if len(pdf_files) > 1 else []

                # Extract employees
                employee_data = await self.extract_employees(statement_pdf)
                employees = await self.employee_repo.bulk_create_employees(
                    session_id, employee_data
                )

                # Extract transactions (assume first employee for now)
                if employees:
                    transaction_data = await self.extract_transactions(
                        statement_pdf, session_id
                    )
                    # Add employee_id to each transaction
                    for trans in transaction_data:
                        trans["employee_id"] = employees[0].id
                        trans["session_id"] = session_id

                    await self.transaction_repo.bulk_create_transactions(transaction_data)

                # Extract receipts
                if receipt_pdfs:
                    receipt_data = await self.extract_receipts(receipt_pdfs, session_id)
                    for receipt in receipt_data:
                        receipt["session_id"] = session_id
                    await self.receipt_repo.bulk_create_receipts(receipt_data)

            # Update session counts
            await self.session_repo.update_session_counts(session_id)

            # Update status to matching (next phase)
            await self.session_repo.update_session_status(session_id, "matching")

        except Exception as e:
            # Update session status to failed
            await self.session_repo.update_session_status(session_id, "failed")
            raise

    async def initialize_progress_tracker(self, session_id: UUID) -> None:
        """
        Initialize progress tracker for this extraction service.

        Args:
            session_id: UUID of the session
        """
        if self.progress_repo:
            async def update_callback(sid: UUID, progress):
                await self.progress_repo.update_session_progress(sid, progress)

            self.progress_tracker = ProgressTracker(session_id, update_callback)

    async def process_session_files_with_progress(
        self, session_id: UUID, temp_dir: Path
    ) -> None:
        """
        Process all files for a session with progress tracking.

        Args:
            session_id: UUID of the session
            temp_dir: Path to temporary directory containing uploaded files

        Note:
            This method is similar to process_session_files but includes
            progress tracking updates at the page level for PDFs.
        """
        try:
            # Initialize progress tracker if not already done
            if not self.progress_tracker and self.progress_repo:
                await self.initialize_progress_tracker(session_id)

            # Get all PDF files in temp directory
            pdf_files = list(temp_dir.glob("*.pdf"))
            total_files = len(pdf_files)

            if total_files == 0:
                return

            # Report processing phase starting
            if self.progress_tracker:
                await self.progress_tracker.update_progress(
                    current_phase="processing",
                    phase_details={
                        "status": "in_progress",
                        "percentage": 0,
                        "total_files": total_files,
                        "current_file_index": 0,
                        "started_at": datetime.utcnow()
                    },
                    force_update=True
                )

            # Process each file with progress tracking
            for file_index, pdf_file in enumerate(pdf_files, 1):
                await self._process_pdf_with_progress(
                    pdf_file=pdf_file,
                    session_id=session_id,
                    file_index=file_index,
                    total_files=total_files
                )

            # Mark processing phase as complete
            if self.progress_tracker:
                await self.progress_tracker.update_progress(
                    current_phase="processing",
                    phase_details={
                        "status": "completed",
                        "percentage": 100,
                        "total_files": total_files,
                        "completed_at": datetime.utcnow()
                    },
                    force_update=True
                )

            # Update session counts
            await self.session_repo.update_session_counts(session_id)

            # Update status to matching (next phase)
            await self.session_repo.update_session_status(session_id, "matching")

        except Exception as e:
            # Report error in progress
            if self.progress_tracker:
                from ..schemas.phase_progress import ErrorContext
                error_context = ErrorContext(
                    type=type(e).__name__,
                    message=str(e),
                    context={
                        "phase": "processing",
                        "session_id": str(session_id)
                    },
                    timestamp=datetime.utcnow()
                )
                await self.progress_tracker.update_progress(
                    current_phase="processing",
                    phase_details={
                        "status": "failed",
                        "error": error_context
                    },
                    force_update=True
                )

            # Update session status to failed
            await self.session_repo.update_session_status(session_id, "failed")
            raise

    async def _process_pdf_with_progress(
        self,
        pdf_file: Path,
        session_id: UUID,
        file_index: int,
        total_files: int
    ) -> None:
        """
        Process a single PDF file with page-level progress tracking.

        Args:
            pdf_file: Path to the PDF file
            session_id: UUID of the session
            file_index: Current file index (1-based)
            total_files: Total number of files being processed
        """
        # TODO: When real PDF processing is implemented with pdfplumber:
        # 1. Open PDF and get total pages: len(pdf.pages)
        # 2. Iterate through pages
        # 3. Update progress for each page
        # 4. Extract data from pages

        # Placeholder implementation showing progress tracking pattern
        total_pages = 10  # Placeholder - would be from PDF metadata

        for page_num in range(1, total_pages + 1):
            # Simulate page processing
            # In real implementation, this is where you'd extract text from the page

            if self.progress_tracker:
                # Calculate progress percentages
                file_progress = self.progress_calculator.calculate_file_progress(
                    page_num, total_pages
                )
                overall_progress = self.progress_calculator.calculate_multi_file_progress(
                    file_index, total_files, page_num, total_pages
                )

                # Update progress
                await self.progress_tracker.update_progress(
                    current_phase="processing",
                    phase_details={
                        "status": "in_progress",
                        "percentage": int(overall_progress),
                        "total_files": total_files,
                        "current_file_index": file_index,
                        "current_file": {
                            "name": pdf_file.name,
                            "total_pages": total_pages,
                            "current_page": page_num,
                            "regex_matches_found": page_num * 5,  # Placeholder
                            "started_at": datetime.utcnow()
                        }
                    },
                    force_update=(page_num == 1 or page_num == total_pages)
                )
