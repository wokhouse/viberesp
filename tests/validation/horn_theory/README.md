# Horn Theory Validation

This directory contains validation data for pure horn theory simulations, validating the T-matrix implementation against Hornresp without driver coupling.

## Purpose

Validates the core acoustic horn theory:
- T-matrix calculation for exponential horns
- Throat impedance transformation
- Mouth radiation impedance
- Cutoff frequency behavior

**This is NOT driver validation** - it validates horn physics independently of any specific driver.

## Test Case 1: Exponential Midrange Horn

**Directory:** `exp_midrange_tc1/`

**Parameters:**
- Throat area (S1): 50 cm²
- Mouth area (S2): 500 cm²
- Length (L12): 30 cm
- Flare type: Exponential
- Cutoff frequency (fc): 210.11 Hz
- Expansion ratio: 10:1
- Radiation: Half-space (infinite baffle, 2π)

**Chambers:**
- Throat chamber: None (Vtc = 0, Atc = S1)
- Rear chamber: None (Vrc = 0, open back)

**Files:**
- `horn_params.txt` - Hornresp input parameters
- `sim.txt` - Hornresp simulation results (acoustical impedance)
- `metadata.json` - Validation metadata and criteria

## Validation Criteria

| Frequency Range | Magnitude Tolerance | Phase Tolerance |
|---|---|---|
| f > 420 Hz (2×fc) | < 1% | < 2° |
| 210 < f ≤ 420 Hz | < 3% | < 5° |
| f ≤ 210 Hz | < 10% | Qualitative only |

## Usage

```python
from viberesp.simulation import ExponentialHorn, exponential_horn_throat_impedance
from viberesp.hornresp.results_parser import load_hornresp_sim_file

# Define horn geometry
horn = ExponentialHorn(
    throat_area=0.005,  # 50 cm²
    mouth_area=0.05,    # 500 cm²
    length=0.3          # 30 cm
)

# Calculate throat impedance
frequencies = np.logspace(1, 4, 200)
z_throat = exponential_horn_throat_impedance(frequencies, horn)

# Load Hornresp reference
hr_data = load_hornresp_sim_file('tests/validation/horn_theory/exp_midrange_tc1/sim.txt')

# Compare results...
```

## Literature

- Kolbrek, B. "Horn Loudspeaker Simulation Part 1: Radiation and T-Matrix"
- Beranek (1954), Eq. 5.20 - Piston radiation impedance
- Olson (1947), Eq. 5.18 - Exponential horn cutoff frequency

## Status

- ✅ Implementation complete (src/viberesp/simulation/horn_theory.py)
- ✅ Unit tests passing (22/22)
- ⏳ Hornresp validation pending
