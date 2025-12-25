# Implementation Notes: Finite Horn Throat Impedance

**Target**: Fix 13 dB RMSE error in case1
**File**: `src/viberesp/enclosures/horns/exponential_horn.py`
**Lines**: 126-140 (throat impedance calculation)

---

## Current Implementation

**Location**: `exponential_horn.py:126-140`

**Current code** (infinite horn approximation):

```python
# Calculate throat resistance
k_term = 4 * k**2 - m**2
resistance = np.zeros_like(frequencies)
above_cutoff = k_term > 0
resistance[above_cutoff] = Z0 * np.sqrt(k_term[above_cutoff]) / (2 * k[above_cutoff])

# Calculate throat reactance
reactance = Z0 * m / (2 * k)

Z_throat = resistance + 1j * reactance
```

**Problems**:
1. Uses infinite horn approximation (no mouth reflections)
2. Missing hyperbolic functions (coth, sinh)
3. No end corrections on horn length
4. Incorrect below-cutoff behavior (purely reactive)

---

## Required Changes

### Change 1: Add Helper Methods

**Location**: Add to `ExponentialHorn` class

```python
def calculate_effective_length(self) -> float:
    """Calculate effective horn length with end corrections.

    End corrections from:
    - Throat: 0.85 × a_throat
    - Mouth: 0.6 × a_mouth

    Returns:
        Effective length in meters
    """
    L_physical = self.horn_length_cm / 100  # cm → m

    # Throat radius
    a_throat = np.sqrt(self.throat_area_cm2 / 10000 / np.pi)

    # Mouth radius
    a_mouth = np.sqrt(self.mouth_area_cm2 / 10000 / np.pi)

    # End corrections
    delta_L = 0.85 * a_throat + 0.6 * a_mouth

    L_eff = L_physical + delta_L

    return L_eff


def calculate_propagation_constant(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate complex propagation constant.

    gamma = sqrt(m²/4 - k²)

    Args:
        frequencies: Frequency array (Hz)

    Returns:
        Complex propagation constant (rad/m)
    """
    omega = 2 * np.pi * frequencies
    c = 343.0
    k = omega / c  # Wavenumber

    m = self._get_or_calculate_flare_rate()

    # Complex propagation constant (must use +0j to ensure complex result)
    gamma = np.sqrt(m**2 / 4 - k**2 + 0j)

    return gamma
```

---

### Change 2: Replace calculate_throat_impedance()

**Location**: `exponential_horn.py:126-140`

**Replace entire method**:

```python
def calculate_throat_impedance(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate finite exponential horn throat impedance.

    Based on Kolbrek's finite horn equation:
    Z_throat = Z_char × coth(γ × L) + Z_mouth / sinh²(γ × L)

    Includes:
    - Finite length effects (hyperbolic functions)
    - Mouth radiation impedance (Beranek circular piston)
    - End corrections on horn length

    Args:
        frequencies: Frequency array (Hz)

    Returns:
        Complex throat impedance (Pa·s/m³)
    """
    rho = 1.184  # air density (kg/m³)
    c = 343.0    # speed of sound (m/s)

    # Characteristic impedance at throat
    S_throat = self.throat_area_cm2 / 10000  # cm² → m²
    Z_char = (rho * c) / S_throat

    # Complex propagation constant
    gamma = self.calculate_propagation_constant(frequencies)

    # Effective horn length with end corrections
    L_eff = self.calculate_effective_length()

    # Hyperbolic functions of gamma × L
    gamma_L = gamma * L_eff
    sinh_gamma_L = np.sinh(gamma_L)
    cosh_gamma_L = np.cosh(gamma_L)

    # Mouth radiation impedance (Beranek circular piston)
    Z_mouth = self.calculate_mouth_radiation_impedance(frequencies)

    # Finite horn throat impedance (complete equation)
    # Note: coth(x) = cosh(x) / sinh(x)
    Z_throat = Z_char * cosh_gamma_L / sinh_gamma_L + Z_mouth / (sinh_gamma_L**2)

    return Z_throat
```

**Key changes**:
1. Uses `coth(γL)` instead of infinite approximation
2. Includes mouth reflection term
3. Uses effective length with end corrections
4. Properly handles complex gamma

---

### Change 3: Simplified Version (For Initial Testing)

If you want to test without mouth radiation first:

```python
def calculate_throat_impedance_simplified(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate finite horn throat impedance (simplified, no mouth radiation).

    This is a simplified version for initial testing.
    Omits the mouth reflection term for simplicity.

    Args:
        frequencies: Frequency array (Hz)

    Returns:
        Complex throat impedance (Pa·s/m³)
    """
    rho = 1.184
    c = 343.0

    S_throat = self.throat_area_cm2 / 10000
    Z_char = (rho * c) / S_throat

    gamma = self.calculate_propagation_constant(frequencies)
    L_eff = self.calculate_effective_length()

    # Simplified finite horn (no mouth reflection)
    # Note: coth(x) = 1/tanh(x)
    Z_throat = Z_char / np.tanh(gamma * L_eff)

    return Z_throat
```

**Expected results**:
- Simplified: 5-7 dB RMSE (vs 13 dB current)
- Complete: 3-5 dB RMSE (with mouth reflection)

---

## Implementation Strategy

### Phase 1: Add Helper Methods

1. Add `calculate_effective_length()`
2. Add `calculate_propagation_constant()`
3. Test these methods independently

**Validation**:
- Check effective length is ~10-20% longer than physical
- Verify gamma is imaginary above cutoff, real below

---

### Phase 2: Implement Simplified Finite Model

1. Implement `calculate_throat_impedance_simplified()`
2. Test against case1 synthetic fixture
3. Verify RMSE drops from 13 → 5-7 dB

**Validation**:
```bash
PYTHONPATH=src pytest tests/validation/test_synthetic_cases.py::test_synthetic_case_validation[case1_straight_horn] -v

# Expected: RMSE ≈ 5-7 dB (vs 13.56 dB current)
```

---

### Phase 3: Implement Complete Model

1. Implement full `calculate_throat_impedance()` with mouth radiation
2. Verify mouth reflection term is included
3. Test again against case1

**Expected**: RMSE drops to 3-5 dB

---

### Phase 4: Validate Complete System

1. Run case2, case3, case4 tests
2. Verify improvements propagate through system
3. Check that finite horn theory helps all cases

**Expected**:
- case2: 9 → 3-5 dB
- case3: 34 → 25-30 dB (still needs chamber fix)
- case4: 35 → 25-30 dB (still needs chamber fix)

---

## Testing Checklist

Before considering implementation complete:

- [ ] `calculate_effective_length()` returns reasonable values (~10-20% longer than physical)
- [ ] `calculate_propagation_constant()` returns:
  - Imaginary values above cutoff (k > m/2)
  - Real values below cutoff (k < m/2)
- [ ] `coth(γL)` oscillates above cutoff (creates ripple)
- [ ] `coth(γL)` → 1 below cutoff (mostly resistive)
- [ ] Mouth reflection term decreases with frequency
- [ ] case1 RMSE < 7 dB (simplified) or < 5 dB (complete)
- [ ] case1 correlation > 0.90
- [ ] Phase response is smooth

---

## Common Pitfalls

### ❌ Pitfall 1: Using coth() Directly

```python
import numpy as np

Z_throat = Z_char * np.coth(gamma * L)  # WRONG - no coth in NumPy
Z_throat = Z_char / np.tanh(gamma * L)  # CORRECT - coth = 1/tanh
```

---

### ❌ Pitfall 2: Real-Only Gamma

```python
gamma = np.sqrt(m**2 / 4 - k**2)  # WRONG - RuntimeWarning for negative values
gamma = np.sqrt(m**2 / 4 - k**2 + 0j)  # CORRECT - Always complex
```

---

### ❌ Pitfall 3: Forgetting End Corrections

```python
Z_throat = Z_char / np.tanh(gamma * L_physical)  # WRONG
Z_throat = Z_char / np.tanh(gamma * L_eff)  # CORRECT - includes end corrections
```

---

### ❌ Pitfall 4: Mixing Throat and Mouth Areas

```python
Z_char = (rho * c) / S_mouth  # WRONG - should be throat
Z_char = (rho * c) / S_throat  # CORRECT - characteristic at throat
```

---

## Validation Against case1

**case1 parameters**:
```
Throat area: 600 cm²
Mouth area: 4800 cm²
Horn length: 200 cm
Flare rate: 4.0 /m
Cutoff: 35 Hz
```

**Expected behavior**:
- Below 35 Hz: Finite horn has real impedance (can transmit)
- 35-100 Hz: Transition region with ripple
- Above 100 Hz: Approaches characteristic impedance

**Validation test**:

```bash
# Run validation
PYTHONPATH=src pytest tests/validation/test_synthetic_cases.py::test_synthetic_case_validation[case1_straight_horn] -v

# Check metrics
# Before: RMSE ≈ 13.56 dB, correlation ≈ -0.21
# After (simplified): RMSE ≈ 5-7 dB, correlation > 0.90
# After (complete): RMSE ≈ 3-5 dB, correlation > 0.95
```

---

## Expected Impact on Baseline Metrics

After implementing these changes, update baselines:

**case1** (straight horn):
- Current RMSE: 13.56 dB
- Target RMSE (simplified): 5-7 dB
- Target RMSE (complete): 3-5 dB
- Expected improvement: ~8-10 dB

When metrics improve, regenerate baselines:

```bash
PYTHONPATH=src python3 tools/generate_baselines.py
```

---

## Code Review Checklist

When reviewing the implementation:

- [ ] `calculate_effective_length()` includes throat and mouth end corrections
- [ ] `calculate_propagation_constant()` returns complex values
- [ ] `calculate_throat_impedance()` uses `coth(γL)` not infinite approximation
- [ ] Mouth reflection term included (for complete version)
- [ ] Units are consistent (SI: m, m², kg/m³, m/s)
- [ ] No RuntimeWarnings for negative sqrt arguments
- [ ] Impedance is complex (not just resistance or reactance)

---

## References

1. **Kolbrek Horn Theory** - Finite horn derivation
2. **throat_impedance.md** - Detailed equations and implementation
3. **mouth_reflections.md** - Mouth reflection physics
4. **Hornresp validation** - Reference for comparison

---

## Next Steps

1. ✅ Add helper methods
2. ✅ Implement simplified finite model
3. ✅ Implement complete finite model
4. ⏳ Run validation tests
5. ⏳ Update baselines
6. ⏳ Document in code
7. ⏳ Move to Priority 3 (rear chamber coupling)
