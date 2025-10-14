"""
ExtractionService - Handles PDF extraction and OCR processing.

This module extracts employee data, transactions, and receipt information
from uploaded PDF files.
"""

import re
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

import pdfplumber

from ..repositories.employee_repository import EmployeeRepository
from ..repositories.progress_repository import ProgressRepository
from ..repositories.receipt_repository import ReceiptRepository
from ..repositories.transaction_repository import TransactionRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.alias_repository import AliasRepository
from .progress_tracker import ProgressTracker
from .progress_calculator import ProgressCalculator

logger = logging.getLogger(__name__)


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
        progress_repo: Optional[ProgressRepository] = None,
        alias_repo: Optional[AliasRepository] = None
    ):
        """
        Initialize extraction service.

        Args:
            session_repo: SessionRepository instance
            employee_repo: EmployeeRepository instance
            transaction_repo: TransactionRepository instance
            receipt_repo: ReceiptRepository instance
            progress_repo: Optional ProgressRepository for tracking extraction progress
            alias_repo: Optional AliasRepository for employee name resolution
        """
        self.session_repo = session_repo
        self.employee_repo = employee_repo
        self.transaction_repo = transaction_repo
        self.receipt_repo = receipt_repo
        self.progress_repo = progress_repo
        self.alias_repo = alias_repo
        self.progress_tracker: Optional[ProgressTracker] = None
        self.progress_calculator = ProgressCalculator()

        # Track current session for debug output
        self._current_session_id: Optional[UUID] = None
        self._current_pdf_filename: Optional[str] = None
        self._current_pdf_size: Optional[int] = None
        self._current_pdf_pages: Optional[int] = None

        # Compile regex patterns for performance (T017)
        # Updated for WEX Fleet card format (space-separated columns)
        # Format: Trans Date  Posted Date  Lvl  Transaction #  Merchant Name  City, State  Group  Description  ...  Net Cost

        # Pattern to extract employee name from section header
        self.employee_header_pattern = re.compile(r'Cardholder Name:\s*([A-Z]+)', re.MULTILINE)
        self.employee_id_pattern = re.compile(r'Employee ID:\s*(\d+)', re.MULTILINE)

        self.date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')
        self.amount_pattern = re.compile(r'([-]?\$?[\d,]+(?:\.\d{2})?)')

        # Merchant group to expense type mapping
        self.expense_type_map = {
            'FUEL': 'Fuel',
            'MISC': 'General Expense',
            'MEALS': 'Meals',
            'LODGING': 'Hotel',
            'LEGAL': 'Legal',
            'MAINT': 'Maintenance',
            'TRANS': 'Misc. Transportation',
            'SERVICE': 'Business Services'
        }

        # WEX transaction pattern (space-separated columns)
        # Format: 03/03/2025 03/04/2025 N 000425061 OVERHEAD DOOR COMKPEMAH, TX MISC ... $768.22
        # Key insight: Merchant name ends at comma (before state abbreviation)
        # Note: Product Description may have doubled chars (OOTTHHEERR) or be numeric (523.93000)
        self.transaction_pattern = re.compile(
            r'^(\d{2}/\d{2}/\d{4})\s+'  # Trans Date
            r'(\d{2}/\d{2}/\d{4})\s+'  # Posted Date
            r'([A-Z])\s+'  # Level (F/N/L)
            r'(\d+)\s+'  # Transaction #
            r'(.+?),\s*'  # Merchant Name (everything until comma)
            r'([A-Z]{2})\s+'  # State (2 letters after comma)
            r'([A-Z]+)\s+'  # Merchant Group (FUEL, MISC, etc.)
            r'(.+?)\s+(?=[\d,]+\.[\d]+\s+[-]?[\d,]+\.[\d]+\s+\$)'  # Product Description (until PPU/G pattern detected via lookahead)
            r'([\d,]+\.?\d+)\s+'  # PPU/G (decimal number)
            r'([-]?[\d,]+\.?\d+)\s+'  # Quantity (can be negative)
            r'\$([-]?[\d,]+\.\d{2})\s+'  # Gross Cost
            r'\$([-]?[\d,]+\.\d{2})\s+'  # Discount
            r'(\$[-]?[\d,]+\.\d{2})$',  # Net Cost (final amount)
            re.MULTILINE
        )

    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using pdfplumber (T016).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Concatenated text from all pages

        Raises:
            Exception: If PDF is scanned image (no text extractable)

        Note:
            Uses context manager for proper resource cleanup
        """
        text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # Validate that we extracted some text (not a scanned image)
        if not text or len(text.strip()) == 0:
            raise Exception("Scanned image PDF not supported. Please upload text-based PDF.")

        # Debug logging to help diagnose extraction issues
        logger.info(f"[PDF_TEXT] Extracted {len(text)} characters from PDF")
        logger.info(f"[PDF_TEXT] First 500 characters: {text[:500]}")
        logger.info(f"[PDF_TEXT] First 5 lines:")
        for i, line in enumerate(text.split('\n')[:5], 1):
            logger.info(f"[PDF_TEXT]   Line {i}: {repr(line)[:100]}")

        # Debug file output: Raw text extraction
        if self._current_session_id:
            from ..utils.debug_writer import write_debug_text

            # Determine file type from content
            file_name = "01_cardholder_text" if "Cardholder" in text[:500] else "02_receipt_text"
            write_debug_text(
                session_id=self._current_session_id,
                file_name=file_name,
                text=text
            )

        return text

    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        Parse date string in MM/DD/YYYY format to date object (T017).

        Args:
            date_str: Date string from PDF (e.g., "03/24/2025" or "3/5/2025")

        Returns:
            date object if parsing succeeds, None otherwise

        Example:
            dt = self._parse_date("03/24/2025")  # -> date(2025, 3, 24)
        """
        if not date_str:
            return None

        try:
            # Handle both MM/DD/YYYY and M/D/YYYY formats
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            try:
                # Try without leading zeros
                return datetime.strptime(date_str, '%-m/%-d/%Y').date()
            except (ValueError, AttributeError):
                logger.warning(f"Failed to parse date: {date_str}")
                return None

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """
        Parse amount string to Decimal, handling commas and negatives (T017).

        Args:
            amount_str: Amount string from PDF (e.g., "1,234.56", "-15.50", "$77.37")

        Returns:
            Decimal value if parsing succeeds, None otherwise

        Example:
            amt = self._parse_amount("1,234.56")  # -> Decimal("1234.56")
            amt = self._parse_amount("-$15.50")   # -> Decimal("-15.50")
        """
        if not amount_str:
            return None

        try:
            # Remove currency symbols and commas
            cleaned = amount_str.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned)
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to parse amount: {amount_str}, error: {e}")
            return None

    async def _extract_credit_transactions(self, text: str) -> List[Dict]:
        """
        Extract credit card transactions from PDF text using regex (T018).
        Updated for WEX Fleet card format.

        Args:
            text: Extracted text from PDF

        Returns:
            List of transaction data dictionaries

        Note:
            Handles extraction errors gracefully by creating incomplete transactions
        """
        transactions = []

        # Extract employee name from section header
        employee_name = None
        logger.info(f"[REGEX_DEBUG] Searching for employee header in text ({len(text)} chars)")
        employee_header_match = self.employee_header_pattern.search(text)
        if employee_header_match:
            employee_name = employee_header_match.group(1).strip()
            logger.info(f"[REGEX_DEBUG] Found employee: {employee_name}")
        else:
            logger.warning(f"[REGEX_DEBUG] Employee header pattern NOT matched")
            logger.warning(f"[REGEX_DEBUG] Pattern: {self.employee_header_pattern.pattern}")
            logger.warning(f"[REGEX_DEBUG] Sample text (first 200 chars): {text[:200]}")

        # Resolve employee_id once for all transactions in this section
        employee_id = None
        if self.alias_repo and employee_name:
            employee_id = await self.alias_repo.resolve_employee_id(employee_name)

        # Apply master transaction pattern to extract all matches
        logger.info(f"[REGEX_DEBUG] Attempting transaction pattern matching...")
        matches_list = list(self.transaction_pattern.finditer(text))
        logger.info(f"[REGEX_DEBUG] Transaction pattern found {len(matches_list)} matches")

        if len(matches_list) == 0:
            logger.warning(f"[REGEX_DEBUG] Transaction pattern DID NOT MATCH")
            logger.warning(f"[REGEX_DEBUG] Pattern expects: MM/DD/YYYY MM/DD/YYYY L NNNN MERCHANT, ST GROUP DESC PPU QTY $GROSS $DISC $NET")
            logger.warning(f"[REGEX_DEBUG] Sample transaction lines from PDF:")
            for i, line in enumerate(text.split('\n')[5:15], 1):  # Skip header lines
                if line.strip() and any(c.isdigit() for c in line[:10]):  # Lines starting with digits
                    logger.warning(f"[REGEX_DEBUG]   Sample {i}: {repr(line)[:150]}")

        for match in matches_list:
            try:
                # Extract fields from regex groups (WEX format)
                trans_date_str = match.group(1).strip() if match.group(1) else None  # Trans Date
                posted_date_str = match.group(2).strip() if match.group(2) else None  # Posted Date
                level = match.group(3).strip() if match.group(3) else None  # Level (F/N/L)
                transaction_num = match.group(4).strip() if match.group(4) else None  # Transaction #
                merchant_name = match.group(5).strip() if match.group(5) else None  # Merchant Name (until comma)
                state = match.group(6).strip() if match.group(6) else None  # State (2 letters after comma)
                merchant_group = match.group(7).strip() if match.group(7) else None  # Group (FUEL, MISC, etc.)
                product_desc = match.group(8).strip() if match.group(8) else None  # Product Description
                net_cost_str = match.group(9).strip() if match.group(9) else None  # Net Cost (final amount)

                # Parse date and amount
                transaction_date = self._parse_date(trans_date_str) if trans_date_str else None
                amount = self._parse_amount(net_cost_str) if net_cost_str else None

                # Map merchant group to expense type
                expense_type = None
                if merchant_group:
                    expense_type = self.expense_type_map.get(merchant_group, "General Expense")

                # Build merchant address with state
                merchant_address = state if state else None

                # Determine flags
                incomplete_flag = any([
                    transaction_date is None,
                    amount is None,
                    employee_id is None,
                    merchant_name is None or len(merchant_name) == 0
                ])

                is_credit = amount is not None and amount < 0

                # Build transaction dict
                # Note: Using merchant_category (not expense_type) to match actual table schema
                transaction = {
                    "employee_id": employee_id,
                    "transaction_date": transaction_date,
                    "amount": amount,
                    "merchant_name": merchant_name,
                    "merchant_category": expense_type,  # Maps to merchant_category column
                    "description": product_desc,  # Store product description
                    "incomplete_flag": incomplete_flag,
                    "is_credit": is_credit,
                    "raw_data": {
                        "raw_text": match.group(0),
                        "extracted_fields": {
                            "employee_name": employee_name,
                            "transaction_number": transaction_num,
                            "merchant_group": merchant_group,
                            "merchant_address": merchant_address,
                            "state": state,
                            "level": level
                        }
                    }
                }

                transactions.append(transaction)

            except (ValueError, AttributeError, KeyError) as e:
                # Handle extraction errors - create incomplete transaction with error
                logger.warning(f"Failed to parse transaction: {e}")
                transactions.append({
                    "employee_id": employee_id,  # Use employee from header even on error
                    "transaction_date": None,
                    "amount": None,
                    "merchant_name": "EXTRACTION_ERROR",
                    "incomplete_flag": True,
                    "is_credit": False,
                    "raw_data": {
                        "error": str(e),
                        "raw_text": match.group(0) if match else ""
                    }
                })

        # Debug logging (Task 1.1)
        logger.info(f"[EXTRACTION] Extracted {len(transactions)} transactions from PDF")
        if transactions:
            logger.info(f"[EXTRACTION] First transaction: date={transactions[0].get('transaction_date')}, "
                       f"amount={transactions[0].get('amount')}, merchant={transactions[0].get('merchant_name')}")
        else:
            logger.warning("[EXTRACTION] No transactions extracted - regex pattern may not match PDF format")

        # Debug file output: Regex processing results
        if self._current_session_id:
            from ..utils.debug_writer import write_debug_json

            debug_data = {
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "session_id": str(self._current_session_id),
                "pdf_metadata": {
                    "filename": self._current_pdf_filename or "unknown",
                    "file_size_bytes": self._current_pdf_size or 0,
                    "total_pages": self._current_pdf_pages or 0
                },
                "employee_name_found": employee_name,
                "employee_id_resolved": str(employee_id) if employee_id else None,
                "total_matches": len(transactions),
                "incomplete_count": sum(1 for t in transactions if t.get("incomplete_flag")),
                "credit_count": sum(1 for t in transactions if t.get("is_credit")),
                "regex_patterns": {
                    "employee_header": self.employee_header_pattern.pattern,
                    "transaction": self.transaction_pattern.pattern
                },
                "sample_text": text[:1000],
                "extracted_transactions": transactions[:10],  # First 10 only
                "extraction_stats": {
                    "text_length": len(text),
                    "lines_processed": len(text.split('\n')),
                    "pattern_matches": len(matches_list)
                },
                "match_statistics": {
                    "total_lines_in_pdf": len(text.split('\n')),
                    "lines_with_dates": len([l for l in text.split('\n') if self.date_pattern.search(l)]),
                    "lines_with_amounts": len([l for l in text.split('\n') if self.amount_pattern.search(l)]),
                    "successful_parses": len([t for t in transactions if not t.get("incomplete_flag")]),
                    "failed_parses": len([t for t in transactions if t.get("incomplete_flag")]),
                    "negative_amounts": len([t for t in transactions if t.get("is_credit")])
                },
                "sample_matches": {
                    "first_matched_line": matches_list[0].group(0) if matches_list else None,
                    "first_10_lines": text.split('\n')[5:15] if len(text.split('\n')) > 15 else text.split('\n')
                }
            }

            file_name = "03_cardholder_regex_results" if "Cardholder" in text[:500] else "04_receipt_regex_results"
            write_debug_json(
                session_id=self._current_session_id,
                file_name=file_name,
                data=debug_data
            )

        return transactions

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
            List of transaction data dictionaries with all fields populated

        Example:
            transactions = await service.extract_transactions(
                Path("/tmp/statement.pdf"),
                session_id
            )
            # Returns: [
            #     {
            #         "employee_id": UUID(...),
            #         "transaction_date": date(2025, 3, 24),
            #         "amount": Decimal("77.37"),
            #         "merchant_name": "CHEVRON 0308017",
            #         "merchant_address": "27952 WALKER SOUTH",
            #         "expense_type": "Fuel",
            #         "incomplete_flag": False,
            #         "is_credit": False,
            #         "raw_data": {"raw_text": "...", "extracted_fields": {...}}
            #     },
            #     ...
            # ]

        Note:
            Uses pdfplumber for text extraction and regex patterns for parsing.
            Replaces placeholder implementation with real PDF extraction.
        """
        try:
            # Track session for debug output
            self._current_session_id = session_id
            self._current_pdf_filename = pdf_path.name
            self._current_pdf_size = pdf_path.stat().st_size

            # Get page count for metadata
            with pdfplumber.open(pdf_path) as pdf:
                self._current_pdf_pages = len(pdf.pages)

            # Extract text from PDF using pdfplumber (T016)
            text = self._extract_text(pdf_path)

            # Extract transactions using regex patterns (T018)
            transactions = await self._extract_credit_transactions(text)

            # Add session_id to each transaction
            for transaction in transactions:
                transaction["session_id"] = session_id

            return transactions

        finally:
            # Clear tracking variables
            self._current_session_id = None
            self._current_pdf_filename = None
            self._current_pdf_size = None
            self._current_pdf_pages = None

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

                # Extract transactions
                # Note: employee_id is now resolved from PDF header and aliases in extract_transactions()
                # Don't need employees to be created first
                transaction_data = await self.extract_transactions(
                    statement_pdf, session_id
                )
                # session_id is already added in extract_transactions(), but ensure it's set
                for trans in transaction_data:
                    if "session_id" not in trans:
                        trans["session_id"] = session_id
                    # Don't overwrite employee_id - it's resolved from aliases in extraction

                if transaction_data:
                    await self.transaction_repo.bulk_create_transactions(transaction_data)

                # Extract receipts
                if receipt_pdfs:
                    receipt_data = await self.extract_receipts(receipt_pdfs, session_id)
                    for receipt in receipt_data:
                        receipt["session_id"] = session_id
                    await self.receipt_repo.bulk_create_receipts(receipt_data)

            # Update session counts
            await self.session_repo.update_session_counts(session_id)

            # Update status to matching phase (next phase after extraction completes)
            # Database constraint now supports: processing, extracting, matching, completed, failed, expired
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

            # Update status to matching phase (next phase after extraction completes)
            # Database constraint now supports: processing, extracting, matching, completed, failed, expired
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
        # Real PDF processing with pdfplumber (007-actual-pdf-parsing)
        # Extract transactions from PDF
        logger.info(f"[PROCESS_PDF] Processing {pdf_file.name} for session {session_id}")

        # Get total pages for progress tracking
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)

        logger.info(f"[PROCESS_PDF] PDF has {total_pages} pages")

        # Update progress - starting file processing
        if self.progress_tracker:
            await self.progress_tracker.update_progress(
                current_phase="processing",
                phase_details={
                    "status": "in_progress",
                    "total_files": total_files,
                    "current_file_index": file_index,
                    "current_file": {
                        "name": pdf_file.name,
                        "total_pages": total_pages,
                        "current_page": 1,
                        "started_at": datetime.utcnow()
                    }
                },
                force_update=True
            )

        # Extract transactions from the PDF
        transaction_data = await self.extract_transactions(pdf_file, session_id)
        logger.info(f"[PROCESS_PDF] Extracted {len(transaction_data)} transactions from {pdf_file.name}")

        # Bulk insert transactions
        if transaction_data:
            await self.transaction_repo.bulk_create_transactions(transaction_data)
            logger.info(f"[PROCESS_PDF] Saved {len(transaction_data)} transactions to database")

        # Simulate page-by-page progress updates (since we already extracted all)
        for page_num in range(1, min(total_pages + 1, 11)):  # Update progress for first 10 pages only
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
