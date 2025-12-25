# TC-P1-RAD-01: Hornresp Setup Notes

## Test Case Overview

**ID**: TC-P1-RAD-01
**Name**: Small ka (Low Frequency)
**Purpose**: Verify radiation impedance behavior when ka << 1 (mass-controlled region)

## Target Parameters

- Mouth area: 1257 cm² (20 cm radius)
- Test frequency: 50 Hz
- Expected ka: 0.18
- Expected R_norm: 0.016
- Expected X_norm: 0.24

## Hornresp Configuration Rationale

### Geometry: Short Straight Duct

```
S1 = S2 = 1257 cm² (no expansion, straight duct)
Length = 0.1 cm (minimal transmission line effects)
```

**Why this works:**
- A straight duct with equal input/output areas minimizes horn flare effects
- Minimal length ensures throat impedance ≈ mouth impedance
- Throat impedance Z_throat = Z_radiation + Z_duct ≈ Z_radiation when L → 0

### Radiation Angle: Half-Space

```
Ang = 0.5 x Pi
```

**Why this works:**
- Half-space radiation approximates a piston in an infinite baffle
- This matches the theoretical assumptions for circular piston radiation impedance

### Driver: Idealized Parameters

```
Sd = 1257 cm²   (matches mouth area for continuity)
Bl = 1.00 T·m   (arbitrary, will cancel out in normalization)
Cms = 1.0E-6 m/N (very large compliance → low mechanical impedance)
Rms = 0.00 N·s/m (zero mechanical resistance)
Mmd = 0.00 g    (zero moving mass)
Le = 0.00 mH    (zero inductance)
Re = 0.01 Ω     (near-zero resistance)
```

**Why this works:**
- Ideal driver minimizes mechanical impedance contributions
- With Z_mechanical ≈ 0, throat impedance is dominated by radiation impedance
- Very low Re prevents numerical issues while maintaining near-ideal behavior

### Chamber: Zero Rear Volume

```
Vrc = 0.001 L   (effectively zero → acts as infinite baffle)
```

**Why this works:**
- Zero rear chamber volume creates an acoustically rigid rear boundary
- This approximates an infinite baffle condition

## Data Extraction Procedure

### Step 1: Import into Hornresp

1. Open Hornresp application
2. File → Open → Select `hornresp_params.txt`
3. Verify all parameters loaded correctly

### Step 2: Generate Impedance Data

1. Go to **Tools** → **Loudspeaker Driver**
2. Select **Electrical Impedance** tab
3. Set frequency range: 20 Hz to 200 Hz
4. Set number of points: 181 (1 Hz resolution)
5. Click **Calculate** to generate impedance curve
6. Click **Save** to export impedance data

### Step 3: Extract Throat Impedance

From the impedance export, extract:
- Frequency (Hz)
- Resistance (R) in ohms
- Reactance (X) in ohms
- Impedance magnitude |Z| in ohms
- Phase angle (degrees)

### Step 4: Normalize to Radiation Impedance

Convert electrical impedance to acoustic radiation impedance:

```python
import numpy as np

# Constants
rho_0 = 1.204  # kg/m³
c = 343.7      # m/s
S = 1257 / 10000  # m² (convert cm² to m²)

# For each frequency point:
Z_electrical = R + 1j * X  # ohms

# Convert to acoustic impedance (simplified, assumes ideal driver)
# Note: This is an approximation - exact conversion requires full T-matrix analysis
Z_acoustic = Z_electrical * (rho_0 * c / S)  # Pa·s/m³

# Normalize to characteristic impedance
Z_norm = Z_acoustic / (rho_0 * c / S)

# Expected: Z_norm = R_norm + j*X_norm
```

**Note**: The exact conversion from electrical to acoustic impedance depends on the full driver equivalent circuit. For validation purposes, we compare the normalized trend and values.

### Step 5: Compare with Theoretical Values

At 50 Hz (ka = 0.18):
- Theoretical R_norm = 0.016
- Theoretical X_norm = 0.24

Calculate percentage error:
```
error_R = |R_extracted - 0.016| / 0.016 × 100%
error_X = |X_extracted - 0.24| / 0.24 × 100%
```

Acceptable tolerance: ±5%

## Validation Checklist

- [ ] Hornresp parameters loaded correctly
- [ ] Impedance data exported for frequency range 20-200 Hz
- [ ] Throat impedance extracted at 50 Hz
- [ ] Normalized impedance calculated
- [ ] R_norm within ±5% of 0.016
- [ ] X_norm within ±5% of 0.24
- [ ] Mass loading behavior verified (X dominates when ka << 1)

## Known Limitations

1. **Driver Idealization**: The idealized driver parameters are not physically realizable. This is intentional to isolate radiation impedance effects.

2. **Numerical Precision**: Hornresp may have numerical limitations with extreme parameter values. If issues occur, try:
   - Increasing Cms to 1.0E-5
   - Increasing Re to 0.1 Ω
   - Increasing duct length to 1.0 cm

3. **Conversion Simplification**: The electrical-to-acoustic impedance conversion is simplified. For exact validation, a full T-matrix analysis comparing Hornresp throat impedance with analytical radiation impedance is preferred.

## References

- Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound Fields and Transducers*. Chapter 4: Radiation Impedance.
- Kolbrek, K. (2019). "Horn Modelling with the Transfer Matrix Method - Part 1: Radiation Impedance".

## Output Files

After extraction, place these files in `planning/reference_data/outputs/TC-P1-RAD-01/`:

- `impedance_data.csv` - Raw Hornresp impedance export
- `hornresp_screenshot.png` - Screenshot of impedance curve
- `extraction_log.txt` - Notes on extraction process and any issues
- `validation_results.json` - Final comparison with theoretical values

---

*Created: 2025-12-24*
*Test Case: TC-P1-RAD-01*
*Phase: 1 - Radiation Impedance*
