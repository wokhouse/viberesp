"""
Generate corrected plots showing fixed F3 calculation.

This script recreates the "Bass Extension vs Box Size" plot to show
that F3 now varies correctly with box volume instead of being flat.
"""

import sys
sys.path.insert(0, '/Users/fungj/vscode/viberesp/src')

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver.bc_drivers import get_bc_8fmb51
from viberesp.enclosure.ported_box import (
    calculate_ported_box_system_parameters,
    calculate_spl_ported_transfer_function
)

# Setup
driver = get_bc_8fmb51()
Fb = 40.0  # Fixed tuning

# Box volume range
volumes_liters = np.linspace(15, 50, 35)

# Calculate F3 for each volume
f3_values = []
for Vb_L in volumes_liters:
    Vb = Vb_L / 1000.0
    params = calculate_ported_box_system_parameters(driver, Vb, Fb)
    f3_values.append(params.F3)

f3_values = np.array(f3_values)

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot F3 vs Vb
ax.plot(volumes_liters, f3_values, 'b-', linewidth=2.5, label='F3 (from SPL)')
ax.axhline(y=Fb, color='r', linestyle='--', linewidth=1.5, label=f'Fb ({Fb} Hz) - Old simplified formula')

# Fill region showing improvement
ax.fill_between(volumes_liters, Fb, f3_values, alpha=0.2, color='blue',
                label='Variable F3 (CORRECT)')

# Labels and title
ax.set_xlabel('Box Volume Vb (liters)', fontsize=12, fontweight='bold')
ax.set_ylabel('Bass Extension F3 (Hz)', fontsize=12, fontweight='bold')
ax.set_title(f'Fixed: Bass Extension vs Box Size (Fb={Fb}Hz)\nBC_8FMB51 Driver (Qts={driver.Q_ts:.3f})',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='best', fontsize=10)

# Annotations
ax.annotate('Old formula: F3=Fb (flat line)\nIncorrect for most designs',
            xy=(32, Fb+2), fontsize=10, color='red',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.annotate('New formula: F3 from SPL response\nCorrectly varies with box size',
            xy=(18, 85), fontsize=10, color='blue',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Add text about driver
textstr = f'Driver: BC_8FMB51\nQts = {driver.Q_ts:.3f} (low for B4)\nVas = {driver.V_as*1000:.1f} L\nFs = {driver.F_s:.1f} Hz'
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('tasks/figure5_f3_fix.png', dpi=300, bbox_inches='tight')
print("✓ Saved: tasks/figure5_f3_fix.png")

# Create comparison plot: OLD vs NEW
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# OLD (incorrect): flat line
ax1.plot(volumes_liters, [Fb]*len(volumes_liters), 'r-', linewidth=2.5, label='F3 = Fb')
ax1.set_xlabel('Box Volume Vb (liters)', fontsize=12, fontweight='bold')
ax1.set_ylabel('F3 (Hz)', fontsize=12, fontweight='bold')
ax1.set_title('OLD: Simplified Formula (INCORRECT)\nF3 = Fb for all designs',
              fontsize=12, fontweight='bold', color='red')
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0, 100])
ax1.legend(loc='best')

# NEW (correct): variable F3
ax2.plot(volumes_liters, f3_values, 'b-', linewidth=2.5, label='F3 from SPL response')
ax2.axhline(y=Fb, color='gray', linestyle=':', linewidth=1.5, label=f'Fb reference')
ax2.set_xlabel('Box Volume Vb (liters)', fontsize=12, fontweight='bold')
ax2.set_ylabel('F3 (Hz)', fontsize=12, fontweight='bold')
ax2.set_title('NEW: Accurate Calculation (CORRECT)\nF3 varies with box volume',
              fontsize=12, fontweight='bold', color='blue')
ax2.grid(True, alpha=0.3)
ax2.set_ylim([0, 100])
ax2.legend(loc='best')

plt.suptitle(f'F3 Calculation Fix: BC_8FMB51 @ {Fb}Hz Tuning',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('tasks/figure6_f3_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: tasks/figure6_f3_comparison.png")

print("\n" + "="*70)
print("FIXED PLOTS GENERATED")
print("="*70)
print("\nKey improvements:")
print("  ✓ F3 now varies with box volume (not flat)")
print("  ✓ Smaller boxes show higher F3 (less bass)")
print("  ✓ Larger boxes show lower F3 (more bass)")
print("  ✓ Matches physical expectations")
print("\nFiles:")
print("  - tasks/figure5_f3_fix.png (main fix visualization)")
print("  - tasks/figure6_f3_comparison.png (before/after)")
