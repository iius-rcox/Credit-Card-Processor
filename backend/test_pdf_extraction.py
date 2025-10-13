"""
Test script to debug PDF extraction - check if regex patterns match PDF format.

This script:
1. Extracts text from test PDF files
2. Shows sample text to verify format
3. Tests regex patterns against actual PDF text
4. Identifies why 0 transactions are being extracted
"""

import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)


def extract_and_analyze_pdf(pdf_path: Path):
    """Extract text from PDF and analyze format."""
    print(f"\n{'=' * 80}")
    print(f"Analyzing PDF: {pdf_path.name}")
    print(f"{'=' * 80}\n")

    # Check if file exists
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        return

    # Extract text using pdfplumber
    print("Step 1: Extracting text from PDF...")
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            print(f"  [OK] PDF has {page_count} pages")

            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    print(f"  [OK] Extracted text from page {i} ({len(page_text)} characters)")
                else:
                    print(f"  [FAIL] No text on page {i} (scanned image?)")
    except Exception as e:
        print(f"ERROR extracting PDF: {e}")
        return

    if not text.strip():
        print("\n[FAIL] PROBLEM: No text extracted from PDF (likely a scanned image)")
        return

    print(f"\n  [OK] Total extracted text: {len(text)} characters")

    # Show first 2000 characters of text
    print(f"\nStep 2: First 2000 characters of extracted text:")
    print("-" * 80)
    print(text[:2000])
    print("-" * 80)

    # Test employee header pattern
    print("\nStep 3: Testing employee header pattern...")
    employee_header_pattern = re.compile(r'Cardholder Name:\s*([A-Z]+)', re.MULTILINE)
    employee_matches = list(employee_header_pattern.finditer(text))
    print(f"  Found {len(employee_matches)} employee name headers")
    for i, match in enumerate(employee_matches[:5], 1):
        print(f"    {i}. '{match.group(1)}' at position {match.start()}")

    # Test transaction pattern
    print("\nStep 4: Testing transaction pattern...")
    transaction_pattern = re.compile(
        r'^(\d{2}/\d{2}/\d{4})\s+'  # Trans Date
        r'(\d{2}/\d{2}/\d{4})\s+'  # Posted Date
        r'([A-Z])\s+'  # Level (F/N/L)
        r'(\d+)\s+'  # Transaction #
        r'(.+?),\s*'  # Merchant Name (everything until comma)
        r'([A-Z]{2})\s+'  # State (2 letters after comma)
        r'([A-Z]+)\s+'  # Merchant Group (FUEL, MISC, etc.)
        r'(.+?)\s+'  # Product Description
        r'[\d,]+\.?\d*\s+'  # PPU/G
        r'[-]?[\d,]+\.?\d*\s+'  # Quantity
        r'\$[-]?[\d,]+\.\d{2}\s+'  # Gross Cost
        r'\$[-]?[\d,]+\.\d{2}\s+'  # Discount
        r'(\$[-]?[\d,]+\.\d{2})$',  # Net Cost (final amount)
        re.MULTILINE
    )

    transaction_matches = list(transaction_pattern.finditer(text))
    print(f"  Found {len(transaction_matches)} transaction matches")

    if len(transaction_matches) == 0:
        print("\n  [FAIL] PROBLEM: Regex pattern does not match any transactions!")
        print("\n  Debugging: Let's look for transaction-like lines...")

        # Look for lines with dates at the start
        date_lines = []
        for line in text.split('\n'):
            if re.match(r'^\d{1,2}/\d{1,2}/\d{4}', line.strip()):
                date_lines.append(line.strip())

        print(f"\n  Found {len(date_lines)} lines starting with dates:")
        for i, line in enumerate(date_lines[:10], 1):
            print(f"    {i}. {line[:120]}")

        if date_lines:
            print("\n  -> Regex pattern may need adjustment to match actual format")
            print("  -> Compare pattern expectations vs actual line format above")
    else:
        print(f"\n  [OK] SUCCESS: Found {len(transaction_matches)} transactions")
        print("\n  First 3 transactions:")
        for i, match in enumerate(transaction_matches[:3], 1):
            print(f"\n    Transaction {i}:")
            print(f"      Trans Date: {match.group(1)}")
            print(f"      Posted Date: {match.group(2)}")
            print(f"      Merchant: {match.group(5)}")
            print(f"      State: {match.group(6)}")
            print(f"      Group: {match.group(7)}")
            print(f"      Amount: {match.group(9)}")
            print(f"      Raw: {match.group(0)[:100]}...")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("PDF EXTRACTION DIAGNOSTIC TOOL")
    print("=" * 80)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir

    # List of test PDFs to check
    test_pdfs = [
        "Cardholder+Activity+Report+General-S-89S,DD2LJ,DFRHA (6).pdf",
        "ReceiptImagesReportNew - 2025-04-16T092121.632.pdf",
    ]

    # Try to find test PDFs
    found_pdfs = []
    for pdf_name in test_pdfs:
        # Search in project directory
        pdf_path = None
        for path in project_root.rglob(pdf_name):
            pdf_path = path
            break

        if pdf_path and pdf_path.exists():
            found_pdfs.append(pdf_path)
        else:
            print(f"\nNote: Test PDF not found: {pdf_name}")

    if not found_pdfs:
        print("\n[!] No test PDFs found in project directory")
        print("\nPlease provide a PDF path as argument:")
        print(f"  python {Path(__file__).name} <path-to-pdf>")

        if len(sys.argv) > 1:
            manual_path = Path(sys.argv[1])
            if manual_path.exists():
                found_pdfs.append(manual_path)
            else:
                print(f"\nERROR: Provided path does not exist: {manual_path}")
                sys.exit(1)
        else:
            sys.exit(1)

    # Analyze each PDF
    for pdf_path in found_pdfs:
        extract_and_analyze_pdf(pdf_path)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
