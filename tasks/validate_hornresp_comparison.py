#!/usr/bin/env python3
"""
Validate viberesp voice coil inductance implementation against Hornresp simulation.

This script compares viberesp predictions with Hornresp simulation output to
validate that our complex transfer function implementation correctly models
voice coil inductance effects.

Literature:
- Leach (2002), "Introduction to Electroacoustics", Eq. 4.20
- Small (1972), "Direct-Radiator Loudspeaker System Analysis"
- Research: tasks/ported_box_transfer_function_research_brief.md
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import calculate_spl_from_transfer_function

# ==============================================================================
# DRIVER: BC 8NDL51 (same as Hornresp simulation)
# ==============================================================================
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
print("VOICE COIL INDUCTANCE VALIDATION - VIBERESP VS HORNRESP")
print("=" * 80)
print()
print("Driver: BC 8NDL51")
print(f"  F_s   = {driver.F_s:.2f} Hz")
print(f"  Q_ts  = {driver.Q_ts:.3f}")
print(f"  V_as  = {driver.V_as*1000:.2f} L")
print(f"  R_e   = {driver.R_e:.2f} Ω")
print(f"  L_e   = {driver.L_e*1000:.2f} mH")
print(f"  f_Le  = {f_Le:.1f} Hz (inductance corner)")
print(f"  f_mass = {f_mass} Hz (mass break, empirical)")
print()
print(f"Enclosure: Sealed Box {Vb*1000:.1f}L")
print(f"  Fc    = {Fc:.2f} Hz (system resonance)")
print()

# ==============================================================================
# PARSE HORNRESP SIMULATION RESULTS
# ==============================================================================
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
            if len(parts) >= 5:  # Should have Freq, Ra, Xa, Za, SPL at minimum
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

# ==============================================================================
# CALCULATE VIBERESP PREDICTIONS
# ==============================================================================
print("Calculating viberesp predictions at same frequencies...")
print()

# Calculate viberesp predictions with HF rolloff
spl_vib = np.array([
    calculate_spl_from_transfer_function(
        f, driver, Vb, f_mass=f_mass, Quc=float('inf')
    )
    for f in freqs_hr
])

# Calculate viberesp predictions WITHOUT HF rolloff (baseline)
spl_vib_no_hf = np.array([
    calculate_spl_from_transfer_function(
        f, driver, Vb, f_mass=None, Quc=float('inf')
    )
    for f in freqs_hr
])

print()

# ==============================================================================
# COMPARISON AT KEY FREQUENCIES
# ==============================================================================
print("=" * 80)
print("FREQUENCY RESPONSE COMPARISON")
print("=" * 80)
print()

# Key comparison frequencies
key_freqs = [20, 50, 100, 200, 500, 1000, 2000, 2865, 5000, 10000]

print(f"{'Freq (Hz)':>12} | {'Hornresp':>10} | {'VibResp':>10} | {'Δ (H-V)':>10}")
print("-" * 50)

for f in key_freqs:
    # Find closest frequency in Hornresp data
    idx = np.argmin(np.abs(freqs_hr - f))
    f_actual = freqs_hr[idx]

    spl_hr_f = spl_hr[idx]
    spl_vib_f = spl_vib[idx]

    # Calculate difference
    diff = spl_vib_f - spl_hr_f

    # Add marker if f is close to special frequencies
    marker = ""
    if abs(f_actual - Fc) < 5:
        marker = " ← Fc"
    elif abs(f_actual - f_Le) < 5:
        marker = " ← f_Le"

    print(f"{f_actual:>10.1f} | {spl_hr_f:>10.2f} | {spl_vib_f:>10.2f} | {diff:>10.2f}{marker}")

print()

# ==============================================================================
# STATISTICAL ANALYSIS
# ==============================================================================
print("=" * 80)
print("STATISTICAL VALIDATION")
print("=" * 80)
print()

# Calculate differences across all frequencies
diff_all = spl_vib - spl_hr
diff_bass = spl_vib[freqs_hr < 200] - spl_hr[freqs_hr < 200]
diff_mid = spl_vib[(freqs_hr >= 200) & (freqs_hr < 2000)] - spl_hr[(freqs_hr >= 200) & (freqs_hr < 2000)]
diff_hf = spl_vib[freqs_hr >= 2000] - spl_hr[freqs_hr >= 2000]

print(f"Full range ({freqs_hr[0]:.0f} - {freqs_hr[-1]:.0f} Hz, {len(freqs_hr)} points):")
print(f"  Mean error:     {np.mean(np.abs(diff_all)):.3f} dB")
print(f"  RMS error:      {np.sqrt(np.mean(diff_all**2)):.3f} dB")
print(f"  Max error:     {np.max(np.abs(diff_all)):.3f} dB")
print(f"  Min error:     {np.min(np.abs(diff_all)):.3f} dB")
print()

print(f"Bass region (<200 Hz, {np.sum(freqs_hr < 200)} points):")
print(f"  Mean error:     {np.mean(np.abs(diff_bass)):.3f} dB")
print(f"  RMS error:      {np.sqrt(np.mean(diff_bass**2)):.3f} dB")
print()

print(f"Midrange (200-2000 Hz, {np.sum((freqs_hr >= 200) & (freqs_hr < 2000))} points):")
print(f"  Mean error:     {np.mean(np.abs(diff_mid)):.3f} dB")
print(f"  RMS error:      {np.sqrt(np.mean(diff_mid**2)):.3f} dB")
print()

print(f"High-freq (≥2000 Hz, {np.sum(freqs_hr >= 2000)} points):")
print(f"  Mean error:     {np.mean(np.abs(diff_hf)):.3f} dB")
print(f"  RMS error:      {np.sqrt(np.mean(diff_hf**2)):.3f} dB")
print()

# Check for systematic bias
print(f"Systematic bias (mean of signed errors): {np.mean(diff_all):.3f} dB")
if np.abs(np.mean(diff_all)) > 0.5:
    print(f"  ⚠️  Bias detected! viberresp is {'higher' if np.mean(diff_all) > 0 else 'lower'} than Hornresp")
else:
    print(f"  ✓ No significant bias (|bias| < 0.5 dB)")
print()

# ==============================================================================
# HIGH-FREQUENCY ROLLOFF VALIDATION
# ==============================================================================
print("=" * 80)
print("HIGH-FREQUENCY ROLLOFF VALIDATION")
print("=" * 80)
print()

# Compare rolloff at specific frequencies
rolloff_freqs = [500, 1000, 2000, 5000, 10000]
print(f"{'Frequency':>12} | {'Hornresp':>10} | {'VibResp':>10} | {'Δ from 100Hz':>15}")
print("-" * 65)

# Find 100 Hz reference in Hornresp
idx_100 = np.argmin(np.abs(freqs_hr - 100))
ref_spl_hr = spl_hr[idx_100]
ref_spl_vib = spl_vib[idx_100]

for f in rolloff_freqs:
    idx = np.argmin(np.abs(freqs_hr - f))
    f_actual = freqs_hr[idx]

    spl_hr_f = spl_hr[idx]
    spl_vib_f = spl_vib[idx]

    # Calculate rolloff from 100 Hz reference
    rolloff_hr = spl_hr_f - ref_spl_hr
    rolloff_vib = spl_vib_f - ref_spl_vib

    print(f"{f_actual:>10.1f} | {spl_hr_f:>10.2f} | {spl_vib_f:>10.2f} | {rolloff_vib:>15.2f} / {rolloff_hr:>10.2f}")

print()

# ==============================================================================
# INDUCTANCE CORNER FREQUENCY VALIDATION
# ==============================================================================
print("=" * 80)
print(f"INDUCTANCE CORNER FREQUENCY (f_Le = {f_Le:.1f} Hz)")
print("=" * 80)
print()

# Check SPL at f_Le
idx_fLe = np.argmin(np.abs(freqs_hr - f_Le))
f_actual = freqs_hr[idx_fLe]

spl_hr_fLe = spl_hr[idx_fLe]
spl_vib_fLe = spl_vib[idx_fLe]

# Calculate expected -3 dB point relative to midband
# Find "flat" region reference (500-1000 Hz)
idx_ref = np.argmin(np.abs(freqs_hr - 700))
ref_spl = spl_hr[idx_ref]

# Expected rolloff at f_Le: -3 dB from corner (first-order filter)
expected_rolloff = -3.01
actual_rolloff_hr = spl_hr_fLe - ref_spl
actual_rolloff_vib = spl_vib_fLe - ref_spl

print(f"At f_Le = {f_actual:.1f} Hz:")
print(f"  Hornresp SPL:   {spl_hr_fLe:.2f} dB")
print(f"  Viberesp SPL:   {spl_vib_fLe:.2f} dB")
print(f"  Reference SPL:   {ref_spl:.2f} dB (at {freqs_hr[idx_ref]:.0f} Hz)")
print()
print(f"  Hornresp rolloff: {actual_rolloff_hr:.2f} dB")
print(f"  Viberesp rolloff: {actual_rolloff_vib:.2f} dB")
print(f"  Expected (1st order): {expected_rolloff:.2f} dB")
print()

# Validate corner frequency behavior
if abs(actual_rolloff_vib - expected_rolloff) < 1.0:
    print(f"  ✓ Viberresp correctly shows ~{expected_rolloff:.0f} dB rolloff at f_Le")
else:
    print(f"  ⚠️  Viberesp rolloff differs from expected by {abs(actual_rolloff_vib - expected_rolloff):.2f} dB")

print()

# ==============================================================================
# FINAL VALIDATION SUMMARY
# ==============================================================================
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print()

# Calculate percentage of points within tolerance
tolerances = [0.5, 1.0, 2.0, 3.0]
for tol in tolerances:
    count = np.sum(np.abs(diff_all) <= tol)
    pct = 100 * count / len(diff_all)
    print(f"  Points within ±{tol} dB: {count:4d}/{len(diff_all):4d} ({pct:5.1f}%)")

print()
print("Validation criteria:")
print("  ✓ Mean error < 1 dB: ", "PASS" if np.abs(np.mean(diff_all)) < 1.0 else "FAIL")
print("  ✓ RMS error < 2 dB: ", "PASS" if np.sqrt(np.mean(diff_all**2)) < 2.0 else "FAIL")
print("  ✓ Max error < 5 dB: ", "PASS" if np.max(np.abs(diff_all)) < 5.0 else "FAIL")
print()

if (np.abs(np.mean(diff_all)) < 1.0 and
    np.sqrt(np.mean(diff_all**2)) < 2.0 and
    np.max(np.abs(diff_all)) < 5.0):
    print("🎉 VALIDATION SUCCESSFUL! Viberesp matches Hornresp within tolerance.")
else:
    print("⚠️  Validation shows significant differences. Investigate discrepancies.")

print()
print("=" * 80)
