#!/usr/bin/env python3
"""
Optimize BC_15DS115 ported box for maximally flat subwoofer response.

This script uses scipy's differential evolution to find the optimal Vb and Fb
for the BC_15DS115 driver, specifically targeting subwoofer applications.

Optimization objectives:
1. Bass region flatness (20-80 Hz) - Primary objective
2. Crossover region flatness (80-120 Hz) - Integration with mains
3. Passband ripple minimization (40-100 Hz) - Smoothness
4. Deep bass extension (F3) - Lower is better

Literature:
    - Thiele (1971) - Vented box alignments
    - Small (1973) - Butterworth maximally flat response
    - literature/thiele_small/thiele_1971_vented_boxes.md
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from scipy.optimize import differential_evolution, minimize
from datetime import datetime

from viberesp.driver.bc_drivers import get_bc_15ds115
from viberesp.optimization.objectives.subwoofer import (
    calculate_subwoofer_objectives,
    objective_subwoofer_flatness,
    objective_b4_alignment_error,
    evaluate_subwoofer_designs,
    print_subwoofer_comparison,
    SubwooferObjectives,
)


def optimize_bc15ds115_flatness():
    """
    Optimize BC_15DS115 for maximally flat subwoofer response.

    Uses differential evolution to find optimal Vb and Fb.

    Returns:
        dict: Optimization results with design parameters and objectives
    """
    # Get driver
    driver = get_bc_15ds115()

    print("\n" + "=" * 100)
    print("BC_15DS115 SUBWOOFER OPTIMIZATION")
    print("Maximally Flat Response Design")
    print("=" * 100)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\nDriver Parameters:")
    print(f"  Fs: {driver.F_s:.2f} Hz")
    print(f"  Vas: {driver.V_as*1000:.1f} L")
    print(f"  Qts: {driver.Q_ts:.3f} (VERY LOW - high BL motor)")
    print(f"  BL: {driver.BL:.1f} T·m")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")
    print(f"  Le: {driver.L_e*1000:.1f} mH")

    # Define parameter bounds
    # Vb: 40L to 400L (practical range for 15" subwoofer)
    # Fb: 20 Hz to 40 Hz (subwoofer tuning range)
    vb_min, vb_max = 0.040, 0.400  # m³
    fb_min, fb_max = 20.0, 40.0     # Hz

    bounds = [(vb_min, vb_max), (fb_min, fb_max)]

    print(f"\nOptimization Bounds:")
    print(f"  Vb: {vb_min*1000:.0f} - {vb_max*1000:.0f} L")
    print(f"  Fb: {fb_min:.0f} - {fb_max:.0f} Hz")

    # Objective function wrapper
    def objective(x):
        """Objective function for minimization."""
        Vb, Fb = x[0], x[1]
        return objective_subwoofer_flatness(np.array([Vb, Fb]), driver)

    # Run differential evolution optimization
    print(f"\nRunning optimization...")
    print(f"Algorithm: Differential Evolution")
    print(f"Population size: 15")
    print(f"Max generations: 30")

    result = differential_evolution(
        objective,
        bounds,
        strategy='best1bin',
        maxiter=30,
        popsize=15,
        tol=1e-6,
        mutation=0.8,
        recombination=0.9,
        seed=42,
        disp=True,
    )

    # Extract optimal design
    Vb_opt, Fb_opt = result.x[0], result.x[1]
    objective_value = result.fun

    print(f"\nOptimization converged: {result.success}")
    print(f"Final objective value: {objective_value:.4f}")

    # Calculate all objectives for optimal design
    objectives_opt = calculate_subwoofer_objectives(Vb_opt, Fb_opt, driver)

    # Compare with reference designs
    print(f"\nComparing with reference designs...")

    reference_designs = [
        ("Compact (60L, 34Hz)", 0.060, 34.0),
        ("Small (80L, 33Hz)", 0.080, 33.0),
        ("Medium (120L, 31Hz)", 0.120, 31.0),
        ("Large (150L, 30Hz)", 0.150, 30.0),
        ("Very Large (180L, 29Hz)", 0.180, 29.0),
        ("B4 Alignment (Vas, Fs)", driver.V_as, driver.F_s),
        ("Extra Large (254L, 28Hz)", 0.254, 28.0),
        ("Huge (300L, 27Hz)", 0.300, 27.0),
        ("Optimal Design", Vb_opt, Fb_opt),
    ]

    results = evaluate_subwoofer_designs(driver, reference_designs)

    # Print comparison
    print_subwoofer_comparison(results)

    # Print detailed analysis of optimal design
    print("=" * 100)
    print("OPTIMAL DESIGN ANALYSIS")
    print("=" * 100)

    print(f"\nOptimal Parameters:")
    print(f"  Vb: {Vb_opt*1000:.1f} L")
    print(f"  Fb: {Fb_opt:.2f} Hz")

    # Calculate system parameters
    from viberesp.enclosure.ported_box import (
        calculate_optimal_port_dimensions,
        calculate_ported_box_system_parameters,
    )

    port_area, port_length, v_max = calculate_optimal_port_dimensions(
        driver, Vb_opt, Fb_opt
    )

    sys_params = calculate_ported_box_system_parameters(
        driver, Vb_opt, Fb_opt, port_area, port_length
    )

    print(f"\nSystem Parameters:")
    print(f"  Alpha (α): {sys_params.alpha:.2f}")
    print(f"  Tuning ratio (h): {sys_params.h:.2f}")
    print(f"  F3: {sys_params.F3:.2f} Hz")

    print(f"\nPort Dimensions:")
    print(f"  Port area: {port_area*10000:.1f} cm²")
    print(f"  Port length: {port_length*100:.1f} cm")
    print(f"  Max port velocity: {v_max:.2f} m/s")

    # Calculate B4 alignment error
    b4_error = objective_b4_alignment_error(np.array([Vb_opt, Fb_opt]), driver)
    print(f"\nAlignment Analysis:")
    print(f"  Deviation from B4: {b4_error:.2%}")

    # Determine alignment type
    if sys_params.alpha > 1.2:
        alignment_type = "Larger than B4 (box > Vas)"
    elif sys_params.alpha < 0.8:
        alignment_type = "Smaller than B4 (box < Vas)"
    else:
        alignment_type = "Close to B4 alignment"

    print(f"  Alignment type: {alignment_type}")

    # Performance objectives
    print(f"\nPerformance Objectives:")
    print(f"  Bass flatness (20-80 Hz):     σ = {objectives_opt.bass_flatness:.2f} dB")
    print(f"  Crossover flatness (80-120 Hz): σ = {objectives_opt.crossover_flatness:.2f} dB")
    print(f"  Passband ripple (40-100 Hz):   Δ = {objectives_opt.passband_ripple:.2f} dB")
    print(f"  Deep bass extension (F3):      {objectives_opt.f3:.2f} Hz")
    print(f"  Max SPL (40-80 Hz):           {objectives_opt.max_spl_bass:.1f} dB @ 2.83V, 1m")

    # Ranking among reference designs
    rankings = {}
    for category, key, reverse in [
        ("F3", "f3", False),  # Lower is better
        ("Bass Flatness", "bass_flatness", False),  # Lower is better
        ("Crossover Flatness", "crossover_flatness", False),  # Lower is better
        ("Passband Ripple", "passband_ripple", False),  # Lower is better
        ("Max SPL", "max_spl_bass", True),  # Higher is better
    ]:
        sorted_designs = sorted(
            results.items(),
            key=lambda x: getattr(x[1], key),
            reverse=reverse
        )
        rank = [i for i, (name, _) in enumerate(sorted_designs) if name == "Optimal Design"][0] + 1
        rankings[category] = rank

    print(f"\nRankings (out of {len(reference_designs)} designs):")
    for category, rank in rankings.items():
        print(f"  {category}: {rank}/{len(reference_designs)}")

    # Calculate frequency response for optimal design
    print(f"\nFrequency Response (select points):")
    frequencies = np.logspace(np.log10(20), np.log10(200), 50)

    from viberesp.enclosure.ported_box import calculate_spl_ported_transfer_function

    for freq in [20, 30, 40, 50, 60, 80, 100, 150, 200]:
        spl = calculate_spl_ported_transfer_function(
            frequency=freq,
            driver=driver,
            Vb=Vb_opt,
            Fb=Fb_opt,
            include_hf_rolloff=True,
        )
        print(f"  {freq:3.0f} Hz: {spl:6.1f} dB")

    # Recommendations
    print(f"\nRecommendations:")
    if objectives_opt.bass_flatness < 2.0:
        print(f"  ✓ Excellent bass flatness - suitable for critical listening")
    elif objectives_opt.bass_flatness < 3.0:
        print(f"  ✓ Good bass flatness - suitable for most applications")
    else:
        print(f"  ⚠ Bass flatness could be improved - consider larger box")

    if objectives_opt.crossover_flatness < 1.0:
        print(f"  ✓ Excellent crossover region - will integrate well with mains")
    elif objectives_opt.crossover_flatness < 1.5:
        print(f"  ✓ Good crossover region - minor EQ may be needed")
    else:
        print(f"  ⚠ Crossover region has ripple - consider bi-amping or DSP")

    if objectives_opt.f3 < 30:
        print(f"  ✓ Excellent deep bass extension - true subwoofer performance")
    elif objectives_opt.f3 < 35:
        print(f"  ✓ Good deep bass extension - adequate for most content")
    else:
        print(f"  ⚠ Limited deep bass - more suitable for mid-bass modules")

    print()

    return {
        'Vb': Vb_opt,
        'Fb': Fb_opt,
        'port_area': port_area,
        'port_length': port_length,
        'objectives': objectives_opt,
        'sys_params': sys_params,
        'b4_error': b4_error,
        'rankings': rankings,
    }


if __name__ == "__main__":
    result = optimize_bc15ds115_flatness()

    print("=" * 100)
    print("Optimization complete!")
    print("=" * 100)
