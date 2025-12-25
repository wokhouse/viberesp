# TC-P1-RAD-03: Hornresp Setup Notes

## Test Case Overview

**ID**: TC-P1-RAD-03
**Name**: High Frequency (ka >> 1)
**Purpose**: Verify high frequency behavior where radiation impedance becomes purely resistive

## Target Parameters

- Mouth area: 1257 cm² (20 cm radius)
- Test frequency: 2000 Hz
- Expected ka: 7.26
- Expected R_norm: 0.97 (approaches 1)
- Expected X_norm: 0.08 (approaches 0)

## Hornresp Configuration

Same as TC-P1-RAD-01:
- Straight duct with S1=S2=1257 cm²
- Half-space radiation (Ang = 0.5 × Pi)
- Idealized driver parameters

## Data Extraction Procedure

### Step 1: Import into Hornresp

1. Open Hornresp application
2. File → Open → Select `hornresp_params.txt`
3. Verify all parameters loaded correctly

### Step 2: Generate Impedance Data

1. Go to **Tools** → **Loudspeaker Driver**
2. Select **Electrical Impedance** tab
3. Set frequency range: 500 Hz to 5000 Hz (focus on high frequency)
4. Set number of points: 901 (5 Hz resolution)
5. Click **Calculate** to generate impedance curve
6. Click **Save** to export impedance data

### Step 3: Extract Throat Impedance

From the impedance export, extract values at **2000 Hz**:
- Normalized resistance: R_norm
- Normalized reactance: X_norm

### Step 4: Compare with Theoretical Values

At 2000 Hz (ka = 7.26):
- Theoretical R_norm ≈ 0.97 (should approach 1)
- Theoretical X_norm ≈ 0.08 (should approach 0)
- Radiation is nearly purely resistive

Calculate percentage error:
```
error_R = |R_extracted - 0.97| / 0.97 × 100%
error_X = |X_extracted - 0.08| / 0.08 × 100%
```

Acceptable tolerance: ±10% (R), ±20% (X - small values have larger relative error)

## Validation Checklist

- [ ] Hornresp parameters loaded correctly
- [ ] Impedance data exported for frequency range 500-5000 Hz
- [ ] Throat impedance extracted at 2000 Hz
- [ ] R_norm > 0.9 (approaches 1)
- [ ] X_norm < 0.2 (approaches 0)
- [ ] Radiation-controlled behavior verified

## Notes

**High Frequency Behavior:**
- At ka >> 1, radiation impedance becomes purely resistive
- R approaches 1 (matched to characteristic impedance)
- X approaches 0 (no reactive component)
- Near 100% radiation efficiency
- Maximum power transfer to the radiated sound field

**Progression Across Test Cases:**
- TC-P1-RAD-01 (ka=0.18): X >> R (mass-controlled)
- TC-P1-RAD-02 (ka=1.0): X ≈ R (transition)
- TC-P1-RAD-03 (ka=7.26): R >> X (radiation-controlled)

This demonstrates the complete frequency-dependent behavior of radiation impedance.

---

*Created: 2025-12-25*
*Test Case: TC-P1-RAD-03*
*Phase: 1 - Radiation Impedance*
