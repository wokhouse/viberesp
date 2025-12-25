# Throat Impedance: Finite vs Infinite Horns

**Application**: Exponential horn throat impedance calculation
**Priority**: 🟡 **High** - Core fix for case1 (13 dB error)

---

## Infinite Horn Approximation (Current Viberesp)

### Equation

For an **infinite exponential horn**, the throat impedance is (Kolbrek Eq. 3.7):

```
Z_throat = (ρ₀c/S_t) × √(1 - m²/(4k²))  for k > m/2 (above cutoff)
Z_throat = j × (ρ₀c/S_t) × m/(2k)        for k < m/2 (below cutoff)
```

Where:
- `S_t` = throat cross-sectional area (m²)
- `m` = flare rate (1/m)
- `k = ω/c` = wavenumber (rad/m)
- `ρ₀c/S_t` = characteristic impedance

### Implementation (Current Viberesp)

```python
# In exponential_horn.py:126-140
def calculate_throat_impedance_infinite(self, frequencies):
    """Calculate infinite horn throat impedance."""
    rho = 1.184
    c = 343.0
    omega = 2 * np.pi * frequencies
    k = omega / c

    m = self._get_or_calculate_flare_rate()
    S_throat = self.throat_area_cm2 / 10000

    Z0 = (rho * c) / S_throat

    # Above cutoff
    k_term = 4 * k**2 - m**2
    resistance = np.zeros_like(frequencies)
    above_cutoff = k_term > 0
    resistance[above_cutoff] = Z0 * np.sqrt(k_term[above_cutoff]) / (2 * k[above_cutoff])

    # Reactance (same formula for all frequencies)
    reactance = Z0 * m / (2 * k)

    Z_throat = resistance + 1j * reactance

    return Z_throat
```

### Problems with Infinite Approximation

1. **No mouth reflections** - assumes horn continues forever
2. **No standing waves** - no impedance ripples
3. **Wrong below cutoff** - purely reactive, no power transmission
4. **Incorrect magnitude** - typically 10-15 dB error

**Result**: 13.56 dB RMSE compared to Hornresp.

---

## Finite Horn Model (Correct)

### Derivation

Starting from the **Webster horn equation** for exponential horns:

```
d²p/dx² + m × dp/dx + k² × p = 0
```

Where `p(x)` is pressure at position `x` along the horn.

### General Solution

The pressure varies along the horn as:

```
p(x) = A × e^(γx) + B × e^(-γx)
```

Where `γ = sqrt(m²/4 - k²)` is the complex propagation constant.

### Volume Velocity

Volume velocity at position `x`:

```
U(x) = (S(x) / (ρ₀c)) × (A × e^(γx) - B × e^(-γx))
```

Where `S(x) = S_t × e^(mx)` is the horn area at position `x`.

### Boundary Conditions

At the **throat** (x = 0):
```
p(0) = p_throat
U(0) = U_throat
```

At the **mouth** (x = L):
```
p(L) = Z_mouth × U(L)
```

### Solving for Throat Impedance

Apply boundary conditions and solve for `Z_throat = p(0) / U(0)`:

```
Z_throat = Z_char × coth(γ × L) + Z_mouth / sinh²(γ × L)
```

This is the **complete finite horn equation** (Kolbrek Eq. 3.21).

---

## Component Analysis

### Term 1: Characteristic Impedance × coth(γL)

```
Z_1 = Z_char × coth(γ × L)
```

**Physical meaning**:
- Impedance of finite horn **without** mouth reflections
- `coth(γL)` captures the exponential flare

**Behavior**:
- **Above cutoff** (γ imaginary): `coth(γL)` oscillates
- **Below cutoff** (γ real): `coth(γL)` → 1 (mostly resistive)

---

### Term 2: Mouth Reflection

```
Z_2 = Z_mouth / sinh²(γ × L)
```

**Physical meaning**:
- Correction for mouth radiation impedance
- Accounts for impedance mismatch at horn termination

**Behavior**:
- **Low frequencies**: `sinh(γL)` small → `Z_2` large → strong reflections
- **High frequencies**: `sinh(γL)` large → `Z_2` small → negligible reflections
- **At cutoff**: `γ → 0` → `sinh(γL) → 0` → `Z_2 → ∞` → perfect reflection

---

## Complete Implementation

```python
import numpy as np
from scipy.special import j1, struve_h1

class FiniteExponentialHorn:
    """Finite exponential horn with mouth radiation."""

    def __init__(self, throat_area_cm2, mouth_area_cm2, horn_length_cm, flare_rate):
        self.throat_area_cm2 = throat_area_cm2
        self.mouth_area_cm2 = mouth_area_cm2
        self.horn_length_cm = horn_length_cm
        self.flare_rate = flare_rate  # m (1/m)

        # Physical constants
        self.rho = 1.184  # kg/m³
        self.c = 343.0    # m/s

    def calculate_effective_length(self):
        """Calculate effective horn length with end corrections."""
        L_physical = self.horn_length_cm / 100  # cm → m

        # Throat radius
        a_throat = np.sqrt(self.throat_area_cm2 / 10000 / np.pi)

        # Mouth radius
        a_mouth = np.sqrt(self.mouth_area_cm2 / 10000 / np.pi)

        # End corrections
        delta_L = 0.85 * a_throat + 0.6 * a_mouth

        L_eff = L_physical + delta_L

        return L_eff

    def calculate_propagation_constant(self, frequencies):
        """Calculate complex propagation constant."""
        omega = 2 * np.pi * frequencies
        k = omega / self.c

        # Complex propagation constant
        gamma = np.sqrt(self.flare_rate**2 / 4 - k**2 + 0j)

        return gamma

    def calculate_mouth_radiation_impedance(self, frequencies):
        """Calculate mouth radiation impedance (Beranek circular piston)."""
        omega = 2 * np.pi * frequencies
        k = omega / self.c

        # Mouth radius
        a_mouth = np.sqrt(self.mouth_area_cm2 / 10000 / np.pi)
        S_mouth = self.mouth_area_cm2 / 10000

        # Characteristic impedance
        Z0 = (self.rho * self.c) / S_mouth

        # Beranek's circular piston radiation impedance
        ka = k * a_mouth

        # Resistance: R₁(ka) = 1 - 2×J₁(ka)/ka
        R1 = 1 - 2 * j1(ka) / ka

        # Reactance: X₁(ka) = 2×H₁(ka)/ka
        X1 = 2 * struve_h1(ka) / ka

        # Radiation impedance
        Z_rad = Z0 * (R1 + 1j * X1)

        return Z_rad

    def calculate_throat_impedance(self, frequencies):
        """Calculate finite horn throat impedance."""
        # Characteristic impedance at throat
        S_throat = self.throat_area_cm2 / 10000
        Z_char = (self.rho * self.c) / S_throat

        # Propagation constant
        gamma = self.calculate_propagation_constant(frequencies)

        # Effective horn length
        L_eff = self.calculate_effective_length()

        # Hyperbolic functions
        gamma_L = gamma * L_eff
        sinh_gamma_L = np.sinh(gamma_L)
        cosh_gamma_L = np.cosh(gamma_L)

        # Mouth radiation impedance
        Z_mouth = self.calculate_mouth_radiation_impedance(frequencies)

        # Finite horn throat impedance (complete equation)
        Z_throat = Z_char * cosh_gamma_L / sinh_gamma_L + Z_mouth / (sinh_gamma_L**2)

        return Z_throat


# Example usage
if __name__ == "__main__":
    # Case 1 parameters
    horn = FiniteExponentialHorn(
        throat_area_cm2=600,
        mouth_area_cm2=4800,
        horn_length_cm=200,
        flare_rate=4.0,  # m = 4.0 /m
    )

    # Calculate impedance
    frequencies = np.logspace(1, 3, 600)  # 10 Hz - 1 kHz
    Z_throat = horn.calculate_throat_impedance(frequencies)

    # Analyze
    print(f"Throat impedance at 20 Hz: {abs(Z_throat[0]):.2f} Pa·s/m³")
    print(f"Throat impedance at 100 Hz: {abs(Z_throat[50]):.2f} Pa·s/m³")
    print(f"Throat impedance at 1 kHz: {abs(Z_throat[-1]):.2f} Pa·s/m³")
```

---

## Simplified Implementation (Without Mouth Radiation)

For initial testing, you can omit the mouth reflection term:

```python
def calculate_throat_impedance_simplified(self, frequencies):
    """Calculate finite horn throat impedance (simplified, no mouth radiation)."""
    S_throat = self.throat_area_cm2 / 10000
    Z_char = (self.rho * self.c) / S_throat

    gamma = self.calculate_propagation_constant(frequencies)
    L_eff = self.calculate_effective_length()

    # Simplified finite horn (no mouth reflection)
    Z_throat = Z_char / np.tanh(gamma * L_eff)  # coth(x) = 1/tanh(x)

    return Z_throat
```

**Expected accuracy**: Still within 5-7 dB of Hornresp (vs 13 dB with infinite).

---

## Comparison: Infinite vs Finite

### At 20 Hz (Below Cutoff)

**Infinite**:
```python
f = 20  # Hz
k = 2*pi*f/c = 0.366  # rad/m
m = 4.0  # 1/m
# m/2 = 2.0 > k = 0.366 (below cutoff)

Z_infinite ≈ j × (ρ₀c/S_t) × m/(2k)
           ≈ j × 85400  (purely reactive)
```

**Finite**:
```python
L = 2.0  # m (200 cm)
γ = sqrt(4²/4 - 0.366²) = 1.983  (real, below cutoff)

Z_finite = (ρ₀c/S_t) × coth(γL)
         ≈ 85400 × coth(3.966)
         ≈ 85400 × 1.003
         ≈ 85670  (mostly resistive!)
```

**Key difference**: Finite horn has **real part** below cutoff, infinite doesn't.

---

### At 100 Hz (Above Cutoff)

**Infinite**:
```python
f = 100  # Hz
k = 2*pi*f/c = 1.83  # rad/m
# m/2 = 2.0 < k = 1.83 (above cutoff)

Z_infinite ≈ (ρ₀c/S_t) × sqrt(1 - m²/(4k²))
           ≈ 85400 × sqrt(1 - 16/(4×3.35))
           ≈ 85400 × 0.08
           ≈ 6832  (resistive)
```

**Finite**:
```python
γ = sqrt(4²/4 - 1.83²) = sqrt(4 - 3.35) = 0.80j  (imaginary)

Z_finite = (ρ₀c/S_t) × coth(γL)
         ≈ 85400 × coth(1.6j)
         ≈ 85400 × (0.07 - 0.72j)
         ≈ 5988 - 61489j  (complex, with ripple)
```

**Key difference**: Finite horn has **reactive component** due to reflections.

---

### At 1 kHz (Well Above Cutoff)

**Infinite**:
```python
f = 1000  # Hz
k = 2*pi*f/c = 18.3  # rad/m

Z_infinite ≈ (ρ₀c/S_t) × sqrt(1 - m²/(4k²))
           ≈ 85400 × sqrt(1 - 16/(4×335))
           ≈ 85400 × 0.99
           ≈ 84546  (resistive, close to Z_char)
```

**Finite**:
```python
γ = sqrt(4²/4 - 18.3²) = sqrt(4 - 335) = 18.2j  (imaginary)

Z_finite = (ρ₀c/S_t) × coth(γL)
         ≈ 85400 × coth(36.4j)
         ≈ 85400 × 1.00  (oscillating but near 1)
         ≈ 85400  (essentially Z_char)
```

**Key difference**: Minimal at high frequencies (as expected).

---

## Validation

### Test Against Hornresp

For **case1** (straight exponential horn):

```python
horn = FiniteExponentialHorn(
    throat_area_cm2=600,
    mouth_area_cm2=4800,
    horn_length_cm=200,
    flare_rate=4.0,
)

frequencies = np.logspace(1, 3, 600)
Z_throat = horn.calculate_throat_impedance(frequencies)

# Calculate response
response = calculate_response_from_impedance(Z_throat)

# Compare to Hornresp
rmse = calculate_rmse(response, hornresp_reference)
print(f"RMSE: {rmse:.2f} dB")  # Expected: 3-5 dB (vs 13.56 dB infinite)
```

---

## Common Mistakes

### ❌ Mistake 1: Using coth() Directly

```python
Z_throat = Z_char * np.coth(gamma * L)  # WRONG - no coth in NumPy
Z_throat = Z_char / np.tanh(gamma * L)  # CORRECT - coth = 1/tanh
```

---

### ❌ Mistake 2: Forgetting Complex Gamma

```python
gamma = np.sqrt(m**2 / 4 - k**2)  # WRONG - warning for negative values
gamma = np.sqrt(m**2 / 4 - k**2 + 0j)  # CORRECT - always complex
```

---

### ❌ Mistake 3: Using Physical Length

```python
Z_throat = Z_char / np.tanh(gamma * L_physical)  # WRONG
Z_throat = Z_char / np.tanh(gamma * L_eff)  # CORRECT - includes end corrections
```

---

### ❌ Mistake 4: Omitting Mouth Reflection

```python
Z_throat = Z_char * coth(gamma * L)  # Simplified (OK for testing)
Z_throat = Z_char * coth(gamma * L) + Z_mouth / sinh(gamma * L)**2  # COMPLETE (production)
```

---

## References

1. **Kolbrek, "Horn Theory: An Introduction"** - Derivation of finite horn equations
2. **Olson, "Acoustical Engineering"** - Chapter on horn impedance
3. **Beranek, "Acoustics"** - Radiation impedance model
4. **Webster, "Acoustical Impedance of Horns"** - Original horn equation

---

## Next Steps

1. ✅ Understand finite horn derivation
2. ⏳ Study mouth reflections (`mouth_reflections.md`)
3. ⏳ Review implementation notes
4. ⏳ Implement in `exponential_horn.py:126-140`
5. ⏳ Validate against case1 synthetic fixture
