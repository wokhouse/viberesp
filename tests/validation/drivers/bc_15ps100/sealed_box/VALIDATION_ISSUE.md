# BC_15PS100 Sealed Box Validation Results

## Parser Verification ✅

The Hornresp parser is **working correctly**. After regenerating the sim.txt file:
- Impedance peak correctly at 59.76 Hz (56.04 Ω) - matches expected Fc
- Parser correctly reading all 16 columns
- Validation checks pass

## Current Status

The validation tests confirm the **same systematic error** as BC_8NDL51:
- Mechanical impedance ~40% too high
- Velocity ~27% too low
- SPL ~12 dB too low

This is the **known issue** documented in `sealed_box_spl_investigation.md`.

## Detailed Comparison @ 60 Hz

```
Hornresp (reference):
  Ze: 56.0 Ω @ 7.3°
  Velocity: 0.171 m/s
  SPL: 103.4 dB
  Current: 0.0505 A

Viberesp (current):
  Ze: 73.5 Ω @ -5.0°
  Velocity: 0.124 m/s
  SPL: 91.5 dB
  Current: 0.0385 A

Error:
  Ze: +31.2% (17.5 Ω too high)
  Velocity: -27.5% (0.047 m/s too low)
  SPL: -11.9 dB
```

## Root Cause (from investigation)

Mechanical impedance is too high:
- **Current Z_mech**: 5.44 N·s/m
- **Required Z_mech**: ~3.9 N·s/m (to match Hornresp velocity)
- **Error**: +40%

This affects both BC_8NDL51 and BC_15PS100 similarly (systematic, not random error).

## What's Working ✅

1. **Parser**: Correctly reading all columns from sim.txt
2. **Complex current model**: Using F = BL × I_complex correctly
3. **System parameters**: Fc = 59.7 Hz, Qtc = 0.707 (accurate)
4. **Phase validation**: Passes within tolerance
5. **Test infrastructure**: Robust with validation checks

## What Needs Investigation ❌

The **mechanical impedance model** in `sealed_box.py`:
- We use `driver.M_ms` (with 2× radiation mass) for sealed boxes
- But this gives ~40% higher impedance than Hornresp expects
- Possible causes:
  - Frequency-dependent radiation mass
  - Box damping (Q_b) not included
  - Different compliance model
  - Hornresp uses a different algorithm

## Next Steps

1. ✅ Parser verified - no issues here
2. ✅ Test infrastructure working correctly
3. ⏳ Research agent investigating mechanical impedance formula
4. ⏳ Implement fix based on research findings

## Test Results

```
test_electrical_impedance_magnitude: FAILED
  Max error: 32.99% @ 58.9 Hz
  RMS error: 1.70 Ω
  Expected tolerance: <10%
  Status: Known issue - mechanical impedance model

test_electrical_impedance_phase: PASSED ✓
  Phase correctly matches Hornresp

test_spl: FAILED
  Max error: ~12 dB
  Due to velocity error from mechanical impedance
```

---
Generated: 2025-12-27
Updated: Parser verified, awaiting mechanical impedance research
