#!/usr/bin/env python3
"""
Extract BC_15DS115 driver and horn parameters for manual Hornresp entry.
"""

from viberesp.driver.bc_drivers import get_bc_15ds115
import json

# Load driver
driver = get_bc_15ds115()

# Load optimization results
with open("exports/bc15ds115_bass_horn_designs.json", "r") as f:
    results = json.load(f)

# Get top design (Design #2 - recommended)
top_design = results["best_designs"][1]  # Index 1 = Design #2
params = top_design["parameters"]

print("=" * 80)
print("BC_15DS115 DRIVER & HORN PARAMETERS FOR HORNRESP MANUAL ENTRY")
print("=" * 80)
print()

# Traditional Driver Parameters (in Hornresp units)
print("|TRADITIONAL DRIVER PARAMETER VALUES:")
print("-" * 80)
print(f"  Sd  = {driver.S_d * 10000:7.2f}  # Effective piston area (cm²)")
print(f"  Bl  = {driver.BL:7.2f}  # Force factor (T·m)")
print(f"  Cms = {driver.C_ms:.2E}  # Mechanical compliance (m/N)")
print(f"  Rms = {driver.R_ms:7.2f}  # Mechanical resistance (N·s/m)")
print(f"  Mmd = {driver.M_md * 1000:7.2f}  # Moving mass (g) - NOT M_ms!")
print(f"  Le  = {driver.L_e * 1000:7.2f}  # Voice coil inductance (mH)")
print(f"  Re  = {driver.R_e:7.2f}  # DC resistance (Ω)")
print(f"  Nd  = {1:7d}  # Number of drivers")
print()

# Radiation and Source Parameters
print("|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:")
print("-" * 80)
print(f"  Ang = 2.0 x Pi  # Half-space (front-loaded horn)")
print(f"  Eg  = 2.83      # Input voltage (V) for 1W into 8Ω")
print(f"  Rg  = 0.00      # Source resistance (Ω)")
print()

# Horn Parameters
print("|HORN PARAMETER VALUES:")
print("-" * 80)
throat_cm2 = params["throat_area"] * 10000
mouth_cm2 = params["mouth_area"] * 10000
length_m = params["length"]

# Calculate flare constant
import numpy as np
if params["mouth_area"] > params["throat_area"] and params["length"] > 0:
    flare_constant = np.log(params["mouth_area"] / params["throat_area"]) / params["length"]
else:
    flare_constant = 0.0

# Calculate cutoff frequency for Hornresp (F12 = c * m / 4π)
from viberesp.simulation.constants import SPEED_OF_SOUND
f12_hornresp = (SPEED_OF_SOUND * flare_constant) / (4.0 * np.pi)

print(f"  S1  = {throat_cm2:7.2f}  # Throat area (cm²)")
print(f"  S2  = {mouth_cm2:7.2f}  # Mouth area (cm²)")
print(f"  Exp = 50.00      # Exponential horn (fixed)")
print(f"  F12 = {f12_hornresp:7.2f}  # Cutoff frequency (Hz) - Hornresp formula")
print(f"  L12 = {length_m:7.2f}  # Horn length (m)")
print()

# Calculate flare constant for reference
print(f"DERIVED PARAMS:")
print(f"  Flare constant (m) = {flare_constant:.3f} m⁻¹")
print(f"  Horn cutoff (Olson) = {(SPEED_OF_SOUND * flare_constant) / (2 * np.pi):.2f} Hz")
print(f"  Hornresp F12 formula = {f12_hornresp:.2f} Hz (uses 4π, not 2π!)")
print()

# Throat and Rear Chambers
print("|CHAMBER PARAMETER VALUES:")
print("-" * 80)
vtc_liters = params["V_tc"] * 1000
vrc_liters = params["V_rc"] * 1000

# Calculate rear chamber depth (auto-calculated for Hornresp)
# Lrc = cube_root(Vrc) typically, or constrained by driver depth
import math
lrc_cm = (vrc_liters * 1000) ** (1/3)  # Cube root in cm
lrc_cm = max(2 * (driver.S_d * 10000 / (4 * np.pi))**0.5 * 100, lrc_cm)  # At least 2×piston radius

print(f"  Vtc = {vtc_liters:.3f}  # Throat chamber volume (L)")
print(f"  Atc = {throat_cm2:.2f}  # Throat chamber area (cm²) - same as horn throat")
print(f"  Vrc = {vrc_liters:.2f}  # Rear chamber volume (L)")
print(f"  Lrc = {lrc_cm:.2f}  # Rear chamber depth (cm) - auto-calculated")
print()

# Performance objectives
print("DESIGN PERFORMANCE:")
print("-" * 80)
print(f"  F3  = {top_design['objectives']['f3']:.2f} Hz")
print(f"  Efficiency optimized (check Hornresp for actual %)")
print()

# Geometry summary
print("GEOMETRY SUMMARY:")
print("-" * 80)
print(f"  Throat diameter:  {2 * np.sqrt(params['throat_area'] / np.pi) * 100:.1f} cm")
print(f"  Mouth diameter:   {2 * np.sqrt(params['mouth_area'] / np.pi) * 100:.1f} cm")
print(f"  Horn length:      {params['length']:.2f} m")
print(f"  Horn volume:      {np.pi * params['length'] * (params['throat_area'] + params['mouth_area'] + np.sqrt(params['throat_area'] * params['mouth_area'])) / 3 * 1000:.1f} L")
print(f"  Total volume:     {(params['V_rc'] + np.pi * params['length'] * (params['throat_area'] + params['mouth_area'] + np.sqrt(params['throat_area'] * params['mouth_area'])) / 3) * 1000:.1f} L")
print()

print("=" * 80)
print("MANUAL ENTRY SEQUENCE IN HORNRESP:")
print("=" * 80)
print("1. File → New")
print("2. Enter driver parameters (Sd, Bl, Cms, Rms, Mmd, Le, Re)")
print("3. Enter horn parameters (S1, S2, F12, L12)")
print("4. Enter chamber parameters (Vtc, Atc, Vrc, Lrc)")
print("5. Set Ang = 2.0 x Pi, Eg = 2.83, Rg = 0.00")
print("6. Calculate → simulate")
print()
print("NOTE: M_md (not M_ms) is critical! Hornresp calculates its own radiation mass.")
print("      If you enter M_ms, Hornresp will double-count radiation loading.")
print("=" * 80)
