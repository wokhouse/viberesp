# Webster's Horn Equation Revisited

**Author**: S.W. Rienstra
**Source**: SIAM Journal on Applied Mathematics, 65(6), 1981-2004
**Year**: 2005
**DOI**: 10.1137/S0036139902413040

---

## Abstract

The problem of low-frequency sound propagation in slowly varying ducts is systematically analyzed as a perturbation problem of slow variation. Webster's horn equation and variants in bent ducts, in ducts with nonuniform sound speed, and in ducts with irrotational mean flow, with and without lining, are derived, and the entrance/exit plane boundary layer is given. It is shown why a varying lined duct in general does not have an (acoustic) solution.

---

## Key Contributions

### 1. Systematic Derivation of Webster's Equation

Unlike the traditional derivation based on assuming uniform pressure across the duct cross-section, Rienstra provides an **asymptotically sound derivation** using:
- Method of slow variation
- Matched asymptotic expansions
- Explicit error quantification

### 2. Webster's Horn Equation

The classic equation:

```
A⁻¹(A·φ_X)_X + κ²φ = 0
```

where:
- `A(X)` = duct cross-sectional area
- `φ(X)` = acoustic potential
- `κ` = wavenumber (scaled)
- `X` = slow axial variable

**Alternative form** (transformation to ψ):

```
A(X) = d(X)²
φ = d⁻¹·ψ

ψ'' + (κ² - d''/d)ψ = 0
```

**Key insight**: The sign of `κ² - d''/d` determines:
- **Positive**: Propagating waves
- **Negative**: Exponential decay (evanescent)

### 3. Salmon's Family of Horns

Elementary solutions exist when `d''/d = m²` (constant):
- **Exponential horns**: `S(x) = S₁·e^(2mx)`
- **Conical horns**: `S(x) = S₁·(1 + x/X)²`

---

## Classical Problem Derivation

### Geometry

Cylindrical coordinates with duct radius `R(X,θ)`:
```
Σ(X,r,θ) = r - R(X,θ) ≤ 0
```

where `X = εx` is the **slow variable**.

### Helmholtz Equation

```
∇²φ + ε²κ²φ = 0    if x ∈ V
∇φ·n = 0           if x ∈ ∂V
```

### Asymptotic Expansion

```
φ(X,r,θ;ε) = φ₀(X,r,θ) + ε·φ₁(X,r,θ) + ε²·φ₂(X,r,θ) + ...
```

### Leading Order (O(1))

```
∇⊥²φ₀ = 0
with ∇⊥φ₀·n⊥ = 0 at r = R
```

**Solution**: `φ₀ = φ₀(X)` (constant across cross-section)

### Second Order (O(ε²))

Integrate over cross-section `A(X)` and apply Gauss's theorem:

```
A⁻¹(A·φ₀_X)_X + κ²φ₀ = 0
```

This is **Webster's horn equation**.

---

## Entrance Boundary Layer

### The Problem

Near the entrance plane `x = 0`, the outer (Webster) solution cannot satisfy the `r`-dependent boundary condition. A **boundary layer** of thickness `x = O(1)` (i.e., `X = O(ε)`) forms.

### Inner Solution (Laplace Equation)

```
∇²Φ₀ = 0
Φ₀(0,r,θ) = F(r,θ)  (given source)
```

### Matching Conditions

At `X → 0` (outer) matches `x → ∞` (inner):

```
φ₀(0) = F₀         (average of source)
φ₁(0) = Σₙ Fₙ/λₙ ∫ RR_X ψₙ|_r=R dη   (depends on source shape)
```

**Key result**: `φ₁ = 0` when:
- Source is a simple piston `F = F₀` (uniform)
- Duct starts smoothly `R_X = 0`
- Only symmetric modes are excited

---

## Curved Ducts

**Result**: For duct curvature radius `~ O(ε⁻¹)`, Webster's equation remains **unchanged**.

Example: Perturbed torus with centerline radius `ε⁻¹` and tube radius `R`:
```
x = ε⁻¹(1 + εr·cosθ)cos(εξ)
y = ε⁻¹(1 + εr·cosθ)sin(εξ)
z = r·sinθ
```

**Asymptotic analysis**: The Laplacian is unchanged to `O(ε³)`.

---

## Impedance Walls

### Key Finding

For lined ducts with impedance `Z`:

#### Case 1: `Z = O(1)` (Typical lining)
**Only trivial solution exists**: `φ₀ = φ₁ = ... = 0`

#### Case 2: `Z = O(ε)` (Very small impedance)
**Eigenvalue problem**: Solutions exist only for discrete values of `ζ = 1/Z`.

For a **circular duct** with `Z = O(ε)`:
```
φ₀ = f(X)(r/R)^m {cos(mθ); sin(mθ)}
with ζ = m/R
```

**Critical limitation**: Since `ζ` varies along the duct, **no nonzero solution exists** for the full duct (except for constant cross-section).

---

## Variable Sound Speed

When sound speed `C = C(X,r,θ)` and density `D = D(X,r,θ)` vary slowly:

**Generalized Webster's equation**:
```
A⁻¹(A·Ĉ²·p₀_X)_X + Ω²p₀ = 0
```

where `Ĉ² = (1/A)∬ C² dσ` (cross-sectional average)

**Alternative form**:
```
A(X)·C²(X) = d(X)²
p₀ = d⁻¹·ψ

ψ'' + (Ω²/C² - d''/d)ψ = 0
```

---

## Mean Flow

### Irrotational Isentropic Flow

For **potential mean flow** with velocity `V` and sound speed `C`:

**Generalized convected wave equation**:
```
D⁻¹∇·(D∇φ) - (iΩ + V·∇)[C⁻²(iΩ + V·∇)φ] = 0
```

**Reduced to Webster form** (after cross-sectional averaging):
```
(D₀A)⁻¹(D₀A·φ₀_X)_X = (iΩ + U₀·∂_X)[C₀⁻²(iΩ + U₀·∂_X)φ₀]
```

where `U₀(X)` is the mean axial velocity.

### Mean Flow + Impedance Walls

**Result**: For `Z = O(1)`, only **hydrodynamic (non-acoustic) solutions** exist:
```
p₀ = constant · [1/(U₀D₀L)] · exp(-i∫^X Ω/U₀(ξ) dξ)
```

This convects at **mean flow velocity**, not sound speed.

---

## Key Constants and Scaling

| Parameter | Definition |
|-----------|------------|
| `ε` | Helmholtz number = ratio of wavelength to duct diameter |
| `X` | Slow variable = `ε·x` |
| `κ` | Wavenumber = `ε·k` |
| `Ω` | Frequency = `ε·ω` |
| `A(X)` | Cross-sectional area |

---

## Important Results Summary

### 1. Validity of Webster's Equation

**Conditions**:
- Low Helmholtz number (`ε << 1`)
- Slow duct variation (`X = ε·x`)
- Hard walls or specific impedance values

**Error**: `O(ε)` or `O(ε²)` depending on source configuration

### 2. Boundary Layer Structure

- **Thickness**: `x = O(1)` near entrance
- **Matching**: Determines initial conditions for outer solution
- **First-order term**: `φ₁(0)` depends on source shape and duct geometry

### 3. Lined Ducts

- **Varying impedance**: Generally **no solution** (discrete spectrum problem)
- **Constant cross-section**: Solutions exist for special impedance values

### 4. Mean Flow Effects

- **Potential flow**: Modifies effective wave speed
- **Lined ducts with flow**: Only hydrodynamic waves for `Z = O(1)`

---

## Comparison with Other Derivations

| Aspect | Traditional Derivation | Rienstra's Approach |
|--------|----------------------|---------------------|
| Pressure uniformity | Assumed | Derived from asymptotics |
| Small parameter | Implicit | Explicit (`ε = ka`) |
| Error estimate | None | Quantified (`O(ε)`) |
| Boundary layer | Not addressed | Solved via matching |
| Lined ducts | Not treated | Discrete spectrum problem |

---

## References Cited

1. **Webster (1919)**: Original horn equation
2. **Salmon (1946)**: Generalized plane wave horn theory
3. **Lesser & Crighton (1975)**: Matched asymptotic expansions in acoustics
4. **Eisner (1967)**: Complete solutions of Webster equation
5. **Myers (1980)**: Impedance boundary condition with flow

---

## Practical Implications for Horn Design

### 1. When Webster's Equation is Valid

```
Condition: ka << 1 and λ ~ L
```

where:
- `k` = wavenumber
- `a` = typical duct radius
- `λ` = wavelength
- `L` = duct length scale

### 2. Boundary Conditions

For accurate simulation, match:
- **Throat**: Driver velocity profile (determines `φ₀(0)`, `φ₁(0)`)
- **Mouth**: Radiation impedance (circular piston in infinite baffle)

### 3. Numerical Implementation

Webster's equation can be solved by:
- **Analytical methods** (for exponential, conical, hyperbolic horns)
- **Numerical integration** (arbitrary profiles)
- **Multi-segment approximation** (piecewise exponential/conical)

### 4. Limitations

**Not valid for**:
- High frequencies (`ka ~ 1`): Need full wave equation
- Rapid area changes: Need boundary layer corrections
- Lined ducts with varying impedance: Generally no solution
- Strong mean flow: Need full CFD

---

*This paper provides the mathematical foundation for modern horn simulation and explains the range of validity of Webster's equation.*
