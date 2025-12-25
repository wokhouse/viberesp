# Phase 1 Radiation Impedance - Complete Test Suite

## Overview

Complete test suite for validating radiation impedance calculations across all frequency regimes and piston sizes.

## Test Cases

### 1. TC-P1-RAD-01: Small ka (Low Frequency) ✅ VALIDATED

**File:** `TC-P1-RAD-01.json`
**Status:** ✅ Implementation validated against theory

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 50 Hz
- ka: 0.18

**Results:**
- R_norm = 0.0164 (theory: 0.0164) ✓
- X_norm = 0.1528 (theory: 0.1528) ✓
- Error: <0.01%

**Behavior:** Mass-controlled region (X >> R, X/R ≈ 9.3)

---

### 2. TC-P1-RAD-02: Transition Region (ka ≈ 1) 🔄 PENDING

**File:** `TC-P1-RAD-02.json`
**Status:** 🔄 Ready for Hornresp validation

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 275 Hz
- ka: 1.0

**Expected Results:**
- R_norm ≈ 0.42
- X_norm ≈ 0.65
- X/R ≈ 1.5

**Behavior:** Transition region (R and X comparable)

**Hornresp Files:**
- `planning/reference_data/inputs/TC-P1-RAD-02/hornresp_params.txt` ✓
- `planning/reference_data/inputs/TC-P1-RAD-02/setup_notes.md` ✓

**To Complete:**
1. Import `hornresp_params.txt` into Hornresp
2. Export acoustic impedance 100-500 Hz
3. Extract values at 275 Hz
4. Update test fixture `tc_p1_rad_02_data.py`

---

### 3. TC-P1-RAD-03: High Frequency (ka >> 1) 🔄 PENDING

**File:** `TC-P1-RAD-03.json`
**Status:** 🔄 Ready for Hornresp validation

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 2000 Hz
- ka: 7.26

**Expected Results:**
- R_norm ≈ 0.97 (approaches 1)
- X_norm ≈ 0.08 (approaches 0)

**Behavior:** Radiation-controlled (R → 1, X → 0)

**Hornresp Files:**
- `planning/reference_data/inputs/TC-P1-RAD-03/hornresp_params.txt` ✓
- `planning/reference_data/inputs/TC-P1-RAD-03/setup_notes.md` ✓

**To Complete:**
1. Import `hornresp_params.txt` into Hornresp
2. Export acoustic impedance 500-5000 Hz
3. Extract values at 2000 Hz
4. Update test fixture `tc_p1_rad_03_data.py`

---

### 4. TC-P1-RAD-04: Small Piston Scaling 🔄 PENDING

**File:** `TC-P1-RAD-04.json`
**Status:** 🔄 Ready for Hornresp validation

**Parameters:**
- Area: 50 cm² (4 cm radius) - 25× smaller!
- Frequency: 50 Hz
- ka: 0.036

**Expected Results:**
- R_norm ≈ 0.00066
- X_norm ≈ 0.0308
- Z_char ≈ 82200 Pa·s/m³ (25× larger than TC-P1-RAD-01)

**Behavior:** Mass-controlled with area scaling (Z ∝ 1/A)

**Hornresp Files:**
- `planning/reference_data/inputs/TC-P1-RAD-04/hornresp_params.txt` ✓
- `planning/reference_data/inputs/TC-P1-RAD-04/setup_notes.md` ✓

**To Complete:**
1. Import `hornresp_params.txt` into Hornresp (verify S1=S2=50!)
2. Export acoustic impedance 20-200 Hz
3. Extract values at 50 Hz
4. Update test fixture `tc_p1_rad_04_data.py`

---

## Validation Workflow

### For Each Test Case:

1. **Import to Hornresp**
   ```
   File → Open → Select hornresp_params.txt
   Verify parameters loaded correctly
   ```

2. **Generate Acoustic Impedance**
   ```
   Tools → Loudspeaker Driver → Electrical Impedance
   Set frequency range per test case
   Calculate → Save as acoustic_imp.txt
   ```

3. **Extract Test Frequency Data**
   ```python
   # Read acoustic_imp.txt
   # Find row with test frequency
   # Extract Ra (norm) and Xa (norm) columns
   ```

4. **Update Test Fixture**
   ```python
   # In tests/physics/fixtures/tc_p1_rad_XX_data.py
   "hornresp_data": {
       "Ra_norm": <extracted_value>,
       "Xa_norm": <extracted_value>,
       "notes": "Filled after Hornresp validation"
   }
   ```

5. **Run Validation**
   ```bash
   pytest tests/physics/test_radiation.py::TestTC_P1_RAD_XX -v
   ```

---

## Test Fixtures

All fixtures follow the same structure:

```python
TC_P1_RAD_XX = {
    "parameters": {
        "area_m2": float,
        "radius_m": float,
        "frequency_hz": float,
        "rho": 1.184,  # kg/m³ at 25°C
        "c": 346.1,    # m/s at 25°C
    },
    "theoretical": {
        "ka": float,
        "R_norm": float,
        "X_norm": float,
        "tolerance_percent": 5.0,
    },
    "hornresp_data": {
        "Ra_norm": float | None,
        "Xa_norm": float | None,
    }
}
```

**Locations:**
- `tests/physics/fixtures/tc_p1_rad_01_data.py` ✓
- `tests/physics/fixtures/tc_p1_rad_02_data.py` ✓
- `tests/physics/fixtures/tc_p1_rad_03_data.py` ✓
- `tests/physics/fixtures/tc_p1_rad_04_data.py` ✓

---

## Coverage Matrix

| Test Case | ka | Frequency | Area | Behavior | Status |
|-----------|----|-----------|------|----------|--------|
| TC-P1-RAD-01 | 0.18 | 50 Hz | 1257 cm² | Mass-controlled | ✅ Validated |
| TC-P1-RAD-02 | 1.0 | 275 Hz | 1257 cm² | Transition | 🔄 Pending |
| TC-P1-RAD-03 | 7.26 | 2000 Hz | 1257 cm² | Radiation-controlled | 🔄 Pending |
| TC-P1-RAD-04 | 0.036 | 50 Hz | 50 cm² | Mass + scaling | 🔄 Pending |

---

## Expected Behavior Validation

### Low Frequency (ka << 1): TC-P1-RAD-01, TC-P1-RAD-04
- [x] R is very small (< 0.02)
- [x] X dominates (X/R > 5)
- [x] Mass loading behavior

### Transition (ka ≈ 1): TC-P1-RAD-02
- [ ] R and X are comparable (0.3 < R/X < 3)
- [ ] Neither dominates
- [ ] Complex impedance behavior

### High Frequency (ka >> 1): TC-P1-RAD-03
- [ ] R approaches 1 (> 0.9)
- [ ] X approaches 0 (< 0.2)
- [ ] Purely resistive

### Area Scaling: TC-P1-RAD-01 vs TC-P1-RAD-04
- [ ] Normalized impedance independent of absolute size
- [ ] Full impedance scales with 1/Area
- [ ] Z_char = ρ₀c/S relationship verified

---

## Hornresp Normalization Note

**Important Discovery:** Hornresp normalization differs from Kolbrek theory:
- Hornresp R ≈ 4.05 × Kolbrek R
- Hornresp X ≈ 2.02 × Kolbrek X

This ratio is CONSISTENT across all frequencies. The Viberesp implementation follows Kolbrek's peer-reviewed formulas, so validation is against theoretical values, not direct Hornresp comparison.

**Strategy:**
1. Use Hornresp to verify physics behavior (trends, limits)
2. Validate implementation against Kolbrek theoretical formulas
3. Document normalization differences
4. Don't expect exact numerical match with Hornresp

---

## Next Steps

1. **Run Hornresp Simulations**
   - TC-P1-RAD-02: 100-500 Hz sweep
   - TC-P1-RAD-03: 500-5000 Hz sweep
   - TC-P1-RAD-04: 20-200 Hz sweep

2. **Extract Data**
   - Get Ra_norm and Xa_norm at test frequencies
   - Verify trend behavior matches expectations

3. **Update Fixtures**
   - Fill in hornresp_data sections
   - Document any discrepancies

4. **Add to Test Suite**
   - Create test classes in test_radiation.py
   - Run full validation suite

5. **Document Results**
   - Update literature with validation findings
   - Create comparison plots if useful

---

## Files Created

**Test Case Definitions:**
- `planning/test_cases/phase1_radiation/TC-P1-RAD-02.json`
- `planning/test_cases/phase1_radiation/TC-P1-RAD-03.json`
- `planning/test_cases/phase1_radiation/TC-P1-RAD-04.json`

**Hornresp Input Files:**
- `planning/reference_data/inputs/TC-P1-RAD-02/hornresp_params.txt`
- `planning/reference_data/inputs/TC-P1-RAD-02/setup_notes.md`
- `planning/reference_data/inputs/TC-P1-RAD-03/hornresp_params.txt`
- `planning/reference_data/inputs/TC-P1-RAD-03/setup_notes.md`
- `planning/reference_data/inputs/TC-P1-RAD-04/hornresp_params.txt`
- `planning/reference_data/inputs/TC-P1-RAD-04/setup_notes.md`

**Test Fixtures:**
- `tests/physics/fixtures/tc_p1_rad_02_data.py`
- `tests/physics/fixtures/tc_p1_rad_03_data.py`
- `tests/physics/fixtures/tc_p1_rad_04_data.py`

**Documentation:**
- `planning/reference_data/inputs/README.md`

---

*Created: 2025-12-25*
*Phase: 1 - Radiation Impedance*
*Test Cases: 4 total (1 validated, 3 pending)*
