"""
Run ported box simulations for all B&C drivers and save results.

This script simulates the frequency response and impedance for each driver
in their B4 ported box alignment, saving data for comparison with Hornresp.

Literature:
- Thiele (1971) - Vented box theory
- Beranek (1954) - Radiation impedance
"""

import numpy as np
import csv
from pathlib import Path

from viberesp.driver.bc_drivers import get_all_bc_drivers
from viberesp.enclosure.ported_box import (
    calculate_ported_box_system_parameters,
    calculate_optimal_port_dimensions,
    ported_box_electrical_impedance,
)


def simulate_ported_box_response(driver, driver_name: str, output_dir: Path):
    """
    Simulate ported box frequency response for a driver.

    Generates CSV files with impedance and SPL data across frequency range.

    Args:
        driver: ThieleSmallParameters instance
        driver_name: Driver name for output files
        output_dir: Directory to save results
    """

    # B4 alignment: Vb = Vas, Fb = Fs
    Vb_m3 = driver.V_as
    Fb = driver.F_s

    # Calculate optimal port dimensions
    port_area_m2, port_length_m, v_max = calculate_optimal_port_dimensions(
        driver, Vb_m3, Fb
    )

    # Get system parameters
    params = calculate_ported_box_system_parameters(
        driver, Vb_m3, Fb,
        port_area=port_area_m2,
        port_length=port_length_m
    )

    # Frequency range: 20 Hz to 1 kHz (logarithmic spacing)
    # Use 50 points per decade for good resolution
    frequencies = np.logspace(np.log10(20), np.log10(1000), 100)

    # Storage for results
    results = []

    print(f"\nSimulating {driver_name}...")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Vb: {Vb_m3*1000:.1f} L")
    print(f"  Fb: {Fb:.1f} Hz")
    print(f"  Port: {port_area_m2*10000:.1f} cm² x {port_length_m*100:.1f} cm")
    print(f"  α: {params.alpha:.3f}, h: {params.h:.3f}")

    # Simulate each frequency
    for freq in frequencies:
        result = ported_box_electrical_impedance(
            frequency=freq,
            driver=driver,
            Vb=Vb_m3,
            Fb=Fb,
            port_area=port_area_m2,
            port_length=port_length_m,
            voltage=2.83,
            measurement_distance=1.0,
        )

        results.append({
            'frequency_hz': freq,
            'Ze_magnitude_ohm': result['Ze_magnitude'],
            'Ze_phase_deg': result['Ze_phase'],
            'Ze_real_ohm': result['Ze_real'],
            'Ze_imag_ohm': result['Ze_imag'],
            'SPL_db': result['SPL'],
            'diaphragm_velocity_ms': result['diaphragm_velocity'],
            'radiation_resistance': result['radiation_resistance'],
            'radiation_reactance': result['radiation_reactance'],
        })

    # Save results to CSV
    output_file = output_dir / f"{driver_name}_ported_B4_viberesp.csv"

    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'frequency_hz',
            'Ze_magnitude_ohm',
            'Ze_phase_deg',
            'Ze_real_ohm',
            'Ze_imag_ohm',
            'SPL_db',
            'diaphragm_velocity_ms',
            'radiation_resistance',
            'radiation_reactance',
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"  Saved: {output_file}")

    # Find impedance peaks and dip
    ze_mags = [r['Ze_magnitude_ohm'] for r in results]
    freqs = [r['frequency_hz'] for r in results]

    # Find peaks (local maxima)
    peaks = []
    for i in range(1, len(ze_mags)-1):
        if ze_mags[i] > ze_mags[i-1] and ze_mags[i] > ze_mags[i+1]:
            peaks.append((freqs[i], ze_mags[i]))

    # Find dip (local minimum)
    dip_idx = ze_mags.index(min(ze_mags))
    dip_freq = freqs[dip_idx]
    dip_mag = ze_mags[dip_idx]

    print(f"\n  Impedance characteristics:")
    if len(peaks) >= 2:
        # Two main peaks in ported box
        peaks_sorted = sorted(peaks, key=lambda x: x[1], reverse=True)
        print(f"    Peak 1: {peaks_sorted[0][0]:.1f} Hz, {peaks_sorted[0][1]:.1f} Ω")
        print(f"    Peak 2: {peaks_sorted[1][0]:.1f} Hz, {peaks_sorted[1][1]:.1f} Ω")
    print(f"    Dip: {dip_freq:.1f} Hz, {dip_mag:.1f} Ω")
    print(f"    Re: {driver.R_e:.1f} Ω")

    # Find -3dB point
    spls = [r['SPL_db'] for r in results]
    spl_max = max(spls)
    f3_idx = next((i for i, spl in enumerate(spls) if spl < spl_max - 3), len(spls) - 1)
    f3_freq = freqs[f3_idx] if f3_idx < len(freqs) else None

    if f3_freq:
        print(f"\n  SPL characteristics:")
        print(f"    Max SPL: {spl_max:.1f} dB")
        print(f"    F3: {f3_freq:.1f} Hz")

    return results


def main():
    """Run simulations for all drivers."""

    drivers = get_all_bc_drivers()

    # Create output directory
    output_dir = Path("validation_cases/ported_box")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("PORTED BOX VALIDATION SIMULATIONS")
    print("="*60)
    print("\nRunning viberesp simulations for all B&C drivers")
    print(f"Output directory: {output_dir}")

    all_results = {}

    for driver, driver_name in drivers:
        results = simulate_ported_box_response(driver, driver_name, output_dir)
        all_results[driver_name] = results

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Simulated {len(all_results)} driver(s)")
    print(f"\nCSV files saved to: {output_dir}")
    print(f"\nNext steps:")
    print(f"1. Import the Hornresp .txt files into Hornresp")
    print(f"2. Export Hornresp impedance and SPL data")
    print(f"3. Compare with viberesp CSV results")

    return all_results


if __name__ == "__main__":
    main()
