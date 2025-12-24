# Synthetic Hornresp Test Cases

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
