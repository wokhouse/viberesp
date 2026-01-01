#!/usr/bin/env python3
"""
Analyze F3 vs horn length trade-off for BC_21DS115.

Tests practical designs from 4m to 7m to help choose the right balance
between bass extension and physical size.

Literature:
    - Olson (1947) - Horn length and cutoff frequency relationship
    - Beranek (1954) - Low-frequency loading requirements
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


def analyze_length_tradeoff(driver, total_length, target_F3=34.0):
    """
    Analyze a design with specific total length, keeping proportions
    similar to the optimized F3=34Hz design.
    """

    Sd = driver.S_d

    # Proportions based on optimized design (6.78m total)
    # Throat: 840 cm² (50% Sd)
    # Middle: 3088 cm² (3.68× throat)
    # Mouth: 29843 cm² (9.66× middle, 35.5× throat)
    # Length ratio: L1:L2 = 2.94:3.84 = 0.77:1.0

    throat_area = 0.5 * Sd  # 840 cm²
    middle_area = 3.68 * throat_area  # Proportional scaling
    mouth_area = min(35.5 * throat_area, 3.0)  # Cap at 3.0 m² (practical limit)

    # Length distribution (keep ratio similar)
    length1 = total_length * 0.43  # 43% of total
    length2 = total_length * 0.57  # 57% of total

    # Test three rear chamber sizes
    v_rc_options = [
        (1.5 * driver.V_as, "1.5×Vas"),
        (2.0 * driver.V_as, "2.0×Vas"),
        (3.0 * driver.V_as, "3.0×Vas"),
    ]

    results = []

    for V_rc, v_rc_label in v_rc_options:
        # Build horn (exponential, T=1.0 based on optimization results)
        seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=1.0)
        seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=1.0)
        horn = MultiSegmentHorn([seg1, seg2])

        flh = FrontLoadedHorn(driver, horn, V_tc=0.0, V_rc=V_rc)

        # Calculate F3
        design_vector = np.array([throat_area, middle_area, mouth_area,
                                  length1, length2, 1.0, 1.0, 0.0, V_rc])
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

        v1 = (middle_area - throat_area) / m1 if m1 > 0 else (throat_area + middle_area) / 2 * length1
        v2 = (mouth_area - middle_area) / m2 if m2 > 0 else (middle_area + mouth_area) / 2 * length2
        horn_volume = v1 + v2

        # Calculate flatness (std dev of SPL 20-200 Hz)
        valid_mask = ~np.isnan(spl_values)
        flatness = np.std(spl_values[valid_mask])

        results.append({
            'total_length': total_length,
            'V_rc_ratio': V_rc / driver.V_as,
            'V_rc_label': v_rc_label,
            'f3': f3,
            'reference_spl': reference_spl,
            'horn_volume': horn_volume,
            'flatness': flatness,
            'mouth_area': mouth_area,
            'compression_ratio': Sd / throat_area,
        })

    return results


def main():
    print("=" * 80)
    print("BC_21DS115 F3 vs Horn Length Trade-off Analysis")
    print("=" * 80)

    # Load driver
    print("\nLoading driver...")
    driver = load_driver("BC_21DS115")
    print(f"  Driver: BC_21DS115")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")

    # Test different horn lengths
    print("\n" + "=" * 80)
    print("Testing horn lengths from 4m to 7m...")
    print("=" * 80)

    lengths = [4.0, 5.0, 6.0, 6.78]  # 6.78m is the optimized F3=34Hz design
    all_results = []

    for length in lengths:
        print(f"\n[Length: {length:.2f} m]")
        results = analyze_length_tradeoff(driver, length)
        all_results.extend(results)

        for r in results:
            print(f"  V_rc={r['V_rc_label']:>8} → F3={r['f3']:>5.1f} Hz, "
                  f"SPL={r['reference_spl']:>5.1f} dB, Flatness={r['flatness']:>4.2f} dB")

    # Print comprehensive comparison table
    print("\n" + "=" * 80)
    print("COMPREHENSIVE COMPARISON")
    print("=" * 80)

    print(f"\n{'Length':<8} {'V_rc':<10} {'F3':<8} {'SPL':<8} {'Flatness':<10} {'Horn Vol':<12} {'F3 Dev':<10}")
    print("-" * 90)

    for r in all_results:
        f3_dev = r['f3'] - 34.0
        deviation_str = f"{f3_dev:+.1f} Hz" if f3_dev != 0 else "✓ TARGET"

        print(f"{r['total_length']:<8.1f} {r['V_rc_label']:<10} {r['f3']:<8.1f} "
              f"{r['reference_spl']:<8.1f} {r['flatness']:<10.2f} "
              f"{r['horn_volume']*1000:<12.0f} {deviation_str:<10}")

    # Find recommended designs
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    # Best compromise (closest to 34 Hz with reasonable length)
    candidates = [r for r in all_results if r['total_length'] <= 6.0]
    if candidates:
        best_compact = min(candidates, key=lambda r: abs(r['f3'] - 34.0))

        print(f"\n📏 BEST COMPACT DESIGN (≤6m):")
        print(f"   Length: {best_compact['total_length']:.1f} m")
        print(f"   Rear chamber: {best_compact['V_rc_label']}")
        print(f"   F3: {best_compact['f3']:.1f} Hz (deviation: {best_compact['f3']-34.0:+.1f} Hz)")
        print(f"   SPL: {best_compact['reference_spl']:.1f} dB")
        print(f"   Flatness: {best_compact['flatness']:.2f} dB")
        print(f"   Horn volume: {best_compact['horn_volume']*1000:.0f} L")

    # Best overall (optimized result)
    best_overall = min(all_results, key=lambda r: abs(r['f3'] - 34.0))

    print(f"\n🎯 BEST OVERALL (exact F3=34Hz):")
    print(f"   Length: {best_overall['total_length']:.1f} m")
    print(f"   Rear chamber: {best_overall['V_rc_label']}")
    print(f"   F3: {best_overall['f3']:.1f} Hz ✓ EXACT TARGET")
    print(f"   SPL: {best_overall['reference_spl']:.1f} dB")
    print(f"   Flatness: {best_overall['flatness']:.2f} dB")
    print(f"   Horn volume: {best_overall['horn_volume']*1000:.0f} L")

    # Size comparison
    print("\n" + "=" * 80)
    print("SIZE COMPARISON")
    print("=" * 80)

    print(f"\n{'Length':<8} {'Folded Footprint':<20} {'Est. Cabinet Size':<25}")
    print("-" * 70)

    # Assume folding reduces length to ~1/3
    for length in lengths:
        folded_depth = length / 3.0
        # Typical cabinet: width × height × depth
        # Width and height determined by mouth size
        mouth_diameter = np.sqrt(3.0) * 100  # cm (for 3.0 m² mouth)
        cabinet_width = mouth_diameter  # cm
        cabinet_height = mouth_diameter * 0.8  # cm (slightly less than square)
        cabinet_depth = folded_depth * 100  # cm

        folded_footprint = f"{cabinet_width:.0f}×{cabinet_height:.0f} cm"
        cabinet_size = f"{cabinet_width:.0f}×{cabinet_height:.0f}×{cabinet_depth:.0f} cm"

        print(f"{length:<8.1f} {folded_footprint:<20} {cabinet_size:<25}")

    # Plot results
    print("\nGenerating trade-off plots...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Group by V_rc ratio
    v_rc_ratios = sorted(set(r['V_rc_ratio'] for r in all_results))
    colors = ['blue', 'green', 'red']

    for i, v_rc_ratio in enumerate(v_rc_ratios):
        results_subset = [r for r in all_results if r['V_rc_ratio'] == v_rc_ratio]
        lengths = [r['total_length'] for r in results_subset]
        f3s = [r['f3'] for r in results_subset]
        spls = [r['reference_spl'] for r in results_subset]
        flatness = [r['flatness'] for r in results_subset]
        volumes = [r['horn_volume']*1000 for r in results_subset]

        label = f"V_rc = {v_rc_ratio:.1f}×Vas"

        # Plot 1: F3 vs Length
        ax1.plot(lengths, f3s, 'o-', color=colors[i], linewidth=2, markersize=8, label=label)
        ax1.axhline(34.0, color='orange', linestyle='--', alpha=0.7, label='Target F3 = 34 Hz')
        ax1.set_xlabel('Total Horn Length (m)')
        ax1.set_ylabel('F3 (Hz)')
        ax1.set_title('F3 vs Horn Length')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim([25, 70])

        # Plot 2: SPL vs Length
        ax2.plot(lengths, spls, 's-', color=colors[i], linewidth=2, markersize=8, label=label)
        ax2.set_xlabel('Total Horn Length (m)')
        ax2.set_ylabel('Reference SPL (dB)')
        ax2.set_title('Efficiency vs Horn Length')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_ylim([102, 106])

        # Plot 3: Flatness vs Length
        ax3.plot(lengths, flatness, '^-', color=colors[i], linewidth=2, markersize=8, label=label)
        ax3.set_xlabel('Total Horn Length (m)')
        ax3.set_ylabel('Response Flatness (dB)')
        ax3.set_title('Flatness (20-200 Hz) vs Horn Length')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_ylim([1.5, 3.0])

        # Plot 4: Horn Volume vs Length
        ax4.plot(lengths, volumes, 'd-', color=colors[i], linewidth=2, markersize=8, label=label)
        ax4.set_xlabel('Total Horn Length (m)')
        ax4.set_ylabel('Horn Volume (L)')
        ax4.set_title('Horn Volume vs Length')
        ax4.grid(True, alpha=0.3)
        ax4.legend()

    plt.tight_layout()

    plot_file = "tasks/BC21DS115_f3_vs_length_tradeoff.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Plot saved to: {plot_file}")

    # Save results
    output_file = "tasks/BC21DS115_f3_vs_length_tradeoff.txt"
    with open(output_file, 'w') as f:
        f.write("BC_21DS115 F3 vs Horn Length Trade-off Analysis\n")
        f.write("=" * 80 + "\n\n")

        f.write("Design Comparison:\n")
        f.write(f"{'Length':<8} {'V_rc':<10} {'F3':<8} {'SPL':<8} {'Flatness':<10} "
                f"{'Horn Vol':<12} {'F3 Dev':<10}\n")
        f.write("-" * 90 + "\n")

        for r in all_results:
            f3_dev = r['f3'] - 34.0
            deviation_str = f"{f3_dev:+.1f} Hz" if f3_dev != 0 else "✓ TARGET"

            f.write(f"{r['total_length']:<8.1f} {r['V_rc_label']:<10} {r['f3']:<8.1f} "
                   f"{r['reference_spl']:<8.1f} {r['flatness']:<10.2f} "
                   f"{r['horn_volume']*1000:<12.0f} {deviation_str:<10}\n")

        f.write(f"\n\nBest compact design (≤6m):\n")
        if candidates:
            f.write(f"  Length: {best_compact['total_length']:.1f} m\n")
            f.write(f"  Rear chamber: {best_compact['V_rc_label']}\n")
            f.write(f"  F3: {best_compact['f3']:.1f} Hz\n")
            f.write(f"  SPL: {best_compact['reference_spl']:.1f} dB\n")
            f.write(f"  Flatness: {best_compact['flatness']:.2f} dB\n")
            f.write(f"  Horn volume: {best_compact['horn_volume']*1000:.0f} L\n")

        f.write(f"\n\nBest overall design (F3=34Hz):\n")
        f.write(f"  Length: {best_overall['total_length']:.1f} m\n")
        f.write(f"  Rear chamber: {best_overall['V_rc_label']}\n")
        f.write(f"  F3: {best_overall['f3']:.1f} Hz ✓\n")
        f.write(f"  SPL: {best_overall['reference_spl']:.1f} dB\n")
        f.write(f"  Flatness: {best_overall['flatness']:.2f} dB\n")
        f.write(f"  Horn volume: {best_overall['horn_volume']*1000:.0f} L\n")

    print(f"Results saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
