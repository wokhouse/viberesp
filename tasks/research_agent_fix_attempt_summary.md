# Research Agent Fix Attempt Summary

**Date:** 2025-12-29
**Status:** Incomplete - Fix did not resolve the HF rise bug

---

## Executive Summary

The research agent diagnosed the ported box SPL bug as a **sign error** in the port volume velocity calculation: the port should be driven by `-Ud` (rear wave) instead of `+Ud` (front wave). I implemented the vector summation approach with this fix, but **the problem persists** - both BC_8FMB51 and BC_12NDL76 still show incorrect behavior.

---

## Problem Statement

### Current State (Before Fix)
- **Small's transfer function** (`calculate_spl_ported_transfer_function`): Shows monotonic HF rise for BC_12NDL76
- **BC_8FMB51**: "Works" (passes validation)
- **BC_12NDL76**: Fails with monotonic rise to 200 Hz (should peak at 69 Hz)

### Research Agent Diagnosis
> "The root cause is a **polarity error** in the calculation of the port volume velocity ($U_p$)."

**Agent's Fix:**
```python
Up = -Ud * (Z_box / Z_box_branch)  # Add negative sign
```

**Agent's Explanation:**
- Without negative sign: Port and driver sum in-phase below resonance (wrong)
- With negative sign: Port and driver cancel below resonance (correct)
- This fixes the HF rise and creates proper peak-rolloff behavior

---

## Implementation Attempts

### Attempt 1: Original Formula with Negative Sign
**Code:**
```python
Up = -Ud * (Z_box / Z_box_branch)
```

**Result:** FAILED
- BC_12NDL76: Peak at 200 Hz (monotonic rise persists)
- BC_8FMB51: Peak at 58 Hz (target: 52.5 Hz), magnitude too low

### Attempt 2: Current Divider Formula
**Code:**
```python
Up = -Ud * (Z_box / (Z_box_branch + Z_box))
```

**Rationale:** For parallel impedances, current divider formula is `I_branch = I_total × Z_other / (Z_branch + Z_other)`

**Result:** FAILED (different way)
- BC_12NDL76: Peak at 65 Hz (better! but...)
- **Deep notch at Fb (40 Hz):** -28 dB instead of expected -4 dB
- Phase analysis showed Ud and Up canceling (180° out of phase) at Fb
- This is wrong - at Fb they should be 90° out of phase

---

## Debug Analysis

### At Fb (41.2 Hz) with Current Divider Formula:
```
Cancellation ratio |Ud + Up| / |Ud|: 0.18
This means 82% cancellation (-15 dB notch)

Ud phase:  -21.75°
Up phase:  +152.62°
Phase diff: 174.37° ≈ 180° (WRONG! Should be 90°)
```

### Conclusion from Debug:
The current divider formula creates **180° phase difference** at Fb, causing complete cancellation. This is incorrect physics - at Fb, the port and driver should be **90° out of phase**, not 180°.

---

## Key Insight

Both formulas (with or without current divider correction) produce wrong results:

| Formula | Peak Frequency | Peak Shape | Issue |
|---------|---------------|------------|-------|
| `Up = Ud × Z_box / Z_box_branch` (original) | 200 Hz | Monotonic rise | HF rise bug |
| `Up = -Ud × Z_box / Z_box_branch` (agent fix) | 200 Hz | Monotonic rise | No change! |
| `Up = -Ud × Z_box / (Z_box_branch + Z_box)` (current divider) | 65 Hz | Notch at Fb | Wrong phase |

**The sign error is NOT the root cause.**

---

## What's Actually Wrong

Looking at the data:
1. **BC_12NDL76 Hornresp:** Peaks at 69 Hz, then rolls off
2. **BC_12NDL76 Viberesp (both formulas):** Monotonically increases to 200 Hz
3. The negative sign alone doesn't fix this
4. The impedance calculation might be fundamentally wrong

### Possible Issues:
1. **Box impedance calculation** might be wrong
2. **Missing radiation impedance** at port opening
3. **Wrong circuit topology** (series vs parallel)
4. **Domain conversion issue** (acoustic vs mechanical)
5. **Calibration/normalization issue**

---

## Files Created

- `/Users/fungj/vscode/viberesp/src/viberesp/enclosure/ported_box_vector_sum.py`
  - New implementation with vector summation
  - Includes both corrected sign attempts
  - Currently uses: `Up = -Ud * (Z_box / Z_box_branch)` (agent's recommendation)

---

## Test Results

### BC_12NDL76 (Failing Case)
```
Target (Hornresp): Peak at 68.95 Hz, +0.56 dB
Original formula: Peak at 200 Hz, +3.07 dB (monotonic rise)
Agent's fix (-Ud): Peak at 200 Hz, +3.07 dB (NO CHANGE!)
Current divider: Peak at 65 Hz, +8.05 dB (better location, wrong shape)
```

### BC_8FMB51 (Working Case)
```
Target (Hornresp): Peak at 52.5 Hz, +6.40 dB
Agent's fix: Peak at 58 Hz, +3.33 dB (BROKEN!)
```

**The fix breaks BC_8FMB51 while not fixing BC_12NDL76.**

---

## Recommendation

The research agent's diagnosis (sign error) **does not solve the problem**. The issue is deeper than just a missing negative sign. We need to:

1. **Verify the impedance circuit topology** is correct
2. **Check if radiation impedance** is needed at the port
3. **Compare with Hornresp source code** or detailed derivation
4. **Consider using Small's transfer function** instead of vector summation (it's already validated for most cases)

The current Small's transfer function implementation (`calculate_spl_ported_transfer_function`) also shows HF rise for BC_12NDL76, so this is a **fundamental issue** affecting both approaches.

---

## Next Steps

1. **Revert to Small's transfer function** - it's more authoritative than vector summation
2. **Investigate why Small's TF fails** for BC_12NDL76 specifically
3. **Check if there's a driver-specific issue** (parameter inconsistency, etc.)
4. **Consider that the bug might be in calibration/HF rolloff**, not the core transfer function

---

## References

- Research brief: `tasks/ported_box_transfer_function_research_brief.md`
- New implementation: `src/viberesp/enclosure/ported_box_vector_sum.py`
- Test script: `tasks/test_ported_vector_sum_tf.py` (updated with sign fix)
