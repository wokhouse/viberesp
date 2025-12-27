"""
Compare viberesp ported box simulations with Hornresp results.

This script reads viberesp CSV results and Hornresp exported data,
then generates comparison plots and statistics.

Usage:
    1. Run Hornresp simulations and export impedance/SPL data
    2. Save Hornresp exports as CSV files with naming convention:
       "{DRIVER}_ported_B4_hornresp.csv"
    3. Run this script to generate comparison plots

Literature:
- Thiele (1971) - Vented box theory
- Beranek (1954) - Radiation impedance
"""

import numpy as np
import matplotlib.pyplot as plt
import csv
from pathlib import Path
from typing import Optional, Dict, List


def read_csv(filepath: str) -> List[Dict]:
    """Read CSV file into list of dictionaries."""
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def interpolate_hornresp_to_viberesp_freqs(
    viberesp_data: List[Dict],
    hornresp_data: List[Dict],
    value_key: str
) -> tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """
    Interpolate Hornresp data to viberesp frequency points.

    Args:
        viberesp_data: Viberesp simulation results
        hornresp_data: Hornresp simulation results
        value_key: Key to interpolate (e.g., 'Ze_magnitude_ohm')

    Returns:
        (frequencies, viberesp_values, hornresp_values)
    """
    # Extract Hornresp frequencies and values
    hr_freqs = np.array([float(row['frequency_hz']) for row in hornresp_data])
    hr_values = np.array([float(row[value_key]) for row in hornresp_data])

    # Extract viberesp frequencies and values
    vb_freqs = np.array([float(row['frequency_hz']) for row in viberesp_data])
    vb_values = np.array([float(row[value_key]) for row in viberesp_data])

    # Interpolate Hornresp to viberesp frequencies
    hr_interpolated = np.interp(vb_freqs, hr_freqs, hr_values)

    return vb_freqs, vb_values, hr_interpolated


def calculate_statistics(
    viberesp_values: np.ndarray,
    hornresp_values: np.ndarray,
    name: str = ""
) -> Dict:
    """Calculate comparison statistics between viberesp and Hornresp."""
    # Remove NaN values
    mask = ~(np.isnan(viberesp_values) | np.isnan(hornresp_values))
    vb_clean = viberesp_values[mask]
    hr_clean = hornresp_values[mask]

    if len(vb_clean) == 0:
        return {}

    # Calculate differences
    abs_diff = np.abs(vb_clean - hr_clean)
    rel_diff = np.abs((vb_clean - hr_clean) / hr_clean) * 100  # Percentage

    stats = {
        'name': name,
        'n_points': len(vb_clean),
        'max_abs_diff': np.max(abs_diff),
        'mean_abs_diff': np.mean(abs_diff),
        'max_rel_diff': np.max(rel_diff),
        'mean_rel_diff': np.mean(rel_diff),
        'rmse': np.sqrt(np.mean((vb_clean - hr_clean)**2)),
    }

    return stats


def plot_impedance_comparison(
    driver_name: str,
    viberesp_data: List[Dict],
    hornresp_data: Optional[List[Dict]] = None,
    output_dir: Path = Path("validation_cases/ported_box")
):
    """Plot impedance comparison (magnitude and phase)."""

    # Extract viberesp data
    vb_freqs = np.array([float(row['frequency_hz']) for row in viberesp_data])
    vb_z_mag = np.array([float(row['Ze_magnitude_ohm']) for row in viberesp_data])
    vb_z_phase = np.array([float(row['Ze_phase_deg']) for row in viberesp_data])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Plot impedance magnitude
    ax1.semilogx(vb_freqs, vb_z_mag, 'b-', linewidth=2, label='viberesp')
    ax1.axhline(y=2.6, color='gray', linestyle='--', alpha=0.5, label='Re')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('|Ze| (Ω)')
    ax1.set_title(f'{driver_name} Ported Box - Electrical Impedance Magnitude')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # Plot impedance phase
    ax2.semilogx(vb_freqs, vb_z_phase, 'b-', linewidth=2, label='viberesp')
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (degrees)')
    ax2.set_title(f'{driver_name} Ported Box - Electrical Impedance Phase')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()

    # Save plot
    output_file = output_dir / f"{driver_name}_ported_B4_impedance_comparison.png"
    plt.savefig(output_file, dpi=150)
    print(f"  Saved: {output_file}")

    # Calculate statistics if Hornresp data available
    if hornresp_data:
        freqs, vb_mag, hr_mag = interpolate_hornresp_to_viberesp_freqs(
            viberesp_data, hornresp_data, 'Ze_magnitude_ohm'
        )
        _, vb_phase, hr_phase = interpolate_hornresp_to_viberesp_freqs(
            viberesp_data, hornresp_data, 'Ze_phase_deg'
        )

        stats_mag = calculate_statistics(vb_mag, hr_mag, "Impedance Magnitude")
        stats_phase = calculate_statistics(vb_phase, hr_phase, "Impedance Phase")

        return stats_mag, stats_phase

    return None, None


def plot_spl_comparison(
    driver_name: str,
    viberesp_data: List[Dict],
    hornresp_data: Optional[List[Dict]] = None,
    output_dir: Path = Path("validation_cases/ported_box")
):
    """Plot SPL comparison."""

    # Extract viberesp data
    vb_freqs = np.array([float(row['frequency_hz']) for row in viberesp_data])
    vb_spl = np.array([float(row['SPL_db']) for row in viberesp_data])

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    ax.semilogx(vb_freqs, vb_spl, 'b-', linewidth=2, label='viberesp')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('SPL (dB @ 1m, 2.83V)')
    ax.set_title(f'{driver_name} Ported Box - Frequency Response')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()

    # Save plot
    output_file = output_dir / f"{driver_name}_ported_B4_spl_comparison.png"
    plt.savefig(output_file, dpi=150)
    print(f"  Saved: {output_file}")

    # Calculate statistics if Hornresp data available
    if hornresp_data:
        freqs, vb_spl, hr_spl = interpolate_hornresp_to_viberesp_freqs(
            viberesp_data, hornresp_data, 'SPL_db'
        )

        stats = calculate_statistics(vb_spl, hr_spl, "SPL")

        return stats

    return None


def main():
    """Main comparison workflow."""

    output_dir = Path("validation_cases/ported_box")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Drivers to compare
    drivers = ["BC_8NDL51", "BC_12NDL76", "BC_15DS115", "BC_15PS100", "BC_18PZW100"]

    print("="*60)
    print("PORTED BOX VALIDATION COMPARISON")
    print("="*60)

    all_stats = []

    for driver_name in drivers:
        print(f"\n{driver_name}:")

        # Read viberesp data
        vb_file = output_dir / f"{driver_name}_ported_B4_viberesp.csv"
        if not vb_file.exists():
            print(f"  WARNING: viberesp file not found: {vb_file}")
            continue

        viberesp_data = read_csv(str(vb_file))

        # Check for Hornresp data (optional)
        hr_file = output_dir / f"{driver_name}_ported_B4_hornresp.csv"
        hornresp_data = None
        if hr_file.exists():
            hornresp_data = read_csv(str(hr_file))
            print(f"  Found Hornresp data")
        else:
            print(f"  No Hornresp data (expected if not yet exported)")

        # Plot impedance
        stats_mag, stats_phase = plot_impedance_comparison(
            driver_name, viberesp_data, hornresp_data, output_dir
        )

        # Plot SPL
        stats_spl = plot_spl_comparison(
            driver_name, viberesp_data, hornresp_data, output_dir
        )

        # Collect statistics
        if hornresp_data and stats_mag and stats_spl:
            all_stats.append({
                'driver': driver_name,
                'impedance_mag': stats_mag,
                'impedance_phase': stats_phase,
                'spl': stats_spl,
            })

            print(f"\n  Comparison Statistics:")
            print(f"    Impedance Magnitude:")
            print(f"      Max difference: {stats_mag['max_abs_diff']:.2f} Ω")
            print(f"      Mean difference: {stats_mag['mean_abs_diff']:.2f} Ω")
            print(f"      Max relative: {stats_mag['max_rel_diff']:.1f}%")
            print(f"    SPL:")
            print(f"      Max difference: {stats_spl['max_abs_diff']:.2f} dB")
            print(f"      Mean difference: {stats_spl['mean_abs_diff']:.2f} dB")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Generated plots for {len(drivers)} driver(s)")
    print(f"\nPlots saved to: {output_dir}")

    if all_stats:
        print(f"\nOverall Statistics:")
        for stats in all_stats:
            print(f"\n  {stats['driver']}:")
            print(f"    Impedance: {stats['impedance_mag']['mean_rel_diff']:.1f}% mean deviation")
            print(f"    SPL: {stats['spl']['mean_abs_diff']:.2f} dB mean deviation")


if __name__ == "__main__":
    main()
