#!/usr/bin/env python3
"""
Quick optimizer for BC_21DS115 with 350L volume constraint.

Usage:
    python3 tasks/optimize_bc21ds115_350L.py --folded --max-volume 350
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Just re-use the existing optimizer with BC_21DS115
from viberesp.driver import load_driver

# Monkey-patch to use BC_21DS115
import viberesp.optimization.parameters.multisegment_horn_params as horn_params

_original_get_horn_params = horn_params.get_multisegment_horn_parameter_space

def _get_bc21ds115_params(driver, preset="bass_horn", num_segments=2):
    """Generate parameter space optimized for BC_21DS115."""
    from viberesp.optimization.parameters.parameter_space import (
        ParameterSpace, ParameterRange
    )

    # Throat area: 40-80% of Sd
    throat_min = 0.40 * driver.S_d
    throat_max = 0.80 * driver.S_d

    # Mouth area: 3-6x Sd for good loading
    mouth_min = 2.0 * driver.S_d
    mouth_max = 6.0 * driver.S_d

    # Rear chamber: 0.3-1.5x Vas
    v_rc_min = 0.3 * driver.V_as
    v_rc_max = 1.5 * driver.V_as

    parameters = [
        ParameterRange("throat_area", throat_min, throat_max, "m²",
                      "Throat area"),
        ParameterRange("middle_area", 0.5 * driver.S_d, mouth_max, "m²",
                      "Middle area (segment 1 exit)"),
        ParameterRange("mouth_area", mouth_min, mouth_max, "m²",
                      "Mouth area"),
        ParameterRange("length1", 1.5, 4.0, "m",
                      "Segment 1 length"),
        ParameterRange("length2", 1.5, 4.0, "m",
                      "Segment 2 length"),
        ParameterRange("T1", 0.6, 1.0, "",
                      "Shape parameter T for segment 1"),
        ParameterRange("T2", 0.7, 1.0, "",
                      "Shape parameter T for segment 2"),
        ParameterRange("V_tc", 0.0, 0.0, "m³",
                      "Throat chamber (front loaded)"),
        ParameterRange("V_rc", v_rc_min, v_rc_max, "m³",
                      "Rear chamber volume"),
    ]

    return ParameterSpace(parameters)

# Temporarily patch
horn_params.get_multisegment_horn_parameter_space = _get_bc21ds115_params

# Now import and run the optimizer
from tasks.optimize_bc15ds115_size_vs_f3 import main as _main_opt

# Run with BC_21DS115
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimize BC_21DS115 bass horn (350L max)"
    )
    parser.add_argument("--folded", action="store_true",
                       help="Add 30%% volume overhead for folded construction")
    parser.add_argument("--max-volume", type=float, default=350,
                       help="Max cabinet volume in liters (default: 350)")
    parser.add_argument("--pop-size", type=int, default=80)
    parser.add_argument("--generations", type=int, default=40)

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("BC_21DS115 Bass Horn Optimization")
    print("=" * 80)
    print("\nNote: This will use BC_21DS115 driver parameters instead of BC_15DS115")
    print("      The optimizer script will be temporarily patched.\n")

    # Load driver to show specs
    driver = load_driver("BC_21DS115")
    print(f"BC_21DS115 Specs:")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")
    print(f"  Qts: {driver.Qts:.3f}")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")

    print("\nStarting optimization with BC_21DS115...")
    print("=" * 80 + "\n")

    # Run the optimizer
    _main_opt(
        folded_horn=args.folded,
        pop_size=args.pop_size,
        n_generations=args.generations,
        max_volume_liters=args.max_volume
    )
