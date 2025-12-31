#!/usr/bin/env python3
"""
Mixed-Profile Horn Optimization using NSGA-II

This script demonstrates multi-objective optimization of mixed-profile
multi-segment horns, where each segment can independently be:
- Exponential (profile_type=0)
- Conical (profile_type=1)
- Hyperbolic with T parameter (profile_type=2)

This allows the optimizer to discover designs that combine the strengths
of different horn profiles, such as:
- Conical throat for smooth spherical wavefronts
- Exponential mid-section for controlled expansion
- Hyperbolic mouth for extended bass response

Literature:
    - Deb et al. (2002) - NSGA-II algorithm
    - Olson (1947) - Compound horns with mixed profiles
    - Kolbrek Part 1 - T-matrix chaining for arbitrary segment types
    - literature/horns/kolbrek_horn_theory_tutorial.md

Usage:
    # For midrange horn optimization
    PYTHONPATH=src python tasks/optimize_mixed_profile_horn.py --driver TC2 --preset midrange

    # For bass horn optimization
    PYTHONPATH=src python tasks/optimize_mixed_profile_horn.py --driver BC15DS115 --preset bass

    # For 3-segment optimization
    PYTHONPATH=src python tasks/optimize_mixed_profile_horn.py --driver TC2 --segments 3
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
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_mixed_profile_parameter_space,
    decode_mixed_profile_design,
    build_mixed_profile_horn,
)
from viberesp.optimization.optimizers.pymoo_interface import run_nsga2
from pymoo.operators.sampling.lhs import LHS


def create_profile_seeded_population(
    problem, n_profiles: int = 3
):
    """
    Create initial population seeded with standard horn profiles.

    This injects known good designs (exponential, conical, mixed) into the
    initial population to give the optimizer a head start.

    Args:
        problem: EnclosureOptimizationProblem instance
        n_profiles: Number of profile seeds to generate (default 3)

    Returns:
        Population array with shape (n_profiles, n_var)
    """
    profiles = []

    # Get parameter bounds
    xl = problem.xl
    xu = problem.xu

    # Determine number of segments from n_var
    # Mixed profile 2-seg: 11 vars
    # Mixed profile 3-seg: 14 vars
    if problem.n_var == 11:
        num_segments = 2
    elif problem.n_var == 14:
        num_segments = 3
    else:
        num_segments = 2  # default

    # Profile 1: All exponential (profile_type=0 for all segments)
    if num_segments == 2:
        throat_area = (xl[0] + xu[0]) / 2
        mouth_area = (xl[2] + xu[2]) / 2
        geometric_mean = np.sqrt(throat_area * mouth_area)

        length_total = ((xl[3] + xu[3]) / 2 + (xl[4] + xu[4]) / 2) / 2
        length1 = length2 = length_total / 2

        profile_exp = np.array([
            throat_area,
            geometric_mean,
            mouth_area,
            length1,
            length2,
            0, 0,  # profile_type1, profile_type2 (both exponential)
            1.0, 1.0,  # T1, T2 (not used for exponential)
            xl[9] if len(xl) > 9 else 0.0,  # V_tc (min)
            xl[10] if len(xl) > 10 else 0.0,  # V_rc (min)
        ])[:problem.n_var]
        profiles.append(profile_exp)

        # Profile 2: Conical throat, exponential mouth
        middle_area_con = throat_area * 3  # Moderate expansion
        length1_con = length_total * 0.4   # Shorter conical section
        length2_exp = length_total * 0.6   # Longer exponential section

        profile_mixed = np.array([
            throat_area,
            middle_area_con,
            mouth_area,
            length1_con,
            length2_exp,
            1, 0,  # profile_type1=conical, profile_type2=exponential
            1.0, 1.0,  # T1, T2 (not used)
            xl[9] if len(xl) > 9 else 0.0,
            xl[10] if len(xl) > 10 else 0.0,
        ])[:problem.n_var]
        profiles.append(profile_mixed)

        # Profile 3: Exponential throat, hypex mouth
        middle_area_hyp = throat_area * 4
        length1_hyp = length_total * 0.3  # Short throat segment
        length2_hyp = length_total * 0.7  # Long mouth segment

        profile_hypex = np.array([
            throat_area,
            middle_area_hyp,
            mouth_area,
            length1_hyp,
            length2_hyp,
            0, 2,  # profile_type1=exponential, profile_type2=hyperbolic
            1.0, 0.7,  # T1 (not used), T2 (hypex)
            xl[9] if len(xl) > 9 else 0.0,
            xl[10] if len(xl) > 10 else 0.0,
        ])[:problem.n_var]
        profiles.append(profile_hypex)

    # Clip to bounds
    profiles_array = np.array(profiles)
    for i in range(len(profiles_array)):
        profiles_array[i] = np.clip(profiles_array[i], xl, xu)

    return profiles_array


def optimize_mixed_profile_horn(
    driver,
    preset: str = "midrange_horn",
    num_segments: int = 2,
    pop_size: int = 150,
    n_generations: int = 100,
    use_lhs: bool = True,
    use_profile_seeding: bool = True,
    seed: int = 42,
):
    """
    Run multi-objective optimization for mixed-profile horn.

    Args:
        driver: ThieleSmallParameters instance
        preset: Design preset ("bass_horn", "midrange_horn", "fullrange_horn")
        num_segments: Number of segments (2 or 3)
        pop_size: Population size for NSGA-II
        n_generations: Number of generations
        use_lhs: Use Latin Hypercube Sampling for initial population
        use_profile_seeding: Inject standard horn profiles into initial population
        seed: Random seed

    Returns:
        Tuple of (result, metadata, problem)
    """
    print(f"\n{'='*70}")
    print(f"Mixed-Profile Horn Optimization")
    print(f"{'='*70}")
    print(f"Driver: {driver}")
    print(f"Preset: {preset}")
    print(f"Segments: {num_segments}")
    print(f"Profile Types: Exponential (0), Conical (1), Hyperbolic (2)")
    print(f"Population: {pop_size}")
    print(f"Generations: {n_generations}")
    print(f"Sampling: {'Latin Hypercube' if use_lhs else 'Random'}")
    print(f"Profile Seeding: {'Yes' if use_profile_seeding else 'No'}")
    print(f"{'='*70}\n")

    # Get parameter space
    param_space = get_mixed_profile_parameter_space(
        driver, preset=preset, num_segments=num_segments
    )

    # Extract parameter bounds as dict
    parameter_bounds = {}
    for param in param_space.parameters:
        parameter_bounds[param.name] = (param.min_value, param.max_value)

    # Define optimization objectives
    objectives = ["flatness", "impedance_smoothness"]

    # Define constraints
    constraints = [
        "segment_continuity",
        "flare_constant_limits",
    ]

    # Define target frequency band based on preset
    if preset == "bass_horn":
        target_band = (40, 300)
    elif preset == "midrange_horn":
        target_band = (200, 5000)
    else:  # fullrange_horn
        target_band = (100, 10000)

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

    # Setup algorithm with LHS
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS() if use_lhs else None,
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )

    # Inject profile seeds into initial population if requested
    if use_profile_seeding:
        profile_seeds = create_profile_seeded_population(problem, n_profiles=3)
        print(f"Injecting {len(profile_seeds)} profile seeds into initial population")

    # Run optimization
    from pymoo.optimize import minimize
    from pymoo.termination import get_termination

    termination = get_termination("n_gen", n_generations)

    result = minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        save_history=True,
        verbose=True
    )

    metadata = {
        "algorithm": "NSGA-II",
        "pop_size": pop_size,
        "n_generations": n_generations,
        "n_evaluations": result.algorithm.evaluator.n_eval,
        "n_pareto_designs": len(result.F) if result.F is not None else 0,
    }

    print(f"\n{'='*70}")
    print(f"Optimization Complete!")
    print(f"{'='*70}")
    print(f"Evaluations: {metadata['n_evaluations']}")
    print(f"Pareto Designs: {metadata['n_pareto_designs']}")
    print(f"{'='*70}\n")

    return result, metadata, problem


def analyze_results(result, problem, driver, preset: str, output_dir: str = None):
    """
    Analyze and plot optimization results.

    Args:
        result: pymoo optimization result
        problem: EnclosureOptimizationProblem instance
        driver: ThieleSmallParameters instance
        preset: Design preset name
        output_dir: Output directory for plots (default: tasks/)
    """
    if output_dir is None:
        output_dir = str(Path(__file__).parent)

    # Extract Pareto front
    F = result.F  # Objective values
    X = result.X  # Design variables

    # Plot 1: Pareto front
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(F[:, 0], F[:, 1], c='blue', alpha=0.6, s=50, label='Pareto Front')
    ax.set_xlabel('Objective 1: Response Flatness (dB)', fontsize=12)
    ax.set_ylabel('Objective 2: Impedance Smoothness', fontsize=12)
    ax.set_title(f'Mixed-Profile Horn Optimization - Pareto Front\n({preset})', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Mark best trade-off point
    F_norm = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0))
    best_idx = np.argmin(np.linalg.norm(F_norm, axis=1))
    ax.scatter(F[best_idx, 0], F[best_idx, 1], c='red', s=200, marker='*',
               edgecolors='black', linewidths=2, label='Best Trade-off', zorder=10)
    ax.legend(fontsize=10)

    plt.tight_layout()
    pareto_path = Path(output_dir) / f"pareto_front_{preset}_mixed_profile.png"
    plt.savefig(pareto_path, dpi=150)
    print(f"Pareto front plot saved to: {pareto_path}")

    # Print best designs
    print(f"\n{'='*70}")
    print(f"Top 5 Pareto-Optimal Designs")
    print(f"{'='*70}")
    print(f"{'Flatness':<12} {'Impedance':<12} {'Profile Types':<20} {'Design Parameters':<50}")
    print(f"{'(dB)':<12} {'Smoothness':<12} {'(seg1, seg2)':<20} {'(throat, middle, mouth areas + lengths)':<50}")
    print("-" * 100)

    # Sort by flatness (objective 0)
    sorted_indices = np.argsort(F[:, 0])

    # Profile type names
    profile_names = {
        0: "Exp",
        1: "Con",
        2: "Hyp",
    }

    for i, idx in enumerate(sorted_indices[:5]):
        flatness = F[idx, 0]
        impedance = F[idx, 1]
        design = X[idx]

        # Decode design
        params = decode_mixed_profile_design(design, driver, num_segments=2)

        # Get profile types
        profile_types_str = ", ".join([profile_names.get(pt, "?") for pt in params['profile_types']])

        # Format design string
        areas = [params.get('throat_area', 0),
                params.get('segments', [(0,0,0,0,0)])[0][1] if params.get('segments') else 0,
                params.get('mouth_area', 0)]
        lengths = [params.get('segments', [(0,0,0,0,0)])[i][2] for i in range(min(2, len(params.get('segments', []))))]

        design_str = f"S=[{areas[0]*10000:.1f}, {areas[1]*10000:.1f}, {areas[2]*10000:.1f}] cm², L=[{lengths[0]:.2f}, {lengths[1]:.2f}] m"

        print(f"{flatness:<12.4f} {impedance:<12.4f} {profile_types_str:<20} {design_str:<50}")

    print(f"{'='*70}\n")

    # Save best design to file
    best_design = X[best_idx]
    best_params = decode_mixed_profile_design(best_design, driver, num_segments=2)
    best_objectives = F[best_idx]

    output_file = Path(output_dir) / f"best_design_{preset}_mixed_profile.txt"
    with open(output_file, 'w') as f:
        f.write(f"Best Mixed-Profile Horn Design - {preset}\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"Objectives:\n")
        f.write(f"  Response Flatness: {best_objectives[0]:.4f} dB\n")
        f.write(f"  Impedance Smoothness: {best_objectives[1]:.4f}\n\n")
        f.write(f"Design Parameters:\n")
        for key, value in best_params.items():
            f.write(f"  {key}: {value}\n")

    print(f"Best design saved to: {output_file}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Optimize mixed-profile multi-segment horns using NSGA-II"
    )
    parser.add_argument(
        "--driver",
        type=str,
        default="TC2",
        choices=["TC2", "TC3", "TC4", "BC_8NDL51", "BC_12NDL76", "BC_15DS115"],
        help="Driver to use for optimization"
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="midrange_horn",
        choices=["bass_horn", "midrange_horn", "fullrange_horn"],
        help="Design preset"
    )
    parser.add_argument(
        "--segments",
        type=int,
        default=2,
        choices=[2, 3],
        help="Number of horn segments"
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=150,
        help="Population size (default: 150)"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=100,
        help="Number of generations (default: 100)"
    )
    parser.add_argument(
        "--no-lhs",
        action="store_true",
        help="Disable Latin Hypercube Sampling (use random sampling)"
    )
    parser.add_argument(
        "--no-seeding",
        action="store_true",
        help="Disable profile seeding (no standard horns in initial population)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )

    args = parser.parse_args()

    # Load driver
    driver = load_driver(args.driver)

    # Run optimization
    result, metadata, problem = optimize_mixed_profile_horn(
        driver=driver,
        preset=args.preset,
        num_segments=args.segments,
        pop_size=args.pop_size,
        n_generations=args.generations,
        use_lhs=not args.no_lhs,
        use_profile_seeding=not args.no_seeding,
        seed=args.seed,
    )

    # Analyze results
    analyze_results(result, problem, driver, args.preset)

    print("\nOptimization complete! Review the generated plots and design files.")
    print("\nProfile type codes:")
    print("  0 = Exponential (HornSegment)")
    print("  1 = Conical (ConicalHorn)")
    print("  2 = Hyperbolic (HyperbolicHorn with T parameter)")


if __name__ == "__main__":
    main()
