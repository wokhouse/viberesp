# Conical Horn Theory

## Overview

The conical horn is the simplest horn geometry, consisting of a straight-sided cone. Unlike exponential horns, it expands linearly in radius and quadratically in area. It supports spherical wavefronts rather than the plane waves assumed in Webster's equation.

## Geometry

### Area Function

The area expansion for a conical horn is:

$$S(x) = S_t \left(1 + \frac{x}{x_0}\right)^2$$

Where:
- $S_t$ is the throat area
- $x$ is the axial distance from the throat
- $x_0$ is the distance from the projected apex of the cone to the throat

Alternatively, if defining by throat radius $r_t$ and mouth radius $r_m$ over length $L$:

$$r(x) = r_t + \frac{r_m - r_t}{L}x$$

$$S(x) = \pi r(x)^2$$

The two forms are geometrically equivalent.

### Calculating x0

From similar triangles relating the throat and mouth radii:

$$\frac{r_t}{x_0} = \frac{r_m - r_t}{L}$$

Therefore:

$$x_0 = \frac{r_t \cdot L}{r_m - r_t}$$

This can also be expressed in terms of areas:

$$x_0 = \frac{L \sqrt{S_t}}{\sqrt{S_m} - \sqrt{S_t}}$$

**Literature:**
- Olson (1947), Section 5.15 - Conical horn geometry

## Acoustic Impedance

### Infinite Conical Horn

The throat impedance of an infinite conical horn is derived from spherical wave theory:

$$Z_t = \frac{\rho c}{S_t} \left[ \frac{j k x_0}{1 + j k x_0} \right]$$

Where:
- $\rho$ = air density (~1.21 kg/m³)
- $c$ = speed of sound (~343 m/s)
- $k$ = wavenumber ($\omega/c$ or $2\pi f/c$)
- $x_0$ = distance from apex to throat

**Real and Imaginary Components:**

Separating into resistance $R_t$ and reactance $X_t$ where $Z_t = R_t + jX_t$:

$$R_t = \frac{\rho c}{S_t} \cdot \frac{k^2 x_0^2}{1 + k^2 x_0^2}$$

$$X_t = \frac{\rho c}{S_t} \cdot \frac{k x_0}{1 + k^2 x_0^2}$$

**Literature:**
- Olson (1947), Eq. 5.16 - Infinite conical horn impedance
- Beranek (1954), p. 270 - Spherical wave impedance derivation

### Finite Conical Horns

For finite conical horns, the impedance must be calculated using the transmission matrix (T-Matrix) method or by transforming the mouth load impedance back to the throat. The infinite horn formula above provides the theoretical ideal behavior for validation.

**Literature:**
- Kolbrek, "Horn Loudspeaker Simulation Part 1" - T-Matrix method for conical horns

## Cutoff Frequency Behavior

### Crucial Distinction from Exponential Horns

Conical horns **do not have a distinct cutoff frequency** in the same way exponential horns do.

| Horn Type | Cutoff Behavior |
|-----------|-----------------|
| **Exponential** | Sharp cutoff at $f_C = mc/4\pi$. Below this, resistance drops to zero. |
| **Conical** | No sharp cutoff. Resistance rises gradually from zero frequency. |

**Literature:**
- Pierce (1981) - Notes that applying Webster's equation to cones reveals no cutoff frequency
- Post (1994) - Discussion of cutoff frequency in conical waveguides

### Implications

1. **No frequency below which propagation stops** - Conical horns can propagate at all frequencies, but efficiency is poor at low frequencies due to the small $x_0$.

2. **Smoother impedance curve** - The resistance rises smoothly rather than showing a sharp step at cutoff.

3. **Wider bandwidth** - Conical horns can maintain reasonable loading over a wider frequency range compared to exponential horns, though with less optimal loading at any specific frequency.

4. **Constant directivity potential** - The linear expansion provides more constant directivity characteristics compared to exponential horns.

## Comparison with Exponential Horns

| Feature | Exponential / Hyperbolic | Conical |
|:--------|:-------------------------|:---------|
| **Wavefront** | Planar (Webster's equation) | Spherical |
| **Area Expansion** | $S_t e^{mx}$ | $S_t (1 + x/x_0)^2$ |
| **Impedance** | High ripple, sharp cutoff | Low ripple, no sharp cutoff |
| **Bandwidth** | Limited (high freq distortion) | Wide (constant directivity potential) |
| **Distortion** | Higher (throat constriction) | Lower |
| **Cutoff** | Yes, sharp cutoff frequency | No distinct cutoff |

**Literature:**
- Smith, J. O. (2010). *Physical Audio Signal Processing*, Section C.165 - Conical Acoustic Tubes

## Implementation Notes

### Hornresp Convention

Hornresp defines conical horns using:
- S1 (Throat area)
- S2 (Mouth area)
- L12 (Length)

The x0 parameter is then derived from these three inputs using the formula above.

### Numerical Considerations

1. **Small x0** - When the flare angle is large (small x0), the impedance becomes highly frequency-dependent and reactive.

2. **Large x0** - As x0 → ∞ (cylinder), the impedance approaches that of a cylindrical pipe.

3. **Finite vs Infinite** - Real horns are finite and require T-matrix simulation. The infinite formula is primarily for validation and understanding.

### Validation Approach

To validate conical horn implementation:

1. **Geometry Check**: Verify area calculation at various points
   - At throat (x=0): S(0) = S_t
   - At mouth (x=L): S(L) = S_m
   - At midpoint (x=L/2): Verify against geometric mean of radii

2. **Impedance Check**: Compare infinite horn impedance with theory
   - Low frequency (k*x0 << 1): Mostly reactive, mass-like
   - High frequency (k*x0 >> 1): Approaches ρc/S_t

3. **Hornresp Comparison**:
   - Export conical horn parameters to Hornresp
   - Compare throat impedance curves
   - Resistance should rise smoothly (no sharp cutoff step)

## References

1. **Olson, H. F. (1947)**. *Elements of Acoustical Engineering*. D. Van Nostrand Company.
   - Section 5.15: Conical Horn geometry
   - Equation 5.16: Infinite throat impedance

2. **Beranek, L. L. (1954)**. *Acoustics*. McGraw-Hill.
   - Pages 268-270: Detailed derivation using spherical coordinates
   - Chapter 5: Horn impedance calculations

3. **Pierce, A. D. (1981)**. *Acoustics: An Introduction to Its Physical Principles and Applications*.
   - Discussion of cutoff frequency in conical waveguides

4. **Post, J. T. (1994)**. "Cutoff frequency in conical waveguides".
   - Analysis of Webster's equation applied to cones

5. **Smith, J. O. (2010)**. *Physical Audio Signal Processing*.
   - Section C.165: Conical Acoustic Tubes
   - Online: https://ccrma.stanford.edu/~jos/pasp/

6. **Kolbrek, B.** "Horn Loudspeaker Simulation Part 1: Radiation and T-Matrix"
   - T-Matrix method for conical horns
   - Online: https://kolbrek.hornspeakersystems.info/
