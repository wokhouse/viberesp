#!/usr/bin/env python3
"""Parameter sweep analysis for exponential horn optimization.

This script sweeps key horn parameters to understand:
1. How mouth size affects flatness and loading
2. How throat size affects response
3. How length affects cutoff frequency and flatness
4. Optimal parameter combinations for <3 dB flatness

Literature:
    - Olson (1947) - Horn parameter relationships
    - Beranek (1954) - Mouth size requirements
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple

from viberesp.driver.test_drivers import get_tc2_compression_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
from viberesp.optimization.parameters.exponential_horn_params import (
    calculate_horn_cutoff_frequency,
    calculate_horn_volume
)
from viberesp.simulation.constants import SPEED_OF_SOUND


def calculate_flatness(driver: 'ThieleSmallParameters',
                      throat_area: float,
                      mouth_area: float,
                      length: float,
                      V_rc: float = 0.0,
                      f_min_mult: float = 2.0,
                      f_max_mult: float = 10.0,
                      n_points: int = 100) -> Dict:
    """
    Calculate horn response and flatness metrics.

    Args:
        driver: ThieleSmallParameters
        throat_area: Throat area (m²)
        mouth_area: Mouth area (m²)
        length: Horn length (m)
        V_rc: Rear chamber volume (m³)
        f_min_mult: Lower frequency multiplier for Fc (e.g., 2.0 = 2×Fc)
        f_max_mult: Upper frequency multiplier for Fc (e.g., 10.0 = 10×Fc)
        n_points: Number of frequency points

    Returns:
        dict: Analysis results including flatness metrics
    """
    # Create horn
    horn = ExponentialHorn(throat_area, mouth_area, length)
    flh = FrontLoadedHorn(driver, horn, V_rc=V_rc)

    # Calculate cutoff frequency
    fc = calculate_horn_cutoff_frequency(throat_area, mouth_area, length, SPEED_OF_SOUND)

    # Frequency range for analysis
    f_min = fc * f_min_mult
    f_max = fc * f_max_mult

    # Generate frequency points
    frequencies = np.logspace(np.log10(f_min), np.log10(f_max), n_points)

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
        except Exception as e:
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)
    valid_mask = ~np.isnan(spl_values)

    if np.sum(valid_mask) == 0:
        return {
            'fc': fc,
            'flatness_std': 100.0,
            'flatness_p2p': 100.0,
            'frequencies': frequencies,
            'spl': spl_values,
        }

    # Calculate flatness metrics
    std_dev = np.std(spl_values[valid_mask])
    peak_to_peak = np.nanmax(spl_values) - np.nanmin(spl_values)

    # Calculate mouth size metric
    wavelength_fc = SPEED_OF_SOUND / fc
    mouth_radius = np.sqrt(mouth_area / np.pi)
    mouth_circumference = 2 * np.pi * mouth_radius
    mouth_loading_ratio = mouth_circumference / wavelength_fc

    # Calculate volume
    volume = calculate_horn_volume(throat_area, mouth_area, length) * 1000  # L

    return {
        'fc': fc,
        'flatness_std': std_dev,
        'flatness_p2p': peak_to_peak,
        'mouth_loading_ratio': mouth_loading_ratio,
        'volume': volume,
        'frequencies': frequencies,
        'spl': spl_values,
        'f_min': f_min,
        'f_max': f_max,
    }


def sweep_mouth_area(driver: 'ThieleSmallParameters',
                     throat_area: float,
                     length: float,
                     mouth_areas: np.ndarray) -> Tuple[Dict, plt.Figure]:
    """Sweep mouth area to understand loading effects."""

    print("\n" + "="*70)
    print("SWEEP 1: Mouth Area Effect on Flatness")
    print("="*70)

    results = []
    for mouth_area in mouth_areas:
        result = calculate_flatness(driver, throat_area, mouth_area, length)
        result['mouth_area_cm2'] = mouth_area * 1e4
        results.append(result)

        # Check mouth loading
        ratio = result['mouth_loading_ratio']
        status = "✓" if ratio >= 1.0 else "✗"
        print(f"  Mouth: {mouth_area*1e4:6.1f} cm² | "
              f"Loading: {ratio:.2f} {status} | "
              f"Fc: {result['fc']:6.1f} Hz | "
              f"Flatness: {result['flatness_std']:5.2f} dB")

    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    mouth_cm2 = [r['mouth_area_cm2'] for r in results]
    flatness = [r['flatness_std'] for r in results]
    loading = [r['mouth_loading_ratio'] for r in results]
    fc = [r['fc'] for r in results]

    # Plot 1: Flatness vs mouth area
    ax1.plot(mouth_cm2, flatness, 'bo-', linewidth=2, markersize=8)
    ax1.axhline(y=3.0, color='g', linestyle='--', label='Target: <3 dB')
    ax1.axhline(y=4.0, color='orange', linestyle='--', label='Acceptable: <4 dB')
    ax1.set_xlabel('Mouth Area (cm²)', fontsize=12)
    ax1.set_ylabel('Flatness (std dev, dB)', fontsize=12)
    ax1.set_title('Flatness vs Mouth Area', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Mouth loading ratio
    ax2.plot(mouth_cm2, loading, 'ro-', linewidth=2, markersize=8, label='Loading ratio')
    ax2.axhline(y=1.0, color='g', linestyle='--', linewidth=2, label='Beranek criterion (≥1.0)')
    ax2.set_xlabel('Mouth Area (cm²)', fontsize=12)
    ax2.set_ylabel('Mouth Circumference / Wavelength at Fc', fontsize=12)
    ax2.set_title('Mouth Loading vs Mouth Area', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()

    return {'results': results, 'figure': fig}


def sweep_throat_area(driver: 'ThieleSmallParameters',
                      throat_areas: np.ndarray,
                      mouth_area: float,
                      length: float) -> Tuple[Dict, plt.Figure]:
    """Sweep throat area to understand throat coupling effects."""

    print("\n" + "="*70)
    print("SWEEP 2: Throat Area Effect on Flatness")
    print("="*70)

    results = []
    for throat_area in throat_areas:
        result = calculate_flatness(driver, throat_area, mouth_area, length)
        result['throat_area_mm2'] = throat_area * 1e6
        results.append(result)

        print(f"  Throat: {throat_area*1e6:6.1f} mm² | "
              f"Fc: {result['fc']:6.1f} Hz | "
              f"Flatness: {result['flatness_std']:5.2f} dB")

    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    throat_mm2 = [r['throat_area_mm2'] for r in results]
    flatness = [r['flatness_std'] for r in results]
    fc = [r['fc'] for r in results]

    # Plot 1: Flatness vs throat area
    ax1.plot(throat_mm2, flatness, 'bo-', linewidth=2, markersize=8)
    ax1.axhline(y=3.0, color='g', linestyle='--', label='Target: <3 dB')
    ax1.set_xlabel('Throat Area (mm²)', fontsize=12)
    ax1.set_ylabel('Flatness (std dev, dB)', fontsize=12)
    ax1.set_title('Flatness vs Throat Area', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Cutoff frequency vs throat area
    ax2.plot(throat_mm2, fc, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Throat Area (mm²)', fontsize=12)
    ax2.set_ylabel('Cutoff Frequency (Hz)', fontsize=12)
    ax2.set_title('Cutoff Frequency vs Throat Area', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    return {'results': results, 'figure': fig}


def sweep_length(driver: 'ThieleSmallParameters',
                 throat_area: float,
                 mouth_area: float,
                 lengths: np.ndarray) -> Tuple[Dict, plt.Figure]:
    """Sweep horn length to understand cutoff frequency effects."""

    print("\n" + "="*70)
    print("SWEEP 3: Horn Length Effect on Flatness")
    print("="*70)

    results = []
    for length in lengths:
        result = calculate_flatness(driver, throat_area, mouth_area, length)
        result['length_cm'] = length * 100
        results.append(result)

        # Check mouth loading
        ratio = result['mouth_loading_ratio']
        status = "✓" if ratio >= 1.0 else "✗"
        print(f"  Length: {length*100:6.1f} cm | "
              f"Fc: {result['fc']:6.1f} Hz | "
              f"Loading: {ratio:.2f} {status} | "
              f"Flatness: {result['flatness_std']:5.2f} dB")

    # Create plot
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    length_cm = [r['length_cm'] for r in results]
    flatness = [r['flatness_std'] for r in results]
    fc = [r['fc'] for r in results]
    loading = [r['mouth_loading_ratio'] for r in results]

    # Plot 1: Flatness vs length
    ax1.plot(length_cm, flatness, 'bo-', linewidth=2, markersize=8)
    ax1.axhline(y=3.0, color='g', linestyle='--', label='Target: <3 dB')
    ax1.set_xlabel('Horn Length (cm)', fontsize=12)
    ax1.set_ylabel('Flatness (std dev, dB)', fontsize=12)
    ax1.set_title('Flatness vs Horn Length', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot 2: Cutoff frequency vs length
    ax2.plot(length_cm, fc, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Horn Length (cm)', fontsize=12)
    ax2.set_ylabel('Cutoff Frequency (Hz)', fontsize=12)
    ax2.set_title('Cutoff Frequency vs Horn Length', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Mouth loading vs length
    ax3.plot(length_cm, loading, 'go-', linewidth=2, markersize=8)
    ax3.axhline(y=1.0, color='r', linestyle='--', linewidth=2, label='Beranek criterion (≥1.0)')
    ax3.set_xlabel('Horn Length (cm)', fontsize=12)
    ax3.set_ylabel('Mouth Circumference / Wavelength at Fc', fontsize=12)
    ax3.set_title('Mouth Loading vs Horn Length', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    plt.tight_layout()

    return {'results': results, 'figure': fig}


def analyze_parameter_interactions(driver: 'ThieleSmallParameters') -> plt.Figure:
    """Create a 2D heatmap showing mouth vs length interaction."""

    print("\n" + "="*70)
    print("SWEEP 4: Parameter Interaction (Mouth Area × Length)")
    print("="*70)

    # Fixed throat area (typical for TC2)
    throat_area = 200e-6  # m² (200 mm²)

    # Parameter ranges
    mouth_areas = np.linspace(0.02, 0.06, 15)  # 200-600 cm²
    lengths = np.linspace(0.3, 0.8, 12)  # 30-80 cm

    # Calculate flatness for each combination
    flatness_matrix = np.zeros((len(lengths), len(mouth_areas)))
    fc_matrix = np.zeros((len(lengths), len(mouth_areas)))
    loading_matrix = np.zeros((len(lengths), len(mouth_areas)))

    for i, length in enumerate(lengths):
        for j, mouth_area in enumerate(mouth_areas):
            result = calculate_flatness(driver, throat_area, mouth_area, length)
            flatness_matrix[i, j] = result['flatness_std']
            fc_matrix[i, j] = result['fc']
            loading_matrix[i, j] = result['mouth_loading_ratio']

    # Create heatmap plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    extent = [mouth_areas[0]*1e4, mouth_areas[-1]*1e4,
              lengths[-1]*100, lengths[0]*100]

    # Plot 1: Flatness heatmap
    im1 = axes[0].imshow(flatness_matrix, extent=extent, aspect='auto', cmap='RdYlGn_r', vmin=0, vmax=8)
    axes[0].set_xlabel('Mouth Area (cm²)', fontsize=12)
    axes[0].set_ylabel('Horn Length (cm)', fontsize=12)
    axes[0].set_title('Flatness (std dev, dB)\nLower is better', fontsize=14, fontweight='bold')
    plt.colorbar(im1, ax=axes[0], label='Std Dev (dB)')

    # Plot 2: Cutoff frequency heatmap
    im2 = axes[1].imshow(fc_matrix, extent=extent, aspect='auto', cmap='viridis')
    axes[1].set_xlabel('Mouth Area (cm²)', fontsize=12)
    axes[1].set_ylabel('Horn Length (cm)', fontsize=12)
    axes[1].set_title('Cutoff Frequency (Hz)', fontsize=14, fontweight='bold')
    plt.colorbar(im2, ax=axes[1], label='Fc (Hz)')

    # Plot 3: Mouth loading heatmap
    im3 = axes[2].imshow(loading_matrix, extent=extent, aspect='auto', cmap='RdYlGn', vmin=0.5, vmax=1.5)
    axes[2].set_xlabel('Mouth Area (cm²)', fontsize=12)
    axes[2].set_ylabel('Horn Length (cm)', fontsize=12)
    axes[2].set_title('Mouth Loading Ratio\nGreen = Good (≥1.0)', fontsize=14, fontweight='bold')
    plt.colorbar(im3, ax=axes[2], label='Ratio')

    # Add contour line for flatness = 3 dB target
    axes[0].contour(mouth_areas*1e4, lengths*100, flatness_matrix,
                   levels=[3.0], colors='blue', linewidths=2, linestyles='--')
    axes[0].text(0.05, 0.95, '--- 3 dB target', transform=axes[0].transAxes,
                color='blue', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    # Find optimal parameters
    min_idx = np.unravel_index(np.argmin(flatness_matrix), flatness_matrix.shape)
    optimal_length = lengths[min_idx[0]] * 100
    optimal_mouth = mouth_areas[min_idx[1]] * 1e4
    optimal_flatness = flatness_matrix[min_idx[0], min_idx[1]]
    optimal_fc = fc_matrix[min_idx[0], min_idx[1]]
    optimal_loading = loading_matrix[min_idx[0], min_idx[1]]

    print(f"\nOptimal parameters found:")
    print(f"  Mouth: {optimal_mouth:.1f} cm²")
    print(f"  Length: {optimal_length:.1f} cm")
    print(f"  Throat: 200 mm² (fixed)")
    print(f"  Fc: {optimal_fc:.1f} Hz")
    print(f"  Loading: {optimal_loading:.2f}")
    print(f"  Flatness: {optimal_flatness:.2f} dB")

    if optimal_loading >= 1.0 and optimal_flatness < 3.0:
        print(f"\n✓ MEETS TARGET: <3 dB flatness with proper loading!")
    elif optimal_loading >= 1.0:
        print(f"\n⚠ Proper loading but flatness still above target")
    else:
        print(f"\n✗ Neither criterion met")

    return fig


def main():
    """Run all parameter sweeps."""

    print("="*70)
    print("HORN PARAMETER SWEEP ANALYSIS")
    print("="*70)
    print("\nAnalyzing how horn parameters affect frequency response flatness...")
    print("Driver: TC2 (compression driver)")

    # Get driver
    driver = get_tc2_compression_driver()

    # Create output directory
    output_dir = Path("tasks/optimized_horn_validations")
    output_dir.mkdir(exist_ok=True)

    # ===== SWEEP 1: Mouth Area =====
    print("\n" + "="*70)
    print("SWEEP 1: How Mouth Size Affects Flatness")
    print("="*70)
    print("Fixed: Throat = 200 mm², Length = 60 cm")
    print("Varying: Mouth area from 100 to 600 cm²")

    sweep1 = sweep_mouth_area(
        driver,
        throat_area=200e-6,  # 200 mm²
        length=0.6,  # 60 cm
        mouth_areas=np.linspace(0.01, 0.06, 20)  # 100-600 cm²
    )

    fig1_path = output_dir / "sweep1_mouth_area.png"
    sweep1['figure'].savefig(fig1_path, dpi=150)
    print(f"\n✓ Saved: {fig1_path}")
    plt.close(sweep1['figure'])

    # ===== SWEEP 2: Throat Area =====
    print("\n" + "="*70)
    print("SWEEP 2: How Throat Size Affects Flatness")
    print("="*70)
    print("Fixed: Mouth = 400 cm², Length = 60 cm")
    print("Varying: Throat area from 100 to 400 mm²")

    sweep2 = sweep_throat_area(
        driver,
        throat_areas=np.linspace(100e-6, 400e-6, 20),  # 100-400 mm²
        mouth_area=0.04,  # 400 cm²
        length=0.6,  # 60 cm
    )

    fig2_path = output_dir / "sweep2_throat_area.png"
    sweep2['figure'].savefig(fig2_path, dpi=150)
    print(f"\n✓ Saved: {fig2_path}")
    plt.close(sweep2['figure'])

    # ===== SWEEP 3: Horn Length =====
    print("\n" + "="*70)
    print("SWEEP 3: How Horn Length Affects Flatness")
    print("="*70)
    print("Fixed: Throat = 200 mm², Mouth = 400 cm²")
    print("Varying: Length from 30 to 80 cm")

    sweep3 = sweep_length(
        driver,
        throat_area=200e-6,  # 200 mm²
        mouth_area=0.04,  # 400 cm²
        lengths=np.linspace(0.3, 0.8, 20)  # 30-80 cm
    )

    fig3_path = output_dir / "sweep3_horn_length.png"
    sweep3['figure'].savefig(fig3_path, dpi=150)
    print(f"\n✓ Saved: {fig3_path}")
    plt.close(sweep3['figure'])

    # ===== SWEEP 4: Parameter Interaction =====
    print("\n" + "="*70)
    print("SWEEP 4: Parameter Interaction (2D Heatmap)")
    print("="*70)
    print("Fixed: Throat = 200 mm²")
    print("Varying: Mouth (200-600 cm²) × Length (30-80 cm)")

    fig4 = analyze_parameter_interactions(driver)

    fig4_path = output_dir / "sweep4_parameter_interaction.png"
    fig4.savefig(fig4_path, dpi=150)
    print(f"\n✓ Saved: {fig4_path}")
    plt.close(fig4)

    # ===== SUMMARY =====
    print("\n" + "="*70)
    print("SWEEP ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nAll plots saved to: {output_dir}")
    print("""
Generated files:
  - sweep1_mouth_area.png: Mouth size vs flatness
  - sweep2_throat_area.png: Throat size vs flatness
  - sweep3_horn_length.png: Length vs flatness
  - sweep4_parameter_interaction.png: 2D parameter space heatmap

Key findings to look for:
  1. At what mouth size does flatness plateau?
  2. Does throat size significantly affect flatness?
  3. What length gives the best trade-off between Fc and flatness?
  4. What parameter combinations achieve <3 dB flatness?
    """)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Sweep analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
