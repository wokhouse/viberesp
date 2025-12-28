#!/usr/bin/env python3
"""
Validate TC2 SPL response against Hornresp.

This script compares viberesp SPL calculations with Hornresp simulation
results for the TC2 test case (driver + horn, no chambers).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from viberesp.driver.test_drivers import get_tc2_compression_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def parse_hornresp_spl(sim_path: str):
    """
    Parse Hornresp sim.txt file to extract SPL data.

    Returns:
        dict with 'frequency' and 'SPL' arrays
    """
    data = {'frequency': [], 'SPL': []}

    with open(sim_path, 'r') as f:
        lines = f.readlines()

    # Skip header line
    for i, line in enumerate(lines):
        if i == 0:
            continue  # Skip header

        line = line.strip()
        if not line or line.startswith('*'):
            continue

        # Split by tab
        parts = line.split('\t')
        if len(parts) >= 5:
            try:
                freq = float(parts[0])      # Column 1: Frequency
                spl = float(parts[4])       # Column 5: SPL (dB)

                data['frequency'].append(freq)
                data['SPL'].append(spl)
            except (ValueError, IndexError) as e:
                print(f"Warning: Skipping line {i+1}: {e}")
                continue

    if not data['frequency']:
        raise ValueError(f"No data found in {sim_path}")

    # Convert to numpy arrays
    for key in data:
        data[key] = np.array(data[key])

    return data


def calculate_viberesp_spl(frequencies, driver, horn_params):
    """Calculate viberesp SPL at given frequencies."""
    throat_area, mouth_area, length = horn_params

    horn = ExponentialHorn(throat_area, mouth_area, length)
    flh = FrontLoadedHorn(driver, horn, V_tc=0.0, V_rc=0.0)

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        spl = flh.spl_response(freq, voltage=2.83, measurement_distance=1.0)
        spl_values.append(spl)

    return np.array(spl_values)


def compare_spl(hr_data, ve_spl, frequencies):
    """Compare Hornresp and viberesp SPL."""
    print("\n" + "=" * 70)
    print("SPL VALIDATION: Viberesp vs Hornresp")
    print("=" * 70)
    print()

    # Calculate errors
    spl_error = np.abs(ve_spl - hr_data['SPL'])

    # Overall statistics
    print("OVERALL STATISTICS:")
    print(f"  Mean error:   {np.mean(spl_error):.2f} dB")
    print(f"  Max error:    {np.max(spl_error):.2f} dB")
    print(f"  Median error: {np.median(spl_error):.2f} dB")
    print(f"  Std deviation: {np.std(spl_error):.2f} dB")
    print()

    # Find worst case
    worst_idx = np.argmax(spl_error)
    print(f"WORST CASE:")
    print(f"  Frequency: {hr_data['frequency'][worst_idx]:.1f} Hz")
    print(f"  Hornresp:  {hr_data['SPL'][worst_idx]:.2f} dB")
    print(f"  Viberesp:  {ve_spl[worst_idx]:.2f} dB")
    print(f"  Error:     {spl_error[worst_idx]:.2f} dB")
    print()

    # Frequency bands
    print("FREQUENCY BAND ANALYSIS:")
    bands = [
        ("Below cutoff (10-400 Hz)", hr_data['frequency'] < 400),
        ("Above cutoff (400-1000 Hz)", (hr_data['frequency'] >= 400) & (hr_data['frequency'] < 1000)),
        ("Midrange (1k-5k Hz)", (hr_data['frequency'] >= 1000) & (hr_data['frequency'] < 5000)),
        ("High (5k-10k Hz)", hr_data['frequency'] >= 5000),
    ]

    for band_name, mask in bands:
        if np.any(mask):
            err_band = spl_error[mask]
            mean_err = np.mean(err_band)
            max_err = np.max(err_band)
            print(f"  {band_name}:")
            print(f"    Mean error: {mean_err:.2f} dB (max {max_err:.2f} dB)")
    print()

    # Validation criteria
    # Above cutoff: <3 dB deviation (as per plan)
    # Below cutoff: qualitative agreement only (expected to be less accurate)
    above_cutoff_mask = hr_data['frequency'] >= 400
    mean_error_above = np.mean(spl_error[above_cutoff_mask])
    max_error_above = np.max(spl_error[above_cutoff_mask])

    print("VALIDATION CRITERIA:")
    print(f"  Above cutoff (f > 400 Hz):")
    print(f"    Mean error: {mean_error_above:.2f} dB (criteria: <3 dB)")
    print(f"    Max error:  {max_error_above:.2f} dB")
    print(f"    Status:     {'✓ PASS' if mean_error_above < 3.0 else '✗ FAIL'}")
    print()

    # Check specific frequencies
    print("SPOT CHECKS (above cutoff):")
    test_freqs = [500, 1000, 2000, 5000]
    for test_f in test_freqs:
        idx = np.argmin(np.abs(hr_data['frequency'] - test_f))
        print(f"  {hr_data['frequency'][idx]:.0f} Hz:")
        print(f"    Hornresp: {hr_data['SPL'][idx]:.2f} dB")
        print(f"    Viberesp: {ve_spl[idx]:.2f} dB")
        print(f"    Error:    {spl_error[idx]:.2f} dB")
    print()

    return mean_error_above < 3.0


def main():
    """Run SPL validation for TC2."""
    print("=" * 70)
    print("TC2 SPL VALIDATION")
    print("=" * 70)
    print()

    # Load driver and create horn
    driver = get_tc2_compression_driver()

    print("SYSTEM PARAMETERS:")
    print(f"  Driver: TC2 compression driver")
    print(f"    Sd = {driver.S_d*10000:.1f} cm²")
    print(f"    Fs = {driver.F_s:.1f} Hz")
    print(f"  Horn: Exponential")
    print(f"    Throat area = 5.0 cm²")
    print(f"    Mouth area = 200.0 cm²")
    print(f"    Length = 0.50 m")
    print(f"    Cutoff fc ≈ 404 Hz")
    print()

    # Parse Hornresp results
    sim_path = Path(__file__).parent.parent / "tests/validation/horn_theory/exp_midrange_tc2/sim.txt"
    if not sim_path.exists():
        print(f"ERROR: {sim_path} not found!")
        return 1

    print(f"Reading Hornresp data from: {sim_path}")
    hr_data = parse_hornresp_spl(str(sim_path))
    print(f"✓ Loaded {len(hr_data['frequency'])} data points")
    print(f"  Frequency range: {hr_data['frequency'][0]:.1f} - {hr_data['frequency'][-1]:.1f} Hz")
    print()

    # Calculate viberesp SPL (sample subset for speed)
    # Use every 10th point to speed up calculation
    sample_indices = np.arange(0, len(hr_data['frequency']), 10)
    freq_sample = hr_data['frequency'][sample_indices]

    print(f"Calculating viberesp SPL at {len(freq_sample)} frequency points...")
    ve_spl_sample = calculate_viberesp_spl(freq_sample, driver, (0.0005, 0.02, 0.5))
    print("✓ Viberesp calculation complete")
    print()

    # For comparison, we need Hornresp data at same points
    hr_spl_sample = hr_data['SPL'][sample_indices]

    # Compare
    passed = compare_spl(
        {'frequency': freq_sample, 'SPL': hr_spl_sample},
        ve_spl_sample,
        freq_sample
    )

    print("=" * 70)
    if passed:
        print("✓ SPL VALIDATION PASSED")
        print()
        print("Conclusion: Viberesp SPL calculation matches Hornresp within")
        print("acceptable tolerance above cutoff frequency (<3 dB mean error).")
        print()
        print("The response_flatness objective can now be used for optimization")
        print("with confidence that it matches Hornresp's behavior.")
    else:
        print("✗ SPL VALIDATION FAILED")
        print()
        print("SPL errors exceed acceptable tolerance. Need to investigate")
        print("the SPL calculation implementation.")
    print("=" * 70)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
