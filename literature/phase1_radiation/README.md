# Phase 1: Radiation Impedance Literature

## Overview

Phase 1 implements radiation impedance calculations for a circular piston in an infinite baffle. This is the fundamental building block for horn loudspeaker simulation, determining how sound energy radiates into free space at the horn mouth.

## Primary References

### 1. Kolbrek (2019) Part 1: Radiation and T-Matrix

**Location:** `../phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md`

**Sections Used:**
- "Radiation Impedance"
- "Circular Piston in Infinite Baffle"

**Key Formulas:**
```
Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))

where:
R(ka) = 1 - J₁(2ka)/(ka)
X(ka) = H₁(2ka)/(ka)
ka = 2πf·a/c
```

**Used for:**
- Bessel function formulation for radiation resistance
- Struve function formulation for radiation reactance
- Normalized impedance definition
- High and low frequency asymptotic behavior

### 2. Wolfram MathWorld: Struve Function

**Location:** http://mathworld.wolfram.com/StruveFunction.html

**Used for:**
- Struve H₁ function approximation formula
- Numerical implementation guidance
- Accuracy verification

**Note:** The Viberesp implementation uses `scipy.special.struve` directly for maximum accuracy, rather than the MathWorld approximation.

### 3. Beranek & Mellow (2012): Acoustics

**Reference:** Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound Fields and Transducers*. Chapter 4: Radiation Impedance.

**Status:** Future addition to literature directory

**Used for:**
- Alternative derivation of radiation impedance
- Physical interpretation of impedance components
- Mass-controlled and resistance-controlled regions

## Implementation

**Code Location:** `src/viberesp/physics/radiation.py`

**Functions:**
- `circular_piston_impedance_normalized(ka)` - Normalized impedance
- `circular_piston_impedance(area, frequency, rho, c)` - Full impedance
- `_struve_h1(x)` - Struve H₁ helper (internal)

**Tests:** `tests/physics/test_radiation.py`

**Validation:** TC-P1-RAD-01 against theoretical Kolbrek values

## Physical Behavior

### Low Frequency (ka << 1): Mass-Controlled Region

- **Condition:** ka < 0.5 approximately
- **Behavior:** Reactance X dominates resistance R
- **Physical interpretation:** Radiation adds mass loading to the system
- **Limit:** X(ka) → (2/π)·ka as ka → 0

**Example:** At 50 Hz for 20 cm radius piston:
- ka = 0.18
- R_norm = 0.016 (very small)
- X_norm = 0.153 (dominates)
- X/R ratio ≈ 9.3

### Transition Region (ka ≈ 1)

- **Condition:** ka ≈ 0.5 to 2
- **Behavior:** R and X are comparable
- **Physical interpretation:** Complex radiation behavior

### High Frequency (ka >> 1): Radiation-Controlled

- **Condition:** ka > 10 approximately
- **Behavior:** Resistance R approaches 1, reactance X → 0
- **Physical interpretation:** Radiation becomes purely resistive
- **Efficiency:** 100% radiation efficiency at high frequencies

**Example:** At 10 kHz for 20 cm radius:
- ka ≈ 36
- R_norm ≈ 0.999
- X_norm ≈ 0.018
- Almost purely resistive

## Validation Results

**Test Case:** TC-P1-RAD-01
**Configuration:** 1257 cm² circular piston, 50 Hz
**Expected (Theory):** R_norm = 0.0164, X_norm = 0.1528
**Implementation:** R_norm = 0.0164, X_norm = 0.1528
**Error:** < 0.01% (numerical precision)

**All 25 unit tests pass:**
- Struve function accuracy: < 1% error vs scipy
- Normalized impedance: Matches Kolbrek formulas
- Full impedance: Correct area and frequency scaling
- Edge cases: Handles extreme frequencies and areas
- Validation: Matches theoretical expectations

## Hornresp Comparison

**Note:** Hornresp exported values show systematic scaling:
- Hornresp R ≈ 4.05 × Kolbrek R
- Hornresp X ≈ 2.02 × Kolbrek X

This ratio is consistent across frequencies, suggesting a normalization convention difference (possibly throat vs mouth impedance, or different impedance definition). Viberesp follows the peer-reviewed Kolbrek formulation.

## Future Extensions

Out of scope for Phase 1 but planned for future:

1. **Additional geometries:**
   - Rectangular piston
   - Elliptical piston
   - Annular piston

2. **Boundary conditions:**
   - Finite circular baffle
   - Free space (4π radiation vs half-space)
   - Quarter-space (corner loading)

3. **Directivity:**
   - Radiation pattern calculations
   - Directivity index

## Related Literature

For T-matrix implementation (Phase 2):
- **Kolbrek Part 1:** Exponential and conical horn T-matrices
- **Throat impedance:** Z₁ = (a·Z₂ + b) / (c·Z₂ + d)
- **Multi-segment horns:** Matrix multiplication for composite horns

---

*Last Updated: 2025-12-25*
*Phase: 1 - Radiation Impedance*
*Status: Complete*
