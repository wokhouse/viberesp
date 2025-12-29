#!/usr/bin/env python3
"""
Test script to validate acoustic power calculation fix.

This script tests the fixed acoustic_power() method against the TC2 optimized
design to verify that efficiency predictions are now correct.

Expected results (from Hornresp):
- Efficiency: ~1.07% (~ -19.7 dB)
- Frequency response variation: ~55 dB

Literature:
- Kolbrek, "Horn Loudspeaker Simulation Part 3" - Power calculation
- Beranek (1954), Chapter 4 - Acoustic power
"""

import sys
import numpy as np

# Add src to path for imports
sys.path.insert(0, 'src')

from viberesp.driver.test_drivers import get_tc2_compression_driver as get_tc2
from viberesp.simulation.types import MultiSegmentHorn, HornSegment
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def test_tc2_multiseg_efficiency():
    """Test TC2 multi-segment horn efficiency after fix."""

    print("=" * 70)
    print("Testing TC2 Multi-Segment Horn - Acoustic Power Fix Validation")
    print("=" * 70)
    print()

    # Get TC2 driver
    driver = get_tc2()
    print(f"Driver: TC2 Compression Driver")
    print(f"  Fs = {driver.F_s:.1f} Hz")
    print(f"  Sd = {driver.S_d*1e4:.1f} cm²")
    print()

    # Optimized design from optimization run
    # From: exports/tc2_multiseg_opt_20251228_174155.json
    # Segments: 1.6 cm² → 358 cm² → 591 cm²
    # Lengths: 27.4 cm + 60.0 cm = 87.4 cm total
    # Vtc = 14.56 cm³, Vrc = 0.0044 L

    segment1_length = 0.274  # 27.4 cm
    segment2_length = 0.600  # 60.0 cm

    segment1 = HornSegment(
        throat_area=1.6e-4,    # 1.6 cm² in m²
        mouth_area=358e-4,     # 358 cm² in m²
        length=segment1_length
    )

    segment2 = HornSegment(
        throat_area=358e-4,    # 358 cm² in m²
        mouth_area=591e-4,     # 591 cm² in m²
        length=segment2_length
    )

    horn = MultiSegmentHorn([segment1, segment2])

    V_tc = 1.456e-5  # 14.56 cm³ in m³ (from optimized design)
    V_rc = 4.44e-6   # 0.0044 L in m³ (from optimized design)

    print(f"Horn Design:")
    print(f"  Segment 1: {segment1.throat_area*1e4:.1f} → {segment1.mouth_area*1e4:.0f} cm², {segment1.length*100:.1f} cm")
    print(f"  Segment 2: {segment2.throat_area*1e4:.0f} → {segment2.mouth_area*1e4:.0f} cm², {segment2.length*100:.1f} cm")
    print(f"  Total length: {horn.total_length()*100:.1f} cm")
    print(f"  Throat chamber: {V_tc*1e6:.2f} cm³")
    print(f"  Rear chamber: {V_rc*1e3:.4f} L")
    print()

    # Create horn system
    flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

    # Test at a range of frequencies
    test_frequencies = [100, 200, 500, 1000, 2000, 5000, 10000]

    print("Acoustic Power Test (2.83V input):")
    print("-" * 70)
    print(f"{'Freq (Hz)':>12} {'Power (W)':>15} {'SPL (dB)':>15} {'Efficiency (%)':>15}")
    print("-" * 70)

    efficiencies = []
    for freq in test_frequencies:
        # Calculate acoustic power
        power = flh.acoustic_power(freq, voltage=2.83)

        # Calculate electrical power
        result = flh.electrical_impedance(freq, voltage=2.83)
        Ze = result['Ze_real'] + 1j * result['Ze_imag']
        if abs(Ze) > 0:
            Pe = (2.83**2) * Ze.real / (abs(Ze)**2)
        else:
            Pe = 0

        # Efficiency
        if Pe > 0:
            efficiency = (power / Pe) * 100  # percentage
        else:
            efficiency = 0

        efficiencies.append(efficiency)

        # Calculate SPL
        spl = flh.spl_response(freq, voltage=2.83)

        print(f"{freq:>12.0f} {power:>15.6e} {spl:>15.2f} {efficiency:>15.4f}")

    print("-" * 70)

    # Calculate frequency response across full range
    print()
    print("Frequency Response Analysis:")
    print("-" * 70)

    frequencies = np.logspace(np.log10(20), np.log10(20000), 100)
    spl_values = []

    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
        except Exception as e:
            print(f"Warning: Failed at {freq:.1f} Hz: {e}")
            spl_values.append(-100)

    spl_values = np.array(spl_values)
    valid_mask = spl_values > -200
    spl_valid = spl_values[valid_mask]

    if len(spl_valid) > 0:
        spl_min = np.min(spl_valid)
        spl_max = np.max(spl_valid)
        spl_variation = spl_max - spl_min

        print(f"  SPL range: {spl_min:.1f} to {spl_max:.1f} dB")
        print(f"  Variation: {spl_variation:.1f} dB")
        print()

        # Compare with Hornresp
        print("Comparison with Hornresp:")
        print("-" * 70)
        print(f"  Expected efficiency (from Hornresp): ~1.07%")
        print(f"  Measured efficiency (at 1 kHz): {efficiencies[3]:.4f}%")
        print(f"  Difference: {abs(efficiencies[3] - 1.07):.4f}%")
        print()
        print(f"  Expected SPL variation (from Hornresp): ~54.9 dB")
        print(f"  Measured SPL variation: {spl_variation:.1f} dB")
        print(f"  Difference: {abs(spl_variation - 54.9):.1f} dB")
        print()

        # Check if fix is successful
        # Tolerance: within 20% relative error for efficiency, 10 dB for SPL variation
        eff_error = abs(efficiencies[3] - 1.07) / 1.07 * 100
        spl_error = abs(spl_variation - 54.9)

        if eff_error < 20 and spl_error < 10:
            print("✓ FIX SUCCESSFUL: Results within acceptable tolerance!")
            print(f"  Efficiency error: {eff_error:.1f}% < 20%")
            print(f"  SPL variation error: {spl_error:.1f} dB < 10 dB")
            return True
        else:
            print("✗ FIX INCOMPLETE: Results still outside tolerance")
            print(f"  Efficiency error: {eff_error:.1f}% (target < 20%)")
            print(f"  SPL variation error: {spl_error:.1f} dB (target < 10 dB)")
            return False
    else:
        print("ERROR: No valid SPL values calculated!")
        return False


if __name__ == "__main__":
    success = test_tc2_multiseg_efficiency()
    sys.exit(0 if success else 1)
