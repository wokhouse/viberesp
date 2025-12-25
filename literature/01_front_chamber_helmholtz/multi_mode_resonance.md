# Multi-Mode Resonance in Front Chambers

**Application**: Standing wave modes in large front chambers
**Priority**: 🔴 **Critical** - Completes front chamber model

---

## Why Multi-Mode Matters

The Helmholtz resonance (0th mode) treats the chamber as a lumped element - the air moves uniformly in and out.

**But** when chamber dimensions are large compared to wavelength:
- Standing waves form inside the chamber
- Multiple resonant frequencies appear
- Each mode acts as an independent resonator

**When does this matter?**

```
L_chamber > λ/4  or  f > c / (4 × L_chamber)
```

For typical front chambers (6-20 L), this matters above ~100-200 Hz.

---

## Standing Wave Fundamentals

### 1D Standing Waves in a Tube

For a chamber approximated as a tube of length `L_chamber`:

```
f_n = n × c / (2 × L_chamber)  for n = 1, 2, 3, ...
```

Where:
- `n` = mode number (1 = fundamental, 2 = 2nd harmonic, etc.)
- `c` = speed of sound (343 m/s)
- `L_chamber` = effective chamber length (m)

**Boundary conditions**:
- Open-closed tube (one end driver, one end horn throat)
- Closed-closed tube (both ends rigid)
- Open-open tube (both ends open to larger volume)

**Most front chambers**: Open-closed approximation works well.

---

## Modal Impedance

Each mode acts as a **second-order resonant system**:

```
Z_n(f) = R_n / (1 + jQ_n × (f/f_n - f_n/f))
```

Where:
- `Z_n(f)` = impedance of mode n at frequency f
- `R_n` = modal resistance at resonance
- `Q_n` = modal quality factor
- `f_n` = resonant frequency of mode n

**Alternative form** (more common in acoustics):

```
Z_n(f) = R_n × (f_n / f) × Q_n / (1 + jQ_n × (f/f_n - f_n/f))
```

---

## Total Chamber Impedance

The complete chamber impedance includes **all modes**:

```
Z_chamber_total(f) = Z_helmholtz(f) + Σ[Z_n(f) for n = 1 to N]
```

Where:
- `Z_helmholtz` = 0th mode (Helmholtz resonance)
- `Z_n` = nth standing wave mode
- `N` = number of modes to include (typically 3-5)

**Physical intuition**:
- Each mode is a parallel resonance pathway
- At frequencies near `f_n`, that mode dominates impedance
- Far from `f_n`, mode impedance is high (doesn't affect response)

---

## Modal Quality Factor (Q)

The **Q factor** determines how sharp each resonance is:

```
Q_n = 2π × (stored energy) / (energy dissipated per cycle)
```

**Typical values**:
- **Q = 5-10**: Moderately damped (typical for lined enclosures)
- **Q = 10-20**: Lightly damped (unlined enclosures)
- **Q = 20-50**: Very light damping (hard walls)

**Factors affecting Q**:
- **Absorption**: Damping material lowers Q
- **Wall losses**: Porous walls lower Q
- **Radiation**: Openings to throat lower Q
- **Viscous losses**: Air viscosity lowers Q (higher at small scales)

---

## Complete Python Implementation

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class MultiModeChamber:
    """Front chamber with Helmholtz + multi-mode resonance."""

    throat_area_cm2: float
    chamber_volume_liters: float
    chamber_length_cm: float
    throat_length_cm: float
    num_modes: int = 3
    modal_Q: float = 10.0

    def __post_init__(self):
        """Calculate derived properties."""
        self.c = 343.0
        self.rho = 1.184

        # SI units
        self.S_throat = self.throat_area_cm2 / 10000
        self.V_chamber = self.chamber_volume_liters / 1000
        self.L_chamber = self.chamber_length_cm / 100
        self.L_throat = self.throat_length_cm / 100

        # Effective lengths with end corrections
        a_throat = np.sqrt(self.S_throat / np.pi)
        self.L_throat_eff = self.L_throat + 1.7 * a_throat

    def calculate_helmholtz_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """Calculate Helmholtz (0th mode) impedance."""
        omega = 2 * np.pi * frequencies

        # Acoustic compliance
        C_acoustic = self.V_chamber / (self.rho * self.c**2)

        # Chamber impedance (compliance)
        Z_helmholtz = 1 / (1j * omega * C_acoustic)

        return Z_helmholtz

    def calculate_standing_wave_frequencies(self) -> np.ndarray:
        """Calculate standing wave mode frequencies."""
        # Open-closed tube approximation
        f_n = np.arange(1, self.num_modes + 1) * self.c / (2 * self.L_chamber)
        return f_n

    def calculate_modal_impedance(self, frequencies: np.ndarray, mode_n: int) -> np.ndarray:
        """Calculate impedance of a specific standing wave mode."""
        # Resonant frequency for this mode
        f_n = mode_n * self.c / (2 * self.L_chamber)
        omega_n = 2 * np.pi * f_n

        omega = 2 * np.pi * frequencies

        # Modal resistance (empirical - needs calibration)
        # R_n depends on throat area, chamber volume, and damping
        R_n = (self.rho * self.c / self.S_throat) / self.modal_Q

        # Second-order resonant system
        Z_n = R_n / (1 + 1j * self.modal_Q * (omega/omega_n - omega_n/omega))

        return Z_n

    def calculate_total_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """Calculate total chamber impedance including all modes."""
        # Start with Helmholtz mode
        Z_total = self.calculate_helmholtz_impedance(frequencies)

        # Add standing wave modes
        for n in range(1, self.num_modes + 1):
            Z_n = self.calculate_modal_impedance(frequencies, n)
            Z_total += Z_n

        return Z_total

    def analyze_modes(self) -> dict:
        """Analyze all modes and return frequencies and Q."""
        f_n = self.calculate_standing_wave_frequencies()

        # Helmholtz frequency
        f_h = (self.c / (2 * np.pi)) * np.sqrt(
            self.S_throat / (self.L_throat_eff * self.V_chamber)
        )

        return {
            'helmholtz_frequency': f_h,
            'standing_wave_frequencies': f_n,
            'num_modes': self.num_modes,
            'modal_Q': self.modal_Q,
        }


# Example usage
if __name__ == "__main__":
    # Case 3 parameters (from validation test)
    chamber = MultiModeChamber(
        throat_area_cm2=600,
        chamber_volume_liters=6,
        chamber_length_cm=30,  # Approximate from geometry
        throat_length_cm=5,
        num_modes=3,
        modal_Q=10.0,
    )

    # Analyze modes
    analysis = chamber.analyze_modes()
    print(f"Helmholtz frequency: {analysis['helmholtz_frequency']:.2f} Hz")
    print(f"Standing wave modes: {analysis['standing_wave_frequencies']}")

    # Calculate impedance across frequency range
    frequencies = np.logspace(1, 3, 600)  # 10 Hz - 1 kHz
    Z_chamber = chamber.calculate_total_impedance(frequencies)

    # Find impedance minima (resonances)
    min_idx = np.argmin(np.abs(Z_chamber))
    print(f"Impedance minimum at: {frequencies[min_idx]:.2f} Hz")
```

---

## When to Use Multi-Mode

### Rule of Thumb

Use multi-mode analysis when:

```
L_chamber > c / (4 × f_max)
```

Where `f_max` is the highest frequency of interest.

**Example**: For bass horn up to 200 Hz:
```
L_chamber > 343 / (4 × 200) = 0.43 m = 43 cm
```

So chambers longer than ~43 cm need multi-mode analysis.

---

### Validation Test case3

**Parameters**:
- Chamber volume: 6 L
- Approximate chamber length: 30 cm (estimated from volume)
- Throat area: 600 cm²

**Analysis**:
```
L_chamber = 30 cm < 43 cm
→ Multi-mode effects are small
→ Helmholtz mode dominates
```

**But**: 30 cm is close to threshold, so including 1-2 modes is still recommended for accuracy.

---

## Interaction with Horn Throat

The multi-mode chamber impedance couples to the horn throat:

```
        ┌─── Z_helmholtz ──┐
        │                 │
        ├─── Z_1 (mode 1) ─┤
        │                 │
Driver ─┼─── Z_2 (mode 2) ─┼─── Throat ──── Horn
        │                 │
        ├─── Z_3 (mode 3) ─┤
        │                 │
        └─────────────────┘
```

**Total chamber impedance**:

```
Z_chamber = Z_helmholtz + Z_1 + Z_2 + Z_3 + ...
```

**Combined with throat**:

```
Z_total = (Z_throat × Z_chamber) / (Z_throat + Z_chamber)
```

---

## Design Implications

### 1. Higher Modes Create Response Ripples

Each standing wave mode creates:
- **Impedance dip** at its resonant frequency
- **Phase shift** around resonance
- **Group delay peak** at resonance

**Result**: Frequency response shows ripples above first standing wave mode.

---

### 2. Damping Reduces Ripple Height

Adding damping material:
- **Lowers Q** (broader, shallower resonances)
- **Reduces impedance variation**
- **Smooths frequency response**

**Trade-off**: Too much damping can:
- Reduce efficiency
- Change phase response
- Affect transient response

---

### 3. Optimal Chamber Geometry

To minimize unwanted resonances:

**Option A**: Make chamber small
```
L_chamber < c / (4 × f_max)
→ No standing waves in passband
```

**Option B**: Make chamber highly damped
```
Use absorptive lining
→ Low Q reduces ripple amplitude
```

**Option C**: Tune resonances away from passband
```
Ensure f_n > f_max for all modes
→ Resonances occur above operating range
```

---

## Common Mistakes

### ❌ Mistake 1: Ignoring Higher Modes

Using only Helmholtz mode for large chambers:

```python
Z_chamber = calculate_helmholtz_impedance(f)  # INCOMPLETE for large chambers
Z_chamber = calculate_helmholtz_impedance(f) + sum_modal_impedances(f)  # CORRECT
```

**Impact**: Missing ripples and peaks in 100-500 Hz range.

---

### ❌ Mistake 2: Wrong Boundary Conditions

Using open-open tube formula instead of open-closed:

```python
# Open-open (both ends open)
f_n = n * c / (2 * L)  # WRONG for most front chambers

# Open-closed (one closed, one open)
f_n = (2n - 1) * c / (4 * L)  # CORRECT for n=1,2,3...
```

**Impact**: Mode frequencies will be wrong (typically 2× error).

---

### ❌ Mistake 3: Incorrect Modal Q

Using same Q for all modes without considering damping:

```python
Q_all = 10.0  # Too simplistic
```

**Better**:
```python
# Q typically decreases with frequency (more damping at higher modes)
Q_n = Q_base / sqrt(n)  # Or measure empirically
```

---

### ❌ Mistake 4: Forgetting End Corrections

Using physical chamber length instead of effective:

```python
L_effective = L_physical  # WRONG
L_effective = L_physical + end_correction  # CORRECT
```

**Impact**: Mode frequencies shifted by 10-20%.

---

## Validation Examples

### Example 1: Small Chamber (No Standing Waves)

```
V_chamber = 6 L
L_chamber ≈ 20 cm
f_max = 200 Hz

Check: 20 cm < 43 cm → No standing waves needed
```

**Model**: Helmholtz only (0th mode sufficient)

---

### Example 2: Medium Chamber (1-2 Modes)

```
V_chamber = 20 L
L_chamber ≈ 40 cm
f_max = 200 Hz

Check: 40 cm ≈ 43 cm → Borderline
```

**Model**: Helmholtz + 1-2 standing wave modes

---

### Example 3: Large Chamber (Multiple Modes)

```
V_chamber = 50 L
L_chamber ≈ 60 cm
f_max = 200 Hz

Check: 60 cm > 43 cm → Standing waves important
```

**Model**: Helmholtz + 3-5 standing wave modes

---

## Implementation Checklist

When implementing multi-mode resonance:

- ✅ Calculate Helmholtz frequency (0th mode)
- ✅ Calculate standing wave frequencies: `f_n = n×c/(2×L_chamber)`
- ✅ Assign appropriate Q values (5-20 typical)
- ✅ Calculate modal impedance for each mode
- ✅ Sum all modes: `Z_total = Z_helmholtz + Σ(Z_n)`
- ✅ Combine with throat impedance (parallel combination)
- ✅ Validate against Hornresp for simple chamber cases

---

## References

1. **Kinsler et al., "Fundamentals of Acoustics"** - Standing waves in pipes
2. **Munjal, "Acoustics of Ducts and Mufflers"** - Modal analysis methods
3. **Kolbrek AES 2018** - Multi-mode chambers in horn loudspeakers
4. **Beranek & Mellow** - Higher-order modes in enclosures

---

## Next Steps

1. ✅ Understand multi-mode resonance
2. ⏳ Review implementation notes (`implementation_notes.md`)
3. ⏳ Implement in `front_loaded_horn.py:592-637`
4. ⏳ Validate against case3 synthetic fixture
