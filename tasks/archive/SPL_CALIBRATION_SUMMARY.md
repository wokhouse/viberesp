# SPL Transfer Function Calibration - Implementation Summary

**Status:** ✅ Scripts Ready - Awaiting Hornresp Data
**Date:** 2025-12-27

---

## ✅ What's Been Completed

### 1. Code Review
- ✅ Reviewed transfer function implementation in `sealed_box.py` (line 270)
- ✅ Reviewed transfer function implementation in `ported_box.py` (line 686)
- ✅ Confirmed both use Small (1972) reference efficiency formula
- ✅ Identified calibration point: `spl_ref` calculation

### 2. Hornresp Test Files Created
- ✅ `tests/validation/drivers/bc_8ndl51/sealed/bc_8ndl51_sealed_10l.txt`
- ✅ `tests/validation/drivers/bc_15ds115/ported/bc_15ds115_ported_180l.txt`

### 3. Validation & Analysis Scripts
All scripts created and tested:

| Script | Purpose | Status |
|--------|---------|--------|
| `tasks/export_hornresp_test_cases.py` | Exports designs to Hornresp format | ✅ Complete |
| `tasks/validate_transfer_function_calibration.py` | Compares viberesp vs Hornresp | ✅ Complete |
| `tasks/analyze_spl_offset.py` | Analyzes offset between SPL methods | ✅ Complete |
| `tasks/apply_spl_calibration.py` | Applies calibration to transfer functions | ✅ Complete |

### 4. Initial Analysis Results

**Sealed Box (BC_8NDL51, 10L):**
```
Consistent offset: +37.4 dB vs impedance coupling
- At 20 Hz:  +37.4 dB
- At 100 Hz: +37.7 dB
- At 500 Hz: +37.3 dB
```

**Ported Box (BC_15DS115, 180L):**
```
Variable offset: +18.7 dB average vs impedance coupling
- At 20 Hz:  +45.6 dB
- At 100 Hz: +17.5 dB
- At 500 Hz: -13.8 dB
```

**Key Finding:** Sealed box has consistent offset (~37 dB), suggesting a simple calibration constant will fix it. Ported box needs Hornresp validation (impedance coupling not reliable for ported boxes).

---

## ⏸️ User Action Required

### BLOCKER: Hornresp Simulation Data Needed

The calibration process is BLOCKED until Hornresp simulation data is available.

### Step-by-Step Instructions

#### 1. Run Hornresp for BC_8NDL51 Sealed Box

```
1. Open Hornresp
2. File → Import → tests/validation/drivers/bc_8ndl51/sealed/bc_8ndl51_sealed_10l.txt
3. Tools → Loudspeaker Wizard (or F10)
4. File → Export → SPL Response
5. Save as: tests/validation/drivers/bc_8ndl51/sealed/spl_hornresp.csv
```

**Simulation parameters:**
- Frequencies: 20, 28, 40, 50, 70, 100, 150, 200, 300, 500 Hz
- Input: 2.83V (1W into 8Ω)
- Distance: 1m

#### 2. Run Hornresp for BC_15DS115 Ported Box

```
1. Open Hornresp
2. File → Import → tests/validation/drivers/bc_15ds115/ported/bc_15ds115_ported_180l.txt
3. Tools → Loudspeaker Wizard (or F10)
4. File → Export → SPL Response
5. Save as: tests/validation/drivers/bc_15ds115/ported/spl_hornresp.csv
```

**Simulation parameters:**
- Same frequencies, input voltage, and distance as above

#### 3. Run Validation Script

```bash
PYTHONPATH=src python3 tasks/validate_transfer_function_calibration.py
```

**Expected output:**
- Comparison table showing viberesp vs Hornresp SPL at each frequency
- Average offset calculation
- Recommended calibration constant
- Pass/fail criteria check

#### 4. Apply Calibration

Once validation script reports the calibration offset:

```bash
# Edit tasks/apply_spl_calibration.py
# Update CALIBRATION_OFFSET_DB with the value from validation

PYTHONPATH=src python3 tasks/apply_spl_calibration.py
```

This will automatically update:
- `src/viberesp/enclosure/sealed_box.py` (line ~270)
- `src/viberesp/enclosure/ported_box.py` (line ~686)

#### 5. Verify Calibration

```bash
PYTHONPATH=src python3 tasks/validate_transfer_function_calibration.py
```

**Success criteria:**
- ✅ Average offset < 0.5 dB
- ✅ Max deviation < 2 dB
- ✅ Frequency response shape correct

---

## 📁 Files Created

### Validation Infrastructure
```
tasks/
├── export_hornresp_test_cases.py           # Export driver designs to Hornresp
├── validate_transfer_function_calibration.py # Compare viberesp vs Hornresp
├── analyze_spl_offset.py                    # Analyze offset between SPL methods
├── apply_spl_calibration.py                 # Apply calibration to code
├── SPL_CALIBRATION_INSTRUCTIONS.md          # Detailed instructions
└── SPL_CALIBRATION_SUMMARY.md               # This file

tests/validation/drivers/
├── bc_8ndl51/sealed/
│   ├── bc_8ndl51_sealed_10l.txt           # Hornresp input (sealed box)
│   └── spl_hornresp.csv                    # TODO: Create this file
└── bc_15ds115/ported/
    ├── bc_15ds115_ported_180l.txt          # Hornresp input (ported box)
    └── spl_hornresp.csv                    # TODO: Create this file
```

---

## 🔬 Technical Details

### Current Implementation

Both transfer functions use Small (1972) reference efficiency formula:

```python
# Reference efficiency (Small 1972)
eta_0 = (air_density / (2 * math.pi * speed_of_sound)) * \
        ((4 * math.pi ** 2 * driver.F_s ** 3 * driver.V_as) / driver.Q_es)

# Efficiency reduced by box stiffness
eta = eta_0 / (1.0 + alpha)

# Reference SPL
spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0
```

### Calibration Point

The calibration will be applied immediately after `spl_ref` calculation:

```python
spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0

# CALIBRATION: Adjust reference SPL to match Hornresp
CALIBRATION_OFFSET_DB = -XX.X  # To be determined
spl_ref += CALIBRATION_OFFSET_DB
```

### Expected Calibration Value

Based on initial analysis, we expect approximately **-37 dB** for sealed boxes. However, the exact value MUST be determined by comparison with Hornresp, not by analysis of the impedance coupling method.

---

## 📊 Validation Criteria

After applying calibration, all criteria must be met:

1. **Accuracy**
   - Average offset between viberesp and Hornresp < 0.5 dB
   - Maximum deviation at any frequency < 2 dB

2. **Frequency Response Shape**
   - Sealed box: 2nd-order high-pass (12 dB/octave rolloff)
   - Ported box: 4th-order high-pass (24 dB/octave rolloff)
   - SPL must roll off at high frequencies

3. **Universal Applicability**
   - Works for sealed boxes
   - Works for ported boxes
   - Works for multiple drivers (different BL, Qts, Vas)

4. **Optimizer Performance**
   - Flatness optimizer finds truly flat responses
   - No rising response artifacts

---

## 🚀 Next Steps (After Calibration)

1. **Test with Additional Drivers**
   - BC_12TK76 (if available)
   - Other drivers with varying parameters
   - Verify calibration works universally

2. **Test Flatness Optimizer**
   ```bash
   PYTHONPATH=src python3 tasks/test_optimizer_flatness.py
   ```
   - Verify optimizer finds truly flat responses
   - Check that calibration doesn't break optimization

3. **Update Unit Tests**
   - Add calibration constant to test fixtures
   - Verify tests pass with new calibration

4. **Document Results**
   - Update `docs/validation/spl_calibration_results.md`
   - Document calibration value and validation results
   - Note any limitations or special cases

---

## 📖 Reference Materials

### Literature
- `literature/thiele_small/small_1972_closed_box.md` - Small (1972) closed box theory
- `literature/thiele_small/thiele_1971_vented_boxes.md` - Thiele (1971) ported box theory

### Documentation
- `docs/validation/transfer_function_spl_implementation.md` - Implementation summary
- `docs/validation/sealed_box_spl_research_summary.md` - Previous research
- `docs/validation/ported_box_impedance_fix.md` - Ported box impedance fix

### Scripts
- `tasks/agent_instructions_spl_transfer_function.md` - Original task instructions

---

## ❓ FAQ

**Q: Why can't we just use the -37 dB from the impedance coupling comparison?**

A: The impedance coupling method may have its own inaccuracies, especially for ported boxes. We need to calibrate against Hornresp (the industry standard) to ensure absolute accuracy.

**Q: Will the same calibration work for both sealed and ported boxes?**

A: Unknown - that's what we're testing. If the calibration offsets differ significantly, it may indicate a problem with the efficiency formula for one or both enclosure types.

**Q: What if the calibration varies by frequency?**

A: That would indicate a problem with the transfer function itself, not just the reference level. We'd need to investigate the numerator of the transfer function more carefully.

**Q: Can I run Hornresp simulations with different frequencies?**

A: Yes, but the validation script expects specific frequencies. If you use different frequencies, you'll need to update `TEST_FREQUENCIES` in the validation script.

---

## ✅ Checklist

- [x] Review transfer function implementation
- [x] Create Hornresp export files
- [x] Create validation scripts
- [x] Run initial offset analysis
- [x] Create calibration application script
- [x] Document instructions
- [ ] **Run Hornresp simulations (USER ACTION)**
- [ ] Validate against Hornresp
- [ ] Apply calibration
- [ ] Verify calibration
- [ ] Test with additional drivers
- [ ] Test flatness optimizer
- [ ] Document final results

---

**Last updated:** 2025-12-27
**Agent:** Claude Code
**Status:** Awaiting Hornresp data from user
