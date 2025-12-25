# Horn Loudspeaker Simulation Part 3: Multiple Segments and More T-Matrices

**Author**: Bjørn Kolbrek
**Source**: https://kolbrek.hornspeakersystems.info/index.php/horns/58-horn-loudspeaker-simulation-part-3-multiple-segments-more-t-matrices
**Date**: 2019

---

## Summary

Part 3 introduces matrix algebra methods for handling multi-segment horns and complete system modeling using composite T-matrices.

---

## Matrix Algebra Approach

Instead of manually finding impedances at circuit points, we can use matrix algebra to form composite matrices describing the entire system from input to output.

### Advantages
- Cleaner code with vectorized operations
- Easy composition of multi-segment horns
- Direct calculation from input voltage to output pressure

---

## Multi-Segment Horns

### Composite Horn Matrix

For a horn with multiple segments, multiply matrices from throat to mouth:

```
M_horn = M_12 · M_23 · M_34 · ... · M_nm
```

Using type-12 matrices (relating throat to mouth):

```
| p₁ |       | a₁₂  b₁₂ | | a₂₃  b₂₃ |         | a_nm  b_nm | | pₙ |
|    | = ... |          | |          | ...   |          | |    |
| U₁ |       | c₁₂  d₁₂ | | c₂₃  d₂₃ |         | c_nm  d_nm | | Uₙ |
```

---

## Conical Horn T-Matrix

### Geometric Definition

For a conical segment with input area S1 and output area S2:

```
x₁ = L / (√(S₂/S₁) - 1)
x₂ = x₁ + L
```

The apex distance `x₁` is the distance from the throat to the virtual apex of the cone.

### T-Matrix Elements

```
kL = k·L
kx₁ = k·x₁
kx₂ = k·x₂

a = (x₂/x₁)·cos(kL) - sin(kL)/kx₁
b = j·(Zrc/S₂)·(x₂/x₁)·sin(kL)
c = j·(S₁/Zrc)·[(x₂/x₁ + 1/(kx₁)²)·sin(kL) - cos(kL)·L/(kx₁·x₁)]
d = (x₁/x₂)·cos(kL) + sin(kL)/kx₂
```

### Octave/Matlab Implementation

```matlab
function [a,b,c,d] = conicalHornMatrix(k, Zrc, S1, S2, L)
    kL = k*L;

    % Handle S1=S2 case (straight duct)
    if abs(S1 - S2) < 1e-10
        a = cos(kL);
        b = 1i*Zrc/S2*sin(kL);
        c = 1i*S2/Zrc*sin(kL);
        d = cos(kL);
        return;
    end

    x1 = L/(sqrt(S2/S1)-1);
    x2 = x1+L;
    kx1 = k*x1;
    kx2 = k*x2;

    sinkL = sin(kL);
    coskL = cos(kL);

    a = x2/x1 * coskL - sinkL./kx1;
    b = Zrc*1i/S2*x2/x1*sinkL;
    c = 1i/Zrc*S1*((x2/x1 + 1./(kx1.*kx1)).*sinkL - coskL.*L./(kx1*x1));
    d = x1/x2.*coskL + sinkL./kx2;
end
```

**Note**: The S1=S2 case must be handled separately to avoid division by zero.

---

## Two-Segment Horn Example

### Configuration: Conical + Exponential

```matlab
% Segment 1: Conical
S1 = 80e-4;    % 80 cm² throat
S2 = 350e-4;   % 350 cm² mid-point
L12 = 60e-2;   % 60 cm length

% Segment 2: Exponential
S3 = 5000e-4;  % 5000 cm² mouth
L23 = 75e-2;   % 75 cm length

Zrc = rho*c;

% Calculate submatrices
Me = expoHornMatrix(k, Zrc, S2, S3, L23);  % Exponential segment
Mc = conicalHornMatrix(k, Zrc, S1, S2, L12); % Conical segment

% Calculate composite horn matrix (order matters!)
Mh = Mc * Me;
```

**Order matters**: Multiply from throat towards mouth, or use type-21 matrices to multiply from mouth towards throat.

---

## Complete System T-Matrix

### Driver Matrix

The complete driver is the product of electrical, electromechanical coupling, mechanical, and transduction matrices:

```
M_driver = M_Te · M_Bl · M_Tm · M_Sd
```

where:

#### Electrical Domain Matrix (Te)
```
Te = | Re    0 |
     | 0   1/Re |
```

#### Electromechanical Coupling (Bl)
```
M_Bl = | 1    Bl |
       | 0     1  |
```

#### Mechanical Domain (Tm)
```
Tm = | Zm    0 |
     | 0   Sd²/Zm |
```

#### Transduction (Sd)
```
M_Sd = | 1    0 |
       | 0   1/Sd |
```

---

### Chamber Matrices

#### Rear Chamber (Series Impedance)

```
M_Cab = | 1    Zcab |
        | 0     1   |
```

#### Front Chamber (Parallel Impedance)

For a parallel impedance `Zcaf`:

```
M_Caf = | 1      0    |
        | 1/Zcaf  1   |
```

---

### Total System Matrix

```
M_system = M_Te · M_Bl · M_Tm · M_Sd · M_Caf · M_horn · M_radiation
```

Or more conveniently:

```
T = M_Te · M_Bl · M_Tm · M_Sd · M_Caf · M_horn
```

Then calculate with radiation impedance separately:

```
Zin = (a·Zrad + b) / (c·Zrad + d)
```

---

## Electrical Input Impedance

Given radiation impedance `Zrad` and system matrix `T = |a b; c d|`:

```
Zin = (a·Zrad + b) / (c·Zrad + d)
```

### Input Current

```
Iin = eg / Zin
```

---

## Output Pressure and Volume Velocity

With input vector `[eg; Iin]`:

```matlab
egv = ones(1, length(freq)) * eg;
Iin = eg./Zin.';

inputs = [egv; Iin];
outputs = inv(T) * inputs;

pm = outputs(1, :);  % Mouth pressure
Um = outputs(2, :);  % Mouth volume velocity

% Acoustic power
Pa = real(pm .* conj(Um));

% Convert to SPL
I = Pa / (2*pi);
prad = sqrt(I*rho*c);
SPL = 20*log10(prad/pref);
```

---

## Diaphragm Displacement

Using only the driver matrix:

```matlab
% Driver output only
driverOut = inv(TD) * inputs;
UaL = driverOut(2, :);

% Diaphragm displacement
x = UaL./w / Sd * sqrt(2);
```

---

## Matrix Type Conventions

### Type-12 Matrix (Throat → Mouth)

```
| p_throat |   | a  b | | p_mouth |
|         | = |      | |         |
| U_throat |   | c  d | | U_mouth |
```

### Type-21 Matrix (Mouth → Throat)

Inverse of type-12:

```
M_21 = M_12⁻¹ = | d  -b |
                | -c  a |
```

Useful when working from mouth towards throat.

---

## 3D Matrix Operations

Since we have a 2×2 matrix per frequency point, we can use 3D matrices:

```matlab
% Create 3D matrix: [2×2×Nfreq]
M3d = zeros(2, 2, length(freq));
M3d(1,1,:) = a;
M3d(1,2,:) = b;
M3d(2,1,:) = c;
M3d(2,2,:) = d;
```

Then define overloaded matrix multiplication for 3D matrices (included in the repo).

---

## Complete System Code Structure

```matlab
% 1. Build matrices
Me = expoHornMatrix(k, Zrc, S2, S3, L23);
Mc = conicalHornMatrix(k, Zrc, S1, S2, L12);
Mh = Mc * Me;

% 2. Build system matrix
Te = buildElectricalMatrix(Re, Le, freq);
Tm = buildMechanicalMatrix(Zm, freq);
TSd = buildTransductionMatrix(Sd);
TCaf = buildParallelMatrix(Zcaf);
TCab = buildSeriesMatrix(Zcab);

% 3. Complete system
TD = Te * buildBlMatrix(Bl) * Tm * TSd;
T = TD * TCaf * Mh;

% 4. Add radiation
Mrad = buildSeriesMatrix(Zrad);
T_total = T * Mrad;

% 5. Calculate input impedance
a = T_total(1,1,:);
b = T_total(1,2,:);
c = T_total(2,1,:);
d = T_total(2,2,:);
Zin = (a.*Zrad + b) ./ (c.*Zrad + d);

% 6. Calculate outputs
Iin = eg./Zin.';
inputs = [eg*ones(1,Nfreq); Iin];
outputs = inv(T_total) * inputs;
```

---

## Verification

The T-matrix approach produces results matching Hornresp for:
- Multi-segment horns (conical + exponential)
- SPL response
- Diaphragm displacement
- Electrical input impedance

---

## Key Advantages of T-Matrix Method

1. **Composability**: Multiply matrices to form composite systems
2. **Directionality**: Use type-12 or type-21 as needed
3. **Efficiency**: Vectorized operations across frequency
4. **Clarity**: Clear system topology from matrix structure
5. **Extensibility**: Add new horn types by implementing their T-matrix

---

## Matrix Implementation Tips

1. **Handle edge cases**: S1=S2 for conical horns, division by zero
2. **Matrix order**: Multiply in correct direction (throat→mouth or vice versa)
3. **Complex numbers**: Octave/Matlab handle these automatically
4. **Type consistency**: Use all type-12 or all type-21, don't mix
5. **3D operations**: For vectorized frequency calculations

---

## Summary of T-Matrices

| Horn Type | Key Parameters | T-Matrix Complexity |
|-----------|----------------|---------------------|
| Exponential | m (flare rate) | γ = √(k² - m²) becomes imaginary below cutoff |
| Conical | x₁, x₂ (apex distances) | Division by zero when S1=S2 |
| Hyperbolic | T (shape parameter) | More complex, T-dependent |
| Tractrix | No closed form | Numerical or approximation needed |
| Straight duct | S1 = S2 | Simplified conical with cos(kL), sin(kL) |

---

*This is Part 3 of a multi-part series on horn loudspeaker simulation.*
