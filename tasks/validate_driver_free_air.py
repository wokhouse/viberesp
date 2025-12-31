#!/usr/bin/env python3
"""
Validate BC_DE250 driver parameters against datasheet WITHOUT horn loading.

Check:
1. Fs = 700 Hz (main impedance peak)
2. Second impedance peak ~1.8 kHz (if visible)
3. Flat response through 19 kHz
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver import load_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def plot_electrical_impedance():
    """Plot electrical impedance without horn loading."""
    driver = load_driver('BC_DE250')

    # Frequency range for impedance plot
    frequencies = np.logspace(np.log10(20), np.log10(20000), 500)

    # Create a very short "dummy" horn to approximate free-air behavior
    # Throat = Mouth = S_d, Length = very small
    dummy_horn = ExponentialHorn(
        throat_area=driver.S_d,
        mouth_area=driver.S_d,
        length=0.001  # 1mm, essentially no horn
    )
    flh = FrontLoadedHorn(driver, dummy_horn, V_tc=0, V_rc=0)

    impedances = []
    for f in frequencies:
        z_dict = flh.electrical_impedance(f)
        impedances.append(z_dict['Ze_magnitude'])

    impedances = np.array(impedances)

    # Find peaks
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(impedances, height=driver.R_e * 2, distance=10)

    print("="*70)
    print("BC_DE250 Electrical Impedance (No Horn Loading)")
    print("="*70)
    print(f"Driver parameters:")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Qts: {driver.Q_ts:.3f}")
    print(f"  Re: {driver.R_e:.2f} Ω")
    print(f"  Le: {driver.L_e*1000:.3f} mH")
    print()
    print(f"Impedance peaks found:")
    for i, peak_idx in enumerate(peaks[:5]):  # Show first 5 peaks
        freq_peak = frequencies[peak_idx]
        z_peak = impedances[peak_idx]
        print(f"  Peak {i+1}: {z_peak:.1f} Ω at {freq_peak:.0f} Hz")
    print()

    # Check against datasheet specs
    print("Datasheet specifications:")
    print("  Peak 1: ~700 Hz at ~100 Ω")
    print("  Peak 2: ~1.8 kHz (cavity resonance)")
    print()

    # Find peak near 700 Hz
    near_700 = peaks[(np.abs(frequencies[peaks] - 700) < 200)]
    if len(near_700) > 0:
        peak_700_idx = near_700[0]
        z_700 = impedances[peak_700_idx]
        f_700 = frequencies[peak_700_idx]
        print(f"Our model peak near 700 Hz:")
        print(f"  {z_700:.1f} Ω at {f_700:.0f} Hz")
        if abs(f_700 - 700) < 100:
            print("  ✓ Frequency is close to datasheet!")
        if 50 < z_700 < 150:
            print("  ✓ Impedance magnitude is reasonable!")
        print()
    else:
        print("  ❌ No peak found near 700 Hz!")

    # Find peak near 1.8 kHz
    near_1800 = peaks[(np.abs(frequencies[peaks] - 1800) < 300)]
    if len(near_1800) > 0:
        peak_1800_idx = near_1800[0]
        z_1800 = impedances[peak_1800_idx]
        f_1800 = frequencies[peak_1800_idx]
        print(f"Our model peak near 1.8 kHz:")
        print(f"  {z_1800:.1f} Ω at {f_1800:.0f} Hz")
        print()
    else:
        print("  No peak found near 1.8 kHz (expected - simple T/S model can't capture cavity resonance)")

    print("="*70)
    print()

    # Plot impedance
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    ax.semilogx(frequencies, impedances, 'b-', linewidth=2, label='Electrical Impedance')
    ax.axhline(driver.R_e, color='r', linestyle='--', alpha=0.5, label=f'Re = {driver.R_e:.1f} Ω')
    ax.axvline(700, color='g', linestyle=':', alpha=0.5, label='Datasheet peak 1 (700 Hz)')
    ax.axvline(1800, color='orange', linestyle=':', alpha=0.5, label='Datasheet peak 2 (1.8 kHz)')

    # Mark peaks
    ax.plot(frequencies[peaks], impedances[peaks], 'ro', label='Peaks')

    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('Impedance (Ω)', fontsize=12)
    ax.set_title('BC_DE250 Electrical Impedance (Infinite Baffle, No Horn)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    ax.set_xlim([20, 20000])

    plt.tight_layout()

    output_path = Path(__file__).parent / "bc_de250_impedance_validation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Impedance plot saved to: {output_path}")
    print()

    return frequencies, impedances


def plot_free_air_spl():
    """Plot SPL response without horn (approximated)."""
    driver = load_driver('BC_DE250')

    # Calculate SPL with dummy "horn" (essentially free air)
    frequencies = np.logspace(np.log10(100), np.log10(20000), 200)

    dummy_horn = ExponentialHorn(
        throat_area=driver.S_d,
        mouth_area=driver.S_d,
        length=0.001,
    )
    flh = FrontLoadedHorn(driver, dummy_horn, V_tc=0, V_rc=0)

    spl_db = []

    for f in frequencies:
        spl = flh.spl_response(f, voltage=2.83)
        spl_db.append(spl)

    spl_db = np.array(spl_db)

    print("="*70)
    print("BC_DE250 SPL Response (Approximated Free Air)")
    print("="*70)
    print(f"SPL at key frequencies:")
    for f_test in [100, 500, 700, 1000, 1800, 5000, 10000, 19000]:
        idx = np.argmin(np.abs(frequencies - f_test))
        print(f"  {f_test:5d} Hz: {spl_db[idx]:.2f} dB")
    print()

    # Calculate flatness in different bands
    # High frequency band (where datasheet says response is flat)
    hf_mask = frequencies >= 1000
    spl_hf = spl_db[hf_mask]
    flatness_hf = spl_hf.max() - spl_hf.min()
    print(f"Flatness above 1 kHz:")
    print(f"  Peak-to-peak: {flatness_hf:.2f} dB")
    print(f"  Range: {spl_hf.min():.2f} - {spl_hf.max():.2f} dB")
    print()

    print("Datasheet claims: 'Flat response through 19 kHz'")
    if flatness_hf < 10:
        print("  ✓ Our model shows reasonably flat response!")
    else:
        print(f"  Note: Our model shows {flatness_hf:.2f} dB variation")
    print("="*70)
    print()

    # Plot SPL
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    ax.semilogx(frequencies, spl_db, 'b-', linewidth=2, label='SPL Response')
    ax.axvspan(1000, 19000, alpha=0.2, color='green', label='Datasheet flat region (1-19 kHz)')
    ax.axvline(700, color='g', linestyle=':', alpha=0.5, label='Fs = 700 Hz')
    ax.axvline(1800, color='orange', linestyle=':', alpha=0.5, label='Cavity resonance ~1.8 kHz')

    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('SPL (dB) @ 2.83V, 1m', fontsize=12)
    ax.set_title('BC_DE250 SPL Response (Approximated Free Air)', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=10)
    ax.set_xlim([100, 20000])

    plt.tight_layout()

    output_path = Path(__file__).parent / "bc_de250_spl_validation.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"SPL plot saved to: {output_path}")


if __name__ == "__main__":
    # Check electrical impedance
    plot_electrical_impedance()

    # Check free-air SPL
    plot_free_air_spl()
