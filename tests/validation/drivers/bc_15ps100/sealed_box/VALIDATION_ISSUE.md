# BC_15PS100 Sealed Box Validation Issue

## Problem Identified

The Hornresp sim.txt file shows **major discrepancies** with viberesp calculations:

### Impedance Comparison @ 60 Hz (Fc)
- **Viberesp**: Ze = 73.51 Ω
- **Hornresp**: Ze = 103.4 Ω
- **Error**: 40% (way beyond acceptable tolerance)

### Displacement Analysis
The Hornresp displacement peaks at **10 Hz** (0.647 mm), which suggests:
1. Hornresp may have simulated a **ported box** instead of sealed box
2. OR the input file parameters were incorrectly exported/imported
3. OR there's a fundamental configuration issue

### Expected vs Actual
- **Expected Fc**: 59.7 Hz (calculated from F_s=37.3 Hz, α=1.56)
- **Hornresp impedance peak**: ~135 Hz (106.8 Ω)
- **Hornresp displacement peak**: 10 Hz (wrong enclosure type?)

## Driver Parameters (Verified)
```
F_s: 37.29 Hz
Q_ts: 0.44
V_as: 105.54 L
M_md: 147 g
C_ms: 1.04E-04 m/N
R_ms: 6.53 N·s/m
BL: 21.2 T·m
Re: 5.2 Ω
```

## Enclosure Parameters (Verified)
```
Vb: 67.5 L
α = V_as/Vb = 1.56
Fc = F_s × √(1+α) = 37.3 × √2.56 = 59.7 Hz ✓
Qtc = Q_ts × √(1+α) = 0.44 × √2.56 = 0.707 ✓
```

## Action Required

**The user needs to regenerate the Hornresp sim.txt file with the following steps:**

1. Open Hornresp fresh
2. File → New (clear any previous configuration)
3. File → Import → Select `input_qtc0.707.txt`
4. **Verify the imported parameters**:
   - Vrc = 67.45 L (sealed box volume)
   - Vtc = 0 (no port, sealed box)
   - Mmd = 147 g
   - Cms = 1.04E-04
   - BL = 21.2
5. Run simulation: 10-20000 Hz
6. **Check the impedance peak** - should be around 60 Hz, not 135 Hz
7. Export to sim.txt

## Test Results (Current Status)

```
test_electrical_impedance_magnitude: FAILED
  Max error: 32.99% @ 58.9 Hz
  RMS error: 1.70 Ω
  Pass: ✗

test_electrical_impedance_phase: PASSED ✓

test_spl: FAILED (likely due to wrong impedance)
```

## Notes

- The phase test passing suggests the **shape** of the impedance curve is correct
- But the magnitude is scaled wrong, pointing to a parameter mismatch
- Most likely: Hornresp simulated wrong enclosure type

---
Generated: 2025-12-27
Status: Awaiting correct Hornresp sim.txt file
