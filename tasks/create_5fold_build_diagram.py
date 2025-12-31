#!/usr/bin/env python3
"""
Create detailed construction diagrams for 5-fold diagonal horn design.

Shows:
- Cabinet dimensions
- 5 diagonal fold paths
- Cross-sections at each fold
- Detailed dimensions for cutting

Literature:
    - Practical horn construction drawings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon
from viberesp.driver import load_driver
from viberesp.simulation.types import HyperbolicHorn
import matplotlib.patches as mpatches


def create_5fold_diagram():
    """Create detailed build diagrams for 5-fold design."""

    print("=" * 80)
    print("BC_21DS115 5-Fold Horn - Construction Diagrams")
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

    const_height = 50.0  # cm

    # Calculate horn expansion
    seg1 = HyperbolicHorn(throat_area, middle_area, length1, T=T1)
    seg2 = HyperbolicHorn(middle_area, mouth_area, length2, T=T2)

    # 5 diagonal folds using width×depth diagonal
    num_folds = 5
    diagonal_WD = np.sqrt(internal_W**2 + internal_D**2)  # Width×Depth diagonal
    fold_length = total_length * 100 / num_folds  # 90 cm per fold

    print(f"\nDesign parameters:")
    print(f"  Cabinet: {cabinet_W:.1f} × {cabinet_H:.1f} × {cabinet_D:.1f} cm (external)")
    print(f"  Internal: {internal_W:.1f} × {internal_H:.1f} × {internal_D:.1f} cm")
    print(f"  Horn length: {total_length*100:.0f} cm")
    print(f"  Number of folds: {num_folds}")
    print(f"  Length per fold: {fold_length:.0f} cm")
    print(f"  Constant height: {const_height} cm")
    print(f"  Available diagonal (W×D): {diagonal_WD:.1f} cm")

    # Calculate cross-sections at each fold
    fold_data = []

    for i in range(num_folds + 1):
        x = i * fold_length / 100  # Convert to meters

        if x <= length1:
            area = seg1.area_at(min(x, length1 - 0.0001))
        else:
            area = seg2.area_at(min(x - length1, length2 - 0.0001))

        area_cm2 = area * 10000

        # With constant height
        width = area_cm2 / const_height
        height = const_height

        fold_data.append({
            'fold': i,
            'distance_cm': x * 100,
            'area_cm2': area_cm2,
            'width_cm': width,
            'height_cm': height,
        })

    print(f"\n{'Fold':<6} {'Dist':<8} {'Width':<10} {'Height':<10} {'Area':<10}")
    print("-" * 55)
    for fd in fold_data:
        print(f"{fd['fold']:<6} {fd['distance_cm']:>6.1f} cm {fd['width_cm']:>8.1f} cm "
              f"{fd['height_cm']:>8.1f} cm {fd['area_cm2']:>8.0f} cm²")

    # ===== FIGURE 1: Complete build diagram =====
    print("\nGenerating Figure 1: Complete build diagram...")

    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Plot 1: Cabinet top view with fold pattern
    ax1 = fig.add_subplot(gs[0, :])

    # Draw cabinet outline
    cabinet_rect = Rectangle((0, 0), cabinet_W, cabinet_H,
                              linewidth=4, edgecolor='black', facecolor='wheat', alpha=0.3)
    ax1.add_patch(cabinet_rect)

    # Draw internal area
    internal_rect = Rectangle((wall_thickness, wall_thickness),
                               internal_W, internal_H,
                               linewidth=2, edgecolor='gray', facecolor='white', alpha=0.5)
    ax1.add_patch(internal_rect)

    # Draw 5 diagonal fold pattern
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']

    for i in range(num_folds):
        fd_start = fold_data[i]
        fd_end = fold_data[i + 1]

        # Calculate diagonal path (front-left to back-right pattern)
        # We'll space them vertically

        y_pos_start = cabinet_H - 10 - i * (internal_H * 0.85 / num_folds)
        y_pos_end = y_pos_start - (internal_H * 0.85 / num_folds)

        # Draw diagonal line
        t = np.linspace(0, 1, 100)
        x_path = wall_thickness + t * internal_W
        y_path = y_pos_start + (y_pos_end - y_pos_start) * t**0.5  # Slight curve

        ax1.plot(x_path, y_path, color=colors[i], linewidth=4, alpha=0.8, zorder=5,
                label=f'Fold {i+1}')

        # Mark start and end points
        ax1.plot(x_path[0], y_path[0], 'o', color=colors[i], markersize=10, zorder=6)
        ax1.plot(x_path[-1], y_path[-1], 's', color=colors[i], markersize=10, zorder=6)

        # Label with dimensions
        mid_x = np.mean(x_path)
        mid_y = np.mean(y_path)

        label_text = f'{i+1}\n{fd_start["width_cm"]:.0f}→{fd_end["width_cm"]:.0f}cm'
        ax1.text(mid_x + 5, mid_y, label_text, fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=colors[i], alpha=0.8))

        # Draw cross-section rectangle at fold point
        rect_width = fd_start['width_cm']
        rect_height = fd_start['height_cm']

        # Place small cross-section view at fold start
        if i < 3:
            cs_x = cabinet_W + 20 + i * 50
            cs_rect = Rectangle((cs_x, cabinet_H - 30 - i*40), rect_width, rect_height,
                                 linewidth=2, edgecolor=colors[i], facecolor=colors[i], alpha=0.5)
            ax1.add_patch(cs_rect)
            ax1.text(cs_x + rect_width/2, cabinet_H - 30 - i*40 - 5,
                    f'Fold {i}\n{rect_width:.0f}×{rect_height:.0f}',
                    ha='center', va='top', fontsize=8)

    # Driver location
    driver_rect = Rectangle((cabinet_W/2 - 10, cabinet_H - 25), 20, 20,
                             linewidth=3, edgecolor='red', facecolor='red', alpha=0.7, zorder=10)
    ax1.add_patch(driver_rect)
    ax1.text(cabinet_W/2, cabinet_H - 15, '21"\nDRIVER',
            ha='center', va='center', fontsize=10, fontweight='bold', color='white', zorder=11)

    # Mouth
    mouth_width = fold_data[-1]['width_cm']
    mouth_height = const_height

    mouth_rect = Rectangle((cabinet_W/2 - mouth_width/2, wall_thickness + 5),
                           mouth_width, mouth_height,
                           linewidth=3, edgecolor='green', facecolor='lightgreen', alpha=0.7, zorder=8)
    ax1.add_patch(mouth_rect)
    ax1.text(cabinet_W/2, wall_thickness + mouth_height/2 + 5,
            f'MOUTH\n{mouth_width:.0f}×{mouth_height:.0f}',
            ha='center', va='center', fontsize=10, fontweight='bold', color='darkgreen', zorder=9)

    # Rear chamber
    rc_rect = Rectangle((wall_thickness + 5, cabinet_H - internal_H * 0.4),
                        internal_W * 0.4, internal_H * 0.35,
                        linewidth=2, edgecolor='purple', facecolor='lavender',
                        hatch='//', alpha=0.6, zorder=4)
    ax1.add_patch(rc_rect)
    ax1.text(wall_thickness + internal_W * 0.2, cabinet_H - internal_H * 0.2,
            'REAR\nCHAMBER\n594L',
            ha='center', va='center', fontsize=9, color='purple',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=5)

    # Dimension arrows
    ax1.annotate('', xy=(0, -10), xytext=(cabinet_W, -10),
                arrowprops=dict(arrowstyle='<->', lw=3))
    ax1.text(cabinet_W/2, -15, f'{cabinet_W:.1f} cm (45\")', ha='center', fontsize=12, fontweight='bold')

    ax1.annotate('', xy=(-10, 0), xytext=(-10, cabinet_H),
                arrowprops=dict(arrowstyle='<->', lw=3))
    ax1.text(-15, cabinet_H/2, f'{cabinet_H:.1f} cm\n(30\")', ha='center', va='center', fontsize=12, fontweight='bold')

    ax1.set_xlim(-30, cabinet_W + 180)
    ax1.set_ylim(-30, cabinet_H + 20)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Width (cm)', fontsize=12)
    ax1.set_ylabel('Height (cm)', fontsize=12)
    ax1.set_title('Top View - 5-Fold Diagonal Pattern\nConstant Height = 50 cm, Width Varies',
                 fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle=':')

    # Plot 2: Side view (showing depth)
    ax2 = fig.add_subplot(gs[1, 0])

    # Cabinet side view
    ax2.set_xlim(-10, cabinet_W + 10)
    ax2.set_ylim(-10, cabinet_D + 20)
    ax2.set_aspect('equal')

    cabinet_side = Rectangle((0, 0), cabinet_W, cabinet_D,
                             linewidth=3, edgecolor='black', facecolor='wheat', alpha=0.3)
    ax2.add_patch(cabinet_side)

    internal_side = Rectangle((wall_thickness, wall_thickness),
                               internal_W, internal_D,
                               linewidth=2, edgecolor='gray', facecolor='white', alpha=0.5)
    ax2.add_patch(internal_side)

    # Show how horn uses depth dimension
    for i in range(num_folds):
        x_center = wall_thickness + 10 + i * (internal_W - 20) / num_folds

        # Draw fold segment
        if i % 2 == 0:
            # Front to back
            y_start = wall_thickness + 2
            y_end = internal_D - wall_thickness - 2
            arrow_style = '→'
        else:
            # Back to front
            y_start = internal_D - wall_thickness - 2
            y_end = wall_thickness + 2
            arrow_style = '←'

        ax2.plot([x_center, x_center], [y_start, y_end],
                color=colors[i], linewidth=5, alpha=0.8, zorder=5)

        # End markers
        ax2.plot(x_center, y_start, 'o', color=colors[i], markersize=8, zorder=6)
        ax2.plot(x_center, y_end, 's', color=colors[i], markersize=8, zorder=6)

        # Label
        ax2.text(x_center, (y_start + y_end)/2, f'{i+1}\n{arrow_style}',
               ha='center', va='center', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='circle,pad=0.5', facecolor=colors[i], alpha=0.9))

        # Show length dimension
        if i % 2 == 0:
            ax2.text(x_center, y_end + 3, f'{fold_length:.0f}', ha='center', fontsize=8, color=colors[i])

    # Depth dimension
    ax2.annotate('', xy=(cabinet_W + 5, 0), xytext=(cabinet_W + 5, cabinet_D),
                arrowprops=dict(arrowstyle='<->', lw=2))
    ax2.text(cabinet_W + 10, cabinet_D/2, f'{cabinet_D:.1f} cm\n(22.5\")',
           ha='left', va='center', fontsize=10, fontweight='bold')

    ax2.set_xlabel('Width (cm)', fontsize=10)
    ax2.set_ylabel('Depth (cm)', fontsize=10)
    ax2.set_title('Side View - Folds Go Front↔Back', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle=':')

    # Plot 3: 3D isometric view
    ax3 = fig.add_subplot(gs[1, 1], projection='3d')

    # Draw cabinet wireframe
    W, H, D = cabinet_W, cabinet_H, cabinet_D

    # Bottom
    ax3.plot([0, W, W, 0, 0], [0, 0, H, H, 0], [0, 0, 0, 0, 0], 'k-', linewidth=2)
    # Top
    ax3.plot([0, W, W, 0, 0], [0, 0, H, H, 0], [D, D, D, D, D], 'k-', linewidth=2, alpha=0.5)
    # Vertical edges
    ax3.plot([0, 0], [0, 0], [0, D], 'k-', linewidth=2, alpha=0.5)
    ax3.plot([W, W], [0, 0], [0, D], 'k-', linewidth=2, alpha=0.5)
    ax3.plot([W, W], [H, H], [0, D], 'k-', linewidth=2, alpha=0.5)
    ax3.plot([0, 0], [H, H], [0, D], 'k-', linewidth=2, alpha=0.5)

    # Draw horn path (simplified)
    path_x, path_y, path_z = [], [], []

    for i in range(num_folds + 1):
        progress = i / num_folds

        x = W/2 + (W/4) * np.sin(progress * np.pi * 2)
        y = H - 10 - progress * (H - 20)
        z = D/2 + (D/3) * np.cos(progress * np.pi)

        path_x.append(x)
        path_y.append(y)
        path_z.append(z)

    ax3.plot(path_x, path_y, path_z, 'r-', linewidth=4, marker='o', markersize=8, label='Horn path')

    # Mark driver and mouth
    ax3.scatter([path_x[0]], [path_y[0]], [path_z[0]], color='red', s=300, marker='*', label='Driver', zorder=10)
    ax3.scatter([path_x[-1]], [path_y[-1]], [path_z[-1]], color='green', s=300, marker='s', label='Mouth', zorder=10)

    ax3.set_xlabel('Width (cm)', fontsize=9)
    ax3.set_ylabel('Height (cm)', fontsize=9)
    ax3.set_zlabel('Depth (cm)', fontsize=9)
    ax3.set_title(f'3D View\n5 Diagonal Folds', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.view_init(elev=20, azim=45)

    # Plot 4: Cross-sections at each fold
    ax4 = fig.add_subplot(gs[1, 2])

    ax4.set_xlim(-10, 100)
    ax4.set_ylim(-10, 70)
    ax4.set_aspect('equal')
    ax4.grid(True, alpha=0.3)

    for i in range(min(num_folds + 1, 6)):
        fd = fold_data[i]

        # Calculate position in subplot
        row = i // 2
        col = i % 2

        x_pos = col * 50
        y_pos = 50 - row * 25

        # Draw rectangle
        rect = Rectangle((x_pos - fd['width_cm']/2, y_pos - fd['height_cm']/2),
                         fd['width_cm'], fd['height_cm'],
                         linewidth=2, edgecolor=colors[i % len(colors)],
                         facecolor=colors[i % len(colors)], alpha=0.6)
        ax4.add_patch(rect)

        # Label
        ax4.text(x_pos, y_pos, f'Fold {i}\n{fd["width_cm"]:.0f}×{fd["height_cm"]:.0f}cm\n{fd["area_cm2"]:.0f}cm²',
               ha='center', va='center', fontsize=8)

    ax4.set_xlim(-10, 100)
    ax4.set_ylim(-10, 60)
    ax4.set_xticks([])
    ax4.set_yticks([])
    ax4.set_title('Cross-Sections at Each Fold', fontsize=11, fontweight='bold')

    # Plot 5: Cutting list
    ax5 = fig.add_subplot(gs[2, :])
    ax5.axis('off')

    cutting_text = """
CUTTING LIST FOR 5-FOLD DESIGN (Constant Height = 50 cm)
═══════════════════════════════════════════════════════════════════════════════════════════════

MATERIAL REQUIRED:
  • 18-19mm (¾") Baltic birch plywood
  • Total internal volume: ~594 L (rear chamber + horn)

PANELS TO CUT (per segment):
────────────────────────────────────────────────────────────────────────────────────────────────

  Side panels (50 cm HEIGHT - same for ALL folds!):
    Quantity: 10 panels (2 per fold × 5 folds)
    Dimensions: 50 × 90 cm each
    ✓ Can mass-produce - cut all 10 at once!

  Top/bottom panels (WIDTH varies per fold):
    Fold 0→1: 2 panels @ 18.5 × 90 cm
    Fold 1→2: 2 panels @ 22.6 × 90 cm
    Fold 2→3: 2 panels @ 27.8 × 90 cm
    Fold 3→4: 2 panels @ 34.6 × 90 cm
    Fold 4→5: 2 panels @ 42.2 × 90 cm
    Mouth:  2 panels @ 81.9 × 90 cm (final segment)

TOTAL PIECES: 10 side panels + 12 top/bottom panels = 22 panels (plus cabinet walls)

ASSEMBLY INSTRUCTIONS:
────────────────────────────────────────────────────────────────────────────────────────────────

  1. Build cabinet shell (45" × 30" × 22.5")
  2. Install rear chamber (594 L sealed box at top)
  3. Mount driver on dividing baffle
  4. Build horn segments in this order:
     a) Cut all side panels to 50 × 90 cm (10 pieces)
     b) Cut top/bottom panels to widths above (12 pieces)
     c) Assemble Fold 1 at throat (below driver)
     d) Continue with Folds 2-5
     e) Final mouth exits at bottom of cabinet

  5. Seal all joints airtight
  6. Line rear chamber with damping (optional)
  7. Test for air leaks

CRITICAL DIMENSIONS:
────────────────────────────────────────────────────────────────────────────────────────────────

  Throat: 16.8 × 50 cm (below 21" driver)
  Mouth:  88.6 × 50 cm (exits cabinet)
  Total horn path: 450 cm (5 folds × 90 cm)
  Compression ratio: 2:1 (driver to throat)
  Rear chamber: 594 L (3.0 × Vas)

  Expected F3: ~30 Hz ✓
    """

    ax5.text(0.05, 0.95, cutting_text, transform=ax5.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.suptitle('BC_21DS115 5-Fold Diagonal Horn - Complete Build Plans\n' +
                 'Cabinet: 45" × 30" × 22.5"  |  F3: ~30 Hz  |  Constant Height: 50 cm',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.savefig('tasks/5fold_build_diagram.png', dpi=150, bbox_inches='tight')
    print("  Saved: tasks/5fold_build_diagram.png")

    # ===== FIGURE 2: Detailed fold dimensions =====
    print("\nGenerating Figure 2: Detailed fold dimensions...")

    fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Horn expansion profile
    ax1.plot([fd['distance_cm'] for fd in fold_data],
             [fd['width_cm'] for fd in fold_data],
             'o-', linewidth=3, markersize=10, color='blue')
    ax1.fill_between([fd['distance_cm'] for fd in fold_data],
                      [fd['width_cm'] for fd in fold_data],
                      alpha=0.3, color='blue')
    ax1.set_xlabel('Distance from Throat (cm)', fontsize=11)
    ax1.set_ylabel('Horn Width (cm)', fontsize=11)
    ax1.set_title('Horn Expansion (Height = 50 cm constant)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Label each fold point
    for i, fd in enumerate(fold_data):
        ax1.annotate(f'Fold {i}\n{fd["width_cm"]:.0f}cm',
                    xy=(fd['distance_cm'], fd['width_cm']),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', lw=1))

    # Plot 2: Cross-sectional area expansion
    ax2.semilogy([fd['distance_cm'] for fd in fold_data],
                 [fd['area_cm2'] for fd in fold_data],
                 's-', linewidth=3, markersize=10, color='green')
    ax2.set_xlabel('Distance from Throat (cm)', fontsize=11)
    ax2.set_ylabel('Cross-Section Area (cm²)', fontsize=11)
    ax2.set_title('Area Expansion (Log Scale)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, which='both')

    for i, fd in enumerate(fold_data):
        ax2.annotate(f'Fold {i}\n{fd["area_cm2"]:.0f}cm²',
                    xy=(fd['distance_cm'], fd['area_cm2']),
                    xytext=(10, -20), textcoords='offset points',
                    fontsize=8, bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', lw=1))

    # Plot 3: Aspect ratio
    ax3.plot([fd['distance_cm'] for fd in fold_data],
             [fd['width_cm']/fd['height_cm'] for fd in fold_data],
             '^-', linewidth=3, markersize=10, color='red')
    ax3.axhline(3.0, color='orange', linestyle='--', linewidth=2, label='Max recommended (3:1)')
    ax3.set_xlabel('Distance from Throat (cm)', fontsize=11)
    ax3.set_ylabel('Aspect Ratio (Width:Height)', fontsize=11)
    ax3.set_title('Aspect Ratio Progression', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)

    for i, fd in enumerate(fold_data):
        ar = fd['width_cm']/fd['height_cm']
        ax3.annotate(f'{ar:.2f}:1',
                    xy=(fd['distance_cm'], ar),
                    xytext=(0, 10), textcoords='offset points',
                    fontsize=8, ha='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7))

    # Plot 4: Panel dimensions for each fold
    ax4.axis('off')

    panel_text = "PANEL DIMENSIONS FOR EACH FOLD\n"
    panel_text += "═" * 80 + "\n\n"

    for i in range(num_folds):
        fd_start = fold_data[i]
        fd_end = fold_data[i + 1]

        avg_width = (fd_start['width_cm'] + fd_end['width_cm']) / 2

        panel_text += f"FOLD {i+1} → {i+2}:\n"
        panel_text += f"  ├─ Side panels (2): 50 × 90 cm\n"
        panel_text += f"  ├─ Top panel: {avg_width:.1f} × 90 cm\n"
        panel_text += f"  └─ Bottom panel: {avg_width:.1f} × 90 cm\n"
        panel_text += f"     Start area: {fd_start['area_cm2']:.0f} cm² ({fd_start['width_cm']:.1f} × 50 cm)\n"
        panel_text += f"     End area: {fd_end['area_cm2']:.0f} cm² ({fd_end['width_cm']:.1f} × 50 cm)\n\n"

    # Mouth segment
    fd_last = fold_data[-1]
    panel_text += f"MOUTH EXIT:\n"
    panel_text += f"  ├─ Side panels (2): 50 × 90 cm\n"
    panel_text += f"  ├─ Top panel: {fd_last['width_cm']:.1f} × 90 cm\n"
    panel_text += f"  └─ Bottom panel: {fd_last['width_cm']:.1f} × 90 cm\n"
    panel_text += f"     Final area: {fd_last['area_cm2']:.0f} cm² ({fd_last['width_cm']:.1f} × 50 cm)\n\n"

    panel_text += f"TOTAL PANELS NEEDED:\n"
    panel_text += f"  • Side panels (50×90): 10 panels\n"
    panel_text += f"  • Top/bottom panels (various × 90): 12 panels\n"
    panel_text += f"  • TOTAL: 22 horn panels (plus cabinet walls)"

    ax4.text(0.05, 0.95, panel_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

    plt.suptitle('5-Fold Horn - Detailed Dimensions', fontsize=14, fontweight='bold')
    plt.tight_layout()

    plt.savefig('tasks/5fold_detailed_dimensions.png', dpi=150, bbox_inches='tight')
    print("  Saved: tasks/5fold_detailed_dimensions.png")

    print("\n" + "=" * 80)
    print("Diagrams complete!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  1. tasks/5fold_build_diagram.png - Complete build plans")
    print("  2. tasks/5fold_detailed_dimensions.png - Detailed dimensions")


if __name__ == "__main__":
    create_5fold_diagram()
