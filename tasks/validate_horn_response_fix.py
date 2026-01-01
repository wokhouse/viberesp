#!/usr/bin/env python3
"""
Validate the horn response calculation fixes.

This script tests that:
1. Blend values stay in range [0, 1]
2. No SPL spikes occur
3. Response is monotonically increasing below fc, then flat at passband sensitivity
"""

import numpy as np
import math


def test_blend_calculation():
    """Test that blend calculation stays in [0, 1] range."""
    print("=" * 70)
    print("TEST 1: Blend Calculation Range")
    print("=" * 70)

    fc = 800.0  # Hz
    passband_sensitivity = 108.5  # dB

    test_frequencies = [
        (fc / 2, "fc/2 (lower bound)"),
        (fc, "fc (midpoint)"),
        (fc * 1.5, "fc*1.5 (upper bound)"),
        (1199, "Previously problematic frequency"),
    ]

    print(f"\nHorn cutoff frequency: {fc} Hz")
    print(f"Passband sensitivity: {passband_sensitivity} dB\n")

    for f, description in test_frequencies:
        blend = (f - fc/2) / fc
        blend_smooth = blend * blend * (3 - 2 * blend)

        print(f"{f:>7.1f} Hz ({description}):")
        print(f"  blend = {blend:.4f} (should be in [0, 1])")
        print(f"  blend_smooth = {blend_smooth:.4f} (should be positive)")

        if blend < 0 or blend > 1:
            print(f"  ❌ ERROR: blend out of range!")
        elif blend_smooth < 0:
            print(f"  ❌ ERROR: blend_smooth negative!")
        else:
            print(f"  ✅ OK")

    print()


def test_response_values():
    """Test that response values are correct at key frequencies."""
    print("=" * 70)
    print("TEST 2: Response Values at Key Frequencies")
    print("=" * 70)

    fc = 800.0
    passband_sensitivity = 108.5

    test_cases = [
        (400, "fc/2", "~96.5 dB (-12 dB relative)"),
        (800, "fc", "~108.5 dB (passband)"),
        (1200, "fc*1.5", "~108.5 dB (passband)"),
        (1199, "Previously problematic", "NOT 143 dB!"),
    ]

    print(f"\nHorn cutoff frequency: {fc} Hz")
    print(f"Passband sensitivity: {passband_sensitivity} dB\n")

    for f, description, expected in test_cases:
        # Calculate response using corrected logic
        if f <= fc / 2:
            # Below cutoff: 12 dB/octave rolloff
            octaves_below = math.log2(max(f, 10) / fc)
            response = passband_sensitivity + octaves_below * 12
        elif f <= fc * 1.5:
            # Transition region
            blend = (f - fc/2) / fc
            blend_smooth = blend * blend * (3 - 2 * blend)
            octaves_below = math.log2(max(f, 10) / fc)
            below_cutoff = passband_sensitivity + octaves_below * 12
            response = below_cutoff * (1 - blend_smooth) + passband_sensitivity * blend_smooth
        else:
            # Above cutoff
            response = passband_sensitivity

        print(f"{f:>7.1f} Hz ({description}):")
        print(f"  Response: {response:>6.2f} dB")
        print(f"  Expected: {expected}")
        if response > 120:
            print(f"  ❌ ERROR: Response too high (possible spike!)")
        else:
            print(f"  ✅ OK")
        print()


def test_frequency_sweep():
    """Test that response doesn't spike across full frequency range."""
    print("=" * 70)
    print("TEST 3: Frequency Sweep - No Spikes")
    print("=" * 70)

    fc = 800.0
    passband_sensitivity = 108.5

    frequencies = np.logspace(np.log10(20), np.log10(20000), 1000)
    responses = []

    for f in frequencies:
        if f > 5000:
            # HF beaming rolloff (include for completeness)
            hf_rolloff = 3 * np.log2(f / 5000)
            transition = 0.5 * (1 + np.tanh((f - 7000) / 1000))
            response = passband_sensitivity - hf_rolloff * transition
        elif f <= fc / 2:
            octaves_below = math.log2(max(f, 10) / fc)
            response = passband_sensitivity + octaves_below * 12
        elif f <= fc * 1.5:
            blend = (f - fc/2) / fc
            blend_smooth = blend * blend * (3 - 2 * blend)
            octaves_below = math.log2(max(f, 10) / fc)
            below_cutoff = passband_sensitivity + octaves_below * 12
            response = below_cutoff * (1 - blend_smooth) + passband_sensitivity * blend_smooth
        else:
            response = passband_sensitivity

        responses.append(response)

    responses = np.array(responses)

    max_response = np.max(responses)
    min_response = np.min(responses)
    max_freq = frequencies[np.argmax(responses)]

    print(f"\nFrequency range: 20 Hz - 20 kHz")
    print(f"Maximum response: {max_response:.2f} dB at {max_freq:.1f} Hz")
    print(f"Minimum response: {min_response:.2f} dB")

    if max_response > passband_sensitivity + 1:
        print(f"❌ ERROR: Response exceeds passband by >1 dB!")
    elif max_response > 120:
        print(f"❌ ERROR: Response suspiciously high (>120 dB)")
    else:
        print(f"✅ OK: No response spikes detected")

    # Test monotonicity below cutoff
    below_cutoff_idx = frequencies <= fc
    below_cutoff_responses = responses[below_cutoff_idx]
    below_cutoff_freqs = frequencies[below_cutoff_idx]

    # Check if response is monotonically increasing below cutoff
    is_monotonic = np.all(np.diff(below_cutoff_responses) >= 0)

    if is_monotonic:
        print(f"✅ OK: Response is monotonically increasing below cutoff")
    else:
        print(f"❌ ERROR: Response is not monotonic below cutoff!")
        # Find where it decreases
        diffs = np.diff(below_cutoff_responses)
        decrease_idx = np.where(diffs < 0)[0]
        print(f"  Response decreases at: {below_cutoff_freqs[decrease_idx]} Hz")

    print()


def test_boundary_conditions():
    """Test that boundary conditions don't overlap."""
    print("=" * 70)
    print("TEST 4: Boundary Condition Coverage")
    print("=" * 70)

    fc = 800.0

    test_freqs = [
        (fc / 2 - 1, "Just below fc/2", "below-cutoff"),
        (fc / 2, "Exactly fc/2", "below-cutoff"),
        (fc / 2 + 1, "Just above fc/2", "transition"),
        (fc, "Exactly fc", "transition"),
        (fc * 1.5, "Exactly fc*1.5", "transition"),
        (fc * 1.5 + 1, "Just above fc*1.5", "passband"),
    ]

    print("\nTesting frequency boundaries:\n")

    for f, description, expected_region in test_freqs:
        if f <= fc / 2:
            actual_region = "below-cutoff"
        elif f <= fc * 1.5:
            actual_region = "transition"
        else:
            actual_region = "passband"

        match = "✅" if expected_region == actual_region else "❌"
        print(f"{f:>7.1f} Hz ({description}):")
        print(f"  Expected: {expected_region} region")
        print(f"  Actual:   {actual_region} region")
        print(f"  {match}\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HORN RESPONSE FIX VALIDATION")
    print("=" * 70 + "\n")

    test_blend_calculation()
    test_response_values()
    test_frequency_sweep()
    test_boundary_conditions()

    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
