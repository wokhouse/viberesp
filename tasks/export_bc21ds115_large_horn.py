#!/usr/bin/env python3
"""
Export BC_21DS115 Large Bass Horn to Hornresp

This script exports the optimal large bass horn design for the BC_21DS115
to Hornresp format for validation.

Design: Large Bass Horn (5 m² mouth, F3 ≈ 39 Hz)
  • Throat: 200 cm²
  • Mouth: 50000 cm² (5.0 m²)
  • Length: 4.5 m
  • F3: ~39 Hz
  • Reference SPL: 104.4 dB @ 1W/1m
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from viberesp.driver.loader import load_driver
from viberesp.simulation.types import ExponentialHorn, HornSegment, MultiSegmentHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn

# Load driver
driver = load_driver("BC_21DS115")

print("="*80)
print("BC_21DS115 LARGE BASS HORN - HORNRESP EXPORT")
print("="*80)
print()

# Horn parameters (Large design)
throat_area = 0.020  # 200 cm²
mouth_area = 5.0     # 50000 cm² (5 m²)
length = 4.5         # 4.5 m
V_tc = 0.0           # No throat chamber
V_rc = 0.0           # No rear chamber

# Create exponential horn
horn = ExponentialHorn(throat_area=throat_area, mouth_area=mouth_area, length=length)
flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

print("Design Parameters:")
print("-"*80)
print(f"  Driver: B&C 21DS115 (21\" woofer)")
print(f"  Throat area: {throat_area*10000:.0f} cm²")
print(f"  Mouth area: {mouth_area*10000:.0f} cm² ({mouth_area:.1f} m²)")
print(f"  Mouth diameter: {2*(mouth_area/3.14159)**0.5:.2f} m ({2*(mouth_area/3.14159)**0.5*100:.0f} cm)")
print(f"  Horn length: {length:.2f} m")
print(f"  Throat chamber: None (V_tc = 0)")
print(f"  Rear chamber: None (V_rc = 0)")
print()

# Calculate horn parameters
import numpy as np
c = 343.0
m = np.log(mouth_area / throat_area) / length
fc = (c * m / 2.0) / (2 * np.pi)

print(f"Horn Characteristics:")
print("-"*80)
print(f"  Flare constant (Olson m): {m:.3f} m⁻¹")
print(f"  Cutoff frequency fc: {fc:.1f} Hz")
print(f"  Expansion ratio: {mouth_area/throat_area:.1f}x")
print()

# Simulate and find F3
freqs = np.logspace(np.log10(20), np.log10(200), 200)
spl_vals = [flh.spl_response(f, voltage=2.83) for f in freqs]
spl_array = np.array(spl_vals)

ref_level = np.max(spl_array)
f3_idx = np.where(spl_array[:80] <= ref_level - 3)[0]
f3 = freqs[f3_idx[-1]] if len(f3_idx) > 0 else 20

print(f"Performance:")
print("-"*80)
print(f"  F3 (-3dB): {f3:.1f} Hz")
print(f"  Reference SPL: {ref_level:.1f} dB @ 1W/1m")
print(f"  SPL @ 40 Hz: {flh.spl_response(40, voltage=2.83):.1f} dB")
print(f"  SPL @ 50 Hz: {flh.spl_response(50, voltage=2.83):.1f} dB")
print(f"  SPL @ 80 Hz: {flh.spl_response(80, voltage=2.83):.1f} dB")
print(f"  SPL @ 100 Hz: {flh.spl_response(100, voltage=2.83):.1f} dB")
print()

# For Hornresp export, we need to provide appropriate parameters
# Hornresp uses different format for horns
# This is a simplified export showing the key parameters

print("="*80)
print("HORNRESP IMPORT INSTRUCTIONS")
print("="*80)
print()
print("Hornresp doesn't directly support exponential horn export from viberesp yet,")
print("but you can manually enter these parameters:")
print()
print("In Hornresp, use:")
print(f"  • S1: {throat_area*10000:.0f}  (throat area in cm²)")
print(f"  • S2: {mouth_area*10000:.0f}  (mouth area in cm²)")
print(f"  • L12: {length:.2f}  (horn length in meters)")
print(f"  • F12: {fc:.1f}  (cutoff frequency - Hornresp will calculate this)")
print()
print("For the driver parameters, use the datasheet values:")
print(f"  • Re: {driver.R_e:.1f} ohms")
print(f"  • Fs: {driver.F_s:.1f} Hz")
print(f"  • Vas: {driver.V_as*1000:.0f} liters")
print(f"  • Qts: {driver.Q_ts:.3f}")
print(f"  • Sd: {driver.S_d*10000:.0f} cm²")
print(f"  • BL: {driver.BL:.1f} T·m")
print(f"  • Mmd: {driver.M_md*1000:.1f} g  (NOT Mms!)")
print()
print("Note: Hornresp will add its own radiation mass loading.")
print("Use Mmd (driver mass only), not Mms (total moving mass).")
print()

# Create a summary file
output_file = Path(__file__).parent / "BC21DS115_large_bass_horn_summary.txt"
with open(output_file, 'w') as f:
    f.write("="*80 + "\n")
    f.write("BC_21DS115 LARGE BASS HORN - DESIGN SUMMARY\n")
    f.write("="*80 + "\n\n")

    f.write("DRIVER: B&C 21DS115\n")
    f.write("-"*80 + "\n")
    f.write(f"  Fs: {driver.F_s:.1f} Hz\n")
    f.write(f"  Qts: {driver.Q_ts:.3f}\n")
    f.write(f"  Vas: {driver.V_as*1000:.0f} L\n")
    f.write(f"  Sd: {driver.S_d*10000:.0f} cm²\n")
    f.write(f"  BL: {driver.BL:.1f} T·m\n")
    f.write(f"  Xmax: {driver.X_max*1000:.1f} mm\n")
    f.write(f"  Re: {driver.R_e:.1f} ohms\n\n")

    f.write("HORN GEOMETRY:\n")
    f.write("-"*80 + "\n")
    f.write(f"  Profile: Exponential\n")
    f.write(f"  Throat area: {throat_area*10000:.0f} cm² ({throat_area*1e6:.0f} mm²)\n")
    f.write(f"  Mouth area: {mouth_area*10000:.0f} cm² ({mouth_area:.1f} m²)\n")
    f.write(f"  Mouth diameter: {2*(mouth_area/np.pi)**0.5:.2f} m ({2*(mouth_area/np.pi)**0.5*100:.0f} cm)\n")
    f.write(f"  Length: {length:.2f} m ({length*100:.0f} cm)\n")
    f.write(f"  Flare constant: {m:.3f} m⁻¹\n")
    f.write(f"  Cutoff fc: {fc:.1f} Hz\n\n")

    f.write("CHAMBERS:\n")
    f.write("-"*80 + "\n")
    f.write(f"  Throat chamber: None (V_tc = 0 m³)\n")
    f.write(f"  Rear chamber: None (V_rc = 0 m³)\n\n")

    f.write("PREDICTED PERFORMANCE:\n")
    f.write("-"*80 + "\n")
    f.write(f"  F3 (-3dB): {f3:.1f} Hz\n")
    f.write(f"  Reference SPL: {ref_level:.1f} dB @ 1W/1m\n")
    f.write(f"  Horn cutoff: {fc:.1f} Hz\n\n")

    f.write("FREQUENCY RESPONSE:\n")
    f.write("-"*80 + "\n")
    f.write(f"{'Freq (Hz)':<12} {'SPL (dB)':<12}\n")
    f.write("-"*25 + "\n")
    for freq in [30, 40, 50, 63, 80, 100, 125, 160, 200]:
        spl = flh.spl_response(freq, voltage=2.83)
        f.write(f"{freq:<12} {spl:<12.1f}\n")
    f.write("\n")

    f.write("BUILD NOTES:\n")
    f.write("-"*80 + "\n")
    f.write("  • This is a MASSIVE horn (2.5m diameter × 4.5m long)\n")
    f.write("  • Consider folding to fit in practical cabinet\n")
    f.write("  • No rear chamber = driver needs protection below Fs\n")
    f.write("  • Use high-pass filter at 35-40 Hz for driver safety\n")
    f.write("  • Build with rigid materials (18mm+ plywood)\n")
    f.write("  • Seal all joints airtight\n")
    f.write("  • Driver mounting: rear-loaded (horn in front of driver)\n\n")

    f.write("LITERATURE:\n")
    f.write("-"*80 + "\n")
    f.write("  • Olson (1947) - Elements of Acoustical Engineering\n")
    f.write("  • Beranek (1954) - Acoustics\n")
    f.write("  • Kolbrek (2018) - Horn Theory Tutorial\n\n")

print(f"Design summary saved to: {output_file}")
print()

print("="*80)
print("VALIDATION CHECKLIST")
print("="*80)
print()
print("Before building:")
print("  1. Export parameters to Hornresp")
print("  2. Compare impedance and SPL response")
print("  3. Verify F3 matches within ±3 Hz")
print("  4. Check excursion limits at max power")
print("  5. Design folding pattern (if applicable)")
print()
print("After building:")
print("  1. Measure impedance (look for peaks at Fs and horn resonance)")
print("  2. Measure SPL response")
print("  3. Compare with predictions")
print("  4. Adjust rear chamber if needed to tune response")
print()
