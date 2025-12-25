# Horn Loudspeaker Simulation Part 2: Adding a Driver

**Author**: Bjørn Kolbrek
**Source**: https://kolbrek.hornspeakersystems.info/index.php/horns/55-horn-loudspeaker-simulation-part-2-adding-a-driver
**Date**: 2019

---

## Summary

Part 2 combines the horn simulation from Part 1 with a driver model, including front and rear chambers, to create a complete horn speaker system.

---

## Moving Coil Driver Equivalent Circuit

### Three-Domain Model

The complete equivalent circuit spans electrical, mechanical, and acoustical domains:

```
Electrical → Mechanical (via Bl coupling) → Acoustical (via Sd)
```

### Electrical Domain
```
Ze = Re + jωLe
```

### Mechanical Domain (reflected from electrical)
```
Zme = (Bl)² / Ze
```

### Total Mechanical Impedance
```
Zm = Rms + jωMmd + 1/(jωCms)
Zmt = Zme + Zm
```

### Acoustical Domain
```
Zas = Zmt / Sd²
```

### Acoustical Source Pressure
```
ps = eg·Bl / (Sd·Ze)
```

where:
- `eg` = generator voltage (typically 2.83V for 1W into 8Ω)
- `Bl` = force factor
- `Sd` = diaphragm area

---

## Octave/Matlab Implementation

```matlab
% Frequency range
fmin = 10;
fmax = 20e3;
freq = logspace(log10(fmin), log10(fmax), 533);
w = 2*pi*freq;

% Driver parameters (MKS units)
Sd = 350e-4;    % 350 cm²
Bl = 18;        % T·m
Cms = 4.0e-4;   % m/N
Rms = 4.0;      % N·s/m
Mmd = 20e-3;    % 20 g
Le = 1e-3;      % 1 mH
Re = 6.0;       % 6 Ω

% Input voltage
eg = 2.83;

% Driver calculations
% 1. Mechanical equivalent of electrical impedance
Ze = Re + 1i*w * Le;
Zme = Bl^2 ./ Ze;

% 2. Total mechanical impedance
Zm = Rms + 1i*w * Mmd + 1./(1i*w * Cms);
Zmt = Zme + Zm;

% 3. Acoustical source impedance
Zas = Zmt ./ Sd^2;

% 4. Acoustical source pressure
ps = eg*Bl ./ (Sd * Ze);
```

---

## Front-Loaded Horn System

### Physical Layout

```
    Rear Chamber     Driver      Front Chamber     Horn
┌────────────────┐  ┌────┐  ┌────────────────┐  ┌──────┐
│                │  │    │  │                │  │      │
│      Vrc       │→ │ Sd │→ │      Vtc       │→ │ Horn │→ Mouth
│                │  │    │  │                │  │      │
└────────────────┘  └────┘  └────────────────┘  └──────┘
```

### Acoustical Equivalent Circuit

```
ps    Zas      ┌─────┐      ┌─────┐      ┌─────┐
───▶  Zas  ──▶│ Cab │───┬─▶│ Caf │───┬─▶│ Zal │───▶
      [series] └─────┘  │  └─────┘  │  └─────┘
                        │           │
                        └───────────┴── [parallel combination]
```

where:
- `Cab` = rear chamber compliance
- `Caf` = front chamber compliance
- `Zal` = horn throat impedance (from T-matrix calculation)

---

## Chamber Compliances

### Compliance of an Air Volume

```
C = V / (ρ₀·c²)
```

where:
- `V` = chamber volume (m³)
- `ρ₀` = air density (kg/m³)
- `c` = speed of sound (m/s)

### Impedance of a Compliance

```
Z = 1 / (jωC)
```

### Octave/Matlab Implementation

```matlab
% Front and rear chamber calculations
Cab = Vrc / (rho*c^2);
Caf = Vtc / (rho*c^2);
Zcab = 1./(1i*w * Cab);
Zcaf = 1./(1i*w * Caf);
```

---

## Acoustic Load Impedance

### Front Load (Horn + Front Chamber in Parallel)

```
Zf = Zal || Zcaf = Zal·Zcaf / (Zal + Zcaf)
```

### Total Load (Front + Rear in Series)

```
Zal = Zf + Zcab
```

### Octave/Matlab Implementation

```matlab
% Calculate horn T-matrix (from Part 1)
[a12,b12,c12,d12] = expoHornMatrix(k, Zrc, S1, S2, L12);
Z1 = (a12.*Z2 + b12) ./ (c12.*Z2 + d12);

% Total load impedance
Zf = Z1.*Zcaf ./ (Z1 + Zcaf);
Zr = Zcab;
Zal = Zf + Zr;

% Volume velocity into the load
UaL = ps ./ (Zas + Zal);
```

---

## Power Output Calculations

### Throat Pressure

```
pth = UaL · Zf
```

### Throat Volume Velocity

```
Uth = pth / Z1
```

### Acoustic Power

```
Pa = |Uth|² · Re(Z1)
```

### Convert Power to SPL

Assuming radiation into a 2π hemisphere:

```
I = Pa / (2πr²)
prad = √(I·ρ₀·c)
SPL = 20·log10(prad/pref)

where:
pref = 20·10⁻⁶ Pa  (reference pressure)
r = 1 m            (reference distance)
```

### Octave/Matlab Implementation

```matlab
% Power into the load
pth = UaL .* Zf;
Uth = pth ./ Z1;
Pa = abs(Uth).^2 .* real(Z1);

% Convert power to SPL
I = Pa / (2*pi);
prad = sqrt(I*rho*c);
pref = 20e-6;
SPL = 20*log10(prad/pref);
```

---

## Diaphragm Displacement

From volume velocity:

```
UaL = v·Sd
v = UaL / Sd
x = v / (jω)
x = UaL / (jω·Sd)
```

For RMS values:

```
x_peak = √2 · UaL / (ω·Sd)
```

### Octave/Matlab Implementation

```matlab
% Diaphragm displacement
x = UaL./w / Sd * sqrt(2);
```

---

## Electrical Input Impedance

Working backwards from the acoustic load:

```
Zma = Zal · Sd²       # Acoustic → Mechanical
Zmt = Zma + Zm        # Add mechanical impedance
Zem = (Bl)² / Zmt     # Mechanical → Electrical
Zet = Zem + Ze        # Add blocked impedance
```

### Octave/Matlab Implementation

```matlab
% Electrical impedance
Zma = Zal * Sd^2;
Zmt = Zma + Zm;
Zem = Bl^2 ./ Zmt;
Zet = Zem + Ze;
```

---

## Complete System Example

```matlab
% Medium properties
rho = 1.205;
c = 344;

% Horn parameters
S1 = 80e-4;      % Throat
S2 = 5000e-4;    % Mouth
L12 = 150e-2;    % Length
Vrc = 100e-3;    % Rear chamber (100L)
Vtc = 0;         % No front chamber

% Calculate radiation impedance
a = sqrt(S2/pi);
Z2 = rho*c/S2 * circularPistonIB(k*a);

% Calculate horn T-matrix
Zrc = rho*c;
[a12,b12,c12,d12] = expoHornMatrix(k, Zrc, S1, S2, L12);

% Throat impedance
Z1 = (a12.*Z2 + b12) ./ (c12.*Z2 + d12);

% Chambers
Cab = Vrc / (rho*c^2);
Caf = Vtc / (rho*c^2);
Zcab = 1./(1i*w * Cab);
Zcaf = 1./(1i*w * Caf);

% Total load
Zf = Z1.*Zcaf ./ (Z1 + Zcaf);
Zr = Zcab;
Zal = Zf + Zr;

% Output calculations
UaL = ps ./ (Zas + Zal);
pth = UaL .* Zf;
Uth = pth ./ Z1;
Pa = abs(Uth).^2 .* real(Z1);
```

---

## Hornresp Validation

The implementation produces results matching Hornresp for:
- SPL response
- Diaphragm displacement
- Electrical input impedance

**Note**: Simulate with "Resonances Masked" option (Tools → Options) when using the simple compliance model for chambers.

---

## Key Formulas Summary

| Quantity | Formula |
|----------|---------|
| Electrical impedance | `Ze = Re + jωLe` |
| Mechanical reflected | `Zme = (Bl)²/Ze` |
| Mechanical total | `Zm = Rms + jωMmd + 1/(jωCms)` |
| Acoustic source impedance | `Zas = (Zme + Zm)/Sd²` |
| Acoustic source pressure | `ps = eg·Bl/(Sd·Ze)` |
| Chamber compliance | `C = V/(ρ₀c²)` |
| Throat volume velocity | `Uth = pth/Z1` |
| Acoustic power | `Pa = \|Uth\|²·Re(Z1)` |
| SPL | `SPL = 20·log10(prad/pref)` |

---

*This is Part 2 of a multi-part series on horn loudspeaker simulation.*
