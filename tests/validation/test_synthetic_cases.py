"""Test synthetic horn cases against Hornresp reference data."""

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


@pytest.mark.parametrize("case_id", SYNTHETIC_CASES)
def test_synthetic_case_validation(case_id, synthetic_dir, driver_from_json, load_hornresp_case, create_enclosure):
    """Test synthetic case against Hornresp reference data.

    This test:
    1. Loads driver, Hornresp parameters, and simulation
    2. Runs Viberesp simulation with same parameters
    3. Compares responses and calculates metrics
    4. Asserts metrics meet validation targets from metadata.json
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

    # Get validation targets from metadata
    targets = metadata["validation_targets"]

    # Assert against validation targets
    # Note: Current physics model may not meet these targets yet
    # These tests establish the baseline for tracking improvements
    assert metrics.rmse <= targets["rmse_max"], (
        f"RMSE {metrics.rmse:.3f} dB exceeds target {targets['rmse_max']} dB"
    )

    if metrics.f3_error is not None:
        assert abs(metrics.f3_error) <= targets["f3_error_max"], (
            f"F3 error {metrics.f3_error:.2f} Hz exceeds target {targets['f3_error_max']} Hz"
        )

    assert metrics.correlation >= targets["correlation_min"], (
        f"Correlation {metrics.correlation:.4f} below target {targets['correlation_min']}"
    )


@pytest.mark.parametrize("case_id", SYNTHETIC_CASES)
def test_synthetic_case_baseline_match(case_id, synthetic_dir, driver_from_json, load_hornresp_case, create_enclosure, case_baseline):
    """Test that current metrics match baseline (within small tolerance for numerical stability).

    This test ensures the simulation produces consistent results.
    Allow small tolerance (1%) for numerical differences across runs/platforms.
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

    # Allow 1% tolerance for numerical stability
    # Use pytest.approx for floating-point comparison
    tolerance = 0.01  # 1%

    # Compare key metrics (allow some variation)
    assert metrics.rmse == pytest.approx(baseline_metrics["rmse"], rel=tolerance), (
        f"RMSE {metrics.rmse:.3f} differs from baseline {baseline_metrics['rmse']:.3f}"
    )

    if metrics.f3_error is not None and baseline_metrics["f3_error"] is not None:
        assert metrics.f3_error == pytest.approx(baseline_metrics["f3_error"], rel=tolerance), (
            f"F3 error {metrics.f3_error:.2f} differs from baseline {baseline_metrics['f3_error']:.2f}"
        )

    assert metrics.correlation == pytest.approx(baseline_metrics["correlation"], rel=tolerance), (
        f"Correlation {metrics.correlation:.4f} differs from baseline {baseline_metrics['correlation']:.4f}"
    )


def test_all_synthetic_cases_have_metadata(synthetic_dir):
    """Verify all synthetic cases have required files."""
    required_files = ["parameters.txt", "simulation.txt", "metadata.json", "baseline.json"]

    for case_id in SYNTHETIC_CASES:
        case_dir = synthetic_dir / case_id
        assert case_dir.exists(), f"Case directory missing: {case_dir}"

        for filename in required_files:
            file_path = case_dir / filename
            assert file_path.exists(), f"Missing file: {file_path}"


def test_metadata_has_required_fields(synthetic_dir):
    """Verify metadata.json files have all required fields."""
    required_fields = [
        "id", "name", "description", "category", "tags",
        "driver", "enclosure_type", "parameters",
        "expected_behavior", "validation_targets", "created"
    ]

    for case_id in SYNTHETIC_CASES:
        case_dir = synthetic_dir / case_id
        metadata_path = case_dir / "metadata.json"

        with open(metadata_path) as f:
            metadata = json.load(f)

        for field in required_fields:
            assert field in metadata, f"Missing field '{field}' in {metadata_path}"


def test_driver_files_exist(fixture_dir):
    """Verify driver JSON files exist for all referenced drivers."""
    referenced_drivers = {"idealized_18inch", "bc_18ds115"}

    for driver_name in referenced_drivers:
        driver_path = fixture_dir / "drivers" / f"{driver_name}.json"
        assert driver_path.exists(), f"Driver file missing: {driver_path}"
