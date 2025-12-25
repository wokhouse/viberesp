# Closed-Box Loudspeaker Systems Part I: Analysis

**Author**: Richard H. Small
**Source**: Journal of the Audio Engineering Society, Vol. 20, No. 10 (Dec. 1972)
**DOI**: 10.17743/jaes.1972.634

---

## Summary

This paper provides the foundational analysis of closed-box (acoustic suspension) loudspeaker systems. It establishes the relationships between Thiele-Small parameters and system performance, enabling direct synthesis of closed-box systems from specifications.

---

## Key Contributions

### 1. **System Parameters Analysis**

The paper defines the key parameters governing closed-box system behavior:

- **f<sub>C</sub>**: System resonance frequency (Hz)
- **Q<sub>TC</sub>**: Total system Q (dimensionless)
- **V<sub>AS</sub>**: Driver equivalent volume of air compliance (L or m³)
- **V<sub>B</sub>**: Enclosure net internal volume (L or m³)
- **η<sub>0</sub>**: Reference efficiency (%)

### 2. **Compliance Ratio (α)**

The **compliance ratio** is the fundamental design parameter:

```
α = V<sub>AS</sub> / V<sub>B</sub>
```

**Air-suspension systems**: α ≥ 3 to 4
**Conventional systems**: α < 3

### 3. **System-Driver Relationships**

For zero source resistance amplifiers:

```
Q<sub>TC</sub> / Q<sub>TS</sub> ≈ Q<sub>EC</sub> / Q<sub>ES</sub> = f<sub>C</sub> / f<sub>S</sub> = (α + 1)<sup>½</sup>
```

Where:
- Q<sub>TS</sub> = Q<sub>ES</sub> · Q<sub>MS</sub> / (Q<sub>ES</sub> + Q<sub>MS</sub>)
- f<sub>S</sub>: Driver free-air resonance
- Q<sub>ES</sub>: Electrical Q
- Q<sub>MS</sub>: Mechanical Q

### 4. **Reference Efficiency**

The reference efficiency (half-space acoustic power efficiency):

```
η<sub>0</sub> = (ρ<sub>0</sub> / 2πc) · (4π² / S<sub>D</sub>) · f<sub>S</sub><sup>3</sup> · V<sub>AS</sub> / Q<sub>ES</sub>
```

Where:
- ρ<sub>0</sub> = 1.205 kg/m³ (air density)
- c = 343.7 m/s (speed of sound)
- S<sub>D</sub> = Diaphragm area (m²)

### 5. **System Response Functions**

The closed-box system behaves as a **second-order high-pass filter**:

**Normalized displacement**:

```
|X(jω)| = (f<sub>C</sub> / f)<sup>2</sup> / { [1 - (f<sub>C</sub> / f)<sup>2</sup>]<sup>2</sup> + [ω / (Q<sub>TC</sub> · f<sub>C</sub>)]<sup>2</sup> }<sup>½</sup>
```

**Normalized pressure response**:

```
|G(jω)| = (f / f<sub>C</sub>)<sup>2</sup> · |X(jω)|
```

### 6. **Alignment Types**

The paper categorizes system responses by Q<sub>TC</sub>:

| Alignment | Q<sub>TC</sub> | f<sub>3</sub>/f<sub>C</sub> | Characteristics |
|-----------|--------------|-------------------|------------------|
| Bessel (BL2) | 0.577 | 1.272 | Maximally flat delay |
| Butterworth (B2) | 0.707 | 1.000 | Maximally flat amplitude |
| Critically damped | 0.500 | 1.554 | No overshoot |
| Chebyshev (C2) | > 0.707 | < 1.000 | Peaked response |

**f<sub>3</sub> (half-power frequency)**:

```
f<sub>3</sub>/f<sub>C</sub> = [ (1/Q<sub>TC</sub><sup>2</sup> - 2) + √( (1/Q<sub>TC</sub><sup>2</sup> - 2)<sup>2</sup> + 4 ) ]<sup>½</sup>
```

### 7. **Power Capacity**

**Displacement-limited power**:

```
P<sub>AR</sub> = (ρ<sub>0</sub> / 2πc) · 4π² · S<sub>D</sub> · |X(jω)|<sub>max</sub><sup>2</sup> · f<sub>3</sub><sup>3</sup>
```

Where V<sub>D</sub> = S<sub>D</sub> · x<sub>max</sub> (peak displacement volume)

**Electrical power rating**:

```
P<sub>ER</sub> = P<sub>AR</sub> / η<sub>0</sub>
```

### 8. **Efficiency-Size Tradeoff**

A key result from the paper:

> "A small air-suspension system, when compared to a large air-suspension system, must have a higher cutoff frequency, or lower efficiency, or both."

For non-wasteful designs (α ≥ 3):

```
η<sub>0</sub> · V<sub>B</sub> = constant
```

**Efficiency is directly proportional to enclosure size** for given response characteristics.

---

## Design Implications

### **Driver Size**

> "A large driver has no inherent advantage over a small one so far as small-signal response and efficiency are concerned."

However, large drivers are advantageous for:
- High acoustic output at low distortion
- Lower modulation distortion
- Larger V<sub>D</sub> (displacement volume)

### **Enclosure Size**

For air-suspension systems (α > 3):
- Once α > 4, no significant reduction in size without affecting performance
- Compact systems require **lower efficiency** or **higher cutoff frequency**
- High power capacity in compact systems requires expensive drivers

---

## System Synthesis Procedure

### **Given a Driver**

1. Check driver suitability:
   - f<sub>S</sub> must be lower than desired f<sub>C</sub>
   - For air-suspension: f<sub>S</sub> ≤ f<sub>C</sub> / √(α+1)

2. Calculate required α:
   ```
   α = (f<sub>C</sub> / f<sub>S</sub>)<sup>2</sup> - 1
   ```

3. Calculate enclosure volume:
   ```
   V<sub>B</sub> = V<sub>AS</sub> / α
   ```

4. Verify efficiency and power capacity

### **From Specifications**

Given desired f<sub>C</sub>, Q<sub>TC</sub>, V<sub>B</sub>, and P<sub>AR</sub>:

1. Assume Q<sub>MC</sub> (typically 5 for lined enclosures)
2. Calculate Q<sub>EC</sub> from Q<sub>TC</sub>
3. Calculate required driver parameters:
   ```
   f<sub>S</sub> = f<sub>C</sub> / (α + 1)<sup>½</sup>
   Q<sub>ES</sub> = Q<sub>EC</sub> / (α + 1)<sup>½</sup>
   V<sub>AS</sub> = α · V<sub>B</sub>
   ```

4. Calculate efficiency η<sub>0</sub> and verify P<sub>ER</sub> ≥ P<sub>E(max)</sub>

---

## Key Formulas for Implementation

### **Acoustic Compliance**

```
C<sub>AS</sub> = V<sub>AS</sub> / (ρ<sub>0</sub> · c<sup>2</sup>)
```

### **Mechanical Compliance**

```
C<sub>MS</sub> = C<sub>AS</sub> / S<sub>D</sub><sup>2</sup>
```

### **Moving Mass**

```
M<sub>MS</sub> = 1 / [ (2πf<sub>S</sub>)<sup>2</sup> · C<sub>MS</sub> ]
```

### **Electromagnetic Damping**

```
B<sup>2</sup>l<sup>2</sup> / R<sub>E</sub> = 2πf<sub>S</sub> · M<sub>MS</sub> / Q<sub>ES</sub>
```

---

## Validation Criteria

### **Parameter Measurement**

The paper provides a method for measuring system parameters from impedance:

1. Measure driver free-air parameters (on test baffle)
2. Measure mounted driver parameters (in enclosure)
3. Calculate system parameters from differences

### **Driver Design Verification**

For air-suspension drivers, the exact values of f<sub>S</sub>, Q<sub>ES</sub>, V<sub>AS</sub> are not critical as long as:

- **f<sub>S</sub><sup>2</sup> · V<sub>AS</sup>** is correct (indicates effective mass)
- **f<sub>S</sub> / Q<sub>ES</sub>** is correct (indicates electromagnetic coupling)
- V<sub>AS</sub> is large enough for satisfactory α

---

## References

This paper is Part I of a two-part series. Part II covers system synthesis methods.

**Related papers**:
- Thiele (1961): "Loudspeakers in Vented Boxes"
- Small (1973-74): Vented-box loudspeaker systems (Parts I & II)

---

## Implementation Notes for Viberesp

### **Data Model**

```python
@dataclass
class ClosedBoxSystem:
    """Closed-box loudspeaker system parameters."""
    f_c: float  # System resonance frequency (Hz)
    q_tc: float  # Total system Q
    v_b: float  # Enclosure volume (m³)
    v_as: float  # Driver compliance volume (m³)
    alpha: float  # Compliance ratio
    eta_0: float  # Reference efficiency
    p_ar: float  # Acoustic power rating (W)
    p_er: float  # Electrical power rating (W)
```

### **Key Calculations**

1. **System response** at frequency f:
   ```python
   def closed_box_response(f, f_c, q_tc):
       ratio = f_c / f
       denom = (1 - ratio**2)**2 + (ratio / q_tc)**2
       return ratio**2 / np.sqrt(denom)
   ```

2. **Cutoff frequency** from Q<sub>TC</sub>:
   ```python
   def half_power_freq(f_c, q_tc):
       term = (1/q_tc**2 - 2)
       return f_c * np.sqrt((term + np.sqrt(term**2 + 4)) / 2)
   ```

3. **Efficiency** calculation:
   ```python
   def reference_efficiency(f_s, v_as, q_es, s_d):
       rho_0 = 1.205
       c = 343.7
       return ((rho_0 / (2*np.pi*c)) *
               (4*np.pi**2 / s_d) *
               f_s**3 * v_as / q_es)
   ```

---

*Paper retrieved from: http://www.readresearch.co.uk/thiele-small_papers/smalls_closed_box_article_3.pdf*

*Last updated: 2025-12-25*
