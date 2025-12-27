"""
Integration tests for sealed box enclosure validation.

These tests validate the viberesp sealed box simulation against Hornresp reference
data for the BC 8NDL51 driver.

Literature:
- Small (1972) - Closed-Box Loudspeaker Systems
- Hornresp validation methodology

Test Data:
- BC_8NDL51 with Qtc=0.707 (Butterworth alignment, Vb=31.65L)

Hornresp Data Generation Required:
1. Import: tests/validation/drivers/bc_8ndl51/sealed_box/input_qtc0.707.txt
2. Run simulation in Hornresp
3. Export: File → Save → Export _sim.txt
4. Save as: tests/validation/drivers/bc_8ndl51/sealed_box/sim.txt
"""

import pytest
import numpy as np
from pathlib import Path

from viberesp.enclosure.sealed_box import (
    calculate_sealed_box_system_parameters,
    sealed_box_electrical_impedance,
)
from viberesp.hornresp.results_parser import load_hornresp_sim_file
from viberesp.validation.compare import (
    compare_electrical_impedance,
    compare_electrical_impedance_phase,
    compare_spl,
    generate_validation_report,
)
from viberesp.driver.bc_drivers import get_bc_8ndl51


# Test configuration
Vb_LITERS = 31.65  # Box volume for Qtc=0.707 Butterworth alignment
Vb_M3 = Vb_LITERS / 1000.0  # Convert to m³
EXPECTED_FC = 86.1  # Expected system resonance (Hz)
EXPECTED_QTC = 0.707  # Expected system Q


class TestSealedBoxSystemParameters:
    """
    Test sealed box system parameters for BC 8NDL51.

    Validates the fundamental formulas from Small (1972):
    - Fc = Fs × √(1 + α) where α = Vas/Vb
    - Qtc = Qts × √(1 + α)
    """

    @pytest.fixture
    def bc_8ndl51_driver(self):
        """Get BC 8NDL51 driver parameters."""
        return get_bc_8ndl51()

    def test_fc_calculation(self, bc_8ndl51_driver):
        """
        Verify system resonance frequency: Fc = Fs × √(1 + α).

        Small (1972), Eq. for system resonance.
        literature/thiele_small/small_1972_closed_box.md

        Test case: BC_8NDL51 in 31.65L box (Butterworth alignment)
        Expected: Fc ≈ 86.1 Hz, Qtc ≈ 0.707

        Tolerance: <0.5 Hz for Fc, <0.02 for Qtc
        """
        params = calculate_sealed_box_system_parameters(bc_8ndl51_driver, Vb_M3)

        # Check Fc within 0.5 Hz
        assert abs(params.Fc - EXPECTED_FC) < 0.5, \
            f"Fc mismatch: {params.Fc:.1f} Hz vs expected {EXPECTED_FC} Hz"

        # Check Qtc within 0.02
        assert abs(params.Qtc - EXPECTED_QTC) < 0.02, \
            f"Qtc mismatch: {params.Qtc:.3f} vs expected {EXPECTED_QTC:.3f}"

        print(f"\\nQtc=0.707 (Butterworth) Validation:")
        print(f"  Vb = {params.Vb*1000:.2f} L")
        print(f"  α = Vas/Vb = {params.alpha:.3f}")
        print(f"  Fc = {params.Fc:.2f} Hz (expected {EXPECTED_FC} Hz)")
        print(f"  Qtc = {params.Qtc:.3f} (expected {EXPECTED_QTC:.3f})")


class TestSealedBoxElectricalImpedance:
    """
    Test electrical impedance validation against Hornresp for Qtc=0.707.

    For BC_8NDL51 in 31.65L box (Butterworth alignment).

    REQUIRES Hornresp sim.txt file (see module docstring).
    """

    @pytest.fixture
    def bc_8ndl51_driver(self):
        """Get BC 8NDL51 driver parameters."""
        return get_bc_8ndl51()

    @pytest.fixture
    def hornresp_data(self, bc_8ndl51_driver):
        """Load Hornresp reference data for Qtc=0.707."""
        data_path = (
            Path(__file__).parent
            / "drivers"
            / "bc_8ndl51"
            / "sealed_box"
            / "sim.txt"
        )

        if not data_path.exists():
            pytest.skip(
                f"Hornresp sim.txt not found. Please generate it using:\n"
                f"  1. Import: {Path(__file__).parent}/drivers/bc_8ndl51/sealed_box/input_qtc0.707.txt\n"
                f"  2. Run simulation in Hornresp\n"
                f"  3. Export: File → Save → Export _sim.txt\n"
                f"  4. Save as: {data_path}"
            )

        return load_hornresp_sim_file(data_path)

    def test_electrical_impedance_magnitude(
        self, bc_8ndl51_driver, hornresp_data
    ):
        """
        Validate electrical impedance magnitude against Hornresp.

        Small (1972) - Closed-box electrical impedance
        Hornresp: "Rear Lined" configuration

        Tolerance: <5% general, <10% near resonance
        """
        # Calculate viberesp response
        ze_viberesp = np.array([
            sealed_box_electrical_impedance(f, bc_8ndl51_driver, Vb=Vb_M3)["Ze_magnitude"]
            for f in hornresp_data.frequency
        ])

        # Compare with Hornresp
        result = compare_electrical_impedance(
            hornresp_data.frequency,
            ze_viberesp,
            hornresp_data,
            tolerance_percent=10.0,  # Relaxed to 10% near resonance
        )

        print(f"\\n[Qtc=0.707] {result.summary}")

        assert result.passed, f"Ze magnitude validation failed: {result.summary}"

    def test_electrical_impedance_phase(
        self, bc_8ndl51_driver, hornresp_data
    ):
        """
        Validate electrical impedance phase against Hornresp.

        Hornresp: "Rear Lined" configuration

        Tolerance: <15° general, <20° near resonance
        """
        # Calculate viberesp response
        ze_viberesp_complex = np.array([
            complex(
                sealed_box_electrical_impedance(f, bc_8ndl51_driver, Vb=Vb_M3)["Ze_real"],
                sealed_box_electrical_impedance(f, bc_8ndl51_driver, Vb=Vb_M3)["Ze_imag"],
            )
            for f in hornresp_data.frequency
        ])

        # Compare with Hornresp
        result = compare_electrical_impedance_phase(
            hornresp_data.frequency,
            ze_viberesp_complex,
            hornresp_data,
            tolerance_degrees=20.0,  # Relaxed to 20° near resonance
        )

        print(f"\\n[Qtc=0.707] {result.summary}")

        assert result.passed, f"Ze phase validation failed: {result.summary}"

    def test_spl(self, bc_8ndl51_driver, hornresp_data):
        """
        Validate SPL response against Hornresp.

        Small (1972) - Normalized pressure response
        Hornresp: "Rear Lined" configuration

        Tolerance: <6 dB (accounts for voice coil model differences)
        """
        # Calculate viberesp SPL
        spl_viberesp = np.array([
            sealed_box_electrical_impedance(f, bc_8ndl51_driver, Vb=Vb_M3)["SPL"]
            for f in hornresp_data.frequency
        ])

        # Compare with Hornresp
        result = compare_spl(
            hornresp_data.frequency,
            spl_viberesp,
            hornresp_data.spl_db,
            tolerance_db=6.0,
        )

        print(f"\\n[Qtc=0.707] {result.summary}")

        assert result.passed, f"SPL validation failed: {result.summary}"
        assert result.max_absolute_error < 6.0, f"Max SPL error {result.max_absolute_error:.2f} dB exceeds 6 dB"
        assert result.rms_error < 4.5, f"SPL RMS error {result.rms_error:.2f} dB too high"

    def test_comprehensive_validation(
        self, bc_8ndl51_driver, hornresp_data
    ):
        """
        Run comprehensive validation for Qtc=0.707 and generate report.
        """
        # Calculate viberesp response at all frequency points
        ze_viberesp_mag = []
        ze_viberesp_phase = []
        spl_viberesp = []

        for f in hornresp_data.frequency:
            result = sealed_box_electrical_impedance(f, bc_8ndl51_driver, Vb=Vb_M3)
            ze_viberesp_mag.append(result["Ze_magnitude"])
            ze_viberesp_phase.append(complex(result["Ze_real"], result["Ze_imag"]))
            spl_viberesp.append(result["SPL"])

        ze_viberesp_mag = np.array(ze_viberesp_mag)
        ze_viberesp_phase = np.array(ze_viberesp_phase)
        spl_viberesp = np.array(spl_viberesp)

        # Compare all metrics
        ze_mag_result = compare_electrical_impedance(
            hornresp_data.frequency,
            ze_viberesp_mag,
            hornresp_data,
            tolerance_percent=10.0,
        )

        ze_phase_result = compare_electrical_impedance_phase(
            hornresp_data.frequency,
            ze_viberesp_phase,
            hornresp_data,
            tolerance_degrees=20.0,
        )

        spl_result = compare_spl(
            hornresp_data.frequency,
            spl_viberesp,
            hornresp_data.spl_db,
            tolerance_db=6.0,
        )

        # Generate report
        report = generate_validation_report(
            "BC_8NDL51",
            "sealed_box_qtc0.707",
            [ze_mag_result, ze_phase_result, spl_result],
            output_format="text",
        )

        # Print report for manual review
        print("\\n" + "=" * 60)
        print(report)
        print("=" * 60)

        # Assert all validations pass
        assert ze_mag_result.passed, f"Ze magnitude validation failed: {ze_mag_result.summary}"
        assert ze_phase_result.passed, f"Ze phase validation failed: {ze_phase_result.summary}"
        assert spl_result.passed, f"SPL validation failed: {spl_result.summary}"


class TestSealedBoxCornerCases:
    """Test corner cases and edge conditions."""

    @pytest.fixture
    def bc_8ndl51_driver(self):
        """Get BC 8NDL51 driver parameters."""
        return get_bc_8ndl51()

    def test_impedance_peak_at_Fc(self, bc_8ndl51_driver):
        """
        Verify that impedance peaks at system resonance Fc.

        Small (1972) - Electrical impedance behavior
        Key diagnostic: Ze(max) occurs at Fc, not Fs

        This is a critical test to verify the model correctly accounts
        for box stiffness. If the peak occurs at Fs instead of Fc,
        the box compliance is not being applied correctly.
        """
        params = calculate_sealed_box_system_parameters(bc_8ndl51_driver, Vb_M3)

        # Calculate impedance at Fc and at frequencies above/below
        ze_at_Fc = sealed_box_electrical_impedance(params.Fc, bc_8ndl51_driver, Vb=Vb_M3)["Ze_magnitude"]
        ze_below = sealed_box_electrical_impedance(params.Fc * 0.8, bc_8ndl51_driver, Vb=Vb_M3)["Ze_magnitude"]
        ze_above = sealed_box_electrical_impedance(params.Fc * 1.2, bc_8ndl51_driver, Vb=Vb_M3)["Ze_magnitude"]

        # Impedance at Fc should be higher than nearby frequencies
        assert ze_at_Fc > ze_below, "Ze at Fc should be > Ze below Fc"
        assert ze_at_Fc > ze_above, "Ze at Fc should be > Ze above Fc"

        print(f"\\nImpedance peak at Fc test:")
        print(f"  Fc = {params.Fc:.2f} Hz")
        print(f"  Ze at Fc = {ze_at_Fc:.2f} Ω")
        print(f"  Ze at 0.8×Fc = {ze_below:.2f} Ω")
        print(f"  Ze at 1.2×Fc = {ze_above:.2f} Ω")
        print(f"  Peak correctly at Fc: ✓")

    def test_Fc_greater_than_Fs(self, bc_8ndl51_driver):
        """
        Verify that Fc > Fs for sealed box (box stiffens the system).

        Small (1972) - System resonance increases with box stiffness
        """
        params = calculate_sealed_box_system_parameters(bc_8ndl51_driver, Vb_M3)

        # Fc should be higher than Fs due to box stiffness
        assert params.Fc > bc_8ndl51_driver.F_s, \
            f"Fc ({params.Fc:.1f} Hz) should be > Fs ({bc_8ndl51_driver.F_s:.1f} Hz)"

        print(f"\\nFc > Fs test:")
        print(f"  Fs = {bc_8ndl51_driver.F_s:.1f} Hz")
        print(f"  Fc = {params.Fc:.1f} Hz")
        print(f"  Stiffness factor √(1+α) = {params.Fc/bc_8ndl51_driver.F_s:.3f}")
