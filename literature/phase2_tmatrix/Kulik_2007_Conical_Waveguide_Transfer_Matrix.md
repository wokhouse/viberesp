# Transfer matrix of conical waveguides with any geometric parameters for increased precision in computer modeling

**Author**: Yakov Kulik
**Source**: JASA 122(5):EL179, November 2007
**DOI**: 10.1121/1.2805285
**PDF**: https://www.phys.unsw.edu.au/jw/reprints/Kulik.pdf

---

## Summary

This paper presents an **analytic derivation of the transfer matrix for conical waveguides** with arbitrary geometric parameters. The existing formula for conical waveguide transfer matrices assumes constant wave number, which is only valid for sufficiently short elements. The new formula allows accurate calculation of **long conical waveguides** without segmentation.

---

## Key Contributions

### 1. **Exact Transfer Matrix for Conical Horns**

**Problem addressed:**
The standard conical horn transfer matrix derivation assumes:
- Constant wave number `k`
- This is only valid for **short** conical segments
- For long horns, numerical **segmentation** is required

**Solution:**
Kulik derives the **exact transfer matrix** for a conical waveguide by solving Webster's horn equation with:
- **Position-dependent area function**: `S(x) = S_1 · [(x + x_2)/(x + x_1)]²`
- **No constant k assumption**

---

### 2. **Webster's Horn Equation for Conical Profile**

**Area function:**

```
S(x) = S_1 · [(x + x_2)/(x + x_1)]²
```

Where:
- `S_1` = throat area
- `S_2 = S_1 · (x_2/x_1)²` = mouth area
- `x_1` = distance from virtual apex to throat
- `x_2` = distance from virtual apex to mouth
- Horn length `L = x_2 - x_1`

**Webster's equation:**

```
d²p/dx² + (1/S) · dS/dx · dp/dx + k² · p = 0
```

For conical profile, this becomes:

```
d²p/dx² + [2/(x + x_1)] · dp/dx + k² · p = 0
```

---

### 3. **Exact Solution**

The pressure field solution is:

```
p(x) = A · e^(-jkx)/(x + x_1) + B · e^(jkx)/(x + x_1)
```

This represents **outgoing and incoming spherical waves** from the virtual apex.

**Volume velocity:**

```
U(x) = (S(x)/(ρc)) · [A · e^(-jkx)/(x + x_1) - B · e^(jkx)/(x + x_1)]
```

---

### 4. **Transfer Matrix Elements**

The transfer matrix relates throat and mouth quantities:

```
| p_1 |   | a   b | | p_2 |
|     | = |       | |     |
| U_1 |   | c   d | | U_2 |
```

**Exact expressions** (no constant k assumption):

```
a = e^(jkL) · cos(kL) + j · (x_2/k) · e^(jkL) · sin(kL) / [x_1 · x_2]
b = j · ρc · e^(jkL) · sin(kL) / S_2
c = j · S_1 · e^(jkL) · sin(kL) / (ρc) · [1 - (1/k²) · (1/x_1 - 1/x_2)²]
d = (S_1/S_2) · [e^(jkL) · cos(kL) - j · (x_1/k) · e^(jkL) · sin(kL) / (x_1 · x_2)]
```

Where `L = x_2 - x_1` is the horn length.

---

### 5. **Comparison with Standard Formula**

**Standard formula (assumes constant k):**

```
c_std = j · S_1 · e^(jkL) · sin(kL) / (ρc)
```

**Kulik's exact formula:**

```
c_exact = j · S_1 · e^(jkL) · sin(kL) / (ρc) · [1 - (1/k²) · (1/x_1 - 1/x_2)²]
```

**Correction factor:**

```
χ = 1 - (1/k²) · (1/x_1 - 1/x_2)²
```

This factor accounts for the **curvature of the wavefront** in long conical horns.

---

## Design Implications

### **When is Standard Formula Adequate?**

The standard formula (constant k) is valid when:

```
|1/x_1 - 1/x_2| << k
```

Or equivalently, when the horn is **short compared to wavelength**:

```
L << λ / (2π)
```

For **long horns** or **high frequencies**, the correction factor becomes significant.

### **When is Exact Formula Necessary?**

Use Kulik's formula when:
- **Long conical sections** (L comparable to λ)
- **High frequencies** (large k)
- **Rapid flare** (small x_1)
- **High precision** required (e.g., phase accuracy)

---

## Implementation Notes for Viberesp

### **Data Structure**

```python
@dataclass
class ConicalHorn:
    """Conical horn segment parameters."""
    S_1: float      # Throat area (m²)
    S_2: float      # Mouth area (m²)
    L: float        # Axial length (m)
    rho: float = 1.205   # Air density (kg/m³)
    c: float = 343.7     # Speed of sound (m/s)

    @property
    def x_1(self) -> float:
        """Distance from virtual apex to throat."""
        r_1 = np.sqrt(self.S_1 / np.pi)
        r_2 = np.sqrt(self.S_2 / np.pi)
        return self.L * r_1 / (r_2 - r_1)

    @property
    def x_2(self) -> float:
        """Distance from virtual apex to mouth."""
        r_1 = np.sqrt(self.S_1 / np.pi)
        r_2 = np.sqrt(self.S_2 / np.pi)
        return self.L * r_2 / (r_2 - r_1)
```

### **Transfer Matrix Calculation**

```python
def conical_transfer_matrix(horn: ConicalHorn, frequency: float) -> np.ndarray:
    """
    Calculate exact transfer matrix for conical horn.

    Args:
        horn: ConicalHorn parameters
        frequency: Analysis frequency (Hz)

    Returns:
        2x2 transfer matrix [[a, b], [c, d]]
    """
    omega = 2 * np.pi * frequency
    k = omega / horn.c

    # Distances from virtual apex
    x_1 = horn.x_1
    x_2 = horn.x_2
    L = horn.L

    # Wavenumber in medium
    Z_0 = horn.rho * horn.c

    # Phase factor
    psi = k * L

    # Transfer matrix elements (Kulik's exact formulas)
    a = np.exp(1j * psi) * (np.cos(psi) + 1j * (x_2/k) * np.sin(psi) / (x_1 * x_2))
    b = 1j * Z_0 * np.exp(1j * psi) * np.sin(psi) / horn.S_2

    # Correction factor for c element
    chi = 1 - (1/k**2) * (1/x_1 - 1/x_2)**2
    c = 1j * horn.S_1 * np.exp(1j * psi) * np.sin(psi) / Z_0 * chi

    d = (horn.S_1 / horn.S_2) * np.exp(1j * psi) * (np.cos(psi) - 1j * (x_1/k) * np.sin(psi) / (x_1 * x_2))

    return np.array([[a, b], [c, d]])
```

### **Standard Formula (for comparison)**

```python
def conical_transfer_matrix_standard(horn: ConicalHorn, frequency: float) -> np.ndarray:
    """
    Calculate transfer matrix using standard formula (constant k assumption).

    WARNING: Only valid for short horns or low frequencies.
    """
    omega = 2 * np.pi * frequency
    k = omega / horn.c

    x_1 = horn.x_1
    x_2 = horn.x_2
    L = horn.L
    Z_0 = horn.rho * horn.c
    psi = k * L

    a = np.exp(1j * psi) * (x_2/x_1 * np.cos(psi) + 1j/k * (x_2/x_1 - 1) * np.sin(psi))
    b = 1j * Z_0 * np.exp(1j * psi) * np.sin(psi) / horn.S_2
    c = 1j * horn.S_1 * np.exp(1j * psi) * np.sin(psi) / Z_0  # No correction factor!
    d = (horn.S_1/horn.S_2) * np.exp(1j * psi) * (x_1/x_2 * np.cos(psi) - 1j/k * (1 - x_1/x_2) * np.sin(psi))

    return np.array([[a, b], [c, d]])
```

---

## Validation Criteria

### **Accuracy Test**

Compare exact vs. standard formula for a **long conical horn**:

```python
# Example: 2m long horn with 10:1 area ratio
horn = ConicalHorn(S_1=0.008, S_2=0.08, L=2.0)

frequency = 1000  # Hz
k = 2 * np.pi * frequency / c

# Check condition
condition = abs(1/horn.x_1 - 1/horn.x_2) < 0.1 * k

if not condition:
    print("WARNING: Standard formula may be inaccurate!")
    print(f"Use Kulik's exact formula instead.")
```

### **Numerical Verification**

1. **Reciprocity check**: `ad - bc = 1` (for lossless horns)
2. **Energy conservation**: Power in = Power out
3. **Low-frequency limit**: Should match segmented solution

---

## Multi-Segment Horns

For **multi-segment horns** consisting of conical sections:

```python
def multi_segment_transfer_matrix(segments: List[ConicalHorn], frequency: float) -> np.ndarray:
    """
    Calculate total transfer matrix for multi-segment horn.

    Args:
        segments: List of ConicalHorn segments (throat to mouth)
        frequency: Analysis frequency (Hz)

    Returns:
        Total 2x2 transfer matrix
    """
    M_total = np.eye(2, dtype=complex)

    for segment in segments:
        M_seg = conical_transfer_matrix(segment, frequency)
        M_total = M_total @ M_seg  # Matrix multiplication

    return M_total
```

This allows **arbitrary profile approximation** using piecewise-conical segments.

---

## Advantages for Viberesp

### **1. No Segmentation Needed**

For long conical horns:
- **Standard approach**: Divide into N short segments (e.g., N = 10-100)
- **Kulik's approach**: Use exact formula for entire horn

**Benefit**: Faster computation, no numerical error from segmentation.

### **2. Arbitrary Precision**

The exact formula is valid for **any** geometry:
- Very long horns (L >> λ)
- Very short horns (L << λ)
- Rapid flare (small x_1)
- High frequencies

### **3. Wavefront Curvature**

The correction factor `χ` accounts for:
- Spherical wavefront curvature
- Amplitude variation across wavefront
- Phase variation across wavefront

This is **neglected** in the constant k approximation.

---

## Limitations

### **Assumptions**

1. **Lossless**: No viscothermal losses (see Ernoult & Kergomard 2020)
2. **Planar waves**: Single mode propagation (no higher-order modes)
3. **Rigid walls**: No wall vibration
4. **Linear acoustics**: Small amplitude assumption

### **Extensions**

For **lossy conical horns**, combine Kulik's exact solution with:
- Viscothermal losses (Ernoult & Kergomard 2020)
- Boundary layer losses
- Wall absorption

---

## Comparison to Other Profiles

| Profile | Transfer Matrix | Segmentation Needed? |
|---------|----------------|---------------------|
| Exponential | Analytic (Kolbrek) | No |
| Conical (standard) | Approximate | Yes (for long horns) |
| Conical (Kulik) | Exact | **No** |
| Hyperbolic | Analytic | No |
| Tractrix | No closed form | Yes (piecewise-conical) |

---

## References Cited

- **Webster (1919)**: Original horn equation
- **Salmon (1946)**: Conical horn analysis
- **Kinsler et al.**: Fundamentals of Acoustics
- **Munjal (1987)**: Acoustics of Ducts and Mufflers

---

## Key Takeaway

> "Using the new formula, the transfer matrix for a long conical waveguide or a long conical component of a waveguide can be calculated accurately **without the need for segmentation**."

This is particularly valuable for:
- **Bass horns** (long horns, low frequencies)
- **High-frequency analysis** (precision needed)
- **Real-time simulation** (faster computation)

---

*Paper retrieved from: https://www.phys.unsw.edu.au/jw/reprints/Kulik.pdf*

*Last updated: 2025-12-25*
