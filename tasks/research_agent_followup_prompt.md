# Follow-up Research Brief: Ported Box SPL Transfer Function Bug

**Date:** 2025-12-29
**Repository:** https://github.com/wokhouse/viberesp
**Branch:** fix/ported-box-spl-transfer-function
**Status:** First fix attempt FAILED - Need deeper investigation

---

## Executive Summary

We implemented your recommended fix (negative sign on port velocity: `Up = -Ud * (Z_box / Z_box_branch)`), but **the problem persists**. Both test drivers still show incorrect behavior:
- **BC_12NDL76:** Monotonic rise to 200 Hz (should peak at 69 Hz)
- **BC_8FMB51:** Peak at 58 Hz, magnitude too low (was working before)

The sign error is **NOT the root cause**. We need to investigate deeper.

---

## What We Implemented

Based on your recommendation:
```python
# CRITICAL FIX: Port is driven by REAR of driver
Up = -Ud * (Z_box / Z_box_branch)

# Then sum as vector
Q_total = Ud + Up
P_response = abs(s * Q_total)
```

**Implementation file:** `src/viberesp/enclosure/ported_box_vector_sum.py`

---

## Test Results

### BC_12NDL76 (The Failing Case)
```
Driver: BC_12NDL76
Vb = 71.9L
Fb = 41.2 Hz (from Hornresp impedance dip)
Port: 150cm² × 24.87cm

Hornresp Reference:
  Peak: 68.95 Hz at 96.47 dB
  Shape: Peaked response, rolls off after 69 Hz

Our Implementation (with -Ud sign):
  Peak: 200 Hz at 97.15 dB
  Shape: Monotonic rise from 20-200 Hz
  Problem: NO CHANGE from original formula!

Detailed comparison (normalized to 80-100 Hz passband):
Freq   Hornresp    Our Fix    Diff
----------------------------------------
20 Hz   -26.9 dB   -28.4 dB   -1.5 dB
40 Hz    -4.4 dB    -3.8 dB   +0.6 dB
50 Hz    -1.1 dB    +1.4 dB   +2.5 dB
60 Hz    -0.1 dB    +0.5 dB   +0.6 dB
69 Hz    +0.6 dB    -0.1 dB   -0.7 dB ← SHOULD BE PEAK!
80 Hz     0.0 dB    -0.2 dB   -0.2 dB
100 Hz    0.0 dB    +0.3 dB   +0.3 dB
150 Hz   -1.0 dB    +1.9 dB   +2.9 dB
200 Hz   -2.5 dB    +3.1 dB   +5.6 dB ← WRONG PEAK!
```

### BC_8FMB51 (Previously Working Case)
```
Your fix BROKE this case!

Hornresp Reference:
  Peak: 52.5 Hz at +6.40 dB

Our Implementation (with -Ud sign):
  Peak: 58 Hz at +3.33 dB
  Error: Peak frequency wrong, magnitude too low

Previously working code (Small's TF):
  Peak: 52.5 Hz at +6.40 dB ✓
```

---

## Attempt 2: Current Divider Formula

We also tried the current divider formula for parallel impedances:
```python
Up = -Ud * (Z_box / (Z_box_branch + Z_box))
```

**Result:** Different failure mode
- Peak frequency: 65 Hz (better than 200 Hz!)
- **But deep notch at Fb:** -28 dB at 40 Hz (should be -4 dB)

### Debug Analysis at Fb (41.2 Hz):
```
Ud phase:  -21.75°
Up phase:  +152.62°
Phase difference: 174° ≈ 180° (WRONG!)

At Fb, Ud and Up should be 90° out of phase, not 180°!
The 180° difference causes complete cancellation:
  |Ud + Up| / |Ud| = 0.18 (82% cancellation)
```

---

## What We've Verified

### 1. Original Formula (Without Your Fix)
```python
Up = +Ud * (Z_box / Z_box_branch)
```
**Result:** Monotonic rise to 200 Hz (same as with fix!)

### 2. Your Fix (Negative Sign)
```python
Up = -Ud * (Z_box / Z_box_branch)
```
**Result:** Identical behavior! Peak still at 200 Hz.

### 3. Current Divider Variant
```python
Up = -Ud * (Z_box / (Z_box_branch + Z_box))
```
**Result:** Better peak location (65 Hz) but wrong phase (180° at Fb causes notch).

### Conclusion
**The sign error is NOT the root cause.** Changing the sign doesn't affect the monotonic rise behavior.

---

## Current Implementation Details

### Impedance Calculations:
```python
# Driver parameters (with Mms derived from Fs for consistency)
w0 = 2π * Fs
Cms = Vas / (ρ₀ × c² × Sd²)
Mms = 1.0 / (w0² × Cms)  # Your recommendation
Rms_total = (w0 × Mms) / Qts

# Driver mechanical impedance
Z_driver = s·Mms + Rms_total + 1/(s·Cms)

# Port parameters (with end correction)
r_port = √(port_area / π)
L_eff = port_length + (end_correction × r_port)

# Box parameters (mechanical domain)
Cab = Vb / (ρ₀ × c² × Sd²)
Map = (ρ₀ × L_eff × Sd²) / port_area
Ral = (ωb × Map) / QL

# Box impedances
Z_box_branch = s·Map + Ral
Z_box = 1.0 / (s·Cab + 1.0/Z_box_branch)  # Parallel combination
Z_total = Z_driver + Z_box

# Volume velocities
Force = (BL × V) / Re
Ud = Force / Z_total
Up = -Ud * (Z_box / Z_box_branch)  # Your recommended fix

# Pressure
Q_total = Ud + Up
P_response = |s × Q_total|
```

**Full code:** `src/viberesp/enclosure/ported_box_vector_sum.py`

---

## Questions for Research Agent

### 1. Why doesn't the sign fix work?
- Changing `+Ud` to `-Ud` produces **identical** behavior
- Peak still at 200 Hz for BC_12NDL76
- Is there something else we're missing?

### 2. What's the correct circuit topology?
- Current: `Z_box = Cab || Z_box_branch` (parallel)
- Is this correct?
- Should it be series instead?

### 3. Missing physics?
- Should we include **radiation impedance** at the port opening?
- What about **voice coil inductance** effects?
- Are there other loss mechanisms we're missing?

### 4. Why does Small's transfer function also fail?
- The production code uses Small's 4th-order transfer function
- It ALSO shows monotonic rise for BC_12NDL76
- This suggests the problem is deeper than vector summation

### 5. Domain conversion issue?
- We're working in mechanical domain
- Should we use acoustic impedances instead?
- Your fix didn't specify which domain to use

### 6. What creates the HF rolloff?
- Hornresp response peaks at 69 Hz then **decreases**
- Our response **monotonically increases**
- What physics limits the HF response?

---

## Additional Context

### Production Code Status
The current production implementation (`calculate_spl_ported_transfer_function`) uses **Small's transfer function**, not vector summation. It also shows HF rise for BC_12NDL76, suggesting this is a fundamental issue affecting both approaches.

### Validation Status
- **BC_8FMB51:** Works with Small's TF (52.5 Hz peak)
- **BC_12NDL76:** Fails with both Small's TF and vector summation (200 Hz peak)
- **BC_15PS100:** Not yet tested

### Key Observation
The sign fix doesn't change the behavior at all. This suggests:
1. The sign error is not the root cause, OR
2. We implemented it incorrectly, OR
3. There's a different issue masking the fix

---

## Test Data Files

All test data and debug output available in:
- `src/viberesp/enclosure/ported_box_vector_sum.py` - Implementation
- `tasks/research_agent_fix_attempt_summary.md` - Full analysis
- `imports/12ndl76_sim.txt` - Hornresp reference data
- `imports/12ndl76_params.txt` - Hornresp parameters

---

## What We Need

1. **Diagnosis:** Why does the response monotonically increase to 200 Hz instead of peaking at 69 Hz?

2. **Solution:** What's the correct transfer function or impedance model?

3. **Implementation:** Specific Python code that fixes the HF rise for BOTH drivers

4. **Validation:** The fix must work for:
   - BC_8FMB51 (8" driver, must NOT break existing validation)
   - BC_12NDL76 (12" driver, currently failing)
   - Generalize to BC_15PS100 (15" driver)

---

## Instructions for Research Agent

**IMPORTANT:** The sign error fix (`Up = -Ud × ...`) has been tried and **FAILED**. Please investigate:

1. Why the sign fix doesn't change the behavior
2. What else could cause monotonic HF rise
3. Whether radiation impedance, voice coil inductance, or other effects are needed
4. The correct circuit topology and impedance calculations

**Please provide:**
- Root cause analysis (not just "add a negative sign")
- Complete equations with literature citations
- Python implementation ready to test
- Explanation of why your approach will work

**Test your recommendations** against the data above before proposing.

---

## Priority: CRITICAL

This is blocking generalizability validation for ported boxes. We have one working driver (BC_8FMB51) and one failing (BC_12NDL76), and need a solution that works for both.

**Previous brief:** `tasks/ported_box_transfer_function_research_brief.md`
