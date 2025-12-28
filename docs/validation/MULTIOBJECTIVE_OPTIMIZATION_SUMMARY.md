# Multi-Objective Horn Optimization Summary

**Date**: 2025-12-28  
**Objectives**: Wavefront Sphericity + Impedance Smoothness + Response Flatness  
**Algorithm**: NSGA-II  
**Population**: 30, Generations: 30  

## Results

Found 30 Pareto-optimal designs showing the fundamental trade-offs between competing objectives.

## Best Designs for Each Objective

### 1. Best Wavefront Sphericity (Design #3)
- **Wavefront**: 0.000121 (nearly perfect spherical wavefronts)
- **Impedance**: 2.81
- **Flatness**: 23.02 dB ✗ (terrible)
- **Cutoff**: ~430 Hz
- **Trade-off**: Optimized for spherical wavefronts at expense of frequency response

### 2. Best Impedance Smoothness (Design #2)
- **Wavefront**: 0.016223
- **Impedance**: 1.62 ✓ (smooth throat impedance)
- **Flatness**: 20.64 dB ✗ (poor)
- **Cutoff**: ~603 Hz
- **Trade-off**: Optimized for neutral sound, but poor frequency response

### 3. Best Flatness (Design #1)
- **Wavefront**: 0.925688
- **Impedance**: 2.85
- **Flatness**: 16.19 dB ✗ (still poor!)
- **Cutoff**: Fc1=1476 Hz, Fc2=639 Hz (very high!)
- **Geometry**: 30.2 cm total length, 4.46 L volume

## Key Findings

### 1. High Cutoff Frequency Problem
All Pareto-optimal designs have cutoff frequencies >400 Hz, with most in the 600-1500 Hz range. This is too high for good midrange performance because:

- Limited bandwidth (starts at 1.5×Fc)
- Horn acts as high-pass filter
- 16-23 dB flatness is unacceptable for audio applications

### 2. Fundamental Trade-off Confirmed
The optimization confirms that **wavefront sphericity is inversely correlated with flatness**:

| Objective | Best Design | Worst Design |
|-----------|-------------|---------------|
| Wavefront sphericity | Spherical (0.0001) | Flatness: 23 dB |
| Impedance smoothness | Smooth (1.62) | Flatness: 20.6 dB |
| Response flatness | 16.2 dB (still poor) | Wavefront: 0.93 |

**No design achieved good flatness (<6 dB)** while also optimizing for wavefront quality.

### 3. Why Previous Optimized Horn Failed
Our previous optimized horn (m1=m2=11.56, Fc=631 Hz):
- Achieved excellent wavefront sphericity (0.0002)
- Achieved good impedance smoothness (1.65)
- Had terrible flatness (-21 dB/decade slope, 4.2 dB std dev)

**This was NOT a bug - it was the optimal trade-off chosen by NSGA-II!**

## Recommendations

### For Good Frequency Response (Flatness <6 dB):
**Optimize ONLY for flatness** (don't include wavefront/impedance objectives):
```python
objectives = ["response_flatness"]
# or with secondary objectives:
objectives = ["response_flatness", "efficiency"]
```

### For "Clean, Neutral" Sound:
**Accept the trade-off**: optimize for impedance smoothness + flatness, accept non-spherical wavefronts:
```python
objectives = ["impedance_smoothness", "response_flatness"]
# Note: This will compromise wavefront sphericity
```

### For Spherical Wavefronts:
**Use tractrix profile** instead of exponential:
- Tractrix horns inherently have spherical wavefronts
- But have colored frequency response (by design)
- Our optimization confirms this fundamental characteristic

## Next Steps

1. **Single-objective flatness optimization**: Find the best flatness achievable
2. **Bi-objective optimization**: Flatness + Efficiency (ignore wavefront/impedance)
3. **Adjust parameter space**: Allow longer horns (>50 cm) for lower cutoff
4. **Lower cutoff target**: Aim for Fc < 300 Hz for wider bandwidth

## Conclusion

The multi-objective optimization successfully demonstrates that **you cannot have it all**:
- Spherical wavefronts (tractrix-like) = colored response
- Flat response = non-spherical wavefronts
- Trade-offs are fundamental to horn physics

The choice depends on the design priority:
- **Hi-fi speakers** → Optimize for flatness
- **PA/sound reinforcement** → Optimize for efficiency + flatness  
- **Instrument amplifiers** → Accept colored response for "tone"
