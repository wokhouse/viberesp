#!/usr/bin/env python3
"""
Test script to verify objective functions work with mixed_profile_horn.
"""

import sys
import os
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver.loader import load_driver
from viberesp.optimization.objectives.response_metrics import objective_f3
from viberesp.optimization.objectives.efficiency import objective_efficiency

def test_objectives():
    """Test F3 and efficiency objectives with mixed_profile_horn."""
    print("Testing objective functions with mixed_profile_horn...")
    print("=" * 70)

    # Load driver
    driver = load_driver('BC_18RBX100')
    print(f"Driver: {driver}")
    print()

    # Test design vector (11 parameters for 2-segment mixed profile)
    # [S_throat, S1, S_mouth, L1, L2, ptype1, ptype2, T1, T2, V_tc, V_rc]
    design = np.array([
        0.01,    # S_throat (m²) - 100 cm²
        0.05,    # S1 (m²) - 500 cm²
        0.5,     # S_mouth (m²) - 5000 cm²
        2.0,     # L1 (m) - 2m throat segment
        3.0,     # L2 (m) - 3m mouth segment
        0,       # ptype1 - Exponential
        1,       # ptype2 - Conical
        1.0,     # T1 - not used for Exp
        1.0,     # T2 - not used for Con
        0.0,     # V_tc (m³)
        0.0,     # V_rc (m³)
    ])

    print(f"Test design vector: {design}")
    print(f"  Throat area: {design[0]*10000:.1f} cm²")
    print(f"  Middle area: {design[1]*10000:.1f} cm²")
    print(f"  Mouth area: {design[2]*10000:.1f} cm²")
    print(f"  Length 1: {design[3]:.2f} m")
    print(f"  Length 2: {design[4]:.2f} m")
    print(f"  Profile types: Exp (0), Con (1)")
    print()

    # Test F3 objective
    print("Testing objective_f3()...")
    try:
        f3 = objective_f3(design, driver, 'mixed_profile_horn', frequency_points=None)
        print(f"  ✓ F3 = {f3:.2f} Hz")
        assert 20 < f3 < 300, f"F3 out of reasonable range: {f3}"
        print(f"  ✓ F3 is in reasonable range (20-300 Hz)")
    except Exception as e:
        print(f"  ✗ F3 calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    # Test efficiency objective
    print("Testing objective_efficiency()...")
    try:
        eff = objective_efficiency(design, driver, 'mixed_profile_horn')
        print(f"  ✓ Efficiency = {-eff:.3f}%")  # Negative because pymoo minimizes
        assert -100 < eff < 0, f"Efficiency out of range: {eff}"
        print(f"  ✓ Efficiency is in reasonable range (0-100%)")
    except Exception as e:
        print(f"  ✗ Efficiency calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()

    print("=" * 70)
    print("All tests passed! ✓")
    print()
    print("The objective functions now support mixed_profile_horn correctly.")
    return True

if __name__ == "__main__":
    success = test_objectives()
    sys.exit(0 if success else 1)
