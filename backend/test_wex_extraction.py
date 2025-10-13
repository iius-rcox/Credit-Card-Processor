"""
Test script to verify WEX format extraction with updated patterns.
"""

import asyncio
import pdfplumber
from pathlib import Path
from src.services.extraction_service import ExtractionService

async def test_extraction():
    # Create extraction service
    service = ExtractionService(
        session_repo=None,  # type: ignore
        employee_repo=None,  # type: ignore
        transaction_repo=None,  # type: ignore
        receipt_repo=None,  # type: ignore
        progress_repo=None,
        alias_repo=None
    )

    # Path to test PDF
    pdf_path = Path(r"C:\Users\rcox\OneDrive - INSULATIONS, INC\Documents\Expense Splitter\Cardholder+Activity+Report+General-S-89S,DD2LJ,DFRHA (6).pdf")

    print(f"Testing extraction with: {pdf_path.name}")
    print("=" * 80)

    # Extract text
    text = service._extract_text(pdf_path)
    print(f"\n[OK] Text extracted: {len(text)} characters, {len(text.split(chr(10)))} lines")

    # Extract transactions
    transactions = await service._extract_credit_transactions(text)
    print(f"\n[OK] Transactions extracted: {len(transactions)}")

    # Show first 5 transactions
    print("\n=== First 5 Transactions ===")
    for i, tx in enumerate(transactions[:5]):
        print(f"\nTransaction {i+1}:")
        print(f"  Date: {tx.get('transaction_date')}")
        print(f"  Amount: {tx.get('amount')}")
        print(f"  Merchant: {tx.get('merchant_name')}")
        print(f"  Address: {tx.get('merchant_address')}")
        print(f"  Expense Type: {tx.get('expense_type')}")
        print(f"  Is Credit: {tx.get('is_credit')}")
        print(f"  Incomplete: {tx.get('incomplete_flag')}")
        print(f"  Employee Name (from header): {tx['raw_data']['extracted_fields'].get('employee_name')}")

    # Count flags
    incomplete_count = sum(1 for tx in transactions if tx.get('incomplete_flag'))
    credit_count = sum(1 for tx in transactions if tx.get('is_credit'))

    print(f"\n=== Summary ===")
    print(f"Total Transactions: {len(transactions)}")
    print(f"Incomplete: {incomplete_count}")
    print(f"Credits/Refunds: {credit_count}")
    print(f"Complete: {len(transactions) - incomplete_count}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
