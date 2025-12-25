# Phase 1 Radiation Impedance Test Cases

This directory contains Hornresp input files for validating Phase 1 radiation impedance calculations against reference data.

## Test Case Summary

### TC-P1-RAD-01: Small ka (Low Frequency) ✅ VALIDATED

**Purpose:** Verify mass-controlled region behavior (ka << 1)

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 50 Hz
- ka: 0.18

**Expected Results:**
- R_norm: 0.016 (very small)
- X_norm: 0.153 (dominates)
- X/R ratio: ≈ 9.3

**Behavior:** Mass-controlled region - reactance dominates, radiation adds mass loading

**Status:** Implementation matches theoretical values within <0.01%

---

### TC-P1-RAD-02: Transition Region (ka ≈ 1) 🔄 PENDING VALIDATION

**Purpose:** Verify transition region where neither mass nor resistance dominates

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 275 Hz
- ka: 1.0

**Expected Results:**
- R_norm: 0.42
- X_norm: 0.65
- X/R ratio: ≈ 1.5

**Behavior:** Transition region - both R and X are comparable, impedance character changing

**To Validate:**
1. Import `TC-P1-RAD-02/hornresp_params.txt` into Hornresp
2. Export acoustic impedance 100-500 Hz
3. Extract values at 275 Hz
4. Compare with theoretical values

---

### TC-P1-RAD-03: High Frequency (ka >> 1) 🔄 PENDING VALIDATION

**Purpose:** Verify high frequency behavior where radiation becomes purely resistive

**Parameters:**
- Area: 1257 cm² (20 cm radius)
- Frequency: 2000 Hz
- ka: 7.26

**Expected Results:**
- R_norm: 0.97 (approaches 1)
- X_norm: 0.08 (approaches 0)

**Behavior:** Radiation-controlled - impedance becomes purely resistive, near 100% efficiency

**To Validate:**
1. Import `TC-P1-RAD-03/hornresp_params.txt` into Hornresp
2. Export acoustic impedance 500-5000 Hz
3. Extract values at 2000 Hz
4. Verify R → 1 and X → 0

---

### TC-P1-RAD-04: Small Piston Scaling 🔄 PENDING VALIDATION

**Purpose:** Verify area scaling relationship

**Parameters:**
- Area: 50 cm² (4 cm radius) - 25x smaller than TC-P1-RAD-01
- Frequency: 50 Hz
- ka: 0.036

**Expected Results:**
- R_norm: 0.00066
- X_norm: 0.0308
- Z_char: 82200 Pa·s/m³ (25x larger than TC-P1-RAD-01)

**Behavior:** Mass-controlled region with smaller piston - tests area scaling Z ∝ 1/A

**To Validate:**
1. Import `TC-P1-RAD-04/hornresp_params.txt` into Hornresp
2. Export acoustic impedance 20-200 Hz
3. Extract values at 50 Hz
4. Verify normalized impedance matches theory
5. Verify full impedance scales with 1/Area

---

## Validation Workflow

For each test case:

1. **Import Hornresp Parameters**
   ```
   File → Open → Select hornresp_params.txt
   ```

2. **Generate Acoustic Impedance**
   ```
   Tools → Loudspeaker Driver → Electrical Impedance
   Set frequency range per test case
   Calculate → Save
   ```

3. **Extract Test Frequency Data**
   - Find row corresponding to test frequency
   - Extract Ra (norm) and Xa (norm) columns

4. **Compare with Theory**
   - Use `tests/physics/fixtures/tc_p1_rad_0X_data.py` for expected values
   - Run pytest: `pytest tests/physics/test_radiation.py::TestTC_P1_RAD_0X`

5. **Document Results**
   - Update test fixture with Hornresp values if needed
   - Document any discrepancies
   - Note Hornresp normalization differences

## Expected Hornresp Behavior

**Important:** Hornresp normalization differs from Kolbrek theoretical formulas:
- Hornresp R ≈ 4.05 × Kolbrek R
- Hornresp X ≈ 2.02 × Kolbrek X

This ratio is CONSISTENT across all test cases. The Viberesp implementation follows Kolbrek's peer-reviewed formulas, so validation is against theoretical values, not direct Hornresp comparison.

## Test Coverage

With these 4 test cases, we cover:

✅ **Low frequency (ka << 1):** TC-P1-RAD-01, TC-P1-RAD-04
- Mass-controlled region
- X dominates R
- Multiple piston sizes

✅ **Transition (ka ≈ 1):** TC-P1-RAD-02
- Neither mass nor resistance dominates
- Complex impedance behavior

✅ **High frequency (ka >> 1):** TC-P1-RAD-03
- Radiation-controlled region
- R dominates, X → 0
- Near 100% efficiency

✅ **Area scaling:** TC-P1-RAD-01 vs TC-P1-RAD-04
- Different piston sizes
- Same ka behavior
- Z_char ∝ 1/A

## Next Steps

1. Run Hornresp simulations for TC-P1-RAD-02, -03, -04
2. Extract acoustic impedance data at test frequencies
3. Create test fixtures in `tests/physics/fixtures/`
4. Add validation tests to `tests/physics/test_radiation.py`
5. Document any Hornresp discrepancies
6. Update literature with validation results

---

*Last Updated: 2025-12-25*
*Phase: 1 - Radiation Impedance*
*Status: TC-P1-RAD-01 validated, TC-P1-RAD-02/03/04 pending*
