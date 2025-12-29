# Ported Box Transfer Function Research Summary

**Date:** 2025-12-28
**Research Agent:** Online research (Claude/GPT with web access)
**Status:** ✅ Resolved - Current numerator is correct

---

## Key Findings

### 1. Current Numerator is Mathematically Correct

**Confirmed by Small (1973), Equation 20:**
```
G(s) = s⁴T₀⁴ / (s⁴T₀⁴ + a₁s³T₀³ + a₂s²T₀² + a₃sT₀ + 1)
```

Where T₀ = T_B · T_S (nominal filter time constant)

**Current implementation:** `numerator = s⁴T_B²T_S²` ✅ CORRECT

### 2. Why "Port Resonance Numerator" Failed

The alternative numerator `(s²T_B² + s×T_B/Q_B + 1)` is from **Small's Equation 16** for **voice coil impedance**, NOT SPL:

```
Z_VC(s) = R_E + R_ES · [s(T_S/Q_ES)(s²T_B² + s×T_B/Q_B + 1)] / D'(s)
```

**This explains the test failure:**
- Applied impedance equation to SPL transfer function
- Result: Excessive HF rolloff (G → 1/s² → 0 as s → ∞)
- Error increased from 4.38 dB → 13.54 dB

**Lesson:** The "port resonance numerator" was never meant for SPL calculation.

### 3. Real Issue: Denominator Coefficients

The missing Fb peak is likely caused by **incorrect denominator coefficients**, not the numerator.

**Small (1973), Equations 21-24:**

| Coefficient | Correct Formula |
|-------------|-----------------|
| h (ratio) | f_S/f_B |
| a₁ | (Q_L + h·Q_T) / (h·Q_L·Q_T) |
| a₂ | [h + (α + 1 + h²)·Q_L·Q_T] / (h·Q_L·Q_T) |
| a₃ | (h·Q_L + Q_T) / (h·Q_L·Q_T) |

**Common implementation errors:**
- Confusing Q_T (total Q) with Q_TS (driver total Q)
- Incorrect α (compliance ratio) calculation
- Missing or incorrect Q_L (box losses, typically 5-10)
- Wrong h ratio (should be f_S/f_B, not T_B/T_S)

### 4. Physical Model Considerations

The transfer function G(s) assumes:
1. Both cone and port radiate into the same space
2. Net volume velocity U_cone - U_port determines pressure
3. At f_B, port velocity is maximum and in-phase

**If port radiation is not properly accounted for**, the response near Fb will be incorrect.

---

## Resolution of Code Review Issues

### Issue #2: Documentation Contradiction ✅ RESOLVED

**Research confirms:** Document B (investigation) was correct - the current numerator is correct.

**Document A error:** Claimed "critical bug in numerator" but was confusing:
- Impedance equation (Small Eq. 16) with port resonance terms
- SPL equation (Small Eq. 20) with s⁴ numerator

**Action needed:** Update `ported_box_spl_validation_bc15ds115.md` to:
- Remove claim of "critical bug in numerator"
- Clarify that the tested "port resonance numerator" was from the wrong equation
- Focus on the real issue: denominator coefficients and port radiation

---

## Next Steps for Issue #26 (Missing Fb Peak)

### Priority 1: Verify Denominator Coefficients

Compare current implementation in `ported_box.py` against Small's exact formulas:

```python
# Current implementation (lines ~780-810)
# Needs verification against:

h = f_s / f_b  # Ratio
Q_T = 1 / (1/Q_ES + 1/Q_MS)  # Total Q (not Q_TS!)
Q_L = 7.0  # Box losses (typically 5-10 for vented boxes)
alpha = V_as / V_b  # Compliance ratio

# Small (1973), Eq. 21-24
a1 = (Q_L + h * Q_T) / (h * Q_L * Q_T)
a2 = (h + (alpha + 1 + h**2) * Q_L * Q_T) / (h * Q_L * Q_T)
a3 = (h * Q_L + Q_T) / (h * Q_L * Q_T)
```

### Priority 2: Check Port Radiation Model

Verify that the implementation accounts for:
- Port volume velocity contribution
- Phase relationship between cone and port at f_B
- Net radiation (U_cone - U_port, not just U_cone)

### Priority 3: Validate Against Hornresp

After corrections, re-test BC_15DS115:
- Expect characteristic peak at f_B = 20 Hz
- Verify mean error < 1 dB across 20-200 Hz
- Check that HF asymptotic behavior is preserved

---

## Literature Sources

| Source | Citation | Key Content |
|--------|----------|-------------|
| Small (1973) | "Vented-Box Loudspeaker Systems Part I", JAES Vol. 21 No. 5 | Eq. 20: Transfer function with s⁴ numerator |
| Small (1973) | Same paper | Eq. 16: Voice coil impedance (port resonance term) |
| Small (1973) | Same paper | Eq. 21-24: Denominator coefficients |
| Thiele (1971) | "Loudspeakers in Vented Boxes: Part I", Proc. IREE Australia | Original vented box analysis |
| AndyC (n.d.) | "Algorithms Shared by All Alignment Types", diy-audio-engineering.org | Modern implementation of Small's equations |

---

## Conclusion

**The current PR approach (calibration offset only) is reasonable** given that:
1. The numerator s⁴T_B²T_S² is mathematically correct
2. The real issue is in denominator coefficients (not addressed by changing numerator)
3. Comprehensive fix requires deeper investigation of coefficient calculations

**However, the PR still has the regression issue** (BC_18RBX100 accuracy) identified in the code review.

**Recommended path forward:**
1. Fix the regression issue (driver-specific calibration or revert to +6 dB)
2. Update documentation to remove "critical bug in numerator" claim
3. Create new investigation for denominator coefficients (Issue #26)
4. Implement proper denominator coefficient calculations from Small (1973)
