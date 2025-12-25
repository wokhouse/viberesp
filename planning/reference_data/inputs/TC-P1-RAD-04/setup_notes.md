# TC-P1-RAD-04: Hornresp Setup Notes

## Test Case Overview

**ID**: TC-P1-RAD-04
**Name**: Small Piston Scaling
**Purpose**: Verify area scaling relationship with different piston size

## Target Parameters

- Mouth area: 50 cm² (4 cm radius)
- Test frequency: 50 Hz
- Expected ka: 0.036
- Expected R_norm: 0.00066
- Expected X_norm: 0.0308
- Expected full impedance: Z_rad ≈ 54 + j2525 Pa·s/m³

## Hornresp Configuration

Same as TC-P1-RAD-01 but with smaller area:
- Straight duct with S1=S2=50 cm² (instead of 1257 cm²)
- Half-space radiation (Ang = 0.5 × Pi)
- Idealized driver parameters (Sd = 50 cm² to match)

## Key Comparison with TC-P1-RAD-01

| Parameter | TC-P1-RAD-01 | TC-P1-RAD-04 | Ratio |
|-----------|--------------|--------------|-------|
| Area | 1257 cm² | 50 cm² | 25.1x |
| Radius | 20 cm | 4 cm | 5x |
| ka @ 50 Hz | 0.18 | 0.036 | 5x |
| Z_char | 3260 Pa·s/m³ | 82200 Pa·s/m³ | 25.2x |
| \|Z_rad\| | 501 Pa·s/m³ | 2526 Pa·s/m³ | 5x |

**Important:** Normalized impedance should match theoretical values regardless of area. The full impedance scales with 1/Area.

## Data Extraction Procedure

### Step 1: Import into Hornresp

1. Open Hornresp application
2. File → Open → Select `hornresp_params.txt`
3. Verify S1=S2=50 cm² (not 1257 cm²)
4. Verify Sd=50 cm² in driver parameters

### Step 2: Generate Impedance Data

1. Go to **Tools** → **Loudspeaker Driver**
2. Select **Electrical Impedance** tab
3. Set frequency range: 20 Hz to 200 Hz
4. Set number of points: 181 (1 Hz resolution)
5. Click **Calculate** to generate impedance curve
6. Click **Save** to export impedance data

### Step 3: Extract Throat Impedance

From the impedance export, extract values at **50 Hz**:
- Normalized resistance: R_norm
- Normalized reactance: X_norm

### Step 4: Compare with Theoretical Values

At 50 Hz (ka = 0.036):
- Theoretical R_norm ≈ 0.00066
- Theoretical X_norm ≈ 0.0308

Calculate percentage error:
```
error_R = |R_extracted - 0.00066| / 0.00066 × 100%
error_X = |X_extracted - 0.0308| / 0.0308 × 100%
```

Acceptable tolerance: ±5%

## Validation Checklist

- [ ] Hornresp parameters loaded correctly with S1=S2=50 cm²
- [ ] Impedance data exported for frequency range 20-200 Hz
- [ ] Throat impedance extracted at 50 Hz
- [ ] Normalized impedance matches theory (±5%)
- [ ] Area scaling verified: Z_char ≈ 25x larger than TC-P1-RAD-01

## Notes

**Purpose of This Test Case:**

1. **Verify area scaling**: Z_char = ρ₀c/S should scale inversely with area
2. **Same ka, different size**: By keeping ka constant, we verify normalized impedance is independent of absolute size
3. **Characteristic impedance**: Smaller area → larger Z_char → larger full impedance

**Comparison Notes:**

- TC-P1-RAD-01: Large piston (1257 cm²) at 50 Hz → ka=0.18
- TC-P1-RAD-04: Small piston (50 cm²) at 50 Hz → ka=0.036

Different ka due to radius difference, but both are in mass-controlled region (ka << 1).

---

*Created: 2025-12-25*
*Test Case: TC-P1-RAD-04*
*Phase: 1 - Radiation Impedance*
