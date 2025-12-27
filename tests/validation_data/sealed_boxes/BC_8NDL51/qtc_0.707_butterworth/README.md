# Sealed Box Validation Case: Qtc = 0.707

**Driver:** BC_8NDL51-8
**Alignment:** Butterworth (maximally flat) ✓
**Box Volume:** 31.65 L
**System Resonance:** 86.1 Hz

## Description

Maximally flat amplitude response in the passband.

## Hornresp Simulation Instructions

1. **Import the Hornresp file**
   - Open Hornresp
   - File → Open → Select `BC_8NDL51_qtc0.707.txt`
   - Verify: Ang=0.5xPi, Vrc=31.65, Lrc=<auto>

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
| System Resonance (Fc) | 86.1 Hz | ±0.5 Hz |
| System Q (Qtc) | 0.707 | ±0.02 |
| -3dB Frequency (F3) | 86.1 Hz | ±0.5 Hz |
| Compliance Ratio (α) | 0.32 | ±0.01 |

## Key Validation Frequencies

When analyzing results, pay special attention to:

- **Fc/2** (43.1 Hz) - Below resonance
- **Fc** (86.1 Hz) - At resonance (impedance peak)
- **2×Fc** (172.3 Hz) - Above resonance
- **F3** (86.1 Hz) - -3dB cutoff point
- **1 kHz** - Midrange reference
- **10 kHz** - High-frequency reference

## Literature

- Small (1972) - Closed-Box Loudspeaker Systems Part I: Analysis
- Reference: `literature/thiele_small/small_1972_closed_box.md`
