#!/usr/bin/env python3
"""
Minimize number of folds for simpler construction.

Instead of 9 small folds, explore using fewer, longer folds using:
- Diagonal folds (front-top to back-bottom)
- Full-depth straight segments
- Zigzag patterns

Literature:
    - Folded horn construction techniques
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from viberesp.driver import load_driver
from viberesp.simulation.types import HyperbolicHorn


def analyze_fold_minimization():
    """Analyze different folding strategies to minimize fold count."""

    print("=" * 80)
    print("BC_21DS115 Folded Horn - Minimizing Number of Folds")
    print("Simpler construction = fewer folds")
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

    # Horn parameters
    throat_area = 0.5 * driver.S_d  # 840 cm²
    middle_area = 0.20  # 2000 cm²
    mouth_area = 0.4716  # 4716 cm²
    length1 = 2.0  # m
    length2 = 2.5  # m
    total_length = 4.5  # m (450 cm)
    T1 = 0.7
    T2 = 1.0

    const_height = 50.0  # cm (use constant height strategy)

    print(f"\nCabinet internal: {internal_W:.1f} W × {internal_H:.1f} H × {internal_D:.1f} D cm")
    print(f"Horn total length: {total_length*100:.0f} cm")
    print(f"Constant height: {const_height} cm")

    print("\n" + "=" * 80)
    print("FOLDING STRATEGIES")
    print("=" * 80)

    strategies = []

    # Strategy 1: Original - 9 short folds (back-and-forth)
    print("\n[1] Original: 9 short folds")
    num_folds_1 = 9
    fold_length_1 = internal_D * 0.9  # ~48 cm per fold
    total_path_1 = num_folds_1 * fold_length_1
    efficiency_1 = (total_length * 100) / total_path_1

    print(f"  Folds: {num_folds_1}")
    print(f"  Length per fold: {fold_length_1:.1f} cm")
    print(f"  Total path: {total_path_1:.0f} cm")
    print(f"  Efficiency: {efficiency_1*100:.1f}%")
    print(f"  Complexity: MANY small segments")

    strategies.append({
        'name': '9 short folds (original)',
        'num_folds': num_folds_1,
        'fold_length_cm': fold_length_1,
        'total_path_cm': total_path_1,
        'efficiency': efficiency_1,
        'complexity': 'High',
        'segments': num_folds_1,
    })

    # Strategy 2: 6 diagonal folds (use diagonal of depth × width)
    print("\n[2] 6 diagonal folds (front-top to back-bottom)")

    # Diagonal length using depth and height
    diagonal_DH = np.sqrt(internal_D**2 + internal_H**2)  # Depth × Height diagonal
    num_folds_2 = 6
    fold_length_2 = min(diagonal_DH * 0.9, total_length * 100 / num_folds_2)
    total_path_2 = num_folds_2 * fold_length_2
    efficiency_2 = (total_length * 100) / total_path_2

    print(f"  Available diagonal (D×H): {diagonal_DH:.1f} cm")
    print(f"  Folds: {num_folds_2}")
    print(f"  Length per fold: {fold_length_2:.1f} cm")
    print(f"  Total path: {total_path_2:.0f} cm")
    print(f"  Efficiency: {efficiency_2*100:.1f}%")
    print(f"  Complexity: Medium (diagonal cuts)")

    strategies.append({
        'name': '6 diagonal folds',
        'num_folds': num_folds_2,
        'fold_length_cm': fold_length_2,
        'total_path_cm': total_path_2,
        'efficiency': efficiency_2,
        'complexity': 'Medium',
        'type': 'diagonal_DH',
        'segments': num_folds_2,
    })

    # Strategy 3: 5 long folds (use diagonal D×W)
    print("\n[3] 5 long diagonal folds (depth × width)")

    diagonal_DW = np.sqrt(internal_D**2 + internal_W**2)  # Depth × Width diagonal
    num_folds_3 = 5
    fold_length_3 = min(diagonal_DW * 0.9, total_length * 100 / num_folds_3)
    total_path_3 = num_folds_3 * fold_length_3
    efficiency_3 = (total_length * 100) / total_path_3

    print(f"  Available diagonal (D×W): {diagonal_DW:.1f} cm")
    print(f"  Folds: {num_folds_3}")
    print(f"  Length per fold: {fold_length_3:.1f} cm")
    print(f"  Total path: {total_path_3:.0f} cm")
    print(f"  Efficiency: {efficiency_3*100:.1f}%")
    print(f"  Complexity: Low (fewer, longer segments)")

    strategies.append({
        'name': '5 diagonal folds (D×W)',
        'num_folds': num_folds_3,
        'fold_length_cm': fold_length_3,
        'total_path_cm': total_path_3,
        'efficiency': efficiency_3,
        'complexity': 'Low',
        'type': 'diagonal_DW',
        'segments': num_folds_3,
    })

    # Strategy 4: 4 super-long diagonal folds
    print("\n[4] 4 super-long folds (maximum diagonal)")

    # Maximum diagonal in cabinet
    max_diagonal = np.sqrt(internal_W**2 + internal_H**2 + internal_D**2)
    num_folds_4 = 4
    fold_length_4 = min(max_diagonal * 0.95, total_length * 100 / num_folds_4)
    total_path_4 = num_folds_4 * fold_length_4
    efficiency_4 = (total_length * 100) / total_path_4

    print(f"  Max 3D diagonal: {max_diagonal:.1f} cm")
    print(f"  Folds: {num_folds_4}")
    print(f"  Length per fold: {fold_length_4:.1f} cm")
    print(f"  Total path: {total_path_4:.0f} cm")
    print(f"  Efficiency: {efficiency_4*100:.1f}%")
    print(f"  Complexity: Very low (fewest segments)")

    strategies.append({
        'name': '4 super-long folds',
        'num_folds': num_folds_4,
        'fold_length_cm': fold_length_4,
        'total_path_cm': total_path_4,
        'efficiency': efficiency_4,
        'complexity': 'Very Low',
        'type': '3D_diagonal',
        'segments': num_folds_4,
    })

    # Strategy 5: Hybrid - some straight, some diagonal
    print("\n[5] Hybrid: 3 straight + 2 diagonal")

    # Use 3 straight depth folds + 2 diagonal
    straight_length = internal_D * 0.9
    diagonal_length = np.sqrt(internal_D**2 + internal_H**2) * 0.9

    num_straight = 3
    num_diagonal = 2
    num_folds_5 = num_straight + num_diagonal

    total_path_5 = num_straight * straight_length + num_diagonal * diagonal_length
    efficiency_5 = (total_length * 100) / total_path_5

    print(f"  Straight folds: {num_straight} × {straight_length:.1f} cm")
    print(f"  Diagonal folds: {num_diagonal} × {diagonal_length:.1f} cm")
    print(f"  Total folds: {num_folds_5}")
    print(f"  Total path: {total_path_5:.0f} cm")
    print(f"  Efficiency: {efficiency_5*100:.1f}%")
    print(f"  Complexity: Low-Medium")

    strategies.append({
        'name': 'Hybrid (3 straight + 2 diagonal)',
        'num_folds': num_folds_5,
        'fold_length_cm': total_path_5 / num_folds_5,
        'total_path_cm': total_path_5,
        'efficiency': efficiency_5,
        'complexity': 'Low-Medium',
        'type': 'hybrid',
        'segments': num_folds_5,
    })

    # Comparison
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)

    print(f"\n{'Strategy':<35} {'Folds':<8} {'Path':<10} {'Eff.':<8} {'Build Ease':<12}")
    print("-" * 90)

    for s in strategies:
        ease_score = {
            'High': '😰 Hard',
            'Medium': '😐 OK',
            'Low': '😊 Easy',
            'Very Low': '🎉 Easiest',
            'Low-Medium': '🙂 OK-ish',
        }[s['complexity']]

        print(f"{s['name']:<35} {s['num_folds']:<8} {s['total_path_cm']:<10.0f} "
              f"{s['efficiency']*100:<8.1f}% {ease_score:<12}")

    # Select best strategies
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    # Filter for strategies that achieve required length
    valid_strategies = [s for s in strategies if s['total_path_cm'] >= total_length * 100]

    if valid_strategies:
        print(f"\n✓ {len(valid_strategies)} strategies achieve required length")

        # Recommend the one with fewest folds
        best = min(valid_strategies, key=lambda s: s['num_folds'])

        print(f"\n🏆 WINNER: {best['name']}")
        print(f"   Folds: {best['num_folds']} (minimum!)")
        print(f"   Path length: {best['total_path_cm']:.0f} cm")
        print(f"   Efficiency: {best['efficiency']*100:.1f}%")
        print(f"   Build complexity: {best['complexity']}")

        # Generate visualization for best strategy
        print("\nGenerating fold pattern visualization...")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot 1: Side-by-side comparison
        ax1 = axes[0, 0]

        y_pos = 0
        for i, s in enumerate(strategies):
            complexity_map = {'High': 4, 'Medium': 3, 'Low': 2, 'Very Low': 1, 'Low-Medium': 2}
            complexity_val = complexity_map[s['complexity']]
            color_map = {4: 'red', 3: 'orange', 2: 'yellow', 1: 'green'}
            color = color_map.get(complexity_val, 'lightgreen')

            ax1.barh(y_pos, s['num_folds'], color=color, alpha=0.7, edgecolor='black')
            ax1.text(s['num_folds'] + 0.2, y_pos, f"{s['num_folds']} folds",
                    ha='left', va='center', fontsize=9, fontweight='bold')
            ax1.text(0.5, y_pos, s['name'],
                    ha='left', va='center', fontsize=8)

            y_pos += 1

        ax1.set_xlabel('Number of Folds (lower is better)', fontsize=10)
        ax1.set_title('Fold Count Comparison', fontsize=12, fontweight='bold')
        ax1.set_xlim(-1, 10)
        ax1.set_ylim(-0.5, len(strategies) - 0.5)
        ax1.set_yticks([])
        ax1.grid(True, alpha=0.3, axis='x')

        # Plot 2: Efficiency comparison
        ax2 = axes[0, 1]

        y_pos = 0
        for s in strategies:
            efficiency_pct = s['efficiency'] * 100
            color = 'green' if efficiency_pct > 90 else 'orange' if efficiency_pct > 80 else 'red'

            ax2.barh(y_pos, efficiency_pct, color=color, alpha=0.7, edgecolor='black')
            ax2.text(efficiency_pct + 1, y_pos, f"{efficiency_pct:.1f}%",
                    ha='left', va='center', fontsize=9, fontweight='bold')
            ax2.text(2, y_pos, s['name'],
                    ha='left', va='center', fontsize=8)

            y_pos += 1

        ax2.set_xlabel('Efficiency % (higher is better)', fontsize=10)
        ax2.set_title('Space Utilization', fontsize=12, fontweight='bold')
        ax2.set_xlim(0, 110)
        ax2.set_ylim(-0.5, len(strategies) - 0.5)
        ax2.set_yticks([])
        ax2.grid(True, alpha=0.3, axis='x')
        ax2.axvline(100, color='r', linestyle='--', alpha=0.5, label='100% (perfect)')
        ax2.legend()

        # Plot 3: Visual comparison of fold patterns
        ax3 = axes[1, 0]

        # Show original 9-fold pattern
        ax3.set_xlim(0, 10)
        ax3.set_ylim(0, 10)
        ax3.set_aspect('equal')

        # Draw cabinet representation
        cabinet_rect = Rectangle((1, 1), 8, 8, linewidth=2, edgecolor='black', facecolor='none')
        ax3.add_patch(cabinet_rect)

        # Draw 9-fold pattern (schematic)
        for i in range(9):
            y_start = 8 - i * 0.8
            y_end = y_start - 0.7

            if i % 2 == 0:
                x_positions = [2, 7]
            else:
                x_positions = [7, 2]

            ax3.plot(x_positions, [y_start, y_end], 'b-', linewidth=2, alpha=0.6)
            ax3.text(5, y_start - 0.35, f'{i+1}', ha='center', fontsize=7,
                   bbox=dict(boxstyle='circle', facecolor='yellow', alpha=0.7))

        ax3.set_title('Original: 9 Folds\n(😰 Complex)', fontsize=10, fontweight='bold')
        ax3.axis('off')

        # Plot 4: Best strategy pattern
        ax4 = axes[1, 1]

        ax4.set_xlim(0, 10)
        ax4.set_ylim(0, 10)
        ax4.set_aspect('equal')

        cabinet_rect2 = Rectangle((1, 1), 8, 8, linewidth=2, edgecolor='black', facecolor='none')
        ax4.add_patch(cabinet_rect2)

        # Draw reduced fold pattern
        num_folds_best = best['num_folds']

        if best.get('type') in ['diagonal_DH', 'diagonal_DW', '3D_diagonal']:
            # Diagonal folds
            for i in range(num_folds_best):
                y_start = 8 - i * 1.5
                y_end = y_start - 1.3

                if i % 2 == 0:
                    # Diagonal down-right
                    ax4.plot([2, 7], [y_start, y_end], 'g-', linewidth=3, alpha=0.7)
                else:
                    # Diagonal down-left
                    ax4.plot([7, 2], [y_start, y_end], 'g-', linewidth=3, alpha=0.7)

                ax4.text(5, y_start - 0.65, f'{i+1}', ha='center', fontsize=8,
                       bbox=dict(boxstyle='circle', facecolor='lightgreen', alpha=0.9))

        else:
            # Regular folds
            for i in range(num_folds_best):
                y_start = 8 - i * 1.5
                y_end = y_start - 1.3

                if i % 2 == 0:
                    x_positions = [2, 7]
                else:
                    x_positions = [7, 2]

                ax4.plot(x_positions, [y_start, y_end], 'g-', linewidth=3, alpha=0.7)
                ax4.text(5, y_start - 0.65, f'{i+1}', ha='center', fontsize=8,
                       bbox=dict(boxstyle='circle', facecolor='lightgreen', alpha=0.9))

        ax4.set_title(f'{best["name"]}\n({best["num_folds"]} folds - 🎉 Much Easier!)',
                     fontsize=10, fontweight='bold')
        ax4.axis('off')

        plt.suptitle('Fold Minimization Strategies', fontsize=14, fontweight='bold')
        plt.tight_layout()

        plot_file = "tasks/fold_minimization_strategies.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved: {plot_file}")

        # Detailed construction implications
        print("\n" + "=" * 80)
        print("CONSTRUCTION IMPLICATIONS")
        print("=" * 80)

        print(f"\nORIGINAL (9 folds):")
        print(f"  • Cut 9 segments × 4 panels = 36 unique pieces")
        print(f"  • 18 joints to seal")
        print(f"  • High error potential")

        print(f"\nOPTIMIZED ({best['num_folds']} folds):")
        print(f"  • Cut {best['num_folds']} segments × 4 panels = ~{best['num_folds']*4} pieces")
        print(f"  • ~{best['num_folds']*2} joints to seal")
        print(f"  • {((9 - best['num_folds'])/9)*100:.0f}% fewer pieces!")

        print(f"\nTIME SAVINGS:")
        print(f"  • Measuring/cutting: {((9 - best['num_folds'])/9)*100:.0f}% less work")
        print(f"  • Assembly: {((9 - best['num_folds'])/9)*100:.0f}% faster")
        print(f"  • Fewer joints = fewer potential leaks")

        # Calculate required fold lengths for best strategy
        if best.get('type') == 'diagonal_DH':
            fold_len = np.sqrt(internal_D**2 + internal_H**2) * 0.9
            print(f"\nFOLD DETAILS ({best['name']}):")
            print(f"  • Each fold: {fold_len:.1f} cm (diagonal)")
            print(f"  • Pattern: Front-top ↔ Back-bottom")
            print(f"  • Requires diagonal cuts")

        elif best.get('type') == 'diagonal_DW':
            fold_len = np.sqrt(internal_D**2 + internal_W**2) * 0.9
            print(f"\nFOLD DETAILS ({best['name']}):")
            print(f"  • Each fold: {fold_len:.1f} cm (diagonal)")
            print(f"  • Pattern: Front-left ↔ Back-right")
            print(f"  • Requires diagonal cuts")

        elif best.get('type') == '3D_diagonal':
            fold_len = np.sqrt(internal_W**2 + internal_H**2 + internal_D**2) * 0.95
            print(f"\nFOLD DETAILS ({best['name']}):")
            print(f"  • Each fold: {fold_len:.1f} cm (3D diagonal)")
            print(f"  • Very complex cuts")
            print(f"  • ⚠️ May not be practical")

        else:
            print(f"\nFOLD DETAILS ({best['name']}):")
            print(f"  • Mixed straight and diagonal folds")
            print(f"  • Requires careful planning")

    else:
        print("\n⚠ No strategies achieve required length - need different approach")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    analyze_fold_minimization()
