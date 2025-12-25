# Implementation Quick Reference

Key formulas and implementation notes for each phase.

---

## Constants

```python
c = 343.7        # Speed of sound in air (m/s) at 20°C
ρ0 = 1.204       # Density of air (kg/m³) at 20°C
π = 3.14159265359
```

---

## Phase 1: Radiation Impedance

### Circular Piston in Infinite Baffle

**Normalized Radiation Impedance:**
```
Z_norm = R(ka) + j·X(ka)

R(ka) = 1 - J₁(2ka) / ka
X(ka) = H₁(2ka) / ka
```

**Actual Radiation Impedance:**
```
Z_rad = ρ₀·c / S · Z_norm
```

Where:
- `ka = 2πf·a / c` (dimensionless frequency)
- `J₁` = Bessel function of first kind, order 1
- `H₁` = Struve function of order 1
- `a` = piston radius (m)
- `S` = piston area (m²)

### SciPy Implementation
```python
from scipy.special import j1, struve

def radiation_impedance(area_m2, frequency_hz):
    """Calculate radiation impedance for circular piston in infinite baffle."""
    radius = np.sqrt(area_m2 / np.pi)
    k = 2 * np.pi * frequency_hz / c
    ka = k * radius

    if ka < 1e-10:  # DC limit
        R_norm = 0.0
        X_norm = 0.0
    else:
        arg = 2 * ka
        R_norm = 1 - j1(arg) / ka
        X_norm = struve(1, arg) / ka

    Z_norm = R_norm + 1j * X_norm
    Z_rad = (ρ0 * c / area_m2) * Z_norm

    return Z_rad
```

---

## Phase 2: Transfer Matrices (Single Segment)

### Transfer Matrix Definition
```
| p₁ |   | a  b | | p₂ |
|    | = |      | |    |
| U₁ |   | c  d | | U₂ |
```

### Exponential Horn
**Area function:** `S(x) = S₁ · exp(2mx)`
**Flare constant:** `m = ln(S₂/S₁) / (2·L)`

**Wave number:**
```
γ = √(k² - m²)      (above cutoff)
γ = j√(m² - k²)     (below cutoff, becomes imaginary)
```

**T-Matrix Elements:**
```
For γ ≠ m:
    a = exp(γL) · (cos(γL) + (m/γ)·sin(γL))
    b = j·ρ₀·c·k/S₂ · exp(γL) · sin(γL)
    c = j·S₂/(ρ₀·c·k) · exp(γL) · [sin(γL) · (γ² + m²)/(γ)]
    d = exp(γL) · (cos(γL) - (m/γ)·sin(γL))
```

**Cutoff frequency:**
```
fc = c·m / (2π)
```

### Conical Horn
**Flare constant:** `m = 1/x = (S₂ - S₁)/(S₁·L)`

Similar to exponential but with `m` redefined.

### Hyperbolic Horn
**T parameter:** 0 (catenoidal), <1 (cosh), >1 (sinh)

---

## Phase 3: Driver Equivalent Circuit

### Thiele-Small to Acoustic Domain

**Electrical Impedance:**
```
Ze = Re + j·ω·Le
```

**Mechanical Impedance (reflected):**
```
Zme = (Bl)² / Ze
```

**Mechanical Impedance (total):**
```
Zm = Rms + j·ω·Mmd + 1/(j·ω·Cms)
```

**Acoustic Source Impedance:**
```
Zas = (Zme + Zm) / Sd²
```

**Acoustic Source Pressure:**
```
ps = eg·Bl / (Sd·Ze)
```

**Volume Velocity:**
```
UaL = ps / (Zas + Zal)
```

Where:
- `Zal` = acoustic load impedance (from horn + chambers)
- `eg` = generator voltage (typically 2.83V for 1W into 8Ω)

---

## Phase 4: Complete Front-Loaded Horn

### Chamber Compliances

**Rear Chamber:**
```
Cab = Vrc / (ρ₀·c²)    [acoustic compliance]
```

**Front (Throat) Chamber:**
```
Caf = Vtc / (ρ₀·c²)
```

### Combined Load Impedance

**Horn Throat Impedance:** `Zth` (from T-matrix calculation)

**Front Chamber in Parallel:**
```
Zf = Zth || Caf = Zth / (1 + j·ω·Caf·Zth)
```

**Rear Chamber in Series:**
```
Zal = Zf + Cab
```

### Power Calculation

**Acoustic Power:**
```
Pa = |Uth|² · Re(Zth)
SPL = 10·log10(Pa/Pref) + 20·log10(d/rref)
```

Where:
- `Pref = 10⁻¹² W` (reference power)
- `d = 1 m`, `rref = 1 m`

---

## Phase 5: Multi-Segment Horns

### Matrix Multiplication

**Composite T-Matrix:**
```
M_total = M₁ · M₂ · M₃ · ... · Mₙ
```

Each segment contributes:
```
M_i = | a_i  b_i |
      | c_i  d_i |
```

### Boundary Conditions

At each junction:
```
p_left = p_right
U_left = U_right
```

---

## Phase 6: Advanced Features

### Tapped Horn

Driver taps into horn at two points. Requires:
- Two paths from driver to mouth
- Combined impedance calculation

### Back-Loaded Horn

Two radiation paths:
1. Direct radiator (front of cone)
2. Horn output (rear of cone)

### Transmission Line

Distributed parameter model:
- Characteristic impedance: `Z₀ = ρ₀·c / S`
- Phase constant: `β = k`
- Losses: Viscothermal damping factor

---

## Validation Checklist

### Phase 1
- [ ] Compare Z_norm vs. ka at 0.1, 1, 10
- [ ] Verify R → 1.0 at high ka
- [ ] Verify X → 0 at high ka

### Phase 2
- [ ] Verify throat impedance at cutoff
- [ ] Check exponential decay below cutoff
- [ ] Validate T-matrix unitarity (det = 1)

### Phase 3
- [ ] Impedance peak at fs
- [ ] Qms, Qes, Qts calculations
- [ ] Phase behavior through resonance

### Phase 4
- [ ] SPL curve shape
- [ ] Impedance modification due to horn loading
- [ ] Cone displacement at resonance

### Phase 5
- [ ] Matrix multiplication correctness
- [ ] Continuity at segment boundaries

### Phase 6
- [ ] Combined output for tapped horn
- [ ] Direct radiator + horn sum for back-loaded

---

## Open-Source Implementation References

**Kolbrek's Octave/Matlab Code:**
```matlab
% T-matrix for exponential horn
function [a,b,c,d] = exp_horn(S1,S2,L,freq)
  c = 343.7;
  rho = 1.204;
  w = 2*pi*freq;
  k = w/c;
  m = log(S2/S1)/(2*L);
  gamma = sqrt(k^2 - m^2);
  % ... (see implementation)
end
```

**Python Equivalent (loudspeaker-tmatrix):**
```python
# https://github.com/nahue-passano/loudspeaker-tmatrix
# Reference for T-matrix implementation in Python
```

---

*Last updated: 2025-12-24*
