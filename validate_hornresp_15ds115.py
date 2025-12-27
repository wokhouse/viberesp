#!/usr/bin/env python3
"""
Validate viberesp against Hornresp simulation results for BC_15DS115 ported box.

This script loads Hornresp export data and compares it with viberesp's
ported box simulation.
"""

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver.bc_drivers import get_bc_15ds115
from viberesp.enclosure.ported_box import ported_box_electrical_impedance


def load_hornresp_data(filename):
    """Load Hornresp export data from tab-separated file."""
    # Load data, skip header row and empty rows
    data = np.loadtxt(filename, delimiter='\t', skiprows=1)

    # Filter out rows with NaN (if any)
    valid_mask = ~np.isnan(data).all(axis=1)
    data = data[valid_mask]

    return {
        'frequency': data[:, 0],      # Freq (hertz)
        'Ra': data[:, 1],                # Ra (norm)
        'Xa': data[:, 2],                # Xa (norm)
        'Za': data[:, 3],                # Za (norm)
        'SPL': data[:, 4],               # SPL (dB)
        'Ze': data[:, 5],                # Ze (ohms)
        'Xd': data[:, 6],                # Xd (mm)
        'WPhase': data[:, 7],            # WPhase (deg)
        'UPhase': data[:, 8],            # UPhase (deg)
        'CPhase': data[:, 9],            # CPhase (deg)
        'Delay': data[:, 10],            # Delay (msec)
        'Efficiency': data[:, 11],      # Efficiency (%)
        'Ein': data[:, 12],              # Ein (volts)
        'Pin': data[:, 13],              # Pin (watts)
        'Iin': data[:, 14],              # Iin (amps)
        'ZePhase': data[:, 15],          # ZePhase (deg)
    }


def calculate_viberesp_response(driver, Vb, Fb, port_area, port_length, frequencies):
    """Calculate viberesp response across frequency range."""
    ze_magnitude = []
    ze_phase = []
    spl = []

    for freq in frequencies:
        result = ported_box_electrical_impedance(
            frequency=freq,
            driver=driver,
            Vb=Vb,
            Fb=Fb,
            port_area=port_area,
            port_length=port_length,
            voltage=2.83,
            measurement_distance=1.0,
            impedance_model="small"
        )
        ze_magnitude.append(result['Ze_magnitude'])
        ze_phase.append(result['Ze_phase'])
        spl.append(result['SPL'])

    return {
        'Ze_magnitude': np.array(ze_magnitude),
        'Ze_phase': np.array(ze_phase),
        'SPL': np.array(spl)
    }


def find_f3(frequencies, spl, reference_spl=None):
    """Find F3 (-3dB cutoff frequency) from SPL response."""
    if reference_spl is None:
        # Use maximum SPL in passband as reference
        reference_spl = np.max(spl[frequencies > 50])  # Above 50Hz

    # Find where SPL drops 3dB from reference
    target = reference_spl - 3.0

    # Find first frequency where SPL < target
    for i in range(len(frequencies)):
        if spl[i] < target:
            # Interpolate for more accurate F3
            if i > 0:
                f1, f2 = frequencies[i-1], frequencies[i]
                spl1, spl2 = spl[i-1], spl[i]
                # Linear interpolation
                if spl2 != spl1:
                    f3 = f1 + (f2 - f1) * (target - spl1) / (spl2 - spl1)
                else:
                    f3 = f1
                return f3
            return frequencies[i]

    return None


def main():
    # Load Hornresp data
    print("Loading Hornresp simulation data...")
    hornresp = load_hornresp_data('imports/15ds115_sim.txt')

    # Extract design parameters from Hornresp file name or metadata
    # These should match our optimized design: Vb=126.9L, Fb=23Hz
    Vb = 0.1269  # m³
    Fb = 23.0    # Hz
    port_area = 0.017831  # m² (from Hornresp: Ap = 178.31 cm²)
    port_length = 0.7278  # m (from Hornresp: Lpt = 72.78 cm)

    print(f"\nDesign parameters:")
    print(f"  Vb: {Vb * 1000:.1f} L")
    print(f"  Fb: {Fb:.1f} Hz")
    print(f"  Port area: {port_area * 10000:.1f} cm²")
    print(f"  Port length: {port_length * 100:.1f} cm")

    # Load driver
    driver = get_bc_15ds115()
    print(f"\nDriver parameters:")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Qts: {driver.Q_ts:.3f}")
    print(f"  Vas: {driver.V_as * 1000:.1f} L")
    print(f"  Sd: {driver.S_d * 10000:.0f} cm²")
    print(f"  BL: {driver.BL} T·m")

    # Calculate viberesp response
    print("\nCalculating viberesp response...")
    frequencies = hornresp['frequency']
    viberesp = calculate_viberesp_response(
        driver, Vb, Fb, port_area, port_length, frequencies
    )

    # Find F3 for both
    f3_hornresp = find_f3(frequencies, hornresp['SPL'])
    f3_viberesp = find_f3(frequencies, viberesp['SPL'])

    print(f"\nF3 comparison:")
    print(f"  Hornresp F3: {f3_hornresp:.1f} Hz" if f3_hornresp else "  Hornresp F3: Not found")
    print(f"  Viberesp F3: {f3_viberesp:.1f} Hz" if f3_viberesp else "  Viberesp F3: Not found")
    if f3_hornresp and f3_viberesp:
        diff = abs(f3_hornresp - f3_viberesp)
        pct_error = (diff / f3_hornresp) * 100
        print(f"  Difference: {diff:.1f} Hz ({pct_error:.1f}%)")

    # Calculate impedance statistics
    ze_diff = hornresp['Ze'] - viberesp['Ze_magnitude']
    ze_pct_error = (ze_diff / hornresp['Ze']) * 100

    print(f"\nElectrical impedance comparison:")
    print(f"  Mean absolute error: {np.mean(np.abs(ze_diff)):.2f} Ω")
    print(f"  Mean percentage error: {np.mean(np.abs(ze_pct_error)):.1f}%")
    print(f"  Max absolute error: {np.max(np.abs(ze_diff)):.2f} Ω")

    # Find impedance peaks
    from scipy.signal import find_peaks

    peaks_hr, _ = find_peaks(hornresp['Ze'], height=20, distance=10)
    peaks_vb, _ = find_peaks(viberesp['Ze_magnitude'], height=20, distance=10)

    print(f"\n  Hornresp impedance peaks:")
    for i, p in enumerate(peaks_hr[:3]):
        print(f"    Peak {i+1}: {hornresp['Ze'][p]:.1f} Ω at {frequencies[p]:.1f} Hz")

    print(f"\n  Viberesp impedance peaks:")
    for i, p in enumerate(peaks_vb[:3]):
        print(f"    Peak {i+1}: {viberesp['Ze_magnitude'][p]:.1f} Ω at {frequencies[p]:.1f} Hz")

    # SPL comparison
    spl_diff = hornresp['SPL'] - viberesp['SPL']

    print(f"\nSPL comparison:")
    print(f"  Mean absolute error: {np.mean(np.abs(spl_diff)):.2f} dB")
    print(f"  Max absolute error: {np.max(np.abs(spl_diff)):.2f} dB")

    # Create comparison plots
    print("\nGenerating comparison plots...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Electrical impedance magnitude
    ax1 = axes[0, 0]
    ax1.plot(frequencies, hornresp['Ze'], 'b-', linewidth=2, label='Hornresp', alpha=0.7)
    ax1.plot(frequencies, viberesp['Ze_magnitude'], 'r--', linewidth=2, label='Viberesp', alpha=0.7)
    ax1.set_xlabel('Frequency (Hz)', fontsize=11)
    ax1.set_ylabel('Impedance (Ω)', fontsize=11)
    ax1.set_title('Electrical Impedance Magnitude', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_xlim(10, 20000)

    # Plot 2: Electrical impedance phase
    ax2 = axes[0, 1]
    ax2.plot(frequencies, hornresp['ZePhase'], 'b-', linewidth=2, label='Hornresp', alpha=0.7)
    ax2.plot(frequencies, viberesp['Ze_phase'], 'r--', linewidth=2, label='Viberesp', alpha=0.7)
    ax2.set_xlabel('Frequency (Hz)', fontsize=11)
    ax2.set_ylabel('Phase (degrees)', fontsize=11)
    ax2.set_title('Electrical Impedance Phase', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_xlim(10, 20000)

    # Plot 3: SPL response
    ax3 = axes[1, 0]
    ax3.plot(frequencies, hornresp['SPL'], 'b-', linewidth=2, label='Hornresp', alpha=0.7)
    ax3.plot(frequencies, viberesp['SPL'], 'r--', linewidth=2, label='Viberesp', alpha=0.7)
    ax3.axhline(y=np.max(hornresp['SPL']) - 3, color='green', linestyle=':',
               alpha=0.5, label='-3dB reference')
    ax3.set_xlabel('Frequency (Hz)', fontsize=11)
    ax3.set_ylabel('SPL (dB @ 1m, 2.83V)', fontsize=11)
    ax3.set_title('SPL Response', fontsize=12, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log')
    ax3.set_xlim(10, 20000)

    # Plot 4: Impedance error
    ax4 = axes[1, 1]
    ax4.plot(frequencies, ze_pct_error, 'purple', linewidth=1.5, alpha=0.7)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax4.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='±5%')
    ax4.axhline(y=-5, color='green', linestyle='--', alpha=0.5)
    ax4.set_xlabel('Frequency (Hz)', fontsize=11)
    ax4.set_ylabel('Percentage Error (%)', fontsize=11)
    ax4.set_title('Viberesp vs Hornresp: Impedance Error', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_xscale('log')
    ax4.set_xlim(10, 20000)
    ax4.legend()

    plt.tight_layout()
    plt.savefig('15ds115_validation_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved plot: 15ds115_validation_comparison.png")

    # Summary statistics
    print("\n" + "="*70)
    print("  VALIDATION SUMMARY")
    print("="*70)

    # Low frequency range (10-100 Hz) - most critical for ported design
    low_freq_mask = frequencies <= 100
    ze_error_low = np.abs(ze_pct_error[low_freq_mask])
    spl_error_low = np.abs(spl_diff[low_freq_mask])

    print(f"\nLow frequency range (10-100 Hz):")
    print(f"  Impedance error: {np.mean(ze_error_low):.1f}% (mean), {np.max(ze_error_low):.1f}% (max)")
    print(f"  SPL error: {np.mean(spl_error_low):.2f} dB (mean), {np.max(spl_error_low):.2f} dB (max)")

    # Overall assessment
    print(f"\nOverall assessment:")
    if np.mean(ze_error_low) < 5 and np.mean(spl_error_low) < 3:
        print("  ✓ GOOD: Viberesp matches Hornresp within acceptable tolerances")
    elif np.mean(ze_error_low) < 10 and np.mean(spl_error_low) < 6:
        print("  ⚠ FAIR: Viberesp is reasonably close but has some deviations")
    else:
        print("  ✗ POOR: Significant differences between Viberesp and Hornresp")

    print(f"\n  F3 cutoff: {f3_hornresp:.1f} Hz (Hornresp) vs {f3_viberesp:.1f} Hz (Viberesp)")


if __name__ == "__main__":
    main()
