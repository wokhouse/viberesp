#!/usr/bin/env python3
"""
Generate baseline metrics for all synthetic test cases.

This script runs Viberesp validation against Hornresp reference data
and generates baseline.json files for regression testing.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.horns import ExponentialHorn, FrontLoadedHorn
from viberesp.validation import parse_hornresp_output, compare_responses
from viberesp.validation.metrics import calculate_validation_metrics


def load_driver_from_json(driver_path: Path) -> ThieleSmallParameters:
    """Load driver parameters from JSON file."""
    with open(driver_path) as f:
        data = json.load(f)
    return ThieleSmallParameters(**data)


def generate_baseline(case_dir: Path, fixture_dir: Path) -> dict:
    """Generate baseline metrics for a single test case."""
    case_id = case_dir.name

    # Load metadata
    metadata_path = case_dir / "metadata.json"
    with open(metadata_path) as f:
        metadata = json.load(f)

    # Load driver
    driver_path = fixture_dir / "drivers" / f"{metadata['driver']}.json"
    driver = load_driver_from_json(driver_path)

    # Load Hornresp simulation
    sim_path = case_dir / "simulation.txt"
    hornresp_data = parse_hornresp_output(sim_path)

    # Create Viberesp simulation
    params = EnclosureParameters(
        enclosure_type=metadata['enclosure_type'],
        vb=0.0,  # Not used for horns
        **metadata['parameters']
    )

    if metadata['enclosure_type'] == 'front_loaded_horn':
        enclosure = FrontLoadedHorn(driver, params)
    else:
        enclosure = ExponentialHorn(driver, params)

    # Calculate response
    frequencies = np.logspace(1, 3, 600)
    spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

    # Compare to Hornresp
    comparison = compare_responses(
        viberesp_freq=frequencies,
        viberesp_spl=spl_db,
        viberesp_phase=phase_degrees,
        hornresp_freq=hornresp_data.frequencies,
        hornresp_spl=hornresp_data.spl,
        hornresp_phase=hornresp_data.phase,
    )

    # Calculate metrics
    metrics = calculate_validation_metrics(comparison)

    # Get current git commit
    import subprocess
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).parent.parent).decode().strip()
    except:
        commit = "unknown"

    # Build baseline dict
    baseline = {
        "test_case": case_id,
        "commit": commit,
        "date": datetime.now().isoformat(),
        "viberesp_version": "0.1.0",
        "metrics": {
            "rmse": float(metrics.rmse),
            "mae": float(metrics.mae),
            "max_error": float(metrics.max_error),
            "max_error_freq": float(metrics.max_error_freq),
            "passband_rmse": float(metrics.passband_rmse),
            "bass_rmse": float(metrics.bass_rmse),
            "f3_viberesp": float(metrics.f3_viberesp) if metrics.f3_viberesp else None,
            "f3_hornresp": float(metrics.f3_hornresp) if metrics.f3_hornresp else None,
            "f3_error": float(metrics.f3_error) if metrics.f3_error else None,
            "correlation": float(metrics.correlation),
            "agreement_score": float(metrics.agreement_score),
        },
        "model_settings": {
            "use_physics_model": True,
            "radiation_model": "beranek",
            "front_chamber_modes": metadata['parameters'].get('front_chamber_modes', 3),
        }
    }

    return baseline


def main():
    """Generate baselines for all synthetic test cases."""
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    synthetic_dir = fixture_dir / "hornresp" / "synthetic"

    cases = [
        synthetic_dir / "case1_straight_horn",
        synthetic_dir / "case2_horn_rear_chamber",
        synthetic_dir / "case3_horn_front_chamber",
        synthetic_dir / "case4_complete_system",
    ]

    all_baselines = {}
    commit = "unknown"

    for case_dir in cases:
        print(f"\n{'='*60}")
        print(f"Processing: {case_dir.name}")
        print('='*60)

        try:
            baseline = generate_baseline(case_dir, fixture_dir)
            commit = baseline["commit"]

            # Save individual baseline
            baseline_path = case_dir / "baseline.json"
            with open(baseline_path, 'w') as f:
                json.dump(baseline, f, indent=2)

            print(f"RMSE: {baseline['metrics']['rmse']:.3f} dB")
            f3_err = baseline['metrics']['f3_error']
            if f3_err is not None:
                print(f"F3 Error: {f3_err:.2f} Hz")
            else:
                print(f"F3 Error: N/A (no F3 found)")
            print(f"Correlation: {baseline['metrics']['correlation']:.4f}")
            print(f"✓ Baseline saved to {baseline_path}")

            # Add to global baselines
            all_baselines[case_dir.name] = {
                "rmse": baseline['metrics']['rmse'],
                "f3_error": baseline['metrics']['f3_error'],
                "correlation": baseline['metrics']['correlation'],
            }

        except Exception as e:
            print(f"✗ Error processing {case_dir.name}: {e}")
            import traceback
            traceback.print_exc()

    # Create global baseline file
    global_baseline = {
        "updated": datetime.now().isoformat(),
        "commit": commit,
        "test_cases": all_baselines,
    }

    global_baseline_path = fixture_dir / "baselines" / "current.json"
    global_baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(global_baseline_path, 'w') as f:
        json.dump(global_baseline, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Global baseline saved to {global_baseline_path}")

    # Create history snapshot
    history_dir = fixture_dir / "baselines" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_path = history_dir / f"{datetime.now().strftime('%Y-%m-%d')}_initial.json"
    with open(history_path, 'w') as f:
        json.dump(global_baseline, f, indent=2)

    print(f"✓ History snapshot saved to {history_path}")

    # Print summary table
    print(f"\n{'='*60}")
    print("BASELINE SUMMARY")
    print('='*60)
    print(f"{'Case':<25} {'RMSE':>8} {'F3 Err':>10} {'Corr':>8}")
    print('-'*60)
    for case_id, metrics in all_baselines.items():
        f3_str = f"{metrics['f3_error']:.2f}" if metrics['f3_error'] is not None else "N/A"
        print(f"{case_id:<25} {metrics['rmse']:>8.3f} {f3_str:>10} {metrics['correlation']:>8.4f}")


if __name__ == "__main__":
    main()
