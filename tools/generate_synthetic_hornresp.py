#!/usr/bin/env python3
"""
Generate synthetic Hornresp test cases for validation.

This script creates 4 Hornresp-format parameter files representing
progressively complex horn configurations to validate physics models.

Test Cases:
1. Straight Exponential Horn (simplest)
2. Horn + Rear Chamber
3. Horn + Front Chamber
4. Complete System (F118 Simplified)

Usage:
    python generate_synthetic_hornresp.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from viberesp.core.models import ThieleSmallParameters
from viberesp.validation.hornresp_exporter import export_hornresp_params


def create_idealized_driver() -> ThieleSmallParameters:
    """Create an idealized 18" driver for synthetic testing."""
    return ThieleSmallParameters(
        fs=30.0,           # Free-air resonance (Hz)
        qes=0.25,          # Electrical Q
        qms=5.0,           # Mechanical Q
        sd=0.121,          # Diaphragm area (1210 cm² = 0.121 m²)
        re=6.0,            # Voice coil resistance (Ω)
        bl=35.0,           # Force factor (T·m)
        mms=300.0,         # Moving mass (g)
        cms=8.24e-5,       # Mechanical compliance (m/N)
        rms=15.0,          # Mechanical resistance (N·s/m)
        le=3.5,            # Voice coil inductance (mH)
        xmax=15.0,         # Maximum linear excursion (mm)
        pe=100.0,          # Thermal power handling (W)
        vas=200.0,         # Equivalent compliance volume (L)
        manufacturer="Idealized",
        model_number="18inch_Test",
    )


def create_bc18ds115_driver() -> ThieleSmallParameters:
    """Create B&C 18DS115 driver from datasheet."""
    return ThieleSmallParameters(
        fs=32.0,
        qes=0.38,
        qms=6.52,
        sd=0.121,          # 1210 cm²
        re=5.0,
        bl=39.0,
        mms=330.0,
        cms=8.24e-5,
        rms=14.72,
        le=3.85,
        xmax=16.5,
        pe=500.0,
        vas=158.0,
        manufacturer="B&C",
        model_number="18DS115",
    )


def generate_case1_straight_horn(output_dir: Path):
    """
    Test Case 1: Straight Exponential Horn (Simplest)

    Driver: Idealized 18" (Fs=30, Qts=0.2)
    Horn: Exponential, S1=600cm², S2=4800cm², L=200cm, fc=35Hz
    No front chamber, no rear chamber

    Expected: Pure horn loading, smooth exponential response
    """
    driver = create_idealized_driver()

    params = {
        'throat_area_cm2': 600.0,
        'mouth_area_cm2': 4800.0,
        'horn_length_cm': 200.0,
        'cutoff_frequency': 35.0,
        'rear_chamber_volume': 0.0,   # No rear chamber
        'front_chamber_volume': 0.0,   # No front chamber
    }

    output_path = output_dir / "synthetic_case1_straight_horn.txt"
    export_hornresp_params(
        driver=driver,
        params=params,
        enclosure_type='exponential_horn',
        output_path=str(output_path),
        comment="Synthetic Case 1: Straight Exponential Horn - No Chambers"
    )

    return output_path


def generate_case2_horn_with_rear_chamber(output_dir: Path):
    """
    Test Case 2: Horn + Rear Chamber

    Driver: Idealized 18" (Fs=30, Qts=0.2)
    Horn: Exponential, S1=600cm², S2=4800cm², L=200cm, fc=35Hz
    Rear chamber: 100L (compliance behind driver)

    Expected: Lowered F3, slight ripple from compliance-horn coupling
    """
    driver = create_idealized_driver()

    params = {
        'throat_area_cm2': 600.0,
        'mouth_area_cm2': 4800.0,
        'horn_length_cm': 200.0,
        'cutoff_frequency': 35.0,
        'rear_chamber_volume': 100.0,  # 100L rear chamber
        'front_chamber_volume': 0.0,    # No front chamber
    }

    output_path = output_dir / "synthetic_case2_horn_rear_chamber.txt"
    export_hornresp_params(
        driver=driver,
        params=params,
        enclosure_type='exponential_horn',
        output_path=str(output_path),
        comment="Synthetic Case 2: Horn + Rear Chamber (100L)"
    )

    return output_path


def generate_case3_horn_with_front_chamber(output_dir: Path):
    """
    Test Case 3: Horn + Front Chamber

    Driver: Idealized 18" (Fs=30, Qts=0.2)
    Horn: Exponential, S1=600cm², S2=4800cm², L=200cm, fc=35Hz
    Front chamber: 6L (compression chamber)

    Expected: Helmholtz dip + standing wave ripples
    """
    driver = create_idealized_driver()

    params = {
        'throat_area_cm2': 600.0,
        'mouth_area_cm2': 4800.0,
        'horn_length_cm': 200.0,
        'cutoff_frequency': 35.0,
        'rear_chamber_volume': 0.0,     # No rear chamber
        'front_chamber_volume': 6.0,    # 6L front chamber
    }

    output_path = output_dir / "synthetic_case3_horn_front_chamber.txt"
    export_hornresp_params(
        driver=driver,
        params=params,
        enclosure_type='front_loaded_horn',
        output_path=str(output_path),
        comment="Synthetic Case 3: Horn + Front Chamber (6L)"
    )

    return output_path


def generate_case4_complete_system(output_dir: Path):
    """
    Test Case 4: Complete System (F118 Simplified)

    Driver: B&C 18DS115
    Horn: Exponential, S1=600, S2=4800, L=200, fc=35
    Rear chamber: 100L
    Front chamber: 6L

    Expected: Combined effects, F3 ≈ 45-50 Hz
    """
    driver = create_bc18ds115_driver()

    params = {
        'throat_area_cm2': 600.0,
        'mouth_area_cm2': 4800.0,
        'horn_length_cm': 200.0,
        'cutoff_frequency': 35.0,
        'rear_chamber_volume': 100.0,  # 100L rear chamber
        'front_chamber_volume': 6.0,    # 6L front chamber
    }

    output_path = output_dir / "synthetic_case4_complete_system.txt"
    export_hornresp_params(
        driver=driver,
        params=params,
        enclosure_type='front_loaded_horn',
        output_path=str(output_path),
        comment="Synthetic Case 4: Complete System - B&C 18DS115 F118 Style"
    )

    return output_path


def generate_readme(output_dir: Path):
    """Generate README documenting the test cases."""
    content = """# Synthetic Hornresp Test Cases

This directory contains 4 Hornresp parameter files for validating
Viberesp horn modeling physics. These files are generated using the
export_hornresp_params() function to ensure correct formatting.

## Test Cases

### Case 1: `synthetic_case1_straight_horn.txt`
**Configuration:** Straight exponential horn, no chambers

- Driver: Idealized 18" (Fs=30 Hz, Qts=0.24)
- Horn: Exponential, S1=600cm², S2=4800cm², L=200cm, fc=35Hz
- Front chamber: None
- Rear chamber: None

**Expected Behavior:**
- Pure horn loading with smooth exponential response
- Cutoff at ~35 Hz with 12 dB/octave roll-off
- Horn gain ≈ 9 dB from area ratio (4800/600)

---

### Case 2: `synthetic_case2_horn_rear_chamber.txt`
**Configuration:** Horn + rear chamber

- Driver: Same as Case 1
- Horn: Same as Case 1
- Rear chamber: 100 L (compliance behind driver)
- Front chamber: None

**Expected Behavior:**
- Lowered F3 compared to Case 1 (sealed box effect)
- Slight ripple from compliance-horn coupling
- System Q increased by rear chamber

---

### Case 3: `synthetic_case3_horn_front_chamber.txt`
**Configuration:** Horn + front chamber

- Driver: Same as Case 1
- Horn: Same as Case 1
- Rear chamber: None
- Front chamber: 6 L (compression chamber)

**Expected Behavior:**
- Helmholtz resonance dip visible in response
- Standing wave ripples above 100 Hz (if multi-mode enabled)
- Front chamber acts as high-pass filter

---

### Case 4: `synthetic_case4_complete_system.txt`
**Configuration:** Complete F118-style system

- Driver: B&C 18DS115 (real datasheet parameters)
- Horn: Exponential, S1=600, S2=4800, L=200, fc=35
- Rear chamber: 100 L
- Front chamber: 6 L

**Expected Behavior:**
- Combined effects from all components
- F3 ≈ 45-50 Hz (similar to Hornresp F118)
- Passband ripple from coupled resonances
- Horn gain ≈ 9-10 dB

---

## Usage

### In Hornresp:
1. Open each `.txt` file: File → Import
2. Run simulation: Tools → Loudspeaker Parameters
3. Export results: File → Export → Frequency Response
4. Save as `synthetic_caseN_sim.txt`

### Validate Viberesp:
```python
from viberesp.validation import parse_hornresp_output, compare_responses
from viberesp.enclosures.horns import FrontLoadedHorn
from viberesp.core.models import EnclosureParameters, ThieleSmallParameters

# Create driver and parameters
driver = ThieleSmallParameters(...)
params = EnclosureParameters(
    enclosure_type='front_loaded_horn',
    throat_area_cm2=600,
    mouth_area_cm2=4800,
    horn_length_cm=200,
    cutoff_frequency=35,
    rear_chamber_volume=100,
    front_chamber_volume=6,
    front_chamber_modes=3,
    radiation_model='beranek',
)

# Simulate
enclosure = FrontLoadedHorn(driver, params)
frequencies, spl_db = enclosure.calculate_frequency_response(np.logspace(1, 3, 600))

# Compare to Hornresp
hornresp_data = parse_hornresp_output('synthetic_case4_sim.txt')
comparison = compare_responses(...)
```

---

## Expected Physics

### Horn Gain
```
gain_db = 10 × log10(S2/S1)
For S2=4800, S1=600: gain = 10 × log10(8) ≈ 9 dB
```

### Helmholtz Resonance (Front Chamber)
```
f_h = 1 / (2π × √(M_horn × C_fc))

For V_fc=6L, S_throat=600cm², L=15cm:
f_h ≈ 45 Hz
```

---

## Validation Metrics

Target accuracy for Phase 1:
- RMSE: < 5.0 dB
- F3 error: < 8.0 Hz
- Correlation: > 0.90
"""
    readme_path = output_dir / "README.md"
    readme_path.write_text(content)
    return readme_path


def main():
    """Generate all synthetic test cases."""
    # Get script directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "hornresp" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate test cases
    case1 = generate_case1_straight_horn(output_dir)
    print(f"✓ Generated: {case1.name}")
    print(f"  Straight Exponential Horn - No Chambers")

    case2 = generate_case2_horn_with_rear_chamber(output_dir)
    print(f"✓ Generated: {case2.name}")
    print(f"  Horn + Rear Chamber (100L)")

    case3 = generate_case3_horn_with_front_chamber(output_dir)
    print(f"✓ Generated: {case3.name}")
    print(f"  Horn + Front Chamber (6L)")

    case4 = generate_case4_complete_system(output_dir)
    print(f"✓ Generated: {case4.name}")
    print(f"  Complete System - B&C 18DS115 F118 Style")

    # Generate README
    readme = generate_readme(output_dir)
    print(f"✓ Generated: {readme.name}")

    print(f"\nAll synthetic test cases generated in: {output_dir}")
    print("\nNext steps:")
    print("1. Import each .txt file in Hornresp (File → Import)")
    print("2. Run simulation and export results")
    print("3. Use exported .txt files for Viberesp validation")


if __name__ == "__main__":
    main()
