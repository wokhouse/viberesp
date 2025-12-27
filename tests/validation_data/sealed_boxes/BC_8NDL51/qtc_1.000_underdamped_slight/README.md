# Sealed Box Validation Case: Qtc = 1.000

**Driver:** BC_8NDL51-8
**Alignment:** Chebyshev-like (slight peak)
**Box Volume:** 6.16 L
**System Resonance:** 121.8 Hz

## Description

Slight bass peak (~1-2 dB), good transient response.

## Hornresp Simulation Instructions

1. **Import the Hornresp file**
   - Open Hornresp
   - File → Open → Select `BC_8NDL51_qtc1.000.txt`
   - Verify: Ang=0.5xPi, Vrc=6.16, Lrc=<auto>

2. **Configure sealed box**
   - Select "Rear Lined" (sealed box option)
   - This ensures the box is modeled as a sealed enclosure

3. **Set up frequency sweep**
   - Tools → Multiple Frequencies
   - Frequency range: 20 Hz - 20000 Hz
   - Number of points: 535 (Hornresp default)
   - Sweep type: Logarithmic
   - Input voltage: 2.83 V (1W into 8Ω)
   - Measurement distance: 1 m

4. **Run simulation**
   - Calculate
   - File → Save → Export _sim.txt
   - Save as: `sim.txt` in this directory

## Expected Results

Based on Small (1972) closed-box theory:

| Parameter | Expected Value | Tolerance |
|-----------|---------------|-----------|
| System Resonance (Fc) | 121.8 Hz | ±0.5 Hz |
| System Q (Qtc) | 1.000 | ±0.02 |
| -3dB Frequency (F3) | 95.8 Hz | ±0.5 Hz |
| Compliance Ratio (α) | 1.64 | ±0.01 |

## Key Validation Frequencies

When analyzing results, pay special attention to:

- **Fc/2** (60.9 Hz) - Below resonance
- **Fc** (121.8 Hz) - At resonance (impedance peak)
- **2×Fc** (243.7 Hz) - Above resonance
- **F3** (95.8 Hz) - -3dB cutoff point
- **1 kHz** - Midrange reference
- **10 kHz** - High-frequency reference

## Literature

- Small (1972) - Closed-Box Loudspeaker Systems Part I: Analysis
- Reference: `literature/thiele_small/small_1972_closed_box.md`
