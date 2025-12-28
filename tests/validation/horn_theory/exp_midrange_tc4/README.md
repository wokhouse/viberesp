# Test Case 4: Driver + Horn + Both Chambers

## Purpose
Validate complete front-loaded horn system with both throat and rear chambers.

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
  - Atc: 5 cm²

- **Rear Chamber**: 2.0 liters
  - Vrc: 2.0 L (sealed box behind driver)

## Validation Goals
1. Complete system with both chambers
2. Throat chamber compliance (series element)
3. Rear chamber compliance (shunt element)
4. Full electromechanical chain validation
5. Complex interaction between compliances

## Expected Results
- Both chambers affect impedance
- Complex interaction between throat and rear compliances
- Multiple resonances possible
- System resonance lower than driver Fs

## Files
- `horn_params.txt` - Hornresp input file (import this)
- `sim.txt` - Hornresp simulation results (run Hornresp to generate)
- `README.md` - This file

## Hornresp Setup
1. Import `horn_params.txt` into Hornresp
2. Set frequency range: 10 Hz - 10 kHz, 10 points/octave
3. Export Electrical Impedance
4. Export Acoustical Impedance
5. Export SPL
6. Save as `sim.txt`
