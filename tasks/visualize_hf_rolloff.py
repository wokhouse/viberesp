#!/usr/bin/env python3
"""
Visualize voice coil inductance high-frequency rolloff effects.

This script plots sealed box SPL responses comparing:
1. No HF rolloff (f_mass=None)
2. Legacy method (dB post-correction)
3. Complex transfer function method

Literature:
- Leach (2002), "Introduction to Electroacoustics", Eq. 4.20
- Small (1972), "Direct-Radiator Loudspeaker System Analysis"
- Research: tasks/ported_box_transfer_function_research_brief.md
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import (
    calculate_spl_from_transfer_function,
    calculate_spl_array
)

# Driver parameters (BC 8NDL51)
driver = ThieleSmallParameters(
    M_md=0.0267,   # kg (driver mass only, ~26.7g)
    C_ms=0.0008,   # m/N (compliance)
    R_ms=1.53,     # kg/s (mechanical resistance)
    R_e=6.3,       # Ω (DC resistance)
    L_e=0.00035,   # H (0.35 mH inductance)
    BL=5.8,        # T·m (force factor)
    S_d=0.0217,    # m² (effective area)
)

# Enclosure parameters
Vb = 0.010  # 10L sealed box
f_mass = 450  # Hz (empirically determined for this driver)

# Calculate inductance corner frequency
f_Le = driver.R_e / (2 * np.pi * driver.L_e)

print(f"Driver: BC 8NDL51 (simulated)")
print(f"  F_s = {driver.F_s:.2f} Hz")
print(f"  Q_ts = {driver.Q_ts:.3f}")
print(f"  V_as = {driver.V_as*1000:.2f} L")
print(f"  R_e = {driver.R_e:.2f} Ω")
print(f"  L_e = {driver.L_e*1000:.2f} mH")
print(f"  f_Le = {f_Le:.1f} Hz (inductance corner)")
print(f"  f_mass = {f_mass} Hz (mass break)")
print(f"  Vb = {Vb*1000:.1f} L")
print()

# Frequency range for plotting
freqs = np.logspace(1, 4.5, 500)  # 10 Hz to ~31 kHz

print("Calculating SPL responses...")

# Method 1: No HF rolloff (baseline)
print("  1. No HF rolloff...")
spl_no_rolloff = calculate_spl_array(freqs, driver, Vb, f_mass=None)

# Method 2: Legacy method (dB post-correction)
print("  2. Legacy method (dB post-correction)...")
spl_legacy = calculate_spl_array(freqs, driver, Vb, f_mass=f_mass)

# Method 3: Complex transfer function method
print("  3. Complex TF method...")
# We need to calculate this one frequency at a time since the scalar function
# doesn't support arrays yet with the use_complex_tf parameter
spl_complex = np.array([
    calculate_spl_from_transfer_function(f, driver, Vb, f_mass=f_mass, use_complex_tf=True)
    for f in freqs
])

print("Plotting...")

# Create figure
fig, axes = plt.subplots(2, 1, figsize=(12, 10))
fig.suptitle(f'Voice Coil Inductance Effects: Sealed Box ({Vb*1000:.1f}L)\n'
             f'Driver: BC 8NDL51 (F_s={driver.F_s:.1f}Hz, f_Le={f_Le:.0f}Hz, f_mass={f_mass}Hz)',
             fontsize=14, fontweight='bold')

# Plot 1: Full frequency range
ax1 = axes[0]
ax1.semilogx(freqs, spl_no_rolloff, 'k--', linewidth=2, label='No HF rolloff', alpha=0.6)
ax1.semilogx(freqs, spl_legacy, 'b-', linewidth=2, label='Legacy method (dB correction)', alpha=0.8)
ax1.semilogx(freqs, spl_complex, 'r-', linewidth=1.5, label='Complex TF method', alpha=0.9)

# Add corner frequency markers
ax1.axvline(f_Le, color='orange', linestyle=':', linewidth=1.5, label=f'f_Le = {f_Le:.0f} Hz')
ax1.axvline(f_mass, color='purple', linestyle=':', linewidth=1.5, label=f'f_mass = {f_mass} Hz')

ax1.grid(True, alpha=0.3)
ax1.set_xlabel('Frequency (Hz)', fontsize=12)
ax1.set_ylabel('SPL (dB @ 1m, 2.83V)', fontsize=12)
ax1.set_title('Full Frequency Response (10 Hz - 30 kHz)', fontsize=12)
ax1.legend(loc='upper right', fontsize=10)
ax1.set_xlim([10, 30000])
ax1.set_ylim([40, 110])

# Plot 2: High-frequency zoom (focus on rolloff region)
ax2 = axes[1]
ax2.semilogx(freqs, spl_no_rolloff, 'k--', linewidth=2, label='No HF rolloff', alpha=0.6)
ax2.semilogx(freqs, spl_legacy, 'b-', linewidth=2, label='Legacy method (dB correction)', alpha=0.8)
ax2.semilogx(freqs, spl_complex, 'r-', linewidth=1.5, label='Complex TF method', alpha=0.9)

# Add corner frequency markers
ax2.axvline(f_Le, color='orange', linestyle=':', linewidth=1.5, label=f'f_Le = {f_Le:.0f} Hz')
ax2.axvline(f_mass, color='purple', linestyle=':', linewidth=1.5, label=f'f_mass = {f_mass} Hz')

ax2.grid(True, alpha=0.3)
ax2.set_xlabel('Frequency (Hz)', fontsize=12)
ax2.set_ylabel('SPL (dB @ 1m, 2.83V)', fontsize=12)
ax2.set_title('High-Frequency Rolloff Detail (500 Hz - 10 kHz)', fontsize=12)
ax2.legend(loc='upper right', fontsize=10)
ax2.set_xlim([500, 10000])
ax2.set_ylim([50, 105])

plt.tight_layout()

# Save figure
output_path = 'tasks/voice_coil_inductance_rolloff.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"\nPlot saved to: {output_path}")

# Print statistics
print("\n" + "=" * 70)
print("HIGH-FREQUENCY ROLLOFF STATISTICS")
print("=" * 70)

# Compare responses at key frequencies
test_freqs = [500, 1000, 2000, 5000, 10000]
print(f"\n{'Frequency':>12} | {'No Rolloff':>12} | {'Legacy':>12} | {'Complex TF':>12} | {'Legacy Δ':>10} | {'Complex Δ':>10}")
print("-" * 80)

for f in test_freqs:
    spl_none = calculate_spl_from_transfer_function(f, driver, Vb, f_mass=None)
    spl_legacy_f = calculate_spl_from_transfer_function(f, driver, Vb, f_mass=f_mass, use_complex_tf=False)
    spl_complex_f = calculate_spl_from_transfer_function(f, driver, Vb, f_mass=f_mass, use_complex_tf=True)
    delta_legacy = spl_legacy_f - spl_none
    delta_complex = spl_complex_f - spl_none
    print(f"{f:>12.0f} | {spl_none:>12.2f} | {spl_legacy_f:>12.2f} | {spl_complex_f:>12.2f} | {delta_legacy:>10.2f} | {delta_complex:>10.2f}")

print("\n" + "=" * 70)
print("LEGACY vs COMPLEX TF COMPARISON")
print("=" * 70)

# Calculate differences between legacy and complex methods
diff = spl_complex - spl_legacy
print(f"\nMaximum difference: {np.max(np.abs(diff)):.3f} dB")
print(f"Mean difference: {np.mean(np.abs(diff)):.3f} dB")
print(f"RMS difference: {np.sqrt(np.mean(diff**2)):.3f} dB")

# Find where differences are significant
significant_diff_mask = np.abs(diff) > 0.01
if np.any(significant_diff_mask):
    print(f"\nSignificant differences (>0.01 dB) at {np.sum(significant_diff_mask)} points")
    max_diff_idx = np.argmax(np.abs(diff))
    print(f"Maximum difference at {freqs[max_diff_idx]:.0f} Hz: {diff[max_diff_idx]:.3f} dB")
else:
    print("\nDifferences are negligible (< 0.01 dB) - methods are equivalent")

print("\n" + "=" * 70)
print("ROLLOFF RATE ANALYSIS")
print("=" * 70)

# Analyze rolloff rate above f_Le
mask_above_Le = freqs > f_Le
freq_above_Le = freqs[mask_above_Le]
spl_above_Le_legacy = spl_legacy[mask_above_Le]
spl_above_Le_complex = spl_complex[mask_above_Le]

# Calculate dB/octave rolloff (approximate)
# For first-order: ~6 dB/octave above corner
octaves = np.log2(freq_above_Le[-1] / freq_above_Le[0])
rolloff_legacy = (spl_above_Le_legacy[0] - spl_above_Le_legacy[-1]) / octaves
rolloff_complex = (spl_above_Le_complex[0] - spl_above_Le_complex[-1]) / octaves

print(f"\nRolloff rate ({freq_above_Le[0]:.0f} - {freq_above_Le[-1]:.0f} Hz, {octaves:.1f} octaves):")
print(f"  Legacy method: {rolloff_legacy:.2f} dB/octave")
print(f"  Complex TF method: {rolloff_complex:.2f} dB/octave")
print(f"\n  Expected (1st order + 1st order): ~12 dB/octave (combined)")
print(f"  Expected (inductance only): ~6 dB/octave")

plt.show()
