#!/usr/bin/env python3
"""
Bass Horn Optimization - Optimized for Low-Frequency Extension

This script optimizes mixed-profile horns for bass extension by minimizing F3
and maximizing sensitivity, rather than just maximizing flatness.

Objectives:
- f3: Minimize -3 dB frequency (for bass extension)
- max_spl: Maximize average SPL (for sensitivity)

This creates horns with proper bass response rather than flat midrange.
"""

import sys
import os
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver.loader import load_driver
from viberesp.optimization.objectives.composite import EnclosureOptimizationProblem
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_mixed_profile_parameter_space,
    decode_mixed_profile_design,
    build_mixed_profile_horn,
)
from viberesp.optimization.optimizers.pymoo_interface import run_nsga2
from pymoo.operators.sampling.lhs import LHS


def optimize_bass_horn_extension(
    driver,
    num_segments=2,
    pop_size=100,
    n_generations=50,
):
    """
    Optimize mixed-profile horn for bass extension.

    Args:
        driver: ThieleSmallParameters instance
        num_segments: Number of horn segments (2 or 3)
        pop_size: Population size
        n_generations: Number of generations

    Returns:
        result: Optimization result from pymoo
        metadata: Dictionary with optimization info
        problem: Optimization problem instance
    """
    print(f"\n{'='*70}")
    print(f"Bass Horn Extension Optimization")
    print(f"{'='*70}")
    print(f"Driver: {driver}")
    print(f"Segments: {num_segments}")
    print(f"Objectives: f3 (minimize), efficiency (maximize)")
    print(f"{'='*70}\n")

    # Get parameter space
    param_space = get_mixed_profile_parameter_space(driver, num_segments=num_segments)

    # Convert to parameter bounds dict
    parameter_bounds = {}
    for param in param_space.parameters:
        parameter_bounds[param.name] = (param.min_value, param.max_value)

    # Define objectives optimized for BASS
    # f3: minimize -3 dB frequency (lower is better for bass)
    # efficiency: maximize acoustic efficiency (higher SPL)
    objectives = ["f3", "efficiency"]

    # Define constraints
    constraints = [
        "segment_continuity",
        "flare_constant_limits",
    ]

    # Wider frequency band for bass horns
    target_band = (30, 300)

    # Create optimization problem
    problem = EnclosureOptimizationProblem(
        driver=driver,
        enclosure_type="mixed_profile_horn",
        objectives=objectives,
        parameter_bounds=parameter_bounds,
        constraints=constraints,
        num_segments=num_segments,
        target_band=target_band,
    )

    print(f"Optimization Problem:")
    print(f"  Objectives: {', '.join(objectives)}")
    print(f"  Constraints: {', '.join(constraints)}")
    print(f"  Target Band: {target_band[0]}-{target_band[1]} Hz")
    print(f"  Variables: {problem.n_var}")
    print(f"  Objectives: {problem.n_obj}")
    print(f"  Constraints: {problem.n_constr}")
    print()

    # Run optimization
    result, opt_metadata = run_nsga2(
        problem=problem,
        pop_size=pop_size,
        n_generations=n_generations,
        seed=42,
        verbose=True,
    )

    # Compile metadata
    metadata = {
        "driver_name": driver.name if hasattr(driver, 'name') else "unknown",
        "num_segments": num_segments,
        "objectives": objectives,
        "target_band": target_band,
        "pop_size": pop_size,
        "n_generations": n_generations,
        "pareto_size": len(result.F),
        "opt_metadata": opt_metadata,
    }

    return result, metadata, problem


def analyze_results(result, problem, driver):
    """Analyze and display optimization results."""
    print(f"\n{'='*70}")
    print(f"Optimization Results - Bass Extension")
    print(f"{'='*70}\n")

    X = result.X
    F = result.F

    print(f"Total Pareto-optimal designs: {len(X)}\n")

    # Filter out invalid designs (penalty values)
    # F3 penalty: 1e10, Efficiency penalty: -1000
    valid_mask = (F[:, 0] < 1e9) & (F[:, 1] > -100)
    X_valid = X[valid_mask]
    F_valid = F[valid_mask]

    print(f"Valid designs (after filtering): {len(X_valid)}\n")

    if len(X_valid) == 0:
        print("No valid designs found! All designs violated constraints or failed evaluation.")
        return None

    # Sort valid designs by F3 (lowest first)
    f3_values = F_valid[:, 0]
    sorted_indices = np.argsort(f3_values)

    print(f"Top 10 Designs (sorted by F3 - lowest cutoff frequency):")
    print(f"{'Rank':<6} {'F3 (Hz)':<12} {'Efficiency (%)':<18} {'Profile':<20} {'Design'}")
    print(f"{'-'*70}")

    for rank, idx in enumerate(sorted_indices[:10], 1):
        design_vector = X_valid[idx]
        f3 = F_valid[idx, 0]
        efficiency = -F_valid[idx, 1] * 100  # Convert to positive percentage

        # Decode design
        params = decode_mixed_profile_design(design_vector, driver, num_segments=2)

        # Get profile types
        profile_types = params.get('profile_types', [0, 0])
        profile_names = ['Exp', 'Con', 'Hyp']
        profile_str = ', '.join([profile_names[pt] for pt in profile_types])

        # Design summary
        design_str = f"S=[{params['throat_area']*10000:.0f}, {params['mouth_area']*10000:.0f}] cm², L={params['total_length']:.2f}m"

        print(f"{rank:<6} {f3:<12.1f} {efficiency:<18.3f} {profile_str:<20} {design_str}")

    print()

    # Find best compromise (lowest F3 with good efficiency)
    # Normalize objectives (both minimization, so we want low values)
    f3_norm = (F_valid[:, 0] - F_valid[:, 0].min()) / (F_valid[:, 0].max() - F_valid[:, 0].min() + 1e-6)
    eff_norm = (F_valid[:, 1] - F_valid[:, 1].min()) / (F_valid[:, 1].max() - F_valid[:, 1].min() + 1e-6)

    # Compromise score (weighted towards F3)
    compromise = 0.7 * f3_norm + 0.3 * eff_norm
    best_idx = np.argmin(compromise)

    print(f"\nBest Compromise Design:")
    print(f"  F3: {F_valid[best_idx, 0]:.1f} Hz")
    print(f"  Efficiency: {-F_valid[best_idx, 1] * 100:.3f}%")
    print(f"  Parameters: {X_valid[best_idx]}")

    # Save best design
    output_dir = Path(__file__).parent
    output_file = output_dir / "best_design_bass_extension_mixed_profile.txt"

    with open(output_file, 'w') as f:
        f.write(f"Best Mixed-Profile Bass Horn Design - Extension Optimized\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"Objectives:\n")
        f.write(f"  F3: {F_valid[best_idx, 0]:.1f} Hz\n")
        f.write(f"  Efficiency: {-F_valid[best_idx, 1] * 100:.3f}%\n\n")

        params = decode_mixed_profile_design(X_valid[best_idx], driver, num_segments=2)
        f.write(f"Parameters:\n")
        for key, value in params.items():
            if isinstance(value, float):
                f.write(f"  {key}: {value:.4f}\n")
            else:
                f.write(f"  {key}: {value}\n")

    print(f"\nBest design saved to: {output_file}")

    return best_idx


def main():
    """Main entry point."""
    # Load BC_18RBX100
    driver = load_driver("BC_18RBX100")

    # Run optimization
    result, metadata, problem = optimize_bass_horn_extension(
        driver=driver,
        num_segments=2,
        pop_size=100,
        n_generations=50,
    )

    # Analyze results
    best_idx = analyze_results(result, problem, driver)

    print(f"\nOptimization complete! Review the generated design file.")


if __name__ == "__main__":
    main()
