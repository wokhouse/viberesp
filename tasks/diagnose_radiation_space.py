#!/usr/bin/env python3
"""
Diagnose radiation space discrepancy between viberesp and Hornresp.

Hornresp uses Ang = 2.0 x Pi (half-space)
Viberesp uses 4π in pressure formula (full-space)

This should cause a 3.01 dB difference.
"""

import sys
sys.path.insert(0, 'src')

import math
import numpy as np
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import calculate_spl_from_transfer_function

# Driver parameters
driver = ThieleSmallParameters(
    M_md=0.0267,
    C_ms=0.0008,
    R_ms=1.53,
    R_e=6.3,
    L_e=0.00035,
    BL=5.8,
    S_d=0.0217,
)

Vb = 0.010  # 10L
f_mass = 450
test_freq = 1000  # Hz - midband frequency

print("=" * 80)
print("RADIATION SPACE DIAGNOSTIC")
print("=" * 80)
print()
print(f"Test frequency: {test_freq} Hz")
print(f"Hornresp Ang parameter: 2.0 x Pi (half-space)")
print()

# Calculate current viberesp SPL
spl_current = calculate_spl_from_transfer_function(
    test_freq, driver, Vb, f_mass=f_mass, Quc=float('inf')
)

print(f"Current viberesp SPL: {spl_current:.2f} dB")
print()

# Manual calculation of pressure with different radiation spaces
# Efficiency calculation
alpha = driver.V_as / Vb
eta_0 = (driver.BL ** 2 * driver.S_d ** 2) / (driver.R_e * driver.M_ms * driver.C_ms)
eta = eta_0 / (1.0 + alpha)

# Reference power
voltage = 2.83
R_nominal = driver.R_e
P_ref = voltage ** 2 / R_nominal

# Physical constants
air_density = 1.18
speed_of_sound = 343.0
measurement_distance = 1.0
p_ref = 20e-6  # 20 μPa

print("Manual pressure calculation:")
print(f"  Efficiency η: {eta:.6f}")
print(f"  Reference power P_ref: {P_ref:.3f} W")
print()

# Full-space radiation (4π) - what our code uses
pressure_full = math.sqrt(eta * P_ref * air_density * speed_of_sound /
                          (4 * math.pi * measurement_distance ** 2))
spl_full = 20 * math.log10(pressure_full / p_ref)

# Half-space radiation (2π) - what Hornresp uses
pressure_half = math.sqrt(eta * P_ref * air_density * speed_of_sound /
                          (2 * math.pi * measurement_distance ** 2))
spl_half = 20 * math.log10(pressure_half / p_ref)

print("Without calibration offset:")
print(f"  Full-space (4π):  {spl_full:.2f} dB")
print(f"  Half-space (2π):  {spl_half:.2f} dB")
print(f"  Difference:       {spl_half - spl_full:.2f} dB")
print(f"  Expected:         3.01 dB (20×log₁₀(√2))")
print()

# Apply calibration offset
CALIBRATION_OFFSET_DB = -25.25
spl_full_cal = spl_full + CALIBRATION_OFFSET_DB
spl_half_cal = spl_half + CALIBRATION_OFFSET_DB

print("With current calibration offset (-25.25 dB):")
print(f"  Full-space (4π):  {spl_full_cal:.2f} dB")
print(f"  Half-space (2π):  {spl_half_cal:.2f} dB")
print()

# Load Hornresp result
hornresp_file = "imports/hf_roll_sim.txt"
with open(hornresp_file, 'r') as f:
    lines = f.readlines()
    for line in lines[2:]:
        if line.strip() and not line.startswith('Freq'):
            parts = line.split()
            if len(parts) >= 5:
                freq = float(parts[0])
                if abs(freq - test_freq) < 5:
                    spl_hr = float(parts[4])
                    print(f"Hornresp (2π):     {spl_hr:.2f} dB")
                    print()
                    print("Comparison:")
                    print(f"  Viberesp - Hornresp: {spl_current - spl_hr:.2f} dB")
                    print(f"  Full-space cal - Hornresp: {spl_full_cal - spl_hr:.2f} dB")
                    print(f"  Half-space cal - Hornresp: {spl_half_cal - spl_hr:.2f} dB")
                    break

print()
print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
print()
print("If viberesp uses 4π (full-space) and Hornresp uses 2π (half-space),")
print("then to match Hornresp we should use 2π in the pressure formula.")
print()
print("Expected fix: Change 4π → 2π in sealed_box.py line 364")
print("This should reduce the bass offset by ~3 dB.")
print()
