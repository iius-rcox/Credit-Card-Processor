#!/usr/bin/env python3
"""
Quick test to verify matching works after refactor fixes.
"""
import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000/api"
TEST_PDF = Path("backend/test-upload.pdf")

def test_matching():
    """Test upload and matching workflow."""
    print("Testing Matching Workflow (Post-Refactor Fix)")
    print("=" * 60)

    # 1. Upload PDF
    print(f"\n1. Uploading {TEST_PDF.name}...")
    with open(TEST_PDF, 'rb') as f:
        files = {'files': (TEST_PDF.name, f, 'application/pdf')}
        response = requests.post(f"{API_URL}/upload", files=files, timeout=120)

    if response.status_code != 202:
        print(f"FAIL: Upload failed with status {response.status_code}")
        print(response.text)
        return False

    session_data = response.json()
    session_id = session_data['id']
    print(f"   Session ID: {session_id}")
    print(f"   Initial status: {session_data['status']}")

    # 2. Poll for completion
    print("\n2. Polling for completion...")
    max_polls = 30
    for i in range(max_polls):
        time.sleep(2)
        response = requests.get(f"{API_URL}/sessions/{session_id}")

        if response.status_code != 200:
            print(f"FAIL: Status check failed with {response.status_code}")
            return False

        data = response.json()
        status = data['status']
        print(f"   Poll {i+1}: status={status}")

        if status == 'completed':
            print("\n3. SUCCESS!")
            print(f"   Final status: {status}")
            print(f"   Transactions: {data.get('total_transactions', 0)}")
            print(f"   Receipts: {data.get('total_receipts', 0)}")
            print(f"   Matches: {data.get('matched_count', 0)}")
            return True

        elif status == 'failed':
            print(f"\n3. FAIL: Session marked as failed")
            return False

    print(f"\n3. TIMEOUT: Session still {status} after {max_polls} polls")
    return False

if __name__ == "__main__":
    try:
        success = test_matching()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        exit(1)
