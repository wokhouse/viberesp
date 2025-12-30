#!/usr/bin/env python3
"""Test different radiation space assumptions to match Hornresp."""

import numpy as np
from viberesp.driver import load_driver
from viberesp.hornresp.results_parser import load_hornresp_sim_file
import math

# Constants
RHO = 1.18  # Air density kg/m³
C = 343.0   # Speed of sound m/s
P_REF = 20e-6  # Reference pressure Pa

# Load driver and Hornresp data
driver = load_driver("BC_8NDL51")
Vb = 0.03165  # 31.65L box
voltage = 2.83
hr_data = load_hornresp_sim_file("tests/validation/drivers/bc_8ndl51/sealed_box/sim.txt")

# Calculate efficiency using Small (1972), Eq. 24
k = (4 * math.pi ** 2) / (C ** 3)
eta_0 = k * (driver.F_s ** 3 * driver.V_as) / driver.Q_es

print(f"Driver: BC_8NDL51")
print(f"Efficiency (η₀): {eta_0:.6f} ({eta_0*100:.3f}%)")
print(f"Input power: {voltage**2/driver.R_e:.3f} W")
print()

# Test at 500 Hz (well above resonance, flat response)
test_freq = 500
f_idx = (np.abs(hr_data.frequency - test_freq)).argmin()
hr_spl = hr_data.spl_db[f_idx]

print(f"Frequency: {test_freq} Hz")
print(f"Hornresp SPL: {hr_spl:.2f} dB")
print()

# Calculate SPL with different radiation space assumptions
P_ref = voltage ** 2 / driver.R_e

print("Testing different radiation space assumptions:")
print("-" * 70)
print(f"{'Radiation Space':<20} {'Steradians':<12} {'SPL (dB)':<12} {'Error':<10}")
print("-" * 70)

radiation_spaces = [
    ("Full space (4π)", 4 * math.pi),
    ("Half space (2π)", 2 * math.pi),
    ("Quarter space (π)", math.pi),
    ("Eighth space (π/2)", math.pi / 2),
]

for name, steradians in radiation_spaces:
    # Pressure calculation for this radiation space
    pressure_rms = math.sqrt(
        eta_0 * P_ref * RHO * C / (steradians * 1.0 ** 2)
    )
    spl = 20 * math.log10(pressure_rms / P_REF)
    error = spl - hr_spl

    print(f"{name:<20} {steradians:<12.4f} {spl:<12.2f} {error:>+7.2f} dB")

print("-" * 70)
print()

# Check B&C datasheet specification
print("B&C 8NDL51 Datasheet:")
print(f"  Sensitivity: 94 dB (2.83V @ 1m)")
print()

# Calculate theoretical sensitivity using Small's formula
# SPL_1W/1m = 112.2 + 10*log10(η₀) for half-space
spl_theory = 112.2 + 10 * math.log10(eta_0)
print(f"Theoretical sensitivity (Small formula): {spl_theory:.2f} dB")

# Calculate using actual power (3.08W, not 1W)
power_actual = voltage ** 2 / driver.R_e
spl_theory_actual = spl_theory + 10 * math.log10(power_actual)
print(f"Theoretical SPL at {power_actual:.2f}W: {spl_theory_actual:.2f} dB")
print()

# Check which radiation space matches the datasheet
for name, steradians in radiation_spaces:
    pressure_rms = math.sqrt(
        eta_0 * power_actual * RHO * C / (steradians * 1.0 ** 2)
    )
    spl = 20 * math.log10(pressure_rms / P_REF)
    if abs(spl - 94.0) < 0.5:
        print(f"✓ {name} matches datasheet ({spl:.2f} dB vs 94 dB spec)")
    elif abs(spl - 94.7) < 0.5:
        print(f"✓ {name} matches theoretical ({spl:.2f} dB vs 94.7 dB theory)")
