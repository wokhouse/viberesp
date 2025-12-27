# Ported Box Implementation Fixes

Based on research agent findings from Small (1973).

## Issues to Fix

### 1. Efficiency Formula (Line 664)
**Current (WRONG):**
```python
eta_0 = (air_density / (2 * math.pi * speed_of_sound)) * \
        ((4 * math.pi ** 2 * driver.F_s ** 3 * driver.V_as) / driver.Q_es)
```
Gives η₀ = 3122 (312,255%!)

**Correct (Small 1973, Eq. 25):**
```python
# Efficiency constant: K_ETA = 4π²/c³ ≈ 9.64e-7 s³/m³
K_ETA = (4 * math.pi**2) / (speed_of_sound**3)
eta_0 = K_ETA * (driver.F_s**3 * driver.V_as) / driver.Q_es
```
Should give η₀ ≈ 0.0245 (2.45%)

### 2. SPL Transfer Function Numerator (Line 637-643)
**Current (WRONG):**
```python
numerator_port = (s ** 2) * (Tb ** 2) + s * (Tb / Qp) + 1
```
This gives -39.69 dB at 200 Hz (wrong frequency dependence).

**Correct (Small 1973, Eq. 13):**
```python
# Numerator should be s⁴·Tb²·Ts² (same as denominator's leading term)
numerator = (s ** 4) * (Tb ** 2) * (Ts ** 2)
```
This ensures transfer function approaches 1 (0 dB) at high frequencies.

### 3. Impedance Q Factor (Throughout ported_box_impedance_small)
**Current:** Using Q_ES correctly ✓

**Wait - the code is already using Q_ES!** Let me check if there's another issue...

Actually, looking at the debug output, the ratio N(s)/D'(s) ≈ 0.694 at Fb, not ≈ 0. This suggests:
- Numerator or denominator coefficients are wrong
- Or the motional resistance calculation is wrong

Let me check the impedance numerator more carefully...

## Implementation Plan

1. Fix efficiency formula
2. Fix SPL transfer function numerator
3. Re-validate against Hornresp
4. Create test cases for typical and extreme drivers
