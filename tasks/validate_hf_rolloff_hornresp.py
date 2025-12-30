#!/usr/bin/env python3
"""
Generate Hornresp input parameters for voice coil inductance validation.

This script creates a Hornresp-compatible input file and prints key
validation points for comparing viberesp vs Hornresp HF rolloff.

Literature:
- Leach (2002), "Introduction to Electroacoustics", Eq. 4.20
- Small (1972), "Direct-Radiator Loudspeaker System Analysis"
- Research: tasks/ported_box_transfer_function_research_brief.md
"""

import sys
sys.path.insert(0, 'src')

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import (
    calculate_sealed_box_system_parameters,
    calculate_spl_from_transfer_function
)
from viberesp.hornresp.export import export_to_hornresp

# ==============================================================================
# DRIVER: BC 8NDL51 (simulated)
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

# ==============================================================================
# ENCLOSURE: Sealed Box 10L
# ==============================================================================
Vb = 0.010  # 10L sealed box
f_mass = 450  # Hz (empirically determined for BC 8NDL51)

# Calculate system parameters
params = calculate_sealed_box_system_parameters(driver, Vb)

# Calculate inductance corner frequency
f_Le = driver.R_e / (2 * 3.14159 * driver.L_e)

print("=" * 80)
print("VOICE COIL INDUCTANCE VALIDATION - HORNRESP COMPARISON")
print("=" * 80)
print()
print("Driver: BC 8NDL51 (simulated)")
print("-" * 80)
print(f"  M_md  = {driver.M_md*1000:.2f} g   (driver mass only)")
print(f"  M_ms  = {driver.M_ms*1000:.2f} g   (total mass including radiation)")
print(f"  C_ms  = {driver.C_ms*10:.6f} mm/N (suspension compliance)")
print(f"  R_ms  = {driver.R_ms:.2f} N·s/m  (mechanical resistance)")
print(f"  R_e   = {driver.R_e:.2f} Ω       (DC resistance)")
print(f"  L_e   = {driver.L_e*1000:.2f} mH     (voice coil inductance)")
print(f"  BL    = {driver.BL:.2f} T·m    (force factor)")
print(f"  S_d   = {driver.S_d*10000:.2f} cm²  (effective area)")
print()
print(f"  F_s   = {driver.F_s:.2f} Hz    (resonance frequency)")
print(f"  Q_ts  = {driver.Q_ts:.3f}      (total Q factor)")
print(f"  V_as  = {driver.V_as*1000:.2f} L     (equivalent volume)")
print()
print("Enclosure: Sealed Box")
print("-" * 80)
print(f"  Vb    = {Vb*1000:.2f} L       (box volume)")
print(f"  α     = {params.alpha:.3f}         (compliance ratio)")
print(f"  Fc    = {params.Fc:.2f} Hz    (system resonance)")
print(f"  Qtc   = {params.Qtc_total:.3f}     (system Q)")
print()
print("High-Frequency Parameters")
print("-" * 80)
print(f"  f_Le  = {f_Le:.1f} Hz       (inductance corner: Re/(2πLe))")
print(f"  f_mass = {f_mass} Hz        (mass break frequency, empirical)")
print()

# ==============================================================================
# EXPORT TO HORNRESP FORMAT
# ==============================================================================
print("=" * 80)
print("HORNRESP INPUT FILE")
print("=" * 80)
print()

export_filename = "tasks/validation/BC_8NDL51_HF_rolloff_validation.txt"
export_to_hornresp(
    driver=driver,
    driver_name="BC 8NDL51 HF Rolloff Validation",
    output_path=export_filename,
    comment=f"Sealed box {Vb*1000:.1f}L, f_mass={f_mass}Hz for HF rolloff validation",
    enclosure_type="sealed_box",
    Vb_liters=Vb * 1000,
)

print(f"✓ Hornresp input file created: {export_filename}")
print()
print("INSTRUCTIONS:")
print("  1. Open Hornresp")
print("  2. File -> Import -> Select the exported file")
print("  3. Run simulation (SPL response)")
print("  4. Compare with viberesp values below")
print()

# ==============================================================================
# VALIDATION POINTS - VIBERESP CALCULATIONS
# ==============================================================================
print("=" * 80)
print("VALIDATION POINTS - VIBERESP PREDICTIONS")
print("=" * 80)
print()

# Key frequencies for validation
validation_freqs = [
    20, 50, 100, 200,  # Bass region
    params.Fc,         # System resonance
    500, 1000, 2000,   # Midrange
    f_Le,             # Inductance corner
    5000, 10000, 20000  # High frequencies
]

# Remove duplicates and sort
validation_freqs = sorted(set(validation_freqs))

print(f"{'Frequency':>12} | {'SPL (no HF)':>12} | {'SPL (with HF)':>12} | {'HF Rolloff':>12}")
print("-" * 65)

for f in validation_freqs:
    spl_no_hf = calculate_spl_from_transfer_function(
        f, driver, Vb, f_mass=None, Quc=float('inf')
    )
    spl_with_hf = calculate_spl_from_transfer_function(
        f, driver, Vb, f_mass=f_mass, Quc=float('inf')
    )
    hf_rolloff = spl_with_hf - spl_no_hf

    # Mark special frequencies
    marker = ""
    if abs(f - params.Fc) < 1:
        marker = " ← Fc (system resonance)"
    elif abs(f - f_Le) < 1:
        marker = " ← f_Le (inductance corner)"

    print(f"{f:>12.1f} | {spl_no_hf:>12.2f} | {spl_with_hf:>12.2f} | {hf_rolloff:>12.2f}{marker}")

print()
print("Notes:")
print("  - SPL at 1m, 2.83V input")
print("  - Quc=∞ (no mechanical losses) to match Hornresp")
print("  - HF Rolloff column shows the effect of voice coil inductance")
print()

# ==============================================================================
# EXPECTED ROLLOFF RATES
# ==============================================================================
print("=" * 80)
print("EXPECTED ROLLOFF RATES")
print("=" * 80)
print()

# Calculate rolloff in different regions
freq_regions = [
    ("Bass (50-200 Hz)", 50, 200),
    ("Midrange (200-2000 Hz)", 200, 2000),
    (f"High (2000-{int(f_Le)} Hz)", 2000, int(f_Le)),
    (f"Very High ({int(f_Le)}-20000 Hz)", int(f_Le), 20000),
]

print(f"{'Region':>30} | {'Range (Hz)':>15} | {'Rolloff (dB/oct)':>17}")
print("-" * 70)

for region_name, f_low, f_high in freq_regions:
    spl_low = calculate_spl_from_transfer_function(
        f_low, driver, Vb, f_mass=f_mass, Quc=float('inf')
    )
    spl_high = calculate_spl_from_transfer_function(
        f_high, driver, Vb, f_mass=f_mass, Quc=float('inf')
    )

    octaves = (f_high / f_low) ** 0.5  # log2(f_high/f_low) in base 2
    # Actually: octaves = log2(f_high/f_low)
    import math
    octaves = math.log2(f_high / f_low)
    rolloff = (spl_low - spl_high) / octaves

    print(f"{region_name:>30} | {f_low:>6.0f} - {f_high:<6.0f} | {rolloff:>17.2f}")

print()
print("Expected values:")
print("  - Bass/Midrange: ~0 dB/octave (flat response)")
print("  - High region: ~6 dB/octave (inductance only)")
print("  - Very high: ~12 dB/octave (inductance + mass, combined)")
print()

# ==============================================================================
# COMPARISON CHECKLIST
# ==============================================================================
print("=" * 80)
print("HORNRESP COMPARISON CHECKLIST")
print("=" * 80)
print()
print("After importing into Hornresp and running simulation, check:")
print()
print("□ SPL at system resonance (Fc)")
print(f"   Expected: ~{calculate_spl_from_transfer_function(params.Fc, driver, Vb, f_mass=f_mass):.1f} dB")
print()
print("□ -3 dB point (F3)")
print(f"   Expected: ~{params.F3:.1f} Hz")
print()
print("□ High-frequency rolloff above 2 kHz")
print("   Should show ~12 dB/octave slope")
print()
print("□ Absolute SPL levels in flat region (100-500 Hz)")
print("   Should match within ±2 dB")
print()
print("□ Rolloff corner frequency")
print(f"   Should see transition around f_Le = {f_Le:.0f} Hz")
print()
print("=" * 80)
print("IMPORTANT: Hornresp Voice Coil Inductance Settings")
print("=" * 80)
print()
print("Hornresp automatically includes voice coil inductance effects when Le > 0.")
print("The exported Hornresp file includes Le = 0.35 mH.")
print()
print("However, Hornresp does NOT have a direct 'f_mass' parameter.")
print("The f_mass = 450 Hz value we use is empirically determined to match Hornresp.")
print()
print("Expected behavior in Hornresp:")
print("  - Hornresp will show HF rolloff from Le (inductance)")
print("  - The rolloff slope may differ slightly from our f_mass model")
print("  - Focus on validating the INDUCTANCE effect (f_Le), not the exact mass break")
print()
print("=" * 80)
print("FILES GENERATED")
print("=" * 80)
print()
print(f"1. Hornresp input: {export_filename}")
print(f"2. Visualization:  tasks/voice_coil_inductance_rolloff.png")
print(f"3. This log:      tasks/validate_hf_rolloff_hornresp.py (run to regenerate)")
print()
