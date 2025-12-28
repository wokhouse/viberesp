"""
Horn Theory Validation - Test Case 1 (Exponential Midrange Horn)

Compares viberesp exponential horn throat impedance with Hornresp reference data.

Validation data location:
  tests/validation/horn_theory/exp_midrange_tc1/

Usage:
    cd tests/validation/horn_theory/exp_midrange_tc1
    python validate.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from viberesp.simulation import ExponentialHorn, exponential_horn_throat_impedance
from viberesp.hornresp.results_parser import load_hornresp_sim_file


def calculate_viberesp_throat_impedance():
    """Calculate throat impedance using viberesp horn theory.

    Returns:
        frequencies: Array of frequencies (Hz)
        z_throat: Complex throat impedance (Pa·s/m³)
    """
    # Horn geometry (from metadata.json)
    horn = ExponentialHorn(
        throat_area=0.005,   # 50 cm²
        mouth_area=0.05,     # 500 cm²
        length=0.3           # 30 cm
    )

    # Frequency range: 10 Hz to 20 kHz (logarithmic spacing)
    # Hornresp data goes from ~12 Hz to 20000 Hz
    # Use more points for better interpolation accuracy
    frequencies = np.logspace(1, 4.31, 500)  # 10^1 to 10^4.31 ≈ 20.4 kHz (slightly above Hornresp max)

    # Calculate throat impedance (half-space radiation)
    z_throat = exponential_horn_throat_impedance(
        frequencies=frequencies,
        horn=horn,
        radiation_angle=2 * np.pi  # Half-space (infinite baffle)
    )

    return frequencies, z_throat


def compare_with_hornresp(viberesp_freq, viberesp_z, hornresp_file):
    """Compare viberesp results with Hornresp reference data.

    Args:
        viberesp_freq: Frequency array from viberesp (Hz)
        viberesp_z: Complex throat impedance from viberesp (Pa·s/m³)
        hornresp_file: Path to Hornresp sim.txt file

    Returns:
        Dictionary with comparison results
    """
    # Load Hornresp reference data
    hr_data = load_hornresp_sim_file(hornresp_file)

    # Hornresp exports frequency in Hz
    hr_freq = hr_data.frequency

    # For pure horn theory validation, Hornresp exports normalized acoustical impedance.
    # To convert to actual throat impedance:
    #   Z_actual = Z_normalized * (ρ*c / S_throat)
    #
    # viberesp and Hornresp both use standard conditions:
    #   ρ = 1.205 kg/m³, c = 344 m/s (at 20°C, 1 atm)
    #
    # S_throat = throat area = 0.005 m² (50 cm²)
    #
    # Hornresp's Ra and Xa are the normalized resistance and reactance.
    throat_area = 0.005  # m² (50 cm²)
    rho = 1.205  # kg/m³ (standard conditions at 20°C)
    c = 344.0    # m/s (speed of sound at 20°C)
    characteristic_impedance = rho * c / throat_area  # Pa·s/m³

    # Convert normalized impedance to actual impedance
    hr_z_throat = (hr_data.ra_norm + 1j * hr_data.xa_norm) * characteristic_impedance

    # Interpolate viberesp results to Hornresp frequency points
    # np.interp doesn't work with complex arrays, so interpolate real/imag separately
    viberesp_z_interp = (
        np.interp(hr_freq, viberesp_freq, viberesp_z.real, left=np.nan, right=np.nan) +
        1j * np.interp(hr_freq, viberesp_freq, viberesp_z.imag, left=np.nan, right=np.nan)
    )

    # Calculate magnitude and phase
    viberesp_mag = np.abs(viberesp_z_interp)
    viberesp_phase = np.angle(viberesp_z_interp, deg=True)

    hr_mag = np.abs(hr_z_throat)
    hr_phase = np.angle(hr_z_throat, deg=True)

    # Calculate errors
    magnitude_error_percent = 100 * (viberesp_mag - hr_mag) / hr_mag
    phase_error_deg = viberesp_phase - hr_phase

    # Handle phase wraparound
    phase_error_deg = np.where(
        phase_error_deg > 180,
        phase_error_deg - 360,
        phase_error_deg
    )
    phase_error_deg = np.where(
        phase_error_deg < -180,
        phase_error_deg + 360,
        phase_error_deg
    )

    # Cutoff frequency
    fc = 210.11  # Hz (from metadata.json)

    # Analyze errors in frequency regions
    mask_well_above = hr_freq > 2 * fc
    mask_transition = (hr_freq > fc) & (hr_freq <= 2 * fc)
    mask_below = hr_freq <= fc

    results = {
        'frequencies': hr_freq,
        'viberesp_magnitude': viberesp_mag,
        'hornresp_magnitude': hr_mag,
        'magnitude_error_percent': magnitude_error_percent,
        'viberesp_phase': viberesp_phase,
        'hornresp_phase': hr_phase,
        'phase_error_deg': phase_error_deg,
        'cutoff_frequency': fc,
        'error_regions': {
            'well_above_fc': mask_well_above,
            'transition': mask_transition,
            'below_fc': mask_below
        }
    }

    return results


def print_validation_summary(results):
    """Print validation summary statistics."""
    fc = results['cutoff_frequency']

    print("=" * 70)
    print("HORN THEORY VALIDATION SUMMARY - TEST CASE 1")
    print("Exponential Midrange Horn")
    print("=" * 70)
    print(f"\nHorn geometry:")
    print(f"  S1 = 50 cm², S2 = 500 cm², L12 = 30 cm")
    print(f"  Expansion ratio: 10:1")
    print(f"  Cutoff frequency (fc) = {fc:.1f} Hz")

    print(f"\nFrequency ranges:")
    print(f"  Well above cutoff:  f > {2*fc:.0f} Hz")
    print(f"  Transition region:  {fc:.0f} < f ≤ {2*fc:.0f} Hz")
    print(f"  Below cutoff:      f ≤ {fc:.0f} Hz")

    # Calculate statistics for each region
    for region_name, region_mask, tolerance in [
        ("Well above cutoff (f > 2×fc)", results['error_regions']['well_above_fc'], 1.0),
        ("Transition (fc < f ≤ 2×fc)", results['error_regions']['transition'], 3.0),
        ("Below cutoff (f ≤ fc)", results['error_regions']['below_fc'], 10.0),
    ]:
        if not np.any(region_mask):
            print(f"\n{region_name}:")
            print(f"  No data points in this region")
            continue

        mag_error = results['magnitude_error_percent'][region_mask]
        phase_error = results['phase_error_deg'][region_mask]

        print(f"\n{region_name}:")
        print(f"  Magnitude error:")
        print(f"    Mean:   {np.mean(np.abs(mag_error)):.3f}%")
        print(f"    Max:    {np.max(np.abs(mag_error)):.3f}%")
        print(f"    RMS:    {np.sqrt(np.mean(mag_error**2)):.3f}%")
        print(f"  Pass (<{tolerance}%): {np.sum(np.abs(mag_error) < tolerance)}/{len(mag_error)} points")

        print(f"  Phase error:")
        print(f"    Mean:   {np.mean(np.abs(phase_error)):.2f}°")
        print(f"    Max:    {np.max(np.abs(phase_error)):.2f}°")

    print("\n" + "=" * 70)
    print("VALIDATION CRITERIA:")
    print("=" * 70)
    print(f"  ✓ f > 2×fc:   <1% magnitude error")
    print(f"  ✓ fc < f ≤ 2×fc:  <3% magnitude error")
    print(f"  ✓ f ≤ fc:     <10% magnitude error (qualitative)")
    print("=" * 70)


def plot_comparison(results, output_file=None):
    """Plot viberesp vs Hornresp comparison.

    Args:
        results: Comparison results dictionary
        output_file: Optional path to save figure
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    freq = results['frequencies']

    # Plot 1: Magnitude
    ax1 = axes[0]
    ax1.semilogx(freq, results['viberesp_magnitude'], 'b-', linewidth=2, label='Viberesp')
    ax1.semilogx(freq, results['hornresp_magnitude'], 'r--', linewidth=2, label='Hornresp')
    ax1.axvline(results['cutoff_frequency'], color='k', linestyle=':', alpha=0.5, label='Cutoff (fc)')
    ax1.axvline(2 * results['cutoff_frequency'], color='k', linestyle=':', alpha=0.3, label='2×fc')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('|Z_throat| (Pa·s/m³)')
    ax1.set_title('Throat Impedance Magnitude')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Phase
    ax2 = axes[1]
    ax2.semilogx(freq, results['viberesp_phase'], 'b-', linewidth=2, label='Viberesp')
    ax2.semilogx(freq, results['hornresp_phase'], 'r--', linewidth=2, label='Hornresp')
    ax2.axvline(results['cutoff_frequency'], color='k', linestyle=':', alpha=0.5, label='Cutoff (fc)')
    ax2.axvline(2 * results['cutoff_frequency'], color='k', linestyle=':', alpha=0.3, label='2×fc')
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (degrees)')
    ax2.set_title('Throat Impedance Phase')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"\n✓ Plot saved to: {output_file}")
    else:
        plt.show()


def main():
    """Main validation workflow."""
    print("\n" + "=" * 70)
    print("HORN THEORY VALIDATION - TEST CASE 1")
    print("Exponential Midrange Horn")
    print("=" * 70)

    # Get the directory containing this script
    validation_dir = Path(__file__).parent

    # Step 1: Calculate viberesp results
    print("\n[1/4] Calculating viberesp throat impedance...")
    viberesp_freq, viberesp_z = calculate_viberesp_throat_impedance()
    print(f"      ✓ Calculated {len(viberesp_freq)} frequency points")

    # Step 2: Load Hornresp reference data
    hornresp_file = validation_dir / "sim.txt"
    print(f"\n[2/4] Loading Hornresp reference data...")
    print(f"      File: {hornresp_file}")

    try:
        results = compare_with_hornresp(viberesp_freq, viberesp_z, str(hornresp_file))
        print(f"      ✓ Loaded {len(results['frequencies'])} frequency points")
    except FileNotFoundError:
        print(f"\n      ✗ ERROR: File not found: {hornresp_file}")
        print(f"\n      To generate this file:")
        print(f"        1. Open Hornresp")
        print(f"        2. File → Import → {validation_dir / 'horn_params.txt'}")
        print(f"        3. Calculate (F5)")
        print(f"        4. Tools → Export → Acoustical Impedance")
        print(f"        5. Save as: {hornresp_file}")
        return
    except Exception as e:
        print(f"\n      ✗ ERROR: {e}")
        return

    # Step 3: Print validation summary
    print("\n[3/4] Analyzing results...")
    print_validation_summary(results)

    # Step 4: Plot comparison
    print("\n[4/4] Generating plots...")
    plot_file = validation_dir / "validation_comparison.png"
    plot_comparison(results, output_file=str(plot_file))

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to:")
    print(f"  • {plot_file}")
    print(f"\nValidation data:")
    print(f"  • {validation_dir / 'metadata.json'}")
    print(f"  • {validation_dir / 'sim.txt'}")


if __name__ == "__main__":
    main()
