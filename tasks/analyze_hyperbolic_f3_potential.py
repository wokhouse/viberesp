#!/usr/bin/env python3
"""
Quick analysis of hyperbolic horn potential for F3 = 34 Hz target.

Tests a few representative designs to understand the design space before
running full optimization.

Literature:
    - Salmon (1946) - Hyperbolic horns for extended bass
    - Kolbrek (2018) - T parameter effects on cutoff frequency
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver import load_driver
from viberesp.simulation.types import HyperbolicHorn, MultiSegmentHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
from viberesp.optimization.objectives.response_metrics import objective_f3


def analyze_design(driver, throat_area, middle_area, mouth_area,
                   length1, length2, T1, T2, V_tc, V_rc, label):
    """Analyze a single hyperbolic horn design."""

    # Build horn
    seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=T1)
    seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=T2)
    horn = MultiSegmentHorn([seg1, seg2])

    flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

    # Calculate F3
    design_vector = np.array([throat_area, middle_area, mouth_area,
                              length1, length2, T1, T2, V_tc, V_rc])
    f3 = objective_f3(design_vector, driver, "multisegment_horn")

    # Calculate frequency response
    frequencies = np.logspace(np.log10(20), np.log10(200), 100)
    spl_values = []

    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
        except:
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Find reference SPL
    passband_mask = (frequencies >= 50) & (frequencies <= 200)
    reference_spl = np.max(spl_values[passband_mask])

    # Calculate horn volume
    m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
    m2 = np.log(mouth_area / middle_area) / length2 if length2 > 0 else 0

    # Hyperbolic volume approximation (using exponential formula)
    v1 = (middle_area - throat_area) / m1 if m1 > 0 else (throat_area + middle_area) / 2 * length1
    v2 = (mouth_area - middle_area) / m2 if m2 > 0 else (middle_area + mouth_area) / 2 * length2
    total_volume = v1 + v2

    return {
        'label': label,
        'f3': f3,
        'reference_spl': reference_spl,
        'total_length': length1 + length2,
        'total_volume': total_volume,
        'mouth_area': mouth_area,
        'compression_ratio': driver.S_d / throat_area,
        'flare_mL1': m1 * length1,
        'flare_mL2': m2 * length2,
    }


def main():
    print("=" * 80)
    print("BC_21DS115 Hyperbolic Horn Analysis")
    print("Target: F3 = 34 Hz")
    print("=" * 80)

    # Load driver
    print("\nLoading driver...")
    driver = load_driver("BC_21DS115")
    print(f"  Driver: BC_21DS115 (B&C Speakers 21\" Subwoofer)")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")

    # Design space exploration
    print("\n" + "=" * 80)
    print("Testing representative designs...")
    print("=" * 80)

    Sd = driver.S_d  # 0.168 m² (1680 cm²)

    designs = []

    # Design 1: Reference (current best exponential)
    print("\n[1] Reference exponential horn (current best: F3=58 Hz)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,      # 840 cm²
        middle_area=0.15,          # 1500 cm²
        mouth_area=1.0,            # 10000 cm² (1 m²)
        length1=1.2,
        length2=1.78,
        T1=1.0,  # Exponential
        T2=1.0,  # Exponential
        V_tc=0.0,
        V_rc=0.5 * driver.V_as,
        label="Reference exp (T1=1.0, T2=1.0)"
    ))

    # Design 2: Hyperbolic throat (T1=0.7)
    print("\n[2] Hyperbolic throat (T1=0.7, deeper bass loading)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.15,
        mouth_area=1.0,
        length1=1.2,
        length2=1.78,
        T1=0.7,  # Hypex
        T2=1.0,
        V_tc=0.0,
        V_rc=0.5 * driver.V_as,
        label="Hypex throat (T1=0.7)"
    ))

    # Design 3: Very large mouth (λ/2 at 34 Hz)
    print("\n[3] Very large mouth (λ/2 at 34 Hz = 2.5 m²)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.3,
        mouth_area=2.5,  # Large mouth
        length1=1.5,
        length2=2.5,
        T1=0.7,
        T2=1.0,
        V_tc=0.0,
        V_rc=0.5 * driver.V_as,
        label="Large mouth (2.5 m²)"
    ))

    # Design 4: Long horn (5 m total)
    print("\n[4] Long horn (5 m total)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.2,
        mouth_area=2.0,
        length1=2.0,
        length2=3.0,
        T1=0.7,
        T2=0.9,
        V_tc=0.0,
        V_rc=0.5 * driver.V_as,
        label="Long horn (5 m)"
    ))

    # Design 5: Large rear chamber (2×Vas)
    print("\n[5] Large rear chamber (2×Vas)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.2,
        mouth_area=2.0,
        length1=1.5,
        length2=2.5,
        T1=0.7,
        T2=1.0,
        V_tc=0.0,
        V_rc=2.0 * driver.V_as,  # Large rear chamber
        label="Large V_rc (2×Vas)"
    ))

    # Design 6: Aggressive all-around (large everything)
    print("\n[6] Aggressive design (large mouth, long, large chamber)")
    designs.append(analyze_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.3,
        mouth_area=2.5,
        length1=2.0,
        length2=3.0,
        T1=0.65,
        T2=0.85,
        V_tc=0.0,
        V_rc=2.5 * driver.V_as,
        label="Aggressive all-around"
    ))

    # Print results
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    print(f"\n{'Design':<30} {'F3':>8} {'SPL':>8} {'Length':>8} {'Volume':>10} {'Mouth':>10}")
    print("-" * 84)

    for d in designs:
        print(f"{d['label']:<30} {d['f3']:>8.1f} {d['reference_spl']:>8.1f} "
              f"{d['total_length']:>8.1f} {d['total_volume']*1000:>10.0f} {d['mouth_area']*10000:>10.0f}")

    # Find best F3
    best = min(designs, key=lambda d: abs(d['f3'] - 34.0))

    print("\n" + "=" * 80)
    print(f"BEST DESIGN for F3 ≈ 34 Hz: {best['label']}")
    print("=" * 80)
    print(f"  F3: {best['f3']:.1f} Hz (target: 34 Hz, deviation: {abs(best['f3']-34.0):.1f} Hz)")
    print(f"  Reference SPL: {best['reference_spl']:.1f} dB")
    print(f"  Total length: {best['total_length']:.2f} m")
    print(f"  Total volume: {best['total_volume']*1000:.1f} L")
    print(f"  Mouth area: {best['mouth_area']*10000:.0f} cm²")
    print(f"  Compression ratio: {best['compression_ratio']:.2f}:1")

    # Generate detailed frequency response plot for best design
    print("\nGenerating detailed comparison plot...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Plot 1: Frequency response comparison
    for d in designs:
        # Recreate full frequency response
        throat_area = 0.5 * Sd if d['label'] != designs[-1]['label'] else 0.5 * Sd
        middle_area = 0.15 if 'Reference' in d['label'] else (0.15 if 'Hypex throat' in d['label'] else
                                                                0.3 if 'Large mouth' in d['label'] else
                                                                0.2 if 'Long' in d['label'] or 'Large V_rc' in d['label'] else 0.3)
        mouth_area = 1.0 if 'Reference' in d['label'] or 'Hypex throat' in d['label'] else (
            2.5 if 'Large mouth' in d['label'] or 'Aggressive' in d['label'] else 2.0)
        length1 = 1.2 if 'Reference' in d['label'] or 'Hypex throat' in d['label'] else (
            1.5 if 'Large mouth' in d['label'] or 'Large V_rc' in d['label'] else 2.0)
        length2 = 1.78 if 'Reference' in d['label'] or 'Hypex throat' in d['label'] else (
            2.5 if 'Large mouth' in d['label'] or 'Large V_rc' in d['label'] else 3.0)
        T1 = 1.0 if 'Reference' in d['label'] else (
            0.7 if not ('Aggressive' in d['label']) else 0.65)
        T2 = 1.0 if 'Reference' in d['label'] or 'Hypex throat' in d['label'] or 'Large mouth' in d['label'] or 'Large V_rc' in d['label'] else (
            0.9 if 'Long' in d['label'] else 0.85)
        V_rc = 0.5 * driver.V_as if not ('Large V_rc' in d['label'] or 'Aggressive' in d['label']) else (
            2.0 * driver.V_as if 'Large V_rc' in d['label'] else 2.5 * driver.V_as)

        seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=T1)
        seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=T2)
        horn = MultiSegmentHorn([seg1, seg2])
        flh = FrontLoadedHorn(driver, horn, V_tc=0.0, V_rc=V_rc)

        frequencies = np.logspace(np.log10(20), np.log10(200), 150)
        spl_values = []

        for freq in frequencies:
            try:
                spl = flh.spl_response(freq, voltage=2.83)
                spl_values.append(spl)
            except:
                spl_values.append(np.nan)

        spl_values = np.array(spl_values)

        ax1.semilogx(frequencies, spl_values, linewidth=2, label=f"{d['label']} (F3={d['f3']:.0f} Hz)")

    ax1.axhline(best['reference_spl'] - 3, color='r', linestyle='--', alpha=0.5, label='-3 dB')
    ax1.axvline(34.0, color='orange', linestyle=':', alpha=0.7, label='Target F3 = 34 Hz')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('SPL (dB) @ 2.83V')
    ax1.set_title('BC_21DS115 Hyperbolic Horn Comparison')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.set_xlim([20, 200])
    ax1.set_ylim([85, 110])

    # Plot 2: F3 vs design parameters
    design_names = [d['label'] for d in designs]
    f3_values = [d['f3'] for d in designs]
    colors = ['green' if abs(f3 - 34.0) < 5.0 else 'red' for f3 in f3_values]

    ax2.barh(range(len(design_names)), f3_values, color=colors, alpha=0.7)
    ax2.axvline(34.0, color='orange', linestyle='--', linewidth=2, label='Target F3 = 34 Hz')
    ax2.set_yticks(range(len(design_names)))
    ax2.set_yticklabels(design_names, fontsize=9)
    ax2.set_xlabel('F3 (Hz)')
    ax2.set_title('F3 Achievement by Design')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim([20, 80])

    plt.tight_layout()

    plot_file = "tasks/BC21DS115_hyperbolic_analysis.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Plot saved to: {plot_file}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if abs(best['f3'] - 34.0) < 5.0:
        print(f"\n✓ Target achievable! Best design: {best['label']}")
        print(f"  Achieved F3: {best['f3']:.1f} Hz")
    elif best['f3'] < 34.0:
        print(f"\n✓ Target exceeded! Best design: {best['label']}")
        print(f"  Achieved F3: {best['f3']:.1f} Hz (below target)")
    else:
        print(f"\n⚠ Target not quite reached with tested designs")
        print(f"  Closest: {best['f3']:.1f} Hz (need {best['f3']-34.0:.1f} Hz lower)")
        print("\n  Suggested adjustments:")
        print("  - Increase mouth area further (λ/2 at 34 Hz needs ~2.5 m²)")
        print("  - Increase horn length (try 6-8 m total)")
        print("  - Use deeper hypex (T1=0.6-0.65)")
        print("  - Increase rear chamber (2-3×Vas)")

    print("\n  Key insights:")
    print("  1. Hyperbolic throat (T1<1.0) extends bass response")
    print("  2. Mouth size is critical: λ/2 at 34 Hz ≈ 5m circumference ≈ 2.5 m²")
    print("  3. Horn length matters: longer horns load lower frequencies")
    print("  4. Rear chamber compliance helps tuning (like ported box)")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)

    # Save results
    output_file = "tasks/BC21DS115_hyperbolic_analysis.txt"
    with open(output_file, 'w') as f:
        f.write("BC_21DS115 Hyperbolic Horn Analysis\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Target F3: 34 Hz\n\n")

        f.write("Design Comparison:\n")
        f.write(f"{'Design':<30} {'F3':>8} {'SPL':>8} {'Length':>8} {'Volume':>10} {'Mouth':>10}\n")
        f.write("-" * 84 + "\n")
        for d in designs:
            f.write(f"{d['label']:<30} {d['f3']:>8.1f} {d['reference_spl']:>8.1f} "
                   f"{d['total_length']:>8.1f} {d['total_volume']*1000:>10.0f} {d['mouth_area']*10000:>10.0f}\n")

        f.write(f"\nBest design: {best['label']}\n")
        f.write(f"  F3: {best['f3']:.1f} Hz\n")
        f.write(f"  Deviation from target: {abs(best['f3']-34.0):.1f} Hz\n")

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
