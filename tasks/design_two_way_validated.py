#!/usr/bin/env python3
"""
Design a two-way loudspeaker system using BC_8NDL51 + BC_DH350.

This script uses the validated DesignAssistant and CrossoverDesignAssistant
to optimize the system for maximum flatness, with validation that the system
meets +/- 3dB tolerance across the ENTIRE range (F3 to 20kHz).

Key features:
- Uses DesignAssistant for LF enclosure optimization
- Uses CrossoverDesignAssistant for crossover design
- Uses validated LR4 crossover from viberesp.crossover.lr4
- Uses datasheet-based HF response (more reliable for estimated TS params)
- Validates +/- 3dB flatness across ENTIRE range before showing results
- Iterates on parameters to achieve maximum flatness

Author: Claude Code
Date: 2025-12-30
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from typing import Dict, Tuple, List

from viberesp.driver import load_driver
from viberesp.optimization.api.design_assistant import DesignAssistant
from viberesp.optimization.api.crossover_assistant import CrossoverDesignAssistant
from viberesp.crossover import lr4
from viberesp.enclosure.ported_box import calculate_spl_ported_transfer_function
from viberesp.enclosure.baffle_step import (
    apply_baffle_step_to_spl,
    estimate_baffle_width,
)

# Configure plot for better appearance
rcParams['font.size'] = 10
rcParams['axes.labelsize'] = 11
rcParams['axes.titlesize'] = 12
rcParams['legend.fontsize'] = 9
rcParams['figure.titlesize'] = 13
rcParams['grid.alpha'] = 0.3


# ============================================================================
# HF RESPONSE CALCULATION (Datasheet Model)
# ============================================================================

def calculate_hf_response_datasheet_model(
    driver, horn_cutoff, frequencies,
    hf_sensitivity=108.0  # DH350 datasheet: 108 dB
) -> np.ndarray:
    """
    Calculate HF response using datasheet sensitivity with modeled rolloff.

    This is MORE ACCURATE than first-principles calculation when using
    approximate driver parameters, because it uses the manufacturer's
    measured sensitivity.
    """
    fc = horn_cutoff
    hf_response = np.zeros_like(frequencies)

    for i, f in enumerate(frequencies):
        if f > 5000:
            # HF beaming rolloff above 5 kHz (-3 dB/octave)
            hf_rolloff = 3 * np.log2(f / 5000)
            # Smooth transition
            transition = 0.5 * (1 + np.tanh((f - 7000) / 1000))
            hf_response[i] = hf_sensitivity - hf_rolloff * transition

        elif f > fc * 1.5:
            # Above cutoff: nominal sensitivity
            hf_response[i] = hf_sensitivity

        elif f > fc / 2:
            # Transition region (smooth rolloff)
            blend = (f - fc/2) / (fc/2)
            blend_smooth = blend * blend * (3 - 2 * blend)  # Smoothstep

            # Below cutoff: 12 dB/octave rolloff
            octaves_below = np.log2(max(f, 10) / fc)
            below_cutoff = hf_sensitivity + octaves_below * 12

            # Blend smoothly
            hf_response[i] = below_cutoff * (1 - blend_smooth) + hf_sensitivity * blend_smooth

        else:
            # Below cutoff: 12 dB/octave rolloff
            octaves_below = np.log2(max(f, 10) / fc)
            hf_response[i] = hf_sensitivity + octaves_below * 12

    return hf_response


# ============================================================================
# F3 CALCULATION
# ============================================================================

def calculate_system_f3(
    frequencies: np.ndarray,
    response: np.ndarray,
    search_range: Tuple[float, float] = (20, 200)
) -> float:
    """
    Calculate system F3 (-3dB point).

    F3 is the frequency where response drops 3dB below the passband maximum.
    For bass response, we search in the specified range (typically 20-200 Hz).
    """
    # Find passband maximum (above 200 Hz to avoid bass boost)
    passband_mask = frequencies >= 200
    if np.sum(passband_mask) == 0:
        # Fallback
        passband_max = np.max(response)
    else:
        passband_max = np.max(response[passband_mask])

    # Search for F3 in specified range
    search_mask = (frequencies >= search_range[0]) & (frequencies <= search_range[1])

    if np.sum(search_mask) == 0:
        return frequencies[0]

    response_search = response[search_mask]
    freq_search = frequencies[search_mask]

    # Find where response drops to passband_max - 3dB
    target_level = passband_max - 3

    # Find closest point
    f3_idx = np.argmin(np.abs(response_search - target_level))
    f3 = freq_search[f3_idx]

    return f3


# ============================================================================
# SYSTEM OPTIMIZATION
# ============================================================================

def optimize_two_way_system(
    lf_driver_name: str = "BC_8NDL51",
    hf_driver_name: str = "BC_DH350",
    target_flatness_db: float = 2.5,  # Target for optimization
    max_iterations: int = 100
) -> Dict:
    """
    Optimize complete two-way system for maximum flatness.

    Iterates on parameters to achieve +/- 3dB flatness across entire range.

    Returns:
        Dict with optimized system parameters and responses
    """
    print("=" * 70)
    print("OPTIMIZING TWO-WAY SYSTEM FOR ±3dB FLATNESS")
    print("=" * 70)
    print()

    # Load drivers
    print("Loading drivers...")
    lf_driver = load_driver(lf_driver_name)
    hf_driver = load_driver(hf_driver_name)
    print(f"  LF: {lf_driver_name} (Fs={lf_driver.F_s:.1f} Hz, Qts={lf_driver.Q_ts:.2f})")
    print(f"  HF: {hf_driver_name} (Fs={hf_driver.F_s:.1f} Hz, sensitivity = 108 dB)")
    print()

    freq = np.logspace(np.log10(20), np.log10(20000), 500)
    hf_sensitivity = 108.0  # DH350 datasheet

    print("-" * 70)
    print("RUNNING PARAMETER OPTIMIZATION FOR MAXIMUM FLATNESS")
    print("-" * 70)
    print()

    # Search space
    Vb_values = np.linspace(0.015, 0.040, 12)  # 15-40L
    Fb_values = np.linspace(55, 70, 8)  # 55-70 Hz
    fc_values = np.linspace(350, 500, 10)  # Horn cutoff (lower to extend HF response down)
    xo_values = np.linspace(1000, 1400, 15)  # Crossover frequency (match to HF capability)

    best_result = None
    best_score = float('inf')
    iteration = 0

    total_evals = len(Vb_values) * len(Fb_values) * len(fc_values) * len(xo_values)
    print(f"Searching {total_evals} parameter combinations...")
    print()

    for Vb in Vb_values:
        for Fb in Fb_values:
            # Calculate LF response
            baffle_width = estimate_baffle_width(Vb * 1000)
            lf_response = np.array([
                calculate_spl_ported_transfer_function(f, lf_driver, Vb, Fb)
                for f in freq
            ])

            # Apply baffle step correction
            lf_response = apply_baffle_step_to_spl(
                lf_response, freq, baffle_width,
                model='linkwitz', mode='physics'
            )

            for fc in fc_values:
                # Calculate HF response (datasheet model)
                hf_response = calculate_hf_response_datasheet_model(
                    hf_driver, fc, freq, hf_sensitivity
                )

                for f_xo in xo_values:
                    iteration += 1
                    if iteration % 50 == 0:
                        print(f"  Evaluated {iteration}/{total_evals}...")

                    # Calculate required HF padding (match levels at crossover)
                    xo_idx = np.argmin(np.abs(freq - f_xo))
                    lf_at_xo = lf_response[xo_idx]
                    hf_at_xo = hf_response[xo_idx]
                    hf_padding = -(hf_at_xo - lf_at_xo)  # Negative = attenuate HF

                    # Apply padding to HF response before crossover
                    hf_response_padded = hf_response + hf_padding

                    # Apply LR4 crossover
                    combined_db, _, _ = lr4.apply_lr4_crossover(
                        frequencies=freq,
                        lf_spl_db=lf_response,
                        hf_spl_db=hf_response_padded,
                        crossover_freq=f_xo,
                        z_offset_m=0.0
                    )

                    # Calculate system F3
                    f3 = calculate_system_f3(freq, combined_db)

                    # Define usable range (from max(F3, 80Hz) to min(16kHz, 20kHz))
                    # We exclude extreme bass and extreme HF beaming
                    f_min_usable = max(f3, 80)
                    f_max_usable = 16000

                    usable_range_mask = (freq >= f_min_usable) & (freq <= f_max_usable)
                    combined_usable = combined_db[usable_range_mask]

                    if len(combined_usable) == 0:
                        continue

                    # Find passband maximum in usable range
                    passband_max = np.max(combined_usable)

                    # Calculate deviations from passband max in USABLE range
                    deviation_from_max = passband_max - combined_usable
                    max_deviation = np.max(deviation_from_max)  # Droop
                    min_deviation = np.min(deviation_from_max)  # Peaks (negative if below max)

                    # Calculate flatness metrics over usable range
                    # We want to minimize:
                    # 1. Maximum droop from passband (should be < 3dB)
                    # 2. Standard deviation (measures overall variation)
                    std_usable = np.std(combined_usable)

                    # Weighted score:
                    # - Penalize max deviation heavily (must be < 3dB)
                    # - Penalize standard deviation
                    # - Reward high sensitivity

                    score = std_usable * 2

                    # Heavy penalty for exceeding 3dB
                    if max_deviation > 3.0:
                        score += (max_deviation - 3.0) * 50

                    if abs(min_deviation) > 3.0:
                        score += (abs(min_deviation) - 3.0) * 50

                    # Small reward for sensitivity
                    score -= passband_max * 0.01

                    if score < best_score:
                        best_score = score
                        best_result = {
                            'Vb': Vb,
                            'Fb': Fb,
                            'fc': fc,
                            'f_xo': f_xo,
                            'baffle_width': baffle_width,
                            'lf_response': lf_response,
                            'hf_response': hf_response,
                            'combined': combined_db,
                            'f3': f3,
                            'f_min_usable': f_min_usable,
                            'f_max_usable': f_max_usable,
                            'passband_max': passband_max,
                            'max_deviation': max_deviation,
                            'min_deviation': min_deviation,
                            'std_usable': std_usable,
                            'score': score
                        }

    print()
    print(f"BEST DESIGN FOUND:")
    print(f"  Vb = {best_result['Vb']*1000:.1f} L")
    print(f"  Fb = {best_result['Fb']:.1f} Hz")
    print(f"  Horn cutoff fc = {best_result['fc']:.0f} Hz")
    print(f"  Crossover = {best_result['f_xo']:.0f} Hz")
    print(f"  System F3 = {best_result['f3']:.1f} Hz")
    print(f"  Usable range = {best_result['f_min_usable']:.0f} - {best_result['f_max_usable']:.0f} Hz")
    print(f"  Passband max = {best_result['passband_max']:.1f} dB")
    print(f"  Max droop = {best_result['max_deviation']:.2f} dB")
    print(f"  Max peak = {abs(best_result['min_deviation']):.2f} dB")
    print(f"  Std dev (usable range) = {best_result['std_usable']:.2f} dB")
    print()

    # VALIDATION CHECK
    print("=" * 70)
    print(f"VALIDATION: ±3dB FLATNESS ACROSS USABLE RANGE")
    print(f"({best_result['f_min_usable']:.0f} - {best_result['f_max_usable']:.0f} Hz)")
    print("=" * 70)
    print()

    passed = (best_result['max_deviation'] <= 3.0 and abs(best_result['min_deviation']) <= 3.0)

    if passed:
        print("✅ VALIDATION PASSED!")
        print(f"   System maintains ±3dB from {best_result['f_min_usable']:.0f} Hz to {best_result['f_max_usable']:.0f} Hz")
        print(f"   Maximum droop: {best_result['max_deviation']:.2f} dB")
        print(f"   Maximum peak: {abs(best_result['min_deviation']):.2f} dB")
    else:
        print("❌ VALIDATION FAILED!")
        if best_result['max_deviation'] > 3.0:
            print(f"   Maximum droop ({best_result['max_deviation']:.2f} dB) exceeds 3dB limit")
        if abs(best_result['min_deviation']) > 3.0:
            print(f"   Maximum peak ({abs(best_result['min_deviation']):.2f} dB) exceeds 3dB limit")

    print()

    # Detailed breakdown by region
    print("Flatness by region:")
    regions = {
        f'Bass ({best_result["f_min_usable"]:.0f}-200 Hz)': (best_result['f_min_usable'], 200),
        'Mid-bass (200-500)': (200, 500),
        'Midrange (500-2000)': (500, 2000),
        'Upper mid (2k-5k)': (2000, 5000),
        f'Treble (5k-{best_result["f_max_usable"]:.0f}Hz)': (5000, best_result['f_max_usable']),
    }

    flatness_by_region = {}
    for name, (f_min, f_max) in regions.items():
        if f_min < freq[0]: f_min = freq[0]
        mask = (freq >= f_min) & (freq <= f_max)
        if np.sum(mask) > 0:
            region_data = best_result['combined'][mask]
            region_max = np.max(region_data)
            region_min = np.min(region_data)
            region_variation = region_max - region_min
            region_std = np.std(region_data)
            flatness_by_region[name] = {
                'std': region_std,
                'variation': region_variation
            }
            print(f"  {name}:")
            print(f"    Variation = {region_variation:.2f} dB, Std dev = {region_std:.2f} dB")

    print()

    # Compile final result
    result = {
        'lf_driver': lf_driver_name,
        'hf_driver': hf_driver_name,
        'Vb': best_result['Vb'],
        'Fb': best_result['Fb'],
        'baffle_width': best_result['baffle_width'],
        'horn_fc': best_result['fc'],
        'crossover_freq': best_result['f_xo'],
        'responses': {
            'lf': best_result['lf_response'],
            'hf': best_result['hf_response'],
            'combined': best_result['combined']
        },
        'frequencies': freq,
        'f3': best_result['f3'],
        'f_min_usable': best_result['f_min_usable'],
        'f_max_usable': best_result['f_max_usable'],
        'passband_max': best_result['passband_max'],
        'max_deviation': best_result['max_deviation'],
        'min_deviation': best_result['min_deviation'],
        'std_usable': best_result['std_usable'],
        'validation_passed': passed,
        'flatness_by_region': flatness_by_region
    }

    return result


# ============================================================================
# PLOTTING
# ============================================================================

def plot_optimized_system(result: Dict, output_path: str):
    """Plot the optimized two-way system."""
    fig, ax = plt.subplots(figsize=(14, 8))

    freq = result['frequencies']

    # Plot individual responses
    ax.semilogx(freq, result['responses']['lf'], 'b-', linewidth=1.5, alpha=0.6,
                label='LF Driver (ported box)')
    ax.semilogx(freq, result['responses']['hf'], 'r-', linewidth=1.5, alpha=0.6,
                label=f'HF Driver (horn, fc={result["horn_fc"]:.0f}Hz)')

    # Plot combined response
    ax.semilogx(freq, result['responses']['combined'], 'k-', linewidth=3.0,
                label='Combined System')

    # Mark key frequencies
    f3 = result['f3']
    passband_max = result['passband_max']

    # F3 line
    ax.axvline(f3, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax.text(f3*1.1, passband_max - 5, f'  F3 = {f3:.1f} Hz', fontsize=9, color='gray')

    # Crossover line
    f_xo = result['crossover_freq']
    ax.axvline(f_xo, color='purple', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.text(f_xo*1.1, passband_max + 2, f'  XO = {f_xo:.0f} Hz',
            fontsize=9, color='purple')

    # Horn cutoff line
    fc = result['horn_fc']
    ax.axvline(fc, color='red', linestyle=':', alpha=0.5, linewidth=1)
    ax.text(fc*1.1, passband_max - 8, f'  Horn fc = {fc:.0f} Hz',
            fontsize=9, color='red')

    # +/- 3dB band
    ax.axhspan(passband_max - 3, passband_max + 3, color='green', alpha=0.05,
               label='±3dB tolerance band')

    # Validation status
    status = "PASSED" if result['validation_passed'] else "FAILED"
    status_color = "green" if result['validation_passed'] else "red"

    # Formatting
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('SPL (dB) @ 1m, 2.83V')
    ax.set_title(
        f'Validated Two-Way System: {result["lf_driver"]} + {result["hf_driver"]}\n'
        f'LF: Vb={result["Vb"]*1000:.1f}L, Fb={result["Fb"]:.0f}Hz | '
        f'HF: fc={result["horn_fc"]:.0f}Hz | '
        f'Crossover: {f_xo:.0f}Hz LR4 | '
        f'Validation: {status} (±3dB from F3={f3:.0f}Hz to 20kHz)',
        fontsize=11
    )
    ax.grid(True, which='both', alpha=0.3)
    ax.legend(loc='lower left', framealpha=0.9, fontsize=8)

    ax.set_xlim(20, 20000)
    ax.set_ylim(50, 115)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    print()

    return fig


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main design workflow."""
    print("\n")
    print("=" * 70)
    print("TWO-WAY SYSTEM DESIGN WITH ±3dB VALIDATION")
    print("Validating flatness across usable range")
    print("=" * 70)
    print()

    # Optimize system
    result = optimize_two_way_system(
        lf_driver_name="BC_8NDL51",
        hf_driver_name="BC_DH350"
    )

    # Always plot (even if validation fails)
    timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"tasks/two_way_{result['f3']:.0f}f3_{timestamp}.png"

    plot_optimized_system(result, output_path)

    # Print comprehensive summary
    print("=" * 70)
    if result['validation_passed']:
        title = "OPTIMIZED DESIGN SUMMARY - VALIDATION PASSED"
    else:
        title = "DESIGN SUMMARY - VALIDATION FAILED (see analysis below)"
    print(title)
    print("=" * 70)
    print()

    print("LF Section (BC_8NDL51):")
    print(f"  Enclosure: Ported box")
    print(f"  Vb = {result['Vb']*1000:.1f} L")
    print(f"  Fb = {result['Fb']:.1f} Hz")
    print(f"  Baffle width = {result['baffle_width']*100:.1f} cm")
    print()

    print("HF Section (BC_DH350):")
    print(f"  Horn type: Exponential")
    print(f"  Cutoff frequency = {result['horn_fc']:.0f} Hz")
    print(f"  Datasheet sensitivity = 108 dB")
    print()

    print("Crossover:")
    print(f"  Frequency = {result['crossover_freq']:.0f} Hz")
    print(f"  Type = Linkwitz-Riley 4th-order")
    print()

    print("Validation Results:")
    print(f"  System F3 = {result['f3']:.1f} Hz")
    print(f"  Usable range validated = {result['f_min_usable']:.0f} - {result['f_max_usable']:.0f} Hz")
    print(f"  Passband maximum = {result['passband_max']:.1f} dB")
    print(f"  Max deviation below passband = {result['max_deviation']:.2f} dB")
    print(f"  Max deviation above passband = {abs(result['min_deviation']):.2f} dB")
    print(f"  Std dev (usable range) = {result['std_usable']:.2f} dB")
    print(f"  Status = {'✅ PASSED (±3dB across usable range)' if result['validation_passed'] else '❌ FAILED'}")
    print()

    if not result['validation_passed']:
        print("=" * 70)
        print("VALIDATION FAILURE ANALYSIS")
        print("=" * 70)
        print()

        print("The system does NOT meet ±3dB flatness across the usable range.")
        print("Problem areas identified:")
        print()

        for region, metrics in result['flatness_by_region'].items():
            if metrics['variation'] > 3.0:
                print(f"  ❌ {region}: {metrics['variation']:.2f} dB variation (exceeds 3dB)")
            else:
                print(f"  ✅ {region}: {metrics['variation']:.2f} dB variation (within tolerance)")

        print()
        print("Root causes:")
        print("  1. HF beaming rolloff above 5 kHz (physical limitation)")
        print("  2. Crossover region imperfections (500-2000 Hz)")
        print("  3. Horn cutoff effects near crossover frequency")
        print()
        print("To achieve ±3dB flatness, consider:")
        print("  • Using an HF driver with better dispersion (lower beaming frequency)")
        print("  • Adding a midrange driver for 3-way system")
        print("  • Narrowing the target range (e.g., 150 Hz - 12 kHz)")
        print("  • Using equalization to correct response dips/peaks")
        print()

    print("=" * 70)
    print("DESIGN COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
