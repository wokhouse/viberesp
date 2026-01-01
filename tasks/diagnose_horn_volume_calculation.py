#!/usr/bin/env python3
"""
Diagnostic script to trace horn volume calculation for BC_21DS115.

This investigates why the minimum horn volume is ~680 L, which seems unrealistically large.

We'll trace through the calculation for a specific design from the optimization results.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_multisegment_horn_parameter_space,
    decode_hyperbolic_design,
    build_multisegment_horn,
    calculate_multisegment_horn_volume,
)


def trace_volume_calculation(throat_area, middle_area, mouth_area, length1, length2, v_rc, label):
    """Trace through the volume calculation step by step."""

    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")

    print(f"\nHORN GEOMETRY:")
    print(f"  Throat area:  {throat_area*10000:.1f} cm² ({throat_area:.6f} m²)")
    print(f"  Middle area:  {middle_area*10000:.1f} cm² ({middle_area:.6f} m²)")
    print(f"  Mouth area:   {mouth_area*10000:.1f} cm² ({mouth_area:.6f} m²)")
    print(f"  Length 1:     {length1:.3f} m")
    print(f"  Length 2:     {length2:.3f} m")
    print(f"  Total length: {length1+length2:.3f} m")

    print(f"\nSEGMENT 1 (Throat → Middle):")
    if length1 > 0 and middle_area > throat_area:
        m1 = np.log(middle_area / throat_area) / length1
        v1 = (middle_area - throat_area) / m1
        print(f"  Flare constant m1: {m1:.4f} m⁻¹")
        print(f"  Expansion ratio:   {middle_area/throat_area:.2f}×")
        print(f"  Volume:           {v1:.6f} m³ = {v1*1000:.1f} L")
        print(f"  Formula:          V = (S₂ - S₁) / m")
        print(f"  Calculation:      ({middle_area:.6f} - {throat_area:.6f}) / {m1:.4f} = {v1:.6f} m³")

        # Also calculate what conical approximation would give
        v1_conical = (throat_area + middle_area) / 2 * length1
        print(f"  Conical approx:   {v1_conical:.6f} m³ = {v1_conical*1000:.1f} L")
        print(f"  Difference:       {v1/v1_conical:.2f}×")
    else:
        v1 = (throat_area + middle_area) / 2 * length1
        print(f"  Using trapezoidal approximation (non-expanding)")
        print(f"  Volume: {v1:.6f} m³ = {v1*1000:.1f} L")

    print(f"\nSEGMENT 2 (Middle → Mouth):")
    if length2 > 0 and mouth_area > middle_area:
        m2 = np.log(mouth_area / middle_area) / length2
        v2 = (mouth_area - middle_area) / m2
        print(f"  Flare constant m2: {m2:.4f} m⁻¹")
        print(f"  Expansion ratio:   {mouth_area/middle_area:.2f}×")
        print(f"  Volume:           {v2:.6f} m³ = {v2*1000:.1f} L")
        print(f"  Formula:          V = (S₂ - S₁) / m")
        print(f"  Calculation:      ({mouth_area:.6f} - {middle_area:.6f}) / {m2:.4f} = {v2:.6f} m³")

        # Conical approximation
        v2_conical = (middle_area + mouth_area) / 2 * length2
        print(f"  Conical approx:   {v2_conical:.6f} m³ = {v2_conical*1000:.1f} L")
        print(f"  Difference:       {v2/v2_conical:.2f}×")
    else:
        v2 = (middle_area + mouth_area) / 2 * length2
        print(f"  Using trapezoidal approximation (non-expanding)")
        print(f"  Volume: {v2:.6f} m³ = {v2*1000:.1f} L")

    horn_vol = v1 + v2
    print(f"\nTOTAL HORN VOLUME:")
    print(f"  Horn volume: {horn_vol:.6f} m³ = {horn_vol*1000:.1f} L")

    print(f"\nREAR CHAMBER:")
    print(f"  V_rc: {v_rc:.6f} m³ = {v_rc*1000:.1f} L")

    total_vol = horn_vol + v_rc
    print(f"\nTOTAL ACOUSTIC VOLUME:")
    print(f"  Total (horn + rear): {total_vol:.6f} m³ = {total_vol*1000:.1f} L")

    # Check against Olson's guidelines
    print(f"\nOLSON'S HORN THEORY CHECKS:")
    print(f"  Cutoff frequency (fc = c·m/2π):")
    c = 343.0
    fc1 = c * m1 / (2*np.pi) if length1 > 0 and middle_area > throat_area else 0
    fc2 = c * m2 / (2*np.pi) if length2 > 0 and mouth_area > middle_area else 0
    print(f"    Segment 1: {fc1:.1f} Hz")
    print(f"    Segment 2: {fc2:.1f} Hz")

    # Mouth size check
    print(f"\n  Mouth size for cutoff frequency:")
    # For fc = 70 Hz, wavelength = 343/70 = 4.9 m
    # Mouth circumference should be ≥ wavelength for good loading
    # For circular mouth: circumference = π·d = π·2·r = 2·π·√(area/π) = 2·√(π·area)
    mouth_circumference = 2 * np.sqrt(np.pi * mouth_area)
    effective_fc = max(fc1, fc2) if max(fc1, fc2) > 0 else 1.0
    wavelength_at_fc = c / effective_fc
    print(f"    Mouth circumference: {mouth_circumference:.2f} m")
    print(f"    Wavelength at cutoff: {wavelength_at_fc:.2f} m")
    if wavelength_at_fc > 0:
        print(f"    Ratio: {mouth_circumference/wavelength_at_fc:.2f}× (≥1 needed for good loading)")

    # Quarter-wavelength check
    print(f"\n  Quarter-wavelength check:")
    quarter_wave = c / (4 * effective_fc)
    print(f"    Horn length: {length1+length2:.2f} m")
    print(f"    Quarter wavelength at fc: {quarter_wave:.2f} m")
    if quarter_wave > 0:
        print(f"    Ratio: {(length1+length2)/quarter_wave:.2f}× (≥1 needed for bass loading)")

    return horn_vol, v_rc, total_vol


def analyze_parameter_space(driver, driver_name="BC_21DS115"):
    """Analyze the parameter space bounds."""

    print(f"\n{'='*80}")
    print(f"PARAMETER SPACE ANALYSIS FOR {driver_name}")
    print(f"{'='*80}")

    from viberesp.optimization.parameters.multisegment_horn_params import (
        get_multisegment_horn_parameter_space,
    )

    param_space = get_multisegment_horn_parameter_space(
        driver, preset="bass_horn", num_segments=2
    )

    print(f"\nDriver parameters:")
    print(f"  Sd:  {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")
    print(f"  Fs:  {driver.F_s:.1f} Hz")

    print(f"\nBase parameter space (bass_horn preset):")
    for i, p in enumerate(param_space.parameters):
        print(f"  {p.name:15} {p.min_value:.6f} - {p.max_value:.6f} {p.units:8}  # {p.description}")

    # Now check what happens when we expand the bounds (like in optimizer)
    print(f"\nNOTE: Optimizer EXPANDS these bounds:")
    print(f"  mouth_max:  1.5 → 2.0 m²")
    print(f"  length_max: 3.0 → 4.0 m")
    print(f"  V_rc_max:   2.0 → 3.0 × Vas")


def check_minimum_viable_horn(driver, driver_name="BC_21DS115"):
    """Calculate what the minimum viable horn should be based on theory."""

    print(f"\n{'='*80}")
    print(f"MINIMUM VIABLE HORN THEORY FOR {driver_name}")
    print(f"{'='*80}")

    c = 343.0

    # For bass extension to Fc = 70 Hz (near Fs)
    Fc = 70.0  # Hz

    print(f"\nTarget cutoff frequency: {Fc} Hz")
    print(f"Driver Fs: {driver.F_s:.1f} Hz")

    # Flare constant needed
    m_needed = 2 * np.pi * Fc / c
    print(f"\nRequired flare constant: m = 2π·fc/c = {m_needed:.4f} m⁻¹")

    # For exponential horn: S(x) = S_throat · exp(m·x)
    # At the mouth: S_mouth = S_throat · exp(m·L)
    # So: L = ln(S_mouth/S_throat) / m

    # Try different throat sizes
    print(f"\nMinimum horn length for different throat/mouth combinations:")

    throat_options = [
        (0.5 * driver.S_d, "50% Sd (compressed)"),
        (0.7 * driver.S_d, "70% Sd (mild compression)"),
        (1.0 * driver.S_d, "100% Sd (no compression)"),
    ]

    mouth_options = [
        (0.3, "Small mouth (3000 cm²)"),
        (0.5, "Medium mouth (5000 cm²)"),
        (1.0, "Large mouth (10000 cm²)"),
    ]

    print(f"\n{'Throat':>15} {'Mouth':>15} {'Expansion':>12} {'Length':>10} {'Horn Vol':>12}")
    print("-" * 75)

    for throat_area, throat_label in throat_options:
        for mouth_area, mouth_label in mouth_options:
            if mouth_area > throat_area:
                # Calculate required length
                length = np.log(mouth_area / throat_area) / m_needed

                # Calculate volume
                horn_vol = (mouth_area - throat_area) / m_needed

                print(f"{throat_area*10000:>10.0f} cm²  {mouth_area*10000:>10.0f} cm²  "
                      f"{mouth_area/throat_area:>10.2f}×  {length:>8.2f} m  {horn_vol*1000:>10.0f} L")

    # Now check what volume this gives
    print(f"\nFor comparison, let's calculate a PRACTICAL horn:")
    throat_area = 0.8 * driver.S_d  # Typical design
    mouth_area = 0.5  # m²
    m = m_needed
    length = np.log(mouth_area / throat_area) / m
    horn_vol = (mouth_area - throat_area) / m
    v_rc = driver.V_as  # Typical rear chamber

    print(f"\n  Throat:  {throat_area*10000:.0f} cm² ({throat_area/driver.S_d*100:.0f}% of Sd)")
    print(f"  Mouth:   {mouth_area*10000:.0f} cm²")
    print(f"  Length:  {length:.2f} m")
    print(f"  Horn:    {horn_vol*1000:.0f} L")
    print(f"  Rear:    {v_rc*1000:.0f} L")
    print(f"  Total:   {(horn_vol+v_rc)*1000:.0f} L (acoustic)")
    print(f"  Folded:  {(horn_vol+v_rc)*1000*1.3:.0f} L (with 30% overhead)")


def main():
    print("="*80)
    print("HORN VOLUME DIAGNOSTIC FOR BC_21DS115")
    print("="*80)

    # Load driver
    driver = load_driver("BC_21DS115")
    driver_name = "BC_21DS115"

    # 1. Analyze parameter space
    analyze_parameter_space(driver, driver_name)

    # 2. Check minimum viable horn based on theory
    check_minimum_viable_horn(driver, driver_name)

    # 3. Trace through a specific design from optimization results
    # From the BC_21DS115 results (smallest design):
    # F3: 70.3 Hz, Volume: 682 L
    # Throat: 888 cm², Mouth: 3632 cm², Length: 3.23 m
    # T1: 0.993, T2: 0.996

    trace_volume_calculation(
        throat_area=0.0888,  # m² (888 cm²)
        middle_area=0.0888,  # Assuming no middle expansion for now
        mouth_area=0.3632,   # m² (3632 cm²)
        length1=1.5,         # Estimated
        length2=1.73,        # Estimated (total 3.23 m)
        v_rc=0.198,          # m³ (Vas = 198 L)
        label="OPTIMIZER RESULT: Smallest BC_21DS115 Design (682 L)"
    )

    # 4. Try a more reasonable design
    trace_volume_calculation(
        throat_area=0.084,   # m² (50% of Sd = 840 cm²)
        middle_area=0.15,    # m²
        mouth_area=0.30,     # m²
        length1=1.5,         # m
        length2=1.5,         # m
        v_rc=0.150,          # m³
        label="THEORETICAL COMPACT DESIGN (for comparison)"
    )

    print(f"\n{'='*80}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    print("""
If the optimizer is producing 680+ L horns, the issue is likely one of:

1. **PARAMETER BOUNDS TOO LARGE**: The optimizer is searching huge ranges
   - mouth_area up to 2.0 m² (expanded from 1.5 m²)
   - length up to 4.0 m (expanded from 3.0 m)
   - This forces exploration of very large horns

2. **CONSTRAINTS TOO LOOSE**: The physical constraints allow:
   - Any mouth size (no upper constraint)
   - Any length (no upper constraint)
   - Only continuity and flare limits are enforced

3. **FLATNESS OBJECTIVE**: The optimizer may be finding that:
   - Larger horns have flatter response (better passband flatness)
   - This conflicts with volume minimization
   - Pareto front includes impractically large designs

4. **OPTIMIZER BIAS**: NSGA-II explores the full parameter space
   - Without practical upper bounds, it finds "optimal" but impractical designs
   - The 680 L minimum might actually be the smallest horn that meets
     all constraints AND achieves reasonable F3/flatness

RECOMMENDATION:
- Add MAXIMUM mouth area constraint (e.g., 0.5 m² for compact design)
- Add MAXIMUM length constraint (e.g., 2.5 m total)
- Or accept that bass horns ARE large and 680 L might be realistic
""")


if __name__ == "__main__":
    main()
