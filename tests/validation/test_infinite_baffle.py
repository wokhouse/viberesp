"""
Integration tests for direct radiator infinite baffle validation.

These tests validate the viberesp simulation against Hornresp reference
data for the BC 8NDL51 driver in infinite baffle configuration.
"""

import pytest
import numpy as np
from pathlib import Path

from viberesp.driver.response import direct_radiator_electrical_impedance
from viberesp.hornresp.results_parser import load_hornresp_sim_file
from viberesp.validation.compare import (
    compare_electrical_impedance,
    compare_spl,
    compare_electrical_impedance_phase,
    generate_validation_report,
)
from viberesp.driver.bc_drivers import get_bc_8ndl51


class TestInfiniteBaffleValidationBC8NDL51:
    """Validation tests for BC 8NDL51 driver in infinite baffle."""

    @pytest.fixture
    def bc_8ndl51_driver(self):
        """Get BC 8NDL51 driver parameters."""
        return get_bc_8ndl51()

    @pytest.fixture
    def bc_8ndl51_hornresp_data(self):
        """Load Hornresp reference data for BC 8NDL51."""
        data_path = (
            Path(__file__).parent
            / "drivers"
            / "bc_8ndl51"
            / "infinite_baffle"
            / "bc_8ndl51_inf_sim.txt"
        )
        return load_hornresp_sim_file(data_path)

    def test_bc_8ndl51_electrical_impedance_magnitude(
        self, bc_8ndl51_driver, bc_8ndl51_hornresp_data
    ):
        """
        Validate electrical impedance magnitude for BC 8NDL51.

        Compares viberesp electrical impedance magnitude against Hornresp
        reference data. Tolerance: <2% for most frequencies.
        """
        # Calculate viberesp response at same frequencies as Hornresp
        ze_viberesp = np.array(
            [
                direct_radiator_electrical_impedance(f, bc_8ndl51_driver)[
                    "Ze_magnitude"
                ]
                for f in bc_8ndl51_hornresp_data.frequency
            ]
        )

        # Compare with Hornresp
        result = compare_electrical_impedance(
            bc_8ndl51_hornresp_data.frequency,
            ze_viberesp,
            bc_8ndl51_hornresp_data,
            tolerance_percent=2.0,
        )

        # Print summary for manual review
        print(result.summary)

        # Assert validation passes
        assert result.passed, f"ELECTRICAL IMPEDANCE MAGNITUDE validation failed: {result.summary}"
        assert result.max_percent_error < 2.0, f"Max error {result.max_percent_error:.2f}% exceeds 2%"

    def test_bc_8ndl51_electrical_impedance_phase(
        self, bc_8ndl51_driver, bc_8ndl51_hornresp_data
    ):
        """
        Validate electrical impedance phase for BC 8NDL51.

        Compares viberesp electrical impedance phase against Hornresp
        reference data. Tolerance: <5° general, <10° near resonance.
        """
        # Calculate viberesp response
        ze_viberesp_complex = np.array(
            [
                complex(
                    direct_radiator_electrical_impedance(f, bc_8ndl51_driver)["Ze_real"],
                    direct_radiator_electrical_impedance(f, bc_8ndl51_driver)["Ze_imag"],
                )
                for f in bc_8ndl51_hornresp_data.frequency
            ]
        )

        # Compare phase
        result = compare_electrical_impedance_phase(
            bc_8ndl51_hornresp_data.frequency,
            ze_viberesp_complex,
            bc_8ndl51_hornresp_data,
            tolerance_degrees=5.0,
        )

        # Print summary for manual review
        print(result.summary)

        # Assert validation passes
        assert result.passed, f"ELECTRICAL IMPEDANCE PHASE validation failed: {result.summary}"
        assert result.max_absolute_error < 5.0, f"Max phase error {result.max_absolute_error:.1f}° exceeds 5°"

    def test_bc_8ndl51_spl(self, bc_8ndl51_driver, bc_8ndl51_hornresp_data):
        """
        Validate SPL for BC 8NDL51.

        Compares viberesp SPL against Hornresp reference data.
        Tolerance: <3 dB (industry standard).
        """
        # Calculate viberesp SPL
        spl_viberesp = np.array(
            [
                direct_radiator_electrical_impedance(f, bc_8ndl51_driver)["SPL"]
                for f in bc_8ndl51_hornresp_data.frequency
            ]
        )

        # Compare with Hornresp
        result = compare_spl(
            bc_8ndl51_hornresp_data.frequency,
            spl_viberesp,
            bc_8ndl51_hornresp_data.spl_db,
            tolerance_db=3.0,
        )

        # Print summary for manual review
        print(result.summary)

        # Assert validation passes (±3 dB tolerance)
        assert result.passed, f"SPL validation failed: {result.summary}"
        assert result.max_absolute_error < 3.0, f"Max SPL error {result.max_absolute_error:.2f} dB exceeds 3 dB"

        # RMS error should be < 2 dB
        assert result.rms_error < 2.0, f"SPL RMS error {result.rms_error:.2f} dB too high"

    def test_bc_8ndl51_comprehensive_validation(
        self, bc_8ndl51_driver, bc_8ndl51_hornresp_data
    ):
        """
        Run comprehensive validation on BC 8NDL51 and generate report.

        This test validates all metrics (Ze magnitude, Ze phase, SPL)
        and generates a comprehensive validation report.
        """
        # Calculate viberesp response at all frequency points
        ze_viberesp_mag = []
        ze_viberesp_phase = []
        spl_viberesp = []

        for f in bc_8ndl51_hornresp_data.frequency:
            result = direct_radiator_electrical_impedance(f, bc_8ndl51_driver)
            ze_viberesp_mag.append(result["Ze_magnitude"])
            ze_viberesp_phase.append(
                complex(result["Ze_real"], result["Ze_imag"])
            )
            spl_viberesp.append(result["SPL"])

        ze_viberesp_mag = np.array(ze_viberesp_mag)
        ze_viberesp_phase = np.array(ze_viberesp_phase)
        spl_viberesp = np.array(spl_viberesp)

        # Compare all metrics
        ze_mag_result = compare_electrical_impedance(
            bc_8ndl51_hornresp_data.frequency,
            ze_viberesp_mag,
            bc_8ndl51_hornresp_data,
            tolerance_percent=2.0,
        )

        ze_phase_result = compare_electrical_impedance_phase(
            bc_8ndl51_hornresp_data.frequency,
            ze_viberesp_phase,
            bc_8ndl51_hornresp_data,
            tolerance_degrees=5.0,
        )

        spl_result = compare_spl(
            bc_8ndl51_hornresp_data.frequency,
            spl_viberesp,
            bc_8ndl51_hornresp_data.spl_db,
            tolerance_db=3.0,
        )

        # Generate report
        report = generate_validation_report(
            "BC_8NDL51",
            "infinite_baffle",
            [ze_mag_result, ze_phase_result, spl_result],
            output_format="text",
        )

        # Print report for manual review
        print("\n" + "=" * 60)
        print(report)
        print("=" * 60)

        # Assert all validations pass
        assert ze_mag_result.passed, f"Ze magnitude validation failed: {ze_mag_result.summary}"
        assert ze_phase_result.passed, f"Ze phase validation failed: {ze_phase_result.summary}"
        assert spl_result.passed, f"SPL validation failed: {spl_result.summary}"

        # Verify error statistics are reasonable
        print("\n=== Validation Statistics ===")
        print(f"Ze magnitude - Max error: {ze_mag_result.max_percent_error:.2f}%, RMS: {ze_mag_result.rms_error:.3f} Ω")
        print(f"Ze phase - Max error: {ze_phase_result.max_absolute_error:.1f}°, RMS: {ze_phase_result.rms_error:.1f}°")
        print(f"SPL - Max error: {spl_result.max_absolute_error:.2f} dB, RMS: {spl_result.rms_error:.2f} dB")
