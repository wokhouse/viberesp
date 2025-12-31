#!/usr/bin/env python3
"""
Redesign folded horn with ONE CONSTANT DIMENSION for easier construction.

Instead of varying both width and height, fix one dimension (e.g., height = 50 cm)
and only vary the other dimension to achieve the required cross-sectional area.

This makes construction much simpler: all panels the same length on one side.

Literature:
    - Practical folded horn construction (Klipschorn approach)
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


def redesign_constant_dimension():
    """Redesign horn with one fixed dimension for easier construction."""

    print("=" * 80)
    print("BC_21DS115 Folded Horn - Constant Dimension Design")
    print("Making construction easier: Fix ONE dimension, vary the other")
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

    print(f"\nCabinet internal: {internal_W:.1f} × {internal_H:.1f} × {internal_D:.1f} cm")

    # Original design parameters
    throat_area = 0.5 * driver.S_d  # 840 cm²
    middle_area = 0.20  # 2000 cm²
    mouth_area = 0.4716  # 4716 cm²
    length1 = 2.0  # m
    length2 = 2.5  # m
    total_length = 4.5  # m
    T1 = 0.7
    T2 = 1.0

    # Test different constant dimension strategies
    print("\n" + "=" * 80)
    print("TESTING CONSTANT DIMENSION STRATEGIES")
    print("=" * 80)

    strategies = []

    # Strategy 1: Constant height = 50 cm
    print("\n[1] Constant height = 50 cm")
    const_dim_1 = 50.0  # cm

    fold_points_1 = []
    seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=T1)
    seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=T2)

    fold_length = internal_D * 0.9
    num_folds = 9

    valid_1 = True
    for i in range(num_folds + 1):
        x = i * fold_length / 100
        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        height = const_dim_1
        width = (area * 10000) / height

        # Check if fits in cabinet
        fits = (width <= internal_W and height <= internal_H)

        if not fits:
            valid_1 = False

        fold_points_1.append({
            'fold': i,
            'dist_cm': x * 100,
            'area_cm2': area * 10000,
            'height_cm': height,
            'width_cm': width,
            'fits': fits,
        })

    if valid_1:
        print(f"  ✓ Valid! Height fixed at {const_dim_1} cm, width varies")
        print(f"  Throat: {fold_points_1[0]['width_cm']:.1f} × {const_dim_1} cm")
        print(f"  Mouth:  {fold_points_1[-1]['width_cm']:.1f} × {const_dim_1} cm")
        strategies.append(('height', const_dim_1, fold_points_1, valid_1))
    else:
        print(f"  ✗ Won't fit - width exceeds cabinet dimensions")
        strategies.append(('height', const_dim_1, fold_points_1, valid_1))

    # Strategy 2: Constant height = 60 cm (more practical)
    print("\n[2] Constant height = 60 cm")
    const_dim_2 = 60.0  # cm

    fold_points_2 = []
    valid_2 = True

    for i in range(num_folds + 1):
        x = i * fold_length / 100
        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        height = const_dim_2
        width = (area * 10000) / height
        fits = (width <= internal_W and height <= internal_H)

        if not fits:
            valid_2 = False

        fold_points_2.append({
            'fold': i,
            'dist_cm': x * 100,
            'area_cm2': area * 10000,
            'height_cm': height,
            'width_cm': width,
            'fits': fits,
        })

    if valid_2:
        print(f"  ✓ Valid! Height fixed at {const_dim_2} cm")
        print(f"  Throat: {fold_points_2[0]['width_cm']:.1f} × {const_dim_2} cm")
        print(f"  Mouth:  {fold_points_2[-1]['width_cm']:.1f} × {const_dim_2} cm")
        strategies.append(('height', const_dim_2, fold_points_2, valid_2))
    else:
        print(f"  ✗ Won't fit")
        strategies.append(('height', const_dim_2, fold_points_2, valid_2))

    # Strategy 3: Constant width = 70 cm
    print("\n[3] Constant width = 70 cm")
    const_dim_3 = 70.0  # cm

    fold_points_3 = []
    valid_3 = True

    for i in range(num_folds + 1):
        x = i * fold_length / 100
        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        width = const_dim_3
        height = (area * 10000) / width
        fits = (width <= internal_W and height <= internal_H)

        if not fits:
            valid_3 = False

        fold_points_3.append({
            'fold': i,
            'dist_cm': x * 100,
            'area_cm2': area * 10000,
            'height_cm': height,
            'width_cm': width,
            'fits': fits,
        })

    if valid_3:
        print(f"  ✓ Valid! Width fixed at {const_dim_3} cm")
        print(f"  Throat: {const_dim_3} × {fold_points_3[0]['height_cm']:.1f} cm")
        print(f"  Mouth:  {const_dim_3} × {fold_points_3[-1]['height_cm']:.1f} cm")
        strategies.append(('width', const_dim_3, fold_points_3, valid_3))
    else:
        print(f"  ✗ Won't fit")
        strategies.append(('width', const_dim_3, fold_points_3, valid_3))

    # Strategy 4: Square cross-sections (original design)
    print("\n[4] Square cross-sections (original design)")
    fold_points_4 = []
    valid_4 = True

    for i in range(num_folds + 1):
        x = i * fold_length / 100
        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        side = np.sqrt(area * 10000)  # cm
        width = side
        height = side
        fits = (width <= internal_W and height <= internal_H)

        if not fits:
            valid_4 = False

        fold_points_4.append({
            'fold': i,
            'dist_cm': x * 100,
            'area_cm2': area * 10000,
            'height_cm': height,
            'width_cm': width,
            'fits': fits,
        })

    if valid_4:
        print(f"  ✓ Valid! Square cross-sections")
        print(f"  Throat: {fold_points_4[0]['width_cm']:.1f} × {fold_points_4[0]['height_cm']:.1f} cm")
        print(f"  Mouth:  {fold_points_4[-1]['width_cm']:.1f} × {fold_points_4[-1]['height_cm']:.1f} cm")
        strategies.append(('square', None, fold_points_4, valid_4))
    else:
        print(f"  ✗ Won't fit")
        strategies.append(('square', None, fold_points_4, valid_4))

    # Select best strategy
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)

    valid_strategies = [s for s in strategies if s[3]]

    if valid_strategies:
        print(f"\n✓ {len(valid_strategies)} valid strategies found")

        for s_type, const_dim, folds, valid in valid_strategies:
            if s_type == 'square':
                print(f"\n  Square cross-sections:")
                print(f"    Pros: Symmetrical, proven design")
                print(f"    Cons: Both dimensions vary (harder to build)")
            else:
                print(f"\n  Constant {s_type} = {const_dim} cm:")
                print(f"    Pros: Easy to build (cut all panels to {const_dim} cm)")
                print(f"    Other dimension varies: {folds[0][f'{s_type}_cm']:.1f} → {folds[-1][f'{s_type}_cm']:.1f} cm")

        # Choose the most practical (constant height = 60 cm if valid)
        best_strategy = None
        for s_type, const_dim, folds, valid in valid_strategies:
            if s_type == 'height' and const_dim >= 50 and const_dim <= 65:
                best_strategy = (s_type, const_dim, folds, valid)
                break

        if not best_strategy:
            best_strategy = valid_strategies[0]

        print("\n" + "=" * 80)
        print("RECOMMENDED DESIGN")
        print("=" * 80)

        s_type, const_dim, folds, valid = best_strategy

        if s_type == 'square':
            print("\nRecommended: Square cross-sections")
            print("────────────────────────────────")
            print("\nEach fold uses square cross-section:")
            print(f"{'Fold':<6} {'Width':<10} {'Height':<10} {'Area':<10}")
            print("-" * 45)
            for f in folds:
                print(f"{f['fold']:<6} {f['width_cm']:>8.1f} cm {f['height_cm']:>8.1f} cm {f['area_cm2']:>8.0f} cm²")

            print("\n✗ Both dimensions vary - harder to build")
            print("  Each panel needs to be cut to different width")

        else:
            print(f"\nRecommended: Constant {s_type} = {const_dim} cm")
            print("─" * 60)
            print("\n✓ EASY TO BUILD:")
            print(f"  • All {s_type} panels cut to {const_dim} cm")
            print(f"  • Only {'width' if s_type == 'height' else 'height'} varies")
            print(f"  • Rectangular cross-sections")

            print(f"\nDimensions at each fold:")
            print(f"{'Fold':<6} {'Width (cm)':<12} {'Height (cm)':<12} {'Area (cm²)':<12}")
            print("-" * 55)

            for f in folds:
                if s_type == 'height':
                    w, h = f['width_cm'], f['height_cm']
                else:
                    w, h = f['width_cm'], f['height_cm']

                print(f"{f['fold']:<6} {w:>10.1f}   {h:>10.1f}   {f['area_cm2']:>10.0f}")

            print("\n✓ All cross-sections fit in cabinet")
            print(f"  Cabinet internal: {internal_W:.0f} × {internal_H:.0f} cm")

            # Calculate aspect ratio
            throat_ar = max(folds[0]['width_cm'], folds[0]['height_cm']) / min(folds[0]['width_cm'], folds[0]['height_cm'])
            mouth_ar = max(folds[-1]['width_cm'], folds[-1]['height_cm']) / min(folds[-1]['width_cm'], folds[-1]['height_cm'])

            print(f"\nAspect ratios:")
            print(f"  Throat: {throat_ar:.2f}:1")
            print(f"  Mouth:  {mouth_ar:.2f}:1")

            if max(throat_ar, mouth_ar) < 3.0:
                print("  ✓ Good - no extreme aspect ratios")
            else:
                print("  ⚠ Warning - throat may be too narrow")

        # Build comparison plot
        print("\nGenerating comparison plots...")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot 1: All strategies comparison
        ax1 = axes[0, 0]

        for s_type, const_dim, folds, valid in strategies:
            if valid:
                if s_type == 'square':
                    widths = [f['width_cm'] for f in folds]
                    label = 'Square (both vary)'
                elif s_type == 'height':
                    widths = [f['width_cm'] for f in folds]
                    label = f'Const H={const_dim}cm'
                else:
                    widths = [f['width_cm'] for f in folds]
                    label = f'Const W={const_dim}cm'

                ax1.plot(range(len(folds)), widths, 'o-', label=label, linewidth=2, markersize=6)

        ax1.set_xlabel('Fold Number', fontsize=10)
        ax1.set_ylabel('Width (cm)', fontsize=10)
        ax1.set_title('Width Variation Across Folds', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(range(num_folds + 1))

        # Plot 2: Height comparison
        ax2 = axes[0, 1]

        for s_type, const_dim, folds, valid in strategies:
            if valid:
                if s_type == 'square':
                    heights = [f['height_cm'] for f in folds]
                    label = 'Square'
                elif s_type == 'height':
                    heights = [f['height_cm'] for f in folds]
                    label = f'Const H={const_dim}cm'
                else:
                    heights = [f['height_cm'] for f in folds]
                    label = f'Const W={const_dim}cm'

                ax2.plot(range(len(folds)), heights, 's-', label=label, linewidth=2, markersize=6)

        ax2.set_xlabel('Fold Number', fontsize=10)
        ax2.set_ylabel('Height (cm)', fontsize=10)
        ax2.set_title('Height Variation Across Folds', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(range(num_folds + 1))

        # Plot 3: Aspect ratio comparison
        ax3 = axes[1, 0]

        for s_type, const_dim, folds, valid in strategies:
            if valid:
                ars = [max(f['width_cm'], f['height_cm']) / min(f['width_cm'], f['height_cm']) for f in folds]

                if s_type == 'square':
                    label = 'Square'
                elif s_type == 'height':
                    label = f'Const H={const_dim}cm'
                else:
                    label = f'Const W={const_dim}cm'

                ax3.plot(range(len(folds)), ars, '^-', label=label, linewidth=2, markersize=6)

        ax3.axhline(3.0, color='r', linestyle='--', alpha=0.5, label='Max recommended (3:1)')
        ax3.set_xlabel('Fold Number', fontsize=10)
        ax3.set_ylabel('Aspect Ratio', fontsize=10)
        ax3.set_title('Aspect Ratio (Width:Height)', fontsize=12, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        ax3.set_xticks(range(num_folds + 1))

        # Plot 4: Best strategy cross-sections
        ax4 = axes[1, 1]

        if best_strategy[0] != 'square':
            s_type, const_dim, folds, valid = best_strategy

            for i in range(min(len(folds), 9)):
                f = folds[i]
                w, h = f['width_cm'], f['height_cm']

                # Draw rectangle centered
                rect = plt.Rectangle((-w/2, -h/2), w, h,
                                    linewidth=2, edgecolor='blue', facecolor='lightblue', alpha=0.6)
                ax4.add_patch(rect)

                ax4.text(0, 0, f'{i}\n{w:.0f}×{h:.0f}',
                        ha='center', va='center', fontsize=8, fontweight='bold')

                ax4.set_xlim(-80, 80)
                ax4.set_ylim(-80, 80)
                ax4.set_aspect('equal')
                ax4.grid(True, alpha=0.3)

            ax4.set_title(f'Cross-Sections: Const {s_type}={const_dim}cm', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Width (cm)', fontsize=10)
            ax4.set_ylabel('Height (cm)', fontsize=10)

        plt.suptitle('Constant Dimension Strategy Comparison', fontsize=14, fontweight='bold')
        plt.tight_layout()

        plot_file = "tasks/constant_dimension_strategies.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved: {plot_file}")

        # Build recommendations
        print("\n" + "=" * 80)
        print("BUILD RECOMMENDATIONS")
        print("=" * 80)

        if best_strategy[0] != 'square':
            s_type, const_dim, folds, valid = best_strategy

            print(f"\n✓ BUILD WITH CONSTANT {s_type.upper()} = {const_dim} cm")
            print("─" * 60)

            print(f"\nCutting list:")
            print(f"  • All {s_type} panels: {const_dim} cm length")
            print(f"  • {'Width' if s_type == 'height' else 'Height'} panels: varies per fold")

            print(f"\nPanel dimensions for each fold segment:")
            for i, f in enumerate(folds[:-1]):  # All but the last (mouth)
                next_f = folds[i + 1]

                if s_type == 'height':
                    panel1_dim = const_dim  # height (constant)
                    panel2_dim = (f['width_cm'] + next_f['width_cm']) / 2  # avg width

                    print(f"\n  Fold {i+1}→{i+2}:")
                    print(f"    Side panels (2): {panel1_dim:.1f} × {fold_length:.0f} cm")
                    print(f"    Top/bottom (2): {panel2_dim:.1f} × {fold_length:.0f} cm")
                else:
                    panel1_dim = const_dim  # width (constant)
                    panel2_dim = (f['height_cm'] + next_f['height_cm']) / 2  # avg height

                    print(f"\n  Fold {i+1}→{i+2}:")
                    print(f"    Side panels (2): {panel1_dim:.1f} × {fold_length:.0f} cm")
                    print(f"    Top/bottom (2): {panel2_dim:.1f} × {fold_length:.0f} cm")

            print(f"\n✓ SIMPLIFIED CONSTRUCTION:")
            print(f"  • Mass-produce {const_dim} cm panels")
            print(f"  • Cut {'width' if s_type == 'height' else 'height'} panels to length")
            print(f"  • Assemble like a ladder")
            print(f"  • Easier to get square and airtight")

    else:
        print("\n✗ No valid strategies found - need to adjust design")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    redesign_constant_dimension()
