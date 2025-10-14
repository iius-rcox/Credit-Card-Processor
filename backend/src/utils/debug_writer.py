"""
Debug file output utilities.

This module provides functions for writing debug output files during PDF extraction.
Only enabled in development environment with DEBUG_EXTRACTION_OUTPUT flag.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional
from uuid import UUID
from datetime import datetime

from ..config import settings, is_development

logger = logging.getLogger(__name__)


def write_debug_file(
    session_id: UUID,
    file_name: str,
    content: Any,
    file_type: str = "json"
) -> Optional[Path]:
    """
    Write debug output file if debug mode enabled.

    Only writes files when:
    - ENVIRONMENT == "development"
    - DEBUG_EXTRACTION_OUTPUT == true

    Files are organized by session ID and include timestamps.

    Args:
        session_id: Session UUID for organizing files
        file_name: Base name for debug file (e.g., "01_cardholder_text")
        content: Content to write (str for txt, dict/list for json)
        file_type: "json" or "txt"

    Returns:
        Path to written file, or None if debug disabled

    Example:
        write_debug_file(
            session_id=session.id,
            file_name="01_cardholder_text",
            content=extracted_text,
            file_type="txt"
        )

    Note:
        Errors are logged but don't raise exceptions to prevent
        debug functionality from breaking the upload process.
    """
    # Safety check: Only in development with flag enabled
    if not is_development() or not settings.DEBUG_EXTRACTION_OUTPUT:
        return None

    try:
        # Create output directory organized by session ID
        output_dir = Path(settings.DEBUG_OUTPUT_PATH) / str(session_id)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build file path with timestamp for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = "json" if file_type == "json" else "txt"
        output_file = output_dir / f"{timestamp}_{file_name}.{extension}"

        # Write content based on type
        if file_type == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, default=str)
        else:
            # Text file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(str(content))

        logger.info(f"[DEBUG_FILE] Wrote debug output: {output_file}")
        logger.info(f"[DEBUG_FILE]   Type: {file_type}, Size: {output_file.stat().st_size} bytes")

        return output_file

    except Exception as e:
        # Log error but don't raise - debug failures shouldn't break uploads
        logger.error(f"[DEBUG_FILE] Failed to write debug file '{file_name}': {e}")
        return None


def write_debug_text(session_id: UUID, file_name: str, text: str) -> Optional[Path]:
    """
    Write debug text file (convenience wrapper).

    Args:
        session_id: Session UUID
        file_name: Base name for file
        text: Text content to write

    Returns:
        Path to written file, or None if debug disabled
    """
    return write_debug_file(session_id, file_name, text, file_type="txt")


def write_debug_json(session_id: UUID, file_name: str, data: dict) -> Optional[Path]:
    """
    Write debug JSON file (convenience wrapper).

    Args:
        session_id: Session UUID
        file_name: Base name for file
        data: Dictionary to write as JSON

    Returns:
        Path to written file, or None if debug disabled
    """
    return write_debug_file(session_id, file_name, data, file_type="json")
