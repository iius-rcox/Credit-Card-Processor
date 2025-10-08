"""
Progress calculation service for multi-file aggregate progress.

This module provides calculation methods for determining progress
across multiple files and phases.
"""

from typing import List, Dict, Any


class ProgressCalculator:
    """
    Calculates aggregate progress across multiple files and phases.

    This class provides methods for calculating:
    - File-level progress
    - Multi-file aggregate progress
    - Phase-weighted overall progress
    """

    @staticmethod
    def calculate_file_progress(current_page: int, total_pages: int) -> float:
        """
        Calculate progress percentage for a single file.

        Args:
            current_page: Current page being processed (1-indexed)
            total_pages: Total number of pages in the file

        Returns:
            Progress percentage (0.0-100.0)
        """
        if total_pages <= 0:
            return 0.0

        # Ensure current_page is within bounds
        current_page = max(1, min(current_page, total_pages))

        return (current_page / total_pages) * 100.0

    @staticmethod
    def calculate_multi_file_progress(
        current_file_index: int,
        total_files: int,
        current_page: int,
        total_pages_current_file: int
    ) -> float:
        """
        Calculate aggregate progress across multiple files.

        This method assumes all files have equal weight in the overall progress.

        Args:
            current_file_index: Index of the current file (1-indexed)
            total_files: Total number of files to process
            current_page: Current page in the current file (1-indexed)
            total_pages_current_file: Total pages in the current file

        Returns:
            Aggregate progress percentage (0.0-100.0)

        Example:
            - File 1: 100 pages (complete) → 33.33% of aggregate
            - File 2: 50 pages, page 25 → 16.67% of aggregate
            - File 3: 200 pages (not started) → 0% of aggregate
            - Total aggregate: 50%
        """
        if total_files <= 0:
            return 0.0

        # Ensure indices are within bounds
        current_file_index = max(1, min(current_file_index, total_files))

        # Calculate completed files contribution
        files_completed = current_file_index - 1
        completed_contribution = (files_completed / total_files) * 100.0

        # Calculate current file contribution
        if total_pages_current_file > 0:
            file_progress = ProgressCalculator.calculate_file_progress(
                current_page, total_pages_current_file
            )
            current_file_contribution = (file_progress / 100.0) * (100.0 / total_files)
        else:
            current_file_contribution = 0.0

        return min(100.0, completed_contribution + current_file_contribution)

    @staticmethod
    def calculate_weighted_multi_file_progress(
        files_progress: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate weighted aggregate progress across multiple files.

        This method allows files to have different weights based on their size.

        Args:
            files_progress: List of file progress dictionaries, each containing:
                - 'total_pages': Total pages in the file
                - 'current_page': Current page being processed (0 if not started)
                - 'completed': Boolean indicating if file is complete

        Returns:
            Weighted aggregate progress percentage (0.0-100.0)
        """
        if not files_progress:
            return 0.0

        # Calculate total pages across all files
        total_pages_all_files = sum(
            f.get('total_pages', 0) for f in files_progress
        )

        if total_pages_all_files <= 0:
            return 0.0

        # Calculate weighted progress
        total_progress = 0.0
        for file_info in files_progress:
            total_pages = file_info.get('total_pages', 0)
            if total_pages <= 0:
                continue

            # Calculate file weight based on page count
            weight = total_pages / total_pages_all_files

            # Calculate file progress
            if file_info.get('completed', False):
                file_progress = 100.0
            else:
                current_page = file_info.get('current_page', 0)
                file_progress = ProgressCalculator.calculate_file_progress(
                    current_page, total_pages
                )

            # Add weighted contribution
            total_progress += weight * file_progress

        return min(100.0, total_progress)

    @staticmethod
    def calculate_phase_weighted_overall(
        phases: Dict[str, Dict[str, Any]],
        phase_weights: Dict[str, float]
    ) -> float:
        """
        Calculate overall progress with weighted phases.

        Args:
            phases: Dictionary of phase names to phase info containing 'percentage'
            phase_weights: Dictionary of phase names to their weights (must sum to 1.0)

        Returns:
            Weighted overall progress percentage (0.0-100.0)

        Example:
            phases = {
                "upload": {"percentage": 100},
                "processing": {"percentage": 50},
                "matching": {"percentage": 0},
                "report_generation": {"percentage": 0}
            }
            weights = {
                "upload": 0.1,
                "processing": 0.6,
                "matching": 0.2,
                "report_generation": 0.1
            }
            Result: 40.0 (10 + 30 + 0 + 0)
        """
        overall = 0.0

        for phase_name, phase_info in phases.items():
            if phase_name in phase_weights:
                weight = phase_weights[phase_name]
                percentage = phase_info.get('percentage', 0)
                overall += weight * percentage

        return min(100.0, overall)

    @staticmethod
    def estimate_time_remaining(
        current_progress: float,
        elapsed_seconds: float
    ) -> float:
        """
        Estimate time remaining based on current progress.

        Args:
            current_progress: Current progress percentage (0.0-100.0)
            elapsed_seconds: Time elapsed so far in seconds

        Returns:
            Estimated seconds remaining (0.0 if complete or no progress)
        """
        if current_progress <= 0 or current_progress >= 100:
            return 0.0

        # Calculate rate of progress
        rate = current_progress / elapsed_seconds  # percent per second

        # Calculate remaining progress
        remaining_progress = 100.0 - current_progress

        # Estimate time remaining
        return remaining_progress / rate

    @staticmethod
    def calculate_processing_rate(
        pages_processed: int,
        elapsed_seconds: float
    ) -> float:
        """
        Calculate the processing rate in pages per second.

        Args:
            pages_processed: Number of pages processed
            elapsed_seconds: Time elapsed in seconds

        Returns:
            Pages per second rate
        """
        if elapsed_seconds <= 0:
            return 0.0

        return pages_processed / elapsed_seconds

    @staticmethod
    def format_progress_percentage(percentage: float) -> int:
        """
        Format a progress percentage for display.

        Args:
            percentage: Raw percentage value (0.0-100.0)

        Returns:
            Rounded integer percentage (0-100)
        """
        return min(100, max(0, round(percentage)))