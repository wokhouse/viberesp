#!/usr/bin/env python3
"""
Test the OptimizationScriptFactory with a simple optimization.

This script tests the factory by running a quick optimization with
a small population to verify everything works.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from viberesp.optimization import (
    OptimizationScriptFactory,
    OptimizationConfig,
    AlgorithmConfig,
    print_preset_table,
)


def main():
    """Test the factory with a simple optimization."""

    print("=" * 80)
    print("Optimization Factory Test")
    print("=" * 80)

    # Show available presets
    print("\nAvailable presets:")
    print_preset_table()

    # Create configuration for a quick test
    print("\n" + "=" * 80)
    print("Creating test configuration...")
    print("=" * 80)

    config = OptimizationConfig(
        driver_name="BC_15DS115",
        enclosure_type="multisegment_horn",
        objectives=["f3", "flatness"],  # Use objectives supported by multisegment_horn
        constraints={},  # No constraints for simplicity
        parameter_space_preset="bass_horn",
        algorithm=AlgorithmConfig(
            type="nsga2",
            pop_size=20,  # Small population for quick test
            n_generations=10,  # Few generations for quick test
        ),
        output_dir="tasks",
        verbose=True,
    )

    print(f"\nDriver: {config.driver_name}")
    print(f"Enclosure: {config.enclosure_type}")
    print(f"Objectives: {config.objectives}")
    print(f"Constraints: {config.constraints}")
    print(f"Algorithm: {config.algorithm.type}")
    print(f"Population: {config.algorithm.pop_size}")
    print(f"Generations: {config.algorithm.n_generations}")

    # Create factory and run optimization
    print("\n" + "=" * 80)
    print("Creating factory and running optimization...")
    print("=" * 80)

    factory = OptimizationScriptFactory(config)

    try:
        result = factory.run()

        print("\n" + "=" * 80)
        print("TEST SUCCESSFUL!")
        print("=" * 80)

        # Display some results
        print(f"\nFound {result.n_designs_found} Pareto-optimal designs")
        print("\nTop 3 designs:")
        for i, design in enumerate(result.best_designs[:3], 1):
            print(f"\n  Design {i}:")
            print(f"    Objectives:")
            for obj_name, obj_value in design["objectives"].items():
                print(f"      {obj_name}: {obj_value:.2f}")

        return 0

    except Exception as e:
        print("\n" + "=" * 80)
        print("TEST FAILED!")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
