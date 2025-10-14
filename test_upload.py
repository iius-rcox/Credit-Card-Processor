#!/usr/bin/env python3
"""
Test script for the refactored PDF extraction.
Tests inline extraction during upload.
"""
import requests
import json
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000/api/upload"
TEST_PDF = Path(__file__).parent / "backend" / "test-upload.pdf"

def test_upload():
    """Test PDF upload with inline extraction."""
    print("=" * 80)
    print("Testing Refactored PDF Extraction (Feature 008)")
    print("=" * 80)
    print(f"\nTest PDF: {TEST_PDF}")
    print(f"File size: {TEST_PDF.stat().st_size / 1024:.2f} KB")

    if not TEST_PDF.exists():
        print(f"ERROR: Test PDF not found at {TEST_PDF}")
        return

    # Upload the PDF
    print(f"\nUploading to {API_URL}...")
    start_time = time.time()

    try:
        with open(TEST_PDF, 'rb') as f:
            files = {'files': (TEST_PDF.name, f, 'application/pdf')}
            response = requests.post(API_URL, files=files, timeout=120)

        upload_time = time.time() - start_time

        print(f"\n✓ Upload completed in {upload_time:.2f}s")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\nResponse Data:")
            print(json.dumps(data, indent=2, default=str))

            # Verify expected fields
            print("\n" + "=" * 80)
            print("Verification:")
            print("=" * 80)

            session_id = data.get('id')
            status = data.get('status')
            upload_count = data.get('upload_count')
            total_transactions = data.get('total_transactions')

            print(f"✓ Session ID: {session_id}")
            print(f"✓ Status: {status}")
            print(f"✓ Upload Count: {upload_count}")
            print(f"✓ Total Transactions: {total_transactions}")

            # Expected: status should be 'matching' (not 'processing')
            if status == 'matching':
                print("\n✅ SUCCESS: Extraction completed inline during upload!")
                print("   Status is 'matching' - extraction phase complete")
            elif status == 'extracting':
                print("\n⚠️  PARTIAL: Extraction in progress")
            else:
                print(f"\n❌ UNEXPECTED: Status is '{status}' (expected 'matching' or 'extracting')")

            # Check if transactions were extracted
            if total_transactions and total_transactions > 0:
                print(f"✅ SUCCESS: {total_transactions} transactions extracted!")
            else:
                print("⚠️  WARNING: No transactions extracted (check PDF content)")

        else:
            print(f"\n❌ Upload failed with status {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timed out after 120s")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {API_URL}")
        print("   Make sure backend is running: docker ps")
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_upload()
