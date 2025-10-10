"""
Unit tests specifically for aggregate progress calculation formulas.

Tests multi-file aggregation and phase-weighted overall progress calculations
with various edge cases.
"""

import pytest
from src.services.progress_calculator import ProgressCalculator


class TestAggregateCalculations:
    """Test suite for aggregate progress calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ProgressCalculator()

    def test_aggregate_single_file_scenarios(self):
        """Test aggregate calculation with single file scenarios."""
        # Single file not started
        result = self.calculator.calculate_multi_file_progress(1, 1, 0, 100)
        assert result == 0.0

        # Single file halfway
        result = self.calculator.calculate_multi_file_progress(1, 1, 50, 100)
        assert result == 50.0

        # Single file complete
        result = self.calculator.calculate_multi_file_progress(1, 1, 100, 100)
        assert result == 100.0

    def test_aggregate_equal_sized_files(self):
        """Test aggregate with files of equal size."""
        # 3 files, each 100 pages
        # File 1: complete (100%)
        # File 2: halfway (50%)
        # File 3: not started (0%)
        # Expected: (1 + 0.5 + 0) / 3 = 50%

        # Currently on file 2, page 50 of 100
        result = self.calculator.calculate_multi_file_progress(2, 3, 50, 100)
        assert result == pytest.approx(50.0, rel=1e-2)

    def test_aggregate_different_sized_files_weighted(self):
        """Test weighted aggregate with different file sizes."""
        files = [
            {"total_pages": 10, "current_page": 10, "completed": True},    # Small file complete
            {"total_pages": 100, "current_page": 50, "completed": False},  # Large file halfway
            {"total_pages": 40, "current_page": 0, "completed": False}     # Medium file not started
        ]

        # Total: 150 pages
        # Complete: 10 + 50 + 0 = 60 pages
        # Expected: 60/150 = 40%
        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert result == pytest.approx(40.0, rel=1e-2)

    def test_aggregate_edge_case_empty_files(self):
        """Test aggregate with empty files (0 pages)."""
        files = [
            {"total_pages": 0, "current_page": 0, "completed": False},
            {"total_pages": 100, "current_page": 50, "completed": False},
            {"total_pages": 0, "current_page": 0, "completed": False}
        ]

        # Only count file with pages
        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert result == pytest.approx(50.0, rel=1e-2)

    def test_aggregate_all_files_complete(self):
        """Test aggregate when all files are complete."""
        files = [
            {"total_pages": 50, "completed": True},
            {"total_pages": 100, "completed": True},
            {"total_pages": 75, "completed": True}
        ]

        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert result == 100.0

    def test_phase_weighted_overall_standard_workflow(self):
        """Test standard workflow phase progression."""
        # Standard weights
        weights = {
            "upload": 0.1,
            "processing": 0.6,
            "matching": 0.2,
            "report_generation": 0.1
        }

        # Scenario 1: Upload complete
        phases = {
            "upload": {"percentage": 100},
            "processing": {"percentage": 0},
            "matching": {"percentage": 0},
            "report_generation": {"percentage": 0}
        }
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 10.0

        # Scenario 2: Upload complete, processing halfway
        phases["processing"]["percentage"] = 50
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 40.0  # 10 + 30

        # Scenario 3: First two phases complete
        phases["processing"]["percentage"] = 100
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 70.0  # 10 + 60

        # Scenario 4: First three phases complete
        phases["matching"]["percentage"] = 100
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 90.0  # 10 + 60 + 20

        # Scenario 5: All complete
        phases["report_generation"]["percentage"] = 100
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == 100.0

    def test_phase_weighted_overall_custom_weights(self):
        """Test phase calculation with custom weight distributions."""
        phases = {
            "phase1": {"percentage": 75},
            "phase2": {"percentage": 50},
            "phase3": {"percentage": 25}
        }

        # Equal weights
        weights = {"phase1": 0.333, "phase2": 0.333, "phase3": 0.334}
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(50.0, rel=1e-1)

        # Heavy first phase
        weights = {"phase1": 0.8, "phase2": 0.1, "phase3": 0.1}
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(67.5, rel=1e-1)  # 60 + 5 + 2.5

        # Heavy last phase
        weights = {"phase1": 0.1, "phase2": 0.1, "phase3": 0.8}
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(27.5, rel=1e-1)  # 7.5 + 5 + 20

    def test_phase_weighted_overall_missing_phases(self):
        """Test phase calculation when some phases are missing from data."""
        phases = {
            "upload": {"percentage": 100},
            "processing": {"percentage": 75}
            # Missing matching and report_generation
        }

        weights = {
            "upload": 0.1,
            "processing": 0.6,
            "matching": 0.2,
            "report_generation": 0.1
        }

        # Should only calculate for existing phases
        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(55.0, rel=1e-1)  # 10 + 45

    def test_aggregate_boundary_conditions(self):
        """Test aggregate calculations at boundaries."""
        # First file, first page
        result = self.calculator.calculate_multi_file_progress(1, 5, 1, 100)
        assert result == pytest.approx(0.2, rel=1e-1)

        # Last file, last page
        result = self.calculator.calculate_multi_file_progress(5, 5, 100, 100)
        assert result == 100.0

        # Middle file boundaries
        result = self.calculator.calculate_multi_file_progress(3, 5, 1, 50)
        assert result == pytest.approx(40.4, rel=1e-1)  # 2 files complete + 1 page

        result = self.calculator.calculate_multi_file_progress(3, 5, 50, 50)
        assert result == pytest.approx(60.0, rel=1e-1)  # 3 files complete

    def test_aggregate_large_file_counts(self):
        """Test aggregate with large number of files."""
        # 100 files, currently on file 50, halfway through
        result = self.calculator.calculate_multi_file_progress(50, 100, 50, 100)
        assert result == pytest.approx(49.5, rel=1e-1)

        # 1000 files, currently on file 999
        result = self.calculator.calculate_multi_file_progress(999, 1000, 50, 100)
        assert result == pytest.approx(99.85, rel=1e-1)

    def test_weighted_aggregate_performance_characteristics(self):
        """Test weighted aggregate maintains performance with many files."""
        # Create large file list
        files = []
        for i in range(100):
            files.append({
                "total_pages": (i + 1) * 10,  # Varying sizes
                "current_page": (i + 1) * 5 if i < 50 else (i + 1) * 10,
                "completed": i < 50
            })

        result = self.calculator.calculate_weighted_multi_file_progress(files)
        assert 0 <= result <= 100  # Should still be within valid range

    def test_phase_weighted_precision(self):
        """Test phase weighted calculation precision."""
        phases = {
            "p1": {"percentage": 33.333},
            "p2": {"percentage": 66.666},
            "p3": {"percentage": 99.999}
        }
        weights = {
            "p1": 0.33333,
            "p2": 0.33333,
            "p3": 0.33334
        }

        result = self.calculator.calculate_phase_weighted_overall(phases, weights)
        assert result == pytest.approx(66.666, rel=1e-2)

    def test_aggregate_zero_total_files(self):
        """Test aggregate calculation with zero total files."""
        result = self.calculator.calculate_multi_file_progress(0, 0, 0, 0)
        assert result == 0.0

        # Invalid state: current file index but zero total
        result = self.calculator.calculate_multi_file_progress(1, 0, 50, 100)
        assert result == 0.0  # Should handle gracefully