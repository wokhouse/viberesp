#!/usr/bin/env python3
"""
BC_21DS115 Bass Horn Design Package

This script presents multiple horn design options for the B&C 21DS115 21" woofer,
ranging from compact to high-performance designs.

Design Options:
- Compact: 1 m² mouth, F3 ≈ 64 Hz (manageable size)
- Standard: 2.5 m² mouth, F3 ≈ 50 Hz (good bass extension)
- Large: 5 m² mouth, F3 ≈ 40 Hz (true subwoofer)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import matplotlib.pyplot as plt
from viberesp.driver.loader import load_driver
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn

# Load driver
driver = load_driver("BC_21DS115")

print("="*80)
print("BC_21DS115 BASS HORN DESIGN OPTIONS")
print("="*80)
print()

# Design options
designs = {
    "compact": {
        "name": "Compact Bass Horn",
        "throat_area": 0.015,  # 150 cm²
        "mouth_area": 1.0,     # 1 m² (1.1m diameter)
        "length": 3.5,         # 3.5 m
        "V_rc": 0.0,           # No rear chamber
        "description": "Manageable size, F3 ~64 Hz, good for bass guitar/kick drum"
    },
    "standard": {
        "name": "Standard Bass Horn",
        "throat_area": 0.015,  # 150 cm²
        "mouth_area": 2.5,     # 2.5 m² (1.8m diameter)
        "length": 4.0,         # 4 m
        "V_rc": 0.0,           # No rear chamber
        "description": "Good bass extension, F3 ~50 Hz, excellent for PA/subwoofer"
    },
    "large": {
        "name": "Large Bass Horn",
        "throat_area": 0.020,  # 200 cm² (slightly larger for 21" driver)
        "mouth_area": 5.0,     # 5 m² (2.5m diameter)
        "length": 4.5,         # 4.5 m
        "V_rc": 0.0,           # No rear chamber
        "description": "True subwoofer, F3 ~40 Hz, massive output"
    }
}

# Create horns and simulate
results = {}
for key, design in designs.items():
    horn = ExponentialHorn(
        throat_area=design["throat_area"],
        mouth_area=design["mouth_area"],
        length=design["length"]
    )
    flh = FrontLoadedHorn(driver, horn, V_tc=0.0, V_rc=design["V_rc"])

    # Calculate cutoff
    c = 343.0
    m = np.log(design["mouth_area"] / design["throat_area"]) / design["length"]
    fc = (c * m / 2.0) / (2 * np.pi)

    # Simulate response
    freqs = np.logspace(np.log10(20), np.log10(500), 200)
    spl_vals = [flh.spl_response(f, voltage=2.83) for f in freqs]
    spl_array = np.array(spl_vals)

    # Find F3
    ref_level = np.max(spl_array)
    f3_idx = np.where(spl_array[:80] <= ref_level - 3)[0]
    f3 = freqs[f3_idx[-1]] if len(f3_idx) > 0 else 20

    results[key] = {
        "horn": horn,
        "flh": flh,
        "fc": fc,
        "f3": f3,
        "freqs": freqs,
        "spl": spl_array,
        "ref_level": ref_level
    }

    # Print design summary
    print(f"{design['name'].upper()}")
    print("-"*80)
    print(design["description"])
    print()
    print(f"  Throat: {design['throat_area']*10000:.0f} cm²")
    print(f"  Mouth: {design['mouth_area']*10000:.0f} cm² ({design['mouth_area']:.1f} m²)")
    print(f"  Mouth diameter: {2*np.sqrt(design['mouth_area']/np.pi):.2f} m")
    print(f"  Length: {design['length']:.2f} m")
    print(f"  Horn cutoff fc: {fc:.1f} Hz")
    print(f"  F3 (-3dB): {f3:.1f} Hz")
    print(f"  Reference SPL: {ref_level:.1f} dB @ 1W/1m")
    print()

# Performance comparison table
print("="*80)
print("PERFORMANCE COMPARISON")
print("="*80)
print()
print(f"{'Design':<20} {'Mouth':<12} {'Length':<10} {'fc':<8} {'F3':<8} {'Ref SPL':<10}")
print("-"*80)
for key, design in designs.items():
    r = results[key]
    print(f"{design['name']:<20} {design['mouth_area']*10000:<12.0f} {design['length']:<10.1f} "
          f"{r['fc']:<8.1f} {r['f3']:<8.1f} {r['ref_level']:<10.1f}")
print()

# Detailed frequency comparison
print("="*80)
print("DETAILED FREQUENCY RESPONSE (dB SPL @ 1W/1m)")
print("="*80)
print()
print(f"{'Freq (Hz)':<12} {'Compact':<12} {'Standard':<12} {'Large':<12}")
print("-"*40)

test_freqs = [30, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400]
for freq in test_freqs:
    line = f"{freq:<12}"
    for key in ["compact", "standard", "large"]:
        flh = results[key]["flh"]
        spl = flh.spl_response(freq, voltage=2.83)
        line += f"{spl:<12.1f}"
    print(line)

print()

# Create comparison plot
fig, ax = plt.subplots(figsize=(14, 9))

colors = {"compact": "blue", "standard": "green", "large": "red"}

for key in ["compact", "standard", "large"]:
    r = results[key]
    design = designs[key]
    ax.semilogx(r["freqs"], r["spl"], linewidth=2.5,
                label=f"{design['name']} (F3={r['f3']:.1f}Hz)",
                color=colors[key])
    ax.axvline(x=r["f3"], linestyle=':', color=colors[key], alpha=0.5)

ax.set_xlabel('Frequency (Hz)', fontsize=14)
ax.set_ylabel('SPL (dB @ 1W/1m)', fontsize=14)
ax.set_title('BC_21DS115 Bass Horn - Design Options Comparison\n'
              'All designs: No throat/rear chamber, direct coupling', fontsize=16)
ax.grid(True, alpha=0.3)
ax.legend(loc='lower right', fontsize=12)
ax.set_xlim([20, 500])
ax.set_ylim([80, 110])

# Add design info text box
info_text = """DRIVER: B&C 21DS115 (21" woofer)
  • Sd: 1680 cm² (37% larger than 18")
  • BL: 38 T·m (51% stronger motor)
  • Xmax: 16.5 mm (65% more excursion)
  • Fs: 36 Hz, Qts: 0.30"""

ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()

# Save plot
output_path = Path(__file__).parent / "BC21DS115_bass_horn_comparison.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"Comparison plot saved to: {output_path}")
print()

# Build recommendations
print("="*80)
print("RECOMMENDATIONS")
print("="*80)
print()
print("CHOOSING THE RIGHT DESIGN:")
print()
print("1. COMPACT (1 m² mouth, F3 ≈ 64 Hz)")
print("   Best for: Bass guitar, kick drum, small venue PA")
print("   Pros: Manageable size (1.1m × 3.5m)")
print("   Cons: Limited bass extension below 60 Hz")
print()
print("2. STANDARD (2.5 m² mouth, F3 ≈ 50 Hz)")
print("   Best for: Full-range PA, subwoofer applications")
print("   Pros: Good balance of size and performance")
print("   Cons: Requires large space (1.8m × 4m)")
print()
print("3. LARGE (5 m² mouth, F3 ≈ 40 Hz)")
print("   Best for: Outdoor events, permanent installations")
print("   Pros: True subwoofer performance (40 Hz)")
print("   Cons: Massive size (2.5m × 4.5m)")
print()
print("PRACTICAL CONSIDERATIONS:")
print("-"*80)
print("  • All designs can be FOLDED to reduce footprint")
print("  • No rear chamber = driver needs protection below Fs")
print("  • Use high-pass filter at 35-40 Hz for driver safety")
print("  • Consider multiple horns (array) for even more output")
print()
print("NEXT STEPS:")
print("-"*80)
print("  1. Choose design based on application")
print("  2. Export to Hornresp for validation")
print("  3. Build folded horn if space is limited")
print("  4. Measure impedance and SPL after construction")
print()
