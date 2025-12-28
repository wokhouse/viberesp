#!/usr/bin/env python3
"""Validate the NEW optimized horn designs (with corrected frequency range).

This script validates the designs generated after fixing the frequency range issue.
It compares the NEW optimization results (with adaptive frequency range) against
the OLD results (with fixed 20-500 Hz range).

Literature:
    - Olson (1947) - Horn cutoff frequency
    - Beranek (1954) - Horn impedance and response
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from viberesp.driver.test_drivers import get_tc2_compression_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
from viberesp.optimization.parameters.exponential_horn_params import (
    calculate_horn_cutoff_frequency
)
from viberesp.simulation.constants import SPEED_OF_SOUND


def analyze_design(driver, throat_area, mouth_area, length, V_rc=0.0):
    """Analyze a single horn design.

    Args:
        driver: ThieleSmallParameters
        throat_area: Throat area (m²)
        mouth_area: Mouth area (m²)
        length: Horn length (m)
        V_rc: Rear chamber volume (m³)

    Returns:
        dict: Analysis results
    """
    # Create horn system
    horn = ExponentialHorn(throat_area, mouth_area, length)
    flh = FrontLoadedHorn(driver, horn, V_rc=V_rc)

    # Calculate cutoff frequency
    fc = calculate_horn_cutoff_frequency(throat_area, mouth_area, length, SPEED_OF_SOUND)

    # Determine appropriate frequency range for this horn type
    if fc < 100:
        f_min = 20
        f_max = 500
        horn_type = "Bass"
    elif fc < 500:
        f_min = 100
        f_max = 5000
        horn_type = "Midrange"
    else:
        f_min = 500
        f_max = 20000
        horn_type = "Tweeter"

    # Generate frequency points (log-spaced)
    frequencies = np.logspace(np.log10(f_min), np.log10(f_max), 200)

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
        except Exception as e:
            print(f"  Warning: SPL calculation failed at {freq:.1f} Hz: {e}")
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Calculate flatness metrics over different bands
    bands = {
        "full": (f_min, f_max),
        "low_mid": (fc * 1.5, fc * 3),
        "mid": (fc * 3, fc * 10),
        "high_mid": (fc * 10, fc * 20),
    }

    flatness_results = {}
    for band_name, (band_fmin, band_fmax) in bands.items():
        if band_fmin < band_fmax and band_fmin < f_max:
            mask = (frequencies >= band_fmin) & (frequencies <= min(band_fmax, f_max))
            if np.sum(mask) > 0:
                band_spl = spl_values[mask]
                valid_mask = ~np.isnan(band_spl)
                if np.sum(valid_mask) > 0:
                    flatness_results[band_name] = {
                        "std_dev": np.std(band_spl[valid_mask]),
                        "range": np.nanmax(band_spl[valid_mask]) - np.nanmin(band_spl[valid_mask]),
                        "f_range": (band_fmin, min(band_fmax, f_max)),
                    }

    # Calculate horn volume (approximate as truncated cone)
    # For exponential horn, this is an approximation
    avg_area = (throat_area + mouth_area) / 2
    volume_m3 = avg_area * length

    return {
        "horn": horn,
        "flh": flh,
        "fc": fc,
        "horn_type": horn_type,
        "frequencies": frequencies,
        "spl_values": spl_values,
        "flatness": flatness_results,
        "volume": volume_m3 * 1000,  # Convert to liters
    }


def print_comparison_table():
    """Print comparison of old vs new optimization results."""

    print("\n" + "=" * 80)
    print("OLD vs NEW Optimization Results Comparison")
    print("=" * 80)

    print("\nOLD Optimization (WRONG frequency range: 420-500 Hz only):")
    print("  Design #3 (from VALIDATION_REPORT.md):")
    print("    - Predicted flatness: 0.81 dB")
    print("    - Hornresp measured: 5.81 dB (500-5000 Hz)")
    print("    - Error: 5.0 dB (optimization completely missed variations)")
    print("    - Status: INVALID for design use")

    print("\nNEW Optimization (CORRECTED frequency range: adaptive based on Fc):")
    print("  Designs #1-3 (generated with fix):")
    print("    - All have flatness ~6.1-6.5 dB")
    print("    - Evaluates over 7000-8000 Hz bandwidth (not 80 Hz)")
    print("    - Status: PENDING Hornresp validation")

    print("\nKEY IMPROVEMENT:")
    print("  ✓ Frequency range now adaptive: 20×Fc for midrange horns")
    print("  ✓ Catches response variations across full passband")
    print("  ✓ Flatness values now realistic (6 dB vs 0.8 dB)")


def validate_new_designs():
    """Validate the new optimized designs."""

    print("=" * 80)
    print("Validating NEW Optimized Horn Designs (with Corrected Frequency Range)")
    print("=" * 80)

    # Get driver
    driver = get_tc2_compression_driver()

    # NEW optimized designs (from re-running optimization with fix)
    new_designs = [
        {
            "name": "Design #1",
            "throat_area": 225.0e-6,  # m² (225 mm²)
            "mouth_area": 102.7e-4,   # m² (102.7 cm²)
            "length": 0.459,          # m (45.9 cm)
            "V_rc": 0.0,
            "optimized_flatness": 6.49,  # dB (from new optimization)
        },
        {
            "name": "Design #2",
            "throat_area": 260.8e-6,  # m² (260.8 mm²)
            "mouth_area": 102.7e-4,   # m² (102.7 cm²)
            "length": 0.458,          # m (45.8 cm)
            "V_rc": 0.0,
            "optimized_flatness": 6.40,  # dB (from new optimization)
        },
        {
            "name": "Design #3",
            "throat_area": 281.9e-6,  # m² (281.9 mm²)
            "mouth_area": 100.9e-4,   # m² (100.9 cm²)
            "length": 0.512,          # m (51.2 cm)
            "V_rc": 0.0,
            "optimized_flatness": 6.13,  # dB (from new optimization)
        },
    ]

    results = []

    for i, design in enumerate(new_designs):
        print(f"\n{i+1}. Analyzing {design['name']}...")
        print(f"   Throat: {design['throat_area']*1e6:.1f} mm²")
        print(f"   Mouth:  {design['mouth_area']*1e4:.1f} cm²")
        print(f"   Length: {design['length']*100:.1f} cm")

        # Analyze design
        analysis = analyze_design(
            driver,
            design['throat_area'],
            design['mouth_area'],
            design['length'],
            design['V_rc']
        )

        # Print results
        print(f"   Horn Type: {analysis['horn_type']}")
        print(f"   Cutoff (Fc): {analysis['fc']:.1f} Hz")
        print(f"   Volume: {analysis['volume']:.2f} L")

        print(f"\n   Flatness Analysis (viberesp internal simulation):")
        for band_name, band_data in analysis['flatness'].items():
            f_min_band, f_max_band = band_data['f_range']
            print(f"     {band_name:12s} ({f_min_band:.0f}-{f_max_band:.0f} Hz): "
                  f"std={band_data['std_dev']:.2f} dB, "
                  f"p2p={band_data['range']:.2f} dB")

        # Compare with optimization prediction
        opt_flatness = design['optimized_flatness']
        sim_flatness = analysis['flatness']['full']['std_dev']

        print(f"\n   Optimization vs Simulation:")
        print(f"     Optimizer predicted: {opt_flatness:.2f} dB")
        print(f"     Simulation measured: {sim_flatness:.2f} dB")
        print(f"     Difference: {abs(opt_flatness - sim_flatness):.2f} dB")

        results.append({
            "design": design,
            "analysis": analysis,
        })

    # Create comparison plot
    print("\n" + "=" * 80)
    print("Generating frequency response comparison plot...")
    print("=" * 80)

    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    fig.suptitle('NEW Optimized Horn Designs - Frequency Response Comparison\n'
                 '(with Corrected Frequency Range)', fontsize=14, fontweight='bold')

    colors = ['blue', 'red', 'green']

    for i, (result, color) in enumerate(zip(results, colors)):
        ax = axes[i]
        design = result['design']
        analysis = result['analysis']

        freq = analysis['frequencies']
        spl = analysis['spl_values']
        fc = analysis['fc']

        # Plot full response
        ax.semilogx(freq, spl, color=color, linewidth=2, label='Full Response')

        # Mark cutoff frequency
        ax.axvline(fc, color='black', linestyle='--', alpha=0.5, label=f'Fc = {fc:.1f} Hz')

        # Mark evaluation bands
        band_data = analysis['flatness']
        if 'low_mid' in band_data:
            f_min_lm, f_max_lm = band_data['low_mid']['f_range']
            ax.axvspan(f_min_lm, f_max_lm, alpha=0.1, color='yellow', label='Low-Mid (1.5-3×Fc)')
        if 'mid' in band_data:
            f_min_m, f_max_m = band_data['mid']['f_range']
            ax.axvspan(f_min_m, f_max_m, alpha=0.1, color='green', label='Mid (3-10×Fc)')
        if 'high_mid' in band_data:
            f_min_hm, f_max_hm = band_data['high_mid']['f_range']
            ax.axvspan(f_min_hm, f_max_hm, alpha=0.1, color='blue', label='High-Mid (10-20×Fc)')

        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('SPL (dB)')
        ax.set_title(f"{design['name']}: Fc={fc:.1f} Hz, "
                    f"Flatness={design['optimized_flatness']:.2f} dB, "
                    f"Vol={analysis['volume']:.2f} L")
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=8)

        # Add flatness metrics as text
        text_str = "Flatness (std dev):\n"
        for band_name, band_data in analysis['flatness'].items():
            f_min_band, f_max_band = band_data['f_range']
            text_str += f"  {band_name}: {band_data['std_dev']:.2f} dB\n"

        ax.text(0.02, 0.98, text_str,
                transform=ax.transAxes, fontsize=8,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save plot
    output_dir = Path("tasks/optimized_horn_validations")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "new_designs_frequency_response.png"
    plt.savefig(output_path, dpi=150)
    print(f"✓ Saved plot to: {output_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nNEW Optimization Results (with Corrected Frequency Range):")
    print("\n  Design  Flatness(dB)  Volume(L)  Fc(Hz)  Type      Status")
    print("  ------- ------------ --------- ------- -------- --------------")

    for i, result in enumerate(results):
        design = result['design']
        analysis = result['analysis']
        fc = analysis['fc']
        horn_type = analysis['horn_type']
        flatness = design['optimized_flatness']
        volume = analysis['volume']

        print(f"  #{i+1:2d}     {flatness:6.2f}      {volume:6.2f}   {fc:6.1f}   "
              f"{horn_type:8s}  PENDING VALIDATION")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("""
1. Import the new design files into Hornresp:
   - tasks/optimized_horn_validations/tc2_optimized_1.txt
   - tasks/optimized_horn_validations/tc2_optimized_2.txt
   - tasks/optimized_horn_validations/tc2_optimized_3.txt

2. Run Hornresp simulation over FULL PASSBAND:
   - Midrange horns: 100-5000 Hz (not 420-500 Hz like before!)
   - Use 5 points per octave resolution

3. Compare Hornresp results with viberesp:
   - Expected flatness: ~6 dB (not 0.8 dB!)
   - Expected cutoff frequency: ~380-450 Hz

4. Document validation results in:
   - tasks/optimized_horn_validations/NEW_VALIDATION_REPORT.md
    """)

    print_comparison_table()

    print("\n" + "=" * 80)
    print("✓ Validation analysis complete")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = validate_new_designs()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
