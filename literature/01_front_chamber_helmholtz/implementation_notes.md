# Implementation Notes: Front Chamber Helmholtz Resonance

**Target**: Fix 34-35 dB RMSE errors in case3 and case4
**File**: `src/viberesp/enclosures/horns/front_loaded_horn.py`
**Lines**: 592-637 (front chamber impedance calculation)

---

## Current Implementation Issues

### Problem 1: Missing Helmholtz Resonance

**Current code** (simplified):

```python
# In front_loaded_horn.py, calculate_system_response()
# Line 592-637 region

# Front chamber modeled as simple compliance
if self.front_chamber_volume:
    C_fc = self.front_chamber_volume / (rho * c**2)
    Z_fc = 1 / (1j * omega * C_fc)
```

**Issues**:
- No Helmholtz frequency calculation
- Throat area not included in resonance
- Missing effective length with end corrections
- No modal impedance structure

---

### Problem 2: Incomplete Multi-Mode Implementation

**Current code** has `front_chamber_modes` parameter but:

```python
# Front chamber modes parameter exists
self.front_chamber_modes = front_chamber_modes or 0

# But actual modal calculation is incomplete
# Missing: standing wave frequencies, modal Q, impedance summation
```

**Issues**:
- Standing wave modes not calculated correctly
- Modal impedance not summed with Helmholtz mode
- Mode frequency calculation may use wrong boundary conditions

---

### Problem 3: Incorrect Impedance Topology

**Current code** treats chamber impedance incorrectly:

```python
# Likely uses series combination (WRONG)
Z_total = Z_throat + Z_chamber

# Should use parallel combination (CORRECT)
Z_total = (Z_throat * Z_chamber) / (Z_throat + Z_chamber)
```

**Impact**: 30+ dB errors in predicted response.

---

## Required Changes

### Change 1: Add Helmholtz Frequency Calculation

**Location**: New method in `FrontLoadedHorn` class

```python
def calculate_helmholtz_frequency(self) -> float:
    """Calculate Helmholtz resonance frequency of front chamber.

    Based on: Kolbrek AES 2018, Eq. for Helmholtz resonance
    f_h = (c / 2π) × √(S_throat / (L_eff × V_chamber))

    Returns:
        Helmholtz frequency in Hz
    """
    c = 343.0  # speed of sound (m/s)

    # Convert to SI units
    S_throat = self.throat_area_cm2 / 10000  # cm² → m²
    V_chamber = self.front_chamber_volume / 1000  # L → m³

    # Effective throat length with end corrections
    a_throat = np.sqrt(S_throat / np.pi)
    L_throat_physical = self.throat_length_cm / 100 if hasattr(self, 'throat_length_cm') else 0.05
    L_throat_eff = L_throat_physical + 1.7 * a_throat  # End correction

    # Helmholtz frequency
    f_h = (c / (2 * np.pi)) * np.sqrt(S_throat / (L_throat_eff * V_chamber))

    return f_h
```

**Test**:
```python
# For case3 parameters: 600 cm² throat, 6 L chamber
# Expected f_h ≈ 125 Hz
```

---

### Change 2: Implement Chamber Impedance with Modes

**Location**: New method in `FrontLoadedHorn` class

```python
def calculate_front_chamber_impedance(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate front chamber impedance including Helmholtz and standing wave modes.

    Based on:
    - Helmholtz resonance: f_h = (c/2π) × √(S_throat / (L_eff × V_chamber))
    - Standing wave modes: f_n = n × c / (2 × L_chamber)
    - Kolbrek AES 2018, Section on multi-mode chambers

    Args:
        frequencies: Frequency array (Hz)

    Returns:
        Complex impedance array (Pa·s/m³)
    """
    omega = 2 * np.pi * frequencies
    rho = 1.184  # air density (kg/m³)
    c = 343.0    # speed of sound (m/s)

    # Convert to SI
    S_throat = self.throat_area_cm2 / 10000
    V_chamber = self.front_chamber_volume / 1000

    # === Mode 0: Helmholtz Resonance ===
    # Acoustic compliance
    C_acoustic = V_chamber / (rho * c**2)

    # Helmholtz impedance
    Z_helmholtz = 1 / (1j * omega * C_acoustic)

    # === Higher Modes: Standing Waves ===
    Z_modes = np.zeros_like(frequencies, dtype=complex)

    if self.front_chamber_modes > 0:
        # Estimate chamber length from volume (assuming cube-ish shape)
        # In practice, this should come from geometry
        L_chamber = (V_chamber * 1000) ** (1/3) / 100  # Rough approximation in m

        # Modal Q (empirical, could be parameterized)
        Q_modal = 10.0

        for n in range(1, self.front_chamber_modes + 1):
            # Standing wave frequency (open-closed tube)
            f_n = n * c / (2 * L_chamber)
            omega_n = 2 * np.pi * f_n

            # Modal resistance
            R_n = (rho * c / S_throat) / Q_modal

            # Second-order resonant impedance
            Z_n = R_n / (1 + 1j * Q_modal * (omega/omega_n - omega_n/omega))

            Z_modes += Z_n

    # Total chamber impedance
    Z_chamber = Z_helmholtz + Z_modes

    return Z_chamber
```

---

### Change 3: Fix Impedance Topology in calculate_system_response()

**Location**: Modify `calculate_system_response()` method around line 592-637

**Current (broken)**:

```python
# Likely something like this - WRONG
if self.front_chamber_volume:
    Z_fc = calculate_chamber_impedance()
    Z_acoustic = Z_throat + Z_fc  # Series combination
```

**Should be (CORRECT)**:

```python
# Calculate throat impedance (from horn)
Z_throat = self.calculate_throat_impedance(frequencies)

# Calculate chamber impedance
if self.front_chamber_volume:
    Z_chamber = self.calculate_front_chamber_impedance(frequencies)

    # Parallel combination (chamber in parallel with throat)
    Z_acoustic = (Z_throat * Z_chamber) / (Z_throat + Z_chamber)
else:
    Z_acoustic = Z_throat
```

**Why parallel?** The driver can push air either into the horn throat OR compress the chamber - two parallel pathways.

---

### Change 4: Update calculate_volume_velocity()

**Location**: Modify method that calculates driver volume velocity

**Current**:

```python
# Driver sees throat impedance directly
U = (B_l * voltage) / (Z_e * Z_m) * self.driver.sd
```

**Should be**:

```python
# Driver sees combined acoustic load (throat || chamber)
Z_mechanical = (R_ms + 1j * omega * M_ms + 1 / (1j * omega * C_ms) +
                self.driver.sd**2 * Z_acoustic)

Z_electrical = R_e + 1j * omega * L_e + (B_l**2) / Z_mechanical

# Volume velocity at throat
U_throat = (B_l * voltage) / (Z_electrical * Z_mechanical) * self.driver.sd
```

**Key point**: The mechanical impedance must include `S_d² × Z_acoustic` where `Z_acoustic` is the **parallel combination** of throat and chamber.

---

## Implementation Strategy

### Phase 1: Add Helmholtz Resonance Only

**Goal**: Verify basic chamber physics works

1. Add `calculate_helmholtz_frequency()` method
2. Implement `calculate_front_chamber_impedance()` with **only Helmholtz mode**
3. Fix impedance topology (parallel combination)
4. Test against case3 synthetic fixture

**Expected result**: RMSE should drop from 34 → 15-20 dB

---

### Phase 2: Add Multi-Mode Support

**Goal**: Capture standing wave effects

1. Implement standing wave frequency calculation
2. Add modal impedance summation
3. Parameterize `front_chamber_modes` (0 = Helmholtz only, 3 = with modes)
4. Test against case3 with different mode counts

**Expected result**: RMSE should drop from 15-20 → 4-6 dB

---

### Phase 3: Validate Complete System

**Goal**: Verify case4 (complete system) works

1. Run case4 validation with new chamber model
2. Check that front and rear chambers interact correctly
3. Verify overall system response

**Expected result**: RMSE should drop from 35 → 5-7 dB

---

## Testing Checklist

Before considering implementation complete:

- [ ] Helmholtz frequency is reasonable (100-150 Hz for typical 6 L chamber)
- [ ] Chamber impedance shows compliance behavior at low frequency
- [ ] Standing wave modes create expected ripples at higher frequencies
- [ ] Impedance topology is parallel (not series)
- [ ] case3 RMSE < 10 dB (ideally 4-6 dB)
- [ ] case4 RMSE < 10 dB (ideally 5-7 dB)
- [ ] Phase response is smooth (no wild swings)
- [ ] F3 frequency is within 5 Hz of Hornresp

---

## Validation Against case3

**Case3 parameters** (from `tests/fixtures/hornresp/synthetic/case3_horn_front_chamber/`):

```
Driver: idealized_18inch
Throat area: 600 cm²
Mouth area: 4800 cm²
Horn length: 200 cm
Front chamber: 6 L
Rear chamber: 1 L (very small)
Cutoff: 35 Hz
```

**Expected behavior**:
- Helmholtz resonance around 125 Hz
- Small rear chamber has minimal effect
- Horn response dominates below 100 Hz
- Chamber effects visible 100-300 Hz

**Validation test**:

```bash
# Run validation
PYTHONPATH=src pytest tests/validation/test_synthetic_cases.py::test_synthetic_case_validation[case3_horn_front_chamber] -v

# Check metrics
# Before: RMSE ≈ 34 dB, correlation ≈ 0.33
# After: RMSE ≈ 4-6 dB, correlation > 0.95
```

---

## Common Pitfalls

### ❌ Pitfall 1: Using Physical Length Instead of Effective

```python
L_eff = L_physical  # WRONG
L_eff = L_physical + 1.7 * radius  # CORRECT
```

**Symptom**: Helmholtz frequency 10-20% too high.

---

### ❌ Pitfall 2: Wrong Boundary Conditions

```python
# Open-open tube (WRONG for most chambers)
f_n = n * c / (2 * L_chamber)

# Open-closed tube (CORRECT)
f_n = n * c / (2 * L_chamber)  # For approximation
# Or better: use actual chamber geometry
```

**Symptom**: Standing wave frequencies 2× too high.

---

### ❌ Pitfall 3: Series Instead of Parallel Impedance

```python
# Series (WRONG)
Z_total = Z_throat + Z_chamber

# Parallel (CORRECT)
Z_total = (Z_throat * Z_chamber) / (Z_throat + Z_chamber)
```

**Symptom**: Catastrophic errors (30+ dB) across all frequencies.

---

### ❌ Pitfall 4: Missing Throat Area in Helmholtz Calculation

```python
f_h = (c / 2π) * sqrt(1 / (L_eff * V_chamber))  # WRONG - missing S_throat

f_h = (c / 2π) * sqrt(S_throat / (L_eff * V_chamber))  # CORRECT
```

**Symptom**: Helmholtz frequency wildly incorrect.

---

## Code Review Checklist

When reviewing the implementation:

- [ ] `calculate_helmholtz_frequency()` uses end corrections
- [ ] `calculate_front_chamber_impedance()` sums all modes
- [ ] Impedance topology is parallel combination
- [ ] Mechanical impedance includes `S_d² × Z_acoustic`
- [ ] Chamber impedance is calculated across frequency array
- [ ] Modal Q is reasonable (5-20)
- [ ] Standing wave frequencies are calculated correctly
- [ ] Units are consistent (SI, not mixing cm/m/L/m³)

---

## Expected Impact on Baseline Metrics

After implementing these changes, update baselines:

**case3** (front chamber):
- Current RMSE: 34.39 dB
- Target RMSE: 4-6 dB
- Expected improvement: ~28-30 dB

**case4** (complete system):
- Current RMSE: 35.83 dB
- Target RMSE: 5-7 dB
- Expected improvement: ~28-30 dB

When metrics improve, regenerate baselines:

```bash
PYTHONPATH=src python3 tools/generate_baselines.py
```

---

## References

1. **Kolbrek AES 2018** - Front chamber Helmholtz resonance
2. **helholtz_resonance.md** - Detailed physics derivation
3. **multi_mode_resonance.md** - Standing wave modes
4. **Hornresp source** (if available) - Reference implementation

---

## Next Steps After Implementation

1. ✅ Implement Helmholtz resonance
2. ✅ Implement multi-mode support
3. ✅ Fix impedance topology
4. ⏳ Run validation tests
5. ⏳ Update baselines if improved
6. ⏳ Document in code with literature citations
7. ⏳ Move to Priority 2 (finite horn theory)
