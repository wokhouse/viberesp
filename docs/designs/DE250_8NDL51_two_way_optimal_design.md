# Two-Way Speaker Design: BC_DE250 + BC_8NDL51

**Date:** 2026-01-01
**Optimization Goals:** Maximum flatness + Wavefront sphericity

## Design Summary

This two-way loudspeaker system combines the BC_8NDL51 8" midrange driver with the BC_DE250 compression driver, optimized for both flat frequency response and spherical wavefront propagation through a multi-segment horn design.

---

## System Specifications

### Low Frequency Driver: BC_8NDL51
- **Enclosure Type:** Ported (B4 alignment)
- **Box Volume (Vb):** 10.1 L
- **Tuning Frequency (Fb):** 75 Hz
- **Expected F3:** 90.6 Hz
- **Rationale:** Ported enclosure provides good bass extension for the driver's Qts=0.62

### High Frequency Driver: BC_DE250
- **Horn Type:** Multi-segment (2-segment optimized)
- **Horn Cutoff (fc):** 251 Hz
- **Horn Length:** 35.0 cm
- **Mouth Area:** 500 cm² (≈ 25 cm diameter)
- **Optimization Objectives:** Wavefront sphericity + Impedance smoothness
- **Rationale:** Multi-segment horn provides improved wavefront sphericity compared to single exponential profile

### Crossover Network
- **Crossover Frequency:** 1584 Hz
- **Filter Type:** 4th-order Linkwitz-Riley (LR4)
- **LF Padding:** 0 dB
- **HF Padding:** -19.2 dB (L-pad required)
- **Estimated Ripple:** <1 dB (after padding)

---

## Performance Characteristics

### Frequency Response
- **Bass Extension:** F3 = 90.6 Hz
- **Passband Ripple:** <1 dB (optimized)
- **System Sensitivity:** ~89 dB (2.83V, 1m)
  - Limited by LF driver sensitivity
  - HF driver padding reduces system sensitivity to match LF

### Wavefront Quality
- **Optimization Method:** Multi-segment horn profile
- **Objective Function:** Minimized wavefront distortion
- **Result:** Improved spherical wavefront compared to exponential horn

### System Alignment
- **Crossover Selection:** Based on driver response overlap
- **LF Driver at XO:** Beginning natural rolloff (-3 dB/octave)
- **HF Driver at XO:** Flat response in crossover region
- **Phase Match:** LR4 provides in-phase summation at crossover

---

## Design Rationale

### Why Ported for BC_8NDL51?
- Qts = 0.62 is ideal for ported enclosure
- Vas = 10.1 L makes for compact design
- B4 alignment (Vb=Vas, Fb=Fs) provides good balance

### Why Multi-Segment Horn for BC_DE250?
- **Wavefront Sphericity:** Multi-segment profiles reduce wavefront distortion
- **Cutoff Frequency:** 251 Hz provides safe margin below crossover (1584 Hz)
- **Mouth Size:** 500 cm² ensures good directivity control at crossover frequency
- **Optimization:** NSGA-II algorithm balanced wavefront quality vs impedance smoothness

### Why 1584 Hz Crossover?
- **Driver Overlap:** Both drivers have smooth response in 1200-2000 Hz range
- **LF Capability:** BC_8NDL51 can extend to ~2 kHz without break-up
- **HF Capability:** BC_DE250 on horn can play down to ~800 Hz
- **Optimal Region:** 1584 Hz is in "sweet spot" for both drivers

---

## Construction Notes

### LF Enclosure
- **Internal Volume:** 10.1 L (net, after driver/port displacement)
- **Port Tuning:** 75 Hz (adjust port length for final tuning)
- **Recommended Port Size:** 5 cm diameter × 15 cm length (adjust for exact Fb)
- **Material:** 18mm MDF recommended

### HF Horn
- **Profile:** 2-segment expansion
  - Segment 1: 6.5 cm² → 121.5 cm² over 21.5 cm
  - Segment 2: 121.5 cm² → 598.2 cm² over 22.5 cm
- **Throat:** Accepts standard 1" (25.4 mm) compression driver
- **Mouth:** 25 cm diameter
- **Material:** Cast or CNC-machined (smooth surfaces critical)

### Crossover Implementation
- **Filter Topology:** LR4 = two cascaded 2nd-order Butterworth sections
- **HF Attenuation:** 19.2 dB L-pad required
  - Can implement as: 15Ω series + 6.8Ω parallel (approximately)
  - Use non-inductive resistors rated for HF power
- **Component Quality:** Polypropylene capacitors, air-core inductors recommended

---

## Validation Recommendations

### Measure and Verify
1. **Impedance:** Check both drivers individually and combined
2. **Frequency Response:** Measure on-axis and off-axis (±30°)
3. **Crossover Alignment:** Verify LR4 summation is flat
4. **Horn Performance:** Check directivity and wavefront quality
5. **Bass Tuning:** Adjust Fb if necessary for room placement

### Expected Measurements
- **On-Axis Response:** ±2 dB from 90 Hz - 20 kHz
- **Impedance:** No wild peaks, smooth transition at crossover
- **Directivity:** Controlled pattern above 2 kHz from horn

---

## Design Files

- **Parameters:** `tasks/results/DE250_8NDL51_two_way_design.json`
- **Response Plot:** `tasks/results/DE250_8NDL51_two_way_response.png`
- **Optimization Script:** `tasks/two_way_DE250_8NDL51_optimal.py`

---

## Literature References

- Small (1972) - Closed and vented box design
- Thiele (1971) - Vented box alignments
- Linkwitz (1976) - Active crossover networks
- Olson (1947) - Exponential horn theory
- Beranek (1954) - Acoustic impedance and radiation
- Kolbrek - Horn theory and T-matrix methods

---

## Notes

- **HF Padding:** The -19.2 dB padding is significant. This is normal when combining high-sensitivity compression drivers (108.5 dB) with moderate-sensitivity woofers (~89 dB).
- **Alternative:** If higher sensitivity is desired, consider a more sensitive LF driver or accept the HF padding.
- **Horn Optimization:** The multi-segment horn was optimized for wavefront sphericity, which is critical for imaging and soundstage quality.
- **Crossover Frequency:** 1584 Hz is a compromise. Lower crossovers (1200 Hz) would reduce LF beaming but require HF padding. Higher crossovers (2000 Hz) would increase LF beaming at crossover.

---

**Design Generated by:** Viberesp CLI Tool
**Validation:** Compare with Hornresp for horn response validation
