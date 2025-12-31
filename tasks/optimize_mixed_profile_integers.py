#!/usr/bin/env python3
"""
Optimize mixed-profile horn using integer variable support for profile types.

This script demonstrates the new mixed-variable optimization capability where
profile types (Con/Exp/Hyp) are treated as discrete integers (0, 1, 2) instead
of continuous floats.

Literature:
    - Deb (2001) - Multi-Objective Optimization using NSGA-II
    - pymoo documentation - Mixed-variable GA
    - Olson (1947), Chapter 8 - Compound horns

Usage:
    PYTHONPATH=src python3 tasks/optimize_mixed_profile_integers.py
"""

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination

from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_mixed_profile_parameter_space,
)
from viberesp.optimization.objectives.composite import EnclosureOptimizationProblem


def optimize_mixed_profile_horn(
    driver_name: str = 'BC_DE250',
    num_segments: int = 2,
    pop_size: int = 100,
    n_generations: int = 50,
):
    """
    Optimize mixed-profile horn with integer profile types.

    Args:
        driver_name: Name of driver to use
        num_segments: Number of horn segments (2 or 3)
        pop_size: Population size for GA
        n_generations: Number of generations to run

    Returns:
        Optimization result with Pareto front solutions
    """
    print("="*70)
    print(f"MIXED-PROFILE HORN OPTIMIZATION ({num_segments} segments)")
    print("="*70)

    # Load driver
    driver = load_driver(driver_name)
    print(f"\nDriver: {driver_name}")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Vas: {driver.V_as*1000:.1f} L")

    # Get parameter space
    param_space = get_mixed_profile_parameter_space(
        driver, preset='midrange_horn', num_segments=num_segments
    )

    print(f"\nParameter space: {len(param_space.parameters)} parameters")
    for p in param_space.parameters:
        is_integer = p.name.startswith("profile_type")
        vtype_str = "INTEGER" if is_integer else "continuous"
        print(f"  - {p.name:15s} [{p.min_value:.4f}, {p.max_value:.4f}] ({vtype_str})")

    # Create optimization problem
    # Objectives: minimize impedance variation (smoother response)
    #             minimize response deviation from flat (better sound)
    problem = EnclosureOptimizationProblem(
        driver=driver,
        enclosure_type='mixed_profile_horn',
        objectives=['impedance_smoothness', 'flatness'],
        parameter_bounds={p.name: (p.min_value, p.max_value)
                        for p in param_space.parameters},
        constraints=['segment_continuity', 'mouth_size'],
        num_segments=num_segments,
        target_band=(500, 5000)  # Midrange optimization
    )

    print(f"\nOptimization problem:")
    print(f"  Objectives: {problem.n_obj} (impedance_smoothness, flatness)")
    print(f"  Constraints: {problem.n_constr}")
    print(f"  Variables: {problem.n_var} total")
    print(f"    - Integer: {sum(~problem.vtype)} (profile types)")
    print(f"    - Continuous: {sum(problem.vtype)}")

    # Setup NSGA-II algorithm
    # Note: Using standard SBX/PM operators - pymoo handles integer rounding
    algorithm = NSGA2(
        pop_size=pop_size,
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )

    print(f"\nNSGA-II Configuration:")
    print(f"  Population size: {pop_size}")
    print(f"  Generations: {n_generations}")
    print(f"  Crossover: SBX (prob=0.9, eta=15)")
    print(f"  Mutation: PM (eta=20)")

    # Run optimization
    print(f"\n{'='*70}")
    print("RUNNING OPTIMIZATION...")
    print(f"{'='*70}\n")

    result = minimize(
        problem,
        algorithm,
        termination=get_termination('n_gen', n_generations),
        verbose=True,
        seed=42
    )

    # Analyze results
    print(f"\n{'='*70}")
    print("OPTIMIZATION COMPLETE")
    print(f"{'='*70}")

    print(f"\nNumber of solutions on Pareto front: {len(result.F)}")

    # Find best compromise solution (minimize combined objective)
    # Normalize objectives and find point closest to origin
    F_norm = (result.F - result.F.min(axis=0)) / (result.F.max(axis=0) - result.F.min(axis=0))
    distances = np.sqrt(np.sum(F_norm**2, axis=1))
    best_idx = np.argmin(distances)

    print(f"\nBest compromise solution (index {best_idx}):")
    print(f"  Impedance smoothness: {result.F[best_idx, 0]:.4f}")
    print(f"  Response flatness: {result.F[best_idx, 1]:.4f}")
    print(f"  Normalized distance: {distances[best_idx]:.4f}")

    # Decode best solution
    best_design = result.X[best_idx]
    print(f"\nBest design parameters:")
    print(f"  Throat area: {best_design[0]*10000:.2f} cm²")
    print(f"  Middle area: {best_design[1]*10000:.2f} cm²")
    print(f"  Mouth area: {best_design[2]*10000:.2f} cm²")
    print(f"  Length 1: {best_design[3]*100:.1f} cm")
    print(f"  Length 2: {best_design[4]*100:.1f} cm")

    if num_segments == 2:
        type_names = ['Exp', 'Con', 'Hyp']
        ptype1 = int(best_design[5])
        ptype2 = int(best_design[6])
        print(f"  Profile type 1: {ptype1} ({type_names[ptype1]})")
        print(f"  Profile type 2: {ptype2} ({type_names[ptype2]})")
        print(f"  T1: {best_design[7]:.3f}")
        print(f"  T2: {best_design[8]:.3f}")

    # Show profile type distribution in population
    print(f"\nProfile type distribution in final population:")
    profile_types = result.X[:, 5:7].astype(int) if num_segments == 2 else result.X[:, 6:9].astype(int)

    type_names = ['Exp', 'Con', 'Hyp']
    for i in range(num_segments):
        unique, counts = np.unique(profile_types[:, i], return_counts=True)
        print(f"  Segment {i+1}:")
        for val, count in zip(unique, counts):
            print(f"    {type_names[val]}: {count} designs ({count/len(profile_types)*100:.1f}%)")

    return result, best_idx


def main():
    """Run optimization and display results."""
    try:
        # Run optimization
        result, best_idx = optimize_mixed_profile_horn(
            driver_name='BC_DE250',
            num_segments=2,
            pop_size=100,
            n_generations=50
        )

        print(f"\n{'='*70}")
        print("OPTIMIZATION SUCCESSFUL")
        print(f"{'='*70}")
        print(f"\nBest solution is at index {best_idx} in result.X")
        print(f"Use result.X[{best_idx}] to access design vector")
        print(f"Use result.F[{best_idx}] to access objective values")

        return 0

    except Exception as e:
        print(f"\n✗ Optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
