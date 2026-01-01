#!/usr/bin/env python3
"""
Test script for mixed-profile horn enhancement features.

Tests the following enhancements:
1. impedance_smoothness support for mixed_profile_horn
2. Integer variable optimization (discrete profile types)
3. Three-segment mixed-profile horn support

Literature:
    - Olson (1947), Chapter 8 - Compound horns with mixed profiles
    - Kolbrek Part 1 - T-matrix chaining for arbitrary segment types
    - literature/horns/kolbrek_horn_theory_tutorial.md

Usage:
    PYTHONPATH=src python3 tasks/test_mixed_profile_enhancements.py
"""

import sys
import numpy as np
from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_mixed_profile_parameter_space,
    build_mixed_profile_horn,
    decode_mixed_profile_design,
)
from viberesp.optimization.objectives.response_metrics import (
    objective_impedance_smoothness,
)
from viberesp.optimization.objectives.composite import EnclosureOptimizationProblem


def test_impedance_smoothness_mixed_profile():
    """Test 1: impedance_smoothness objective for mixed_profile_horn"""
    print("\n" + "="*70)
    print("TEST 1: impedance_smoothness for mixed_profile_horn")
    print("="*70)

    driver = load_driver('BC_DE250')

    # 2-segment design: [throat, middle, mouth, L1, L2, ptype1, ptype2, T1, T2, V_tc, V_rc]
    design = np.array([
        7.5e-4,    # throat
        0.02963,   # middle
        0.05102,   # mouth
        0.26,      # L1
        1.0,       # L2
        1,         # ptype1 (Conical)
        0,         # ptype2 (Exponential)
        1.0, 1.0,  # T1, T2
        0.0, 0.0   # V_tc, V_rc
    ])

    try:
        result = objective_impedance_smoothness(
            design, driver, 'mixed_profile_horn',
            num_segments=2, frequency_range=(500, 5000), n_points=20
        )
        print(f"✓ impedance_smoothness works: {result:.4f}")
        print(f"  Design: Con → Exp horn")
        print(f"  Frequency range: 500-5000 Hz")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integer_variable_optimization():
    """Test 2: Integer variable support for profile types"""
    print("\n" + "="*70)
    print("TEST 2: Integer Variable Optimization")
    print("="*70)

    driver = load_driver('BC_DE250')

    # Get parameter space
    param_space = get_mixed_profile_parameter_space(
        driver, preset='midrange_horn', num_segments=2
    )

    # Create optimization problem
    try:
        problem = EnclosureOptimizationProblem(
            driver=driver,
            enclosure_type='mixed_profile_horn',
            objectives=['impedance_smoothness'],
            parameter_bounds={p.name: (p.min_value, p.max_value)
                            for p in param_space.parameters},
            num_segments=2
        )

        # Check vtype (variable types)
        print(f"✓ Optimization problem created")
        print(f"  Number of variables: {problem.n_var}")
        print(f"  Parameter names: {problem.param_names}")

        # Check which variables are integers
        integer_vars = [i for i, vtype in enumerate(problem.vtype) if not vtype]
        continuous_vars = [i for i, vtype in enumerate(problem.vtype) if vtype]

        print(f"  Integer variables (profile types): {len(integer_vars)}")
        for idx in integer_vars:
            print(f"    - {problem.param_names[idx]} (index {idx})")
        print(f"  Continuous variables: {len(continuous_vars)}")

        # Test evaluation with a sample design
        design = np.array([
            7.5e-4, 0.02963, 0.05102, 0.26, 1.0,
            1.5, 1.3,  # Float profile types (should be rounded)
            1.0, 1.0, 0.0, 0.0
        ])
        X = design.reshape(1, -1)

        out = {}
        problem._evaluate(X, out)
        print(f"  ✓ Evaluation works: objective = {out['F'][0][0]:.4f}")

        # Verify that profile types were rounded to integers
        # (by decoding the design and checking)
        params = decode_mixed_profile_design(design, driver, num_segments=2)
        print(f"  ✓ Profile types decoded as: {params['profile_types']}")

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_three_segment_horn():
    """Test 3: Three-segment mixed-profile horn"""
    print("\n" + "="*70)
    print("TEST 3: Three-Segment Mixed-Profile Horn")
    print("="*70)

    driver = load_driver('BC_DE250')

    # 3-segment design: [throat, middle, area2, mouth, L1, L2, L3,
    #                     ptype1, ptype2, ptype3, T1, T2, T3, V_tc, V_rc]
    # Test: Con → Exp → Hyp combination
    design_3seg = np.array([
        7.5e-4,    # throat
        0.02,      # middle
        0.04,      # area2
        0.05,      # mouth
        0.2, 0.3, 0.4,  # L1, L2, L3
        1, 0, 2,   # ptype1=Con, ptype2=Exp, ptype3=Hyp
        1.0, 1.0, 0.7,  # T1, T2, T3
        0.0, 0.0   # V_tc, V_rc
    ])

    try:
        # Build horn
        horn, V_tc, V_rc = build_mixed_profile_horn(
            design_3seg, driver, num_segments=3
        )

        print(f"✓ Built 3-segment horn:")
        print(f"  - Number of segments: {len(horn.segments)}")
        print(f"  - Segment types: {[type(s).__name__ for s in horn.segments]}")
        print(f"  - Total length: {horn.total_length():.3f} m")

        # Decode to verify parameters
        params = decode_mixed_profile_design(design_3seg, driver, num_segments=3)
        print(f"  - Profile types: {params['profile_types']}")
        print(f"  - Segment classes: {params['segment_classes']}")

        # Test impedance smoothness
        smoothness = objective_impedance_smoothness(
            design_3seg, driver, 'mixed_profile_horn',
            num_segments=3, frequency_range=(500, 5000), n_points=20
        )
        print(f"  - Impedance smoothness: {smoothness:.4f}")

        # Test parameter space for 3 segments
        param_space = get_mixed_profile_parameter_space(
            driver, preset='midrange_horn', num_segments=3
        )
        print(f"  - Parameter space size: {len(param_space.parameters)} parameters")

        expected_params = 15  # For 3 segments
        if len(param_space.parameters) == expected_params:
            print(f"  ✓ Correct number of parameters ({expected_params})")
        else:
            print(f"  ✗ Expected {expected_params} parameters, got {len(param_space.parameters)}")
            return False

        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profile_combinations():
    """Test 4: Various profile type combinations"""
    print("\n" + "="*70)
    print("TEST 4: Profile Type Combinations")
    print("="*70)

    driver = load_driver('BC_DE250')

    # Test different 2-segment combinations
    combinations = [
        ([0, 0], ["Exp", "Exp"], "Exponential → Exponential"),
        ([0, 1], ["Exp", "Con"], "Exponential → Conical"),
        ([0, 2], ["Exp", "Hyp"], "Exponential → Hyperbolic"),
        ([1, 0], ["Con", "Exp"], "Conical → Exponential"),
        ([1, 1], ["Con", "Con"], "Conical → Conical"),
        ([1, 2], ["Con", "Hyp"], "Conical → Hyperbolic"),
        ([2, 0], ["Hyp", "Exp"], "Hyperbolic → Exponential"),
        ([2, 1], ["Hyp", "Con"], "Hyperbolic → Conical"),
        ([2, 2], ["Hyp", "Hyp"], "Hyperbolic → Hyperbolic"),
    ]

    all_passed = True
    for ptypes, expected_names, description in combinations:
        design = np.array([
            7.5e-4, 0.02, 0.05,  # throat, middle, mouth
            0.2, 0.4,            # L1, L2
            *ptypes,             # profile_type1, profile_type2
            1.0, 1.0,            # T1, T2
            0.0, 0.0             # V_tc, V_rc
        ])

        try:
            horn, _, _ = build_mixed_profile_horn(design, driver, num_segments=2)
            actual_names = [type(s).__name__ for s in horn.segments]

            # Map expected names to actual class names
            name_map = {"Exp": "HornSegment", "Con": "ConicalHorn", "Hyp": "HyperbolicHorn"}
            expected_classes = [name_map[name] for name in expected_names]

            if actual_names == expected_classes:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}: Expected {expected_classes}, got {actual_names}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {description}: {e}")
            all_passed = False

    if all_passed:
        print(f"\n✓ All profile combinations work correctly")

    return all_passed


def main():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print("MIXED-PROFILE HORN ENHANCEMENT TEST SUITE")
    print("="*70)

    tests = [
        ("impedance_smoothness support", test_impedance_smoothness_mixed_profile),
        ("Integer variable optimization", test_integer_variable_optimization),
        ("Three-segment horn support", test_three_segment_horn),
        ("Profile type combinations", test_profile_combinations),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
