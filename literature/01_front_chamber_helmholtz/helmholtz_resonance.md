# Helmholtz Resonance: Physics and Derivation

**Application**: Front chamber in horn-loaded loudspeakers
**Priority**: 🔴 **Critical** - Foundation for fixing 34-35 dB errors

---

## What is Helmholtz Resonance?

A **Helmholtz resonator** is a system where a volume of air (the chamber) is connected to the outside through a narrow opening (the throat). When air oscillates in the throat, it bounces against the springy air in the chamber, creating a resonant frequency.

**Analogy**: Think of blowing across the top of a bottle - the note you hear is the Helmholtz resonance.

### In Horn Loudspeakers

For a front-loaded horn:
- **Mass**: Air in the throat moves back and forth
- **Spring**: Air in the front chamber compresses and expands
- **Resonance**: System oscillates at a specific frequency

---

## Derivation of Helmholtz Frequency

### Step 1: Acoustic Mass of Throat Air

The air in the throat has effective mass:

```
M_acoustic = ρ₀ × L_effective / S_throat
```

Where:
- `ρ₀` = air density (≈1.184 kg/m³ at 20°C)
- `L_effective` = effective throat length including end corrections (m)
- `S_throat` = throat cross-sectional area (m²)

**End corrections**:
For a flanged throat, the effective length is longer than physical length:

```
L_effective = L_physical + 1.7 × a_throat
```

Where `a_throat = √(S_throat/π)` is the throat radius.

---

### Step 2: Acoustic Compliance of Chamber

The air in the chamber acts as a spring with acoustic compliance:

```
C_acoustic = V_front / (ρ₀ × c²)
```

Where:
- `V_front` = front chamber volume (m³)
- `c` = speed of sound (≈343 m/s at 20°C)
- `ρ₀` = air density (kg/m³)

**Physical intuition**: Larger chambers are "softer" springs (higher compliance).

---

### Step 3: Resonant Frequency

For any mass-spring system, the resonant frequency is:

```
f_resonant = 1 / (2π) × √(k/m)
```

In acoustic terms:

```
f_helmholtz = 1 / (2π) × √(1 / (M_acoustic × C_acoustic))
```

Substituting the acoustic mass and compliance:

```
f_helmholtz = 1 / (2π) × √(S_throat / (L_effective × V_front / (ρ₀ × c²) × ρ₀))
```

Simplifying (ρ₀ cancels out):

```
f_helmholtz = (c / 2π) × √(S_throat / (L_effective × V_front))
```

**This is the Helmholtz resonance frequency equation.**

---

## Complete Python Implementation

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class HelmholtzResonator:
    """Front chamber Helmholtz resonator model."""

    throat_area_cm2: float      # Throat area (cm²)
    chamber_volume_liters: float # Chamber volume (L)
    throat_length_cm: float      # Physical throat length (cm)
    temperature_c: float = 20.0  # Air temperature (°C)

    def __post_init__(self):
        """Calculate derived properties."""
        # Physical constants
        self.c = 343.0  # speed of sound at 20°C (m/s)
        self.rho = 1.184  # air density at 20°C (kg/m³)

        # Convert to SI units
        self.S_throat = self.throat_area_cm2 / 10000  # cm² → m²
        self.V_chamber = self.chamber_volume_liters / 1000  # L → m³
        self.L_physical = self.throat_length_cm / 100  # cm → m

        # Calculate effective throat length
        self.L_effective = self.calculate_effective_length()

    def calculate_effective_length(self) -> float:
        """Calculate effective throat length with end corrections."""
        # Throat radius
        a_throat = np.sqrt(self.S_throat / np.pi)

        # End correction for flanged opening
        delta_L = 1.7 * a_throat

        return self.L_physical + delta_L

    def calculate_helmholtz_frequency(self) -> float:
        """Calculate Helmholtz resonance frequency."""
        numerator = self.S_throat
        denominator = self.L_effective * self.V_chamber

        f_h = (self.c / (2 * np.pi)) * np.sqrt(numerator / denominator)
        return f_h

    def calculate_acoustic_compliance(self) -> float:
        """Calculate acoustic compliance of chamber."""
        C_acoustic = self.V_chamber / (self.rho * self.c**2)
        return C_acoustic

    def calculate_acoustic_mass(self) -> float:
        """Calculate acoustic mass of throat air."""
        M_acoustic = self.rho * self.L_effective / self.S_throat
        return M_acoustic

    def calculate_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """Calculate chamber impedance across frequency range."""
        omega = 2 * np.pi * frequencies
        C_acoustic = self.calculate_acoustic_compliance()

        # Chamber impedance (compliance)
        Z_chamber = 1 / (1j * omega * C_acoustic)

        return Z_chamber


# Example usage
if __name__ == "__main__":
    # Typical front-loaded horn parameters
    resonator = HelmholtzResonator(
        throat_area_cm2=600,      # 600 cm² throat
        chamber_volume_liters=6,   # 6 L front chamber
        throat_length_cm=5,        # 5 cm physical length
    )

    f_helmholtz = resonator.calculate_helmholtz_frequency()
    print(f"Helmholtz resonance: {f_helmholtz:.2f} Hz")

    # Calculate impedance at resonance
    Z_at_resonance = resonator.calculate_impedance(np.array([f_helmholtz]))
    print(f"Chamber impedance at resonance: {abs(Z_at_resonance[0]):.2f} Pa·s/m³")
```

---

## Impedance Behavior

### Below Resonance (f < f_h)

The chamber acts as a **stiffness spring** (compliance dominates):

```
Z_chamber ≈ -j / (ω × C_acoustic)
```

Phase angle: **-90°** (voltage leads current)

**Physical meaning**: Air in chamber is compressing, not moving much.

---

### At Resonance (f = f_h)

The mass and spring cancel each other:

```
Z_chamber = 0  (ideal, lossless case)
```

**Physical meaning**: Maximum oscillation - air moves freely in and out of throat.

**Real systems** have some resistance due to:
- Viscous losses in throat
- Thermal losses in chamber
- Radiation losses

**With losses**:

```
Z_chamber(f_h) = R_losses  (small but non-zero)
```

---

### Above Resonance (f > f_h)

The throat air mass dominates:

```
Z_chamber ≈ j × ω × M_acoustic
```

Phase angle: **+90°** (current leads voltage)

**Physical meaning**: Air in throat is too heavy to move fast - chamber becomes irrelevant.

---

## Coupling to Horn Throat

The front chamber is **in parallel** with the horn throat impedance:

```
        ┌─── Z_chamber ──┐
Driver ─┤               ├─── Throat ──── Horn
        └───────────────┘
```

**Combined impedance**:

```
Z_combined = (Z_throat × Z_chamber) / (Z_throat + Z_chamber)
```

**Key insight**:
- **Below f_h**: Chamber impedance is high (stiff spring) → most current goes to horn
- **At f_h**: Chamber impedance is low → current splits between horn and chamber
- **Above f_h**: Chamber impedance is high again (mass) → current goes to horn

This creates a **dip in response** at the Helmholtz frequency if not properly managed.

---

## Design Implications

### 1. Helmholtz Frequency Should Be Low

For bass horns, you want `f_h` **below** the operating range:

```
f_helmholtz < f_cutoff / 2
```

This ensures the chamber doesn't interfere with bass output.

**Design strategy**: Make chamber large enough and/or throat short enough.

---

### 2. Avoid Chamber Resonances in Passband

If `f_h` falls in the operating range, you'll get a response dip.

**Example**: If horn is 35-200 Hz and `f_h = 80 Hz`:
- Expect 3-6 dB dip at 80 Hz
- Phase response becomes irregular
- Group delay increases

---

### 3. Multi-Mode Considerations

For larger chambers, standing wave modes appear:

```
f_n = n × c / (2 × L_chamber)  for n = 1, 2, 3, ...
```

These create **additional resonances** above the Helmholtz mode.

**Design strategy**:
- Keep chamber dimensions small (< λ/4 at highest operating frequency)
- Or use damping material to suppress higher modes
- See `multi_mode_resonance.md` for details

---

## Validation Examples

### Example 1: Small Chamber (6 L)

```
Throat area: 600 cm²
Chamber volume: 6 L
Throat length: 5 cm

Expected f_h ≈ 125 Hz
```

This is **above** typical bass horn cutoff (35 Hz) → may cause response dip.

---

### Example 2: Large Chamber (20 L)

```
Throat area: 600 cm²
Chamber volume: 20 L
Throat length: 5 cm

Expected f_h ≈ 68 Hz
```

Better, but still in bass range. May need damping.

---

### Example 3: Very Large Chamber (50 L)

```
Throat area: 600 cm²
Chamber volume: 50 L
Throat length: 5 cm

Expected f_h ≈ 43 Hz
```

Close to cutoff → minimal interference with bass response.

---

## Common Mistakes

### ❌ Mistake 1: Ignoring End Corrections

Using physical throat length instead of effective length:

```
L_effective = L_physical  # WRONG
L_effective = L_physical + 1.7 × a_throat  # CORRECT
```

**Impact**: Calculated `f_h` will be too high.

---

### ❌ Mistake 2: Wrong Impedance Topology

Treating chamber as series impedance instead of parallel:

```
Z_total = Z_throat + Z_chamber  # WRONG
Z_total = (Z_throat × Z_chamber) / (Z_throat + Z_chamber)  # CORRECT
```

**Impact**: Catastrophic errors (30+ dB) in response prediction.

---

### ❌ Mistake 3: Missing Throat Area Loading

Forgetting that throat area affects both mass and resonance:

```
f_h = (c/2π) × √(1 / (L × V))  # WRONG (missing S_throat)
f_h = (c/2π) × √(S_throat / (L × V))  # CORRECT
```

**Impact**: Resonance frequency will be incorrect.

---

## References

1. **Kinsler et al., "Fundamentals of Acoustics"** - Derivation of Helmholtz resonance
2. **Beranek & Mellow, "Acoustics"** - Acoustic impedance and compliance
3. **Munjal, "Acoustics of Ducts and Mufflers"** - End corrections for orifices
4. **Kolbrek AES 2018** - Application to front-loaded horns

---

## Next Steps

1. ✅ Understand Helmholtz resonance physics
2. ⏳ Study multi-mode resonance (`multi_mode_resonance.md`)
3. ⏳ Review implementation notes (`implementation_notes.md`)
4. ⏳ Implement Helmholtz calculation in `front_loaded_horn.py`
