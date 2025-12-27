"""
Integration tests for sealed box enclosure validation.

These tests validate the viberesp sealed box simulation against Hornresp reference
data. Before running tests, you must generate Hornresp reference data using
the instructions below.

Literature:
- Small (1972) - Closed-Box Loudspeaker Systems
- Hornresp validation methodology

Hornresp Data Generation:
--------------------------
For each test case, you need to generate Hornresp reference data:

1. Export driver parameters using viberesp.hornresp.export:
   >>> from viberesp.hornresp.export import export_to_hornresp
   >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
   >>> driver = get_bc_8ndl51()
   >>> export_to_hornresp(driver, "BC_8NDL51", "bc_8ndl51_input.txt")

2. In Hornresp:
   - Import the driver parameters
   - Set: S1 = L45 = 0 (infinite baffle front)
   - Set: Vrc = <Vb_liters>, Lrc = 0 (sealed box rear chamber)
   - Select: "Rear Lined" option
   - Run simulation: File → Save → Export _sim.txt

3. Save the output file to the validation data directory:
   tests/validation/drivers/<driver>/sealed_box/<driver>_sealed_Vb<Vb>L_sim.txt

Example file naming:
- bc_8ndl51_sealed_Vb5L_sim.txt
- bc_8ndl51_sealed_Vb10L_sim.txt
- bc_15ds115_sealed_Vb50L_sim.txt
"""

import pytest
import numpy as np
from pathlib import Path

# NOTE: Uncomment these imports when Hornresp data is available
# from viberesp.enclosure.sealed_box import (
#     calculate_sealed_box_system_parameters,
#     sealed_box_electrical_impedance,
# )
# from viberesp.hornresp.results_parser import load_hornresp_sim_file
# from viberesp.validation.compare import (
#     compare_electrical_impedance,
#     compare_electrical_impedance_phase,
#     compare_spl,
#     generate_validation_report,
# )
# from viberesp.driver.bc_drivers import (
#     get_bc_8ndl51,
#     get_bc_15ds115,
#     get_bc_18pzw100,
# )


class TestSealedBoxSystemParameters:
    """
    Test sealed box system parameters across multiple drivers and box sizes.

    Validates the fundamental formulas from Small (1972):
    - Fc = Fs × √(1 + α) where α = Vas/Vb
    - Qtc = Qts × √(1 + α)

    Expected test cases (from plan):
    BC_8NDL51 (Fs=64 Hz, Qts=0.37, Vas=14L):
        - Vb=5L:  α=2.8, Fc=119 Hz, Qtc=0.71 (Butterworth ✓)
        - Vb=10L: α=1.4, Fc=99 Hz,  Qtc=0.58 (typical)
        - Vb=20L: α=0.7, Fc=83 Hz,  Qtc=0.49 (over-damped)
        - Vb=3L:  α=4.7, Fc=139 Hz, Qtc=0.80 (stress test)

    BC_15DS115 (Fs=33 Hz, Qts=0.35, Vas=94L):
        - Vb=50L:  α=1.88, Fc=55 Hz, Qtc=0.59 (ideal)
        - Vb=100L: α=0.94, Fc=46 Hz, Qtc=0.49 (large box)
        - Vb=30L:  α=3.13, Fc=67 Hz, Qtc=0.72 (compact)

    BC_18PZW100 (Fs=37 Hz, Qts=0.32, Vas=186L):
        - Vb=100L: α=1.86, Fc=58 Hz, Qtc=0.54 (ideal)
        - Vb=200L: α=0.93, Fc=51 Hz, Qtc=0.45 (large box)
        - Vb=50L:  α=3.72, Fc=80 Hz, Qtc=0.76 (compact)
    """

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    @pytest.mark.parametrize("driver_name,Vb_liters,expected_Fc,expected_Qtc", [
        # BC_8NDL51 test cases
        ("bc_8ndl51", 5, 119, 0.71),   # Small box, Butterworth
        ("bc_8ndl51", 10, 99, 0.58),   # Medium box, typical
        ("bc_8ndl51", 20, 83, 0.49),   # Large box, over-damped
        ("bc_8ndl51", 3, 139, 0.80),   # Tiny box, stress test

        # BC_15DS115 test cases
        ("bc_15ds115", 50, 55, 0.59),  # Ideal alignment
        ("bc_15ds115", 100, 46, 0.49), # Large box
        ("bc_15ds115", 30, 67, 0.72),  # Compact design

        # BC_18PZW100 test cases
        ("bc_18pzw100", 100, 58, 0.54), # Ideal alignment
        ("bc_18pzw100", 200, 51, 0.45), # Large box
        ("bc_18pzw100", 50, 80, 0.76),  # Compact design
    ])
    def test_Fc_calculation(self, driver_name, Vb_liters, expected_Fc, expected_Qtc):
        """
        Verify system resonance frequency formula: Fc = Fs × √(1 + α).

        Small (1972), Eq. for system resonance.
        literature/thiele_small/small_1972_closed_box.md

        Tolerance: <0.5 Hz for Fc
        """
        # TODO: Implement when drivers are available
        # driver = get_driver_by_name(driver_name)
        # Vb = Vb_liters / 1000.0  # Convert L to m³

        # params = calculate_sealed_box_system_parameters(driver, Vb)

        # Check Fc within 0.5 Hz
        # assert abs(params.Fc - expected_Fc) < 0.5, \
        #     f"Fc mismatch: {params.Fc:.1f} Hz vs expected {expected_Fc} Hz"

        pytest.skip("Requires Hornresp reference data")

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    @pytest.mark.parametrize("driver_name,Vb_liters,expected_Fc,expected_Qtc", [
        # Same test cases as Fc test
        ("bc_8ndl51", 5, 119, 0.71),
        ("bc_8ndl51", 10, 99, 0.58),
        ("bc_8ndl51", 20, 83, 0.49),
        ("bc_15ds115", 50, 55, 0.59),
        ("bc_15ds115", 100, 46, 0.49),
        ("bc_18pzw100", 100, 58, 0.54),
    ])
    def test_Qtc_calculation(self, driver_name, Vb_liters, expected_Fc, expected_Qtc):
        """
        Verify system Q formula: Qtc = Qts × √(1 + α).

        Small (1972), Eq. for system Q.
        literature/thiele_small/small_1972_closed_box.md

        Tolerance: <0.02 for Qtc
        """
        # TODO: Implement when drivers are available
        # driver = get_driver_by_name(driver_name)
        # Vb = Vb_liters / 1000.0

        # params = calculate_sealed_box_system_parameters(driver, Vb)

        # Check Qtc within 0.02
        # assert abs(params.Qtc - expected_Qtc) < 0.02, \
        #     f"Qtc mismatch: {params.Qtc:.2f} vs expected {expected_Qtc:.2f}"

        pytest.skip("Requires Hornresp reference data")


class TestSealedBoxElectricalImpedance:
    """
    Test electrical impedance validation against Hornresp.

    For each test case, validates:
    - Electrical impedance magnitude (<5% general tolerance)
    - Electrical impedance phase (<10° general tolerance)
    - SPL response (<6 dB tolerance)

    Key diagnostic: Impedance should peak at Fc, not Fs.
    """

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    @pytest.mark.parametrize("driver_name,Vb_liters", [
        ("bc_8ndl51", 5),
        ("bc_8ndl51", 10),
        ("bc_8ndl51", 20),
        ("bc_15ds115", 50),
        ("bc_15ds115", 100),
        ("bc_18pzw100", 100),
    ])
    def test_electrical_impedance_magnitude(self, driver_name, Vb_liters):
        """
        Validate electrical impedance magnitude against Hornresp.

        Small (1972) - Closed-box electrical impedance
        Hornresp: "Rear Lined" configuration

        Tolerance: <5% general, <10% near resonance
        """
        # TODO: Implement when Hornresp data is available
        # driver = get_driver_by_name(driver_name)
        # Vb = Vb_liters / 1000.0

        # data_path = (
        #     Path(__file__).parent / "drivers" / driver_name / "sealed_box" /
        #     f"{driver_name}_sealed_Vb{Vb_liters}L_sim.txt"
        # )
        # hornresp_data = load_hornresp_sim_file(data_path)

        # ze_viberesp = np.array([
        #     sealed_box_electrical_impedance(f, driver, Vb=Vb)["Ze_magnitude"]
        #     for f in hornresp_data.frequency
        # ])

        # result = compare_electrical_impedance(
        #     hornresp_data.frequency,
        #     ze_viberesp,
        #     hornresp_data,
        #     tolerance_percent=5.0,
        # )

        # print(f"\n[{driver_name.upper()} Vb={Vb_liters}L] {result.summary}")
        # assert result.passed, f"Ze magnitude validation failed: {result.summary}"

        pytest.skip("Requires Hornresp reference data")

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    @pytest.mark.parametrize("driver_name,Vb_liters", [
        ("bc_8ndl51", 5),
        ("bc_8ndl51", 10),
        ("bc_8ndl51", 20),
        ("bc_15ds115", 50),
        ("bc_15ds115", 100),
        ("bc_18pzw100", 100),
    ])
    def test_electrical_impedance_phase(self, driver_name, Vb_liters):
        """
        Validate electrical impedance phase against Hornresp.

        Hornresp: "Rear Lined" configuration

        Tolerance: <10° general, <15° near resonance
        """
        # TODO: Implement when Hornresp data is available
        # driver = get_driver_by_name(driver_name)
        # Vb = Vb_liters / 1000.0

        # data_path = (
        #     Path(__file__).parent / "drivers" / driver_name / "sealed_box" /
        #     f"{driver_name}_sealed_Vb{Vb_liters}L_sim.txt"
        # )
        # hornresp_data = load_hornresp_sim_file(data_path)

        # ze_viberesp = np.array([
        #     complex(
        #         sealed_box_electrical_impedance(f, driver, Vb=Vb)["Ze_real"],
        #         sealed_box_electrical_impedance(f, driver, Vb=Vb)["Ze_imag"],
        #     )
        #     for f in hornresp_data.frequency
        # ])

        # result = compare_electrical_impedance_phase(
        #     hornresp_data.frequency,
        #     ze_viberesp,
        #     hornresp_data,
        #     tolerance_degrees=10.0,
        # )

        # print(f"\n[{driver_name.upper()} Vb={Vb_liters}L] {result.summary}")
        # assert result.passed, f"Ze phase validation failed: {result.summary}"

        pytest.skip("Requires Hornresp reference data")

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    @pytest.mark.parametrize("driver_name,Vb_liters", [
        ("bc_8ndl51", 5),
        ("bc_8ndl51", 10),
        ("bc_8ndl51", 20),
        ("bc_15ds115", 50),
        ("bc_15ds115", 100),
        ("bc_18pzw100", 100),
    ])
    def test_spl(self, driver_name, Vb_liters):
        """
        Validate SPL response against Hornresp.

        Small (1972) - Normalized pressure response
        Hornresp: "Rear Lined" configuration

        Tolerance: <6 dB (accounts for voice coil model differences)
        """
        # TODO: Implement when Hornresp data is available
        # driver = get_driver_by_name(driver_name)
        # Vb = Vb_liters / 1000.0

        # data_path = (
        #     Path(__file__).parent / "drivers" / driver_name / "sealed_box" /
        #     f"{driver_name}_sealed_Vb{Vb_liters}L_sim.txt"
        # )
        # hornresp_data = load_hornresp_sim_file(data_path)

        # spl_viberesp = np.array([
        #     sealed_box_electrical_impedance(f, driver, Vb=Vb)["SPL"]
        #     for f in hornresp_data.frequency
        # ])

        # result = compare_spl(
        #     hornresp_data.frequency,
        #     spl_viberesp,
        #     hornresp_data.spl_db,
        #     tolerance_db=6.0,
        # )

        # print(f"\n[{driver_name.upper()} Vb={Vb_liters}L] {result.summary}")
        # assert result.passed, f"SPL validation failed: {result.summary}"

        pytest.skip("Requires Hornresp reference data")


class TestSealedBoxCornerCases:
    """Test corner cases and edge conditions."""

    @pytest.mark.skip(reason="Requires driver imports")
    def test_extremely_small_box(self):
        """
        Test very small box (Qtc >> 1.0) - should still work.

        Small (1972) - System behavior with extreme α values
        Expected: Qtc > 1.0, Fc >> Fs
        """
        # TODO: Implement when drivers are available
        # driver = get_bc_8ndl51()
        # Vb = 0.002  # 2L box (extremely small)

        # params = calculate_sealed_box_system_parameters(driver, Vb)

        # α = 14/2 = 7, so Qtc ≈ 0.37 × √8 ≈ 1.05
        # assert params.Qtc > 1.0, "Qtc should be >1.0 for tiny box"
        # assert params.Fc > driver.F_s * 2, "Fc should be much higher than Fs"

        pytest.skip("Requires driver imports")

    @pytest.mark.skip(reason="Requires driver imports")
    def test_extremely_large_box(self):
        """
        Test very large box (Qtc → Qts) - should approach infinite baffle.

        Small (1972) - Limit as α → 0
        Expected: Qtc < 0.5, Fc ≈ Fs
        """
        # TODO: Implement when drivers are available
        # driver = get_bc_15ds115()  # Vas = 94L
        # Vb = 0.500  # 500L box (extremely large)

        # params = calculate_sealed_box_system_parameters(driver, Vb)

        # α = 94/500 ≈ 0.19, so Fc ≈ Fs × √1.19 ≈ 1.09 × Fs
        # System should be close to infinite baffle
        # assert params.Qtc < 0.5, "Qtc should be <0.5 for huge box"
        # assert abs(params.Fc - driver.F_s) / driver.F_s < 0.2, \
        #     "Fc should be close to Fs"

        pytest.skip("Requires driver imports")

    @pytest.mark.skip(reason="Requires driver imports")
    def test_impedance_peak_at_Fc(self):
        """
        Verify that impedance peaks at system resonance Fc.

        Small (1972) - Electrical impedance behavior
        Key diagnostic: Ze(max) occurs at Fc, not Fs

        This is a critical test to verify the model correctly accounts
        for box stiffness. If the peak occurs at Fs instead of Fc,
        the box compliance is not being applied correctly.
        """
        # TODO: Implement when drivers are available
        # driver = get_bc_8ndl51()
        # Vb = 0.010  # 10L box

        # params = calculate_sealed_box_system_parameters(driver, Vb)

        # Calculate impedance at Fc and at frequencies above/below
        # ze_at_Fc = sealed_box_electrical_impedance(params.Fc, driver, Vb)["Ze_magnitude"]
        # ze_below = sealed_box_electrical_impedance(params.Fc * 0.8, driver, Vb)["Ze_magnitude"]
        # ze_above = sealed_box_electrical_impedance(params.Fc * 1.2, driver, Vb)["Ze_magnitude"]

        # Impedance at Fc should be higher than nearby frequencies
        # assert ze_at_Fc > ze_below, "Ze at Fc should be > Ze below Fc"
        # assert ze_at_Fc > ze_above, "Ze at Fc should be > Ze above Fc"

        pytest.skip("Requires driver imports")


class TestSealedBoxComprehensiveValidation:
    """
    Comprehensive validation tests that generate full reports.

    These tests run all validation metrics and generate a comprehensive
    report showing the agreement between viberesp and Hornresp.
    """

    @pytest.mark.skip(reason="Requires Hornresp reference data - see file docstring")
    def test_bc_8ndl51_comprehensive_validation(self):
        """
        Run comprehensive validation on BC_8NDL51 and generate report.

        Tests all metrics (Ze magnitude, Ze phase, SPL) for BC_8NDL51
        in a 10L sealed box.

        Expected: <5% Ze, <10° phase, <6 dB SPL
        """
        # TODO: Implement when Hornresp data is available
        # driver = get_bc_8ndl51()
        # Vb = 0.010

        # data_path = (
        #     Path(__file__).parent / "drivers" / "bc_8ndl51" / "sealed_box" /
        #     "bc_8ndl51_sealed_Vb10L_sim.txt"
        # )
        # hornresp_data = load_hornresp_sim_file(data_path)

        # Calculate viberesp response at all frequency points
        # ze_viberesp_mag = []
        # ze_viberesp_phase = []
        # spl_viberesp = []

        # for f in hornresp_data.frequency:
        #     result = sealed_box_electrical_impedance(f, driver, Vb=Vb)
        #     ze_viberesp_mag.append(result["Ze_magnitude"])
        #     ze_vibersep_phase.append(complex(result["Ze_real"], result["Ze_imag"]))
        #     spl_viberesp.append(result["SPL"])

        # Compare all metrics
        # ze_mag_result = compare_electrical_impedance(...)
        # ze_phase_result = compare_electrical_impedance_phase(...)
        # spl_result = compare_spl(...)

        # Generate report
        # report = generate_validation_report(
        #     "BC_8NDL51",
        #     "sealed_box_Vb10L",
        #     [ze_mag_result, ze_phase_result, spl_result],
        #     output_format="text",
        # )

        # Print report for manual review
        # print("\n" + "=" * 60)
        # print(report)
        # print("=" * 60)

        # Assert all validations pass
        # assert ze_mag_result.passed
        # assert ze_phase_result.passed
        # assert spl_result.passed

        pytest.skip("Requires Hornresp reference data")
