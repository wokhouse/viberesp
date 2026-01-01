#!/usr/bin/env python3
"""
Analyze flatness of optimizer results by loading actual design vectors.

This reads the optimization results and properly evaluates flatness
to understand the size vs F3 vs flatness trade-off.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    build_multisegment_horn,
)
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def analyze_design_flatness(throat, middle, mouth, l1, l2, t1, t2, v_rc, driver, label):
    """Analyze a single design's flatness and SPL response."""

    design = np.array([throat, middle, mouth, l1, l2, t1, t2, 0.0, v_rc])

    try:
        # Build horn
        horn, V_tc, V_rc_actual = build_multisegment_horn(design, driver, num_segments=2)
        flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc_actual)

        # Calculate SPL response across bass range
        frequencies = np.logspace(np.log10(20), np.log10(200), 50)
        spl_values = []

        for freq in frequencies:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)

        spl_values = np.array(spl_values)

        # Calculate metrics
        reference_spl = np.max(spl_values)
        flatness_std = np.std(spl_values)
        range_db = np.max(spl_values) - np.min(spl_values)

        # Find F3
        below_3db = spl_values < (reference_spl - 3)
        if np.any(below_3db):
            f3_idx = np.where(below_3db)[0][0]
            f3 = frequencies[f3_idx]
        else:
            f3 = frequencies[0]

        # Calculate horn volume
        m1 = np.log(middle / throat) / l1 if l1 > 0 else 0
        m2 = np.log(mouth / middle) / l2 if l2 > 0 else 0

        v1 = (middle - throat) / m1 if m1 > 0 else (throat + middle) / 2 * l1
        v2 = (mouth - middle) / m2 if m2 > 0 else (middle + mouth) / 2 * l2
        horn_vol = v1 + v2
        total_vol = (horn_vol + v_rc) * 1.3  # With folding overhead

        return {
            'label': label,
            'f3': f3,
            'volume': total_vol * 1000,  # L
            'flatness_std': flatness_std,
            'range_db': range_db,
            'reference_spl': reference_spl,
            'spl': spl_values,
            'frequencies': frequencies,
        }

    except Exception as e:
        print(f"  ERROR analyzing {label}: {e}")
        return None


def main():
    print("=" * 80)
    print("BC_15DS115 Flatness Analysis")
    print("=" * 80)

    # Load driver
    driver = load_driver("BC_15DS115")

    # Test designs from the optimization
    # Format: throat, middle, mouth, l1, l2, t1, t2, v_rc
    test_designs = [
        # Compact design (from optimizer)
        (0.0428, 0.15, 0.30, 1.55, 1.52, 0.821, 0.993, 0.128, "Compact (75Hz)"),

        # Mid-size
        (0.0445, 0.15, 0.30, 2.00, 2.00, 0.950, 0.990, 0.127, "Mid-size"),

        # Larger
        (0.0500, 0.20, 0.40, 2.00, 2.50, 0.950, 0.990, 0.127, "Large mouth"),

        # Very large (best F3)
        (0.0479, 0.15, 0.363, 3.79, 3.84, 0.982, 0.993, 0.142, "Very large (20Hz)"),
    ]

    results = []

    print(f"\nAnalyzing {len(test_designs)} designs...")
    print("  (This may take a minute...)\n")

    for design_data in test_designs:
        throat, middle, mouth, l1, l2, t1, t2, v_rc, label = design_data
        result = analyze_design_flatness(throat, middle, mouth, l1, l2, t1, t2, v_rc, driver, label)
        if result:
            results.append(result)
            print(f"[{label}]")
            print(f"  F3: {result['f3']:.1f} Hz")
            print(f"  Volume: {result['volume']:.0f} L")
            print(f"  Flatness (std): {result['flatness_std']:.2f} dB")
            print(f"  Range: {result['range_db']:.1f} dB")
            print(f"  Ref SPL: {result['reference_spl']:.1f} dB\n")

    # Create comparison plot
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    colors = ['blue', 'orange', 'green', 'red']

    # Plot 1: SPL responses
    ax1 = axes[0, 0]
    for i, r in enumerate(results):
        ax1.semilogx(r['frequencies'], r['spl'],
                     color=colors[i], linewidth=2, label=r['label'])
    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('SPL (dB @ 2.83V)', fontsize=12)
    ax1.set_title('SPL Response Comparison', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.set_xlim([20, 200])

    # Plot 2: Flatness vs Volume
    ax2 = axes[0, 1]
    for i, r in enumerate(results):
        ax2.scatter(r['volume'], r['flatness_std'],
                   color=colors[i], s=200, label=r['label'],
                   edgecolors='black', linewidths=1)
    ax2.set_xlabel('Total Volume (L)', fontsize=12)
    ax2.set_ylabel('Flatness (std dev dB)', fontsize=12)
    ax2.set_title('Flatness vs Cabinet Size', fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)

    # Plot 3: F3 vs Volume (colored by flatness)
    ax3 = axes[1, 0]
    for i, r in enumerate(results):
        ax3.scatter(r['volume'], r['f3'],
                   s=r['flatness_std']*30,  # Size = flatness
                   color=colors[i], alpha=0.6,
                   edgecolors='black', linewidths=1,
                   label=r['label'])
    ax3.set_xlabel('Total Volume (L)', fontsize=12)
    ax3.set_ylabel('F3 (Hz)', fontsize=12)
    ax3.set_title('F3 vs Volume (bubble size = flatness)', fontsize=14)
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)

    # Plot 4: Summary metrics
    ax4 = axes[1, 1]
    labels = [r['label'] for r in results]
    f3_vals = [r['f3'] for r in results]
    vol_vals = [r['volume'] for r in results]
    flat_vals = [r['flatness_std'] for r in results]

    x = np.arange(len(labels))
    width = 0.25

    ax4_twin = ax4.twinx()

    bars1 = ax4.bar(x - width, f3_vals, width, label='F3 (Hz)',
                    color='coral', alpha=0.7)
    bars2 = ax4.bar(x, vol_vals, width, label='Volume (L)',
                    color='steelblue', alpha=0.7)
    bars3 = ax4_twin.bar(x + width, flat_vals, width,
                         label='Flatness (dB)', color='green', alpha=0.7)

    ax4.set_xlabel('Design', fontsize=12)
    ax4.set_ylabel('F3 (Hz) / Volume (L)', fontsize=12)
    ax4_twin.set_ylabel('Flatness (dB)', fontsize=12, color='green')
    ax4.set_title('Design Metrics Comparison', fontsize=14)
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels, fontsize=8, rotation=15, ha='right')
    ax4.legend(loc='upper left', fontsize=8)
    ax4_twin.legend(loc='upper right', fontsize=8)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4_twin.tick_params(axis='y', labelcolor='green')

    plt.tight_layout()

    plot_file = "tasks/bc15ds115_flatness_analysis_detailed.png"
    plt.savefig(plot_file, dpi=150)
    print(f"\nPlot saved to: {plot_file}")

    # Summary
    print("\n" + "=" * 80)
    print("FLATNESS ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"\n{'Design':<20} {'F3':<8} {'Vol':<8} {'Flat':<10} {'Range':<10}")
    print("-" * 70)
    for r in results:
        print(f"{r['label']:<20} {r['f3']:<8.1f} {r['volume']:<8.0f} "
              f"{r['flatness_std']:<10.2f} {r['range_db']:<10.1f}")

    print("\nKey finding: Flatness varies from {:.1f} to {:.1f} dB".format(
        min(r['flatness_std'] for r in results),
        max(r['flatness_std'] for r in results)
    ))


if __name__ == "__main__":
    main()
