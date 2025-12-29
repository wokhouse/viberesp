#!/usr/bin/env python3
"""
Design an exponential bass horn for the BC_15DS115 driver.

This script uses multi-objective optimization to find the best horn design
for bass reproduction (40-80 Hz target band).

Driver: BC_15DS115-8
- Fs: 33 Hz
- Qts: 0.17 (excellent for horn loading)
- Vas: 94 L
- Sd: 855 cm²
- BL: 38.7 T·m
- Xmax: 16.5 mm

Literature:
- Olson (1947) - Exponential horn theory
- Small (1972) - Horn driver requirements
"""

import numpy as np
import json
from viberesp.driver.bc_drivers import get_bc_15ds115
from viberesp.optimization.api.design_assistant import DesignAssistant


def main():
    """Run bass horn optimization for BC_15DS115."""
    print("=" * 70)
    print("BASS HORN DESIGN FOR BC_15DS115")
    print("=" * 70)

    # Load driver
    driver = get_bc_15ds115()
    print(f"\nDriver: B&C 15DS115-8")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Qts: {driver.Q_ts:.3f}")
    print(f"  Vas: {driver.V_as*1000:.1f} L")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  BL: {driver.BL:.1f} T·m")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")

    # Check horn suitability
    print(f"\nHorn Loading Suitability:")
    if driver.Q_ts < 0.35:
        print(f"  ✓ Qts={driver.Q_ts:.3f} < 0.35: Excellent for horn loading")
    elif driver.Q_ts < 0.45:
        print(f"  ✓ Qts={driver.Q_ts:.3f}: Good for horn loading")
    else:
        print(f"  ⚠ Qts={driver.Q_ts:.3f}: May require rear chamber for horn loading")

    # Initialize design assistant
    assistant = DesignAssistant(validation_mode=False)

    # Define objectives for bass horn
    # For bass reproduction, we want:
    # 1. Low cutoff frequency (bass extension)
    # 2. High efficiency (horn loading advantage)
    # 3. Reasonable size (practical constraints)
    objectives = ["f3", "efficiency", "size"]

    # Define constraints
    # Note: For bass horns, we use minimal constraints because full mouth loading
    # at low frequencies is impractical (would require >6 m² mouth at 60 Hz)
    constraints = {
        "preset": "bass_horn",  # Use bass horn parameter ranges
        "constraint_list": [],  # Start with NO constraints to debug
    }

    print(f"\nOptimization Objectives:")
    print(f"  • f3: Minimize cutoff frequency")
    print(f"  • efficiency: Maximize horn efficiency")
    print(f"  • size: Minimize enclosure size")

    print(f"\nConstraints:")
    for key, value in constraints.items():
        if key == "constraint_list":
            if value:
                print(f"  • {key}: {', '.join(value)}")
            else:
                print(f"  • {key}: None (unconstrained optimization)")
        else:
            print(f"  • {key}: {value}")

    # Run optimization
    print(f"\n{'=' * 70}")
    print("RUNNING NSGA-II OPTIMIZATION")
    print(f"{'=' * 70}\n")

    result = assistant.optimize_design(
        driver_name="BC_15DS115",
        enclosure_type="exponential_horn",
        objectives=objectives,
        constraints=constraints,
        population_size=100,
        generations=100,
        top_n=10
    )

    # Check if optimization succeeded
    if not result.success:
        print(f"\n❌ Optimization failed!")
        print(f"Warnings:")
        for warning in result.warnings:
            print(f"  • {warning}")
        return

    print(f"✓ Optimization completed successfully")
    print(f"  Found {result.n_designs_found} valid designs")
    print(f"  Pareto front size: {len(result.pareto_front)} designs\n")

    # Display best designs
    print(f"{'=' * 70}")
    print("TOP 10 BASS HORN DESIGNS")
    print(f"{'=' * 70}\n")

    for i, design in enumerate(result.best_designs[:10], 1):
        params = design["parameters"]
        objs = design["objectives"]

        # Extract parameters
        throat_area = params["throat_area"]
        mouth_area = params["mouth_area"]
        length = params["length"]
        V_tc = params["V_tc"]
        V_rc = params["V_rc"]

        # Calculate derived parameters
        from viberesp.simulation.constants import SPEED_OF_SOUND

        if mouth_area > throat_area and length > 0:
            flare_constant = np.log(mouth_area / throat_area) / length
        else:
            flare_constant = None

        # Calculate cutoff frequency
        if flare_constant:
            fc = (SPEED_OF_SOUND * flare_constant) / (2 * np.pi)
        else:
            fc = float('inf')

        # Calculate horn volume
        from viberesp.optimization.parameters.exponential_horn_params import (
            calculate_horn_volume
        )
        V_horn = calculate_horn_volume(throat_area, mouth_area, length)
        total_volume = (V_horn + V_rc) * 1000  # Convert to liters

        print(f"Design #{i}:")
        print(f"  Throat area: {throat_area*10000:.1f} cm²")
        print(f"  Mouth area:  {mouth_area*10000:.0f} cm² (radius: {np.sqrt(mouth_area/np.pi)*100:.1f} cm)")
        print(f"  Length:      {length:.2f} m")
        print(f"  Flare const: {flare_constant:.2f} m⁻¹" if flare_constant else "  Flare const: N/A")
        print(f"  Cutoff (fc): {fc:.1f} Hz" if fc < 1000 else "  Cutoff (fc): N/A")
        print(f"  Throat cham: {V_tc*1e6:.1f} cm³")
        print(f"  Rear cham:   {V_rc*1000:.1f} L")
        print(f"  Horn volume: {V_horn*1000:.1f} L")
        print(f"  Total volume:{total_volume:.1f} L")
        print(f"  Objectives:")
        print(f"    F3:         {objs['f3']:.1f} Hz")
        print(f"    Efficiency: {objs['efficiency']*100:.2f}%")
        print(f"    Size:       {objs['size']:.1f} L")
        print()

    # Save results to JSON
    output_file = "exports/bc15ds115_bass_horn_designs.json"
    with open(output_file, 'w') as f:
        json.dump({
            "driver": "BC_15DS115",
            "enclosure_type": "exponential_horn",
            "preset": "bass_horn",
            "objectives": objectives,
            "constraints": constraints,
            "n_designs_found": result.n_designs_found,
            "best_designs": result.best_designs,
            "pareto_front": result.pareto_front,
            "parameter_names": result.parameter_names,
            "objective_names": result.objective_names,
        }, f, indent=2)

    print(f"{'=' * 70}")
    print(f"Results saved to: {output_file}")
    print(f"{'=' * 70}\n")

    # Export top design to Hornresp format
    print("Exporting top design to Hornresp format...")
    top_design = result.best_designs[0]
    params = top_design["parameters"]

    # Recalculate flare constant for top design
    from viberesp.simulation.constants import SPEED_OF_SOUND
    if params["mouth_area"] > params["throat_area"] and params["length"] > 0:
        flare_constant = np.log(params["mouth_area"] / params["throat_area"]) / params["length"]
    else:
        flare_constant = 0.0

    from viberesp.hornresp.export import export_front_loaded_horn_to_hornresp
    from viberesp.simulation.types import ExponentialHorn

    # Create horn object
    horn = ExponentialHorn(
        throat_area=params["throat_area"],
        mouth_area=params["mouth_area"],
        length=params["length"]
    )

    # Export to Hornresp
    export_front_loaded_horn_to_hornresp(
        driver=driver,
        horn=horn,
        driver_name="BC_15DS115 Bass Horn",
        output_path="exports/bc15ds115_bass_horn.txt",
        comment=f"Optimized exponential bass horn - Fc={flare_constant:.2f}m⁻¹, F3={top_design['objectives']['f3']:.1f}Hz",
        V_tc_liters=params["V_tc"] * 1000,
        V_rc_liters=params["V_rc"] * 1000,
        radiation_angle="2pi",  # Half-space
    )

    print(f"✓ Exported to: exports/bc15ds115_bass_horn.txt")
    print(f"\nImport this file into Hornresp for validation!")
    print(f"  File → Import → Select bc15ds115_bass_horn.txt\n")


if __name__ == "__main__":
    main()
