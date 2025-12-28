# Test Case 3: Driver + Horn + Throat Chamber

## Purpose
Validate throat chamber compliance effect on horn-loaded driver.

## System Configuration
- **Driver**: Compression driver (B&C DE10-style)
  - S_d: 8 cm²
  - M_md: 8g
  - BL: 12 T·m
  - R_e: 6.5 Ω

- **Horn**: Exponential
  - Throat area (S1): 5 cm²
  - Mouth area (S2): 200 cm²
  - Length (L12): 50 cm
  - Cutoff frequency: ~630 Hz

- **Throat Chamber**: 0.5 liters
  - Vtc: 0.5 L
  - Atc: 5 cm² (equals throat area)

- **Rear Chamber**: None
  - Vrc = 0 (open back)

## Validation Goals
1. Throat chamber adds series compliance to horn impedance
2. Electrical impedance shows chamber-related effects
3. Comparison with TC2 shows throat chamber impact
4. Compliance resonance is visible

## Expected Results
- Throat chamber creates additional compliance
- Impedance shifts compared to TC2
- Possible resonance from throat chamber compliance
- Lower frequency resonance due to added compliance

## Files
- `horn_params.txt` - Hornresp input file (import this)
- `sim.txt` - Hornresp simulation results (run Hornresp to generate)
- `README.md` - This file

## Hornresp Setup
1. Import `horn_params.txt` into Hornresp
2. Set frequency range: 10 Hz - 10 kHz, 10 points/octave
3. Export Electrical Impedance
4. Export Acoustical Impedance
5. Save as `sim.txt`
