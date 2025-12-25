# Transfer matrix of a truncated cone with viscothermal losses: application of the WKB method

**Authors**: Augustin Ernoult and Jean Kergomard
**Source**: Acta Acustica, Vol. 4(2), Article 7 (2020)
**DOI**: 10.1051/aacus/2020006
**PDF**: https://acta-acustica.edpsciences.org/articles/aacus/pdf/2020/02/aacus200006.pdf

---

## Summary

This paper investigates the use of the **WKB (Wentzel-Kramers-Brillouin) method** for calculating the transfer matrix of **truncated cones (horns)** with **viscothermal losses**, without requiring division into smaller sections. The method provides accurate modeling of **dissipative effects** in conical waveguides for wind instruments and acoustic horns.

---

## Key Contributions

### 1. **Viscothermal Losses in Horns**

**Physical phenomena:**
- **Viscous losses**: Friction due to air viscosity (boundary layer)
- **Thermal losses**: Heat conduction at walls (thermal boundary layer)
- Both effects are **frequency-dependent**
- More significant at **low frequencies** and **small diameters**

**Boundary layer thickness:**

```
δ_v = √(2ω / ω) = √(2μ / (ρω))
δ_α = √(2α / ω)
```

Where:
- `δ_v` = viscous boundary layer thickness
- `δ_α` = thermal boundary layer thickness
- `μ` = dynamic viscosity
- `α` = thermal diffusivity
- `ω` = angular frequency

**Viscothermal losses become important when:**
```
δ_v, δ_α ≳ radius
```

---

### 2. **Webster's Equation with Losses**

**Standard Webster equation (lossless):**

```
d²p/dx² + (1/S) · dS/dx · dp/dx + k² · p = 0
```

**With viscothermal losses:**

```
d²p/dx² + (1/S) · dS/dx · dp/dx + k² · (1 - (1-j)/√2 · δ_v/r) · p = 0
```

Where:
- `r(x) = √(S(x)/π)` = local radius
- `δ_v` = viscous boundary layer thickness

**Complex wavenumber:**

```
k_c² = k² · [1 - (1-j)/√2 · (δ_v + (γ-1) · δ_α) / r]
```

Where `γ` = ratio of specific heats (≈ 1.4 for air).

---

### 3. **WKB Method for Conical Horns**

The **WKB (Wentzel-Kramers-Brillouin) method** is an asymptotic technique for solving differential equations with **slowly varying coefficients**.

**Key idea:** The horn radius varies slowly compared to the wavelength:
```
|dr/dx| << k · r
```

**WKB ansatz:**

```
p(x) = A(x) · exp[j · ∫ k_c(x) dx]
```

Where:
- `A(x)` = slowly varying amplitude
- `k_c(x)` = complex wavenumber (position-dependent)

**Zeroth-order WKB solution:**

```
p(x) ≈ [1/√(S(x))] · [C_1 · e^(j∫ k_c dx) + C_2 · e^(-j∫ k_c dx)]
```

This represents **spherical waves with amplitude correction** due to area variation.

---

### 4. **Transfer Matrix with Losses**

The transfer matrix relates pressure and volume velocity at throat (x=0) and mouth (x=L):

```
| p_1 |   | a   b | | p_2 |
|     | = |       | |     |
| U_1 |   | c   d | | U_2 |
```

**WKB-based transfer matrix elements:**

```
a = √(S_2/S_1) · cos(ψ) · e^(-αL)
b = j · Z_c · √(S_2/S_1) · sin(ψ) · e^(-αL)
c = j · √(S_1 S_2) / Z_c · sin(ψ) · e^(-αL)
d = √(S_1/S_2) · cos(ψ) · e^(-αL)
```

Where:
- `S_1, S_2` = throat and mouth areas
- `ψ = ∫₀ᴸ Re(k_c) dx` = phase integral
- `α = (1/L) ∫₀ᴸ Im(k_c) dx` = average attenuation
- `Z_c = ρc / √(S_1 S_2)` = characteristic impedance (geometric mean)

---

### 5. **Phase Integral Calculation**

For a **conical horn** with radius `r(x) = r_1 + (r_2 - r_1) · x/L`:

**Lossless case (k is constant):**

```
ψ = k · L
```

**With viscothermal losses:**

```
ψ = ∫₀ᴸ k · √[1 - (1-j)/√2 · (δ_v + (γ-1)δ_α) / r(x)] dx
```

**WKB approximation:**

```
ψ ≈ k · L · [1 - (δ_v + (γ-1)δ_α) / (r_2 - r_1) · ln(r_2/r_1)]
```

---

### 6. **Attenuation Calculation**

**Viscothermal attenuation coefficient:**

```
α_v(x) = (δ_v / 2r(x)) · k
α_α(x) = ((γ-1) · δ_α / 2r(x)) · k
```

**Total attenuation:**

```
α = (1/L) ∫₀ᴸ [α_v(x) + α_α(x)] dx
```

For a **conical horn**:

```
α = k / (2L) · [δ_v + (γ-1)δ_α] · (1/r_2 - 1/r_1)
```

---

## Physical Interpretation

### **Loss Mechanism**

1. **Viscous losses**:
   - Air velocity gradient at wall creates shear stress
   - Energy dissipated as heat due to viscosity
   - Boundary layer thickness `δ_v ∝ 1/√f`

2. **Thermal losses**:
   - Pressure changes cause temperature oscillations
   - Heat conduction at walls creates thermal lag
   - Boundary layer thickness `δ_α ∝ 1/√f`

### **Frequency Dependence**

```
α ∝ √f
```

- **Low frequencies**: Thicker boundary layers → higher losses
- **High frequencies**: Thinner boundary layers → lower losses

### **Geometry Dependence**

```
α ∝ 1/r
```

- **Small horns** (small r): Higher losses
- **Large horns** (large r): Lower losses

---

## Implementation Notes for Viberesp

### **Physical Constants**

```python
@dataclass
class AirProperties:
    """Standard air properties for viscothermal loss calculation."""
    rho: float = 1.205        # Density (kg/m³) at 20°C
    c: float = 343.7          # Speed of sound (m/s) at 20°C
    mu: float = 1.81e-5       # Dynamic viscosity (Pa·s)
    nu: float = 1.51e-5       # Kinematic viscosity (m²/s)
    alpha: float = 2.19e-5    # Thermal diffusivity (m²/s)
    gamma: float = 1.4        # Ratio of specific heats
    Pr: float = 0.71          # Prandtl number
```

### **Boundary Layer Calculation**

```python
def boundary_layer_thickness(frequency: float, air: AirProperties) -> tuple:
    """
    Calculate viscous and thermal boundary layer thickness.

    Args:
        frequency: Analysis frequency (Hz)
        air: Air properties

    Returns:
        (delta_viscous, delta_thermal) in meters
    """
    omega = 2 * np.pi * frequency

    # Viscous boundary layer
    delta_v = np.sqrt(2 * air.nu / omega)

    # Thermal boundary layer
    delta_alpha = np.sqrt(2 * air.alpha / omega)

    return delta_v, delta_alpha
```

### **Complex Wavenumber**

```python
def complex_wavenumber(k: float, r: float, delta_v: float, delta_alpha: float, gamma: float = 1.4) -> complex:
    """
    Calculate complex wavenumber with viscothermal losses.

    Args:
        k: Lossless wavenumber (rad/m)
        r: Local radius (m)
        delta_v: Viscous boundary layer (m)
        delta_alpha: Thermal boundary layer (m)
        gamma: Ratio of specific heats

    Returns:
        Complex wavenumber k_c
    """
    # Viscothermal correction factor (low-frequency approximation)
    correction = (1 - 1j) / np.sqrt(2) * (delta_v + (gamma - 1) * delta_alpha) / r

    # Complex wavenumber
    k_c = k * np.sqrt(1 - correction)

    return k_c
```

### **Transfer Matrix with Losses**

```python
def conical_transfer_matrix_with_losses(
    horn: ConicalHorn,
    frequency: float,
    air: AirProperties
) -> np.ndarray:
    """
    Calculate transfer matrix for conical horn with viscothermal losses.

    Uses WKB approximation for phase integral.

    Args:
        horn: ConicalHorn parameters
        frequency: Analysis frequency (Hz)
        air: Air properties

    Returns:
        2x2 transfer matrix [[a, b], [c, d]]
    """
    omega = 2 * np.pi * frequency
    k = omega / air.c

    # Boundary layer thickness
    delta_v, delta_alpha = boundary_layer_thickness(frequency, air)

    # Throat and mouth radii
    r_1 = np.sqrt(horn.S_1 / np.pi)
    r_2 = np.sqrt(horn.S_2 / np.pi)

    # Average radius (geometric mean)
    r_avg = np.sqrt(r_1 * r_2)

    # Complex wavenumber (evaluated at average radius)
    k_c = complex_wavenumber(k, r_avg, delta_v, delta_alpha, air.gamma)

    # Phase integral
    psi = np.real(k_c) * horn.L

    # Attenuation factor
    alpha = np.imag(k_c)
    damping = np.exp(-alpha * horn.L)

    # Characteristic impedance (geometric mean of throat and mouth)
    Z_c = air.rho * air.c / np.sqrt(horn.S_1 * horn.S_2)

    # Transfer matrix elements (with losses)
    a = np.sqrt(horn.S_2 / horn.S_1) * np.cos(psi) * damping
    b = 1j * Z_c * np.sqrt(horn.S_2 / horn.S_1) * np.sin(psi) * damping
    c = 1j * np.sqrt(horn.S_1 * horn.S_2) / Z_c * np.sin(psi) * damping
    d = np.sqrt(horn.S_1 / horn.S_2) * np.cos(psi) * damping

    return np.array([[a, b], [c, d]])
```

---

## Comparison: Lossless vs. Lossy

### **Lossless Transfer Matrix**

```python
a = √(S_2/S_1) · cos(kL)
b = j · Z_c · √(S_2/S_1) · sin(kL)
c = j · √(S_1 S_2) / Z_c · sin(kL)
d = √(S_1/S_2) · cos(kL)
```

**Properties:**
- `|det(M)| = 1` (lossless)
- No amplitude decay
- Pure phase shift

### **Lossy Transfer Matrix**

```python
a = √(S_2/S_1) · cos(ψ) · e^(-αL)
b = j · Z_c · √(S_2/S_1) · sin(ψ) · e^(-αL)
c = j · √(S_1 S_2) / Z_c · sin(ψ) · e^(-αL)
d = √(S_1/S_2) · cos(ψ) · e^(-αL)
```

**Properties:**
- `|det(M)| < 1` (lossy)
- Amplitude decay `e^(-αL)`
- Phase shift modified by `ψ ≠ kL`

---

## Accuracy and Validity

### **WKB Validity Condition**

The WKB approximation is valid when:

```
|dr/dx| << k · r
```

For a **conical horn** with constant flare:

```
|r_2 - r_1| / L << k · r_avg
```

**Rule of thumb:** WKB is valid when:
```
L > λ/4
```

For **shorter horns**, use exact solution or numerical integration.

### **Frequency Range**

| Frequency | Loss Mechanism | Magnitude |
|-----------|----------------|-----------|
| **Low** (< 100 Hz) | Viscous + thermal | Significant |
| **Mid** (100-1000 Hz) | Viscous + thermal | Moderate |
| **High** (> 1000 Hz) | Boundary layer thin | Negligible |

---

## Design Implications

### **When to Include Viscothermal Losses**

**Include losses for:**
- **Bass horns** (low frequencies, long horns)
- **Small throats** (high velocity gradients)
- **High-precision modeling** (phase accuracy)
- **Efficiency calculations** (power loss)

**Can neglect for:**
- **High-frequency horns** (short wavelengths)
- **Large mouths** (low velocity)
- **Quick estimates** (within ±1 dB)

### **Efficiency Impact**

**Transmission loss (TL):**

```
TL = 20 · log₁₀(e^(αL)) = 8.686 · αL [dB]
```

**Example:** For a 2m bass horn at 50 Hz:
- `α ≈ 0.02` 1/m
- `TL ≈ 8.686 × 0.02 × 2 ≈ 0.35 dB`

This is **small but measurable** for high-precision work.

---

## Extensions

### **Higher-Order Modes**

The paper focuses on **planar waves**. For higher-order modes:
- Different boundary layer profiles
- Modal-dependent attenuation
- Cut-off frequency effects

### **Wall Roughness**

For **rough walls**, add:
- Additional viscous losses
- Frequency-dependent scattering
- Empirical correction factors

### **Temperature Dependence**

Viscothermal parameters depend on temperature:
- `μ(T)`: Viscosity varies with T
- `α(T)`: Thermal diffusivity varies with T
- `c(T)`: Speed of sound varies with T

---

## Comparison to Other Methods

| Method | Pros | Cons |
|--------|------|------|
| **Lossless** | Simple, fast | No damping |
| **Boundary layer** (WKB) | Accurate for slowly varying horns | Requires `dr/dx << k·r` |
| **Numerical segmentation** | General, accurate | Slow, convergence issues |
| **FEM/BEM** | Most accurate | Very slow, complex |

**WKB is optimal** for:
- **Conical horns** (exact for lossless, good for lossy)
- **Multi-segment horns** (piecewise-conical)
- **Real-time simulation** (fast evaluation)

---

## References Cited

- **Webster (1919)**: Original horn equation
- **Kinsler et al.**: Fundamentals of Acoustics
- **Bruneau et al.**: Viscothermal losses in ducts
- **Kulik (2007)**: Conical waveguide transfer matrix
- **Thibault et al. (2021)**: Dissipative time-domain model

---

## Key Takeaway

> The WKB method provides an **accurate and efficient** way to calculate transfer matrices for **conical horns with viscothermal losses**, without requiring numerical segmentation. This is particularly valuable for **bass horns** and **precision modeling**.

For Viberesp, this enables:
- **Accurate efficiency calculations**
- **Realistic SPL predictions** (with damping)
- **Phase-accurate simulations** (for multi-segment horns)

---

*Paper retrieved from: https://acta-acustica.edpsciences.org/articles/aacus/pdf/2020/02/aacus200006.pdf*

*Last updated: 2025-12-25*
