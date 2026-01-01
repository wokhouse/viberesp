#!/usr/bin/env python3
"""
Plot SPL response for optimized mixed-profile horn design.

Usage:
    PYTHONPATH=src python tasks/plot_optimized_horn.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    decode_mixed_profile_design,
    build_mixed_profile_horn,
)
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def plot_horn_response():
    """Plot SPL response for the optimized horn design."""

    # Optimized design from optimization
    # [throat_area, middle_area, mouth_area, length1, length2,
    #  profile_type1, profile_type2, T1, T2, V_tc, V_rc]
    design = np.array([
        7.50e-4,    # throat_area (m²) - 7.5 cm²
        0.02963,    # middle_area (m²) - 296.3 cm²
        0.05102,    # mouth_area (m²) - 510.2 cm²
        0.46,       # length1 (m)
        0.26,       # length2 (m)
        1,          # profile_type1 (conical)
        1,          # profile_type2 (conical)
        1.0, 1.0,   # T1, T2 (not used for conical)
        0.0, 0.0,   # V_tc, V_rc
    ])

    # Load driver
    driver = load_driver("BC_DE250")

    # Decode design
    params = decode_mixed_profile_design(design, driver, num_segments=2)

    print("="*70)
    print("Optimized Horn Design Parameters")
    print("="*70)
    print(f"Driver: BC_DE250")
    print(f"Throat area: {params['throat_area']*10000:.2f} cm²")
    print(f"Middle area: {params['segments'][0][1]*10000:.2f} cm²")
    print(f"Mouth area: {params['mouth_area']*10000:.2f} cm²")
    print(f"Segment 1: {params['segment_classes'][0]}, L={params['segments'][0][2]:.2f} m")
    print(f"Segment 2: {params['segment_classes'][1]}, L={params['segments'][1][2]:.2f} m")
    print(f"Total length: {params['total_length']:.2f} m")
    print(f"Profile types: {params['profile_types']}")
    print("="*70)
    print()

    # Build horn
    horn, V_tc, V_rc = build_mixed_profile_horn(design, driver, num_segments=2)

    # Create front-loaded horn system
    flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

    # Calculate frequency response
    # Use log-spaced frequencies from 20 Hz to 20 kHz
    frequencies = np.logspace(np.log10(20), np.log10(20000), 200)

    print("Calculating SPL response...")
    spl_db = []

    for freq in frequencies:
        spl = flh.spl_response(freq, voltage=2.83)
        spl_db.append(spl)

    spl_db = np.array(spl_db)

    # Calculate flatness metrics
    # Target band: 1kHz - 17kHz
    target_mask = (frequencies >= 1000) & (frequencies <= 17000)
    spl_target = spl_db[target_mask]

    flatness_rms = np.std(spl_target)
    flatness_peak_to_peak = spl_target.max() - spl_target.min()

    print("="*70)
    print("SPL Response Metrics")
    print("="*70)
    print(f"SPL at 100 Hz: {spl_db[np.argmin(np.abs(frequencies-100))]:.2f} dB")
    print(f"SPL at 1 kHz:  {spl_db[np.argmin(np.abs(frequencies-1000))]:.2f} dB")
    print(f"SPL at 10 kHz: {spl_db[np.argmin(np.abs(frequencies-10000))]:.2f} dB")
    print(f"SPL at 17 kHz: {spl_db[np.argmin(np.abs(frequencies-17000))]:.2f} dB")
    print()
    print(f"Target band (1-17 kHz):")
    print(f"  Min SPL: {spl_target.min():.2f} dB at {frequencies[target_mask][np.argmin(spl_target)]:.0f} Hz")
    print(f"  Max SPL: {spl_target.max():.2f} dB at {frequencies[target_mask][np.argmax(spl_target)]:.0f} Hz")
    print(f"  Peak-to-peak: {flatness_peak_to_peak:.2f} dB")
    print(f"  RMS deviation: {flatness_rms:.2f} dB")
    print(f"  Mean SPL: {spl_target.mean():.2f} dB")
    print("="*70)
    print()

    # Create figure
    fig, ax1 = plt.subplots(1, 1, figsize=(12, 8))

    # Plot 1: SPL response
    ax1.semilogx(frequencies, spl_db, 'b-', linewidth=2, label='SPL Response')

    # Mark target band
    ax1.axvspan(1000, 17000, alpha=0.2, color='green', label='Target Band (1-17 kHz)')

    # Mark ±3 dB from mean
    mean_spl = spl_target.mean()
    ax1.axhline(mean_spl, color='r', linestyle='--', alpha=0.7, label=f'Mean: {mean_spl:.2f} dB')
    ax1.axhline(mean_spl + 3, color='orange', linestyle=':', alpha=0.5, label='±3 dB')
    ax1.axhline(mean_spl - 3, color='orange', linestyle=':', alpha=0.5)

    ax1.set_xlabel('Frequency (Hz)', fontsize=12)
    ax1.set_ylabel('SPL (dB) @ 2.83V, 1m', fontsize=12)
    ax1.set_title('Optimized Mixed-Profile Horn SPL Response\nBC_DE250, Conical-Conical Horn', fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best', fontsize=10)
    ax1.set_xlim([20, 20000])

    # Add text box with metrics
    textstr = f'Horn Geometry:\n'
    textstr += f"Throat: {params['throat_area']*10000:.1f} cm²\n"
    textstr += f"Middle: {params['segments'][0][1]*10000:.1f} cm²\n"
    textstr += f"Mouth: {params['mouth_area']*10000:.1f} cm²\n"
    textstr += f"Length: {params['total_length']:.2f} m\n\n"
    textstr += f'Target Band (1-17 kHz):\n'
    textstr += f"Flatness (RMS): {flatness_rms:.2f} dB\n"
    textstr += f"Peak-to-peak: {flatness_peak_to_peak:.2f} dB"

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.02, 0.98, textstr, transform=ax1.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)

    plt.tight_layout()

    # Save plot
    output_path = Path(__file__).parent / "optimized_horn_response.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")

    # Also show the plot
    plt.show()


if __name__ == "__main__":
    plot_horn_response()
