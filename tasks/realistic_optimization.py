#!/usr/bin/env python3
"""
Re-optimize BC_21DS115 horn with CORRECT volume constraints.

Previous optimization violated physics - assumed 594L rear chamber
could fit in 426L cabinet. This uses realistic constraints.

Literature:
    - Practical folded horn design
    - Volume partitioning (horn vs rear chamber)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver import load_driver
from viberesp.simulation.types import HyperbolicHorn, MultiSegmentHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
from viberesp.optimization.objectives.response_metrics import objective_f3


def realistic_optimization():
    """Optimize with correct volume constraints."""

    print("=" * 80)
    print("BC_21DS115 - REALISTIC Optimization with Volume Constraints")
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

    total_internal_volume_L = (internal_W * internal_H * internal_D) / 1000

    print(f"\nCABINET CONSTRAINTS:")
    print(f"  External: {cabinet_W:.1f} × {cabinet_H:.1f} × {cabinet_D:.1f} cm")
    print(f"  Internal: {internal_W:.1f} × {internal_H:.1f} × {internal_D:.1f} cm")
    print(f"  Total volume: {total_internal_volume_L:.1f} L")

    print(f"\n" + "=" * 80)
    print("STRATEGY: Partition Cabinet into Horn + Rear Chamber")
    print("=" * 80)

    print("""
In a folded horn, we partition the cabinet:

  ┌─────────────────────────────┐
  │  REAR CHAMBER (sealed box)  │ ← Behind driver
  │  ┌─────┐                   │
  │  │ 21" │                   │
  │  │Driver                   │
  │  └─────┘                   │
  │─────────────────────────────│ ← Baffle/separation
  │                             │
  │  HORN (folded path)        │ ← Takes most space
  │  ╱────╲  ╱────╲  ╱────╲    │
  │ ╱      ╲╱      ╲╱      ╲   │
  │╱                            │
  │└───────────────────────────┘│ ← Mouth exit
  └─────────────────────────────┘

Realistic partition:
  • Rear chamber: Top 15-20 cm of cabinet
  • Horn: Remaining volume
    """)

    # Test different partition strategies
    print("\n" + "=" * 80)
    print("TESTING REAR CHAMBER SIZES")
    print("=" * 80)

    strategies = []

    # Option 1: Small rear chamber (top 15 cm)
    rc_depth_1 = 15  # cm
    rc_volume_1 = (internal_W * internal_H * rc_depth_1) / 1000
    horn_volume_1 = total_internal_volume_L - rc_volume_1

    print(f"\n[1] Small rear chamber (top {rc_depth_1} cm)")
    print(f"  Rear chamber: {rc_volume_1:.1f} L")
    print(f"  Horn volume: {horn_volume_1:.1f} L")
    print(f"  Remaining: {100 - rc_volume_1/total_internal_volume_L*100:.1f}% for horn")

    strategies.append({
        'name': f'Small RC ({rc_depth_1}cm)',
        'V_rc_L': rc_volume_1,
        'V_rc_ratio': rc_volume_1 / driver.V_as,
        'horn_volume_L': horn_volume_1,
    })

    # Option 2: Medium rear chamber (top 20 cm)
    rc_depth_2 = 20  # cm
    rc_volume_2 = (internal_W * internal_H * rc_depth_2) / 1000
    horn_volume_2 = total_internal_volume_L - rc_volume_2

    print(f"\n[2] Medium rear chamber (top {rc_depth_2} cm)")
    print(f"  Rear chamber: {rc_volume_2:.1f} L")
    print(f"  Horn volume: {horn_volume_2:.1f} L")
    print(f"  Remaining: {100 - rc_volume_2/total_internal_volume_L*100:.1f}% for horn")

    strategies.append({
        'name': f'Medium RC ({rc_depth_2}cm)',
        'V_rc_L': rc_volume_2,
        'V_rc_ratio': rc_volume_2 / driver.V_as,
        'horn_volume_L': horn_volume_2,
    })

    # Option 3: Larger rear chamber (top 25 cm)
    rc_depth_3 = 25  # cm
    rc_volume_3 = (internal_W * internal_H * rc_depth_3) / 1000
    horn_volume_3 = total_internal_volume_L - rc_volume_3

    print(f"\n[3] Larger rear chamber (top {rc_depth_3} cm)")
    print(f"  Rear chamber: {rc_volume_3:.1f} L")
    print(f"  Horn volume: {horn_volume_3:.1f} L")
    print(f"  Remaining: {100 - rc_volume_3/total_internal_volume_L*100:.1f}% for horn")

    strategies.append({
        'name': f'Larger RC ({rc_depth_3}cm)',
        'V_rc_L': rc_volume_3,
        'V_rc_ratio': rc_volume_3 / driver.V_as,
        'horn_volume_L': horn_volume_3,
    })

    # Calculate F3 for each strategy
    # Using 5-fold design with constant height = 50 cm
    throat_area = 0.5 * driver.S_d
    mouth_area_max = internal_W * internal_H / 10000  # Max that fits

    print(f"\n" + "=" * 80)
    print("PERFORMANCE CALCULATIONS (5-Fold Design)")
    print("=" * 80)

    for i, strat in enumerate(strategies):
        print(f"\n[{i+1}] {strat['name']}:")
        print(f"  Rear chamber: {strat['V_rc_L']:.1f} L ({strat['V_rc_ratio']:.2f}×Vas)")
        print(f"  Horn volume available: {strat['horn_volume_L']:.1f} L")

        # Calculate F3 with this rear chamber
        # Using simplified horn design for calculation
        V_tc = 0.0
        V_rc = strat['V_rc_L'] / 1000  # Convert to m³

        # Use best mouth area that fits
        mouth_area = min(mouth_area_max, 0.8)  # 0.8 m² max

        # Adjust horn length to fit available volume
        # Average horn area
        avg_area = (throat_area + mouth_area) / 2
        max_horn_length = strat['horn_volume_L'] * 1000 / (avg_area * 10000)  # cm

        # Use practical length (5 folds of ~90cm each)
        horn_length = min(450, max_horn_length * 100)  # cm

        # Calculate mouth area for this length
        # Assuming exponential expansion
        m = np.log(mouth_area / throat_area) / (horn_length / 100)

        # Calculate F3 using objective function
        design_vector = np.array([throat_area, mouth_area, horn_length/100, V_tc, V_rc])

        try:
            f3 = calculate_f3_for_design(design_vector, driver)
            print(f"  Horn length: {horn_length:.0f} cm")
            print(f"  Mouth area: {mouth_area*10000:.0f} cm²")
            print(f"  F3: {f3:.1f} Hz")
            print(f"  Status: {'✓ EXCELLENT' if f3 <= 35 else '✓ GOOD' if f3 <= 40 else '⚠ OK'}")

            strat['f3'] = f3
            strat['horn_length_cm'] = horn_length
            strat['mouth_area_cm2'] = mouth_area * 10000

        except Exception as e:
            print(f"  Error calculating F3: {e}")
            strat['f3'] = None

    # Find best strategy
    valid_strategies = [s for s in strategies if s.get('f3') is not None]

    if valid_strategies:
        best = min(valid_strategies, key=lambda s: s['f3'])

        print(f"\n" + "=" * 80)
        print("RECOMMENDED DESIGN")
        print("=" * 80)

        print(f"\n🏆 BEST: {best['name']}")
        print(f"   Rear chamber: {best['V_rc_L']:.1f} L ({best['V_rc_ratio']:.2f}×Vas)")
        print(f"   F3: {best['f3']:.1f} Hz")
        print(f"   Horn length: {best['horn_length_cm']:.0f} cm (5 folds)")
        print(f"   Mouth area: {best['mouth_area_cm2']:.0f} cm²")

        # Check if F3 target achievable
        if best['f3'] <= 30:
            print(f"\n  ✓✓ MEETS F3 ≤ 30 Hz TARGET!")
        elif best['f3'] <= 35:
            print(f"\n  ✓ Very close to target (within 5 Hz)")
            print(f"    Excellent performance for subwoofer!")
        elif best['f3'] <= 40:
            print(f"\n  ✓ Good bass extension")
            print(f"    Still hits most sub-bass goals")
        else:
            print(f"\n  ⚠ Higher than desired")
            print(f"    Consider larger cabinet or compromise")

    # Generate comparison plot
    print("\nGenerating comparison plot...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: F3 comparison
    if valid_strategies:
        names = [s['name'] for s in valid_strategies]
        f3s = [s['f3'] for s in valid_strategies]
        rc_vols = [s['V_rc_L'] for s in valid_strategies]

        colors = ['green' if f3 <= 30 else 'lightgreen' if f3 <= 35 else 'yellow' if f3 <= 40 else 'orange'
                  for f3 in f3s]

        ax1.bar(range(len(names)), f3s, color=colors, alpha=0.7, edgecolor='black')
        ax1.axhline(30, color='r', linestyle='--', linewidth=2, label='Target F3 = 30 Hz')
        ax1.axhline(40, color='orange', linestyle='--', linewidth=1, label='Good bass (<40 Hz)')
        ax1.set_xticks(range(len(names)))
        ax1.set_xticklabels(names, rotation=15, ha='right')
        ax1.set_ylabel('F3 (Hz)', fontsize=11)
        ax1.set_title('F3 vs Rear Chamber Size', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for i, (name, f3) in enumerate(zip(names, f3s)):
            ax1.text(i, f3 + 1, f'{f3:.1f} Hz', ha='center', fontsize=9, fontweight='bold')

    # Plot 2: Volume breakdown
    total_vol = total_internal_volume_L

    for i, s in enumerate(valid_strategies):
        rc_vol = s['V_rc_L']
        horn_vol = s['horn_volume_L']

        ax2.bar(i, rc_vol, color='purple', alpha=0.7, label='Rear Chamber' if i == 0 else '')
        ax2.bar(i, horn_vol, bottom=rc_vol, color='blue', alpha=0.7, label='Horn' if i == 0 else '')

        ax2.text(i, rc_vol/2, f'{rc_vol:.0f}L', ha='center', fontsize=8, color='white', fontweight='bold')
        ax2.text(i, rc_vol + horn_vol/2, f'{horn_vol:.0f}L', ha='center', fontsize=8, color='white', fontweight='bold')

    ax2.set_xticks(range(len(valid_strategies)))
    ax2.set_xticklabels([s['name'] for s in valid_strategies], rotation=15, ha='right')
    ax2.set_ylabel('Volume (Liters)', fontsize=11)
    ax2.set_title('Cabinet Volume Partition', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Trade-off curve
    if valid_strategies:
        rc_vols = [s['V_rc_L'] for s in valid_strategies]
        f3s = [s['f3'] for s in valid_strategies]

        ax3.plot(rc_vols, f3s, 'o-', linewidth=3, markersize=10, color='blue')
        ax3.set_xlabel('Rear Chamber Volume (L)', fontsize=11)
        ax3.set_ylabel('F3 (Hz)', fontsize=11)
        ax3.set_title('F3 vs Rear Chamber Size', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)

        for i, (rc, f3) in enumerate(zip(rc_vols, f3s)):
            ax3.annotate(f'{f3:.1f} Hz', xy=(rc, f3), xytext=(5, 5), textcoords='offset points',
                        fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))

        # Mark target
        ax3.axhline(30, color='r', linestyle='--', alpha=0.5, label='Target: 30 Hz')
        ax3.legend()

    # Plot 4: Cabinet layout (best strategy)
    ax4.axis('off')

    if valid_strategies:
        best = min(valid_strategies, key=lambda s: s['f3'])
        rc_depth = int(best['name'].split('(')[1].split('cm')[0])

        layout_text = f"""
RECOMMENDED LAYOUT: {best['name']}
══════════════════════════════════════════

CABINET: {cabinet_W:.0f} × {cabinet_H:.0f} × {cabinet_D:.0f} cm (45" × 30" × 22.5")

TOP VIEW (from above):
┌─────────────────────────────────────┐
│ REAR CHAMBER (sealed box)            │
│ {rc_depth}cm depth │
│ ┌─────────┐                           │
│ │ 21"     │                           │
│ │ Driver  │                           │
│ └─────────┘                           │
├─────────────────────────────────────┤ ← Baffle
│                                     │
│ HORN (5 diagonal folds)              │
│ ╱──── Fold 1                        │
│╱      ╲ Fold 2                      │
│        ╱──── Fold 3                 │
│       ╱      ╲                      │
│      ╱──── Fold 4                   │
│     ╱                               │
│    ╱── Fold 5 → MOUTH               │
│                                     │
└─────────────────────────────────────┘

SPECIFICATIONS:
  Rear chamber:  {best['V_rc_L']:.1f} L ({best['V_rc_ratio']:.2f} × Vas)
  Horn:         5 diagonal folds, 90 cm each
  Horn volume:   {best['horn_volume_L']:.0f} L
  Mouth:        {best['mouth_area_cm2']:.0f} cm² (rectangular)
  Height:       Constant 50 cm (builds easy!)

PERFORMANCE:
  F3:           {best['f3']:.1f} Hz
  Target:       ≤30 Hz
  Status:       {'✓ EXCELLENT!' if best['f3'] <= 30 else '✓ VERY GOOD' if best['f3'] <= 35 else '✓ GOOD'}

CONSTRUCTION:
  • Build cabinet shell: 45×30×22.5"
  • Install horizontal baffle at {rc_depth} cm from top
  • Mount driver on baffle
  • Above baffle: Sealed rear chamber
  • Below baffle: 5-fold horn path
  • Mouth exits at bottom
        """

        ax4.text(0.05, 0.95, layout_text, transform=ax4.transAxes,
                fontsize=9, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

    plt.suptitle('Realistic Horn Optimization - Volume-Constrained Design',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    plt.savefig('tasks/realistic_optimization_results.png', dpi=150, bbox_inches='tight')
    print("\n  Saved: tasks/realistic_optimization_results.png")

    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)


def calculate_f3_for_design(design_vector, driver):
    """Calculate F3 for a given design."""

    V_rc = design_vector[4]

    # Create simple horn model
    throat_area = design_vector[0]
    mouth_area = design_vector[1]
    horn_length = design_vector[2]

    seg1 = HyperbolicHorn(throat_area, (throat_area + mouth_area)/2, horn_length/2, T=0.7)
    seg2 = HyperbolicHorn((throat_area + mouth_area)/2, mouth_area, horn_length/2, T=1.0)
    horn = MultiSegmentHorn([seg1, seg2])

    flh = FrontLoadedHorn(driver, horn, V_tc=0.0, V_rc=V_rc)

    # Calculate F3
    frequencies = np.logspace(np.log10(20), np.log10(200), 150)
    spl_values = []

    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)
        except:
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Find reference SPL
    passband_mask = (frequencies >= 50) & (frequencies <= 200)
    reference_spl = np.max(spl_values[passband_mask])
    target_spl = reference_spl - 3.0

    # Find F3
    for i in range(len(frequencies) - 1):
        if spl_values[i] < target_spl and spl_values[i+1] >= target_spl:
            f1, f2 = frequencies[i], frequencies[i+1]
            spl1, spl2 = spl_values[i], spl_values[i+1]
            log_f3 = np.log10(f1) + (np.log10(f2) - np.log10(f1)) * (target_spl - spl1) / (spl2 - spl1)
            return 10**log_f3

    return frequencies[0]  # Return lowest freq if F3 not found


if __name__ == "__main__":
    realistic_optimization()
