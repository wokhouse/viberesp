#!/usr/bin/env python3
"""
Check if 594L rear chamber actually fits in the cabinet.

This is a critical validation - the rear chamber takes up ACTUAL PHYSICAL SPACE
that competes with the horn volume.

Literature:
    - Practical cabinet volume calculations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver import load_driver
from viberesp.simulation.types import HyperbolicHorn


def check_rear_chamber_fit():
    """Validate if 594L rear chamber fits with horn volume."""

    print("=" * 80)
    print("CRITICAL CHECK: Will 594L Rear Chamber Actually Fit?")
    print("=" * 80)

    driver = load_driver("BC_21DS115")

    # Cabinet dimensions
    cabinet_W = 114.3  # cm (45")
    cabinet_H = 76.2   # cm (30")
    cabinet_D = 57.1   # cm (22.5")

    # Internal dimensions
    wall_thickness = 1.9  # cm
    internal_W = cabinet_W - 2 * wall_thickness
    internal_H = cabinet_H - 2 * wall_thickness
    internal_D = cabinet_D - 2 * wall_thickness

    # Total internal volume
    total_internal_volume_L = (internal_W * internal_H * internal_D) / 1000

    print(f"\nCABINET DIMENSIONS:")
    print(f"  External: {cabinet_W:.1f} × {cabinet_H:.1f} × {cabinet_D:.1f} cm")
    print(f"  Internal: {internal_W:.1f} × {internal_H:.1f} × {internal_D:.1f} cm")
    print(f"  Total internal volume: {total_internal_volume_L:.1f} L")

    # Horn parameters
    throat_area = 0.5 * driver.S_d
    mouth_area = 0.4716  # m²
    length1 = 2.0  # m
    length2 = 2.5  # m
    total_length = 4.5  # m
    T1 = 0.7
    T2 = 1.0
    const_height = 0.50  # m (50 cm)

    # Calculate horn volume (actual space horn takes up)
    seg1 = HyperbolicHorn(throat_area, 0.20, length1, T=T1)
    seg2 = HyperbolicHorn(0.20, mouth_area, length2, T=T2)

    # Calculate horn volume using numerical integration
    num_points = 1000
    horn_volume_m3 = 0.0

    x_points = np.linspace(0, total_length, num_points)

    for x in x_points:
        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        horn_volume_m3 += area * (total_length / num_points)

    horn_volume_L = horn_volume_m3 * 1000

    print(f"\nHORN VOLUME:")
    print(f"  Horn path length: {total_length*100:.0f} cm")
    print(f"  Average cross-section: ~{(throat_area + mouth_area)/2*10000:.0f} cm²")
    print(f"  Horn physical volume: {horn_volume_L:.1f} L")

    # Desired rear chamber
    desired_rear_chamber_L = 3.0 * driver.V_as  # 594 L

    print(f"\nDESIRED REAR CHAMBER:")
    print(f"  Target: {desired_rear_chamber_L:.1f} L (3.0 × Vas)")

    # Check if fits
    available_for_rear_L = total_internal_volume_L - horn_volume_L

    print(f"\nSPACE CHECK:")
    print(f"  Total cabinet volume: {total_internal_volume_L:.1f} L")
    print(f"  Horn volume:          {horn_volume_L:.1f} L")
    print(f"  Remaining for rear:   {available_for_rear_L:.1f} L")
    print(f"  Required rear:        {desired_rear_chamber_L:.1f} L")

    if desired_rear_chamber_L > available_for_rear_L:
        deficit = desired_rear_chamber_L - available_for_rear_L
        print(f"\n❌ PROBLEM: Need {deficit:.1f} L more space!")
        print(f"   The rear chamber WON'T FIT!")
        print(f"   We only have {available_for_rear_L:.1f} L available, need {desired_rear_chamber_L:.1f} L")
    else:
        surplus = available_for_rear_L - desired_rear_chamber_L
        print(f"\n✓ OK: {surplus:.1f} L to spare")

    print("\n" + "=" * 80)
    print("WHAT'S ACTUALLY POSSIBLE?")
    print("=" * 80)

    # Maximum practical rear chamber
    max_rear_chamber_L = available_for_rear_L * 0.9  # Leave 10% for driver, structure

    print(f"\nMaximum rear chamber that fits: {max_rear_chamber_L:.1f} L")
    print(f"This is: {max_rear_chamber_L / driver.V_as:.2f} × Vas")

    # Recalculate F3 with smaller rear chamber
    print(f"\nREAR CHAMBER SIZE OPTIONS:")

    rear_options = [
        (max_rear_chamber_L, "Maximum that fits"),
        (2.0 * driver.V_as, "2.0 × Vas"),
        (1.5 * driver.V_as, "1.5 × Vas"),
        (1.0 * driver.V_as, "1.0 × Vas"),
    ]

    print(f"\n{'Rear Chamber':<20} {'Vas Ratio':<12} {'F3 Impact':<20}")
    print("-" * 60)

    for V_rc, description in rear_options:
        if V_rc <= max_rear_chamber_L:
            vas_ratio = V_rc / driver.V_as
            # Rough F3 estimate: smaller V_rc = higher F3
            # Original: 3.0×Vas → 29.7 Hz
            # Linear approximation (not exact, but indicative)
            f3_estimate = 29.7 * (3.0 / vas_ratio)**0.5

            fits = "✓"
            print(f"{V_rc:>6.1f} L ({description:<12}) {vas_ratio:>8.2f}×   ~{f3_estimate:>5.1f} Hz {fits}")
        else:
            print(f"{V_rc:>6.1f} L ({description:<12})         ❌ Won't fit")

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    best_V_rc = min([opt[0] for opt in rear_options if opt[0] <= max_rear_chamber_L])
    vas_ratio = best_V_rc / driver.V_as

    print(f"\n✓ Maximum realistic rear chamber: {best_V_rc:.1f} L ({vas_ratio:.2f} × Vas)")
    print(f"  This is what will actually FIT in your cabinet")
    print(f"  Expected F3: ~{29.7 * (3.0 / vas_ratio)**0.5:.1f} Hz (still excellent!)")

    print(f"\n  Trade-off:")
    print(f"    Original plan: 3.0×Vas → F3 = 29.7 Hz ❌ Won't fit")
    print(f"    Maximum fit:  {vas_ratio:.2f}×Vas → F3 ~ {29.7 * (3.0 / vas_ratio)**0.5:.1f} Hz ✓")

    if 29.7 * (3.0 / vas_ratio)**0.5 <= 30.0:
        print(f"\n  ✓ Still meets F3 ≤ 30 Hz target!")
    else:
        f3_new = 29.7 * (3.0 / vas_ratio)**0.5
        print(f"\n  ⚠ F3 increases to {f3_new:.1f} Hz (close to 30 Hz target)")

    print(f"\n  Alternative solutions:")
    print(f"    1. Use {max_rear_chamber_L:.1f} L rear chamber (fits, F3 ~{29.7 * (3.0 / (max_rear_chamber_L/driver.V_as))**0.5:.1f} Hz)")
    print(f"    2. Increase cabinet size to fit 594 L")
    print(f"    3. Use external rear chamber (box behind cabinet)")

    # Calculate required cabinet size for 594L
    required_V_rc = 3.0 * driver.V_as
    required_extra_L = required_V_rc - max_rear_chamber_L

    # If we increase depth
    extra_depth_cm = (required_extra_L * 1000) / (internal_W * internal_H)

    print(f"\n  To fit 594 L rear chamber:")
    print(f"    Current depth: {cabinet_D:.1f} cm")
    print(f"    Required depth: {cabinet_D + extra_depth_cm:.1f} cm (+{extra_depth_cm:.1f} cm)")

    # Create visualization
    print("\nGenerating volume comparison plot...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Plot 1: Volume breakdown
    volumes = ['Horn\nVolume', 'Available\nRear Chamber', 'Required\nRear Chamber (594L)']
    values = [horn_volume_L, available_for_rear_L, desired_rear_chamber_L]
    colors = ['blue', 'green', 'red' if desired_rear_chamber_L > available_for_rear_L else 'lightgreen']

    bars = ax1.bar(volumes, values, color=colors, alpha=0.7, edgecolor='black')

    ax1.set_ylabel('Volume (Liters)', fontsize=11)
    ax1.set_title('Cabinet Volume Breakdown', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Add value labels
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                f'{val:.0f} L', ha='center', fontsize=11, fontweight='bold')

    # Plot 2: What fits and what doesn't
    categories = ['Horn', 'Max Rear\nChamber', '594L\nRear Chamber']
    fits_or_not = [horn_volume_L, max_rear_chamber_L, desired_rear_chamber_L]
    bar_colors = ['green' if v <= total_internal_volume_L else 'red' for v in fits_or_not]

    ax2.bar(categories, fits_or_not, color=bar_colors, alpha=0.7, edgecolor='black')
    ax2.axhline(total_internal_volume_L, color='blue', linestyle='--', linewidth=2,
               label=f'Total Cabinet: {total_internal_volume_L:.0f} L')
    ax2.set_ylabel('Volume (Liters)', fontsize=11)
    ax2.set_title('What Fits vs What We Want', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')

    # Add labels
    for i, (cat, val) in enumerate(zip(categories, fits_or_not)):
        if val > total_internal_volume_L:
            ax2.text(i, val - 30, f"❌\n{val:.0f}L\nToo big!",
                    ha='center', fontsize=10, fontweight='bold', color='darkred')
        else:
            ax2.text(i, val + 10, f"✓\n{val:.0f}L",
                    ha='center', fontsize=10, fontweight='bold')

    plt.suptitle(f'Cabinet Volume Analysis - 594L Rear Chamber: ❌ WON\'T FIT!',
                 fontsize=14, fontweight='bold', color='red')
    plt.tight_layout()

    plt.savefig('tasks/rear_chamber_volume_check.png', dpi=150, bbox_inches='tight')
    print("\n  Saved: tasks/rear_chamber_volume_check.png")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    check_rear_chamber_fit()
