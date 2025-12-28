#!/usr/bin/env python3
"""
Optimized BC_15DS115 ported box study with improved simulation model.

This script performs a comprehensive optimization study comparing:
1. Multiple design configurations
2. Improved HF roll-off model (mass break + inductance)
3. Focus on flatness metrics across different frequency ranges

Improvements over old study:
- Calibrated transfer function SPL with +13 dB offset
- Frequency-dependent Leach inductance model (n=0.4)
- Mass-controlled roll-off from JBL formula
- More comprehensive flatness evaluation

Literature:
- Small (1973) - Vented-box transfer function
- JBL - Mass break frequency formula
- Leach (2002) - Voice coil inductance losses
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import json
from datetime import datetime
from viberesp.driver.bc_drivers import get_bc_15ds115
from viberesp.enclosure.ported_box import (
    calculate_optimal_port_dimensions,
    calculate_spl_ported_transfer_function,
    calculate_ported_box_system_parameters,
    calculate_mass_break_frequency,
    calculate_inductance_corner_frequency
)


def evaluate_design_comprehensive(driver, Vb, Fb, name, freq_points=None):
    """
    Evaluate a design with comprehensive metrics.

    Args:
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)
        Fb: Tuning frequency (Hz)
        name: Design name
        freq_points: Frequency points to evaluate (optional)

    Returns:
        Dictionary with comprehensive metrics
    """
    if freq_points is None:
        # Generate frequency points from 10 Hz to 500 Hz (log spaced)
        freq_points = np.logspace(np.log10(10), np.log10(500), 200)

    # Calculate optimal port dimensions
    port_area, port_length, v_max = calculate_optimal_port_dimensions(driver, Vb, Fb)

    # Calculate system parameters
    sys_params = calculate_ported_box_system_parameters(
        driver, Vb, Fb, port_area, port_length
    )

    # Calculate frequency response (using improved transfer function)
    frequencies = []
    spl_values = []
    hf_rolloff_values = []

    for freq in freq_points:
        # SPL with HF roll-off enabled (default, improved model)
        spl_hf_on = calculate_spl_ported_transfer_function(
            frequency=freq,
            driver=driver,
            Vb=Vb,
            Fb=Fb,
            voltage=2.83,
            measurement_distance=1.0,
            Qp=7.0,
            include_hf_rolloff=True  # IMPROVED: includes mass + inductance roll-off
        )

        # SPL without HF roll-off (old model for comparison)
        spl_hf_off = calculate_spl_ported_transfer_function(
            frequency=freq,
            driver=driver,
            Vb=Vb,
            Fb=Fb,
            voltage=2.83,
            measurement_distance=1.0,
            Qp=7.0,
            include_hf_rolloff=False  # OLD: no HF roll-off
        )

        hf_rolloff_db = spl_hf_off - spl_hf_on  # Positive = roll-off applied

        frequencies.append(freq)
        spl_values.append(spl_hf_on)  # Use improved model
        hf_rolloff_values.append(hf_rolloff_db)

    frequencies = np.array(frequencies)
    spl_values = np.array(spl_values)
    hf_rolloff_values = np.array(hf_rolloff_values)

    # Calculate metrics in different ranges
    def calc_flatness(f_min, f_max):
        """Calculate standard deviation of SPL in frequency range."""
        mask = (frequencies >= f_min) & (frequencies <= f_max)
        return np.std(spl_values[mask])

    def calc_spl_at_freq(freq):
        """Get SPL at specific frequency."""
        idx = np.argmin(np.abs(frequencies - freq))
        return spl_values[idx]

    def calc_max_spl_in_range(f_min, f_max):
        """Get maximum SPL in range."""
        mask = (frequencies >= f_min) & (frequencies <= f_max)
        return np.max(spl_values[mask])

    # Flatness metrics
    flatness_deep_bass = calc_flatness(20, 40)
    flatness_bass = calc_flatness(20, 80)
    flatness_midbass = calc_flatness(40, 120)
    flatness_full = calc_flatness(20, 200)
    flatness_extended = calc_flatness(20, 500)

    # Peak SPL metrics
    peak_spl = np.max(spl_values)
    peak_freq = frequencies[np.argmax(spl_values)]

    # F3 calculation
    max_spl = calc_max_spl_in_range(50, 200)  # Reference level above tuning
    f3_idx = np.where(spl_values < max_spl - 3)[0]
    f3 = frequencies[f3_idx[0]] if len(f3_idx) > 0 else None

    # HF roll-off analysis
    f_mass = calculate_mass_break_frequency(driver.BL, driver.R_e, driver.M_ms)
    f_le_dc = calculate_inductance_corner_frequency(driver.R_e, driver.L_e)

    # HF roll-off at 200 Hz
    idx_200 = np.argmin(np.abs(frequencies - 200))
    hf_rolloff_200hz = hf_rolloff_values[idx_200]

    return {
        'name': name,
        'Vb': Vb,
        'Fb': Fb,
        'port_area': port_area,
        'port_length': port_length,
        'port_velocity_max': v_max,
        'alpha': sys_params.alpha,
        'h': sys_params.h,
        'F3': f3,
        'frequencies': frequencies,
        'spl_values': spl_values,
        'hf_rolloff_values': hf_rolloff_values,
        'flatness_deep_bass': flatness_deep_bass,
        'flatness_bass': flatness_bass,
        'flatness_midbass': flatness_midbass,
        'flatness_full': flatness_full,
        'flatness_extended': flatness_extended,
        'peak_spl': peak_spl,
        'peak_freq': peak_freq,
        'max_spl_ref': max_spl,
        'hf_rolloff_200hz': hf_rolloff_200hz,
        'f_mass': f_mass,
        'f_le_dc': f_le_dc,
        'spl_at_freqs': {
            20: calc_spl_at_freq(20),
            30: calc_spl_at_freq(30),
            40: calc_spl_at_freq(40),
            50: calc_spl_at_freq(50),
            60: calc_spl_at_freq(60),
            80: calc_spl_at_freq(80),
            100: calc_spl_at_freq(100),
            150: calc_spl_at_freq(150),
            200: calc_spl_at_freq(200),
            300: calc_spl_at_freq(300),
            500: calc_spl_at_freq(500),
        }
    }


def compare_designs(driver, designs):
    """
    Compare multiple designs and create comprehensive comparison.

    Args:
        driver: ThieleSmallParameters instance
        designs: List of (name, Vb, Fb) tuples

    Returns:
        Dictionary with comparison results
    """
    results = []

    for name, Vb, Fb in designs:
        print(f"\nEvaluating: {name}")
        result = evaluate_design_comprehensive(driver, Vb, Fb, name)
        results.append(result)

    # Sort by different flatness metrics
    sorted_by_full = sorted(results, key=lambda x: x['flatness_full'])
    sorted_by_bass = sorted(results, key=lambda x: x['flatness_bass'])
    sorted_by_midbass = sorted(results, key=lambda x: x['flatness_midbass'])

    return {
        'results': results,
        'sorted_by_full': sorted_by_full,
        'sorted_by_bass': sorted_by_bass,
        'sorted_by_midbass': sorted_by_midbass
    }


def print_comparison_table(comparison):
    """Print detailed comparison table."""

    print("\n" + "=" * 100)
    print("FLATNESS COMPARISON TABLE (Improved Model with HF Roll-off)")
    print("=" * 100)
    print(f"{'Design':<28} | {'Vb':>5} | {'Fb':>5} | {'α':>5} | {'h':>5} | {'σ(20-40)':>9} | {'σ(20-80)':>9} | {'σ(40-120)':>10} | {'σ(20-200)':>10}")
    print("-" * 100)

    for r in comparison['sorted_by_full']:
        print(f"{r['name']:<28} | {r['Vb']*1000:>5.0f} | {r['Fb']:>5.1f} | {r['alpha']:>5.2f} | {r['h']:>5.2f} | "
              f"{r['flatness_deep_bass']:>9.2f} | {r['flatness_bass']:>9.2f} | {r['flatness_midbass']:>10.2f} | "
              f"{r['flatness_full']:>10.2f} {'⭐' if r == comparison['sorted_by_full'][0] else ''}")

    print("\n" + "=" * 100)
    print("PERFORMANCE METRICS")
    print("=" * 100)
    print(f"{'Design':<28} | {'Peak SPL':>10} | {'Peak Freq':>10} | {'F3':>6} | {'HF@200Hz':>9}")
    print("-" * 100)

    for r in comparison['sorted_by_full']:
        print(f"{r['name']:<28} | {r['peak_spl']:>10.1f} | {r['peak_freq']:>10.1f} | {r['F3']:>6.1f} | "
              f"{r['hf_rolloff_200hz']:>9.2f}")

    print("\n" + "=" * 100)
    print("FREQUENCY RESPONSE DETAIL (SPL in dB at 2.83V, 1m)")
    print("=" * 100)
    print(f"{'Freq':>6} | ", end="")
    for r in comparison['sorted_by_full'][:5]:  # Top 5 designs
        print(f"{r['name'][:20]:>22} | ", end="")
    print()
    print("-" * 100)

    for freq in [20, 30, 40, 50, 60, 80, 100, 150, 200, 300, 500]:
        print(f"{freq:>6} | ", end="")
        for r in comparison['sorted_by_full'][:5]:
            spl = r['spl_at_freqs'][freq]
            print(f"{spl:>22.1f} | ", end="")
        print()

    print()


def print_analysis(comparison, driver):
    """Print detailed analysis of results."""

    print("=" * 100)
    print("ANALYSIS: FLATNESS vs BOX SIZE")
    print("=" * 100)

    best_overall = comparison['sorted_by_full'][0]
    best_bass = comparison['sorted_by_bass'][0]
    best_midbass = comparison['sorted_by_midbass'][0]

    print(f"\n🏆 BEST OVERALL FLATNESS (20-200 Hz): {best_overall['name']}")
    print(f"   Flatness: σ = {best_overall['flatness_full']:.2f} dB")
    print(f"   Design: Vb = {best_overall['Vb']*1000:.1f} L, Fb = {best_overall['Fb']:.1f} Hz")
    print(f"   Alpha: {best_overall['alpha']:.2f}, h: {best_overall['h']:.2f}")
    print(f"   F3: {best_overall['F3']:.1f} Hz")
    print(f"   Port: {best_overall['port_area']*10000:.1f} cm² × {best_overall['port_length']*100:.1f} cm")

    print(f"\n🎯 BEST BASS FLATNESS (20-80 Hz): {best_bass['name']}")
    print(f"   Flatness: σ = {best_bass['flatness_bass']:.2f} dB")
    print(f"   Design: Vb = {best_bass['Vb']*1000:.1f} L, Fb = {best_bass['Fb']:.1f} Hz")

    print(f"\n🎵 BEST MIDBASS FLATNESS (40-120 Hz): {best_midbass['name']}")
    print(f"   Flatness: σ = {best_midbass['flatness_midbass']:.2f} dB")
    print(f"   Design: Vb = {best_midbass['Vb']*1000:.1f} L, Fb = {best_midbass['Fb']:.1f} Hz")

    # Find B4 alignment
    b4 = next((r for r in comparison['results'] if "B4" in r['name']), None)
    if b4:
        print(f"\n📊 B4 ALIGNMENT (Classic Butterworth):")
        print(f"   Design: Vb = {b4['Vb']*1000:.1f} L, Fb = {b4['Fb']:.1f} Hz")
        print(f"   Flatness (20-200 Hz): σ = {b4['flatness_full']:.2f} dB")
        print(f"   Flatness (20-80 Hz): σ = {b4['flatness_bass']:.2f} dB")
        print(f"   Difference from best: Δσ = {best_overall['flatness_full'] - b4['flatness_full']:+.2f} dB")

    # Driver characteristics
    print(f"\n🔧 DRIVER CHARACTERISTICS:")
    print(f"   Driver: BC_15DS115")
    print(f"   Fs: {driver.F_s:.1f} Hz")
    print(f"   Vas: {driver.V_as*1000:.1f} L")
    print(f"   Qts: {driver.Q_ts:.3f} (VERY LOW - high BL motor)")
    print(f"   BL: {driver.BL:.1f} T·m")
    print(f"   Mass break frequency: {best_overall['f_mass']:.1f} Hz")
    print(f"   Inductance corner: {best_overall['f_le_dc']:.1f} Hz")

    # HF roll-off impact
    print(f"\n📉 HIGH-FREQUENCY ROLL-OFF IMPACT:")
    print(f"   At 200 Hz: -{best_overall['hf_rolloff_200hz']:.2f} dB (from mass + inductance)")
    print(f"   This is IMPROVED model - old model would show ~0 dB roll-off")
    print(f"   Mass break: {best_overall['f_mass']:.1f} Hz (JBL formula)")
    print(f"   Inductance corner: {best_overall['f_le_dc']:.1f} Hz (DC approximation)")

    print()


def main():
    """Main study workflow."""

    print("\n" + "=" * 100)
    print("BC_15DS115 OPTIMIZED PORTED BOX STUDY")
    print("Improved Simulation Model with HF Roll-off")
    print("=" * 100)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get driver
    driver = get_bc_15ds115()

    print(f"\nDriver Parameters:")
    print(f"  Fs: {driver.F_s:.2f} Hz")
    print(f"  Vas: {driver.V_as*1000:.1f} L")
    print(f"  Qts: {driver.Q_ts:.3f}")
    print(f"  Qes: {driver.Q_es:.3f}")
    print(f"  BL: {driver.BL:.1f} T·m")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")

    # Define designs to compare
    # Mix of box sizes from compact to very large
    designs = [
        ("Compact (40L, 36Hz)", 0.040, 36.0),
        ("Small (60L, 34Hz)", 0.060, 34.0),
        ("Medium-Small (80L, 33Hz)", 0.080, 33.0),
        ("Medium (100L, 32Hz)", 0.100, 32.0),
        ("Medium-Large (120L, 31Hz)", 0.120, 31.0),
        ("Large (150L, 30Hz)", 0.150, 30.0),
        ("Very Large (180L, 29Hz)", 0.180, 29.0),
        ("B4 Alignment (254L, 33Hz)", driver.V_as, driver.F_s),
        ("Extra Large (300L, 27Hz)", 0.300, 27.0),
    ]

    print(f"\nEvaluating {len(designs)} designs...")
    print("This may take a moment...")

    # Compare all designs
    comparison = compare_designs(driver, designs)

    # Print results
    print_comparison_table(comparison)
    print_analysis(comparison, driver)

    # Save results to JSON
    output_file = "/tmp/bc15ds115_optimized_study_results.json"
    save_results = {
        'timestamp': datetime.now().isoformat(),
        'driver_params': {
            'Fs': driver.F_s,
            'Vas': driver.V_as,
            'Qts': driver.Q_ts,
            'Qes': driver.Q_es,
            'BL': driver.BL,
            'Sd': driver.S_d,
            'Xmax': driver.X_max,
        },
        'designs': []
    }

    for r in comparison['results']:
        save_results['designs'].append({
            'name': r['name'],
            'Vb_liters': r['Vb'] * 1000,
            'Fb_hz': r['Fb'],
            'alpha': r['alpha'],
            'h': r['h'],
            'F3': r['F3'],
            'flatness_full': r['flatness_full'],
            'flatness_bass': r['flatness_bass'],
            'flatness_midbass': r['flatness_midbass'],
            'peak_spl': r['peak_spl'],
            'peak_freq': r['peak_freq'],
            'hf_rolloff_200hz': r['hf_rolloff_200hz'],
            'spl_at_freqs': {str(k): v for k, v in r['spl_at_freqs'].items()}
        })

    with open(output_file, 'w') as f:
        json.dump(save_results, f, indent=2)

    print("=" * 100)
    print(f"Results saved to: {output_file}")
    print("=" * 100)

    return comparison


if __name__ == "__main__":
    comparison = main()
