"""
Analyze PDF format to understand structure for regex pattern development.

This script extracts sample text from PDFs to identify:
- Column layout and separators
- Header patterns
- Transaction line format
- Field order and content
"""

import sys
from pathlib import Path
import pdfplumber


def analyze_pdf(pdf_path: Path) -> None:
    """
    Extract and display sample text from PDF for format analysis.

    Args:
        pdf_path: Path to PDF file to analyze
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}\n")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} pages\n")

            # Analyze first 3 pages
            for page_num in range(min(3, len(pdf.pages))):
                page = pdf.pages[page_num]
                text = page.extract_text()

                if not text:
                    print(f"WARNING: Page {page_num + 1}: No extractable text (may be scanned image)\n")
                    continue

                print(f"\n{'-'*80}")
                print(f"PAGE {page_num + 1}")
                print(f"{'-'*80}")

                # Show first 500 characters
                print(f"\nFirst 500 characters:")
                print(f"{text[:500]}")

                # Show first 15 lines with repr() to see exact spacing
                print(f"\nFirst 15 lines (with repr to show spacing):")
                lines = text.split('\n')
                for i, line in enumerate(lines[:15], 1):
                    print(f"Line {i:2d}: {repr(line)}")

                # Search for potential patterns
                print(f"\nPattern Detection:")

                # Check for employee header
                if 'Cardholder Name' in text:
                    print(f"FOUND: 'Cardholder Name' pattern")
                    for line in lines[:20]:
                        if 'Cardholder Name' in line:
                            print(f"  > {repr(line)}")
                else:
                    print(f"NOT FOUND: 'Cardholder Name'")
                    print(f"  Searching for alternative employee patterns...")
                    for keyword in ['Employee', 'Name', 'Cardholder', 'Card Holder']:
                        for line in lines[:20]:
                            if keyword in line:
                                print(f"  Found '{keyword}': {repr(line)}")
                                break

                # Check for date patterns (MM/DD/YYYY)
                import re
                date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
                date_lines = [line for line in lines[:30] if date_pattern.search(line)]
                print(f"\nFOUND: {len(date_lines)} lines with dates (first 5):")
                for line in date_lines[:5]:
                    print(f"  > {repr(line)}")

                # Check for dollar amounts
                amount_pattern = re.compile(r'\$[\d,]+\.\d{2}')
                amount_lines = [line for line in lines[:30] if amount_pattern.search(line)]
                print(f"\nFOUND: {len(amount_lines)} lines with dollar amounts (first 5):")
                for line in amount_lines[:5]:
                    print(f"  > {repr(line)}")

                # Show statistics
                print(f"\nStatistics:")
                print(f"  Total characters: {len(text):,}")
                print(f"  Total lines: {len(lines):,}")
                print(f"  Average line length: {len(text) / len(lines) if lines else 0:.1f} chars")
                print(f"  Lines with dates: {len(date_lines)}")
                print(f"  Lines with amounts: {len(amount_lines)}")

    except Exception as e:
        print(f"ERROR analyzing PDF: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_pdf_format.py <path_to_pdf>")
        print("\nExample:")
        print('  python analyze_pdf_format.py "C:\\Users\\rcox\\OneDrive - INSULATIONS, INC\\Documents\\Expense Splitter\\Cardholder+Activity+Report+General-S-89S,DD2LJ,DFRHA (6).pdf"')
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"ERROR: Not a PDF file: {pdf_path}")
        sys.exit(1)

    analyze_pdf(pdf_path)

    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
