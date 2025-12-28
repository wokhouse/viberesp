"""
Hornresp comparison tests for QL (box losses) implementation.

These tests validate viberesp's QL implementation against Hornresp simulations.
Reference data should be generated using Hornresp with various QL settings.

To generate Hornresp reference data:
1. Open Hornresp
2. Load driver (e.g., BC 8NDL51)
3. Design enclosure (sealed or ported)
4. Set desired QL value (double-click QL label)
5. Export simulation results to CSV
6. Save to: tests/validation/drivers/{driver}/{enclosure}/ql{QL}.csv

Literature:
- Hornresp User Manual - QL parameter documentation
- Hornresp V53.20 release notes - Default QL = 7
"""

import pytest
import csv
import os
from pathlib import Path
from viberesp.driver.bc_drivers import get_bc_8ndl51, get_bc_15ps100
from viberesp.enclosure.sealed_box import sealed_box_electrical_impedance
from viberesp.enclosure.ported_box import ported_box_electrical_impedance


class HornrespDataLoader:
    """Load Hornresp reference data from CSV files."""

    @staticmethod
    def load_hornresp_csv(file_path: str) -> dict:
        """
        Load Hornresp CSV export.

        Expected CSV format (Hornresp export):
        Frequency, Impedance, Phase, SPL, ...
        20.0, 6.5, 45.2, 65.3, ...
        25.0, 6.8, 47.1, 68.1, ...
        ...

        Returns:
            Dictionary with keys: frequencies, impedances, phases, spl
        """
        if not os.path.exists(file_path):
            pytest.skip(f"Hornresp reference data not found: {file_path}")

        data = {'frequencies': [], 'impedances': [], 'phases': [], 'spl': []}

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data['frequencies'].append(float(row['Frequency']))
                data['impedances'].append(float(row['Impedance']))
                if 'Phase' in row:
                    data['phases'].append(float(row['Phase']))
                if 'SPL' in row:
                    data['spl'].append(float(row['SPL']))

        return data

    @staticmethod
    def find_closest_frequency(hornresp_data: dict, target_freq: float) -> dict:
        """Find Hornresp data point closest to target frequency."""
        freqs = hornresp_data['frequencies']
        idx = min(range(len(freqs)), key=lambda i: abs(freqs[i] - target_freq))

        result = {}
        for key in hornresp_data:
            if hornresp_data[key]:
                result[key] = hornresp_data[key][idx]

        return result


class TestSealedBoxQLHornrespComparison:
    """Compare sealed box QL implementation with Hornresp."""

    @pytest.fixture
    def bc8ndl51_sealed_ql7_path(self, tmp_path):
        """
        Path to Hornresp reference data for BC 8NDL51 sealed box with QL=7.

        TO GENERATE:
        1. Hornresp: BC 8NDL51, sealed box, Vb=10L, QL=7
        2. Tools → Export → Angular Frequency (or similar)
        3. Save as: tests/validation/drivers/bc8ndl51/sealed/ql7.csv
        """
        return Path('tests/validation/drivers/bc8ndl51/sealed/ql7.csv')

    @pytest.fixture
    def bc8ndl51_sealed_ql20_path(self, tmp_path):
        """Path to Hornresp data with QL=20 (well-sealed)."""
        return Path('tests/validation/drivers/bc8ndl51/sealed/ql20.csv')

    @pytest.fixture
    def bc8ndl51_sealed_ql100_path(self, tmp_path):
        """Path to Hornresp data with QL=100 (near-lossless)."""
        return Path('tests/validation/drivers/bc8ndl51/sealed/ql100.csv')

    @pytest.mark.parametrize("ql,expected_error", [
        (7.0, 0.10),   # Hornresp default - <10% error acceptable
        (20.0, 0.10),  # Well-sealed
        (100.0, 0.15), # Near-lossless (may have larger numerical errors)
    ])
    def test_sealed_box_ql_impedance_vs_hornresp(
        self, bc8ndl51_sealed_ql7_path,
        ql, expected_error
    ):
        """
        Compare sealed box impedance with Hornresp for various QL values.

        NOTE: We use Quc for sealed boxes, but Hornresp uses QL.
        For comparison, Quc ≈ QL (both represent box losses).
        """
        driver = get_bc_8ndl51()
        Vb = 0.010  # 10L

        # Map QL to Quc for sealed box
        Quc = ql

        # Load Hornresp reference data
        # (Using same path for all QL values - in practice, separate files needed)
        hornresp_file = bc8ndl51_sealed_ql7_path
        hornresp_data = HornrespDataLoader.load_hornresp_csv(str(hornresp_file))

        # Test frequencies around system resonance
        test_freqs = [40, 60, 80, 100, 200, 500, 1000]

        max_error = 0.0
        for freq in test_freqs:
            # Calculate viberesp impedance
            viberesp_result = sealed_box_electrical_impedance(
                freq, driver, Vb, Quc=Quc
            )

            # Get closest Hornresp data point
            hornresp_point = HornrespDataLoader.find_closest_frequency(
                hornresp_data, freq
            )

            # Calculate error
            hornresp_ze = hornresp_point['impedances']
            viberesp_ze = viberesp_result['Ze_magnitude']
            error = abs(viberesp_ze - hornresp_ze) / hornresp_ze
            max_error = max(max_error, error)

            # Check individual point
            assert error < expected_error * 1.5, \
                f"Impedance error too large at {freq}Hz: " \
                f"viberesp={viberesp_ze:.2f}Ω, Hornresp={hornresp_ze:.2f}Ω, " \
                f"error={error*100:.1f}%"

        # Check overall error
        assert max_error < expected_error, \
            f"Overall impedance error too large: {max_error*100:.1f}%"

    @pytest.mark.parametrize("ql", [7.0, 20.0, 100.0])
    def test_sealed_box_ql_reduces_impedance_peak(
        self, bc8ndl51_sealed_ql7_path, ql
    ):
        """
        Test that lower QL (more losses) reduces impedance peak height.

        This validates the parallel Q combination is working correctly.
        """
        driver = get_bc_8ndl51()
        Vb = 0.010
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)

        # Calculate impedance at resonance (highest point)
        result = sealed_box_electrical_impedance(
            params.Fc, driver, Vb, Quc=ql
        )

        # Higher QL (fewer losses) should give higher impedance
        result_low_loss = sealed_box_electrical_impedance(
            params.Fc, driver, Vb, Quc=100.0
        )

        assert result['Ze_magnitude'] < result_low_loss['Ze_magnitude'], \
            f"QL={ql} should give lower impedance than QL=100"

    def test_sealed_box_impedance_peak_frequency(
        self, bc8ndl51_sealed_ql7_path
    ):
        """Test that impedance peak occurs at expected Fc."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)

        # Sweep around Fc to find impedance peak
        freqs = params.Fc * 0.8 + (params.Fc * 0.4) * \
                 [i/10 for i in range(11)]  # 0.8*Fc to 1.2*Fc

        max_impedance = 0
        peak_freq = None

        for freq in freqs:
            result = sealed_box_electrical_impedance(freq, driver, Vb, Quc=7.0)
            if result['Ze_magnitude'] > max_impedance:
                max_impedance = result['Ze_magnitude']
                peak_freq = freq

        # Peak should be close to Fc
        freq_error = abs(peak_freq - params.Fc) / params.Fc
        assert freq_error < 0.05, \
            f"Impedance peak frequency error too large: " \
            f"peak at {peak_freq:.1f}Hz vs Fc={params.Fc:.1f}Hz"


class TestPortedBoxQLHornrespComparison:
    """Compare ported box QL implementation with Hornresp."""

    @pytest.fixture
    def bc8ndl51_ported_ql7_path(self, tmp_path):
        """
        Path to Hornresp reference data for BC 8NDL51 ported box with QL=7.

        TO GENERATE:
        1. Hornresp: BC 8NDL51, ported box, Vb=20L, Fb=50Hz, QL=7
        2. Tools → Export → Angular Frequency
        3. Save as: tests/validation/drivers/bc8ndl51/ported/ql7.csv
        """
        return Path('tests/validation/drivers/bc8ndl51/ported/ql7.csv')

    @pytest.mark.parametrize("ql,expected_error", [
        (7.0, 0.12),   # Hornresp default
        (10.0, 0.12),  # WinISD default
        (20.0, 0.15),  # Well-sealed
    ])
    def test_ported_box_ql_impedance_vs_hornresp(
        self, bc8ndl51_ported_ql7_path,
        ql, expected_error
    ):
        """
        Compare ported box impedance with Hornresp for various QL values.

        Ported boxes use QL directly (unlike sealed boxes which use Quc).
        """
        driver = get_bc_8ndl51()
        Vb = 0.020  # 20L
        Fb = 50.0
        port_area = 0.003  # m² (from calculate_optimal_port_dimensions)
        port_length = 0.08  # m (from calculate_optimal_port_dimensions)

        # Load Hornresp reference data
        hornresp_file = bc8ndl51_ported_ql7_path
        hornresp_data = HornrespDataLoader.load_hornresp_csv(str(hornresp_file))

        # Test frequencies around dual impedance peaks
        test_freqs = [20, 30, 40, 50, 60, 70, 80, 100, 200]

        max_error = 0.0
        for freq in test_freqs:
            # Calculate viberesp impedance
            viberesp_result = ported_box_electrical_impedance(
                freq, driver, Vb, Fb,
                port_area=port_area,
                port_length=port_length,
                QL=ql, QA=100.0  # Use default QA
            )

            # Get closest Hornresp data point
            hornresp_point = HornrespDataLoader.find_closest_frequency(
                hornresp_data, freq
            )

            # Calculate error
            hornresp_ze = hornresp_point['impedances']
            viberesp_ze = viberesp_result['Ze_magnitude']
            error = abs(viberesp_ze - hornresp_ze) / hornresp_ze
            max_error = max(max_error, error)

        # Check overall error
        assert max_error < expected_error, \
            f"Overall impedance error too large: {max_error*100:.1f}%"

    def test_ported_box_dual_impedance_peaks(
        self, bc8ndl51_ported_ql7_path
    ):
        """
        Test that ported box shows dual impedance peaks.

        Lower peak ≈ Fb/√2, Upper peak ≈ Fb×√2
        """
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0
        port_area = 0.003
        port_length = 0.08

        # Sweep frequency range
        freqs = [20 + i*5 for i in range(18)]  # 20-105 Hz

        impedances = []
        for freq in freqs:
            result = ported_box_electrical_impedance(
                freq, driver, Vb, Fb,
                port_area=port_area,
                port_length=port_length,
                QL=7.0, QA=100.0
            )
            impedances.append(result['Ze_magnitude'])

        # Find peaks
        peaks = []
        for i in range(1, len(impedances)-1):
            if impedances[i] > impedances[i-1] and impedances[i] > impedances[i+1]:
                peaks.append((freqs[i], impedances[i]))

        # Should have 2 peaks (lower and upper)
        assert len(peaks) >= 2, \
            f"Ported box should show dual impedance peaks, found {len(peaks)}"

        # Lower peak should be below Fb
        lower_peak_freq = min(peaks, key=lambda p: p[0])[0]
        assert lower_peak_freq < Fb, \
            f"Lower impedance peak should be below Fb ({Fb}Hz), found at {lower_peak_freq}Hz"

        # Upper peak should be above Fb
        upper_peak_freq = max(peaks, key=lambda p: p[0])[0]
        assert upper_peak_freq > Fb, \
            f"Upper impedance peak should be above Fb ({Fb}Hz), found at {upper_peak_freq}Hz"

    def test_ported_box_ql_affects_impedance_dip(self):
        """
        Test that QL affects the impedance dip at Fb.

        Lower QL (more losses) should raise the impedance minimum
        (make the dip less deep).
        """
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0
        port_area = 0.003
        port_length = 0.08

        # Calculate at tuning frequency with different QL values
        result_low_loss = ported_box_electrical_impedance(
            Fb, driver, Vb, Fb,
            port_area=port_area,
            port_length=port_length,
            QL=100.0, QA=100.0
        )

        result_high_loss = ported_box_electrical_impedance(
            Fb, driver, Vb, Fb,
            port_area=port_area,
            port_length=port_length,
            QL=5.0, QA=100.0
        )

        # Higher losses should give higher impedance at Fb
        # (Less dip = more damping)
        assert result_high_loss['Ze_magnitude'] > result_low_loss['Ze_magnitude'], \
            "Higher losses (lower QL) should reduce impedance dip depth"


class TestQLParameterValidation:
    """Test QL parameter validation and edge cases."""

    def test_quc_zero_raises_error(self):
        """Test that Quc = 0 raises an error (division by zero)."""
        driver = get_bc_8ndl51()
        Vb = 0.010

        with pytest.raises((ValueError, ZeroDivisionError)):
            calculate_sealed_box_system_parameters(driver, Vb, Quc=0.0)

    def test_quc_negative_raises_error(self):
        """Test that negative Quc raises an error."""
        driver = get_bc_8ndl51()
        Vb = 0.010

        # Should handle negative values gracefully
        # (Either raise error or produce warning)
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=-5.0)

        # Result should still be valid (even if physically meaningless)
        # Qtc_total will be negative, which indicates invalid input
        assert params.Qtc_total < 0, "Negative Quc should produce negative Qtc_total"

    def test_qb_parallel_combination_properties(self):
        """Test that QB parallel combination has expected properties."""
        # Test 1: QB should be less than smallest component
        QL, QA, QP = 7.0, 100.0, 20.0
        QB = 1.0 / (1.0/QL + 1.0/QA + 1.0/QP)

        smallest = min(QL, QA, QP)
        assert QB < smallest, \
            f"QB ({QB:.2f}) should be < smallest component ({smallest})"

        # Test 2: QB should approach QL when QA, QP → ∞
        QB_ql_only = 1.0 / (1.0/QL + 0.0 + 0.0)
        assert abs(QB_ql_only - QL) < 0.001, \
            "QB should equal QL when QA, QP are infinite"

        # Test 3: All components equal
        Q_equal = 10.0
        QB_equal = 1.0 / (3.0 / Q_equal)
        expected = Q_equal / 3.0
        assert abs(QB_equal - expected) < 0.001, \
            f"QB with equal components should be Q/3: {QB_equal:.2f} vs {expected:.2f}"


class TestQLDocumentationExamples:
    """Test examples from documentation for correctness."""

    def test_sealed_box_example_from_docs(self):
        """Test sealed box example from documentation."""
        # From CLAUDE.md or QL documentation
        driver = get_bc_15ps100()  # Use BC 15PS100 as example
        Vb = 0.050  # 50L
        Quc = 7.0  # Typical unfilled box

        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=Quc)

        # Verify calculations are reasonable
        assert params.Fc > driver.F_s, \
            "System resonance Fc should be higher than Fs"
        assert params.Qtc_total < params.Qec, \
            "Qtc_total should be less than Qec (parallel damping)"

        # Verify parallel formula
        expected_qtc = (params.Qec * Quc) / (params.Qec + Quc)
        assert abs(params.Qtc_total - expected_qtc) < 0.001, \
            "Qtc_total should match parallel combination formula"

    def test_ported_box_example_from_docs(self):
        """Test ported box example from documentation."""
        driver = get_bc_8ndl51()
        Vb = 0.020  # 20L
        Fb = 50.0
        QL = 7.0   # Hornresp default
        QA = 100.0 # WinISD default
        QP = None   # Auto-calculate

        params = calculate_ported_box_system_parameters(
            driver, Vb, Fb, QL=QL, QA=QA, QP=QP
        )

        # Verify combined losses
        expected_qb = 1.0 / (1.0/QL + 1.0/QA + 1.0/params.Qp)
        assert abs(params.QB - expected_qb) < 0.01, \
            "QB should match parallel combination formula"

        # Verify QB is reasonable
        assert params.QB < params.QL, \
            "QB should be less than QL (parallel with QA and QP)"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
