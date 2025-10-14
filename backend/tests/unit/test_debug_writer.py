"""
Unit tests for debug_writer module.

Tests debug file output functionality with various configurations.
"""

import json
import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.utils.debug_writer import write_debug_file, write_debug_text, write_debug_json


@pytest.fixture
def session_id():
    """Generate a test session ID."""
    return uuid4()


@pytest.fixture
def temp_debug_path(tmp_path):
    """Create temporary debug output path."""
    return tmp_path / "debug_output"


@pytest.fixture
def mock_settings_development(temp_debug_path):
    """Mock settings for development environment with debug enabled."""
    with patch('src.utils.debug_writer.settings') as mock_settings, \
         patch('src.utils.debug_writer.is_development') as mock_is_dev:
        mock_settings.DEBUG_EXTRACTION_OUTPUT = True
        mock_settings.DEBUG_OUTPUT_PATH = str(temp_debug_path)
        mock_is_dev.return_value = True
        yield mock_settings


@pytest.fixture
def mock_settings_production():
    """Mock settings for production environment."""
    with patch('src.utils.debug_writer.settings') as mock_settings, \
         patch('src.utils.debug_writer.is_development') as mock_is_dev:
        mock_settings.DEBUG_EXTRACTION_OUTPUT = True
        mock_settings.DEBUG_OUTPUT_PATH = "./debug_output"
        mock_is_dev.return_value = False  # Production
        yield mock_settings


@pytest.fixture
def mock_settings_flag_disabled(temp_debug_path):
    """Mock settings with debug flag disabled."""
    with patch('src.utils.debug_writer.settings') as mock_settings, \
         patch('src.utils.debug_writer.is_development') as mock_is_dev:
        mock_settings.DEBUG_EXTRACTION_OUTPUT = False  # Flag disabled
        mock_settings.DEBUG_OUTPUT_PATH = str(temp_debug_path)
        mock_is_dev.return_value = True
        yield mock_settings


def test_write_debug_file_production_disabled(session_id, mock_settings_production):
    """Test that debug files are NOT written in production environment."""
    result = write_debug_file(
        session_id=session_id,
        file_name="test_file",
        content="test content",
        file_type="txt"
    )

    assert result is None, "Debug file should not be written in production"


def test_write_debug_file_flag_disabled(session_id, mock_settings_flag_disabled):
    """Test that debug files are NOT written when flag is disabled."""
    result = write_debug_file(
        session_id=session_id,
        file_name="test_file",
        content="test content",
        file_type="txt"
    )

    assert result is None, "Debug file should not be written when flag disabled"


def test_write_debug_file_text(session_id, mock_settings_development, temp_debug_path):
    """Test writing text debug file."""
    test_content = "This is test content\nLine 2\nLine 3"

    result = write_debug_file(
        session_id=session_id,
        file_name="test_text",
        content=test_content,
        file_type="txt"
    )

    assert result is not None, "Debug file path should be returned"
    assert result.exists(), "Debug file should exist"
    assert result.suffix == ".txt", "File should have .txt extension"
    assert "test_text" in result.name, "Filename should contain base name"

    # Verify content
    content = result.read_text(encoding="utf-8")
    assert content == test_content, "File content should match input"


def test_write_debug_file_json(session_id, mock_settings_development, temp_debug_path):
    """Test writing JSON debug file."""
    test_data = {
        "key": "value",
        "number": 123,
        "nested": {"inner": "data"},
        "list": [1, 2, 3]
    }

    result = write_debug_file(
        session_id=session_id,
        file_name="test_json",
        content=test_data,
        file_type="json"
    )

    assert result is not None, "Debug file path should be returned"
    assert result.exists(), "Debug file should exist"
    assert result.suffix == ".json", "File should have .json extension"

    # Verify content
    with open(result, 'r', encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data == test_data, "JSON content should match input"


def test_write_debug_file_creates_directory(session_id, mock_settings_development, temp_debug_path):
    """Test that debug writer creates necessary directories."""
    # Ensure directory doesn't exist
    session_dir = temp_debug_path / str(session_id)
    assert not session_dir.exists(), "Session directory should not exist yet"

    # Write file
    result = write_debug_file(
        session_id=session_id,
        file_name="test",
        content="test",
        file_type="txt"
    )

    assert result is not None
    assert session_dir.exists(), "Session directory should be created"
    assert session_dir.is_dir(), "Should be a directory"


def test_write_debug_file_handles_errors(session_id):
    """Test graceful error handling when write fails."""
    with patch('src.utils.debug_writer.settings') as mock_settings, \
         patch('src.utils.debug_writer.is_development') as mock_is_dev, \
         patch('src.utils.debug_writer.Path.mkdir') as mock_mkdir:
        mock_settings.DEBUG_EXTRACTION_OUTPUT = True
        mock_settings.DEBUG_OUTPUT_PATH = "/test/path"
        mock_is_dev.return_value = True

        # Simulate directory creation failure
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # Should return None instead of raising exception
        result = write_debug_file(
            session_id=session_id,
            file_name="test",
            content="test",
            file_type="txt"
        )

        assert result is None, "Should return None on error, not raise exception"


def test_write_debug_file_serializes_types(session_id, mock_settings_development, temp_debug_path):
    """Test JSON serialization of complex types (UUID, Decimal, datetime)."""
    from datetime import datetime

    test_data = {
        "uuid": uuid4(),
        "decimal": Decimal("123.45"),
        "datetime": datetime.utcnow(),
        "date": datetime.utcnow().date()
    }

    result = write_debug_file(
        session_id=session_id,
        file_name="test_types",
        content=test_data,
        file_type="json"
    )

    assert result is not None, "Should handle complex types"
    assert result.exists(), "File should be created"

    # Verify it's valid JSON
    with open(result, 'r', encoding="utf-8") as f:
        loaded_data = json.load(f)

    # All types should be serialized to strings
    assert isinstance(loaded_data["uuid"], str)
    assert isinstance(loaded_data["decimal"], str)
    assert isinstance(loaded_data["datetime"], str)
    assert isinstance(loaded_data["date"], str)


def test_write_debug_text_convenience(session_id, mock_settings_development, temp_debug_path):
    """Test write_debug_text convenience wrapper."""
    result = write_debug_text(
        session_id=session_id,
        file_name="convenience_test",
        text="test content"
    )

    assert result is not None
    assert result.suffix == ".txt"


def test_write_debug_json_convenience(session_id, mock_settings_development, temp_debug_path):
    """Test write_debug_json convenience wrapper."""
    result = write_debug_json(
        session_id=session_id,
        file_name="convenience_test",
        data={"test": "data"}
    )

    assert result is not None
    assert result.suffix == ".json"


def test_timestamp_in_filename(session_id, mock_settings_development, temp_debug_path):
    """Test that filename includes timestamp for uniqueness."""
    import time

    result1 = write_debug_text(session_id, "test", "content1")
    time.sleep(1.1)  # Ensure different timestamp (second precision)
    result2 = write_debug_text(session_id, "test", "content2")

    # Different files should be created
    assert result1 != result2, "Different timestamps should create different files"
    assert result1.exists() and result2.exists(), "Both files should exist"


def test_session_organization(mock_settings_development, temp_debug_path):
    """Test that files are organized by session ID."""
    session1 = uuid4()
    session2 = uuid4()

    file1 = write_debug_text(session1, "test", "content1")
    file2 = write_debug_text(session2, "test", "content2")

    assert file1.parent.name == str(session1), "File should be in session1 directory"
    assert file2.parent.name == str(session2), "File should be in session2 directory"
    assert file1.parent != file2.parent, "Different sessions should have different directories"
