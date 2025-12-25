"""Tests for radiation impedance calculations."""

import numpy as np
import pytest
from scipy.special import j1, struve

from viberesp.core.constants import RHO, C
from viberesp.physics.radiation import (
    _struve_h1,
    circular_piston_impedance,
    circular_piston_impedance_normalized,
)


class TestStruveH1:
    """Tests for the Struve H₁ function approximation."""

    def test_struve_h1_scalar(self):
        """Test Struve function with scalar input."""
        result = _struve_h1(0.5)
        assert isinstance(result, (float, np.floating))
        # Compare with scipy
        expected = struve(1, 0.5)
        assert abs(result - expected) < 0.001

    def test_struve_h1_array(self):
        """Test Struve function with array input."""
        x = np.array([0.5, 1.0, 2.0])
        result = _struve_h1(x)
        assert isinstance(result, np.ndarray)
        assert len(result) == len(x)
        # Compare with scipy
        expected = struve(1, x)
        np.testing.assert_allclose(result, expected, rtol=0.01)

    def test_struve_h1_zero(self):
        """Test Struve function at x=0 (should handle division)."""
        result = _struve_h1(0.0)
        # Should not raise error and should return small value
        assert isinstance(result, (float, np.floating))
        assert result >= 0

    def test_struve_h1_accuracy(self):
        """Verify Struve approximation accuracy vs scipy."""
        x_values = np.linspace(0.1, 10, 50)
        approx = _struve_h1(x_values)
        scipy_vals = struve(1, x_values)
        # Error should be < 1%
        relative_error = np.abs((approx - scipy_vals) / scipy_vals)
        assert np.all(relative_error < 0.01)


class TestNormalizedImpedance:
    """Tests for normalized radiation impedance."""

    def test_single_frequency(self):
        """Test normalized impedance with scalar ka."""
        ka = 0.18
        Z_norm = circular_piston_impedance_normalized(ka)
        assert isinstance(Z_norm, complex)
        assert isinstance(Z_norm.real, (float, np.floating))
        assert isinstance(Z_norm.imag, (float, np.floating))

    def test_frequency_array(self):
        """Test normalized impedance with array input."""
        ka = np.array([0.1, 0.5, 1.0, 2.0, 10.0])
        Z_norm = circular_piston_impedance_normalized(ka)
        assert isinstance(Z_norm, np.ndarray)
        assert len(Z_norm) == len(ka)
        assert Z_norm.dtype == np.complex128

    def test_low_frequency_mass_controlled(self):
        """Test that X dominates R at low frequency (ka << 1)."""
        ka_small = 0.1
        Z_norm = circular_piston_impedance_normalized(ka_small)
        # In mass-controlled region, reactance should dominate
        assert Z_norm.imag > Z_norm.real
        # X/R ratio should be large
        ratio = Z_norm.imag / Z_norm.real
        assert ratio > 5

    def test_high_frequency_limit(self):
        """Test that R → 1 and X → 0 as ka → ∞."""
        ka_large = 100.0
        Z_norm = circular_piston_impedance_normalized(ka_large)
        # Resistance should approach 1
        assert abs(Z_norm.real - 1.0) < 0.01
        # Reactance should approach 0
        assert abs(Z_norm.imag) < 0.01

    def test_impedance_formula_consistency(self):
        """Verify impedance matches Kolbrek formula exactly."""
        ka = 0.181569
        Z_norm = circular_piston_impedance_normalized(ka)

        # Calculate using Kolbrek formula directly
        R_expected = 1 - j1(2 * ka) / ka
        X_expected = struve(1, 2 * ka) / ka

        assert abs(Z_norm.real - R_expected) < 1e-10
        assert abs(Z_norm.imag - X_expected) < 1e-10

    def test_positive_resistance(self):
        """Test that resistance is always positive."""
        ka = np.logspace(-2, 2, 50)  # 0.01 to 100
        Z_norm = circular_piston_impedance_normalized(ka)
        assert np.all(Z_norm.real > 0)

    def test_positive_reactance(self):
        """Test that reactance is positive for circular piston."""
        ka = np.logspace(-2, 2, 50)
        Z_norm = circular_piston_impedance_normalized(ka)
        assert np.all(Z_norm.imag > 0)


class TestFullImpedance:
    """Tests for full radiation impedance calculation."""

    def test_single_frequency_scalar(self):
        """Test impedance with scalar frequency."""
        area = 0.1257  # m²
        freq = 50.0  # Hz
        Z_rad = circular_piston_impedance(area, freq)
        assert isinstance(Z_rad, complex)
        # Should return scalar, not array
        assert not isinstance(Z_rad, np.ndarray)

    def test_frequency_array(self):
        """Test impedance with frequency array."""
        area = 0.1257
        freqs = np.linspace(20, 200, 10)
        Z_rad = circular_piston_impedance(area, freqs)
        assert isinstance(Z_rad, np.ndarray)
        assert len(Z_rad) == len(freqs)

    def test_impedance_magnitude(self):
        """Test that impedance has reasonable magnitude."""
        area = 0.1257
        freq = 50.0
        Z_rad = circular_piston_impedance(area, freq)

        # Characteristic impedance
        Z_char = RHO * C / area

        # Magnitude should be on order of Z_char
        assert abs(Z_rad) < 10 * Z_char
        assert abs(Z_rad) > 0.01 * Z_char

    def test_area_scaling(self):
        """Test that impedance scales inversely with area."""
        freq = 100.0
        area_small = 0.01
        area_large = 0.1

        Z_small = circular_piston_impedance(area_small, freq)
        Z_large = circular_piston_impedance(area_large, freq)

        # Smaller area should give larger impedance
        assert abs(Z_small) > abs(Z_large)

        # Check that scaling is in the right direction
        # Exact ratio depends on ka changes, but should be > 1
        ratio = abs(Z_small) / abs(Z_large)
        assert ratio > 1.5  # At least 1.5x difference for 10x area

    def test_frequency_dependence(self):
        """Test that impedance increases with frequency."""
        area = 0.1257
        freq_low = 20.0
        freq_high = 200.0

        Z_low = circular_piston_impedance(area, freq_low)
        Z_high = circular_piston_impedance(area, freq_high)

        # Magnitude should increase with frequency
        # (both resistance and reactance increase)
        assert abs(Z_high) > abs(Z_low)

    def test_custom_acoustic_parameters(self):
        """Test with custom rho and c values."""
        area = 0.1257
        freq = 50.0
        rho_custom = 1.204
        c_custom = 343.0

        Z_default = circular_piston_impedance(area, freq)
        Z_custom = circular_piston_impedance(area, freq, rho_custom, c_custom)

        # Should be different but same order of magnitude
        assert abs(Z_default - Z_custom) > 0
        assert abs(Z_custom / Z_default - 1.0) < 0.1


class TestTC_P1_RAD_01:
    """Validation tests for TC-P1-RAD-01 test case."""

    def test_tc_p1_rad_01_theoretical(self):
        """Validate against theoretical Kolbrek values."""
        from tests.physics.fixtures.tc_p1_rad_01_data import TC_P1_RAD_01

        params = TC_P1_RAD_01["parameters"]
        theoretical = TC_P1_RAD_01["theoretical"]

        # Calculate ka
        ka = 2 * np.pi * params["frequency_hz"] * params["radius_m"] / params["c"]

        # Calculate normalized impedance
        Z_norm = circular_piston_impedance_normalized(ka)

        # Compare with theoretical values
        R_error = abs(Z_norm.real - theoretical["R_norm"]) / theoretical["R_norm"] * 100
        X_error = abs(Z_norm.imag - theoretical["X_norm"]) / theoretical["X_norm"] * 100

        # Should match within 1% (numerical precision)
        assert (
            R_error < theoretical["tolerance_percent"]
        ), f"R error {R_error:.3f}% exceeds tolerance"
        assert (
            X_error < theoretical["tolerance_percent"]
        ), f"X error {X_error:.3f}% exceeds tolerance"

    def test_tc_p1_rad_01_mass_controlled(self):
        """Verify mass-controlled behavior at ka << 1."""
        from tests.physics.fixtures.tc_p1_rad_01_data import TC_P1_RAD_01

        params = TC_P1_RAD_01["parameters"]

        ka = 2 * np.pi * params["frequency_hz"] * params["radius_m"] / params["c"]
        Z_norm = circular_piston_impedance_normalized(ka)

        # X should dominate R
        assert Z_norm.imag > Z_norm.real

        # Check X/R ratio is approximately correct (~9.3 for ka=0.18)
        ratio = Z_norm.imag / Z_norm.real
        expected_ratio = TC_P1_RAD_01["validation"]["expected_behavior"]["X_to_R_ratio"]
        # Extract approximate value from string "X/R ≈ 9.3"
        expected_val = float(expected_ratio.split("≈")[1].strip().replace(" at ka = 0.18", ""))
        assert abs(ratio - expected_val) / expected_val < 0.05

    def test_tc_p1_rad_01_full_impedance(self):
        """Test full impedance calculation matches theory."""
        from tests.physics.fixtures.tc_p1_rad_01_data import TC_P1_RAD_01

        params = TC_P1_RAD_01["parameters"]

        Z_rad = circular_piston_impedance(
            area=params["area_m2"],
            frequency=params["frequency_hz"],
            rho=params["rho"],
            c=params["c"],
        )

        # Check magnitude is reasonable
        # From TC-P1-RAD-01: Z_rad ≈ 53.4 + j498.0
        assert 50 < abs(Z_rad) < 550  # Should be ~501
        assert Z_rad.real > 0
        assert Z_rad.imag > 0


class TestEdgeCases:
    """Tests for edge cases and special conditions."""

    def test_very_low_frequency(self):
        """Test behavior at very low frequency (ka → 0)."""
        area = 0.1257
        freq = 1.0  # Very low frequency
        Z_rad = circular_piston_impedance(area, freq)
        # Should still work and give finite impedance
        assert np.isfinite(abs(Z_rad))

    def test_very_high_frequency(self):
        """Test behavior at very high frequency (ka >> 1)."""
        area = 0.1257
        freq = 10000.0  # Very high frequency
        Z_rad = circular_piston_impedance(area, freq)
        # Should approach purely resistive
        Z_norm = circular_piston_impedance_normalized(2 * np.pi * freq * np.sqrt(area / np.pi) / C)
        assert Z_norm.real > 0.9  # R should be close to 1
        assert abs(Z_norm.imag) < 0.5  # X should be small

    def test_very_small_area(self):
        """Test with very small piston area."""
        area = 1e-6  # 1 mm²
        freq = 1000.0
        Z_rad = circular_piston_impedance(area, freq)
        # Should give very large impedance
        assert abs(Z_rad) > 1e6

    def test_very_large_area(self):
        """Test with very large piston area."""
        area = 10.0  # 10 m²
        freq = 100.0
        Z_rad = circular_piston_impedance(area, freq)
        # Should give small impedance
        assert abs(Z_rad) < 1000

    def test_array_scalar_consistency(self):
        """Test that array and scalar inputs give consistent results."""
        area = 0.1257
        freq = 50.0

        Z_scalar = circular_piston_impedance(area, freq)
        Z_array = circular_piston_impedance(area, np.array([freq]))

        np.testing.assert_allclose(Z_scalar, Z_array[0], rtol=1e-10)
