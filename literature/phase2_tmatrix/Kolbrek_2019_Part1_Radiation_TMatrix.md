# Horn Loudspeaker Simulation Part 1: Radiation and T-Matrix

**Author**: Bjørn Kolbrek
**Source**: https://kolbrek.hornspeakersystems.info/index.php/horns/53-horn-loudspeaker-simulation-part-1-radiation-and-t-matrix
**Date**: 2019

---

## Summary

This first part of the series covers basic radiation and horn throat impedance calculations, which are fundamental to horn simulation.

---

## Radiation Impedance

### Circular Piston in Infinite Baffle

The acoustic impedance for a piston of radius `a` and area `S` is:

```
Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))
```

where:
- `R(ka) = 1 - J₁(2ka)/(ka)`
- `X(ka) = H₁(2ka)/(ka)`
- `J₁` = Bessel function of order 1
- `H₁` = Struve function of order 1
- `ka = 2πf·a/c` (dimensionless frequency)

### Struve Function Approximation

The Struve function can be approximated using standard functions:

```
H₁(x) = 2/π - J₀(x) + (16/π - 5)·sin(x)/x + (12 - 36/π)·(1 - cos(x))/x²
```

This approximation is from http://mathworld.wolfram.com/StruveFunction.html

### Octave/Matlab Implementation

```matlab
function Znorm = circularPistonIB(ka)
    R = 1 - besselj(1,2*ka)./(ka);
    X = struveH1(2*ka)./(ka);
    Znorm = R + 1i*X;
end

function H1 = struveH1(x)
    H1 = 2/pi - besselj(0,x) + (16/pi - 5)*sin(x)./x + (12-36/pi)*(1-cos(x))./x.^2;
end
```

### Radiation Impedance Behavior

- At low ka (ka << 1): Mass-controlled region, X >> R
- At ka ≈ 1: Transition region
- At high ka (ka >> 1): R → 1, X → 0 (purely resistive)

---

## T-Matrix Method

### Definition

Transfer matrices relate pressure and volume velocity at one end of the horn to the other:

```
| p₁ |   | a  b | | p₂ |
|    | = |      | |    |
| U₁ |   | c  d | | U₂ |
```

**Key advantages**:
- Matrices can be multiplied for multi-segment horns
- Enables composite horns from multiple segments
- Can approximate arbitrary profiles with small conical segments

---

## Exponential Horn T-Matrix

### Area Function Definition

```
S(x) = S₁ · e^(2mx)
```

where the flare constant `m` is:

```
m = ln(S₂/S₁) / (2L)
```

Using `2mx` in the exponent (rather than `mx`) makes `m` equal to the cutoff wavenumber.

### Cutoff Frequency

```
fc = c·m / (2π)
```

Below cutoff, the wave becomes evanescent (exponential decay).

### T-Matrix Elements

```
γ = √(k² - m²)    # Becomes imaginary below cutoff

a = e^(mL) · [cos(γL) - (m/γ)·sin(γL)]
b = e^(mL) · j·(Zrc/S₂) · (k/γ) · sin(γL)
c = e^(mL) · j·(S₁/Zrc) · (k/γ) · sin(γL)
d = e^(mL) · (S₁/S₂) · [cos(γL) + (m/γ)·sin(γL)]
```

where `Zrc = ρ₀c` is the reference characteristic impedance.

### Octave/Matlab Implementation

```matlab
function [a,b,c,d] = expoHornMatrix(k, Zrc, S1, S2, L)
    m = log(S2/S1)/(2*L);
    gamma = sqrt(k.^2 - m^2);  % Becomes imaginary below cutoff
    gL = gamma*L;

    singl = sin(gL);
    cosgl = cos(gL);

    emL = exp(m*L);
    a = emL*(cosgl - m./gamma.*singl);
    b = emL*1i*Zrc/S2.*k./gamma.*singl;
    c = emL*1i*S1/Zrc.*k./gamma.*singl;
    d = emL*S1/S2.*(cosgl + m./gamma.*singl);
end
```

---

## Throat Impedance Calculation

Given the radiation impedance at the mouth `Z₂`, the throat impedance `Z₁` is:

```
Z₁ = (a·Z₂ + b) / (c·Z₂ + d)
```

For normalized impedance (as shown in Hornresp):

```
Z₁_norm = Z₁ · S₁ / (ρ₀c)
```

---

## Complete Example

```matlab
% Medium properties (Hornresp defaults)
rho = 1.205;
c = 344;

% Frequency range
fmin = 10;
fmax = 20e3;
freq = logspace(log10(fmin), log10(fmax), 533);
k = 2*pi*freq/c;

% Horn dimensions
S1 = 80e-4;    % 80 cm² throat
S2 = 5000e-4;  % 5000 cm² mouth
L12 = 150e-2;  % 150 cm length

% Calculate radiation impedance at mouth
a = sqrt(S2/pi);
Z2 = rho*c/S2 * circularPistonIB(k*a);

% Calculate horn T-matrix
Zrc = rho*c;
[a12,b12,c12,d12] = expoHornMatrix(k, Zrc, S1, S2, L12);

% Calculate and normalize throat impedance
Z1 = (a12.*Z2 + b12) ./ (c12.*Z2 + d12);
Z1norm = Z1*S1/(rho*c);

% Plot
semilogx(freq, real(Z1norm), 'k', freq, imag(Z1norm), 'r');
xlim([fmin, fmax]);
ylim([-0.5, 2.5]);
xlabel('Frequency (Hz)');
ylabel('Normalized Impedance');
title('Acoustical Impedance');
grid on;
```

---

## Verification

The implementation produces results matching Hornresp simulations for:
- Throat impedance magnitude and phase
- Cutoff frequency behavior
- High-frequency asymptotic behavior

---

## Key Constants

```
ρ₀ = 1.205 kg/m³  (air density)
c = 344 m/s      (speed of sound)
```

---

## References

- Wolfram MathWorld: Struve Function approximation
- Hornresp software (for validation)

---

*This is Part 1 of a multi-part series on horn loudspeaker simulation.*
