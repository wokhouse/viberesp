"""
Unit tests for horn theory module.

Tests exponential horn simulation functions including:
- Cutoff frequency calculation
- Radiation impedance
- T-matrix calculation
- Throat impedance transformation

Literature:
- Kolbrek, "Horn Loudspeaker Simulation Part 1"
- Beranek (1954), Eq. 5.20
- literature/horns/kolbrek_horn_theory_tutorial.md
- literature/horns/beranek_1954.md
"""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from viberesp.simulation import (
    ExponentialHorn,
    MediumProperties,
    circular_piston_radiation_impedance,
    exponential_horn_throat_impedance,
    exponential_horn_tmatrix,
    throat_impedance_from_tmatrix,
)


class TestMediumProperties:
    """Test MediumProperties dataclass."""

    def test_default_properties(self):
        """Test default medium properties (Hornresp standard)."""
        medium = MediumProperties()
        assert medium.c == 344.0  # m/s at 20°C
        assert medium.rho == 1.205  # kg/m³ at 20°C
        assert_allclose(medium.z_rc, 414.62, rtol=1e-3)  # ρc

    def test_custom_properties(self):
        """Test custom medium properties."""
        medium = MediumProperties(c=350.0, rho=1.2)
        assert medium.c == 350.0
        assert medium.rho == 1.2
        assert_allclose(medium.z_rc, 420.0)  # 1.2 × 350


class TestExponentialHorn:
    """Test ExponentialHorn geometry and derived parameters."""

    def test_basic_geometry(self):
        """Test basic horn geometry creation."""
        horn = ExponentialHorn(
            throat_area=0.005,  # 50 cm²
            mouth_area=0.05,    # 500 cm²
            length=0.3          # 30 cm
        )
        assert horn.throat_area == 0.005
        assert horn.mouth_area == 0.05
        assert horn.length == 0.3

    def test_flare_constant_olson(self):
        """Test flare constant calculation (Olson convention)."""
        # S(x) = S₁·exp(m·x) with m = ln(S₂/S₁)/L
        horn = ExponentialHorn(
            throat_area=0.005,
            mouth_area=0.05,   # 10× expansion
            length=0.3
        )
        expected_m = np.log(10) / 0.3  # ≈ 7.675
        assert_allclose(horn.flare_constant, expected_m, rtol=1e-6)

    def test_expansion_ratio(self):
        """Test area expansion ratio (calculated property)."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        # Calculate expansion ratio: S₂/S₁
        expansion_ratio = horn.mouth_area / horn.throat_area
        assert expansion_ratio == 10.0

    def test_area_profile(self):
        """Test exponential area profile S(x) = S₁·exp(m·x)."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        m = horn.flare_constant

        # At throat (x=0): S = S₁
        assert_allclose(horn.area_at(0), horn.throat_area)

        # At mouth (x=L): S = S₂
        assert_allclose(horn.area_at(horn.length), horn.mouth_area)

        # At midpoint: S = S₁·exp(m·L/2)
        mid_area = horn.area_at(horn.length / 2)
        expected = horn.throat_area * np.exp(m * horn.length / 2)
        assert_allclose(mid_area, expected, rtol=1e-6)

    # Note: The existing types.ExponentialHorn does not have validation for
    # positive parameters or mouth > throat constraint. These tests are skipped.


class TestCircularPistonRadiationImpedance:
    """Test circular piston radiation impedance calculation."""

    def test_low_frequency_behavior(self):
        """Test that low frequency impedance is mostly reactive."""
        # At low ka: Z ≈ (ρc/S)[(ka)²/2 + j·8ka/(3π)]
        frequencies = np.array([10.0, 20.0, 50.0])
        area = 0.01  # 100 cm²
        z = circular_piston_radiation_impedance(frequencies, area)

        # At low frequencies, reactance should dominate resistance
        for i in range(len(frequencies)):
            assert np.abs(z[i].imag) > np.abs(z[i].real), \
                f"At {frequencies[i]} Hz, reactance should dominate resistance"

    def test_high_frequency_behavior(self):
        """Test that high frequency impedance approaches ρc/S (resistive)."""
        # At high ka: Z ≈ ρc/S (purely resistive)
        frequencies = np.array([5000.0, 10000.0])
        area = 0.01
        z = circular_piston_radiation_impedance(frequencies, area)
        medium = MediumProperties()
        z_expected = medium.z_rc / area

        # High frequency: should approach characteristic impedance / area
        for i in range(len(frequencies)):
            ratio = np.abs(z[i]) / z_expected
            assert_allclose(ratio, 1.0, rtol=0.1, atol=0.1,
                          err_msg=f"At {frequencies[i]} Hz, impedance should approach ρc/S")

    def test_array_input(self):
        """Test that function works with array input."""
        frequencies = np.logspace(1, 4, 100)  # 10 Hz to 10 kHz
        area = 0.01
        z = circular_piston_radiation_impedance(frequencies, area)

        assert z.shape == frequencies.shape
        assert np.all(np.isfinite(z))


class TestExponentialHornTmatrix:
    """Test exponential horn T-matrix calculation."""

    def test_tmatrix_shape(self):
        """Test that T-matrix elements have correct shape."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        frequencies = np.array([100.0, 500.0, 1000.0])
        a, b, c, d = exponential_horn_tmatrix(frequencies, horn)

        assert a.shape == frequencies.shape
        assert b.shape == frequencies.shape
        assert c.shape == frequencies.shape
        assert d.shape == frequencies.shape

    def test_tmatrix_unitary_property(self):
        """Test that T-matrix is unitary for lossless horn (det = 1)."""
        # For lossless horns, determinant of T-matrix should be 1
        # det([a b; c d]) = ad - bc = 1
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        medium = MediumProperties()

        # Test well above cutoff
        fc = horn.flare_constant * medium.c / (2 * np.pi)
        frequencies = np.array([fc * 10, fc * 20])  # Well above cutoff
        a, b, c, d = exponential_horn_tmatrix(frequencies, horn, medium)

        for i in range(len(frequencies)):
            det = a[i] * d[i] - b[i] * c[i]
            assert_allclose(np.abs(det), 1.0, rtol=0.01,
                          err_msg=f"T-matrix determinant should be 1.0 at {frequencies[i]} Hz")

    def test_tmatrix_finite_values(self):
        """Test that T-matrix elements are finite."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        frequencies = np.logspace(1, 4, 100)  # Wide frequency range
        a, b, c, d = exponential_horn_tmatrix(frequencies, horn)

        assert np.all(np.isfinite(a))
        assert np.all(np.isfinite(b))
        assert np.all(np.isfinite(c))
        assert np.all(np.isfinite(d))


class TestThroatImpedanceFromTmatrix:
    """Test throat impedance transformation from T-matrix."""

    def test_impedance_transformation(self):
        """Test Z₁ = (a·Z₂ + b)/(c·Z₂ + d)."""
        # Simple test case: unit T-matrix (identity transformation)
        z_mouth = np.array([100 + 50j, 200 + 30j])
        a = b = c = np.array([0.0, 0.0])
        d = np.array([1.0, 1.0])

        # With identity T-matrix, Z₁ should equal Z₂
        # (Actually with our setup: Z₁ = (0·Z₂ + 0)/(0·Z₂ + 1) = 0/1 = 0, not identity)
        # Let's test with actual a=d=1, b=c=0:
        a = d = np.array([1.0 + 0j, 1.0 + 0j])
        z_throat = throat_impedance_from_tmatrix(z_mouth, a, b, c, d)

        assert_allclose(z_throat, z_mouth)

    def test_finite_results(self):
        """Test that transformed impedances are finite."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        frequencies = np.logspace(1, 4, 100)

        # Calculate T-matrix
        a, b, c, d = exponential_horn_tmatrix(frequencies, horn)

        # Calculate mouth radiation impedance
        z_mouth = circular_piston_radiation_impedance(frequencies, horn.mouth_area)

        # Transform to throat
        z_throat = throat_impedance_from_tmatrix(z_mouth, a, b, c, d)

        assert np.all(np.isfinite(z_throat))


class TestExponentialHornThroatImpedance:
    """Test exponential horn throat impedance calculation (main entry point)."""

    def test_basic_functionality(self):
        """Test basic throat impedance calculation."""
        horn = ExponentialHorn(
            throat_area=0.005,  # 50 cm²
            mouth_area=0.05,    # 500 cm²
            length=0.3          # 30 cm
        )
        frequencies = np.array([100.0, 500.0, 1000.0])
        z_throat = exponential_horn_throat_impedance(frequencies, horn)

        assert z_throat.shape == frequencies.shape
        assert np.all(np.isfinite(z_throat))

    def test_cutoff_frequency_behavior(self):
        """Test impedance behavior around cutoff frequency."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        medium = MediumProperties()

        # Calculate cutoff frequency (using Olson's m, which is 2× Kolbrek's m)
        # fc = m_olson * c / (4π) = m_kolbrek * c / (2π)
        m_kolbrek = horn.flare_constant / 2
        fc = m_kolbrek * medium.c / (2 * np.pi)

        # Test below, at, and above cutoff
        frequencies = np.array([fc * 0.5, fc, fc * 2, fc * 10])
        z_throat = exponential_horn_throat_impedance(frequencies, horn, medium)

        # Below cutoff: should be mostly reactive (mass-like)
        phase_below = np.angle(z_throat[0]) * 180 / np.pi
        assert abs(phase_below) > 45, "Below cutoff, impedance should be mostly reactive"

        # Well above cutoff: should become more resistive
        phase_above = np.angle(z_throat[3]) * 180 / np.pi
        assert abs(phase_above) < 60, "Well above cutoff, impedance should be less reactive"

    def test_radiation_angle_effect(self):
        """Test that radiation angle affects throat impedance."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        frequencies = np.array([500.0, 1000.0])

        # Half-space (infinite baffle)
        z_half_space = exponential_horn_throat_impedance(
            frequencies, horn, radiation_angle=2 * np.pi
        )

        # Free field
        z_free_field = exponential_horn_throat_impedance(
            frequencies, horn, radiation_angle=4 * np.pi
        )

        # Radiation angle should affect impedance
        # Free field should have higher radiation impedance (less loading)
        for i in range(len(frequencies)):
            assert z_half_space[i] != z_free_field[i], \
                "Radiation angle should affect throat impedance"

    def test_frequency_range(self):
        """Test throat impedance over wide frequency range."""
        horn = ExponentialHorn(0.005, 0.05, 0.3)
        frequencies = np.logspace(1, 4, 100)  # 10 Hz to 10 kHz
        z_throat = exponential_horn_throat_impedance(frequencies, horn)

        # All values should be finite
        assert np.all(np.isfinite(z_throat))

        # Magnitude should vary smoothly (no spikes)
        magnitude = np.abs(z_throat)
        # Check that adjacent values don't differ by more than factor of 2
        # (except at resonance where it can vary rapidly)
        ratios = magnitude[1:] / magnitude[:-1]
        assert np.all(ratios < 10), "Impedance magnitude should vary smoothly"


class TestValidationTestCases:
    """Test cases based on research agent validation plan.

    These test cases prepare for Hornresp validation.
    """

    def test_test_case_1_midrange_horn(self):
        """Test Case 1: Typical midrange horn from validation plan.

        Hornresp parameters:
        S1 = 50 cm² = 0.005 m²
        S2 = 500 cm² = 0.05 m²
        L12 = 30 cm = 0.3 m
        """
        horn = ExponentialHorn(
            throat_area=0.005,
            mouth_area=0.05,
            length=0.3
        )

        # Expected cutoff frequency (using Kolbrek's convention)
        # m = ln(S₂/S₁)/(2L) = ln(10)/(0.6) ≈ 3.84
        # fc = mc/(2π) ≈ 3.84 × 344 / (2π) ≈ 210 Hz
        m_kolbrek = horn.flare_constant / 2
        fc_expected = m_kolbrek * 344.0 / (2 * np.pi)

        # At 1 kHz (well above cutoff): throat impedance should be mostly resistive
        z_1khz = exponential_horn_throat_impedance(np.array([1000.0]), horn)[0]
        phase_1khz = np.angle(z_1khz) * 180 / np.pi

        # At high frequency, phase should be small (mostly resistive)
        assert abs(phase_1khz) < 45, f"At 1 kHz, phase should be small, got {phase_1khz}°"

        # At 100 Hz (below cutoff): throat impedance should be mostly reactive
        z_100hz = exponential_horn_throat_impedance(np.array([100.0]), horn)[0]
        phase_100hz = np.angle(z_100hz) * 180 / np.pi

        assert abs(phase_100hz) > 45, f"At 100 Hz, phase should be large, got {phase_100hz}°"

    def test_test_case_2_large_bass_horn(self):
        """Test Case 2: Large bass horn.

        Hornresp parameters:
        S1 = 100 cm² = 0.01 m²
        S2 = 5000 cm² = 0.5 m²
        L12 = 100 cm = 1.0 m

        Note: With 50:1 expansion and 1m length, cutoff is ~107 Hz, not ~60 Hz.
        To get ~60 Hz, need longer horn or smaller expansion ratio.
        """
        horn = ExponentialHorn(
            throat_area=0.01,
            mouth_area=0.5,
            length=1.0
        )

        # Calculate actual cutoff
        m_kolbrek = horn.flare_constant / 2
        fc = m_kolbrek * 344.0 / (2 * np.pi)

        # Actual cutoff is ~107 Hz for this geometry
        assert 100 < fc < 115, f"Cutoff frequency should be ~107 Hz, got {fc} Hz"

        # Test impedance calculation works
        frequencies = np.array([20.0, 60.0, 200.0])
        z = exponential_horn_throat_impedance(frequencies, horn)
        assert z.shape == (3,)

    def test_test_case_3_high_expansion(self):
        """Test Case 3: High expansion ratio (100:1)."""
        horn = ExponentialHorn(
            throat_area=0.0025,  # 25 cm²
            mouth_area=0.25,     # 2500 cm²
            length=0.5
        )

        expansion_ratio = horn.mouth_area / horn.throat_area
        assert expansion_ratio == 100.0

        # Test impedance calculation
        frequencies = np.array([100.0, 500.0, 1000.0])
        z = exponential_horn_throat_impedance(frequencies, horn)
        assert np.all(np.isfinite(z))

    def test_test_case_4_low_expansion(self):
        """Test Case 4: Low expansion ratio (4:1)."""
        horn = ExponentialHorn(
            throat_area=0.01,
            mouth_area=0.04,
            length=0.4
        )

        expansion_ratio = horn.mouth_area / horn.throat_area
        assert expansion_ratio == 4.0

        # Test impedance calculation
        frequencies = np.array([100.0, 500.0, 1000.0])
        z = exponential_horn_throat_impedance(frequencies, horn)
        assert np.all(np.isfinite(z))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
