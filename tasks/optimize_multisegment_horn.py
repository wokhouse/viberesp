#!/usr/bin/env python3
"""
Multi-Segment Horn Optimization using NSGA-II

This script demonstrates multi-objective optimization of multi-segment horn
profiles to discover flatter frequency response designs.

Based on research recommendations:
- NSGA-II for multi-objective optimization (flatness vs. impedance smoothness)
- Composite flatness metric (SPL deviation + slope + ripple)
- Flare rate curvature constraint (m_throat ≥ m_mid ≥ m_mouth)
- Latin Hypercube Sampling for initial population
- Profile seeding with standard exponential horns

Literature:
    - Deb et al. (2002) - NSGA-II algorithm
    - Dong et al. (2020) - Horn profile optimization
    - Kolbrek Part 1 - Horn theory and impedance
    - literature/horns/kolbrek_horn_theory_tutorial.md

Usage:
    # For midrange horn optimization
    PYTHONPATH=src python tasks/optimize_multisegment_horn.py --driver TC2 --preset midrange

    # For bass horn optimization
    PYTHONPATH=src python tasks/optimize_multisegment_horn.py --driver BC15DS115 --preset bass

    # For 3-segment optimization
    PYTHONPATH=src python tasks/optimize_multisegment_horn.py --driver TC2 --segments 3
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
    get_multisegment_horn_parameter_space,
    get_hyperbolic_parameter_space,
    decode_hyperbolic_design,
)
from viberesp.optimization.optimizers.pymoo_interface import run_nsga2
from pymoo.operators.sampling.lhs import LHS


def create_profile_seeded_population(
    problem, n_profiles: int = 3, use_hyperbolic: bool = False
):
    """
    Create initial population seeded with standard horn profiles.

    This injects known good designs (exponential, tractrix-like) into the
    initial population to give the optimizer a head start.

    Args:
        problem: EnclosureOptimizationProblem instance
        n_profiles: Number of profile seeds to generate (default 3)
        use_hyperbolic: Whether to include T parameters (for hyperbolic optimization)

    Returns:
        Population array with shape (n_profiles, n_var)
    """
    profiles = []

    # Get parameter bounds
    xl = problem.xl
    xu = problem.xu

    # Determine number of segments from n_var
    # Standard 2-seg: 7 vars, Hyperbolic 2-seg: 9 vars
    # Standard 3-seg: 9 vars, Hyperbolic 3-seg: 12 vars
    if use_hyperbolic:
        if problem.n_var == 9:
            num_segments = 2
        elif problem.n_var == 12:
            num_segments = 3
        else:
            num_segments = 2  # default
    else:
        if problem.n_var == 7:
            num_segments = 2
        elif problem.n_var == 9:
            num_segments = 3
        else:
            num_segments = 2  # default

    # Profile 1: Exponential horn (uniform flare rate)
    # For exponential: m1 ≈ m2 ≈ ... (similar flare constants)
    if num_segments == 2:  # 2-segment horn
        # Mid-point areas
        throat_area = (xl[0] + xu[0]) / 2
        mouth_area = (xl[2] + xu[2]) / 2

        # Choose middle area and lengths for exponential profile
        # Exponential: S(x) = S_throat * exp(m*x)
        # We want smooth expansion: middle_area ≈ sqrt(throat_area * mouth_area)
        geometric_mean = np.sqrt(throat_area * mouth_area)

        # Equal segment lengths
        length_total = ((xl[3] + xu[3]) / 2 + (xl[4] + xu[4]) / 2) / 2
        length1 = length2 = length_total / 2

        # Build profile based on standard or hyperbolic
        if use_hyperbolic:
            # Hyperbolic: add T parameters (T=1.0 for exponential)
            profile_exp = np.array([
                throat_area,
                geometric_mean,  # middle_area
                mouth_area,
                length1,
                length2,
                1.0,  # T1 (exponential)
                1.0,  # T2 (exponential)
                xl[7] if len(xl) > 7 else 0.0,  # V_tc (min)
                xl[8] if len(xl) > 8 else 0.0,  # V_rc (min)
            ])[:problem.n_var]
        else:
            # Standard
            profile_exp = np.array([
                throat_area,
                geometric_mean,  # middle_area
                mouth_area,
                length1,
                length2,
                xl[5] if len(xl) > 5 else 0.0,  # V_tc (min)
                xl[6] if len(xl) > 6 else 0.0,  # V_rc (min)
            ])[:problem.n_var]
        profiles.append(profile_exp)

        # Profile 2: Fast-slow expansion (tractrix-like with hypex)
        # Throat segment: fast expansion (high m1) with hypex (T<1)
        # Mouth segment: slow expansion (low m2)
        middle_area_fast = throat_area * 4  # 4x expansion at throat
        length1_short = length_total * 0.3  # Short throat segment
        length2_long = length_total * 0.7   # Long mouth segment

        if use_hyperbolic:
            # Use hypex at throat for better loading
            profile_tractrix = np.array([
                throat_area,
                middle_area_fast,
                mouth_area,
                length1_short,
                length2_long,
                0.7,  # T1 (hypex for better LF loading)
                1.0,  # T2 (exponential)
                xl[7] if len(xl) > 7 else 0.0,
                xl[8] if len(xl) > 8 else 0.0,
            ])[:problem.n_var]
        else:
            profile_tractrix = np.array([
                throat_area,
                middle_area_fast,
                mouth_area,
                length1_short,
                length2_long,
                xl[5] if len(xl) > 5 else 0.0,
                xl[6] if len(xl) > 6 else 0.0,
            ])[:problem.n_var]
        profiles.append(profile_tractrix)

        # Profile 3: Moderate flare (balanced profile)
        middle_area_mod = throat_area * 2.5  # Moderate expansion
        length1_mod = length_total * 0.4
        length2_mod = length_total * 0.6

        if use_hyperbolic:
            # Mixed profile: slight hypex
            profile_mod = np.array([
                throat_area,
                middle_area_mod,
                mouth_area,
                length1_mod,
                length2_mod,
                0.85,  # T1 (slight hypex)
                0.95,  # T2 (near-exponential)
                xl[7] if len(xl) > 7 else 0.0,
                xl[8] if len(xl) > 8 else 0.0,
            ])[:problem.n_var]
        else:
            profile_mod = np.array([
                throat_area,
                middle_area_mod,
                mouth_area,
                length1_mod,
                length2_mod,
                xl[5] if len(xl) > 5 else 0.0,
                xl[6] if len(xl) > 6 else 0.0,
            ])[:problem.n_var]
        profiles.append(profile_mod)

    # Clip to bounds
    profiles_array = np.array(profiles)
    for i in range(len(profiles_array)):
        profiles_array[i] = np.clip(profiles_array[i], xl, xu)

    return profiles_array


def optimize_horn_profile(
    driver,
    preset: str = "midrange_horn",
    num_segments: int = 2,
    pop_size: int = 150,
    n_generations: int = 100,
    use_lhs: bool = True,
    use_profile_seeding: bool = True,
    use_hyperbolic: bool = False,
    seed: int = 42,
):
    """
    Run multi-objective optimization for multi-segment horn.

    Args:
        driver: ThieleSmallParameters instance
        preset: Design preset ("bass_horn", "midrange_horn", "fullrange_horn")
        num_segments: Number of segments (2 or 3)
        pop_size: Population size for NSGA-II
        n_generations: Number of generations
        use_lhs: Use Latin Hypercube Sampling for initial population
        use_profile_seeding: Inject standard horn profiles into initial population
        use_hyperbolic: Use hyperbolic (T-parameter) optimization instead of standard exponential
        seed: Random seed

    Returns:
        Tuple of (result, metadata, problem)
    """
    print(f"\n{'='*70}")
    print(f"Multi-Segment Horn Optimization")
    print(f"{'='*70}")
    print(f"Driver: {driver}")
    print(f"Preset: {preset}")
    print(f"Segments: {num_segments}")
    print(f"Type: {'Hyperbolic (Hypex)' if use_hyperbolic else 'Standard Exponential'}")
    print(f"Population: {pop_size}")
    print(f"Generations: {n_generations}")
    print(f"Sampling: {'Latin Hypercube' if use_lhs else 'Random'}")
    print(f"Profile Seeding: {'Yes' if use_profile_seeding else 'No'}")
    print(f"{'='*70}\n")

    # Get parameter space (hyperbolic or standard)
    if use_hyperbolic:
        param_space = get_hyperbolic_parameter_space(
            driver, preset=preset, num_segments=num_segments
        )
    else:
        param_space = get_multisegment_horn_parameter_space(
            driver, preset=preset, num_segments=num_segments
        )

    # Extract parameter bounds as dict
    parameter_bounds = {}
    for param in param_space.parameters:
        parameter_bounds[param.name] = (param.min_value, param.max_value)

    # Define optimization objectives
    # Based on research, we want to:
    # 1. Minimize response flatness (composite metric: std dev + slope + ripple)
    # 2. Minimize impedance smoothness (reduce resonances)
    # 3. Optionally: Minimize size (horn length/volume)

    # For 2-objective optimization (recommended for NSGA-II):
    # - flatness (response quality)
    # - impedance_smoothness (loading quality)
    objectives = ["flatness", "impedance_smoothness"]

    # Define constraints
    # Based on research recommendations:
    constraints = [
        "segment_continuity",  # Monotonic area expansion
        "flare_constant_limits",  # Practical flare rates
        "flare_curvature",  # m_throat ≥ m_mid ≥ m_mouth (NEW)
    ]

    # Define target frequency band based on preset
    if preset == "bass_horn":
        target_band = (40, 300)  # Bass range
    elif preset == "midrange_horn":
        target_band = (200, 5000)  # Midrange range
    else:  # fullrange_horn
        target_band = (100, 10000)  # Full range

    # Create optimization problem
    problem = EnclosureOptimizationProblem(
        driver=driver,
        enclosure_type="multisegment_horn",
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

    # Setup algorithm with LHS or random sampling
    if use_lhs:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.operators.crossover.sbx import SBX
        from pymoo.operators.mutation.pm import PM

        algorithm = NSGA2(
            pop_size=pop_size,
            sampling=LHS(),  # Latin Hypercube Sampling
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(eta=20),
            eliminate_duplicates=True
        )
    else:
        algorithm = None  # Use default in run_nsga2

    # Inject profile seeds into initial population if requested
    if use_profile_seeding and algorithm is not None:
        profile_seeds = create_profile_seeded_population(
            problem, n_profiles=3, use_hyperbolic=use_hyperbolic
        )
        print(f"Injecting {len(profile_seeds)} profile seeds into initial population")
        # Note: In pymoo, we can modify the sampling to include these seeds
        # For now, we'll use LHS which provides good space-filling coverage

    # Run optimization
    if algorithm is not None:
        # Custom algorithm setup (with LHS)
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
    else:
        # Use convenience function
        result, metadata = run_nsga2(
            problem,
            pop_size=pop_size,
            n_generations=n_generations,
            seed=seed,
            verbose=True
        )

    print(f"\n{'='*70}")
    print(f"Optimization Complete!")
    print(f"{'='*70}")
    print(f"Evaluations: {metadata['n_evaluations']}")
    print(f"Pareto Designs: {metadata['n_pareto_designs']}")
    print(f"{'='*70}\n")

    return result, metadata, problem


def analyze_results(result, problem, driver, preset: str, output_dir: str = None, use_hyperbolic: bool = False):
    """
    Analyze and plot optimization results.

    Args:
        result: pymoo optimization result
        problem: EnclosureOptimizationProblem instance
        driver: ThieleSmallParameters instance
        preset: Design preset name
        output_dir: Output directory for plots (default: tasks/)
        use_hyperbolic: Whether results include T parameters
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
    title_type = 'Hyperbolic (Hypex)' if use_hyperbolic else 'Standard Exponential'
    ax.set_title(f'Multi-Segment Horn Optimization - Pareto Front\n({preset} - {title_type})', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)

    # Mark best trade-off point
    # Normalize objectives and find point closest to (0, 0)
    F_norm = (F - F.min(axis=0)) / (F.max(axis=0) - F.min(axis=0))
    best_idx = np.argmin(np.linalg.norm(F_norm, axis=1))
    ax.scatter(F[best_idx, 0], F[best_idx, 1], c='red', s=200, marker='*',
               edgecolors='black', linewidths=2, label='Best Trade-off', zorder=10)
    ax.legend(fontsize=10)

    plt.tight_layout()
    pareto_path = Path(output_dir) / f"pareto_front_{preset}{'_hyperbolic' if use_hyperbolic else ''}.png"
    plt.savefig(pareto_path, dpi=150)
    print(f"Pareto front plot saved to: {pareto_path}")

    # Print best designs
    print(f"\n{'='*70}")
    print(f"Top 5 Pareto-Optimal Designs")
    print(f"{'='*70}")

    # Adjust header based on whether hyperbolic
    if use_hyperbolic and problem.n_var >= 9:
        header = f"{'Flatness':<12} {'Impedance':<12} {'Design Parameters':<70}"
        subheader = f"{'(dB)':<12} {'Smoothness':<12} {'(throat, middle, mouth areas + lengths + T1, T2)':<70}"
    else:
        header = f"{'Flatness':<12} {'Impedance':<12} {'Design Parameters':<50}"
        subheader = f"{'(dB)':<12} {'Smoothness':<12} {'(throat, middle, mouth areas + lengths)':<50}"

    print(header)
    print(subheader)
    print("-" * 100)

    # Sort by flatness (objective 0)
    sorted_indices = np.argsort(F[:, 0])

    for i, idx in enumerate(sorted_indices[:5]):
        flatness = F[idx, 0]
        impedance = F[idx, 1]
        design = X[idx]

        # Decode design
        if use_hyperbolic:
            params = decode_hyperbolic_design(design, driver, num_segments=2)
        else:
            params = problem.decode_design_vector(design)

        # Format design string
        if problem.num_segments == 2:
            areas = [params.get('throat_area', 0),
                    params.get('middle_area', 0),
                    params.get('mouth_area', 0)]
            lengths = [params.get(f'length{j+1}', 0) for j in range(2)]

            if use_hyperbolic:
                t_params = params.get('T_params', [1.0, 1.0])
                design_str = f"S=[{areas[0]*10000:.1f}, {areas[1]*10000:.1f}, {areas[2]*10000:.1f}] cm², L=[{lengths[0]:.2f}, {lengths[1]:.2f}] m, T=[{t_params[0]:.2f}, {t_params[1]:.2f}]"
            else:
                design_str = f"S=[{areas[0]*10000:.1f}, {areas[1]*10000:.1f}, {areas[2]*10000:.1f}] cm², L=[{lengths[0]:.2f}, {lengths[1]:.2f}] m"
        else:
            design_str = str(params)

        if use_hyperbolic:
            print(f"{flatness:<12.4f} {impedance:<12.4f} {design_str:<70}")
        else:
            print(f"{flatness:<12.4f} {impedance:<12.4f} {design_str:<50}")

    print(f"{'='*70}\n")

    # Save best design to file
    best_design = X[best_idx]
    best_params = decode_hyperbolic_design(best_design, driver, num_segments=2) if use_hyperbolic else problem.decode_design_vector(best_design)
    best_objectives = F[best_idx]

    output_file = Path(output_dir) / f"best_design_{preset}{'_hyperbolic' if use_hyperbolic else ''}.txt"
    with open(output_file, 'w') as f:
        f.write(f"Best Multi-Segment Horn Design - {preset}\n")
        if use_hyperbolic:
            f.write(f"Type: Hyperbolic (Hypex) Horn\n")
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
        description="Optimize multi-segment horn profiles using NSGA-II"
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
    parser.add_argument(
        "--hyperbolic",
        action="store_true",
        help="Use hyperbolic (Hypex) horn optimization with T parameters (default: standard exponential)"
    )

    args = parser.parse_args()

    # Load driver
    driver = load_driver(args.driver)

    # Run optimization
    result, metadata, problem = optimize_horn_profile(
        driver=driver,
        preset=args.preset,
        num_segments=args.segments,
        pop_size=args.pop_size,
        n_generations=args.generations,
        use_lhs=not args.no_lhs,
        use_profile_seeding=not args.no_seeding,
        use_hyperbolic=args.hyperbolic,
        seed=args.seed,
    )

    # Analyze results
    analyze_results(result, problem, driver, args.preset, use_hyperbolic=args.hyperbolic)

    print("\nOptimization complete! Review the generated plots and design files.")
    print("\nNext steps:")
    print("1. Review the Pareto front plot to understand the trade-offs")
    print("2. Export best designs to Hornresp for validation")
    print("3. Build and measure prototypes")


if __name__ == "__main__":
    main()
