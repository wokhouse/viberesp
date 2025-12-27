# Sealed Box Validation Status

## Branch: `enable-sealed-box-validation`

## What Was Added

### 1. Data Organization
- **Directory:** `tests/validation/drivers/bc_8ndl51/sealed_box/`
- **Hornresp Sim Files:**
  - `sim_qtc0.707.txt` - Qtc=0.707 (Butterworth alignment, Vb=31.65L)
  - `sim_qtc1.000.txt` - Qtc=1.000 (Slightly underdamped, Vb=10.1L)
- **Metadata Files:**
  - `metadata_qtc0.707.json`
  - `metadata_qtc1.000.json`

### 2. Test File
- **File:** `tests/validation/test_sealed_box_enabled.py`
- **Test Classes:**
  - `TestSealedBoxSystemParameters` - Validates Fc, Qtc calculations
  - `TestSealedBoxElectricalImpedanceQtc0_707` - Full validation for Butterworth alignment
  - `TestSealedBoxElectricalImpedanceQtc1_000` - Full validation for Qtc=1.000
  - `TestSealedBoxCornerCases` - Diagnostic tests (impedance peak, Fc > Fs)

### 3. Test Coverage
The tests validate:
- System resonance frequency (Fc)
- System Q factor (Qtc)
- Electrical impedance magnitude
- Electrical impedance phase
- SPL response
- Comprehensive validation reports

## Current Test Status

```
✅ PASSING (4/11):
  - Fc calculation for Qtc=0.707
  - Impedance phase for Qtc=0.707
  - Impedance peak at Fc (corner case)
  - Fc > Fs verification (corner case)

❌ FAILING (7/11):
  - Fc calculation for Qtc=1.000 (off by 0.8 Hz)
  - All electrical impedance magnitude tests
  - All SPL tests
```

## Root Cause: Driver Parameter Mismatch

The Hornresp sealed box simulations were generated with different driver parameters:

**Hornresp Parameters (from BC_8NDL51_qtc0.707.txt):**
```
Bl  = 7.30 T·m
Mmd = 26.286 g
Cms = 1.50E-04 m/N
Rms = 2.44
Le  = 0.150 mH
Re  = 2.60 Ω
Sd  = 220 cm²
```

**Viberesp get_bc_8ndl51() Parameters:**
```
Fs  = 75.0 Hz (after radiation mass correction)
Qts = 0.62
Vas = 10.1 L
Re  = 2.6 Ω
M_md = 26.286 g (before correction)
BL  = 7.3 T·m
Sd  = 220 cm²
```

## Options to Enable Tests

### Option 1: Regenerate Hornresp Data (Recommended)
Use `viberesp.hornresp.export` to create new Hornresp input files with correct parameters:

```python
from viberesp.hornresp.export import export_to_hornresp
from viberesp.driver.bc_drivers import get_bc_8ndl51

driver = get_bc_8ndl51()

# Export Qtc=0.707 alignment
export_to_hornresp(
    driver=driver,
    driver_name="BC_8NDL51",
    output_path="tests/validation/drivers/bc_8ndl51/sealed_box/input_qtc0.707.txt",
    comment="Qtc=0.707 Butterworth alignment",
    enclosure_type="sealed_box",
    Vb_liters=31.65
)

# Export Qtc=1.000 alignment
export_to_hornresp(
    driver=driver,
    driver_name="BC_8NDL51",
    output_path="tests/validation/drivers/bc_8ndl51/sealed_box/input_qtc1.000.txt",
    comment="Qtc=1.000 alignment",
    enclosure_type="sealed_box",
    Vb_liters=10.1
)
```

Then in Hornresp:
1. Import the input files
2. Run simulation
3. Export _sim.txt results
4. Replace the current sim.txt files

### Option 2: Create Custom Driver Getter
Create a function that returns driver parameters matching the Hornresp configuration:

```python
# In src/viberesp/driver/bc_drivers.py
def get_bc_8ndl51_hornresp_sealed():
    """BC 8NDL51 parameters matching Hornresp sealed box simulation."""
    return ThieleSmallParameters(
        F_s=75.0,  # From datasheet
        Q_ts=0.62,
        V_as=0.0101,  # 10.1L
        R_e=2.6,
        L_e=0.150e-3,  # 0.150 mH
        M_md=26.286e-3,  # 26.286g
        BL=7.3,
        S_d=0.022,  # 220 cm²
        C_ms=1.50e-4,  # 1.50E-04 m/N
        R_ms=2.44,
    )
```

### Option 3: Adjust Test Tolerances
If the parameter differences are deemed acceptable, relax tolerances:
- Fc: 0.5 Hz → 1.0 Hz
- Impedance: 10% → 30%
- SPL: 6 dB → 10 dB

**Not recommended** - this masks the underlying parameter mismatch.

## Next Steps

1. **Choose an approach** (Options 1, 2, or 3 above)
2. **Implement the fix**
3. **Run tests:** `PYTHONPATH=src pytest tests/validation/test_sealed_box_enabled.py -v`
4. **Debug any remaining failures** (expect some SPL deviation at high frequencies)
5. **Once tests pass, replace the original test file:**
   ```bash
   mv tests/validation/test_sealed_box.py tests/validation/test_sealed_box.py.old
   mv tests/validation/test_sealed_box_enabled.py tests/validation/test_sealed_box.py
   ```

## Expected Validation Results (After Fix)

Based on infinite baffle results, sealed box should achieve:
- **Electrical impedance magnitude:** <5% above 200 Hz
- **Electrical impedance phase:** <10° above 200 Hz
- **SPL:** <6 dB max, <4.5 dB RMS
- **System parameters (Fc, Qtc):** <0.5 Hz, <0.02 tolerance

## Literature

- Small (1972) - Closed-Box Loudspeaker Systems Part 1: Analysis
- Literature file: `literature/thiele_small/small_1972_closed_box.md`

## Notes

- Corner case tests (impedance peak at Fc, Fc > Fs) are already passing
- These tests verify the fundamental physics is correct
- The failures are only in absolute magnitude comparisons due to parameter mismatch
