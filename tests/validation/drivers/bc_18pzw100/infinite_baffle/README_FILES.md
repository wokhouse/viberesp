# BC 18PZW100 Hornresp Validation Files

## ✅ Validation Complete

### Driver Information
**Manufacturer**: B&C Speakers
**Model**: BC 18PZW100
**Type**: 18 inch woofer
**Configuration**: Infinite baffle (bare driver)

---

## Files in Directory

| File | Purpose | Status |
|------|---------|--------|
| `BC_18PZW100_input.txt` | Hornresp input parameters (167 lines) | ✅ Complete |
| `bc_18pzw100_sim.txt` | Hornresp simulation results (535 lines) | ✅ Complete |
| `metadata.json` | Validation metadata | ✅ Complete |

---

## Driver Parameters

### Thiele-Small Parameters
- **Sd** = 855.0 cm² (diaphragm area)
- **BL** = 38.7 T·m (force factor)
- **Mmd** = 153.0 g (moving mass)
- **Cms** = 0.25 mm/N (compliance)
- **Rms** = 10.15 N·s/m (mechanical resistance)
- **Le** = 2.2 mH (voice coil inductance)
- **Re** = 10.15 Ω (DC resistance)

### Hornresp Configuration
- **Voice coil model**: Simple (jωL inductor)
  - Lossy Inductance Model Flag = 0
  - Semi-Inductance Model Flag = 0
  - Leb = 0, Ke = 0, Rss = 0
- **Input voltage**: 2.83 V (1W into 8Ω)
- **Radiation angle**: 2π (infinite baffle)

---

## Simulation Details

**Frequency range**: 20 Hz - 20 kHz (535 points)
**Simulation type**: Multiple frequencies (electrical impedance + SPL)
**Output format**: Tab-separated text (CRLF line endings)

### Data Columns
- Freq (hertz)
- Ra, Xa, Za (normalized radiation impedance)
- SPL (dB) at 1m
- Ze (ohms) - electrical impedance magnitude
- Xd (mm) - diaphragm displacement
- Phase angles (W, U, C)
- Efficiency (%)
- ZePhase (deg) - electrical impedance phase

---

## Validation Status

**Expected accuracy** (with I_active force model):
| Frequency Range | Expected Max Error |
|-----------------|-------------------|
| <500 Hz | ±5 dB |
| 500 Hz - 2 kHz | ±3 dB |
| 2-20 kHz | ±10 dB |

---

## Usage

### Run Validation Test
```bash
pytest tests/validation/test_infinite_baffle.py -k bc_18pzw100 -v
```

### Load Results in Python
```python
from viberesp.hornresp.results_parser import load_hornresp_sim_file
from viberesp.driver.bc_drivers import get_bc_18pzw100

# Load Hornresp results
sim = load_hornresp_sim_file('tests/validation/drivers/bc_18pzw100/infinite_baffle/bc_18pzw100_sim.txt')

# Get driver parameters
driver = get_bc_18pzw100()
```

---

## Notes

- Parameters exported from viberesp driver definitions
- Simple voice coil model (no semi-inductance or lossy inductance)
- Suitable for low-frequency enclosure design validation
- For high-frequency accuracy (>2 kHz), I_active force model provides 76-81% improvement

---

**Created**: 2025-12-26
**Status**: ✅ Ready for validation
