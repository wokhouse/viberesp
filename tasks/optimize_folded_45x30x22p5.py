#!/usr/bin/env python3
"""
Optimize BC_21DS115 for 45"×30"×22.5" folded cabinet targeting F3 ≤ 30 Hz.

Physical constraints:
- External dimensions: 45" × 30" × 22.5" (114 × 76 × 57 cm)
- Mouth area limited by cabinet: ~114×76 cm max
- Horn must fold to fit within depth of 57 cm
- Target: F3 ≤ 30 Hz

Literature:
    - Olson (1947) - Folded horn design principles
    - Klipschorn - Classic folded horn corner loading
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


def analyze_folded_design(driver, throat_area, middle_area, mouth_area,
                          length1, length2, T1, T2, V_tc, V_rc,
                          cabinet_dims, label):
    """Analyze a folded horn design within cabinet constraints."""

    # Build horn
    seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=T1)
    seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=T2)
    horn = MultiSegmentHorn([seg1, seg2])

    flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

    # Calculate F3
    design_vector = np.array([throat_area, middle_area, mouth_area,
                              length1, length2, T1, T2, V_tc, V_rc])
    f3 = objective_f3(design_vector, driver, "multisegment_horn")

    # Calculate frequency response for SPL
    frequencies = np.logspace(np.log10(20), np.log10(200), 100)
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

    # Calculate folding feasibility
    total_length = length1 + length2
    width_ext, height_ext, depth_ext = cabinet_dims  # External dimensions in cm

    # Estimate folded length capacity
    # Simple fold pattern: back-and-forth along depth dimension
    # Assume 2-3 segments for practical folding
    depth_internal = depth_ext * 0.9  # Account for wall thickness
    num_folds = int(total_length * 100 / depth_internal) + 1

    # Check if mouth fits in cabinet
    mouth_width_cm = np.sqrt(mouth_area) * 100
    mouth_fits = (mouth_width_cm <= width_ext * 0.95 and
                  mouth_width_cm <= height_ext * 0.95)

    # Calculate horn volume
    m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
    m2 = np.log(mouth_area / middle_area) / length2 if length2 > 0 else 0

    v1 = (middle_area - throat_area) / m1 if m1 > 0 else (throat_area + middle_area) / 2 * length1
    v2 = (mouth_area - middle_area) / m2 if m2 > 0 else (middle_area + mouth_area) / 2 * length2
    horn_volume = v1 + v2

    return {
        'label': label,
        'f3': f3,
        'reference_spl': reference_spl,
        'total_length': total_length,
        'horn_volume': horn_volume,
        'mouth_area': mouth_area,
        'mouth_width_cm': mouth_width_cm,
        'mouth_fits': mouth_fits,
        'num_folds_estimate': num_folds,
        'compression_ratio': driver.S_d / throat_area,
        'flare_mL1': m1 * length1 if m1 > 0 else 0,
        'flare_mL2': m2 * length2 if m2 > 0 else 0,
    }


def main():
    print("=" * 80)
    print("BC_21DS115 Folded Horn Design - 45×30×22.5\" Cabinet")
    print("Target: F3 ≤ 30 Hz")
    print("=" * 80)

    # Load driver
    print("\nLoading driver...")
    driver = load_driver("BC_21DS115")
    print(f"  Driver: BC_21DS115")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")

    # Cabinet dimensions
    cabinet_ext = (114.3, 76.2, 57.15)  # cm (45", 30", 22.5")

    print(f"\n" + "=" * 80)
    print("CABINET CONSTRAINTS")
    print("=" * 80)
    print(f"\nExternal dimensions: {cabinet_ext[0]:.1f} × {cabinet_ext[1]:.1f} × {cabinet_ext[2]:.1f} cm")
    print(f"                   (45\" × 30\" × 22.5\")")
    print(f"\nFolding constraints:")
    print(f"  Max mouth: ~{min(cabinet_ext[0], cabinet_ext[1]):.0f} × {min(cabinet_ext[0], cabinet_ext[1]):.0f} cm")
    print(f"  Max mouth area: ~{min(cabinet_ext[0], cabinet_ext[1])**2/10000:.2f} m²")
    print(f"  Fold depth: {cabinet_ext[2]:.1f} cm")

    # Estimate practical limits
    max_mouth_area = (min(cabinet_ext[0], cabinet_ext[1]) * 0.95)**2 / 10000  # m²
    max_folded_length = cabinet_ext[2] * 0.9 / 100  # m (effective depth after wall thickness)

    print(f"\nPractical limits:")
    print(f"  Max mouth area: {max_mouth_area:.3f} m² ({max_mouth_area*10000:.0f} cm²)")
    print(f"  Max folded segment length: {max_folded_length:.2f} m")

    # Design exploration
    print("\n" + "=" * 80)
    print("TESTING FOLDED HORN DESIGNS")
    print("=" * 80)

    Sd = driver.S_d
    designs = []

    # Design 1: Conservative (fits easily)
    print("\n[1] Conservative design (small mouth, shorter)")
    designs.append(analyze_folded_design(
        driver,
        throat_area=0.5 * Sd,      # 840 cm²
        middle_area=0.15,          # 1500 cm²
        mouth_area=0.60,           # 6000 cm² (fits in 114×76)
        length1=1.5,               # Shorter segments
        length2=2.0,
        T1=0.7,                    # Hypex for bass
        T2=1.0,
        V_tc=0.0,
        V_rc=3.0 * driver.V_as,    # Large rear chamber
        cabinet_dims=cabinet_ext,
        label="Conservative (0.6 m²)"
    ))

    # Design 2: Maximum mouth for cabinet
    print("\n[2] Maximum mouth area")
    designs.append(analyze_folded_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.20,
        mouth_area=max_mouth_area * 0.9,  # 90% of max
        length1=2.0,
        length2=2.5,
        T1=0.7,
        T2=1.0,
        V_tc=0.0,
        V_rc=3.0 * driver.V_as,
        cabinet_dims=cabinet_ext,
        label="Max mouth"
    ))

    # Design 3: Longer horn (more aggressive folding)
    print("\n[3] Longer horn (4.5 m total)")
    designs.append(analyze_folded_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.18,
        mouth_area=0.70,
        length1=2.2,
        length2=2.3,
        T1=0.65,
        T2=0.9,
        V_tc=0.0,
        V_rc=3.5 * driver.V_as,    # Even larger rear chamber
        cabinet_dims=cabinet_ext,
        label="Longer horn"
    ))

    # Design 4: Balanced approach
    print("\n[4] Balanced design")
    designs.append(analyze_folded_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.18,
        mouth_area=0.65,
        length1=1.8,
        length2=2.2,
        T1=0.7,
        T2=0.95,
        V_tc=0.0,
        V_rc=3.0 * driver.V_as,
        cabinet_dims=cabinet_ext,
        label="Balanced"
    ))

    # Design 5: Aggressive rear chamber
    print("\n[5] Aggressive rear chamber tuning")
    designs.append(analyze_folded_design(
        driver,
        throat_area=0.5 * Sd,
        middle_area=0.15,
        mouth_area=0.55,
        length1=1.5,
        length2=2.0,
        T1=0.7,
        T2=1.0,
        V_tc=0.0,
        V_rc=4.0 * driver.V_as,    # 4×Vas!
        cabinet_dims=cabinet_ext,
        label="Aggressive V_rc"
    ))

    # Print results
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    print(f"\n{'Design':<20} {'F3':<8} {'SPL':<8} {'Length':<10} {'Mouth':<10} {'Fits?':<8} {'Folds':<8}")
    print("-" * 88)

    for d in designs:
        fits_str = "✓" if d['mouth_fits'] else "✗"
        print(f"{d['label']:<20} {d['f3']:<8.1f} {d['reference_spl']:<8.1f} "
              f"{d['total_length']:<10.1f} {d['mouth_area']*10000:<10.0f} "
              f"{fits_str:<8} {d['num_folds_estimate']:<8}")

    # Find best design meeting F3 ≤ 30 Hz
    viable_designs = [d for d in designs if d['f3'] <= 30.0 and d['mouth_fits']]

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if viable_designs:
        best = min(viable_designs, key=lambda d: d['f3'])

        print(f"\n✓ BEST DESIGN meeting F3 ≤ 30 Hz: {best['label']}")
        print(f"  F3: {best['f3']:.1f} Hz (target: ≤30 Hz)")
        print(f"  Reference SPL: {best['reference_spl']:.1f} dB")
        print(f"  Total length: {best['total_length']:.2f} m")
        print(f"  Mouth area: {best['mouth_area']*10000:.0f} cm² ({best['mouth_width_cm']:.0f}×{best['mouth_width_cm']:.0f} cm)")
        print(f"  Rear chamber: {3.0*driver.V_as*1000:.0f} L")
        print(f"  Estimated folds: {best['num_folds_estimate']}")
        print(f"  Mouth fits cabinet: {'✓' if best['mouth_fits'] else '✗'}")

    else:
        print(f"\n⚠ No design meets F3 ≤ 30 Hz with these constraints")
        best_overall = min(designs, key=lambda d: d['f3'])
        print(f"\nClosest design: {best_overall['label']}")
        print(f"  F3: {best_overall['f3']:.1f} Hz (need {best_overall['f3']-30:.1f} Hz lower)")

    # Folding analysis for best design
    best_for_folding = min(designs, key=lambda d: d['f3'])

    print(f"\n" + "=" * 80)
    print("FOLDING PATTERN ANALYSIS")
    print("=" * 80)

    print(f"\nSelected design: {best_for_folding['label']}")
    print(f"Total unfolded length: {best_for_folding['total_length']:.2f} m ({best_for_folding['total_length']*100:.0f} cm)")

    depth_internal = cabinet_ext[2] * 0.9  # 57.15 * 0.9 = 51.4 cm
    print(f"Internal cabinet depth: {depth_internal:.1f} cm")

    # Calculate fold segments
    segment_length = depth_internal  # Each fold segment = internal depth
    num_segments = int(np.ceil(best_for_folding['total_length'] * 100 / segment_length))

    print(f"\nFolding pattern: {num_segments} segments")
    print(f"  Each segment length: ~{segment_length:.1f} cm")
    print(f"  Total path length: {num_segments * segment_length:.0f} cm")
    print(f"  Utilization: {(best_for_folding['total_length']*100)/(num_segments*segment_length)*100:.1f}%")

    print(f"\nFold layout (unfolded → folded):")
    current_length = 0
    fold_num = 1

    while current_length < best_for_folding['total_length']:
        remaining = best_for_folding['total_length'] - current_length
        this_segment = min(remaining * 100, segment_length)

        direction = "→ (front to back)" if fold_num % 2 == 1 else "← (back to front)"
        print(f"  Fold {fold_num}: {this_segment:.1f} cm {direction}")

        current_length += this_segment / 100
        fold_num += 1

        if fold_num > 20:  # Safety limit
            break

    # Cabinet footprint check
    print(f"\nCabinet footprint check:")
    print(f"  External: {cabinet_ext[0]:.1f} × {cabinet_ext[1]:.1f} × {cabinet_ext[2]:.1f} cm")
    print(f"  (45\" × 30\" × 22.5\")")

    mouth_dim = best_for_folding['mouth_width_cm']
    print(f"  Mouth size: {mouth_dim:.0f} × {mouth_dim:.0f} cm")
    print(f"  Fits in opening: {'✓' if mouth_dim <= min(cabinet_ext[0], cabinet_ext[1]) * 0.95 else '✗'}")

    # Generate comparison plot
    print("\nGenerating comparison plots...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: F3 comparison
    labels = [d['label'] for d in designs]
    f3s = [d['f3'] for d in designs]
    colors = ['green' if f3 <= 30.0 else 'orange' if f3 <= 35.0 else 'red' for f3 in f3s]

    ax1.barh(range(len(labels)), f3s, color=colors, alpha=0.7)
    ax1.axvline(30.0, color='r', linestyle='--', linewidth=2, label='Target F3 = 30 Hz')
    ax1.set_yticks(range(len(labels)))
    ax1.set_yticklabels(labels, fontsize=10)
    ax1.set_xlabel('F3 (Hz)')
    ax1.set_title('F3 Achievement (lower is better)')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.set_xlim([20, 60])

    # Plot 2: Mouth area vs cabinet limit
    mouth_areas = [d['mouth_area']*10000 for d in designs]
    max_mouth = max_mouth_area * 10000

    ax2.barh(range(len(labels)), mouth_areas, color='steelblue', alpha=0.7)
    ax2.axvline(max_mouth, color='r', linestyle='--', linewidth=2, label='Cabinet limit')
    ax2.set_yticks(range(len(labels)))
    ax2.set_yticklabels(labels, fontsize=10)
    ax2.set_xlabel('Mouth Area (cm²)')
    ax2.set_title('Mouth Area vs Cabinet Constraint')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='x')

    # Plot 3: Total length
    lengths = [d['total_length'] for d in designs]

    ax3.barh(range(len(labels)), lengths, color='coral', alpha=0.7)
    ax3.set_yticks(range(len(labels)))
    ax3.set_yticklabels(labels, fontsize=10)
    ax3.set_xlabel('Total Horn Length (m)')
    ax3.set_title('Horn Length (affects folding complexity)')
    ax3.grid(True, alpha=0.3, axis='x')

    # Plot 4: SPL efficiency
    spls = [d['reference_spl'] for d in designs]

    ax4.barh(range(len(labels)), spls, color='purple', alpha=0.7)
    ax4.set_yticks(range(len(labels)))
    ax4.set_yticklabels(labels, fontsize=10)
    ax4.set_xlabel('Reference SPL (dB @ 2.83V)')
    ax4.set_title('Efficiency Comparison')
    ax4.grid(True, alpha=0.3, axis='x')
    ax4.set_xlim([95, 105])

    plt.tight_layout()

    plot_file = "tasks/BC21DS115_folded_45x30x22p5_comparison.png"
    plt.savefig(plot_file, dpi=150)
    print(f"\nPlot saved to: {plot_file}")

    # Save detailed report
    output_file = "tasks/BC21DS115_folded_45x30x22p5_results.txt"
    with open(output_file, 'w') as f:
        f.write("BC_21DS115 Folded Horn Design - 45×30×22.5\" Cabinet\n")
        f.write("=" * 80 + "\n\n")

        f.write("Target: F3 ≤ 30 Hz\n")
        f.write(f"Cabinet: {cabinet_ext[0]:.1f} × {cabinet_ext[1]:.1f} × {cabinet_ext[2]:.1f} cm\n")
        f.write(f"         (45\" × 30\" × 22.5\")\n\n")

        f.write("Design Comparison:\n")
        f.write(f"{'Design':<20} {'F3':<8} {'SPL':<8} {'Length':<10} {'Mouth':<10} {'Fits?':<8}\n")
        f.write("-" * 88 + "\n")

        for d in designs:
            fits_str = "✓" if d['mouth_fits'] else "✗"
            f.write(f"{d['label']:<20} {d['f3']:<8.1f} {d['reference_spl']:<8.1f} "
                   f"{d['total_length']:<10.1f} {d['mouth_area']*10000:<10.0f} "
                   f"{fits_str:<8}\n")

        if viable_designs:
            best = min(viable_designs, key=lambda d: d['f3'])
            f.write(f"\n\nBest design meeting F3 ≤ 30 Hz: {best['label']}\n")
            f.write(f"  F3: {best['f3']:.1f} Hz\n")
            f.write(f"  SPL: {best['reference_spl']:.1f} dB\n")
            f.write(f"  Length: {best['total_length']:.2f} m\n")
            f.write(f"  Mouth: {best['mouth_area']*10000:.0f} cm²\n")
            f.write(f"  Rear chamber: 594 L (3.0×Vas)\n")
        else:
            f.write(f"\n\nNo design meets F3 ≤ 30 Hz target\n")
            f.write(f"Closest: {min(designs, key=lambda d: d['f3'])['label']} at {min(designs, key=lambda d: d['f3'])['f3']:.1f} Hz\n")

    print(f"Results saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
