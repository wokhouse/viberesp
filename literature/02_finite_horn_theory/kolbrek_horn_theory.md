# Kolbrek Horn Theory: Finite Exponential Horns

**Paper**: "Horn Theory: An Introduction, Part 1 & 2"
**Author**: Bjørn Kolbrek
**Publication**: audioXpress
**Priority**: 🟡 **High** - Addresses 13 dB error in case1

---

## Why This Paper is Critical

This paper provides the **finite exponential horn equations** that differ fundamentally from the infinite horn approximation currently used in Viberesp.

- **Current Viberesp**: Uses infinite horn approximation → 13.56 dB RMSE
- **With finite model**: Expected 3-5 dB RMSE

The paper is the foundation for understanding:
1. Finite vs infinite horn impedance
2. Mouth reflection effects
3. Below-cutoff transmission
4. Hyperbolic function formulations

---

## Infinite vs Finite Horns

### Infinite Horn (Current Viberesp - WRONG)

**Assumption**: Horn continues infinitely with no mouth reflections.

**Throat impedance** (Kolbrek Eq. 3.7):

```
Z_throat_infinite = (ρ₀c/S_t) × √(1 - m²/(4k²))  for k > m/2
Z_throat_infinite = (ρ₀c/S_t) × (j × m/(2k))        for k < m/2
```

Where:
- `S_t` = throat area
- `m` = flare rate (1/m)
- `k = ω/c` = wavenumber
- `ρ₀c/S_t` = characteristic impedance

**Problems**:
- No mouth reflections
- No standing waves
- Incorrect below cutoff (kc < 1)
- Wrong impedance magnitude

---

### Finite Horn (Correct Model)

**Reality**: Horn has finite length with mouth reflections.

**Throat impedance** (Kolbrek Eq. 3.21):

```
Z_throat_finite = Z_char × coth(γ × L_eff)
```

Where:
- `Z_char = (ρ₀c/S_t)` = characteristic impedance
- `γ = sqrt(m²/4 - k²)` = complex propagation constant
- `L_eff` = effective horn length with end corrections

**With mouth radiation**:

```
Z_throat = Z_char × [coth(γ × L) + (Z_mouth / Z_char) / sinh²(γ × L)]
```

The second term accounts for mouth reflections.

---

## Key Equations

### 1. Complex Propagation Constant

```
γ = sqrt(m²/4 - k² + 0j)
```

**Properties**:
- **Above cutoff** (k > m/2): γ is **imaginary** → waves propagate
- **Below cutoff** (k < m/2): γ is **real** → waves decay exponentially
- **At cutoff** (k = m/2): γ = 0 → transition point

**Implementation**:

```python
def calculate_propagation_constant(self, frequencies):
    """Calculate complex propagation constant."""
    omega = 2 * np.pi * frequencies
    c = 343.0
    k = omega / c  # Wavenumber

    m = self.flare_rate  # Flare rate (1/m)

    # Complex propagation constant
    gamma = np.sqrt(m**2 / 4 - k**2 + 0j)

    return gamma
```

---

### 2. Characteristic Impedance

```
Z_char = ρ₀ × c / S_t
```

Where:
- `ρ₀` = air density (1.184 kg/m³)
- `c` = speed of sound (343 m/s)
- `S_t` = throat area (m²)

This is the **reference impedance** for the horn.

---

### 3. Finite Horn Throat Impedance (Simplified)

**Without mouth radiation** (still captures key finite effects):

```
Z_throat = Z_char × coth(γ × L)
```

**Implementation**:

```python
def calculate_finite_throat_impedance(self, frequencies):
    """Calculate finite horn throat impedance (simplified)."""
    rho = 1.184
    c = 343.0

    # Characteristic impedance
    S_throat = self.throat_area_cm2 / 10000  # cm² → m²
    Z_char = (rho * c) / S_throat

    # Propagation constant
    gamma = self.calculate_propagation_constant(frequencies)

    # Horn length
    L = self.horn_length_cm / 100  # cm → m

    # Finite horn impedance
    Z_throat = Z_char / np.tanh(gamma * L)  # Note: coth(x) = 1/tanh(x)

    return Z_throat
```

---

### 4. Finite Horn Throat Impedance (With Mouth Radiation)

**Complete equation** including mouth reflections:

```
Z_throat = Z_char × coth(γ × L) + Z_mouth / sinh²(γ × L)
```

Where `Z_mouth` is the radiation impedance at the mouth.

**Implementation**:

```python
def calculate_finite_throat_impedance_complete(self, frequencies):
    """Calculate finite horn throat impedance with mouth radiation."""
    rho = 1.184
    c = 343.0

    # Characteristic impedance
    S_throat = self.throat_area_cm2 / 10000
    Z_char = (rho * c) / S_throat

    # Propagation constant
    gamma = self.calculate_propagation_constant(frequencies)

    # Horn length
    L = self.horn_length_cm / 100

    # Hyperbolic functions
    sinh_gamma_L = np.sinh(gamma * L)
    cosh_gamma_L = np.cosh(gamma * L)

    # Mouth radiation impedance (Beranek circular piston)
    Z_mouth = self.calculate_mouth_radiation_impedance(frequencies)

    # Finite horn with mouth reflection
    Z_throat = Z_char * cosh_gamma_L / sinh_gamma_L + Z_mouth / (sinh_gamma_L**2)

    return Z_throat
```

---

## Hyperbolic Functions

The finite horn model uses hyperbolic functions:

### sinh(x) - Hyperbolic Sine

```
sinh(x) = (eˣ - e⁻ˣ) / 2
```

**Properties**:
- sinh(0) = 0
- sinh(x) → ∞ as x → ∞
- sinh(x) → -∞ as x → -∞

**Python**: `numpy.sinh(x)`

---

### cosh(x) - Hyperbolic Cosine

```
cosh(x) = (eˣ + e⁻ˣ) / 2
```

**Properties**:
- cosh(0) = 1
- cosh(x) → ∞ as x → ±∞
- Always positive

**Python**: `numpy.cosh(x)`

---

### coth(x) - Hyperbolic Cotangent

```
coth(x) = cosh(x) / sinh(x) = (eˣ + e⁻ˣ) / (eˣ - e⁻ˣ)
```

**Properties**:
- coth(x) → 1 as x → ∞
- coth(x) → -1 as x → -∞
- coth(x) → ∞ as x → 0

**Python**: `1 / numpy.tanh(x)` (no direct coth in NumPy)

---

### tanh(x) - Hyperbolic Tangent

```
tanh(x) = sinh(x) / cosh(x) = (eˣ - e⁻ˣ) / (eˣ + e⁻ˣ)
```

**Properties**:
- tanh(0) = 0
- tanh(x) → 1 as x → ∞
- tanh(x) → -1 as x → -∞
- Always between -1 and 1

**Python**: `numpy.tanh(x)`

---

## Below Cutoff Behavior

### Infinite Horn (WRONG)

Below cutoff (k < m/2), the infinite horn has:

```
Z_throat = j × (ρ₀c/S_t) × m/(2k)
```

This is **purely reactive** (no power transmission).

---

### Finite Horn (CORRECT)

Below cutoff (k < m/2), γ is **real**, so:

```
coth(γ × L) ≈ 1 + 2e^(-2γL)  (for γL > 1)
```

This has a **real part** due to:
- Mouth reflections
- Standing waves
- Finite length effects

**Key insight**: Finite horns **can transmit below cutoff** (unlike infinite horns).

---

## Mouth Reflections

The mouth reflection term:

```
Z_reflection = Z_mouth / sinh²(γ × L)
```

**Physical meaning**:
- At low frequencies: sinh(γL) is small → reflection dominates
- At high frequencies: sinh(γL) is large → reflection negligible
- At cutoff: γ → 0 → sinh(γL) → 0 → strong reflection

**Result**: Frequency response ripple due to reflections.

---

## End Corrections

The effective horn length includes end corrections:

```
L_eff = L_physical + Δ_L_throat + Δ_L_mouth
```

**Throat end correction** (driver side):

```
Δ_L_throat = 0.85 × a_throat
```

**Mouth end correction** (radiation side):

```
Δ_L_mouth = 0.6 × a_mouth
```

Where `a = √(S/π)` is the radius.

**Implementation**:

```python
def calculate_effective_length(self):
    """Calculate effective horn length with end corrections."""
    L_physical = self.horn_length_cm / 100

    # Throat radius
    a_throat = np.sqrt(self.throat_area_cm2 / 10000 / np.pi)

    # Mouth radius
    a_mouth = np.sqrt(self.mouth_area_cm2 / 10000 / np.pi)

    # End corrections
    delta_L = 0.85 * a_throat + 0.6 * a_mouth

    L_eff = L_physical + delta_L

    return L_eff
```

---

## Comparison: Infinite vs Finite

### Low Frequency (f << fc)

**Infinite horn**:
```
Z ≈ j × (ρ₀c/S_t) × m/(2k)
→ Purely reactive, no power
```

**Finite horn**:
```
Z ≈ (ρ₀c/S_t) × [1 + 2e^(-2γL)]
→ Has real part, can transmit power
```

**Difference**: Finite horn works below cutoff, infinite doesn't.

---

### High Frequency (f >> fc)

**Infinite horn**:
```
Z ≈ ρ₀c/S_t
→ Constant characteristic impedance
```

**Finite horn**:
```
Z ≈ ρ₀c/S_t + small_reflection_term
→ Nearly same as infinite
```

**Difference**: Minimal at high frequencies (mouth reflections small).

---

### At Cutoff (f = fc)

**Infinite horn**:
```
Z → ∞ (theoretical)
```

**Finite horn**:
```
Z ≈ Z_char × coth(γL)
→ Finite, reflection-dominated
```

**Difference**: Finite horn has finite impedance at cutoff.

---

## Current Viberesp Implementation

**Location**: `src/viberesp/enclosures/horns/exponential_horn.py:126-140`

**Current code** (infinite approximation):

```python
# Calculate throat resistance
k_term = 4 * k**2 - m**2
resistance = np.zeros_like(frequencies)
above_cutoff = k_term > 0
resistance[above_cutoff] = Z0 * np.sqrt(k_term[above_cutoff]) / (2 * k[above_cutoff])

# Calculate throat reactance
reactance = np.zeros_like(frequencies)
reactance[above_cutoff] = Z0 * m / (2 * k[above_cutoff])
reactance[~above_cutoff] = Z0 * m / (2 * k[~above_cutoff])

Z_throat = resistance + 1j * reactance
```

**Issues**:
1. Uses infinite horn approximation
2. Missing hyperbolic functions
3. No mouth reflection term
4. Incorrect below-cutoff behavior

---

## Required Changes

### Replace calculate_throat_impedance()

**Current**: Infinite horn approximation

**Should be**: Finite horn with mouth radiation

See `throat_impedance.md` for detailed implementation guide.

---

### Add End Corrections

**Current**: Uses physical horn length

**Should be**: Effective length with end corrections

```python
L_eff = L_physical + 0.85 * a_throat + 0.6 * a_mouth
```

---

### Add Mouth Radiation Coupling

**Current**: Mouth radiation calculated but not coupled to throat

**Should be**: Include `Z_mouth / sinh²(γL)` term

---

## Expected Results After Implementation

### Validation Test case1 (Straight Horn)

| Metric | Current | Target After Fix |
|--------|---------|------------------|
| RMSE | 13.56 dB | 3-5 dB |
| Correlation | -0.21 | >0.95 |
| F3 error | None | <2 Hz |

**Key improvements**:
- Correct low-frequency behavior (below cutoff)
- Proper standing wave ripple
- Accurate impedance magnitude

---

## References

1. **Kolbrek, "Horn Theory: An Introduction, Part 1"** (audioXpress)
   - https://www.grc.com/acoustics/an-introduction-to-horn-theory.pdf

2. **Kolbrek, "Horn Theory: An Introduction, Part 2"** (audioXpress)
   - Hyperbolic functions and finite horns

3. **Olson, "Acoustical Engineering"** (1957)
   - Chapter on horn loudspeakers

4. **Beranek & Mellow, "Acoustics"** (2012)
   - Radiation impedance modeling

---

## Next Steps

1. ✅ Read this summary
2. ⏳ Study `throat_impedance.md` for detailed derivation
3. ⏳ Review `mouth_reflections.md` for finite length effects
4. ⏳ Consult `implementation_notes.md` for code changes
5. ⏳ Implement finite horn model in `exponential_horn.py:126-140`
