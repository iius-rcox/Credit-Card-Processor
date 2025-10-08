"""
Unit tests for ProgressCalculator service.

Tests the calculation methods for file-level, multi-file, and phase-weighted
progress calculations.
"""

import pytest
from decimal import Decimal

from src.services.progress_calculator import ProgressCalculator


class TestProgressCalculator:
    """Test suite for ProgressCalculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ProgressCalculator()

    def test_calculate_file_progress_zero_pages(self):
        """Test file progress calculation with zero pages."""
        result = self.calculator.calculate_file_progress(0, 0)
        assert result == 0.0

    def test_calculate_file_progress_single_page(self):
        """Test file progress calculation with single page."""
        result = self.calculator.calculate_file_progress(1, 1)
        assert result == 100.0

    def test_calculate_file_progress_partial(self):
        """Test file progress calculation with partial progress."""
        result = self.calculator.calculate_file_progress(5, 10)
        assert result == 50.0

        result = self.calculator.calculate_file_progress(3, 4)
        assert result == 75.0

        result = self.calculator.calculate_file_progress(1, 100)
        assert result == 1.0

    def test_calculate_file_progress_complete(self):
        """Test file progress calculation when complete."""
        result = self.calculator.calculate_file_progress(100, 100)
        assert result == 100.0

    def test_calculate_file_progress_bounds_checking(self):
        """Test file progress with out-of-bounds values."""
        # Current page exceeds total
        result = self.calculator.calculate_file_progress(15, 10)
        assert result == 100.0  # Should be capped at 100%

        # Current page is 0 (should be treated as 1)
        result = self.calculator.calculate_file_progress(0, 10)
        assert result == 10.0  # Treated as page 1 of 10

    def test_calculate_multi_file_progress_single_file(self):
        """Test multi-file progress with single file."""
        result = self.calculator.calculate_multi_file_progress(1, 1, 50, 100)
        assert result == 50.0

    def test_calculate_multi_file_progress_multiple_files(self):
        """Test multi-file progress with multiple files."""
        # First file complete, second file halfway
        result = self.calculator.calculate_multi_file_progress(2, 3, 50, 100)
        assert result == pytest.approx(50.0, rel=1e-2)

        # Three files: first two complete, third at 25%
        result = self.calculator.calculate_multi_file_progress(3, 3, 25, 100)
        assert result == pytest.approx(75.0, rel=1e-2)

    def test_calculate_multi_file_progress_no_files(self):
        """Test multi-file progress with no files."""
        result = self.calculator.calculate_multi_file_progress(0, 0, 0, 0)
        assert result == 0.0

    def test_calculate_multi_file_progress_first_file(self):
        """Test multi-file progress on first file."""
        result = self.calculator.calculate_multi_file_progress(1, 5, 10, 100)
        assert result == pytest.approx(2.0, rel=1e-2)  # 10% of first file = 2% overall

    def test_calculate_multi_file_progress_last_file(self):
        """Test multi-file progress on last file."""
        result = self.calculator.calculate_multi_file_progress(5, 5, 100, 100)
        assert result == 100.0

    def test_calculate_weighted_multi_file_progress_empty(self):
        """Test weighted multi-file progress with no files."""
        result = self.calculator.calculate_weighted_multi_file_progress([])
        assert result == 0.0

    def test_calculate_weighted_multi_file_progress_single_complete(self):
        """Test weighted multi-file progress with single complete file."""
        files = [{
            'total_pages': 100,
            'current_page': 100,
            'completed': True
        }]
        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert result == 100.0

    def test_calculate_weighted_multi_file_progress_mixed(self):
        """Test weighted multi-file progress with files of different sizes."""
        files = [
            {'total_pages': 100, 'current_page': 100, 'completed': True},  # 100 pages complete
            {'total_pages': 50, 'current_page': 25, 'completed': False},   # 50 pages, 50% done
            {'total_pages': 200, 'current_page': 0, 'completed': False}    # 200 pages, not started
        ]
        # Total pages: 350
        # Progress: 100 + 25 + 0 = 125 pages done
        # Expected: 125/350 * 100 = ~35.71%
        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert result == pytest.approx(35.71, rel=1e-1)

    def test_calculate_phase_weighted_overall_basic(self):
        """Test phase-weighted overall calculation."""
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
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 40.0  # 10 + 30 + 0 + 0

    def test_calculate_phase_weighted_overall_complete(self):
        """Test phase-weighted overall when all phases complete."""
        phases = {
            "upload": {"percentage": 100},
            "processing": {"percentage": 100},
            "matching": {"percentage": 100},
            "report_generation": {"percentage": 100}
        }
        weights = {
            "upload": 0.1,
            "processing": 0.6,
            "matching": 0.2,
            "report_generation": 0.1
        }
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 100.0

    def test_calculate_phase_weighted_overall_uneven_weights(self):
        """Test phase-weighted overall with uneven weights."""
        phases = {
            "phase1": {"percentage": 80},
            "phase2": {"percentage": 60}
        }
        weights = {
            "phase1": 0.7,  # 70% weight
            "phase2": 0.3   # 30% weight
        }
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(74.0, rel=1e-2)  # 56 + 18

    def test_estimate_time_remaining_no_progress(self):
        """Test time estimation with no progress."""
        result = self.calculator.estimate_time_remaining(0.0, 100.0)
        assert result == 0.0

    def test_estimate_time_remaining_complete(self):
        """Test time estimation when complete."""
        result = self.calculator.estimate_time_remaining(100.0, 100.0)
        assert result == 0.0

    def test_estimate_time_remaining_halfway(self):
        """Test time estimation at halfway point."""
        result = self.calculator.estimate_time_remaining(50.0, 60.0)
        assert result == pytest.approx(60.0, rel=1e-2)  # 50% more at same rate

    def test_estimate_time_remaining_various(self):
        """Test time estimation with various progress levels."""
        # 25% done in 30 seconds -> 90 seconds remaining
        result = self.calculator.estimate_time_remaining(25.0, 30.0)
        assert result == pytest.approx(90.0, rel=1e-2)

        # 90% done in 45 seconds -> 5 seconds remaining
        result = self.calculator.estimate_time_remaining(90.0, 45.0)
        assert result == pytest.approx(5.0, rel=1e-2)

    def test_calculate_processing_rate_zero_time(self):
        """Test processing rate with zero time."""
        result = self.calculator.calculate_processing_rate(100, 0.0)
        assert result == 0.0

    def test_calculate_processing_rate_normal(self):
        """Test processing rate calculation."""
        result = self.calculator.calculate_processing_rate(100, 10.0)
        assert result == 10.0  # 10 pages per second

        result = self.calculator.calculate_processing_rate(50, 25.0)
        assert result == 2.0  # 2 pages per second

    def test_format_progress_percentage_bounds(self):
        """Test formatting progress percentage with bounds checking."""
        assert self.calculator.format_progress_percentage(-10.5) == 0
        assert self.calculator.format_progress_percentage(0.0) == 0
        assert self.calculator.format_progress_percentage(50.5) == 51
        assert self.calculator.format_progress_percentage(99.9) == 100
        assert self.calculator.format_progress_percentage(100.0) == 100
        assert self.calculator.format_progress_percentage(150.0) == 100

    def test_format_progress_percentage_rounding(self):
        """Test formatting progress percentage rounding."""
        assert self.calculator.format_progress_percentage(33.3) == 33
        assert self.calculator.format_progress_percentage(33.5) == 34
        assert self.calculator.format_progress_percentage(33.7) == 34
        assert self.calculator.format_progress_percentage(66.4) == 66
        assert self.calculator.format_progress_percentage(66.6) == 67