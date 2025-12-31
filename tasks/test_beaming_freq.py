#!/usr/bin/env python3
"""
Quick test script to compare different HF drivers with their beaming frequencies.

This helps verify that the dynamic beaming frequency parameter is working correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from viberesp.driver import get_driver_info

# Test drivers to compare
drivers = ["BC_DH350", "GENERIC_SMALL_VQ", "GENERIC_RING_RADIATOR"]

print("=" * 70)
print("HF DRIVER BEAMING FREQUENCY COMPARISON")
print("=" * 70)
print()

for driver_name in drivers:
    info = get_driver_info(driver_name)
    comp_params = info.get('compression_driver', {})

    beaming_freq = comp_params.get('beaming_freq', 'NOT SET')
    diaphragm = comp_params.get('diaphragm_diameter', 'NOT SET')
    sensitivity = info.get('datasheet', {}).get('sensitivity', 'NOT SET')

    print(f"{driver_name}:")
    print(f"  Sensitivity: {sensitivity} dB")
    print(f"  Diaphragm: {diaphragm*1000 if isinstance(diaphragm, (int, float)) else diaphragm} mm")
    print(f"  Beaming Freq: {beaming_freq} Hz")

    # Calculate theoretical beaming based on diaphragm size
    if isinstance(diaphragm, (int, float)):
        c = 343  # speed of sound
        f_beam_theoretical = c / (3.14159 * diaphragm)
        print(f"  Theoretical f_beam (no plug): {f_beam_theoretical:.0f} Hz")
        print(f"  Phase plug extension: {beaming_freq / f_beam_theoretical:.1f}x" if isinstance(beaming_freq, (int, float)) else "")

    print()

print("=" * 70)
print("KEY INSIGHTS:")
print("=" * 70)
print()
print("- Ring radiators have the HIGHEST beaming frequency (>16kHz)")
print("  → Best HF extension, minimal treble droop")
print()
print("- Small diaphragms (34mm) beam at ~9kHz")
print("  → Better than standard 44mm dome")
print()
print("- Standard 44mm domes (DH350) beam at ~5kHz")
print("  → Limited HF extension, causes treble droop in 2-way systems")
print()
print("For ±3dB flatness in a 2-way system:")
print("  → Ring radiator is theoretically ideal")
print("  → Small diaphragm may also work")
print("  → Standard dome (DH350) likely fails due to 5kHz beaming")
print()
