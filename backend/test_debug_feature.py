#!/usr/bin/env python3
"""
Test the debug extraction output feature.
Creates a simple test PDF with actual content to trigger extraction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pathlib import Path
from uuid import uuid4
from src.utils.debug_writer import write_debug_text, write_debug_json

# Test writing debug files
session_id = uuid4()

print(f"Testing debug writer with session ID: {session_id}")
print("=" * 60)

# Test text file
text_result = write_debug_text(
    session_id=session_id,
    file_name="01_test_text",
    text="This is a test of the debug text output.\nLine 2\nLine 3"
)

if text_result:
    print(f"✓ Text file written: {text_result}")
else:
    print("✗ Text file NOT written (debug disabled or not in development)")

# Test JSON file
json_result = write_debug_json(
    session_id=session_id,
    file_name="03_test_json",
    data={
        "test": "value",
        "number": 123,
        "nested": {"key": "value"},
        "session_id": str(session_id)
    }
)

if json_result:
    print(f"✓ JSON file written: {json_result}")
else:
    print("✗ JSON file NOT written (debug disabled or not in development)")

# Check what files were created
debug_dir = Path("./debug_output") / str(session_id)
if debug_dir.exists():
    print(f"\n✓ Debug directory created: {debug_dir}")
    files = list(debug_dir.glob("*"))
    print(f"  Files created: {len(files)}")
    for f in files:
        print(f"    - {f.name} ({f.stat().st_size} bytes)")
else:
    print(f"\n✗ Debug directory not found: {debug_dir}")

print("\nConfiguration check:")
from src.config import settings, is_development
print(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"  is_development(): {is_development()}")
print(f"  DEBUG_EXTRACTION_OUTPUT: {settings.DEBUG_EXTRACTION_OUTPUT}")
print(f"  DEBUG_OUTPUT_PATH: {settings.DEBUG_OUTPUT_PATH}")
