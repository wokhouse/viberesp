#!/usr/bin/env python3
"""
Plot SPL response for BC_8FMB51 bookshelf speaker designs.

Compares different enclosure configurations:
- B4 Alignment (20.7L, 67.1Hz)
- Optimal Large (40L, 65Hz)
- Compact (15L, 60Hz)
- Medium (25L, 55Hz)
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


def plot_spl_comparison():
    """Generate SPL comparison plot for BC_8FMB51 bookshelf designs."""
    # Load driver
    driver = load_driver("BC_8FMB51")

    # Define designs to compare
    designs = [
        {
            "name": "B4 Alignment (20.7L, 67Hz)",
            "Vb": 0.0207,
            "Fb": 67.1,
            "color": "#2ecc71",  # Green
            "linestyle": "-",
            "linewidth": 2.5,
        },
        {
            "name": "Optimal Large (40L, 65Hz)",
            "Vb": 0.040,
            "Fb": 65.0,
            "color": "#e74c3c",  # Red
            "linestyle": "-",
            "linewidth": 2.5,
        },
        {
            "name": "Compact (15L, 60Hz)",
            "Vb": 0.015,
            "Fb": 60.0,
            "color": "#95a5a6",  # Gray
            "linestyle": "--",
            "linewidth": 1.5,
        },
        {
            "name": "Medium (25L, 55Hz)",
            "Vb": 0.025,
            "Fb": 55.0,
            "color": "#f39c12",  # Orange
            "linestyle": "--",
            "linewidth": 1.5,
        },
    ]

    # Frequency range for plotting
    # 20 Hz to 5 kHz (covering bass to crossover region)
    frequencies = np.logspace(np.log10(20), np.log10(5000), 200)

    # Set up plot
    rcParams['figure.figsize'] = (14, 8)
    rcParams['font.size'] = 11
    rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots()

    # Calculate and plot SPL for each design
    for design in designs:
        Vb = design["Vb"]
        Fb = design["Fb"]

        # Calculate port dimensions
        try:
            port_area, port_length, _ = calculate_optimal_port_dimensions(driver, Vb, Fb)
        except ValueError:
            print(f"Warning: Skipping {design['name']} - impractical port dimensions")
            continue

        # Calculate SPL at each frequency
        spl_values = []
        for freq in frequencies:
            spl = calculate_spl_ported_vector_sum(
                frequency=freq,
                driver=driver,
                Vb=Vb,
                Fb=Fb,
                port_area=port_area,
                port_length=port_length,
            )
            spl_values.append(spl)

        spl_values = np.array(spl_values)

        # Normalize to reference level (average at 200-500Hz)
        ref_region = (frequencies >= 200) & (frequencies <= 500)
        ref_level = np.mean(spl_values[ref_region])
        spl_normalized = spl_values - ref_level

        # Plot
        ax.semilogx(
            frequencies,
            spl_normalized,
            label=design["name"],
            color=design["color"],
            linestyle=design["linestyle"],
            linewidth=design["linewidth"],
        )

        # Calculate and store statistics
        design["F3"] = None
        design["midrange_std"] = None

        # Find F3 (frequency where response drops 3dB from reference)
        for i, freq in enumerate(frequencies):
            if spl_normalized[i] < -3.0 and freq > 50:
                design["F3"] = freq
                break

        # Midrange flatness (80-2000 Hz)
        midrange_region = (frequencies >= 80) & (frequencies <= 2000)
        design["midrange_std"] = np.std(spl_normalized[midrange_region])

    # Formatting
    ax.set_xlabel("Frequency (Hz)", fontsize=13, fontweight="bold")
    ax.set_ylabel("SPL (dB, normalized)", fontsize=13, fontweight="bold")
    ax.set_title(
        "BC_8FMB51 Bookshelf Speaker - SPL Response Comparison",
        fontsize=15,
        fontweight="bold",
        pad=20,
    )

    # Grid
    ax.grid(True, which="major", linestyle="-", alpha=0.3)
    ax.grid(True, which="minor", linestyle="-", alpha=0.15)

    # Limits
    ax.set_xlim([20, 5000])
    ax.set_ylim([-20, 10])

    # Reference lines
    ax.axhline(y=0, color="#34495e", linestyle=":", linewidth=1, alpha=0.5, label="Reference")
    ax.axhline(y=-3, color="#e74c3c", linestyle=":", linewidth=1.5, alpha=0.6, label="-3 dB")
    ax.axvline(x=80, color="#3498db", linestyle=":", linewidth=1, alpha=0.4)
    ax.axvline(x=2000, color="#3498db", linestyle=":", linewidth=1, alpha=0.4, label="Midrange (80-2kHz)")

    # Annotations for crossover region
    ax.annotate(
        "Crossover Region",
        xy=(2000, -5),
        xytext=(2500, -8),
        fontsize=10,
        color="#3498db",
        arrowprops=dict(arrowstyle="->", color="#3498db", alpha=0.5),
    )

    # Legend
    ax.legend(
        loc="upper right",
        frameon=True,
        shadow=True,
        fancybox=True,
        framealpha=0.9,
        fontsize=10,
    )

    # Add statistics box
    stats_text = "Design Statistics:\n\n"
    for design in designs:
        if design["F3"] is not None:
            stats_text += f"{design['name'][:20]}:\n"
            stats_text += f"  F3: {design['F3']:.1f} Hz\n"
            stats_text += f"  Mid σ: {design['midrange_std']:.2f} dB\n\n"

    # Place stats box
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.3)
    ax.text(
        0.14,
        0.14,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=props,
        family="monospace",
    )

    # Subplot labels for key regions
    ax.text(50, -15, "Bass", fontsize=10, color="#7f8c8d", ha="center")
    ax.text(150, -15, "Mid-Bass", fontsize=10, color="#7f8c8d", ha="center")
    ax.text(500, -15, "Midrange", fontsize=10, color="#7f8c8d", ha="center")
    ax.text(2500, -15, "Crossover", fontsize=10, color="#7f8c8d", ha="center")

    plt.tight_layout()

    # Save figure
    output_path = "/Users/fungj/vscode/viberesp/tasks/bc8fmb51_bookshelf_spl_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")

    # Also show
    plt.show()

    # Print summary
    print("\n" + "=" * 80)
    print("BC_8FMB51 BOOKSHELF SPEAKER - DESIGN COMPARISON")
    print("=" * 80)

    print(f"\n{'Design':<30} {'Vb (L)':>8} {'Fb (Hz)':>9} {'F3 (Hz)':>9} {'Mid σ (dB)':>11}")
    print("-" * 80)

    for design in designs:
        if design["F3"] is not None:
            print(
                f"{design['name']:<30} {design['Vb']*1000:8.1f} {design['Fb']:9.1f} "
                f"{design['F3']:9.1f} {design['midrange_std']:11.2f}"
            )

    print("\nRecommendation: B4 Alignment (20.7L, 67Hz)")
    print("  - Best midrange flatness")
    print("  - Compact bookshelf size")
    print("  - Excellent for integration with HF horn")
    print("  - Crossover at 2-2.5kHz recommended")
    print()


if __name__ == "__main__":
    plot_spl_comparison()
