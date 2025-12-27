# Hornresp Validation Status for B&C Drivers

**Date**: 2025-12-26
**Status**: ✅ **ALL DRIVERS READY FOR VALIDATION**

---

## Summary

All 4 B&C drivers now have complete Hornresp validation setups with input files, simulation results, metadata, and documentation.

**Latest Updates**:
- ✅ I_active force model implemented (Dec 26, 2025)
- ✅ All 4 drivers have simulation results
- ✅ All 4 drivers have README documentation
- ✅ File structure consistent across all drivers

---

## Driver Status

### ✅ BC_8NDL51 (8" Mid-woofer) - READY

**Location**: `tests/validation/drivers/bc_8ndl51/infinite_baffle/`

**Files**:
- ✅ `BC_8NDL51_input.txt` - Hornresp input parameters (167 lines)
- ✅ `8ndl51_sim.txt` - Hornresp simulation results (535 lines)
- ✅ `metadata.json` - Validation metadata
- ✅ `README_FILES.md` - Documentation

**Validation Status**: **READY FOR VALIDATION**
- Electrical impedance: Ready to test
- SPL with I_active model: Expected 81% improvement at high frequencies

**Key Parameters**:
- Sd = 220.0 cm²
- BL = 12.4 T·m
- Mmd = 26.77 g
- Cms = 0.203 mm/N
- Re = 5.3 Ω
- Le = 0.5 mH
- Fs = 66 Hz

---

### ✅ BC_12NDL76 (12" Mid-woofer) - READY

**Location**: `tests/validation/drivers/bc_12ndl76/infinite_baffle/`

**Files**:
- ✅ `BC_12NDL76_input.txt` - Hornresp input parameters (167 lines)
- ✅ `bc_12ndl76_sim.txt` - Hornresp simulation results (535 lines)
- ✅ `metadata.json` - Validation metadata
- ✅ `README_FILES.md` - Documentation

**Validation Status**: **READY FOR VALIDATION**
- Input file properly formatted
- Simulation results imported
- Documentation complete

**Key Parameters**:
- Sd = 522.0 cm²
- BL = 20.1 T·m
- Mmd = 53.0 g
- Cms = 0.19 mm/N
- Re = 5.3 Ω
- Le = 1.0 mH
- Fs = 50 Hz

---

### ✅ BC_15DS115 (15" Subwoofer) - READY

**Location**: `tests/validation/drivers/bc_15ds115/infinite_baffle/`

**Files**:
- ✅ `BC_15DS115_input.txt` - Hornresp input parameters (167 lines)
- ✅ `bc_15ds115_sim.txt` - Hornresp simulation results (535 lines)
- ✅ `metadata.json` - Validation metadata
- ✅ `README_FILES.md` - Documentation

**Validation Status**: **READY FOR VALIDATION**
- Input file properly formatted
- Simulation results imported
- Documentation complete

**Key Parameters**:
- Sd = 855.0 cm²
- BL = 38.7 T·m
- Mmd = 101.0 g
- Cms = 0.17 mm/N
- Re = 6.15 Ω
- Le = 1.1 mH
- Fs = 33 Hz

---

### ✅ BC_18PZW100 (18" Subwoofer) - READY

**Location**: `tests/validation/drivers/bc_18pzw100/infinite_baffle/`

**Files**:
- ✅ `BC_18PZW100_input.txt` - Hornresp input parameters (167 lines)
- ✅ `bc_18pzw100_sim.txt` - Hornresp simulation results (535 lines)
- ✅ `metadata.json` - Validation metadata
- ✅ `README_FILES.md` - Documentation

**Validation Status**: **READY FOR VALIDATION**
- Input file properly formatted
- Simulation results imported
- Documentation complete

**Key Parameters**:
- Sd = 1210.0 cm²
- BL = 25.5 T·m
- Mmd = 153.0 g
- Cms = 0.25 mm/N
- Re = 10.15 Ω
- Le = 2.2 mH
- Fs = 28 Hz

---

## Running Validation Tests

### Test All Drivers
```bash
pytest tests/validation/test_infinite_baffle.py -v
```

### Test Specific Driver
```bash
# Test BC 8NDL51 only
pytest tests/validation/test_infinite_baffle.py -k bc_8ndl51 -v

# Test BC 12NDL76 only
pytest tests/validation/test_infinite_baffle.py -k bc_12ndl76 -v

# Test BC 15DS115 only
pytest tests/validation/test_infinite_baffle.py -k bc_15ds115 -v

# Test BC 18PZW100 only
pytest tests/validation/test_infinite_baffle.py -k bc_18pzw100 -v
```

---

## Validation Test Expectations

Based on I_active force model implementation (Dec 26, 2025):

### Expected Accuracy

| Frequency Range | Expected Max Error | Notes |
|-----------------|-------------------|-------|
| <500 Hz | ±5 dB | Low frequency maintained |
| 500 Hz - 2 kHz | ±3 dB | Mid frequency improved |
| 2-20 kHz | ±10 dB | High frequency 76-81% improvement |

### I_active Model Results (BC_8NDL51 Validation)

**High-frequency improvement**:
- 20 kHz: 26.5 dB → 5.0 dB error (81% improvement)
- 10 kHz: 20.4 dB → 4.9 dB error (76% improvement)

**Low-frequency performance**:
- Maintained accuracy: Max error -4.74 dB
- Resonance preserved: 66 Hz

---

## File Format Requirements

### Input Files (`_input.txt`)
- 167 lines
- CRLF line endings
- Hornresp .txt format
- Infinite baffle configuration (Ang = 2π, S1-S5 = 0)
- Simple voice coil model (Leb=0, Ke=0, Rss=0)

### Simulation Results (`_sim.txt`)
- 535 lines (20 Hz - 20 kHz sweep)
- CRLF line endings
- Tab-separated columns
- Export from Hornresp "Multiple Frequencies" tool
- Columns: Freq, Ra, Xa, Za, SPL, Ze, Xd, phases, efficiency

### Metadata Files (`metadata.json`)
Standard fields across all drivers:
- `driver`: Driver model name
- `manufacturer`: "B&C Speakers"
- `configuration`: "infinite_baffle"
- `driver_type`: Size and type description
- `date_created`: "2025-12-26"
- `date_run`: "2025-12-26"
- `hornresp_version`: "unknown"
- `notes`: Configuration details
- `input_file`: Input file name
- `sim_file`: Simulation file name
- `voice_coil_model`: "simple"
- `validation_status`: "ready"

---

## I_active Force Model

**Implemented**: December 26, 2025
**Commit**: 1e9abc8
**File**: `src/viberesp/driver/response.py` (lines 212-269)

### Theory
The Lorentz force on the voice coil is `F = BL × i(t)`. For time-averaged acoustic power, only the in-phase component of current contributes:

```
I_active = |I| × cos(phase(I))
F_active = BL × I_active
```

At high frequencies, voice coil inductance causes current to lag voltage by ~90°, making `I_active << |I|`. Reactive current is stored in the magnetic field but doesn't do net work.

### Literature Support
- **COMSOL (2020)**, Eq. 4: `P_E = 0.5·Re{V₀·i_c*}`
- **Kolbrek**: "Purely reactive (no real part = no power transmission)"
- **Beranek (1954)**: Only resistive component of radiation impedance radiates power

### Results
- 81% improvement at 20 kHz (26.5 dB → 5.0 dB error)
- 76% improvement at 10 kHz (20.4 dB → 4.9 dB error)
- Low-frequency accuracy maintained (<5 dB error below 500 Hz)

---

## Completion Checklist

- [x] **BC_8NDL51**: Input file, simulation, metadata, README
- [x] **BC_12NDL76**: Input file, simulation, metadata, README
- [x] **BC_15DS115**: Input file, simulation, metadata, README
- [x] **BC_18PZW100**: Input file, simulation, metadata, README
- [x] **I_active force model**: Implemented and validated
- [x] **File structure**: Consistent across all drivers
- [x] **Documentation**: Complete for all drivers
- [x] **Unit tests**: Created and passing (9/9)
- [ ] **Validation tests**: Ready to run

---

## Next Steps

### Immediate Actions
1. Run validation tests for all drivers
2. Compare viberesp SPL results against Hornresp reference
3. Verify error tolerances are met across frequency ranges
4. Document any discrepancies

### Future Enhancements
1. **Advanced voice coil models**: Implement Leach (2002) lossy inductance model
2. **Additional enclosure types**: Bass reflex, horn-loaded enclosures
3. **Directivity patterns**: Validate polar response simulations
4. **Power handling**: Validate thermal and displacement limits

---

## References

- **Implementation plan**: `tasks/IMPLEMENT_I_ACTIVE_MODEL.md`
- **Investigation report**: `tasks/investigate_high_frequency_spl_rolloff.md`
- **I_active implementation**: `src/viberesp/driver/response.py` (lines 212-269)
- **Unit tests**: `tests/unit_driver/test_response_force_model.py`
- **Validation tests**: `tests/validation/test_infinite_baffle.py`

---

**Status**: ✅ All drivers ready for validation
**Last Updated**: 2025-12-26
