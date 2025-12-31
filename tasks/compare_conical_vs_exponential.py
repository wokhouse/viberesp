#!/usr/bin/env python3
"""
Compare conical and exponential horn performance.

This script compares the acoustic performance of conical and exponential
horns with equivalent throat area, mouth area, and length.

Usage:
    python tasks/compare_conical_vs_exponential.py --driver BC_DE250

Literature:
- Olson (1947), Chapter 5 - Horn profile comparisons
- literature/horns/conical_theory.md
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from viberesp.driver import load_driver
from viberesp.simulation.types import ConicalHorn, ExponentialHorn
from viberesp.simulation.horn_driver_integration import calculate_horn_spl_flow


def compare_horns(
    driver_name: str,
    throat_area_cm2: float = 50,
    mouth_area_cm2: float = 500,
    length_m: float = 0.5,
    freq_min: float = 20,
    freq_max: float = 20000,
    output_path: str = None
):
    """
    Compare conical vs exponential horn performance.

    Args:
        driver_name: Driver name (e.g., "BC_DE250")
        throat_area_cm2: Throat area [cm²]
        mouth_area_cm2: Mouth area [cm²]
        length_m: Horn length [m]
        freq_min: Minimum frequency [Hz]
        freq_max: Maximum frequency [Hz]
        output_path: Path to save plot (optional)

    Returns:
        dict with comparison results
    """
    # Load driver
    driver = load_driver(driver_name)

    # Convert to m²
    throat_area = throat_area_cm2 / 10000
    mouth_area = mouth_area_cm2 / 10000

    # Create horns with identical geometry
    horn_con = ConicalHorn(
        throat_area=throat_area,
        mouth_area=mouth_area,
        length=length_m
    )

    horn_exp = ExponentialHorn(
        throat_area=throat_area,
        mouth_area=mouth_area,
        length=length_m
    )

    # Calculate frequency response
    freqs = np.logspace(np.log10(freq_min), np.log10(freq_max), 500)

    result_con = calculate_horn_spl_flow(freqs, horn_con, driver)
    result_exp = calculate_horn_spl_flow(freqs, horn_exp, driver)

    # Find key characteristics
    idx_max_con = np.argmax(result_con.spl)
    idx_max_exp = np.argmax(result_exp.spl)

    # Calculate bandwidth metrics
    spl_max_con = result_con.spl[idx_max_con]
    spl_max_exp = result_exp.spl[idx_max_exp]

    # -3dB bandwidth
    idx_3db_down_con = np.where(result_con.spl < spl_max_con - 3)[0]
    idx_3db_down_exp = np.where(result_exp.spl < spl_max_exp - 3)[0]

    # Get -3dB points (if they exist)
    if len(idx_3db_down_con) > 0:
        f_3db_low_con = freqs[idx_3db_down_con[0]] if idx_3db_down_con[0] > 0 else freq_min
        f_3db_high_con = freqs[idx_3db_down_con[-1]]
    else:
        f_3db_low_con = freq_min
        f_3db_high_con = freq_max

    if len(idx_3db_down_exp) > 0:
        f_3db_low_exp = freqs[idx_3db_down_exp[0]] if idx_3db_down_exp[0] > 0 else freq_min
        f_3db_high_exp = freqs[idx_3db_down_exp[-1]]
    else:
        f_3db_low_exp = freq_min
        f_3db_high_exp = freq_max

    # Calculate efficiency (SPL averaged over passband)
    passband_mask = (freqs >= 100) & (freqs <= 5000)
    efficiency_con = np.mean(result_con.spl[passband_mask])
    efficiency_exp = np.mean(result_exp.spl[passband_mask])

    # Calculate expansion ratio
    expansion_ratio = mouth_area / throat_area
    x0 = horn_con.x0  # Distance to apex for conical

    # Get exponential cutoff
    f_cutoff = 343.0 * horn_exp.flare_constant / (2 * np.pi)

    # Create comparison plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: SPL comparison
    ax1.semilogx(freqs, result_con.spl, label='Conical Horn', linewidth=2, color='blue')
    ax1.semilogx(freqs, result_exp.spl, label='Exponential Horn', linewidth=2, color='red', linestyle='--')
    ax1.axvline(f_cutoff, color='red', linestyle=':', alpha=0.5, label=f'Exp. Cutoff: {f_cutoff:.1f} Hz')
    ax1.axhline(spl_max_con - 3, color='gray', linestyle=':', alpha=0.3, label='-3dB')

    # Mark peak frequencies
    ax1.plot(freqs[idx_max_con], spl_max_con, 'bo', markersize=8)
    ax1.plot(freqs[idx_max_exp], spl_max_exp, 'rs', markersize=8)

    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('SPL (dB) @ 1m, 2.83V', fontsize=12)
    ax1.set_title(f'Horn Profile Comparison: {driver_name}\nS_t={throat_area_cm2}cm², S_m={mouth_area_cm2}cm², L={length_m}m', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_xlim(freq_min, freq_max)

    # Add text box with key stats
    stats_text = (
        f"Conical:\n"
        f"  Peak: {spl_max_con:.2f} dB @ {freqs[idx_max_con]:.1f} Hz\n"
        f"  -3dB BW: {f_3db_low_con:.1f}-{f_3db_high_con:.1f} Hz\n"
        f"  x0 (apex): {x0:.3f} m\n\n"
        f"Exponential:\n"
        f"  Peak: {spl_max_exp:.2f} dB @ {freqs[idx_max_exp]:.1f} Hz\n"
        f"  -3dB BW: {f_3db_low_exp:.1f}-{f_3db_high_exp:.1f} Hz\n"
        f"  Cutoff: {f_cutoff:.2f} Hz\n\n"
        f"Expansion ratio: {expansion_ratio:.2f}:1"
    )
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Plot 2: Difference
    spl_diff = result_con.spl - result_exp.spl
    ax2.semilogx(freqs, spl_diff, linewidth=2, color='purple')
    ax2.axhline(0, color='black', linestyle='-', alpha=0.3)
    ax2.axhline(3, color='green', linestyle=':', alpha=0.5, label='+3 dB')
    ax2.axhline(-3, color='red', linestyle=':', alpha=0.5, label='-3 dB')
    ax2.fill_between(freqs, 0, spl_diff, where=(spl_diff > 0), alpha=0.2, color='blue', label='Conical louder')
    ax2.fill_between(freqs, 0, spl_diff, where=(spl_diff < 0), alpha=0.2, color='red', label='Exponential louder')

    ax2.set_xlabel('Frequency (Hz)', fontsize=12)
    ax2.set_ylabel('SPL Difference (Conical - Exponential) [dB]', fontsize=12)
    ax2.set_title('SPL Difference', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_xlim(freq_min, freq_max)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        print(f"Plot saved to: {output_path}")

    plt.show()

    # Return comparison results
    return {
        'driver': driver_name,
        'geometry': {
            'throat_area_cm2': throat_area_cm2,
            'mouth_area_cm2': mouth_area_cm2,
            'length_m': length_m,
            'expansion_ratio': expansion_ratio,
            'x0_m': x0
        },
        'conical': {
            'peak_spl_db': float(spl_max_con),
            'peak_freq_hz': float(freqs[idx_max_con]),
            'f3_low_hz': float(f_3db_low_con),
            'f3_high_hz': float(f_3db_high_con),
            'avg_spl_100_5k': float(efficiency_con)
        },
        'exponential': {
            'peak_spl_db': float(spl_max_exp),
            'peak_freq_hz': float(freqs[idx_max_exp]),
            'f3_low_hz': float(f_3db_low_exp),
            'f3_high_hz': float(f_3db_high_exp),
            'cutoff_hz': float(f_cutoff),
            'avg_spl_100_5k': float(efficiency_exp)
        },
        'difference': {
            'peak_spl_db': float(spl_max_con - spl_max_exp),
            'avg_spl_100_5k_db': float(efficiency_con - efficiency_exp)
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description='Compare conical vs exponential horn performance'
    )
    parser.add_argument('--driver', '-d', default='BC_DE250',
                        help='Driver name (default: BC_DE250)')
    parser.add_argument('--throat-area', type=float, default=50,
                        help='Throat area [cm²] (default: 50)')
    parser.add_argument('--mouth-area', type=float, default=500,
                        help='Mouth area [cm²] (default: 500)')
    parser.add_argument('--length', type=float, default=0.5,
                        help='Horn length [m] (default: 0.5)')
    parser.add_argument('--freq-min', type=float, default=20,
                        help='Minimum frequency [Hz] (default: 20)')
    parser.add_argument('--freq-max', type=float, default=20000,
                        help='Maximum frequency [Hz] (default: 20000)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output path for plot')

    args = parser.parse_args()

    results = compare_horns(
        driver_name=args.driver,
        throat_area_cm2=args.throat_area,
        mouth_area_cm2=args.mouth_area,
        length_m=args.length,
        freq_min=args.freq_min,
        freq_max=args.freq_max,
        output_path=args.output
    )

    # Print summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    print(f"\nDriver: {results['driver']}")
    print(f"Geometry: S_t={results['geometry']['throat_area_cm2']}cm², "
          f"S_m={results['geometry']['mouth_area_cm2']}cm², "
          f"L={results['geometry']['length_m']}m")
    print(f"Expansion ratio: {results['geometry']['expansion_ratio']:.2f}:1")
    print(f"Conical x0: {results['geometry']['x0_m']:.3f} m")

    print(f"\nConical Horn:")
    print(f"  Peak SPL: {results['conical']['peak_spl_db']:.2f} dB @ {results['conical']['peak_freq_hz']:.1f} Hz")
    print(f"  -3dB BW: {results['conical']['f3_low_hz']:.1f}-{results['conical']['f3_high_hz']:.1f} Hz")
    print(f"  Avg SPL (100-5kHz): {results['conical']['avg_spl_100_5k']:.2f} dB")

    print(f"\nExponential Horn:")
    print(f"  Peak SPL: {results['exponential']['peak_spl_db']:.2f} dB @ {results['exponential']['peak_freq_hz']:.1f} Hz")
    print(f"  -3dB BW: {results['exponential']['f3_low_hz']:.1f}-{results['exponential']['f3_high_hz']:.1f} Hz")
    print(f"  Cutoff: {results['exponential']['cutoff_hz']:.2f} Hz")
    print(f"  Avg SPL (100-5kHz): {results['exponential']['avg_spl_100_5k']:.2f} dB")

    print(f"\nDifference (Conical - Exponential):")
    print(f"  Peak SPL: {results['difference']['peak_spl_db']:+.2f} dB")
    print(f"  Avg SPL (100-5kHz): {results['difference']['avg_spl_100_5k_db']:+.2f} dB")

    # Literature-based interpretation
    print(f"\nLiterature-based Interpretation (Olson 1947):")
    if abs(results['difference']['avg_spl_100_5k_db']) < 1.0:
        print("  ✓ Similar overall efficiency - geometry dominates profile choice")
    else:
        if results['difference']['avg_spl_100_5k_db'] > 0:
            print("  → Conical shows higher efficiency in this geometry")
        else:
            print("  → Exponential shows higher efficiency in this geometry")

    print(f"\n  Conical horns: No sharp cutoff, wider bandwidth")
    print(f"  Exponential horns: Sharp cutoff at {results['exponential']['cutoff_hz']:.1f} Hz")
    print(f"  Trade-off: Bandwidth vs loading efficiency")
    print("="*70)


if __name__ == '__main__':
    main()
