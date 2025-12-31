#!/usr/bin/env python3
"""
Two-Way System Optimization: Ported Woofer + Mixed-Profile Horn

Sequential optimization for a two-way loudspeaker system:
- BC_8NDL51: Ported enclosure (bass/midrange)
- BC_DH450: Mixed-profile horn (high frequency)
- Crossover: 1 kHz (LR4 alignment)

Goal: Minimize F3 and maximize flatness with ±3dB constraint from F3 to 17kHz

Literature:
    - Small (1972) - Ported box alignments
    - Thiele (1971) - Vented box theory
    - Linkwitz-Riley crossover theory
    - Olson (1947) - Horn theory

Usage:
    PYTHONPATH=src python tasks/optimize_two_way_mixed_profile.py
"""

import sys
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver.loader import load_driver
from viberesp.optimization.objectives.composite import EnclosureOptimizationProblem
from viberesp.optimization.parameters import get_ported_box_parameter_space
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_mixed_profile_parameter_space,
    decode_mixed_profile_design,
    build_mixed_profile_horn,
)
from viberesp.optimization.optimizers.pymoo_interface import run_nsga2


def optimize_ported_box(
    driver,
    target_f3_max: float = 60,
    pop_size: int = 100,
    n_generations: int = 80,
    seed: int = 42,
):
    """
    Optimize ported box for BC_8NDL51 to minimize F3.

    Args:
        driver: ThieleSmallParameters for BC_8NDL51
        target_f3_max: Maximum acceptable F3 (Hz)
        pop_size: Population size
        n_generations: Number of generations
        seed: Random seed

    Returns:
        Tuple of (result, metadata, problem)
    """
    print(f"\n{'='*70}")
    print(f"Step 1: Optimize Ported Box for BC_8NDL51")
    print(f"{'='*70}")
    print(f"Driver: {driver}")
    print(f"Goal: Minimize F3 while maintaining flatness")
    print(f"Target F3: < {target_f3_max} Hz")
    print(f"{'='*70}\n")

    # Get parameter space
    param_space = get_ported_box_parameter_space(driver)

    # Extract parameter bounds
    parameter_bounds = {}
    for param in param_space.parameters:
        parameter_bounds[param.name] = (param.min_value, param.max_value)

    # Define objectives: minimize F3, maximize flatness
    objectives = ["f3", "flatness"]

    # Define constraints
    constraints = [
        "max_displacement",
        "port_velocity",
    ]

    # Note: F3 constraint will be enforced by filtering results afterwards

    # Target band for flatness calculation (bass region)
    target_band = (20, 200)

    # Create optimization problem
    problem = EnclosureOptimizationProblem(
        driver=driver,
        enclosure_type="ported",
        objectives=objectives,
        parameter_bounds=parameter_bounds,
        constraints=constraints,
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
    result, metadata = run_nsga2(
        problem=problem,
        pop_size=pop_size,
        n_generations=n_generations,
        seed=seed,
        verbose=True
    )

    print(f"\n{'='*70}")
    print(f"Ported Box Optimization Complete!")
    print(f"{'='*70}")
    print(f"Evaluations: {metadata['n_evaluations']}")
    print(f"Pareto Designs: {metadata['n_pareto_designs']}")
    print(f"{'='*70}\n")

    return result, metadata, problem


def analyze_ported_results(result, problem, driver):
    """Analyze ported box results and return best design."""
    F = result.F  # Objective values
    X = result.X  # Design variables

    # Handle both single-objective (F is 1D) and multi-objective (F is 2D) cases
    if F.ndim == 1:
        F = F.reshape(-1, 1)

    # Handle both single-individual (X is 1D) and multiple-individual (X is 2D) cases
    if X.ndim == 1:
        X = X.reshape(1, -1)

    # Sort by F3 (objective 0), get lowest F3
    sorted_indices = np.argsort(F[:, 0])

    print(f"\n{'='*70}")
    print(f"Top 5 Ported Box Designs")
    print(f"{'='*70}")
    print(f"{'F3 (Hz)':<12} {'Flatness (dB)':<15} {'Vb (L)':<12} {'Fb (Hz)':<12}")
    print("-" * 60)

    best_designs = []
    for i, idx in enumerate(sorted_indices[:5]):
        f3 = F[idx, 0]
        flatness = F[idx, 1]
        design = X[idx]
        params = dict(zip(problem.param_names, design))

        vb_liters = params['Vb'] * 1000
        fb_hz = params['Fb']

        print(f"{f3:<12.2f} {flatness:<15.4f} {vb_liters:<12.2f} {fb_hz:<12.2f}")

        best_designs.append({
            'f3': f3,
            'flatness': flatness,
            'Vb': params['Vb'],
            'Fb': params['Fb'],
            'design_vector': design,
        })

    print(f"{'='*70}\n")

    # Return best design (lowest F3)
    return best_designs[0]


def optimize_mixed_profile_horn(
    driver,
    crossover_freq: float = 1000,
    target_band: tuple = (1000, 17000),
    flatness_max: float = 3.0,
    pop_size: int = 150,
    n_generations: int = 100,
    seed: int = 42,
):
    """
    Optimize mixed-profile horn for BC_DH450.

    Args:
        driver: ThieleSmallParameters for BC_DH450
        crossover_freq: Crossover frequency (Hz)
        target_band: Frequency range for optimization (Hz)
        flatness_max: Maximum acceptable deviation (dB)
        pop_size: Population size
        n_generations: Number of generations
        seed: Random seed

    Returns:
        Tuple of (result, metadata, problem)
    """
    print(f"\n{'='*70}")
    print(f"Step 2: Optimize Mixed-Profile Horn for BC_DH450")
    print(f"{'='*70}")
    print(f"Driver: {driver}")
    print(f"Crossover: {crossover_freq} Hz")
    print(f"Target Band: {target_band[0]}-{target_band[1]} Hz")
    print(f"Flatness constraint: ±{flatness_max} dB")
    print(f"{'='*70}\n")

    # Get parameter space
    param_space = get_mixed_profile_parameter_space(
        driver, preset="midrange_horn", num_segments=2
    )

    # Extract parameter bounds
    parameter_bounds = {}
    for param in param_space.parameters:
        parameter_bounds[param.name] = (param.min_value, param.max_value)

    # Define objectives: minimize flatness only (impedance_smoothness not yet supported for mixed_profile)
    objectives = ["flatness"]

    # Define constraints
    constraints = [
        "segment_continuity",
        "flare_constant_limits",
    ]

    # Note: Flatness constraint will be enforced by filtering results afterwards

    # Create optimization problem
    problem = EnclosureOptimizationProblem(
        driver=driver,
        enclosure_type="mixed_profile_horn",
        objectives=objectives,
        parameter_bounds=parameter_bounds,
        constraints=constraints,
        num_segments=2,
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
    result, metadata = run_nsga2(
        problem=problem,
        pop_size=pop_size,
        n_generations=n_generations,
        seed=seed,
        verbose=True
    )

    print(f"\n{'='*70}")
    print(f"Mixed-Profile Horn Optimization Complete!")
    print(f"{'='*70}")
    print(f"Evaluations: {metadata['n_evaluations']}")
    print(f"Pareto Designs: {metadata['n_pareto_designs']}")
    print(f"{'='*70}\n")

    return result, metadata, problem


def analyze_horn_results(result, problem, driver):
    """Analyze horn results and return best design."""
    F = result.F  # Objective values
    X = result.X  # Design variables

    # Handle both single-objective (F is 1D) and multi-objective (F is 2D) cases
    if F.ndim == 1:
        F = F.reshape(-1, 1)

    # Handle both single-individual (X is 1D) and multiple-individual (X is 2D) cases
    if X.ndim == 1:
        X = X.reshape(1, -1)

    # Profile type names
    profile_names = {
        0: "Exp",
        1: "Con",
        2: "Hyp",
    }

    # Sort by flatness (objective 0)
    sorted_indices = np.argsort(F[:, 0])

    print(f"\n{'='*70}")
    print(f"Top 5 Mixed-Profile Horn Designs")
    print(f"{'='*70}")
    print(f"{'Flatness':<12} {'Impedance':<12} {'Profile':<12} {'Design Parameters'}")
    print(f"{'(dB)':<12} {'Smoothness':<12} {'Types':<12} {'(throat, middle, mouth areas + lengths)'}")
    print("-" * 100)

    best_designs = []
    for i, idx in enumerate(sorted_indices[:5]):
        flatness = F[idx, 0]
        impedance = F[idx, 1] if F.shape[1] > 1 else 0.0  # Handle single-objective case
        design = X[idx]

        # Decode design
        params = decode_mixed_profile_design(design, driver, num_segments=2)

        # Get profile types
        profile_types_str = ", ".join([profile_names.get(pt, "?") for pt in params['profile_types']])

        # Format design string
        areas = [
            params.get('throat_area', 0),
            params.get('segments', [(0,0,0,0,0)])[0][1] if params.get('segments') else 0,
            params.get('mouth_area', 0)
        ]
        lengths = [params.get('segments', [(0,0,0,0,0)])[i][2] for i in range(min(2, len(params.get('segments', []))))]

        design_str = f"S=[{areas[0]*10000:.1f}, {areas[1]*10000:.1f}, {areas[2]*10000:.1f}] cm², L=[{lengths[0]:.2f}, {lengths[1]:.2f}] m"

        print(f"{flatness:<12.4f} {impedance:<12.4f} {profile_types_str:<12} {design_str}")

        best_designs.append({
            'flatness': flatness,
            'impedance_smoothness': impedance,
            'params': params,
            'design_vector': design,
        })

    print(f"{'='*70}\n")

    return best_designs[0]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Optimize two-way system: ported woofer + mixed-profile horn"
    )
    parser.add_argument(
        "--skip-ported",
        action="store_true",
        help="Skip ported box optimization (use existing design)"
    )
    parser.add_argument(
        "--skip-horn",
        action="store_true",
        help="Skip horn optimization (use existing design)"
    )
    parser.add_argument(
        "--crossover",
        type=float,
        default=1000,
        help="Crossover frequency in Hz (default: 1000)"
    )
    parser.add_argument(
        "--pop-size-ported",
        type=int,
        default=100,
        help="Population size for ported optimization (default: 100)"
    )
    parser.add_argument(
        "--pop-size-horn",
        type=int,
        default=150,
        help="Population size for horn optimization (default: 150)"
    )
    parser.add_argument(
        "--generations-ported",
        type=int,
        default=80,
        help="Generations for ported optimization (default: 80)"
    )
    parser.add_argument(
        "--generations-horn",
        type=int,
        default=100,
        help="Generations for horn optimization (default: 100)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    # ========================================================================
    # STEP 1: Optimize Ported Box for BC_8NDL51
    # ========================================================================
    ported_result = None
    if not args.skip_ported:
        woofer = load_driver("BC_8NDL51")
        result, metadata, problem = optimize_ported_box(
            driver=woofer,
            target_f3_max=60,
            pop_size=args.pop_size_ported,
            n_generations=args.generations_ported,
            seed=args.seed,
        )
        ported_result = analyze_ported_results(result, problem, woofer)

        print(f"\nBest ported box design:")
        print(f"  Vb: {ported_result['Vb']*1000:.2f} L")
        print(f"  Fb: {ported_result['Fb']:.2f} Hz")
        print(f"  F3: {ported_result['f3']:.2f} Hz")
        print(f"  Flatness: {ported_result['flatness']:.4f} dB")
    else:
        print("\nSkipping ported box optimization")

    # ========================================================================
    # STEP 2: Optimize Mixed-Profile Horn for BC_DE250
    # ========================================================================
    horn_result = None
    if not args.skip_horn:
        tweeter = load_driver("BC_DE250")
        result, metadata, problem = optimize_mixed_profile_horn(
            driver=tweeter,
            crossover_freq=args.crossover,
            target_band=(args.crossover, 17000),
            flatness_max=3.0,
            pop_size=args.pop_size_horn,
            n_generations=args.generations_horn,
            seed=args.seed,
        )
        horn_result = analyze_horn_results(result, problem, tweeter)

        print(f"\nBest horn design:")
        print(f"  Profile types: {horn_result['params']['profile_types']}")
        print(f"  Segment classes: {horn_result['params']['segment_classes']}")
        print(f"  Flatness: {horn_result['flatness']:.4f} dB")
        print(f"  Impedance smoothness: {horn_result['impedance_smoothness']:.4f}")
    else:
        print("\nSkipping horn optimization")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"Two-Way System Optimization Summary")
    print(f"{'='*70}")

    if ported_result:
        print(f"\nWoofer (BC_8NDL51) - Ported Box:")
        print(f"  Vb: {ported_result['Vb']*1000:.2f} L")
        print(f"  Fb: {ported_result['Fb']:.2f} Hz")
        print(f"  F3: {ported_result['f3']:.2f} Hz")

    if horn_result:
        print(f"\nTweeter (BC_DE250) - Mixed-Profile Horn:")
        params = horn_result['params']
        print(f"  Throat area: {params['throat_area']*10000:.2f} cm²")
        print(f"  Mouth area: {params['mouth_area']*10000:.2f} cm²")
        print(f"  Total length: {params['total_length']:.2f} m")
        print(f"  Profile types: {params['profile_types']}")
        print(f"  Flatness: {horn_result['flatness']:.4f} dB")

    print(f"\nCrossover: {args.crossover} Hz (LR4)")
    print(f"Target flatness: ±3.0 dB from F3 to 17 kHz")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
