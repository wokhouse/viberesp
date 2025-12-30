#!/usr/bin/env python3
"""
BC_8FMB51 Sealed Bookshelf Speaker Design

Cabinet: 10" D × 15" H × 12" W (external)
Configuration: Horn-loaded compression driver on top
Enclosure: Sealed box with damping

Design goals:
- F3 ~85-90 Hz for 2-way bookshelf use
- Optimal damping for sealed box (can use heavier fill)
- Clean transients for horn integration
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from viberesp.driver.loader import load_driver
from viberesp.enclosure.sealed_box import (
    calculate_sealed_box_system_parameters,
    calculate_spl_from_transfer_function,
)
from viberesp.enclosure.damping_materials import (
    DampingMaterial,
    DAMPING_MATERIAL_PRESETS,
    calculate_effective_volume,
    calculate_qa_from_material,
    get_material,
)
from viberesp.hornresp.export import export_to_hornresp


def print_section(title: str):
    print('\n' + '=' * 70)
    print(f'  {title}')
    print('=' * 70)


def calculate_spl_with_damping(
    frequency: float,
    driver,
    Vb_physical: float,
    material: DampingMaterial,
    fill_ratio: float,
    voltage: float = 2.83,
    measurement_distance: float = 1.0,
    Quc: float = 7.0,
) -> float:
    """Calculate SPL for sealed box with damping material."""
    # Calculate effective volume
    Vb_effective = calculate_effective_volume(
        Vb_physical, fill_ratio, material, account_for_displacement=True
    )

    # Calculate SPL
    spl = calculate_spl_from_transfer_function(
        frequency=frequency,
        driver=driver,
        Vb=Vb_effective,
        voltage=voltage,
        measurement_distance=measurement_distance,
        Quc=Quc,
    )

    return spl


def design_bc8fmb51_sealed():
    """Design BC_8FMB51 sealed bookshelf speaker."""

    # Load driver
    driver = load_driver('BC_8FMB51')

    print_section('BC_8FMB51 Sealed Bookshelf Design')

    # Cabinet dimensions
    depth_ext = 10.0  # inches
    height_ext = 15.0  # inches
    width_ext = 12.0  # inches

    wall_thickness = 0.75  # inches (3/4" MDF)

    # Internal dimensions
    depth_int = (depth_ext - 2 * wall_thickness) * 25.4  # mm
    height_int = (height_ext - 2 * wall_thickness) * 25.4  # mm
    width_int = (width_ext - 2 * wall_thickness) * 25.4  # mm

    volume_total = (depth_int * height_int * width_int) / 1e6  # Liters

    # Deductions
    horn_volume = 2.5  # L (compression driver pathway)
    driver_disp = 0.5  # L (driver displacement)
    bracing = 1.5  # L (internal bracing)

    Vb_physical = (volume_total - horn_volume - driver_disp - bracing) / 1000  # m³

    print(f'Cabinet: {depth_ext}" D × {height_ext}" H × {width_ext}" W')
    print(f'Internal: {depth_int:.0f} × {height_int:.0f} × {width_int:.0f} mm')
    print(f'Total internal volume: {volume_total:.1f} L')
    print(f'Usable woofer volume: {Vb_physical*1000:.1f} L')
    print()

    # System parameters without damping first
    params = calculate_sealed_box_system_parameters(
        driver=driver,
        Vb=Vb_physical,
        Quc=10.0,  # Unfilled box (mechanical losses only)
    )

    print(f'Design targets:')
    print(f'  Box volume: {Vb_physical*1000:.1f} L')
    print(f'  Compliance ratio α: {params.alpha:.2f}')
    print(f'  System Qtc: {params.Qtc_total:.2f}')
    print(f'  F3: {params.F3:.1f} Hz')
    print(f'  Fc: {params.Fc:.1f} Hz')
    print()

    # Damping material selection
    # Sealed boxes can use heavier damping than ported
    # 25-50% fill is appropriate
    material_preset = 'dacron'
    fill_ratio = 0.30  # 30% fill (moderate for sealed)

    material = get_material(material_preset)

    print_section('Damping Material')
    print(f'Material: {material.name}')
    print(f'Fill ratio: {fill_ratio*100:.0f}%')
    print()

    # Calculate effective volume
    Vb_effective = calculate_effective_volume(
        Vb_physical, fill_ratio, material, account_for_displacement=True
    )

    print(f'Physical volume: {Vb_physical*1000:.2f} L')
    print(f'Effective volume: {Vb_effective*1000:.2f} L (+{(Vb_effective/Vb_physical-1)*100:.1f}%)')
    print()

    # Recalculate system parameters with effective volume
    params_damped = calculate_sealed_box_system_parameters(
        driver=driver,
        Vb=Vb_effective,
        Quc=7.0,  # Moderate damping from Dacron fill
    )

    print(f'With damping:')
    print(f'  Effective Qtc: {params_damped.Qtc_total:.2f}')
    print(f'  Adjusted F3: {params_damped.F3:.1f} Hz')
    print(f'  Adjusted Fc: {params_damped.Fc:.1f} Hz')
    print()

    print(f'Damping notes:')
    print(f'  • 30% Dacron fill provides moderate damping')
    print(f'  • Lowers Qtc from {params.Qtc_total:.2f} to {params_damped.Qtc_total:.2f}')
    print(f'  • Increases effective volume by {(Vb_effective/Vb_physical-1)*100:.1f}%')
    print(f'  • Improves transient response')
    print(f'  • Reduces internal standing waves')
    print()

    # Calculate frequency response
    print_section('Performance')

    frequencies = np.logspace(1.5, 3.5, 400)
    spl_with_damping = []
    for f in frequencies:
        spl = calculate_spl_with_damping(
            frequency=f,
            driver=driver,
            Vb_physical=Vb_physical,
            material=material,
            fill_ratio=fill_ratio,
            voltage=2.83,
            measurement_distance=1.0,
            Quc=7.0,
        )
        spl_with_damping.append(spl)

    spl_with_damping = np.array(spl_with_damping)

    # Find F3
    spl_max = np.max(spl_with_damping)
    target = spl_max - 3

    # Find crossing on bass side
    bass_region = frequencies < 200
    bass_freqs = frequencies[bass_region]
    bass_spl = spl_with_damping[bass_region]

    crossings = np.where(np.diff(np.sign(bass_spl - target)) > 0)[0]
    if len(crossings) > 0:
        idx = crossings[0]
        f1, f2 = bass_freqs[idx], bass_freqs[idx+1]
        s1, s2 = bass_spl[idx], bass_spl[idx+1]
        f3 = f1 + (target - s1) * (f2 - f1) / (s2 - s1)
    else:
        f3 = np.nan

    print(f'System performance (2.83V, 1m):')
    print(f'  SPL max: {spl_max:.1f} dB')
    print(f'  F3 (-3dB): {f3:.1f} Hz')
    print(f'  Fc (system resonance): {params_damped.Fc:.1f} Hz')
    print(f'  Qtc (system Q): {params_damped.Qtc_total:.2f}')
    print()

    print(f'Bass response:')
    for freq in [40, 50, 60, 70, 80, 90, 100, 150]:
        idx = np.argmin(np.abs(frequencies - freq))
        rel = spl_max - spl_with_damping[idx]
        marker = " <-- Fc" if abs(freq - params_damped.Fc) < 3 else ""
        print(f'  {freq:3d} Hz: {spl_with_damping[idx]:5.1f} dB ({rel:+5.1f} dB){marker}')

    # Calculate without damping for comparison
    spl_no_damping = np.array([calculate_spl_from_transfer_function(
        f, driver, Vb_physical, 2.83, 1.0, 343.0, 1.18, None, 10.0
    ) for f in frequencies])

    spl_max_no_damp = np.max(spl_no_damping)
    target_no_damp = spl_max_no_damp - 3
    crossings_no_damp = np.where(np.diff(np.sign(spl_no_damping[:200] - target_no_damp)) > 0)[0]
    if len(crossings_no_damp) > 0:
        idx = crossings_no_damp[0]
        f1, f2 = frequencies[idx], frequencies[idx+1]
        s1, s2 = spl_no_damping[idx], spl_no_damping[idx+1]
        f3_no_damp = f1 + (target_no_damp - s1) * (f2 - f1) / (s2 - s1)
    else:
        f3_no_damp = np.nan

    print()
    print(f'Damping benefit:')
    print(f'  Without damping: F3 = {f3_no_damp:.1f} Hz')
    print(f'  With 30% Dacron:  F3 = {f3:.1f} Hz')
    print(f'  Improvement: {f3_no_damp - f3:.1f} Hz lower F3')
    print()

    # Export to Hornresp (note: Hornresp doesn't support damping in sealed boxes)
    output_dir = Path('tasks/validation')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'BC_8FMB51_sealed_bookshelf.txt'

    export_to_hornresp(
        driver=driver,
        driver_name='BC_8FMB51 Sealed Bookshelf',
        output_path=str(output_path),
        comment=f'Sealed box: {Vb_physical*1000:.1f}L, Qtc={params_damped.Qtc_total:.2f}, Dacron {fill_ratio*100:.0f}% fill',
        enclosure_type='sealed_box',
        Vb_liters=Vb_physical * 1000,
    )

    print(f'✓ Exported to Hornresp: {output_path}')
    print('  Note: Hornresp export uses physical volume (no damping model)')

    # Plot frequency response
    print_section('Generating Frequency Response Plot')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # Plot 1: Full frequency response with and without damping
    ax1.semilogx(frequencies, spl_with_damping, 'b-', linewidth=2, label='With 30% Dacron')
    ax1.semilogx(frequencies, spl_no_damping, 'r--', linewidth=1.5, alpha=0.7, label='No damping')
    ax1.axhline(y=spl_max - 3, color='gray', linestyle='--', alpha=0.3, label='-3dB')
    ax1.axvline(x=f3, color='b', linestyle=':', alpha=0.5, label=f"F3={f3:.0f}Hz (damped)")
    ax1.axvline(x=params_damped.Fc, color='g', linestyle=':', alpha=0.5, label=f"Fc={params_damped.Fc:.0f}Hz")
    ax1.axvline(x=driver.F_s, color='orange', linestyle=':', alpha=0.5, label=f"Fs={driver.F_s:.0f}Hz")

    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('SPL (dB)')
    ax1.set_title(f'BC_8FMB51 Sealed Bookshelf Comparison\n'
                 f'Vb={Vb_physical*1000:.1f}L, {fill_ratio*100:.0f}% Dacron fill')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.set_xlim([20, 5000])
    ax1.set_ylim([70, 105])

    # Plot 2: Bass region detail
    bass_mask = frequencies < 200
    ax2.plot(frequencies[bass_mask], spl_with_damping[bass_mask], 'b-', linewidth=2, label='With 30% Dacron')
    ax2.plot(frequencies[bass_mask], spl_no_damping[bass_mask], 'r--', linewidth=1.5, alpha=0.7, label='No damping')
    ax2.axhline(y=spl_max - 3, color='gray', linestyle='--', alpha=0.3)
    ax2.axvline(x=f3, color='b', linestyle=':', alpha=0.5, label=f"F3={f3:.0f}Hz")
    ax2.axvline(x=f3_no_damp, color='r', linestyle=':', alpha=0.5, label=f"F3={f3_no_damp:.0f}Hz (no damp)")

    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('SPL (dB)')
    ax2.set_title('Bass Response Detail')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_xlim([20, 200])
    ax2.set_ylim([75, 105])

    plt.tight_layout()

    plot_path = output_dir / 'BC_8FMB51_sealed_response.png'
    plt.savefig(plot_path, dpi=150)
    print(f'✓ Saved plot: {plot_path}')

    # Construction summary
    print_section('Construction Summary')

    # Calculate damping material mass
    material_density = material.density  # kg/m³
    fill_volume_m3 = Vb_physical * fill_ratio
    material_mass_kg = fill_volume_m3 * material_density

    print(f"""
CABINET: {depth_ext}" D × {height_ext}" H × {width_ext}" W (external)
Material: 3/4" (19mm) MDF

WOOFER SECTION (bottom):
────────────────────────────────────────────────────────────
  • Internal volume: {Vb_physical*1000:.1f} L
  • Effective volume (with damping): {Vb_effective*1000:.1f} L
  • Driver: BC_8FMB51 (8" mid-bass)
  • Driver cutout: ~190mm diameter
  • Driver mounting: 8 holes, #8 wood screws

SYSTEM PARAMETERS:
────────────────────────────────────────────────────────────
  • Compliance ratio α: {params_damped.alpha:.2f}
  • System Qtc: {params_damped.Qtc_total:.2f} (ideal: 0.5-0.7)
  • System resonance Fc: {params_damped.Fc:.1f} Hz
  • F3 (-3dB): {f3:.1f} Hz
  • Response: 2nd-order high-pass (12 dB/octave)

DAMPING:
────────────────────────────────────────────────────────────
  • Material: {material.name}
  • Amount: {fill_ratio*100:.0f}% fill
  • Volume: {fill_volume_m3*1000:.1f} L ({fill_volume_m3*1000/28.32:.1f} ft³)
  • Mass: {material_mass_kg:.2f} kg ({material_mass_kg*2.205:.1f} lbs)
  • Purchase: ~{material_mass_kg*1.2:.1f} kg (include extra for compression)

  Installation:
    1. Line all internal walls with Dacron batting
    2. Fill center lightly, don't pack tightly
    3. Keep area behind driver clear
    4. Secure with spray adhesive or staples

  Alternative materials:
    • Polyester fiberfill (pillow stuffing): 25-35% fill
    • Acoustic foam: Line walls only (25mm thick)

HORN SECTION (top):
────────────────────────────────────────────────────────────
  • Volume: ~2.5 L for compression driver pathway
  • Mount compression driver horn above woofer
  • Internal partition separates horn from woofer chamber
  • Partition should be airtight

BRACING:
────────────────────────────────────────────────────────────
  • Cross-brace between front and rear baffles
  • Window brace in center (keeps woofer from seeing brace)
  • Account for ~1.5L displacement

GASKET:
────────────────────────────────────────────────────────────
  • Use foam gasket or silicone around driver mounting
  • Ensures airtight seal (critical for sealed box)

PERFORMANCE:
────────────────────────────────────────────────────────────
  • F3: {f3:.0f} Hz
  • Fc: {params_damped.Fc:.1f} Hz
  • Qtc: {params_damped.Qtc_total:.2f} (tight, controlled bass)
  • Max SPL: {spl_max:.0f} dB (2.83V, 1m)
  • Transient response: Excellent
  • Suitable for 2-way with horn compression driver

CROSSOVER NOTES:
────────────────────────────────────────────────────────────
  • Woofer naturally rolls off above ~2 kHz
  • Horn compression driver: 500 Hz - 20 kHz range
  • Recommended crossover: Linkwitz-Riley 4th order @ 1.8-2 kHz
  • Horn provides pattern control above crossover frequency
  • Sealed woofer matches well with horn characteristics

POWER HANDLING:
────────────────────────────────────────────────────────────
  • Below Fc: Driver excursion limited
  • Above Fc: Thermally limited
  • Sealed box has better power handling below resonance
  • Can use {driver.X_max*1000:.1f}mm Xmax to full advantage

ADVANTAGES OF SEALED BOX:
────────────────────────────────────────────────────────────
  ✓ Smaller cabinet than ported (no port volume needed)
  ✓ Tighter, more accurate bass (better transients)
  ✓ No port noise or chuffing
  ✓ Better power handling below resonance
  ✓ Easier to build (no port to design/install)
  ✓ More placement flexibility (near walls OK)
  ✓ Better integration with horn compression driver

TRADE-OFFS:
────────────────────────────────────────────────────────────
  ✗ Higher F3 than ported ({f3:.0f} Hz vs ~95 Hz for this driver/volume)
  ✗ Less bass extension (but still respectable for bookshelf)
  ✗ Requires slightly more amplifier power at low frequencies
  ✗ -3 dB/octave steeper rolloff below Fc vs ported

AMPLIFIER REQUIREMENTS:
────────────────────────────────────────────────────────────
  • Minimum: 50W/channel solid state
  • Recommended: 100W/channel for headroom
  • Stable into 4Ω (driver Re = {driver.R_e:.1f}Ω)
  • High current capability preferred for bass control
""")

    print_section('Design Complete')
    print()
    print('Next steps:')
    print('  1. Import BC_8FMB51_sealed_bookshelf.txt into Hornresp to validate')
    print('  2. Adjust damping amount to taste (20-40% fill range)')
    print('  3. Design crossover for compression driver')
    print('  4. Build cabinets!')

    return params_damped, frequencies, spl_with_damping


if __name__ == '__main__':
    params, frequencies, spl = design_bc8fmb51_sealed()
