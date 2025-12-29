#!/usr/bin/env python3
"""
Optimize BC_8FMB51 ported box for bookshelf speaker application.

This script optimizes the BC_8FMB51 driver for a bookshelf speaker that will be
paired with a horn-loaded compression HF driver. Typical crossover is 2-3 kHz.

Optimization objectives:
1. Midrange flatness (80-2000 Hz) - Primary objective for integration with HF horn
2. Bass extension (F3) - Target 50-60 Hz for bookshelf application
3. Compact size - Bookshelf speakers should be 15-30 L
4. Crossover region smoothness (1500-3000 Hz) - For clean integration

Literature:
    - Thiele (1971) - Vented box alignments
    - Small (1973) - Butterworth maximally flat response
    - literature/thiele_small/thiele_1971_vented_boxes.md
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from scipy.optimize import differential_evolution
from datetime import datetime

from viberesp.driver.loader import load_driver
from viberesp.enclosure.ported_box import (
    calculate_ported_box_system_parameters,
    calculate_optimal_port_dimensions,
)
from viberesp.enclosure.ported_box_vector_sum import calculate_spl_ported_vector_sum


def calculate_bookshelf_objectives(Vb: float, Fb: float, driver) -> dict:
    """
    Calculate objectives for bookshelf speaker optimization.

    Args:
        Vb: Box volume (m³)
        Fb: Port tuning frequency (Hz)
        driver: ThieleSmallParameters

    Returns:
        dict with objectives:
        - midrange_flatness: std dev of SPL 80-2000 Hz (lower is better)
        - bass_extension: F3 frequency (lower is better)
        - crossover_smoothness: std dev of SPL 1500-3000 Hz (lower is better)
        - infeasible: bool indicating if design is impractical
    """
    # Calculate port dimensions (handle constraints)
    try:
        port_area, port_length, _ = calculate_optimal_port_dimensions(driver, Vb, Fb)
    except ValueError as e:
        # Design is infeasible (port too long, etc.)
        return {
            'midrange_flatness': 100.0,
            'bass_extension': 200.0,
            'crossover_smoothness': 100.0,
            'overall_flatness': 300.0,
            'infeasible': True,
        }

    # Midrange flatness (80-2000 Hz) - main operating range
    freq_mid = np.logspace(np.log10(80), np.log10(2000), 50)
    spl_mid = []
    for freq in freq_mid:
        spl = calculate_spl_ported_vector_sum(
            frequency=freq,
            driver=driver,
            Vb=Vb,
            Fb=Fb,
            port_area=port_area,
            port_length=port_length,
        )
        spl_mid.append(spl)
    spl_mid = np.array(spl_mid)
    midrange_flatness = np.std(spl_mid)

    # Crossover region smoothness (1500-3000 Hz) - for HF integration
    freq_cross = np.logspace(np.log10(1500), np.log10(3000), 30)
    spl_cross = []
    for freq in freq_cross:
        spl = calculate_spl_ported_vector_sum(
            frequency=freq,
            driver=driver,
            Vb=Vb,
            Fb=Fb,
            port_area=port_area,
            port_length=port_length,
        )
        spl_cross.append(spl)
    spl_cross = np.array(spl_cross)
    crossover_smoothness = np.std(spl_cross)

    # Bass extension (F3)
    sys_params = calculate_ported_box_system_parameters(driver, Vb, Fb)
    f3 = sys_params.F3

    # Overall flatness (combined metric)
    overall_flatness = midrange_flatness + 0.5 * crossover_smoothness

    return {
        'midrange_flatness': midrange_flatness,
        'bass_extension': f3,
        'crossover_smoothness': crossover_smoothness,
        'overall_flatness': overall_flatness,
    }


def objective_bookshelf(design_vector: np.ndarray, driver) -> float:
    """
    Objective function for bookshelf speaker optimization.

    Minimizes:
    1. Midrange flatness (80-2000 Hz)
    2. Deviation from target F3 (55 Hz target for bookshelf)
    3. Crossover region ripple (1500-3000 Hz)

    Args:
        design_vector: [Vb (m³), Fb (Hz)]
        driver: ThieleSmallParameters

    Returns:
        float: Overall objective value (lower is better)
    """
    Vb, Fb = design_vector[0], design_vector[1]

    # Calculate objectives
    obj = calculate_bookshelf_objectives(Vb, Fb, driver)

    # Target F3 for bookshelf: 55 Hz
    target_f3 = 55.0
    f3_penalty = abs(obj['bass_extension'] - target_f3) / target_f3

    # Combined objective
    # Weight midrange flatness most heavily (main objective)
    # Add F3 penalty if outside acceptable range (45-65 Hz)
    if obj['bass_extension'] < 45:
        f3_penalty *= 2.0  # Penalize too-low F3 (large box)
    elif obj['bass_extension'] > 65:
        f3_penalty *= 2.0  # Penalize too-high F3 (poor bass)

    combined = obj['midrange_flatness'] + f3_penalty + 0.3 * obj['crossover_smoothness']

    return combined


def optimize_bc8fmb51_bookshelf():
    """
    Optimize BC_8FMB51 for bookshelf speaker application.

    Returns:
        dict: Optimization results with design parameters and objectives
    """
    # Get driver
    driver = load_driver("BC_8FMB51")

    print("\n" + "=" * 100)
    print("BC_8FMB51 BOOKSHELF SPEAKER OPTIMIZATION")
    print("Ported Box Design for Horn-Loaded HF Driver Integration")
    print("=" * 100)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\nDriver Parameters:")
    print(f"  Fs: {driver.F_s:.2f} Hz")
    print(f"  Vas: {driver.V_as*1000:.1f} L")
    print(f"  Qts: {driver.Q_ts:.3f}")
    print(f"  BL: {driver.BL:.1f} T·m")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")
    print(f"  Le: {driver.L_e*1000:.1f} mH")

    # Define parameter bounds for bookshelf speaker
    # Vb: 10L to 40L (bookshelf range)
    # Fb: 40 Hz to 65 Hz (bookshelf tuning range)
    vb_min, vb_max = 0.010, 0.040  # m³
    fb_min, fb_max = 40.0, 65.0     # Hz

    bounds = [(vb_min, vb_max), (fb_min, fb_max)]

    print(f"\nOptimization Bounds:")
    print(f"  Vb: {vb_min*1000:.0f} - {vb_max*1000:.0f} L")
    print(f"  Fb: {fb_min:.0f} - {fb_max:.0f} Hz")

    print(f"\nOptimization Objectives:")
    print(f"  1. Midrange flatness (80-2000 Hz) - For integration with HF horn")
    print(f"  2. Bass extension (F3 ≈ 55 Hz target) - Bookshelf typical")
    print(f"  3. Crossover smoothness (1500-3000 Hz) - Clean HF integration")

    # Run differential evolution optimization
    print(f"\nRunning optimization...")
    print(f"Algorithm: Differential Evolution")
    print(f"Population size: 15")
    print(f"Max generations: 30")

    result = differential_evolution(
        objective_bookshelf,
        bounds,
        strategy='best1bin',
        maxiter=30,
        popsize=15,
        tol=1e-6,
        mutation=0.8,
        recombination=0.9,
        seed=42,
        disp=True,
        args=(driver,)
    )

    # Extract optimal design
    Vb_opt, Fb_opt = result.x[0], result.x[1]
    objective_value = result.fun

    print(f"\nOptimization converged: {result.success}")
    print(f"Final objective value: {objective_value:.4f}")

    # Calculate all objectives for optimal design
    objectives_opt = calculate_bookshelf_objectives(Vb_opt, Fb_opt, driver)

    # Calculate port dimensions
    port_area, port_length, v_max = calculate_optimal_port_dimensions(
        driver, Vb_opt, Fb_opt
    )

    # Calculate system parameters
    sys_params = calculate_ported_box_system_parameters(
        driver, Vb_opt, Fb_opt, port_area, port_length
    )

    print(f"\n" + "=" * 100)
    print("OPTIMAL DESIGN")
    print("=" * 100)

    print(f"\nEnclosure Parameters:")
    print(f"  Vb: {Vb_opt*1000:.1f} L")
    print(f"  Fb: {Fb_opt:.2f} Hz")

    print(f"\nSystem Parameters:")
    print(f"  Alpha (α = Vas/Vb): {sys_params.alpha:.2f}")
    print(f"  Tuning ratio (h = Fb/Fs): {sys_params.h:.2f}")
    print(f"  F3: {sys_params.F3:.2f} Hz")

    print(f"\nPort Dimensions:")
    print(f"  Port area: {port_area*10000:.1f} cm²")
    print(f"  Port length: {port_length*100:.1f} cm")
    print(f"  Max port velocity: {v_max:.2f} m/s")

    # Determine alignment type
    print(f"\nAlignment Analysis:")
    if sys_params.alpha > 1.2:
        alignment_type = "Large box (α > 1.2)"
    elif sys_params.alpha < 0.8:
        alignment_type = "Compact box (α < 0.8)"
    else:
        alignment_type = "Near B4 alignment"

    print(f"  Type: {alignment_type}")
    print(f"  Vb/Vas ratio: {Vb_opt/driver.V_as:.2f}")

    # Performance objectives
    print(f"\nPerformance Objectives:")
    print(f"  Midrange flatness (80-2000 Hz):    σ = {objectives_opt['midrange_flatness']:.2f} dB")
    print(f"  Crossover smoothness (1500-3000 Hz): σ = {objectives_opt['crossover_smoothness']:.2f} dB")
    print(f"  Bass extension (F3):                {objectives_opt['bass_extension']:.2f} Hz")

    # Calculate frequency response
    print(f"\nFrequency Response (select points):")
    frequencies = [50, 80, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    for freq in frequencies:
        spl = calculate_spl_ported_vector_sum(
            frequency=freq,
            driver=driver,
            Vb=Vb_opt,
            Fb=Fb_opt,
            port_area=port_area,
            port_length=port_length,
        )
        print(f"  {freq:4.0f} Hz: {spl:6.1f} dB")

    # Compare with reference designs
    print(f"\n" + "=" * 100)
    print("COMPARISON WITH REFERENCE DESIGNS")
    print("=" * 100)

    reference_designs = [
        ("Compact (15L, 60Hz)", 0.015, 60.0),
        ("Small (20L, 55Hz)", 0.020, 55.0),
        ("Medium (25L, 50Hz)", 0.025, 50.0),
        ("Large (30L, 48Hz)", 0.030, 48.0),
        ("B4 Alignment (Vas, Fs)", driver.V_as, driver.F_s),
        ("Optimal Design", Vb_opt, Fb_opt),
    ]

    print(f"\n{'Design':<30} {'Vb':>6} {'Fb':>6} {'F3':>6} {'Mid σ':>8} {'Cross σ':>9}")
    print("-" * 100)

    for name, Vb, Fb in reference_designs:
        port_area_ref, port_length_ref, _ = calculate_optimal_port_dimensions(driver, Vb, Fb)
        sys_params_ref = calculate_ported_box_system_parameters(driver, Vb, Fb, port_area_ref, port_length_ref)
        obj_ref = calculate_bookshelf_objectives(Vb, Fb, driver)

        print(f"{name:<30} {Vb*1000:6.1f} {Fb:6.1f} {obj_ref['bass_extension']:6.1f} "
              f"{obj_ref['midrange_flatness']:8.2f} {obj_ref['crossover_smoothness']:9.2f}")

    # Recommendations
    print(f"\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    print(f"\nDesign Suitability:")
    if objectives_opt['bass_extension'] < 55:
        print(f"  ✓ Excellent bass extension for bookshelf (F3 < 55 Hz)")
    elif objectives_opt['bass_extension'] < 60:
        print(f"  ✓ Good bass extension for bookshelf (F3 < 60 Hz)")
    else:
        print(f"  ⚠ Limited bass - consider subwoofer")

    if objectives_opt['midrange_flatness'] < 2.0:
        print(f"  ✓ Excellent midrange flatness - will integrate well with HF horn")
    elif objectives_opt['midrange_flatness'] < 3.0:
        print(f"  ✓ Good midrange flatness - minor EQ may be beneficial")
    else:
        print(f"  ⚠ Midrange could be improved - consider DSP EQ")

    if objectives_opt['crossover_smoothness'] < 1.0:
        print(f"  ✓ Smooth crossover region - clean integration at 2-3 kHz")
    elif objectives_opt['crossover_smoothness'] < 1.5:
        print(f"  ✓ Acceptable crossover region - minimal EQ needed")
    else:
        print(f"  ⚠ Crossover region has ripple - may benefit from DSP")

    print(f"\nCrossover Recommendations:")
    print(f"  • Suggested crossover frequency: 2000-2500 Hz")
    print(f"  • Use 4th-order Linkwitz-Riley for flat summation")
    print(f"  • Consider time-alignment for HF horn")
    print(f"  • HF horn sensitivity: {95 + (objectives_opt['midrange_flatness']*0.5):.0f} dB (estimate)")

    print(f"\nConstruction Notes:")
    print(f"  • Internal dimensions: {((Vb_opt*1000)**(1/3)*100):.0f} mm cube (approx)")
    print(f"  • Port: {np.sqrt(port_area*10000)*10:.0f} mm diameter × {port_length*100:.0f} mm long")
    print(f"  • Use flared port ends to reduce chuffing")
    print(f"  • Add damping material on back wall")

    print()

    return {
        'Vb': Vb_opt,
        'Fb': Fb_opt,
        'port_area': port_area,
        'port_length': port_length,
        'objectives': objectives_opt,
        'sys_params': sys_params,
    }


if __name__ == "__main__":
    result = optimize_bc8fmb51_bookshelf()

    print("=" * 100)
    print("Optimization complete!")
    print("=" * 100)
