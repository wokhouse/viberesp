# Hornresp Input Format Reference

Based on the existing `hornresp_exporter.py`, here's the complete Hornresp parameter file format.

## File Format

- **Line endings**: CRLF (`\r\n`)
- **Format**: Plain text key-value pairs
- **Sections**: Delimited by all-caps headers with `|` prefix

---

## Parameter Sections

### 1. Header
```
ID = 55.30

Comment = <description>
```

### 2. Radiation and Source Parameters
```
|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:

Ang = <value>       # Radiation angle: 0.5 x Pi (half-space), 1.0 x Pi (full-space)
Eg = <volts>        # Generator voltage (typically 2.83V for 1W into 8Ω)
Rg = <ohms>         # Generator source resistance
Cir = <meters>      # Mouth circumference correction
```

### 3. Horn Parameters
```
|HORN PARAMETER VALUES:

S1 = <cm²>          # Throat area (segment 1 input)
S2 = <cm²>          # Segment 1 output / segment 2 input
Exp = <cm>          # Segment 1 exponential horn length (L12)
F12 = <Hz>          # Segment 1 cutoff frequency (for exponential horns)
S2 = <cm²>          # Segment 2 input (repeated - Hornresp format quirk)
S3 = <cm²>          # Segment 2 output
Exp = <flare>       # Segment 2 flare constant
F23 = <Hz>          # Segment 2 cutoff frequency
S3 = <cm²>          # Segment 3 input
S4 = <cm²>          # Segment 3 output
L34 = <cm>          # Segment 3 length
F34 = <Hz>          # Segment 3 cutoff frequency
S4 = <cm²>          # Segment 4 input
S5 = <cm²>          # Segment 4 output
L45 = <cm>          # Segment 4 length
F45 = <Hz>          # Segment 4 cutoff frequency
```

**Horn Flare Types** (entered interactively in Hornresp):
- `CON` - Conical
- `EXP` - Exponential
- `HYP` - Hyperbolic (catenoidal, cosh, sinh)
- `TRA` - Tractrix
- `LEC` - Le Cléac'h

### 4. Traditional Driver Parameters
```
|TRADITIONAL DRIVER PARAMETER VALUES:

Sd = <cm²>          # Diaphragm area
Bl = <T·m>          # Force factor
Cms = <m/N>         # Mechanical compliance (use scientific notation for small values)
Rms = <N·s/m>       # Mechanical resistance
Mmd = <g>           # Moving mass
Le = <mH>           # Voice coil inductance
Re = <Ω>            # Voice coil DC resistance
Nd = <count>        # Number of drivers
```

**Important**: `Cms` values < 0.001 should be in scientific notation (e.g., `1.23E-04`)

### 5. Advanced Driver Parameters (Semi-Inductance Model)
```
|ADVANCED DRIVER PARAMETER VALUES FOR SEMI-INDUCTANCE MODEL:

Re' = <ohms>
Leb = <H>
Le = <H>
Ke = <unitless>
Rss = <ohms>
```

### 6. Advanced Driver Parameters (Damping Model)
```
|ADVANCED DRIVER PARAMETER VALUES FOR FREQUENCY-DEPENDENT DAMPING MODEL:

Rms = <N·s/m>
Ams = <kg/s>
```

### 7. Passive Radiator
```
|PASSIVE RADIATOR PARAMETER VALUE:

Added Mass = <g>
```

### 8. Chamber Parameters
```
|CHAMBER PARAMETER VALUES:

Vrc = <L>           # Rear chamber volume
Lrc = <cm>          # Rear chamber acoustic path length
Fr = <Hz>           # Rear chamber effective resonance frequency
Tal = <value>       # Rear chamber fill material factor
Vtc = <L>           # Throat (front) chamber volume
Atc = <cm²>         # Throat chamber area

Acoustic Path Length = <cm>   # Additional acoustic path length
```

### 9. Maximum SPL Parameters
```
|MAXIMUM SPL PARAMETER VALUES:

Pamp = <W>          # Amplifier power
Vamp = <V>          # Amplifier voltage
Iamp = <A>          # Amplifier current
Pmax = <W>          # Driver thermal power rating
Xmax = <mm>         # Driver maximum linear excursion

Maximum SPL Setting = <1-5>   # SPL calculation method
```

### 10. Absorbent Filling Material
```
|ABSORBENT FILLING MATERIAL PARAMETER VALUES:

Fr1 = <Hz>          # Fill material frequency 1
Fr2 = <Hz>          # Fill material frequency 2
Fr3 = <Hz>          # Fill material frequency 3
Fr4 = <Hz>          # Fill material frequency 4

Tal1 = <value>      # Fill material absorption 1
Tal2 = <value>      # Fill material absorption 2
Tal3 = <value>      # Fill material absorption 3
Tal4 = <value>      # Fill material absorption 4
```

### 11. Active Band Pass Filter
```
|ACTIVE BAND PASS FILTER PARAMETER VALUES:

High Pass Frequency = <Hz>
High Pass Slope = <1-6>
Low Pass Frequency = <Hz>
Low Pass Slope = <1-6>

Butterworth High Pass Order = <1-8>
Butterworth Low Pass Order = <1-8>
Linkwitz-Riley High Pass Order = <2-8>
Linkwitz-Riley Low Pass Order = <2-8>
Bessel High Pass Order = <1-8>
Bessel Low Pass Order = <1-8>

2nd Order High Pass Q = <0.5-10.0>
2nd Order Low Pass Q = <0.5-10.0>
4th Order High Pass Q = <0.5-10.0>
4th Order Low Pass Q = <0.5-10.0>

Active Filter Alignment = <1>
Active Filter On / Off Switch = <0/1>
```

### 12. Passive Filter
```
|PASSIVE FILTER PARAMETER VALUES:

Series / Parallel 1 = <S/P>
Series / Parallel 2 = <S/P>
Series / Parallel 3 = <S/P>
Series / Parallel 4 = <S/P>
```

### 13. Equalizer Filter
```
|EQUALISER FILTER PARAMETER VALUES:

Band 1 Frequency = <Hz>
Band 1 Q Factor = <0.01-10.0>
Band 1 Gain = <dB>
Band 1 Type = <-1 to 3>
...
Band 6 Frequency = <Hz>
Band 6 Q Factor = <0.01-10.0>
Band 6 Gain = <dB>
Band 6 Type = <-1 to 3>
```

### 14. Status Flags
```
|STATUS FLAGS:

Auto Path Flag = <0/1>
Lossy Inductance Model Flag = <0/1>
Semi-Inductance Model Flag = <0/1>
Damping Model Flag = <0/1>
Closed Mouth Flag = <0/1>
Continuous Flag = <0/1>
End Correction Flag = <0/1>
```

### 15. Other Settings
```
|OTHER SETTINGS:

Filter Type Index = <0>
Filter Input Index = <0>
Filter Output Index = <0>

Filter Type = <1>

MEH Configuration = <0>
ME Amplifier Polarity Value = <1>
```

---

## Hornresp Flare Types

### Exponential (EXP)
Area function: `S(x) = S₁ · exp(2mx)`
Flare constant: `m = ln(S₂/S₁) / (2L)`
Cutoff frequency: `fc = c·m / (2π)`

### Conical (CON)
Area function: `S(x) = S₁ · (1 + x/X)²`
No theoretical cutoff

### Hyperbolic (HYP)
Area function: `S(x) = S₁ · [cosh(mx) + T·sinh(mx)]²`
T parameter:
- `T = 0`: Catenoidal
- `T = 1`: Exponential
- `T < 1`: Cosh family
- `T > 1`: Sinh family

### Tractrix (TRA)
Area function derived from tractrix curve
No simple closed-form T-matrix

### Le Cléac'h (LEC)
Modern horn profile by Jean-Michel Le Cléac'h
Similar to tractrix with different curvature

---

## Key Constants

```
c = 343.5 to 343.7 m/s   # Speed of sound at 20°C
ρ₀ = 1.18 to 1.204 kg/m³ # Air density at 20°C
```

---

## Unit Conversions

| Parameter | Hornresp Unit | SI Unit | Conversion |
|-----------|---------------|---------|------------|
| Area | cm² | m² | ÷ 10000 |
| Length | cm | m | ÷ 100 |
| Volume | L | m³ | ÷ 1000 |
| Mass | g | kg | ÷ 1000 |
| Compliance | mm/N | m/N | ÷ 1000 |
| Inductance | mH | H | ÷ 1000 |

---

## Export Example (from code)

```
viberesp export hornresp 18DS115 \
    -e front_loaded_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --rear-chamber 100 \
    --front-chamber 6 \
    -o design.txt
```

---

*Generated from `src/viberesp/validation/hornresp_exporter.py`*
