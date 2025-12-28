#!/usr/bin/env python3
"""Validate optimized horn designs against Hornresp.

This script:
1. Runs NSGA-II optimization to find Pareto-optimal horn designs
2. Exports top 3 designs to Hornresp format
3. Provides instructions for manual validation

Literature:
    - Deb et al. (2002) - NSGA-II algorithm
    - Olson (1947) - Horn theory
    - Hornresp User Manual - Validation methodology
"""

import sys
import numpy as np
from pathlib import Path

from viberesp.optimization.api.design_assistant import DesignAssistant
from viberesp.driver.test_drivers import get_tc2_compression_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.hornresp.export import export_front_loaded_horn_to_hornresp


def run_optimization_and_export():
    """Run optimization and export top designs for Hornresp validation.

    Returns:
        bool: True if successful, False otherwise
    """
    print("=" * 70)
    print("Optimized Horn Design Validation")
    print("=" * 70)

    # Create design assistant
    da = DesignAssistant()

    # Run optimization
    print("\n1. Running NSGA-II optimization...")
    print("   Driver: TC2 (compression driver, Fs=251 Hz)")
    print("   Objectives: flatness + size")
    print("   Population: 20, Generations: 10")

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
        top_n=3
    )

    if not result.success:
        print(f"   ✗ Optimization failed: {result.warnings}")
        return False

    print(f"   ✓ Found {result.n_designs_found} valid designs")

    # Get driver
    driver = get_tc2_compression_driver()

    # Create output directory
    output_dir = Path("tasks/optimized_horn_validations")
    output_dir.mkdir(exist_ok=True)

    # Export top 3 designs
    print(f"\n2. Exporting top 3 designs to Hornresp format...")
    print(f"   Output directory: {output_dir}")

    for i, design in enumerate(result.best_designs[:3]):
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

        # Create horn
        horn = ExponentialHorn(throat_area, mouth_area, length)

        # Export to Hornresp
        driver_name = f"TC2_Optimized_Design{i+1}"
        output_path = output_dir / f"tc2_optimized_{i+1}.txt"

        # Export to Hornresp (skip rear chamber if V_rc is negligible)
        V_rc_liters = V_rc * 1000  # Convert m³ to liters
        if V_rc_liters < 0.005:  # Less than 5 mL, treat as no rear chamber
            V_rc_liters = 0.0

        export_front_loaded_horn_to_hornresp(
            driver=driver,
            horn=horn,
            driver_name=driver_name,
            output_path=str(output_path),
            comment=f"Optimized horn #{i+1}: Fc={fc:.1f}Hz, Flatness={flatness:.2f}dB, Vol={volume:.2f}L",
            V_rc_liters=V_rc_liters,
            radiation_angle="2pi"  # Half-space
        )

        print(f"\n   Design {i+1}:")
        print(f"     File: {output_path.name}")
        print(f"     Throat: {throat_area*1e6:.1f} mm²")
        print(f"     Mouth:  {mouth_area*1e4:.1f} cm²")
        print(f"     Length: {length*100:.1f} cm")
        print(f"     Fc:     {fc:.1f} Hz")
        print(f"     Flat:   {flatness:.2f} dB")
        print(f"     Vol:    {volume:.2f} L")

    # Print validation instructions
    print(f"\n" + "=" * 70)
    print("3. Validation Instructions")
    print("=" * 70)
    print("""
To validate the optimized designs against Hornresp:

1. Open Hornresp (http://www.hornresp.net/)

2. Import each design file:
   - File → Import → Select tc2_optimized_*.txt
   - Check that all parameters imported correctly

3. Run simulation:
   - Tools → Combined Response
   - Use frequency range: 20 Hz - 20 kHz
   - Set resolution: 5 points per octave
   - Click "Calculate"

4. Export results:
   - File → Export → CSV
   - Save as tc2_optimized_{n}_hornresp.csv

5. Compare with viberesp:
   - Run tasks/validate_tc2_spl.py for each design
   - Compare SPL response and impedance
   - Expected agreement: <3 dB (above 2×Fc)

6. Validation criteria:
   - Electrical impedance: <2% magnitude (f > Fc)
   - SPL response: <3 dB deviation (f > 2×Fc)
   - Cutoff frequency: <5 Hz from Olson's formula

7. Document results:
   - Update this script with validation status
   - Add any discrepancies to notes section
    """)

    # Print design comparison
    print("=" * 70)
    print("4. Design Comparison")
    print("=" * 70)

    print("\n   Design  Flatness(dB)  Volume(L)  Fc(Hz)  Throat(mm²)  Mouth(cm²)  Length(cm)")
    print("   ------- ------------ --------- ------- ------------ ----------- ----------")
    for i, design in enumerate(result.best_designs[:3]):
        params = design['parameters']
        objs = design['objectives']

        throat_area = params['throat_area']
        mouth_area = params['mouth_area']
        length = params['length']

        fc = calculate_horn_cutoff_frequency(
            throat_area, mouth_area, length, SPEED_OF_SOUND
        )

        flatness = objs['flatness']
        volume = objs['size'] * 1000

        print(f"   #{i+1:2d}     {flatness:6.2f}      {volume:6.2f}   {fc:6.1f}   "
              f"{throat_area*1e6:8.1f}    {mouth_area*1e4:7.1f}    {length*100:6.1f}")

    print("\n" + "=" * 70)
    print("✓ Export complete. Follow instructions above to validate.")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = run_optimization_and_export()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
