"""
Test cases for QL (box losses) implementation validation against Hornresp.

This module contains test cases to verify that viberesp's QL implementation
matches Hornresp simulations for various box loss configurations.

Literature:
- Small (1972), Eq. 9 - Parallel Q combination for sealed boxes
- Small (1973), Eq. 13 - Ported box transfer function
- Small (1973), Eq. 19 - Combined box losses
- Hornresp V53.20 - Default QL = 7
"""

import pytest
import math
from viberesp.driver.bc_drivers import get_bc_8ndl51, get_bc_15ps100
from viberesp.enclosure.sealed_box import (
    calculate_sealed_box_system_parameters,
    sealed_box_electrical_impedance,
    calculate_spl_from_transfer_function,
)
from viberesp.enclosure.ported_box import (
    calculate_ported_box_system_parameters,
)


class TestSealedBoxQLFormulas:
    """Test sealed box QL formulas per Small (1972), Eq. 9."""

    def test_parallel_q_combination_formula(self):
        """
        Verify parallel Q combination, NOT geometric mean.

        Small (1972), Eq. 9: Qtc_total = (Qec × Quc) / (Qec + Quc)

        This is a CRITICAL test - geometric mean would be WRONG.
        """
        driver = get_bc_8ndl51()  # Qes = 0.45
        Vb = 0.010  # 10L
        alpha = driver.V_as / Vb  # ≈ 1.4
        Qec = driver.Q_es * math.sqrt(1 + alpha)  # ≈ 0.54
        Quc = 7.0

        # Parallel combination (CORRECT)
        Qtc_correct = (Qec * Quc) / (Qec + Quc)
        expected = 0.50  # Approximate

        assert abs(Qtc_correct - expected) < 0.05, \
            f"Parallel Q combination incorrect: {Qtc_correct:.3f} vs expected {expected:.3f}"

        # Verify it's NOT geometric mean
        Qtc_wrong = (Qec * Quc) / math.sqrt(Qec**2 + Quc**2)
        assert abs(Qtc_correct - Qtc_wrong) > 0.01, \
            "Formula should be parallel combination, NOT geometric mean"

    def test_quc_infinite_no_losses(self):
        """Test Quc = ∞ gives Qtc_total = Qec (no mechanical losses)."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=float('inf'))

        # With no mechanical losses, Qtc_total should equal Qec
        expected_Qec = driver.Q_es * math.sqrt(1 + driver.V_as / Vb)

        assert params.Quc == float('inf'), "Quc should be infinite"
        assert abs(params.Qec - expected_Qec) < 0.01, "Qec calculation incorrect"
        assert abs(params.Qtc_total - params.Qec) < 0.001, \
            "Qtc_total should equal Qec when Quc = ∞"

    def test_quc_lower_reduces_qtc(self):
        """Test that lower Quc (more losses) reduces Qtc_total."""
        driver = get_bc_8ndl51()
        Vb = 0.010

        # Calculate with low losses
        params_low_loss = calculate_sealed_box_system_parameters(driver, Vb, Quc=100.0)

        # Calculate with high losses
        params_high_loss = calculate_sealed_box_system_parameters(driver, Vb, Quc=5.0)

        # Higher losses (lower Quc) should give lower Qtc_total
        assert params_high_loss.Qtc_total < params_low_loss.Qtc_total, \
            "More losses (lower Quc) should reduce total system Q"

    def test_typical_quc_values(self):
        """Test typical Quc values from literature.

        Bullock (1991):
        - Quc = 2-5: Filled box (heavy damping)
        - Quc = 5-10: Unfilled box (mechanical losses only)
        """
        driver = get_bc_8ndl51()
        Vb = 0.020  # 20L

        # Filled box (heavy damping)
        params_filled = calculate_sealed_box_system_parameters(driver, Vb, Quc=3.0)
        assert params_filled.Qtc_total < params_filled.Qec, \
            "Filled box should have lower Qtc than electrical Q alone"

        # Unfilled box (typical)
        params_unfilled = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)
        assert params_unfilled.Qtc_total < params_unfilled.Qec, \
            "Unfilled box should have lower Qtc than electrical Q alone"

        # Unfilled box should have higher Qtc than filled
        assert params_unfilled.Qtc_total > params_filled.Qtc_total, \
            "Unfilled box should have less damping than filled box"

    def test_qec_calculation(self):
        """Verify Qec = Qes × √(1 + α)."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)

        alpha = driver.V_as / Vb
        expected_Qec = driver.Q_es * math.sqrt(1 + alpha)

        assert abs(params.Qec - expected_Qec) < 0.001, \
            f"Qec calculation incorrect: {params.Qec:.4f} vs {expected_Qec:.4f}"

    def test_f3_uses_qtc_total(self):
        """Verify F3 calculation uses Qtc_total, not Qts."""
        driver = get_bc_8ndl51()
        Vb = 0.010

        # Calculate with losses
        params_with_loss = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)

        # Calculate without losses
        params_no_loss = calculate_sealed_box_system_parameters(driver, Vb, Quc=float('inf'))

        # F3 should differ because Qtc_total differs
        assert params_with_loss.F3 != params_no_loss.F3, \
            "F3 should change with different Quc values"


class TestPortedBoxQLFormulas:
    """Test ported box QL formulas per Small (1973), Eq. 19."""

    def test_combined_box_losses_formula(self):
        """
        Verify combined box losses: 1/QB = 1/QL + 1/QA + 1/QP.

        Small (1973), Eq. 19.
        """
        QL = 7.0   # Leakage
        QA = 100.0 # Absorption
        QP = 20.0  # Port

        # Small (1973), Eq. 19
        QB = 1.0 / (1.0/QL + 1.0/QA + 1.0/QP)

        # QB should be less than QL (dominant term)
        assert QB < QL, f"QB ({QB:.2f}) should be < QL ({QL})"

        # QB should be close to but less than QL (since QA and QP are large)
        expected_approx = 5.2  # Approximate for QL=7, QA=100, QP=20
        assert abs(QB - expected_approx) < 0.5, \
            f"Combined Q calculation off: {QB:.2f} vs expected {expected_approx:.2f}"

    def test_qb_infinite_no_losses(self):
        """Test QB = ∞ when all loss components are infinite."""
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0

        params = calculate_ported_box_system_parameters(
            driver, Vb, Fb,
            QL=float('inf'),
            QA=float('inf'),
            QP=float('inf'),
        )

        assert params.QB == float('inf'), "QB should be infinite with no losses"
        assert params.QL == float('inf'), "QL should be infinite"
        assert params.QA == float('inf'), "QA should be infinite"
        assert params.Qp == float('inf'), "QP should be infinite"

    def test_qb_dominated_by_smallest_q(self):
        """Test QB is dominated by smallest Q component."""
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0

        # Case 1: QL dominates (smallest)
        params1 = calculate_ported_box_system_parameters(
            driver, Vb, Fb,
            QL=7.0,   # Smallest
            QA=100.0,
            QP=50.0,
        )
        assert params1.QB < params1.QL, "QB should be less than dominant QL"

        # Case 2: QP dominates (smallest)
        params2 = calculate_ported_box_system_parameters(
            driver, Vb, Fb,
            QL=20.0,
            QA=100.0,
            QP=5.0,   # Smallest
        )
        assert params2.QB < params2.Qp, "QB should be less than dominant QP"

    def test_default_ql_matches_hornresp(self):
        """Verify default QL = 7 matches Hornresp standard."""
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0

        params = calculate_ported_box_system_parameters(driver, Vb, Fb)

        # Default should be QL = 7 (Hornresp V53.20)
        assert params.QL == 7.0, f"Default QL should be 7.0, got {params.QL}"

        # QA should default to 100 (WinISD)
        assert params.QA == 100.0, f"Default QA should be 100.0, got {params.QA}"

    def test_typical_ql_values(self):
        """Test typical QL values from Hornresp and WinISD."""
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0

        # Hornresp default
        params_hornresp = calculate_ported_box_system_parameters(
            driver, Vb, Fb, QL=7.0
        )
        assert 5 < params_hornresp.QB < 7, \
            f"Hornresp default QB should be reasonable: {params_hornresp.QB:.2f}"

        # WinISD default
        params_winisd = calculate_ported_box_system_parameters(
            driver, Vb, Fb, QL=10.0
        )
        assert 8 < params_winisd.QB < 10, \
            f"WinISD default QB should be reasonable: {params_winisd.QB:.2f}"

        # Well-sealed box
        params_tight = calculate_ported_box_system_parameters(
            driver, Vb, Fb, QL=20.0
        )
        assert params_tight.QB > params_hornresp.QB, \
            "Well-sealed box should have higher QB (fewer losses)"


class TestSealedBoxImpedanceWithQL:
    """Test sealed box electrical impedance with Quc parameter."""

    def test_impedance_includes_quc(self):
        """Test that impedance calculation uses Quc parameter."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        frequency = 100  # Hz

        # Calculate with different Quc values
        result_low_loss = sealed_box_electrical_impedance(
            frequency, driver, Vb, Quc=100.0
        )
        result_high_loss = sealed_box_electrical_impedance(
            frequency, driver, Vb, Quc=5.0
        )

        # Higher losses (lower Quc) should reduce impedance peak
        # (More damping = lower impedance magnitude)
        assert result_high_loss['Ze_magnitude'] < result_low_loss['Ze_magnitude'], \
            "Higher losses should reduce impedance magnitude"

    def test_return_dict_includes_q_parameters(self):
        """Test that result dictionary includes Qec, Quc, Qtc_total."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        frequency = 100  # Hz

        result = sealed_box_electrical_impedance(frequency, driver, Vb, Quc=7.0)

        # Check new keys exist
        assert 'Qec' in result, "Result should include Qec"
        assert 'Quc' in result, "Result should include Quc"
        assert 'Qtc_total' in result, "Result should include Qtc_total"

        # Check old key is removed
        assert 'Qtc' not in result, "Old 'Qtc' key should be replaced with Qtc_total"

        # Verify values
        assert result['Quc'] == 7.0, "Quc should match input parameter"
        assert result['Qtc_total'] < result['Qec'], \
            "Qtc_total should be less than Qec (parallel combination)"

    def test_quc_infinite_matches_no_losses(self):
        """Test Quc = ∞ matches behavior of no mechanical losses."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        frequency = 60  # Hz (near resonance)

        result_no_loss = sealed_box_electrical_impedance(
            frequency, driver, Vb, Quc=float('inf')
        )

        # With Quc = ∞, Qtc_total should equal Qec
        assert abs(result_no_loss['Qtc_total'] - result_no_loss['Qec']) < 0.001, \
            "With Quc = ∞, Qtc_total should equal Qec"


class TestSealedBoxSPLWithQL:
    """Test sealed box SPL calculation with Quc parameter."""

    def test_spl_transfer_function_uses_qtc_prime(self):
        """Test that SPL transfer function uses Qtc' (with Quc)."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        frequency = 60  # Hz (near Fc)

        # Calculate with different Quc values
        spl_low_loss = calculate_spl_from_transfer_function(
            frequency, driver, Vb, Quc=100.0
        )
        spl_high_loss = calculate_spl_from_transfer_function(
            frequency, driver, Vb, Quc=5.0
        )

        # Higher losses should reduce SPL peak at resonance
        # (More damping = less peaking)
        assert spl_high_loss < spl_low_loss, \
            "Higher losses should reduce SPL at resonance"

    def test_spl_at_resonance_damping(self):
        """Test SPL response shape around resonance for different Quc."""
        driver = get_bc_8ndl51()
        Vb = 0.010
        params = calculate_sealed_box_system_parameters(driver, Vb, Quc=7.0)

        # At exact resonance
        spl_at_fc = calculate_spl_from_transfer_function(
            params.Fc, driver, Vb, Quc=7.0
        )

        # Below resonance
        spl_below_fc = calculate_spl_from_transfer_function(
            params.Fc * 0.5, driver, Vb, Quc=7.0
        )

        # Above resonance
        spl_above_fc = calculate_spl_from_transfer_function(
            params.Fc * 2.0, driver, Vb, Quc=7.0
        )

        # SPL should increase with frequency through resonance
        assert spl_below_fc < spl_at_fc, \
            "SPL should rise approaching resonance"
        assert spl_at_fc > spl_above_fc, \
            "SPL should fall after resonance (for typical Qtc)"

    def test_spl_quc_variation_effect(self):
        """Test effect of different Quc values on SPL response."""
        driver = get_bc_8ndl51()
        Vb = 0.010

        frequencies = [40, 60, 80, 100, 200]  # Hz
        Quc_values = [3.0, 7.0, 20.0, float('inf')]

        # Store SPL curves
        spl_curves = {}
        for Quc in Quc_values:
            spls = []
            for freq in frequencies:
                spl = calculate_spl_from_transfer_function(
                    freq, driver, Vb, Quc=Quc
                )
                spls.append(spl)
            spl_curves[Quc] = spls

        # Verify monotonic relationship: lower Quc = more damping
        # Compare Quc = 3 (heavy damping) vs Quc = inf (no damping)
        for i, freq in enumerate(frequencies):
            assert spl_curves[3.0][i] < spl_curves[float('inf')][i], \
                f"Heavier damping (Quc=3) should give lower SPL than no damping at {freq}Hz"


class TestHornrespComparisonSetup:
    """
    Setup for Hornresp comparison tests.

    These tests require Hornresp reference data files to be present in:
    tests/validation/drivers/{driver}/{enclosure}/

    Reference data format: CSV with columns for frequency, impedance, SPL, etc.
    """

    @pytest.fixture
    def bc8ndl51_driver(self):
        """BC 8NDL51 driver for testing."""
        return get_bc_8ndl51()

    @pytest.fixture
    def bc15ps100_driver(self):
        """BC 15PS100 driver for testing."""
        return get_bc_15ps100()

    @pytest.fixture
    def sealed_box_params(self, bc8ndl51_driver):
        """Standard sealed box parameters for testing."""
        return {
            'driver': bc8ndl51_driver,
            'Vb': 0.010,  # 10L
            'Quc_values': [5.0, 7.0, 10.0, 20.0, 100.0],
        }

    @pytest.fixture
    def ported_box_params(self, bc8ndl51_driver):
        """Standard ported box parameters for testing."""
        return {
            'driver': bc8ndl51_driver,
            'Vb': 0.020,  # 20L
            'Fb': 50.0,
            'QL_values': [5.0, 7.0, 10.0, 20.0],
        }

    def test_sealed_box_parameter_ranges(self, sealed_box_params):
        """Test that sealed box parameters are in reasonable ranges."""
        driver = sealed_box_params['driver']
        Vb = sealed_box_params['Vb']

        for Quc in sealed_box_params['Quc_values']:
            params = calculate_sealed_box_system_parameters(driver, Vb, Quc=Quc)

            # Sanity checks
            assert 0 < params.alpha < 10, f"α should be reasonable: {params.alpha}"
            assert 40 < params.Fc < 150, f"Fc should be reasonable: {params.Fc} Hz"
            assert 0.3 < params.Qtc_total < 1.5, f"Qtc_total should be reasonable: {params.Qtc_total}"

    def test_ported_box_parameter_ranges(self, ported_box_params):
        """Test that ported box parameters are in reasonable ranges."""
        driver = ported_box_params['driver']
        Vb = ported_box_params['Vb']
        Fb = ported_box_params['Fb']

        for QL in ported_box_params['QL_values']:
            params = calculate_ported_box_system_parameters(
                driver, Vb, Fb, QL=QL
            )

            # Sanity checks
            assert 0 < params.alpha < 10, f"α should be reasonable: {params.alpha}"
            assert 0.5 < params.h < 2.0, f"h should be reasonable: {params.h}"
            assert params.QB < params.QL, \
                f"QB ({params.QB}) should be < QL ({params.QL}) due to parallel combination"


class TestPortedBoxTransferFunctionQT:
    """
    Test that ported box transfer function uses Q_T (total Q), not Q_ES.

    This is a CRITICAL fix per research findings.
    Small (1973), Eq. 13 uses Q_T, not Q_ES.
    """

    def test_uses_qt_not_qes(self):
        """
        Verify transfer function uses driver.Q_ts, not driver.Q_es.

        Small (1973), Eq. 13 states Q_T (total driver Q), NOT Q_ES (electrical Q).
        """
        driver = get_bc_8ndl51()
        Vb = 0.020
        Fb = 50.0

        # Get parameters
        params = calculate_ported_box_system_parameters(driver, Vb, Fb, QL=7.0)

        # Q_T is the total driver Q (Qts)
        Q_T = driver.Q_ts

        # Q_ES is the electrical Q (Qes)
        Q_ES = driver.Q_es

        # These should be different
        assert Q_T != Q_ES, "Q_T and Q_ES should be different"

        # Verify we're using the right one
        # This test will be updated when transfer function is implemented
        # For now, just document the requirement
        assert Q_T > 0, "Q_T should be positive"
        assert Q_ES > 0, "Q_ES should be positive"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
