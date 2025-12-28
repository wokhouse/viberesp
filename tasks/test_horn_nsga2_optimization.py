#!/usr/bin/env python3
"""Test NSGA-II optimization for exponential horn.

This script tests the complete optimization pipeline for exponential horns:
1. Load TC2 compression driver
2. Set up multi-objective optimization (flatness + size)
3. Run NSGA-II to find Pareto-optimal designs
4. Validate results

Literature:
    - Deb et al. (2002) - NSGA-II algorithm
    - Olson (1947) - Horn theory
    - Beranek (1954) - Horn efficiency
"""

import sys
import numpy as np
from viberesp.optimization.api.design_assistant import DesignAssistant


def test_horn_optimization():
    """Test multi-objective horn optimization with NSGA-II.

    Tests the complete optimization pipeline:
    - TC2 compression driver
    - Exponential horn enclosure
    - Objectives: flatness (response variation) + size (volume)
    - Constraints: mouth_size, flare_constant_limits
    - NSGA-II algorithm for Pareto front

    Returns:
        bool: True if test passes, False otherwise
    """
    print("=" * 70)
    print("Horn Optimization NSGA-II Test")
    print("=" * 70)

    # Create design assistant
    da = DesignAssistant()

    # Setup optimization problem
    print("\n1. Setting up optimization problem...")
    print("   Driver: TC2 (compression driver, Fs=251 Hz)")
    print("   Enclosure: Exponential horn")
    print("   Objectives: flatness + size")
    print("   Constraints: mouth_size, flare_constant_limits")
    print("   Algorithm: NSGA-II")
    print("   Population: 20, Generations: 10")

    # Run optimization
    print("\n2. Running NSGA-II optimization...")
    result = da.optimize_design(
        driver_name="TC2",
        enclosure_type="exponential_horn",
        objectives=["flatness", "size"],
        constraints={
            "preset": "midrange_horn",
            "constraint_list": ["mouth_size", "flare_constant_limits"],
        },
        population_size=20,
        generations=10,
        top_n=5
    )

    # Check results
    print("\n3. Checking results...")

    if not result.success:
        print(f"   ✗ Optimization failed!")
        print(f"   Warnings: {result.warnings}")
        return False

    print(f"   ✓ Optimization succeeded")
    print(f"   Designs found: {result.n_designs_found}")

    if result.n_designs_found == 0:
        print("   ✗ No valid designs found (all violated constraints)")
        return False

    print(f"   ✓ Found {result.n_designs_found} valid designs")

    # Check Pareto front
    print("\n4. Analyzing Pareto front...")
    print(f"   Pareto front size: {len(result.pareto_front)}")

    if len(result.pareto_front) == 0:
        print("   ✗ Empty Pareto front")
        return False

    print(f"   ✓ Pareto front has {len(result.pareto_front)} designs")

    # Display top 5 designs
    print("\n5. Top 5 designs:")

    for i, design in enumerate(result.best_designs[:5]):
        params = design['parameters']
        objs = design['objectives']

        throat_area = params['throat_area']
        mouth_area = params['mouth_area']
        length = params['length']
        V_rc = params.get('V_rc', 0.0)

        flatness = objs['flatness']
        volume = objs['size'] * 1000  # Convert to liters

        # Calculate cutoff frequency
        from viberesp.optimization.parameters.exponential_horn_params import (
            calculate_horn_cutoff_frequency
        )
        from viberesp.simulation.constants import SPEED_OF_SOUND

        fc = calculate_horn_cutoff_frequency(
            throat_area, mouth_area, length, SPEED_OF_SOUND
        )

        print(f"\n   Design {i+1}:")
        print(f"     Throat area: {throat_area*1e6:.1f} mm²")
        print(f"     Mouth area:  {mouth_area*1e4:.1f} cm²")
        print(f"     Length:      {length*100:.1f} cm")
        print(f"     Rear chamber: {V_rc*1e6:.2f} cm³")
        print(f"     Cutoff:      {fc:.1f} Hz")
        print(f"     Flatness:    {flatness:.2f} dB")
        print(f"     Volume:      {volume:.2f} L")

    # Verify objectives are reasonable
    print("\n6. Validating objectives...")

    flatness_values = [d['objectives']['flatness'] for d in result.pareto_front]
    volume_values = [d['objectives']['size'] * 1000 for d in result.pareto_front]

    avg_flatness = np.mean(flatness_values)
    avg_volume = np.mean(volume_values)

    print(f"   Average flatness: {avg_flatness:.2f} dB")
    print(f"   Average volume: {avg_volume:.2f} L")

    # Check for reasonable ranges
    if avg_flatness > 20:  # More than 20dB variation is poor
        print(f"   ⚠ Warning: High response variation ({avg_flatness:.2f} dB)")
    else:
        print(f"   ✓ Response flatness is reasonable")

    if avg_volume < 0.1 or avg_volume > 100:  # Less than 0.1L or more than 100L
        print(f"   ⚠ Warning: Unusual volume range ({avg_volume:.2f} L)")
    else:
        print(f"   ✓ Enclosure volume is reasonable")

    print("\n" + "=" * 70)
    print("✓ NSGA-II horn optimization test PASSED")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = test_horn_optimization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
