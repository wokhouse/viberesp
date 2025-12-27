# BC_8NDL51 Ported Box Validation Summary

**Driver:** B&C 8NDL51-8 8" Midrange Driver
**Alignment:** Butterworth B4 (maximally flat response)

## Test Cases

This directory contains 2 validation cases for ported (vented) box simulation,
each targeting the same B4 Butterworth alignment with different port diameters.

### Driver Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Fs | 75.0 Hz | Datasheet (calculated with radiation mass) |
| Qts | 0.616 | Datasheet |
| Vas | 10.1 L | Datasheet |
| Sd | 220 cm² | Datasheet |
| Re | 2.6 Ω | Datasheet |
| X_max | 7 mm | Datasheet |

### B4 Alignment Parameters

| Parameter | Value | Formula |
|-----------|-------|---------|
| Target Qtc | 0.707 | Butterworth alignment |
| α (compliance ratio) | 0.319 | (Qtc/Qts)² - 1 |
| Vb (box volume) | 31.65 L | Vas / α |
| h (tuning ratio) | 0.871 | 1/√(1+α) |
| Fb (tuning frequency) | 65.3 Hz | h × Fs |
| F3 (-3dB frequency) | 65.3 Hz | Fb (for B4) |

## Validation Cases

### Case 1: 2.5" Port

**Directory:** `vb31.6L_fb65Hz_b4_2.5in_port/`

| Parameter | Value |
|-----------|-------|
| Port diameter | 2.5 inch (6.35 cm) |
| Port area | 31.67 cm² |
| Port length | 4.29 cm |
| Hornresp file | `BC_8NDL51_ported_2.5in.txt` |

**Characteristics:**
- Compact port size
- Moderate port velocity (~17 m/s at max excursion)
- Suitable for lower power applications

### Case 2: 3" Port

**Directory:** `vb31.6L_fb65Hz_b4_3in_port/`

| Parameter | Value |
|-----------|-------|
| Port diameter | 3.0 inch (7.62 cm) |
| Port area | 45.60 cm² |
| Port length | 6.83 cm |
| Hornresp file | `BC_8NDL51_ported_3in.txt` |

**Characteristics:**
- Larger port area (44% larger than 2.5")
- Lower port velocity (~12 m/s at max excursion)
- Better power handling and reduced chuffing risk
- Requires longer port for same tuning

## Comparison

| Metric | 2.5" Port | 3" Port | Advantage |
|--------|-----------|---------|-----------|
| Port area | 31.67 cm² | 45.60 cm² | 3" |
| Port length | 4.29 cm | 6.83 cm | 2.5" (shorter) |
| Port velocity | ~17 m/s | ~12 m/s | 3" (lower) |
| Chuffing risk | Moderate | Low | 3" |
| Box fit | Easier | Tighter | 2.5" |

Both cases target identical system parameters (Vb, Fb, α, h) - only port
dimensions differ. This allows validation that viberesp correctly calculates
port length vs area relationship for the Helmholtz tuning.

## Running Simulations

For each case:

1. Open Hornresp
2. Load the `.txt` file in the case directory
3. Run simulation (Tools → Loudspeaker Wizard → Calculate)
4. Save results as `sim.txt` in the same directory
5. Compare with viberesp:
   ```bash
   viberesp validate compare BC_8NDL51 ported/Vb31.6L_Fb65.3Hz_Xin
   ```

## Expected Results

**Impedance:**
- Dual impedance peaks (driver resonance + Helmholtz resonance)
- Lower peak: ~45-50 Hz (≈0.7 × Fb)
- Dip at Fb: ~65.3 Hz (impedance ≈ Re)
- Upper peak: ~90-95 Hz (≈1.4 × Fb)

**Frequency Response:**
- F3 = 65.3 Hz (-3dB point)
- Maximally flat response in passband (B4 characteristic)
- 4th-order high-pass slope (24 dB/octave)

**Validation Tolerances:**
- Fb: ±0.5 Hz
- Vb: ±0.5 L
- Port length: ±0.5 cm
- Ze magnitude: <5% general, <10% near peaks
- Ze phase: <10° general, <15° near peaks

## Literature References

- Thiele (1971) - "Loudspeakers in Vented Boxes" Parts 1 & 2
  - Part 1, Section 2: Helmholtz resonator theory
  - Part 2, Table 1: Alignment constants (B4 values)
- Small (1972) - Closed-Box Loudspeaker Systems Part I
  - Compliance ratio α = Vas/Vb
  - System Qtc calculations
- `literature/thiele_small/thiele_1971_vented_boxes.md`

## Status

| Case | Hornresp File | Metadata | Expected Parameters | README | sim.txt |
|------|---------------|----------|---------------------|--------|---------|
| 2.5" port | ✅ | ✅ | ✅ | ✅ | ⏳ (to be generated) |
| 3" port | ✅ | ✅ | ✅ | ✅ | ⏳ (to be generated) |

**Next Steps:**
1. Run Hornresp simulations for both cases
2. Save results as `sim.txt` in each directory
3. Run viberesp validation comparison
4. Document results and any discrepancies
