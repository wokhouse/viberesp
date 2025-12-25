# Passive modelling of the electrodynamic loudspeaker: from the Thiele–Small model to nonlinear port-Hamiltonian systems

**Authors**: Antoine Falaize and Thomas Hélie
**Source**: Acta Acustica, Vol. 4, Article 1 (2020)
**DOI**: 10.1051/aacus/2019001
**Open Access**: Available under Creative Commons Attribution License

---

## Summary

This paper presents a **port-Hamiltonian systems (PHS)** framework for modeling electrodynamic loudspeakers that guarantees **passivity** and **causality**. The authors reformulate the Thiele-Small model as a linear PHS, then progressively refine it to include:
- Suspension creep (viscoelasticity)
- Nonlinear stress-strain characteristics
- Magnetic saturation
- Eddy-current losses
- Position-dependent electromagnetic coupling

---

## Key Contributions

### 1. **Port-Hamiltonian Framework**

The PHS formalism provides a systematic, modular approach to modeling multiphysical systems with guaranteed passivity:

**General PHS structure:**

```
dx/dt = (J - R)∇H(x) + g u
y = gᵀ∇H(x)
```

Where:
- `x` = state variables (energy, momentum, flux)
- `H(x)` = Hamiltonian (total stored energy)
- `J` = skew-symmetric matrix (conservative coupling)
- `R` = positive semi-definite matrix (dissipation)
- `u` = inputs (voltage, force)
- `y` = outputs (current, velocity)

**Power balance:**

```
dH/dt + P_D = P_S
```

Where `P_D` is dissipated power and `P_S` is supplied power. This guarantees **passive** and **stable** simulations.

---

### 2. **Model 0: Thiele-Small as PHS**

**State variables:**

```
x = [ϕ_C, p_M, q_D]ᵀ
```

- `ϕ_C` = magnetic flux in coil (electrical energy)
- `p_M` = mechanical momentum = M<sub>CDA</sub> · dq<sub>D</sub>/dt
- `q_D` = diaphragm displacement from equilibrium

**Hamiltonian (energy):**

```
H(x) = ϕ_C² / (2L_C) + p_M² / (2M<sub>CDA</sub>) + K<sub>SA</sub> q_D² / 2
```

**Dissipation variables:**

```
w = [i_C, dq_D/dt]ᵀ
z(w) = diag(R_C, R_SA) · w
```

**Equations of motion:**

```
dϕ_C/dt = -R_C · i_C + Bℓ · dq_D/dt + u_e
dp_M/dt = Bℓ · i_C - R_SA · dq_D/dt - K<sub>SA</sub> q_D
dq_D/dt = p_M / M<sub>CDA</sub>
```

Where `Bℓ` is the force factor (Bl product).

---

### 3. **Model 1: Refined Mechanics**

#### **3.1 Suspension Creep (Viscoelasticity)**

The Kelvin-Voigt model describes the **long-term memory** of suspension materials:

**Compliance function:**

```
T_ve(s) = 1/K_0 + 1/(K_1 + s·R_1)
```

Where:
- `K_0` = primary (instantaneous) stiffness
- `K_1` = secondary stiffness (creep element)
- `R_1` = viscosity damper
- Characteristic time: `τ_ve = 2π/K_1R_1`

**Physical interpretation:**
- At low frequencies: suspension appears **softer** (compliance increases)
- At high frequencies: Thiele-Small prediction restored
- Exhibits **long time memory** (creep effect)

**State expansion for creep:**

```
x = [p_M, q_0, q_1]ᵀ
```

- `q_D = q_0 + q_1` = total displacement
- `q_0` = primary elongation (instantaneous spring K_0)
- `q_1` = creep elongation (spring K_1 in series with damper R_1)

**Hamiltonian with creep:**

```
H(x) = p_M² / (2M<sub>CDA</sub>) + K_0 q_0² / 2 + K_1 q_1² / 2
```

#### **3.2 Nonlinear Suspension Hardening**

For large displacements, the suspension stiffens (hardening spring):

**Nonlinear constitutive law:**

```
c_SA(q_0) = q_0 + 4P_sat q_sat / (π) · tan(π q_0 / (2q_sat))
```

**Associated energy function:**

```
H_sat(q_0) = K_0 q_0² / 2 + 8P_sat K_0 q_sat / (4π) · ln[cos(π q_0 / (2q_sat))] + (π/2)(q_0/q_sat)²
```

Where:
- `q_sat` = displacement at which material breakdown occurs
- `P_sat` = shape parameter controlling nonlinearity strength

**Result:** Restoring force increases faster than linear for large `q_0`.

---

### 4. **Model 2: Refined Electromagnetics**

#### **4.1 Coil Model**

**Leakage inductance:**

The coil winding has a **linear leakage inductance** associated with flux that doesn't penetrate the pole piece:

```
L_leak = N_C² · C_leak
C_leak = S_leak / [ℓ_0 · μ_0 · (1 + χ_air)² · A_C]
```

Where:
- `S_leak` = annular surface between coil and core
- `A_C` = coil height
- `ℓ_0` = vacuum magnetic permeability
- `χ_air` = air magnetic susceptibility
- `N_C` = number of wire turns

**Position-dependent coupling:**

The effective number of turns `n_P` surrounding the pole piece varies with coil position:

```
n_P(q_D) = N_C / [1 + exp(-4(q_D - q_center) / (q_+ - q_-))]
```

This models how the coil **leaves the magnetic gap** at large displacements.

#### **4.2 Magnetic Saturation**

The pole piece exhibits **nonlinear magnetic excitation-induction**:

**Constitutive law (tangent-type):**

```
c_PG(ϕ_PG) = P_lin ϕ_PG + 4P_sat ϕ_sat / π · tan(π ϕ_PG / (2ϕ_sat))
```

**Energy function:**

```
H_sat(ϕ_PG) = (P_lin/2) ϕ_PG² + 8P_sat ϕ_sat / (4π) · ln[cos(π ϕ_PG / (2ϕ_sat))] + (π/2)(ϕ_PG/ϕ_sat)²
```

Where:
- `ϕ_PG` = magnetic flux in pole piece + air gap
- `ϕ_sat` = saturation flux (alignment of magnetic moments)
- `P_lin` = linear permeability coefficient
- `P_sat` = saturation strength

**Blocked impedance (high frequency):**

```
Z_C(s) = R_C + s·L_leak + n_P(q_D)² · R_ec · C_ss · s / (R_ec · C_ss · s + 1)
```

Where `R_ec` and `C_ss` describe eddy-current effects.

#### **4.3 Eddy-Current Losses**

**Linear magnetic resistance:**

```
Z_ec(s) = R_ec
τ_ec = R_ec · C_ss
```

**Effects:**
- Power dissipation (Joule heating)
- Added inductive effect
- **Skin effect**: field lines pushed toward boundary

**Characteristic time `τ_ec`** determines the frequency range where eddy currents matter.

#### **4.4 Position-Dependent Force Factor**

The force factor `Bℓ` depends on:
1. **Coil position** (length of wire in gap)
2. **Magnetic flux** (saturation in pole piece)

**Effective length model:**

```
ℓ_C(q_D) = ℓ_C0 / [1 + exp(-P_ℓ(q_D - Q_ℓ))]
```

**Force factor:**

```
Bℓ(q_D, ϕ_PG) = (ϕ_PG / S_G) · ℓ_C(q_D)
```

Where `S_G` is the air gap cross-section.

---

## Complete Model 2 Structure

**State variables (4 storage elements):**

```
x = [x_leak, ϕ_PG, p_M, q_D]ᵀ
```

- `x_leak` = leakage flux state (N_C · ϕ_leak)
- `ϕ_PG` = magnetic flux in pole piece + gap
- `p_M` = mechanical momentum
- `q_D` = diaphragm displacement

**Hamiltonian:**

```
H(x) = x_leak² / (2L_leak) + 0 + p_M² / (2M<sub>CDA</sub>) + K_SA q_D² / 2 + H_sat(ϕ_PG)
```

**Dissipation (3 elements):**

```
w = [i_C, dq_D/dt, w_PG]ᵀ
z(w) = diag(R_C, R_SA, R_ec⁻¹) · w
```

**Inputs (2 ports):**

```
u = [v_I, w_M]ᵀ
```

- `v_I` = input voltage
- `w_M` = magnetomotive force from permanent magnet

**Outputs (2 ports):**

```
y = [i_C, dϕ_PG/dt]ᵀ
```

---

## Key Physical Phenomena Modeled

| Phenomenon | Linear/Nonlinear | Frequency Dependence | Model Element |
|------------|-----------------|---------------------|---------------|
| Suspension creep | Linear (memory) | Low-frequency softening | Kelvin-Voigt chain |
| Suspension hardening | Nonlinear | Large displacement | Saturating spring |
| Magnetic saturation | Nonlinear | High flux | Nonlinear capacitor |
| Eddy currents | Linear | High-frequency losses | Magnetic resistance |
| Position-dependent Bl | Nonlinear | Large displacement | Sigmoid modulation |

---

## Implementation Notes for Viberesp

### **Numerical Integration**

The paper uses a **passivity-preserving discretization** based on the **discrete gradient**:

```python
def discrete_gradient(H, x_k, x_k1):
    """Discrete gradient preserving passivity."""
    dx = x_k1 - x_k

    for i, (H_i, x_i, x_i1) in enumerate(zip(H, x_k, x_k1)):
        if dx[i] != 0:
            grad[i] = (H_i.subs(x, x_i1) - H_i.subs(x, x_i)) / dx[i]
        else:
            grad[i] = dH_i/dx.subs(x, x_i)

    return grad
```

**Euler-like scheme with modified gradient:**

```python
dx = dt * ((J - R) @ discrete_gradient(H, x_k, x_k1) + G @ u_k)
```

This preserves the **power balance** in discrete time, ensuring numerical stability.

### **Model Hierarchy**

```python
# Model 0: Linear Thiele-Small
@dataclass
class TSModel:
    """Thiele-Small model parameters."""
    R_C: float      # Coil resistance (Ω)
    L_C: float      # Coil inductance (H)
    M_CDA: float    # Moving mass (kg)
    K_SA: float     # Suspension stiffness (N/m)
    R_SA: float     # Mechanical damping (N·s/m)
    Bl: float       # Force factor (T·m)

# Model 1: + Creep + Nonlinear suspension
@dataclass
class Model1(TSModel):
    """Model 0 with viscoelastic creep and hardening."""
    K_0: float      # Primary stiffness (N/m)
    K_1: float      # Creep stiffness (N/m)
    R_1: float      # Creep damping (N·s/m)
    q_sat: float    # Saturation displacement (m)
    P_sat: float    # Hardening parameter

# Model 2: + Refined electromagnetics
@dataclass
class Model2(Model1):
    """Model 1 with electromagnetic refinements."""
    L_leak: float   # Leakage inductance (H)
    R_ec: float     # Eddy-current resistance (Ω)
    C_ss: float     # Steady-state capacitance (F)
    phi_sat: float  # Saturation flux (Wb)
    P_lin: float    # Linear permeability
    P_magsat: float # Saturation strength
    S_G: float      # Air gap area (m²)
    ell_C0: float   # Total wire length (m)
    Q_ell: float    # Coil overhang (m)
    P_ell: float    # Shape parameter
    N_C: int        # Number of turns
    q_center: float # Sigmoid center
    q_plus: float   # Sigmoid width
```

### **Frequency-Dependent Parameters**

**Viscoelastic compliance:**

```python
def suspension_compliance(omega, K_0, K_1, R_1):
    """Frequency-dependent compliance from Kelvin-Voigt model."""
    T_0 = 1 / K_0
    T_1 = 1 / (K_1 + 1j * omega * R_1)
    return T_0 + T_1
```

**Eddy-current impedance:**

```python
def eddy_impedance(omega, R_ec, C_ss):
    """Frequency-dependent magnetic impedance."""
    s = 1j * omega
    return R_ec / (1 + s * R_ec * C_ss)
```

---

## Comparison to Thiele-Small

| Aspect | Thiele-Small | PHS Refinements |
|--------|--------------|----------------|
| Suspension | Linear K<sub>SA</sub> | Viscoelastic + hardening |
| Inductance | Single L<sub>C</sub> | Leakage + magnetic path |
| Force factor | Constant Bl | Position + flux dependent |
| Magnetic losses | Neglected | Eddy currents (R<sub>ec</sub>) |
| Passivity | Not guaranteed | Structured into equations |
| Numerical stability | Method-dependent | Guaranteed by structure |

---

## Experimental Validation

The paper presents simulations showing:

1. **Creep effect**: Suspension compliance increases at low frequencies (Fig. 7)
2. **Long-term memory**: Step response shows slow relaxation (Fig. 8)
3. **Hardening**: Large displacements produce nonlinear restoring force (Fig. 9)
4. **Eddy-currents**: Flux changes with characteristic time τ<sub>ec</sub> (Fig. 14)
5. **Saturation**: High-frequency impedance depends on DC bias (Fig. 15)
6. **Position effects**: Impedance varies with coil position (Fig. 16)

All results **qualitatively match measured data** from cited literature.

---

## Advantages for Viberesp

### **1. Guaranteed Passivity**

The PHS structure ensures:
- Stable simulations (no unbounded growth)
- Causality preserved
- Power balance satisfied at every timestep

### **2. Modular Design**

Each physical phenomenon is a **component** that can be:
- Added/removed independently
- Combined with others
- Identified separately from measurements

### **3. Systematic Refinement**

Start with Thiele-Small (Model 0), then add:
- Model 1: Creep + hardening
- Model 2: Electromagnetic refinements
- Combine all for complete model

### **4. Real-Time Applications**

The passive-guaranteed numerical scheme enables:
- Real-time DSP simulation
- Distortion compensation
- Burn-out protection

---

## Open-Source Implementation

The authors mention **PyPHS** software:
- https://github.com/pyphs/pyphs
- Python implementation of PHS
- Automatic equation generation from network graphs

---

## References Cited

**Thiele-Small papers:**
- Thiele (1971): Vented boxes
- Small (1972): Closed-box analysis
- Small (1973): Closed-box synthesis

**Nonlinear phenomena:**
- Klippel (2006): Tutorial on nonlinearities
- Agerkvist (2011): Nonlinear viscoelastic models
- Pedersen (2008): Error correction
- Thorborg et al. (2010): Frequency-dependent damping

**Eddy currents:**
- Vanderkooy (1988): Eddy currents in pole piece
- Wright (1990): Empirical impedance model
- Kong et al. (2015): Lossy inductance

---

## Appendix: Key Formulas

### **Discrete Gradient (Euler-like)**

```python
def rdH(x_k, x_k1, H):
    """Discrete gradient preserving passivity."""
    grad = np.zeros_like(x_k)

    for i in range(len(x_k)):
        dx = x_k1[i] - x_k[i]
        if abs(dx) > 1e-10:
            # Midpoint rule for quadratic Hamiltonian
            grad[i] = (x_k1[i] + x_k[i]) / (2 * C_i)
        else:
            # Analytical derivative at x_k
            grad[i] = dH_i_dx(x_k[i])

    return grad
```

### **Power Balance (Discrete)**

```
0 = dH/dt + P_D + P_S
```

Where:
- `dH/dt = ∇H(x)ᵀ · dx/dt`
- `P_D = z(w)ᵀ · w ≥ 0` (dissipated)
- `P_S = -uᵀ · y` (supplied)

---

*Paper retrieved from: https://acta-acustica.edpsciences.org/articles/aacus/pdf/2020/01/aacus190001s.pdf*

*Last updated: 2025-12-25*
