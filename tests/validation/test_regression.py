"""Regression tests to ensure simulation quality doesn't degrade.

These tests enforce strict regression - if metrics get worse (higher RMSE, lower correlation),
the test FAILS. To update baselines after a legitimate model improvement:
1. Update baseline.json files with new metrics
2. Document the physics improvement with literature backing
3. Submit for manual review and approval
"""

import json
from pathlib import Path

import pytest
import numpy as np

from viberesp.validation import compare_responses, calculate_validation_metrics


# Test case IDs
SYNTHETIC_CASES = [
    "case1_straight_horn",
    "case2_horn_rear_chamber",
    "case3_horn_front_chamber",
    "case4_complete_system",
]


def test_regression_no_degradation(synthetic_dir, driver_from_json, load_hornresp_case, create_enclosure, case_baseline):
    """Strict regression test: fail if any metric degrades from baseline.

    This is the PRIMARY regression test that should run in CI.
    Tests will FAIL if:
    - RMSE increases (worse agreement)
    - Correlation decreases (worse agreement)
    - F3 error increases (worse frequency prediction)

    Tolerance: 0% - any degradation fails the test.
    """
    for case_id in SYNTHETIC_CASES:
        case_dir = synthetic_dir / case_id
        hr_params, hr_sim, metadata = load_hornresp_case(case_dir)

        # Load driver
        driver = driver_from_json(metadata["driver"])

        # Create Viberesp enclosure
        enclosure = create_enclosure(driver, metadata["enclosure_type"], metadata["parameters"])

        # Calculate Viberesp response
        frequencies = np.logspace(1, 3, 600)
        spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

        # Compare to Hornresp
        comparison = compare_responses(
            viberesp_freq=frequencies,
            viberesp_spl=spl_db,
            viberesp_phase=phase_degrees,
            hornresp_freq=hr_sim.frequencies,
            hornresp_spl=hr_sim.spl,
            hornresp_phase=hr_sim.phase,
        )

        # Calculate metrics
        metrics = calculate_validation_metrics(comparison)

        # Load baseline
        baseline = case_baseline(case_dir)
        baseline_metrics = baseline["metrics"]

        # Strict regression: current must be <= baseline (no degradation)
        assert metrics.rmse <= baseline_metrics["rmse"], (
            f"[{case_id}] REGRESSION: RMSE degraded from {baseline_metrics['rmse']:.3f} to {metrics.rmse:.3f} dB"
        )

        assert metrics.correlation >= baseline_metrics["correlation"], (
            f"[{case_id}] REGRESSION: Correlation degraded from {baseline_metrics['correlation']:.4f} to {metrics.correlation:.4f}"
        )

        # Check F3 error if available for both
        if metrics.f3_error is not None and baseline_metrics["f3_error"] is not None:
            # Absolute error increase (worse prediction)
            assert abs(metrics.f3_error) <= abs(baseline_metrics["f3_error"]), (
                f"[{case_id}] REGRESSION: F3 error degraded from {abs(baseline_metrics['f3_error']):.2f} to {abs(metrics.f3_error):.2f} Hz"
            )


def test_regression_improvement_tracking(synthetic_dir, driver_from_json, load_hornresp_case, create_enclosure, case_baseline):
    """Track and report improvements (informational, doesn't fail).

    This test always passes but reports metrics that have IMPROVED.
    Useful for:
    - Monitoring progress during physics model development
    - Identifying which changes help which test cases
    """
    improvements = []
    degradations = []

    for case_id in SYNTHETIC_CASES:
        case_dir = synthetic_dir / case_id
        hr_params, hr_sim, metadata = load_hornresp_case(case_dir)

        # Load driver
        driver = driver_from_json(metadata["driver"])

        # Create Viberesp enclosure
        enclosure = create_enclosure(driver, metadata["enclosure_type"], metadata["parameters"])

        # Calculate Viberesp response
        frequencies = np.logspace(1, 3, 600)
        spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

        # Compare to Hornresp
        comparison = compare_responses(
            viberesp_freq=frequencies,
            viberesp_spl=spl_db,
            viberesp_phase=phase_degrees,
            hornresp_freq=hr_sim.frequencies,
            hornresp_spl=hr_sim.spl,
            hornresp_phase=hr_sim.phase,
        )

        # Calculate metrics
        metrics = calculate_validation_metrics(comparison)

        # Load baseline
        baseline = case_baseline(case_dir)
        baseline_metrics = baseline["metrics"]

        # Track changes
        rmse_change = metrics.rmse - baseline_metrics["rmse"]
        corr_change = metrics.correlation - baseline_metrics["correlation"]

        if rmse_change < 0:  # Negative = improvement
            improvements.append(f"{case_id}: RMSE improved by {abs(rmse_change):.3f} dB")
        elif rmse_change > 0:
            degradations.append(f"{case_id}: RMSE degraded by {rmse_change:.3f} dB")

        if corr_change > 0:  # Positive = improvement
            improvements.append(f"{case_id}: Correlation improved by {corr_change:.4f}")
        elif corr_change < 0:
            degradations.append(f"{case_id}: Correlation degraded by {abs(corr_change):.4f}")

    # Report (always passes)
    if improvements:
        print("\n✓ IMPROVEMENTS DETECTED:")
        for improvement in improvements:
            print(f"  {improvement}")

    if degradations:
        print("\n⚠ DEGRADATIONS DETECTED:")
        for degradation in degradations:
            print(f"  {degradation}")

    if not improvements and not degradations:
        print("\n= No changes from baseline")

    # Always pass (informational only)
    assert True


@pytest.mark.parametrize("case_id", SYNTHETIC_CASES)
def test_individual_case_regression(case_id, synthetic_dir, driver_from_json, load_hornresp_case, create_enclosure, case_baseline):
    """Per-case regression test (useful for debugging specific failures).

    This test runs regression checks for a single case.
    Use: pytest tests/validation/test_regression.py::test_individual_case_regression -k case1
    """
    case_dir = synthetic_dir / case_id
    hr_params, hr_sim, metadata = load_hornresp_case(case_dir)

    # Load driver
    driver = driver_from_json(metadata["driver"])

    # Create Viberesp enclosure
    enclosure = create_enclosure(driver, metadata["enclosure_type"], metadata["parameters"])

    # Calculate Viberesp response
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare to Hornresp
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hr_sim.frequencies,
        hornresp_spl=hr_sim.spl,
        hornresp_phase=hr_sim.phase,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Load baseline
    baseline = case_baseline(case_dir)
    baseline_metrics = baseline["metrics"]

    # Print comparison
    print(f"\n{'='*60}")
    print(f"Regression Test: {case_id}")
    print('='*60)
    print(f"{'Metric':<20} {'Baseline':>12} {'Current':>12} {'Change':>12}")
    print('-'*60)
    print(f"{'RMSE (dB)':<20} {baseline_metrics['rmse']:>12.3f} {metrics.rmse:>12.3f} {metrics.rmse - baseline_metrics['rmse']:>12.3f}")
    print(f"{'Correlation':<20} {baseline_metrics['correlation']:>12.4f} {metrics.correlation:>12.4f} {metrics.correlation - baseline_metrics['correlation']:>12.4f}")

    if baseline_metrics["f3_error"] and metrics.f3_error:
        print(f"{'F3 Error (Hz)':<20} {abs(baseline_metrics['f3_error']):>12.2f} {abs(metrics.f3_error):>12.2f} {abs(metrics.f3_error) - abs(baseline_metrics['f3_error']):>12.2f}")

    # Strict assertions
    assert metrics.rmse <= baseline_metrics["rmse"]
    assert metrics.correlation >= baseline_metrics["correlation"]

    if metrics.f3_error is not None and baseline_metrics["f3_error"] is not None:
        assert abs(metrics.f3_error) <= abs(baseline_metrics["f3_error"])
