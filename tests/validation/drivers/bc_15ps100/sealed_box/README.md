# BC_15PS100 Sealed Box Validation

## Driver

- **Model**: BC 15PS100
- **Manufacturer**: B&C Speakers
- **Size**: 15"
- **Thiele-Small Parameters**:
  - F_s: 39.0 Hz
  - Q_ts: 0.43
  - V_as: 103 L
  - S_d: 855 cm²
  - BL: 21.2 T·m
  - R_e: 5.2 Ω
  - M_md: 147 g (driver mass only)
  - C_ms: 1.04E-04 m/N
  - R_ms: 6.53 N·s/m

## Enclosure Design

- **Type**: Sealed box (acoustic suspension)
- **Alignment**: Qtc = 0.707 (Butterworth, maximally flat)
- **Box Volume**: Vb = 67.5 L
- **System Parameters**:
  - α = 1.53 (Vas/Vb)
  - Fc = 59.7 Hz (Fs × √(1+α))
  - Qtc = 0.707 (Qts × √(1+α))
  - F3 = 59.7 Hz

## Hornresp Simulation

### Input File

**File**: `input_qtc0.707.txt`

This file was generated using viberesp's export function to ensure
driver parameters match exactly between viberesp and Hornresp.

### Generating Hornresp Results

1. Open Hornresp
2. File → Import → Select `input_qtc0.707.txt`
3. Run the simulation tool
4. When prompted for angular range, use same as BC_8NDL51: 10-20000 Hz
5. Tool → Save → Export results to .txt file
6. Save as `sim.txt` in this directory

### Expected Results

With correct simulation, you should see:
- System resonance around 60 Hz
- Qtc ≈ 0.707 (maximally flat response)
- Impedance peak at Fc

## Validation

Once `sim.txt` is generated, run:

```bash
pytest tests/validation/test_sealed_box.py -v
```

The test will compare viberesp's calculations against Hornresp for:
- Electrical impedance magnitude and phase
- Diaphragm velocity
- SPL response

## Notes

- This is a larger 15" driver in a larger sealed box (67.5L vs 31.65L for BC_8NDL51)
- Lower resonance frequency (59.7 Hz vs 86.1 Hz) due to larger volume and lower Fs
- Higher Q_ts (0.43 vs 0.37) requires larger box for Butterworth alignment
- Higher BL (21.2 vs 7.3 T·m) provides more force
- Same Qtc=0.707 alignment as BC_8NDL51 but with different driver size
- Excellent test case for validating sealed box theory across different driver sizes
