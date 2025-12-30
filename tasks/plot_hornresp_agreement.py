#!/usr/bin/env python3
"""
Plot viberesp vs Hornresp comparison for voice coil inductance validation.

Visualizes:
1. Full frequency response comparison (10 Hz - 20 kHz)
2. High-frequency zoom (500 Hz - 20 kHz)
3. Error/difference plot
4. Corner frequency markers
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import calculate_spl_from_transfer_function

# =============================================================================
# DRIVER: BC 8NDL51 (same as Hornresp simulation)
# =============================================================================
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
f_mass = 450  # Hz (empirically determined)

# Calculate system parameters
Fc = driver.F_s * np.sqrt(1 + driver.V_as / Vb)
f_Le = driver.R_e / (2 * np.pi * driver.L_e)

print("=" * 80)
print("PLOTTING VIBERESP VS HORNRESP AGREEMENT")
print("=" * 80)
print(f"Driver: BC 8NDL51")
print(f"  f_Le = {f_Le:.1f} Hz (inductance corner)")
print(f"  Fc   = {Fc:.2f} Hz (system resonance)")
print()

# =============================================================================
# LOAD HORNRESP SIMULATION RESULTS
# =============================================================================
hornresp_file = "imports/hf_roll_sim.txt"

print("Loading Hornresp simulation results...")
freqs_hr = []
spl_hr = []

with open(hornresp_file, 'r') as f:
    lines = f.readlines()
    # Skip header (first 2 lines)
    for line in lines[2:]:
        if line.strip() and not line.startswith('Freq'):
            parts = line.split()
            if len(parts) >= 5:
                try:
                    freq = float(parts[0])
                    spl = float(parts[4])
                    freqs_hr.append(freq)
                    spl_hr.append(spl)
                except ValueError:
                    continue

freqs_hr = np.array(freqs_hr)
spl_hr = np.array(spl_hr)

print(f"  Loaded {len(freqs_hr)} frequency points")
print(f"  Range: {freqs_hr[0]:.1f} - {freqs_hr[-1]:.1f} Hz")
print()

# =============================================================================
# CALCULATE VIBERESP PREDICTIONS
# =============================================================================
print("Calculating viberesp predictions...")

spl_vib = np.array([
    calculate_spl_from_transfer_function(
        f, driver, Vb, f_mass=f_mass, Quc=float('inf')
    )
    for f in freqs_hr
])

print(f"  Calculated {len(spl_vib)} frequency points")
print()

# =============================================================================
# CALCULATE STATISTICS
# =============================================================================
diff_all = spl_vib - spl_hr
diff_hf = spl_vib[freqs_hr >= 2000] - spl_hr[freqs_hr >= 2000]
diff_bass = spl_vib[freqs_hr < 200] - spl_hr[freqs_hr < 200]

print("=" * 80)
print("STATISTICAL SUMMARY")
print("=" * 80)
print()
print(f"Full range (10 Hz - 20 kHz):")
print(f"  Mean error: {np.mean(np.abs(diff_all)):.3f} dB")
print(f"  RMS error:  {np.sqrt(np.mean(diff_all**2)):.3f} dB")
print()
print(f"Bass (<200 Hz):")
print(f"  Mean error: {np.mean(np.abs(diff_bass)):.3f} dB")
print(f"  RMS error:  {np.sqrt(np.mean(diff_bass**2)):.3f} dB")
print()
print(f"High-freq (≥2 kHz):")
print(f"  Mean error: {np.mean(np.abs(diff_hf)):.3f} dB")
print(f"  RMS error:  {np.sqrt(np.mean(diff_hf**2)):.3f} dB")
print()
print(f"At f_Le = {f_Le:.1f} Hz:")
idx_fLe = np.argmin(np.abs(freqs_hr - f_Le))
print(f"  Hornresp: {spl_hr[idx_fLe]:.2f} dB")
print(f"  Viberesp: {spl_vib[idx_fLe]:.2f} dB")
print(f"  Error:    {diff_all[idx_fLe]:.3f} dB")
print()

# =============================================================================
# PLOT
# =============================================================================
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

# Plot 1: Full frequency response (log scale)
ax1 = axes[0]
ax1.semilogx(freqs_hr, spl_hr, 'b-', linewidth=2, label='Hornresp', alpha=0.7)
ax1.semilogx(freqs_hr, spl_vib, 'r--', linewidth=2, label='Viberesp', alpha=0.7)
ax1.axvline(f_Le, color='orange', linestyle=':', linewidth=1.5, label=f'$f_{{Le}}$ = {f_Le:.0f} Hz')
ax1.axvline(Fc, color='green', linestyle=':', linewidth=1.5, label=f'$F_c$ = {Fc:.0f} Hz')
ax1.axvline(f_mass, color='purple', linestyle=':', linewidth=1.5, label=f'$f_{{mass}}$ = {f_mass} Hz')
ax1.grid(True, alpha=0.3)
ax1.set_xlabel('Frequency (Hz)', fontsize=12)
ax1.set_ylabel('SPL (dB)', fontsize=12)
ax1.set_title('Viberesp vs Hornresp - Full Frequency Response', fontsize=14, fontweight='bold')
ax1.legend(loc='best', fontsize=10)
ax1.set_xlim([10, 20000])
ax1.set_ylim([50, 100])

# Plot 2: High-frequency zoom
ax2 = axes[1]
ax2.semilogx(freqs_hr, spl_hr, 'b-', linewidth=2, label='Hornresp', alpha=0.7)
ax2.semilogx(freqs_hr, spl_vib, 'r--', linewidth=2, label='Viberesp', alpha=0.7)
ax2.axvline(f_Le, color='orange', linestyle=':', linewidth=1.5, label=f'$f_{{Le}}$ = {f_Le:.0f} Hz')
ax2.axvline(f_mass, color='purple', linestyle=':', linewidth=1.5, label=f'$f_{{mass}}$ = {f_mass} Hz')
ax2.grid(True, alpha=0.3)
ax2.set_xlabel('Frequency (Hz)', fontsize=12)
ax2.set_ylabel('SPL (dB)', fontsize=12)
ax2.set_title('High-Frequency Zoom (Voice Coil Inductance Region)', fontsize=14, fontweight='bold')
ax2.legend(loc='best', fontsize=10)
ax2.set_xlim([100, 20000])
ax2.set_ylim([50, 100])

# Plot 3: Error/difference
ax3 = axes[2]
ax3.semilogx(freqs_hr, diff_all, 'k-', linewidth=1.5, alpha=0.7)
ax3.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax3.axhline(np.mean(diff_hf), color='green', linestyle='--', linewidth=2,
            label=f'HF mean (≥2kHz): {np.mean(diff_hf):+.3f} dB')
ax3.axhline(np.mean(diff_bass), color='red', linestyle='--', linewidth=2,
            label=f'Bass mean (<200Hz): {np.mean(diff_bass):+.3f} dB')
ax3.axvline(f_Le, color='orange', linestyle=':', linewidth=1.5, label=f'$f_{{Le}}$ = {f_Le:.0f} Hz')
ax3.axvline(2000, color='blue', linestyle=':', linewidth=1.5, alpha=0.5, label='2 kHz boundary')
ax3.grid(True, alpha=0.3)
ax3.set_xlabel('Frequency (Hz)', fontsize=12)
ax3.set_ylabel('Viberesp - Hornresp (dB)', fontsize=12)
ax3.set_title('Difference Plot (Positive = Viberesp Higher)', fontsize=14, fontweight='bold')
ax3.legend(loc='best', fontsize=10)
ax3.set_xlim([10, 20000])
ax3.set_ylim([-10, 10])

plt.tight_layout()
output_file = 'tasks/voice_coil_inductance_hornresp_agreement.png'
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"Plot saved to: {output_file}")
print()
print("=" * 80)
