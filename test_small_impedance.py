#!/usr/bin/env python3
"""
Test Small's transfer function implementation for ported box impedance.

This script tests the new implementation against BC_8NDL51 driver parameters
to verify that dual impedance peaks are correctly produced.

Literature:
- Small (1973) - Vented-box systems, dual impedance peaks
- Thiele (1971) - Loudspeakers in Vented Boxes
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

# Add src to path for imports
sys.path.insert(0, 'src')

from viberesp.driver.bc_drivers import get_bc_8ndl51
from viberesp.enclosure.ported_box import (
    ported_box_electrical_impedance,
    calculate_ported_box_system_parameters,
    calculate_optimal_port_dimensions,
)


def test_dual_peaks():
    """Test that Small's transfer function produces dual impedance peaks."""

    print("="*60)
    print("Testing Small's Transfer Function - Ported Box Impedance")
    print("="*60)

    # Get BC_8NDL51 driver
    driver = get_bc_8ndl51()
    print(f"\nDriver: BC_8NDL51")
    print(f"  Fs = {driver.F_s:.1f} Hz")
    print(f"  Qts = {driver.Q_ts:.2f}")
    print(f"  Vas = {driver.V_as*1000:.1f} L")
    print(f"  Re = {driver.R_e:.1f} Ohms")

    # Design B4 alignment
    # For B4: Vb = Vas, Fb = Fs (approximately)
    Vb = driver.V_as  # B4 alignment
    Fb = driver.F_s   # B4 alignment

    # Calculate optimal port dimensions
    port_area, port_length, v_max = calculate_optimal_port_dimensions(
        driver, Vb, Fb
    )

    print(f"\nBox Design (B4 Alignment):")
    print(f"  Vb = {Vb*1000:.1f} L")
    print(f"  Fb = {Fb:.1f} Hz")
    print(f"  Port area = {port_area*10000:.1f} cm²")
    print(f"  Port length = {port_length*100:.1f} cm")

    # Calculate system parameters
    params = calculate_ported_box_system_parameters(
        driver, Vb, Fb, port_area, port_length
    )

    print(f"\nSystem Parameters:")
    print(f"  alpha = {params.alpha:.2f}")
    print(f"  h = {params.h:.2f}")

    # Test Small's model
    print(f"\n{'='*60}")
    print("Testing Small's Transfer Function Model")
    print(f"{'='*60}")

    # Frequency sweep: 20 Hz to 200 Hz
    frequencies = np.logspace(np.log10(20), np.log10(200), 200)

    # Calculate impedance using Small's model
    impedances_small = []
    for freq in frequencies:
        result = ported_box_electrical_impedance(
            freq,
            driver,
            Vb,
            Fb,
            port_area,
            port_length,
            impedance_model="small",  # Use Small's transfer function
            voice_coil_model="simple",
        )
        impedances_small.append(result['Ze_magnitude'])

    impedances_small = np.array(impedances_small)

    # Find peaks and dip
    # Peak 1: Lower frequency peak (driver resonance)
    # Dip: At Fb (anti-resonance)
    # Peak 2: Higher frequency peak (Helmholtz resonance)

    # Find local maxima (peaks)
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(impedances_small, height=driver.R_e * 1.5, distance=10)

    # Find local minima (dips)
    from scipy.signal import find_peaks
    dips, _ = find_peaks(-impedances_small, distance=10)

    print(f"\nImpedance Analysis:")
    print(f"  Re = {driver.R_e:.1f} Ohms")
    print(f"  Max impedance = {np.max(impedances_small):.1f} Ohms")

    if len(peaks) >= 2:
        f_peak1 = frequencies[peaks[0]]
        z_peak1 = impedances_small[peaks[0]]
        f_peak2 = frequencies[peaks[1]]
        z_peak2 = impedances_small[peaks[1]]

        print(f"\n  Dual Peaks Found:")
        print(f"    Peak 1: f = {f_peak1:.1f} Hz, Z = {z_peak1:.1f} Ohms")
        print(f"    Peak 2: f = {f_peak2:.1f} Hz, Z = {z_peak2:.1f} Ohms")

        # Check against expected values
        # F_low ≈ Fb/√2, F_high ≈ Fb×√2
        f_low_expected = Fb / np.sqrt(2)
        f_high_expected = Fb * np.sqrt(2)

        print(f"\n  Expected (approximate):")
        print(f"    F_low ≈ {f_low_expected:.1f} Hz (Fb/√2)")
        print(f"    F_high ≈ {f_high_expected:.1f} Hz (Fb×√2)")

        # Validate
        freq_error_low = abs(f_peak1 - f_low_expected) / f_low_expected * 100
        freq_error_high = abs(f_peak2 - f_high_expected) / f_high_expected * 100

        print(f"\n  Validation:")
        print(f"    Peak 1 frequency error: {freq_error_low:.1f}%")
        print(f"    Peak 2 frequency error: {freq_error_high:.1f}%")

        if freq_error_low < 15 and freq_error_high < 15:
            print(f"    ✓ PASS: Both peaks within 15% of expected")
        else:
            print(f"    ✗ FAIL: Peaks outside expected range")

    else:
        print(f"\n  ✗ FAIL: Found {len(peaks)} peak(s), expected 2")
        if len(peaks) > 0:
            for i, peak_idx in enumerate(peaks):
                print(f"    Peak {i+1}: f = {frequencies[peak_idx]:.1f} Hz, Z = {impedances_small[peak_idx]:.1f} Ohms")

    if len(dips) >= 1:
        f_dip = frequencies[dips[0]]
        z_dip = impedances_small[dips[0]]

        print(f"\n  Impedance Dip:")
        print(f"    Dip: f = {f_dip:.1f} Hz, Z = {z_dip:.1f} Ohms")
        print(f"    Expected at Fb = {Fb:.1f} Hz")

        dip_error = abs(f_dip - Fb) / Fb * 100
        print(f"    Dip frequency error: {dip_error:.1f}%")

        # Check if dip is close to Re
        z_above_re = (z_dip - driver.R_e) / driver.R_e * 100
        print(f"    Dip is {z_above_re:.1f}% above Re")

        if dip_error < 10:
            print(f"    ✓ PASS: Dip frequency within 10% of Fb")
        else:
            print(f"    ✗ FAIL: Dip frequency not at Fb")

    # Plot impedance
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogx(frequencies, impedances_small, 'b-', linewidth=2, label="Small's Model")
    ax.axhline(y=driver.R_e, color='gray', linestyle='--', alpha=0.5, label='Re')
    ax.axvline(x=Fb, color='red', linestyle=':', alpha=0.5, label='Fb')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Electrical Impedance (Ω)')
    ax.set_title(f"BC_8NDL51 Ported Box - Impedance (Small's Transfer Function)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig('test_small_impedance.png', dpi=150)
    print(f"\nPlot saved: test_small_impedance.png")

    print(f"\n{'='*60}")
    print("Test Complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_dual_peaks()
