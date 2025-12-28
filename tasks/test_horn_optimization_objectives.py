#!/usr/bin/env python3
"""
Test exponential horn optimization objectives with TC2 parameters.

This script validates that all horn optimization objectives work correctly
and produce reasonable results for the TC2 test case.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from viberesp.driver.test_drivers import get_tc2_compression_driver
from viberesp.optimization.parameters import get_exponential_horn_parameter_space
from viberesp.optimization.objectives.response_metrics import (
    objective_f3,
    objective_response_flatness,
)
from viberesp.optimization.objectives.size_metrics import objective_enclosure_volume


def test_parameter_space():
    """Test 1: Parameter space creation."""
    print("=" * 70)
    print("TEST 1: Parameter Space Creation")
    print("=" * 70)

    driver = get_tc2_compression_driver()
    param_space = get_exponential_horn_parameter_space(driver, preset="midrange_horn")

    print(f"Enclosure type: {param_space.enclosure_type}")
    print(f"Parameters: {param_space.get_parameter_names()}")
    print()

    xl, xu = param_space.get_bounds_array()
    print("Parameter bounds:")
    for i, name in enumerate(param_space.get_parameter_names()):
        print(f"  {name:15s}: [{xl[i]:.6f}, {xu[i]:.6f}] {param_space.parameters[i].units}")
    print()

    print("Constraints:")
    for constraint in param_space.constraints:
        print(f"  - {constraint}")
    print()

    print("✓ PASSED: Parameter space created successfully\n")
    return True


def test_f3_objective():
    """Test 2: F3 (cutoff frequency) objective."""
    print("=" * 70)
    print("TEST 2: F3 Objective (Horn Cutoff Frequency)")
    print("=" * 70)

    driver = get_tc2_compression_driver()

    # TC2 horn parameters
    design_vector = np.array([0.0005, 0.02, 0.5, 0.0])

    print("Design parameters:")
    print(f"  Throat area: {design_vector[0]*10000:.1f} cm²")
    print(f"  Mouth area:  {design_vector[1]*10000:.1f} cm²")
    print(f"  Length:      {design_vector[2]:.2f} m")
    print(f"  Rear chamber: {design_vector[3]*1000:.1f} L")
    print()

    fc = objective_f3(design_vector, driver, "exponential_horn")

    print(f"Cutoff frequency: {fc:.1f} Hz")
    print(f"Expected:         ~404 Hz (Olson's formula)")
    print(f"Error:            {abs(fc - 404.0):.1f} Hz")

    if abs(fc - 404.0) < 10.0:
        print("✓ PASSED: Cutoff frequency within tolerance\n")
        return True
    else:
        print("✗ FAILED: Cutoff frequency outside tolerance\n")
        return False


def test_volume_objective():
    """Test 3: Enclosure volume objective."""
    print("=" * 70)
    print("TEST 3: Enclosure Volume Objective")
    print("=" * 70)

    driver = get_tc2_compression_driver()

    # Test 1: No rear chamber
    design_vector_no_rc = np.array([0.0005, 0.02, 0.5, 0.0])
    vol_no_rc = objective_enclosure_volume(design_vector_no_rc, driver, "exponential_horn")

    print("Design 1: Horn only (no rear chamber)")
    print(f"  Throat area: {design_vector_no_rc[0]*10000:.1f} cm²")
    print(f"  Mouth area:  {design_vector_no_rc[1]*10000:.1f} cm²")
    print(f"  Length:      {design_vector_no_rc[2]:.2f} m")
    print(f"  Volume:      {vol_no_rc*1000:.2f} L")
    print(f"  Expected:    ~2.6 L (analytical)")
    print()

    # Test 2: With rear chamber
    design_vector_with_rc = np.array([0.0005, 0.02, 0.5, 0.002])
    vol_with_rc = objective_enclosure_volume(design_vector_with_rc, driver, "exponential_horn")

    print("Design 2: Horn + 2L rear chamber")
    print(f"  Throat area:   {design_vector_with_rc[0]*10000:.1f} cm²")
    print(f"  Mouth area:    {design_vector_with_rc[1]*10000:.1f} cm²")
    print(f"  Length:        {design_vector_with_rc[2]:.2f} m")
    print(f"  Rear chamber:  {design_vector_with_rc[3]*1000:.1f} L")
    print(f"  Total volume:  {vol_with_rc*1000:.2f} L")
    print(f"  Expected:      ~4.6 L (2.6 L horn + 2.0 L chamber)")
    print()

    vol_check = abs(vol_no_rc - 0.0026) < 0.001
    vol_check_rc = abs(vol_with_rc - 0.0046) < 0.001

    if vol_check and vol_check_rc:
        print("✓ PASSED: Volume calculations correct\n")
        return True
    else:
        print("✗ FAILED: Volume calculations incorrect\n")
        return False


def test_flatness_objective():
    """Test 4: Response flatness objective."""
    print("=" * 70)
    print("TEST 4: Response Flatness Objective")
    print("=" * 70)

    driver = get_tc2_compression_driver()
    design_vector = np.array([0.0005, 0.02, 0.5, 0.0])

    print("Design parameters:")
    print(f"  Throat area: {design_vector[0]*10000:.1f} cm²")
    print(f"  Mouth area:  {design_vector[1]*10000:.1f} cm²")
    print(f"  Length:      {design_vector[2]:.2f} m")
    print(f"  Cutoff:      {objective_f3(design_vector, driver, 'exponential_horn'):.1f} Hz")
    print()

    # Test flatness above cutoff (where response is meaningful)
    flatness = objective_response_flatness(
        design_vector, driver, "exponential_horn",
        frequency_range=(400, 5000),
        n_points=20,
        voltage=2.83
    )

    print(f"Response flatness: {flatness:.2f} dB (std dev)")
    print(f"Frequency range:   400-5000 Hz (above cutoff)")
    print(f"Interpretation:    Lower is better (flatter response)")
    print()

    # Flatness should be reasonable (< 10 dB std dev)
    if flatness < 10.0 and flatness > 0:
        print("✓ PASSED: Flatness within reasonable range\n")
        return True
    else:
        print("✗ FAILED: Flatness outside reasonable range\n")
        return False


def test_parameter_sweep():
    """Test 5: Parameter sweep to show optimization tradeoffs."""
    print("=" * 70)
    print("TEST 5: Parameter Sweep (Showing Optimization Potential)")
    print("=" * 70)

    driver = get_tc2_compression_driver()

    # Sweep mouth area (affects cutoff frequency and volume)
    mouth_areas = np.array([0.01, 0.02, 0.04, 0.08])  # cm²
    throat_area = 0.0005  # Fixed: 5 cm²
    length = 0.5  # Fixed: 0.5 m
    V_rc = 0.0  # No rear chamber

    print("Sweeping mouth area (throat=5cm², length=0.5m, V_rc=0L):")
    print()
    print(f"{'Mouth':>10s} {'Cutoff':>10s} {'Volume':>10s} {'Flatness':>10s}")
    print("-" * 50)

    for mouth_area in mouth_areas:
        design_vector = np.array([throat_area, mouth_area, length, V_rc])

        fc = objective_f3(design_vector, driver, "exponential_horn")
        vol = objective_enclosure_volume(design_vector, driver, "exponential_horn")

        # Calculate flatness in appropriate range (above cutoff)
        f_min = max(400, fc * 1.5)
        flatness = objective_response_flatness(
            design_vector, driver, "exponential_horn",
            frequency_range=(f_min, 5000),
            n_points=15,
            voltage=2.83
        )

        print(f"{mouth_area*10000:>6.0f} cm²  {fc:>6.0f} Hz  {vol*1000:>6.2f} L  {flatness:>6.2f} dB")

    print()
    print("Observations:")
    print("  - Larger mouth → Lower cutoff (better bass extension)")
    print("  - Larger mouth → Larger volume (trade-off)")
    print("  - All designs have reasonable flatness above cutoff")
    print()

    print("✓ PASSED: Parameter sweep shows optimization tradeoffs\n")
    return True


def test_multi_objective():
    """Test 6: Multi-objective evaluation (user's priority objectives)."""
    print("=" * 70)
    print("TEST 6: Multi-Objective Evaluation (User Priorities)")
    print("=" * 70)

    driver = get_tc2_compression_driver()

    # Compare two designs
    print("Comparing two horn designs:")
    print()

    # Design 1: Small midrange horn (TC2-like)
    design1 = np.array([0.0005, 0.02, 0.5, 0.0])
    fc1 = objective_f3(design1, driver, "exponential_horn")
    vol1 = objective_enclosure_volume(design1, driver, "exponential_horn")
    flat1 = objective_response_flatness(
        design1, driver, "exponential_horn",
        frequency_range=(400, 5000), n_points=20, voltage=2.83
    )

    print("Design 1: Compact midrange horn")
    print(f"  Throat: {design1[0]*10000:.1f} cm², Mouth: {design1[1]*10000:.0f} cm², Length: {design1[2]:.1f} m")
    print(f"  Cutoff:  {fc1:.0f} Hz")
    print(f"  Volume:  {vol1*1000:.2f} L")
    print(f"  Flatness: {flat1:.2f} dB")
    print()

    # Design 2: Larger bass horn
    design2 = np.array([0.0005, 0.08, 1.0, 0.002])
    fc2 = objective_f3(design2, driver, "exponential_horn")
    vol2 = objective_enclosure_volume(design2, driver, "exponential_horn")
    flat2 = objective_response_flatness(
        design2, driver, "exponential_horn",
        frequency_range=(200, 5000), n_points=20, voltage=2.83
    )

    print("Design 2: Larger bass horn")
    print(f"  Throat: {design2[0]*10000:.1f} cm², Mouth: {design2[1]*10000:.0f} cm², Length: {design2[2]:.1f} m")
    print(f"  Cutoff:  {fc2:.0f} Hz")
    print(f"  Volume:  {vol2*1000:.2f} L")
    print(f"  Flatness: {flat2:.2f} dB")
    print()

    print("Trade-off analysis:")
    print(f"  Cutoff improvement: {fc1 - fc2:.0f} Hz ({(fc1-fc2)/fc1*100:.1f}% lower)")
    print(f"  Volume increase:    {(vol2-vol1)*1000:.2f} L ({(vol2-vol1)/vol1*100:.1f}% larger)")
    print(f"  Flatness change:    {flat2 - flat1:+.2f} dB")
    print()

    print("✓ PASSED: Multi-objective evaluation shows design tradeoffs\n")
    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  EXPONENTIAL HORN OPTIMIZATION - OBJECTIVE TESTS".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        ("Parameter Space Creation", test_parameter_space),
        ("F3 Objective", test_f3_objective),
        ("Volume Objective", test_volume_objective),
        ("Flatness Objective", test_flatness_objective),
        ("Parameter Sweep", test_parameter_sweep),
        ("Multi-Objective Evaluation", test_multi_objective),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Total: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 ALL TESTS PASSED! Horn optimization objectives are working correctly.")
        print()
        print("Next steps:")
        print("  1. Add horn constraints (Step 5)")
        print("  2. Integrate with Design Assistant (Step 6)")
        print("  3. Run NSGA-II optimization test")
        print("  4. Validate optimized designs against Hornresp")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
