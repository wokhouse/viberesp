#!/usr/bin/env python3
"""
Debug script for flatness objective calculation.

Tests the flatness calculation with different design types to identify
why the objective is returning penalty values.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import warnings

from viberesp.driver import load_driver
from viberesp.optimization.objectives.response_metrics import objective_response_flatness
from viberesp.optimization.parameters.multisegment_horn_params import (
    decode_hyperbolic_design,
    build_multisegment_horn,
)
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def test_flatness_calculation():
    """Test flatness calculation with hyperbolic design."""

    print("=" * 80)
    print("FLATNESS OBJECTIVE DEBUG")
    print("=" * 80)

    # Load driver
    print("\nLoading driver...")
    driver = load_driver("BC_15DS115")
    print(f"  Driver: BC_15DS115")

    # Test design (hyperbolic horn with T parameters)
    # [throat_area, middle_area, mouth_area, length1, length2, T1, T2, V_tc, V_rc]
    design = np.array([
        0.0445, 0.150, 0.3000, 1.60, 2.46, 0.961, 1.000, 0.0, 0.127
    ])

    print(f"\nTest design vector (9 parameters):")
    print(f"  throat_area: {design[0]*10000:.0f} cm²")
    print(f"  middle_area: {design[1]*10000:.0f} cm²")
    print(f"  mouth_area: {design[2]*10000:.0f} cm²")
    print(f"  length1: {design[3]:.2f} m")
    print(f"  length2: {design[4]:.2f} m")
    print(f"  T1: {design[5]:.3f}")
    print(f"  T2: {design[6]:.3f}")
    print(f"  V_tc: {design[7]:.6f} m³")
    print(f"  V_rc: {design[8]:.3f} m³")

    # Test 1: Try to decode as hyperbolic design
    print("\n" + "=" * 80)
    print("TEST 1: Decode as hyperbolic design")
    print("=" * 80)

    try:
        params = decode_hyperbolic_design(design, driver, num_segments=2)
        print("✓ Successfully decoded hyperbolic design")
        print(f"  Throat area: {params['throat_area']*10000:.0f} cm²")
        print(f"  Mouth area: {params['mouth_area']*10000:.0f} cm²")
        print(f"  T_params: {params['T_params']}")
        print(f"  Segment types: {params.get('segment_types', 'N/A')}")
    except Exception as e:
        print(f"✗ Failed to decode hyperbolic design: {e}")
        return

    # Test 2: Try to build horn
    print("\n" + "=" * 80)
    print("TEST 2: Build multisegment horn")
    print("=" * 80)

    try:
        horn, V_tc, V_rc = build_multisegment_horn(design, driver, num_segments=2)
        print("✓ Successfully built hyperbolic horn")
        print(f"  Horn type: {type(horn).__name__}")
        print(f"  V_tc: {V_tc:.6f} m³")
        print(f"  V_rc: {V_rc:.3f} m³")
        print(f"  Num segments: {len(horn.segments)}")
        print(f"  Segment 0 type: {type(horn.segments[0]).__name__}")
        print(f"  Segment 1 type: {type(horn.segments[1]).__name__}")
    except Exception as e:
        print(f"✗ Failed to build horn: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Try to calculate SPL response
    print("\n" + "=" * 80)
    print("TEST 3: Calculate SPL response")
    print("=" * 80)

    try:
        flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)
        print("✓ Created FrontLoadedHorn")

        # Test at a few frequencies
        test_freqs = [20, 50, 100, 200, 500]
        for freq in test_freqs:
            spl = flh.spl_response(freq, voltage=2.83)
            print(f"  {freq:3d} Hz: {spl:5.1f} dB")

    except Exception as e:
        print(f"✗ Failed to calculate SPL: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 4: Try flatness objective with different enclosure types
    print("\n" + "=" * 80)
    print("TEST 4: Flatness objective calculation")
    print("=" * 80)

    for enc_type in ["multisegment_horn", "mixed_profile_horn"]:
        print(f"\nTesting with enclosure_type='{enc_type}':")

        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                flatness = objective_response_flatness(
                    design,
                    driver,
                    enc_type,
                    frequency_range=(20.0, 200.0),
                    n_points=20,
                    num_segments=2,
                )

                print(f"  Flatness: {flatness:.2f} dB")

                if w:
                    print(f"  Warnings: {len(w)}")
                    for warning in w:
                        print(f"    - {warning.message}")

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            import traceback
            traceback.print_exc()

    # Test 5: Manual flatness calculation
    print("\n" + "=" * 80)
    print("TEST 5: Manual flatness calculation")
    print("=" * 80)

    try:
        frequencies = np.logspace(np.log10(20.0), np.log10(200.0), 20)
        spl_values = []

        print("  Calculating SPL at 20 frequencies:")
        for i, freq in enumerate(frequencies):
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
            if i % 5 == 0 or i == len(frequencies) - 1:
                print(f"    {freq:5.1f} Hz: {spl:5.1f} dB")

        spl_values = np.array(spl_values)
        flatness = np.std(spl_values)

        print(f"\n  Manual flatness: {flatness:.2f} dB")
        print(f"  Min SPL: {np.min(spl_values):.2f} dB")
        print(f"  Max SPL: {np.max(spl_values):.2f} dB")
        print(f"  Range: {np.max(spl_values) - np.min(spl_values):.2f} dB")

    except Exception as e:
        print(f"  ✗ Exception: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_flatness_calculation()
