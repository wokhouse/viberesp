#!/usr/bin/env python3
"""
Plot the effect of QL on BC_8FMB51 bookshelf frequency response.

Shows how enclosure losses (QL) affect the frequency response,
particularly in the bass region around Fb.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

from viberesp.driver.loader import load_driver
from viberesp.enclosure.ported_box import calculate_optimal_port_dimensions
from viberesp.enclosure.ported_box_vector_sum import calculate_spl_ported_vector_sum


def plot_ql_effect():
    """Generate plots showing QL effect on frequency response."""
    # Load driver
    driver = load_driver("BC_8FMB51")

    # B4 Alignment design
    Vb = 0.0207  # 20.7 L
    Fb = 67.1    # Hz

    # Calculate port dimensions
    port_area, port_length, _ = calculate_optimal_port_dimensions(driver, Vb, Fb)

    # QL values to compare
    ql_values = [7.0, 10.0, 20.0, 50.0, 100.0]
    colors = ['#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#2ecc71']

    # Frequency range
    frequencies = np.logspace(np.log10(20), np.log10(5000), 300)

    # Calculate responses
    responses = {}
    for QL in ql_values:
        spl_values = []
        for freq in frequencies:
            spl = calculate_spl_ported_vector_sum(
                frequency=freq,
                driver=driver,
                Vb=Vb,
                Fb=Fb,
                port_area=port_area,
                port_length=port_length,
                QL=QL,
            )
            spl_values.append(spl)
        responses[QL] = np.array(spl_values)

    # Normalize all to reference (QL=100 at 200-500Hz)
    ref_region = (frequencies >= 200) & (frequencies <= 500)
    ref_level = np.mean(responses[100.0][ref_region])

    for QL in ql_values:
        responses[QL] = responses[QL] - ref_level

    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    rcParams['font.size'] = 11
    rcParams['font.family'] = 'DejaVu Sans'

    # === Plot 1: SPL Responses ===
    ax1.set_title(
        "BC_8FMB51 B4 Alignment - Effect of QL on SPL Response",
        fontsize=15,
        fontweight="bold",
        pad=15,
    )

    for QL, color in zip(ql_values, colors):
        label = f"QL={QL:.0f}"
        if QL == 7.0:
            label += " (typical box)"
        elif QL == 100.0:
            label += " (lossless)"

        ax1.semilogx(
            frequencies,
            responses[QL],
            label=label,
            color=color,
            linewidth=2.5 if QL in [7.0, 100.0] else 1.5,
            linestyle="-" if QL in [7.0, 100.0] else "--",
        )

    ax1.set_xlabel("Frequency (Hz)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("SPL (dB, normalized)", fontsize=12, fontweight="bold")
    ax1.grid(True, which="major", linestyle="-", alpha=0.3)
    ax1.grid(True, which="minor", linestyle="-", alpha=0.15)
    ax1.set_xlim([20, 5000])
    ax1.set_ylim([-20, 10])

    # Reference lines
    ax1.axhline(y=0, color="#34495e", linestyle=":", linewidth=1, alpha=0.5)
    ax1.axhline(y=-3, color="#e74c3c", linestyle=":", linewidth=1.5, alpha=0.6, label="-3 dB")
    ax1.axvline(x=Fb, color="#3498db", linestyle="-.", linewidth=1.5, alpha=0.5, label=f"Fb={Fb:.0f}Hz")

    ax1.legend(
        loc="upper right",
        frameon=True,
        shadow=True,
        fancybox=True,
        framealpha=0.9,
        fontsize=10,
    )

    # Add annotation
    ax1.text(
        100,
        -18,
        "Lower QL = more losses = damped port resonance",
        fontsize=10,
        color="#7f8c8d",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    # === Plot 2: Difference from Lossless (QL=100) ===
    ax2.set_title(
        "SPL Difference from Lossless (QL=100)",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )

    for QL, color in zip(ql_values[:-1], colors[:-1]):  # Skip QL=100 itself
        diff = responses[QL] - responses[100.0]
        label = f"QL={QL:.0f} - QL=100"

        ax2.semilogx(
            frequencies,
            diff,
            label=label,
            color=color,
            linewidth=2.0 if QL == 7.0 else 1.5,
            linestyle="-" if QL == 7.0 else "--",
        )

    ax2.set_xlabel("Frequency (Hz)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("SPL Difference (dB)", fontsize=12, fontweight="bold")
    ax2.grid(True, which="major", linestyle="-", alpha=0.3)
    ax2.grid(True, which="minor", linestyle="-", alpha=0.15)
    ax2.set_xlim([20, 5000])
    ax2.set_ylim([-5, 1])

    # Zero line
    ax2.axhline(y=0, color="#2c3e50", linestyle="-", linewidth=1.5, alpha=0.7)
    ax2.axvline(x=Fb, color="#3498db", linestyle="-.", linewidth=1.5, alpha=0.5)

    # Fill region of significant effect
    ax2.fill_between(
        [20, 100],
        -5,
        1,
        color="#e74c3c",
        alpha=0.1,
        label="Significant effect region"
    )

    ax2.legend(
        loc="lower right",
        frameon=True,
        shadow=True,
        fancybox=True,
        framealpha=0.9,
        fontsize=10,
    )

    # Add annotations
    ax2.annotate(
        "Maximum damping\nat Fb",
        xy=(Fb, -3.1),
        xytext=(Fb*1.5, -2.5),
        fontsize=10,
        color="#e74c3c",
        arrowprops=dict(arrowstyle="->", color="#e74c3c", alpha=0.7),
    )

    ax2.text(
        200,
        -4.5,
        "QL has minimal effect above 100 Hz\n(< 0.3 dB difference)",
        fontsize=10,
        color="#27ae60",
        bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.3),
    )

    plt.tight_layout()

    # Save figure
    output_path = "/Users/fungj/vscode/viberesp/tasks/bc8fmb51_ql_effect.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")

    plt.show()

    # Print summary statistics
    print("\n" + "=" * 80)
    print("QL EFFECT SUMMARY - BC_8FMB51 B4 ALIGNMENT")
    print("=" * 80)

    print(f"\n{'QL':>6} {'Bass σ':>10} {'Mid σ':>9} {'Peak dB':>10} {'Peak Hz':>10}")
    print("-" * 80)

    for QL in ql_values:
        # Bass flatness (40-80 Hz)
        bass_region = (frequencies >= 40) & (frequencies <= 80)
        bass_std = np.std(responses[QL][bass_region])

        # Midrange flatness (80-2000 Hz)
        mid_region = (frequencies >= 80) & (frequencies <= 2000)
        mid_std = np.std(responses[QL][mid_region])

        # Peak
        peak_idx = np.argmax(responses[QL])
        peak_freq = frequencies[peak_idx]
        peak_spl = responses[QL][peak_idx]

        print(f"{QL:>6.1f} {bass_std:>10.3f} {mid_std:>9.3f} {peak_spl:>10.2f} {peak_freq:>10.1f}")

    print("\nKey Observations:")
    print("  1. QL primarily affects response below 100 Hz")
    print("  2. Maximum effect at/near Fb (67 Hz)")
    print("  3. Minimal effect in midrange and crossover regions")
    print("  4. For bookshelf + subwoofer: QL=7-10 is appropriate")
    print("  5. For standalone: QL=15-20 gives slightly more bass")
    print()


if __name__ == "__main__":
    plot_ql_effect()
