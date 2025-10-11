"""
Debug script to show what's being extracted from PDFs.
Run this to see actual extraction results from your PDFs.
"""
import PyPDF2
from pathlib import Path
import re

def extract_text_from_pdf(pdf_path):
    """Extract raw text from PDF."""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def simple_bank_extraction(text):
    """Simple pattern matching for bank transactions."""
    # Look for common bank transaction patterns
    patterns = [
        r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(.+?)\s+\$?([\d,]+\.\d{2})',  # Date Description Amount
        r'(\d{1,2}-\d{1,2}-\d{2,4})\s+(.+?)\s+\$?([\d,]+\.\d{2})',       # Date-format
    ]

    transactions = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            transactions.append({
                'date': match.group(1),
                'description': match.group(2).strip(),
                'amount': match.group(3).replace(',', '')
            })

    return transactions

def simple_credit_extraction(text):
    """Simple pattern matching for credit card transactions."""
    # Similar patterns but looking for credit-specific markers
    patterns = [
        r'(\d{1,2}/\d{1,2})\s+(\d{1,2}/\d{1,2})?\s*(.+?)\s+\$?([\d,]+\.\d{2})',
    ]

    transactions = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            groups = match.groups()
            transactions.append({
                'trans_date': groups[0],
                'post_date': groups[1] if groups[1] else groups[0],
                'description': groups[2].strip(),
                'amount': groups[3].replace(',', '')
            })

    return transactions

def main():
    # Find sample PDFs
    test_pdf = Path("backend/test-upload.pdf")

    if not test_pdf.exists():
        print(f"[!] Test PDF not found: {test_pdf}")
        print("\n[SEARCH] Looking for PDFs in current directory...")
        pdfs = list(Path(".").rglob("*.pdf"))
        if pdfs:
            print(f"Found {len(pdfs)} PDFs:")
            for pdf in pdfs[:10]:
                print(f"  - {pdf}")
            test_pdf = pdfs[0]
            print(f"\n[+] Using: {test_pdf}")
        else:
            print("No PDFs found!")
            return

    print("=" * 80)
    print("PDF EXTRACTION DEBUG")
    print("=" * 80)

    # Extract raw text
    print(f"\n[PDF] Processing: {test_pdf}")
    print("-" * 80)

    raw_text = extract_text_from_pdf(test_pdf)
    print("\n[RAW TEXT] EXTRACTED:")
    print("-" * 80)
    print(raw_text[:2000])  # First 2000 chars
    if len(raw_text) > 2000:
        print(f"\n... (showing first 2000 of {len(raw_text)} characters)")

    # Try simple extractions
    print("\n" + "=" * 80)
    print("SIMPLE PATTERN MATCHING")
    print("=" * 80)

    bank_txs = simple_bank_extraction(raw_text)
    print(f"\n[BANK] Found {len(bank_txs)} potential bank transactions:")
    for i, tx in enumerate(bank_txs[:10], 1):
        print(f"  {i}. {tx['date']:12} ${tx['amount']:>10} - {tx['description'][:50]}")

    credit_txs = simple_credit_extraction(raw_text)
    print(f"\n[CREDIT] Found {len(credit_txs)} potential credit transactions:")
    for i, tx in enumerate(credit_txs[:10], 1):
        print(f"  {i}. {tx['trans_date']:12} ${tx['amount']:>10} - {tx['description'][:50]}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"[+] Raw text length: {len(raw_text)} characters")
    print(f"[+] Bank pattern matches: {len(bank_txs)}")
    print(f"[+] Credit pattern matches: {len(credit_txs)}")
    print("\n[!] These are simple pattern matches - the actual extraction service")
    print("    may use different patterns. Check backend/src/services/extraction_service.py")

if __name__ == "__main__":
    main()
