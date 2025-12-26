# Beranek (1954): Acoustics

**Citation**: Leo L. Beranek, *Acoustics*, McGraw-Hill, 1954.

**Status**: Classic reference, needs full PDF review for equation extraction

**Key Equations for Viberesp Implementation**:

### Radiation Impedance of Circular Piston

**Equation 5.20**: Radiation impedance for circular piston in infinite baffle
```
Z_R = ρc·S · [R₁(2ka) + jX₁(2ka)]
```
where:
- `Z_R` = radiation impedance (complex Ω)
- `ρ` = air density (kg/m³)
- `c` = speed of sound (m/s)
- `S` = piston area = πa² (m²)
- `a` = piston radius (m)
- `k` = wavenumber = ω/c = 2πf/c
- `R₁(2ka)` = radiation resistance function
- `X₁(2ka)` = radiation reactance function

**Component functions**:
```
R₁(2ka) = 1 - J₁(2ka)/(ka)
X₁(2ka) = H₁(2ka)/(ka)
```
where:
- `J₁` = Bessel function of first kind, order 1
- `H₁` = Struve function of order 1

### Asymptotic Behavior

**Low frequency limit (ka << 1)**:
```
R₁ ≈ (ka)²/2
X₁ ≈ (8ka)/(3π)
```
Radiation impedance is stiffness-like (mass controlled).

**High frequency limit (ka >> 1)**:
```
R₁ ≈ 1
X₁ ≈ 1/(πka)
```
Radiation impedance approaches ρc/S (characteristic impedance of free space).

## Implementation Notes for Viberesp

**What to implement**:
1. ✅ Bessel J₁ function via scipy.special.j1 (Stage 5)
2. ✅ Struve H₁ function via scipy.special.struve (Stage 5)
3. ✅ Aarts approximation for Struve H₁ (optional, for speed) (Stage 5)
4. ✅ Radiation impedance calculation (Stage 5, Stage 1B)

**Numerical considerations**:
- Use scipy.special for Bessel and Struve functions
- Handle small ka carefully (use series expansion if needed)
- High-frequency approximation can speed up calculations

**Validation approach**:
- Compare with Hornresp test cases TC-P1-RAD-01 through TC-P1-RAD-04
- Verify asymptotic limits (ka → 0, ka → ∞)
- Check accuracy of Aarts approximation (<0.1% vs scipy)

### Finite Horn Corrections

Beranek Chapter 5 also discusses:
- Mouth reflection corrections for finite horns
- Effect of horn length on impedance transformation
- Equivalent circuit representations

These become important in Stage 6 (finite horn impedance).

## Resources

**Primary source**: Beranek (1954), "Acoustics"
- PDF available: [https://cdn.preterhuman.net/texts/science_and_technology/physics/Waves_and_Thermodynamics/Acoustics%20-%20L.%20Beranek.pdf](https://cdn.preterhuman.net/texts/science_and_technology/physics/Waves_and_Thermodynamics/Acoustics%20-%20L.%20Beranek.pdf)
- Chapter 5: Radiation of Sound

**Secondary references**:
- Aarts (2003): Efficient Struve H₁ approximation
- Kolbrek Part 1: Summarizes Beranek Eq. 5.20

**Companion references**:
- Olson (1947): Throat impedance equations
- Chabassier (2018): T-matrix propagation through finite horns

**TODO**: Full PDF review to extract exact equation numbers and page numbers

## Connection to Other References

**In Kolbrek Part 1**:
- Revisits Beranek's radiation impedance formula
- Provides implementation notes for Bessel/Struve functions
- Discusses numerical methods for evaluation

**In Aarts (2003)**:
- Provides fast approximation for Struve H₁ function
- Cites Beranek as original source for radiation impedance equation
- Achieves 0.1% accuracy with rational function approximation

**Implementation priority**:
1. High priority for Stage 5 (radiation impedance)
2. Also needed for Stage 1B (bare driver model)
3. Essential for validation against Hornresp
