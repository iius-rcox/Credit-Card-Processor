"""
PDF text extraction utilities using pdfplumber.

This module provides core PDF parsing functionality used by
credit card statement and expense report parsers.
"""

from typing import List
import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> List[str]:
    """
    Extract text from all pages of a PDF file.

    Args:
        pdf_path: Absolute path to PDF file

    Returns:
        List of strings, one per page. Empty list if parsing fails.

    Example:
        >>> pages = extract_text_from_pdf("statement.pdf")
        >>> print(f"Found {len(pages)} pages")
        >>> print(pages[0][:100])  # First 100 chars of page 1
    """
    try:
        page_texts = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if text:
                    page_texts.append(text)
                else:
                    # Page has no extractable text
                    page_texts.append("")

        return page_texts

    except FileNotFoundError:
        # PDF file doesn't exist
        return []
    except Exception as e:
        # Parsing failed (corrupted PDF, permission error, etc.)
        print(f"Error parsing PDF {pdf_path}: {e}")
        return []


def extract_tables_from_pdf(pdf_path: str) -> List[List[List[str]]]:
    """
    Extract tables from all pages of a PDF file.

    Args:
        pdf_path: Absolute path to PDF file

    Returns:
        List of page tables. Each page contains a list of tables.
        Each table is a list of rows. Each row is a list of cell values.
        Empty list if parsing fails.

    Example:
        >>> page_tables = extract_tables_from_pdf("statement.pdf")
        >>> for page_idx, tables in enumerate(page_tables):
        >>>     print(f"Page {page_idx + 1} has {len(tables)} tables")
        >>>     for table in tables:
        >>>         print(f"  Table has {len(table)} rows")
    """
    try:
        all_page_tables = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                if tables:
                    all_page_tables.append(tables)
                else:
                    # Page has no tables
                    all_page_tables.append([])

        return all_page_tables

    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error extracting tables from PDF {pdf_path}: {e}")
        return []


def is_valid_pdf(pdf_path: str) -> bool:
    """
    Check if a file is a valid PDF that can be opened.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if file is a valid, parseable PDF. False otherwise.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Try to access first page to verify it's valid
            if len(pdf.pages) > 0:
                return True
            return False
    except Exception:
        return False
