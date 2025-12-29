# Ported Box SPL Validation - BC_15DS115

**Date:** 2025-12-28
**Driver:** BC_15DS115-8
**Design:** 400L @ 20Hz (155.1cm² × 22.9cm port)
**Reference:** Hornresp simulation

---

## Executive Summary

Validation against Hornresp revealed a **critical bug in the vented box transfer function numerator**. The current implementation uses `s⁴T_B²T_S²` as the numerator, which is **incorrect for ported boxes**.

**Impact:**
- Mean absolute error: **4.38 dB**
- Maximum error: **9.41 dB** at 20 Hz
- Bass response shape is **fundamentally wrong**

**Root Cause:** Missing port resonance term in transfer function numerator

---

## Validation Results

### Frequency-by-Frequency Comparison

| Freq (Hz) | Hornresp (dB) | Viberesp (dB) | Error (dB) | Status |
|-----------|---------------|---------------|------------|--------|
| 20.15     | 92.81         | 83.40         | **-9.41**  | ✗ Poor |
| 30.08     | 84.87         | 91.74         | **+6.87**  | ✗ Poor |
| 40.04     | 85.36         | 91.44         | **+6.08**  | ✗ Poor |
| 50.00     | 87.82         | 91.75         | +3.93      | ~ Fair |
| 60.00     | 89.32         | 92.30         | +2.98      | ✓ Good |
| 80.00     | 90.10         | 93.33         | +3.23      | ~ Fair |
| 100.00    | 91.99         | 94.01         | +2.02      | ✓ Good |
| 150.00    | 95.82         | 94.43         | -1.39      | ✓ Good |
| 200.00    | 97.26         | 93.77         | -3.49      | ~ Fair |

**Summary:**
- Mean absolute error: **4.38 dB**
- Maximum error: **9.41 dB** (at tuning frequency)
- Bias: **+1.20 dB** (viberesp runs hot overall)

---

## Response Shape Analysis

### Hornresp Response (Correct)
```
20 Hz:  92.8 dB  ← PEAK at tuning frequency
30 Hz:  84.9 dB  ← DIP
40 Hz:  85.4 dB
100 Hz: 92.0 dB
200 Hz: 97.3 dB
```

**Characteristic:** Peak at Fb (20 Hz) → dip → gradual rise
This is the **expected vented box behavior**.

### Viberesp Response (Incorrect)
```
20 Hz:  83.4 dB  ← TOO LOW (should be peak!)
30 Hz:  91.7 dB  ← TOO HIGH
40 Hz:  91.4 dB  ← TOO HIGH
100 Hz: 94.0 dB
200 Hz: 93.8 dB
```

**Characteristic:** Gradual rise from 20-80 Hz, no peak at Fb
This is **wrong for ported boxes**.

---

## Bass Flatness Comparison

| Metric            | Hornresp | Viberesp | Difference |
|-------------------|----------|----------|------------|
| Mean SPL (20-80)  | 88.38 dB | 91.54 dB | +3.16 dB   |
| Std dev (σ)       | 2.75 dB  | 2.00 dB  | -0.75 dB   |

**Observation:** Viberesp predicts flatter bass (lower σ) but at the wrong absolute level and with the wrong shape.

---

## Root Cause Analysis

### Bug Location: `src/viberesp/enclosure/ported_box.py:780`

**Current (INCORRECT) code:**
```python
# Line 780
numerator = (s ** 4) * a4  # s⁴T_B²T_S²
```

This numerator is valid for **sealed boxes** (to ensure G(s) → 1 as s → ∞), but **NOT for ported boxes**.

### Correct Form (from Thiele 1971)

**Literature:** Thiele (1971), Part 1, Section 7 - "System Transfer Function"

The vented box transfer function should be:
```
G(s) = (s² + ωb²/Qtb×s + ωb²) / D(s)
```

Where:
- ωb = 2π × Fb (angular tuning frequency)
- Qtb = Total Q of the box (combined QL, QA, QP)
- D(s) = 4th-order denominator polynomial

In normalized form (using Tb = 1/ωb):
```
G(s) = (s²×Tb² + s×Tb/Qtb + 1) / D(s)
```

**Correct implementation:**
```python
# Port resonance term in numerator (Thiele 1971)
numerator = (s ** 2) * (Tb ** 2) + s * (Tb / QB) + 1
```

### Why This Matters

The port resonance term `s²×Tb² + s×Tb/Qtb + 1` creates the **characteristic peak at the tuning frequency**. Without it:
- No peak at Fb
- Incorrect low-frequency roll-off
- Wrong bass response shape

---

## Parameter Discrepancies

### Qts Mismatch

| Parameter | Hornresp (calc) | Viberesp | Difference |
|-----------|-----------------|----------|------------|
| Qes       | 0.0527          | 0.0631   | +0.0104    |
| Qms       | 1.5869          | 1.9006   | +0.3137    |
| Qts       | **0.0510**      | **0.0611** | **+0.0101** |

**Impact:** The 0.01 Qts difference (20% relative error) contributes to response shape errors but doesn't explain the full 9 dB error at 20 Hz.

### Design Parameters

All other parameters match:
- Fs: 33.0 Hz ✓
- Vas: 253.7 L ✓
- BL: 38.7 T·m ✓
- Re: 4.9 Ω ✓
- Sd: 855 cm² ✓
- Mmd: 64.86 g ✓
- Le: 4.5 mH ✓
- Vb: 400 L ✓
- Fb: 20 Hz ✓
- Port: 155.1 cm² × 22.9 cm ✓

---

## Validation Methodology

### Hornresp Data Source

**File:** `/Users/fungj/vscode/viberesp/imports/ported_sim.txt`

Contains tab-separated simulation results:
- Freq (Hz)
- SPL (dB) - 5th column
- Ze (ohms) - 6th column
- Other acoustic/electrical parameters

### Viberesp Calculation

**Function:** `calculate_spl_ported_transfer_function()`
```python
spl_vb = calculate_spl_ported_transfer_function(
    frequency=freq_hr,
    driver=driver,
    Vb=0.400,
    Fb=20.0,
    voltage=2.83
)
```

### Test Conditions

- Input voltage: 2.83V (1W into 4.9Ω)
- Measurement distance: 1m
- Frequency range: 20-200 Hz
- Reference: Hornresp with identical parameters

---

## Required Fix

### Change Required in `ported_box.py`

**Location:** Lines 778-796

**Current code:**
```python
# Numerator (Small 1973, Eq. 13): N(s) = s⁴T_B²T_S²
# This matches the denominator's leading term to ensure G(s) → 1 as s → ∞
numerator = (s ** 4) * a4
```

**Should be:**
```python
# Numerator (Thiele 1971, Eq. 7): N(s) = s²T_B² + sT_B/Q_B + 1
# This includes the port resonance term, creating the characteristic peak at Fb
numerator = (s ** 2) * (Tb ** 2) + s * (Tb / QB) + 1
```

### Expected Improvement

After fixing the numerator:
- Response should show **peak at Fb (20 Hz)**
- Error at 20 Hz should reduce from **-9.41 dB → <±1 dB**
- Bass shape should match Hornresp within **±2 dB**
- Mean absolute error should improve from **4.38 dB → <2 dB**

---

## References

1. **Thiele (1971)** - "Loudspeakers in Vented Boxes", Part 1, Section 7
   - File: `literature/thiele_small/thiele_1971_vented_boxes.md`
   - Equation: G(s) = (s² + ωb²/Qtb×s + ωb²) / D(s)

2. **Hornresp Simulation Results**
   - File: `/Users/fungj/vscode/viberesp/imports/ported_sim.txt`
   - Parameters: `/Users/fungj/vscode/viberesp/imports/ported_params.txt`

3. **Viberesp Implementation**
   - File: `src/viberesp/enclosure/ported_box.py`
   - Function: `calculate_spl_ported_transfer_function()` (line 618)

---

## Status

⚠️ **CRITICAL BUG IDENTIFIED**
- Root cause: Missing port resonance term in transfer function numerator
- Impact: 9 dB error at tuning frequency, wrong bass shape
- Fix: Change numerator from `s⁴T_B²T_S²` to `s²T_B² + sT_B/Q_B + 1`
- Priority: HIGH - affects all ported box simulations

---

**Generated:** 2025-12-28
**Author:** Claude Code validation
**Next Steps:** Implement numerator fix and re-validate
