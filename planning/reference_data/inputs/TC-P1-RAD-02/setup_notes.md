# TC-P1-RAD-02: Hornresp Setup Notes

## Test Case Overview

**ID**: TC-P1-RAD-02
**Name**: Transition Region (ka ≈ 1)
**Purpose**: Verify radiation impedance behavior in transition region where neither mass nor resistance dominates

## Target Parameters

- Mouth area: 1257 cm² (20 cm radius)
- Test frequency: 275 Hz
- Expected ka: 1.0
- Expected R_norm: 0.42
- Expected X_norm: 0.65

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
3. Set frequency range: 100 Hz to 500 Hz (focus on ka ≈ 1 region)
4. Set number of points: 401 (1 Hz resolution)
5. Click **Calculate** to generate impedance curve
6. Click **Save** to export impedance data

### Step 3: Extract Throat Impedance

From the impedance export, extract values at **275 Hz**:
- Normalized resistance: R_norm
- Normalized reactance: X_norm

### Step 4: Compare with Theoretical Values

At 275 Hz (ka = 1.0):
- Theoretical R_norm ≈ 0.42
- Theoretical X_norm ≈ 0.65
- Both R and X are significant (transition region)

Calculate percentage error:
```
error_R = |R_extracted - 0.42| / 0.42 × 100%
error_X = |X_extracted - 0.65| / 0.65 × 100%
```

Acceptable tolerance: ±10% (transition region values are approximate)

## Validation Checklist

- [ ] Hornresp parameters loaded correctly
- [ ] Impedance data exported for frequency range 100-500 Hz
- [ ] Throat impedance extracted at 275 Hz
- [ ] R_norm within ±10% of 0.42
- [ ] X_norm within ±10% of 0.65
- [ ] Transition behavior verified (R and X comparable)

## Notes

**Transition Region Behavior:**
- At ka ≈ 1, radiation impedance transitions from mass-controlled to radiation-controlled
- Both R and X contribute significantly
- Complex impedance behavior
- This is where the radiation loading changes character

**Comparison with TC-P1-RAD-01:**
- TC-P1-RAD-01 (ka=0.18): X >> R (mass-controlled, X/R ≈ 9.3)
- TC-P1-RAD-02 (ka=1.0): X ≈ R (transition, X/R ≈ 1.5)
- Shows progression toward high frequency behavior

---

*Created: 2025-12-25*
*Test Case: TC-P1-RAD-02*
*Phase: 1 - Radiation Impedance*
