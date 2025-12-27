# Sealed Box Validation Summary

## Test Results (2025-12-27)

### ✅ System Parameter Tests: ALL PASSING (9/9)

All 9 new test cases validate correctly against Small (1972) formulas for Fc and Qtc calculations.

#### BC_8NDL51 (8" driver) - 5 test cases
| Qtc  | Vb (L) | Fc (Hz) | Status | Sim File       |
|------|--------|---------|--------|----------------|
| 0.65 | 87.83  | 79.2    | ✅ PASS| sim_qtc0_65.txt |
| 0.71 | 31.65  | 86.1    | ✅ PASS| sim_qtc0_707.txt |
| 0.80 | 14.66  | 97.5    | ✅ PASS| sim_qtc0_8.txt |
| 1.00 | 6.16   | 121.8   | ✅ PASS| sim_qtc1.txt |
| 1.10 | 4.60   | 134.0   | ✅ PASS| sim_qtc1_1.txt |
| 20L  | 0.755  | 92.0    | ✅ PASS| sim_vbl20.txt |

#### BC_15PS100 (15" driver) - 4 test cases
| Qtc  | Vb (L) | Fc (Hz) | Status | Sim File        |
|------|--------|---------|--------|-----------------|
| 0.50 | 373.30 | 42.2    | ✅ PASS| sim_qtc0_5.txt |
| 0.71 | 67.45  | 59.7    | ✅ PASS| sim_qtc0_707.txt |
| 0.94 | 30.0   | 79.3    | ✅ PASS| sim_qtc0_97.txt |
| 50L  | 0.773  | 65.9    | ✅ PASS| sim_vbl50.txt |
| 80L  | 0.672  | 56.8    | ✅ PASS| sim_vbl80.txt |

### ✅ Electrical Impedance Validation: BUTTERWORTH PASSING

#### BC_8NDL51 Qtc=0.707
- **Status**: ✅ PASSING (max error <8%)
- **Test class**: `TestSealedBoxElectricalImpedanceBC8NDL51`
- **Sim file**: `sim_qtc0_707.txt`

#### BC_15PS100 Qtc=0.707
- **Status**: ✅ PASSING (max error <7%)
- **Test class**: `TestSealedBoxElectricalImpedanceBC15PS100`
- **Sim file**: `sim_qtc0_707.txt`

### ⏸️ Additional Impedance Validation: PENDING

The other 7 Hornresp sim files have been generated but impedance validation tests
are not yet implemented for those alignments. To add impedance validation for
additional alignments, we would need to:

1. Create new test classes (similar to `TestSealedBoxElectricalImpedanceBC8NDL51`)
2. Parameterize tests to load specific sim files and use correct Vb values
3. Run validation against each Hornresp sim file

### ⚠️ Known Limitation: SPL Validation

SPL validation shows ~19-24 dB error due to Hornresp internal inconsistency
(41% difference between electrical and mechanical domains in Hornresp's exported data).

This is documented in:
- `docs/validation/sealed_box_spl_research_summary.md`
- `tests/validation/drivers/bc_15ps100/sealed_box/VALIDATION_ISSUE.md`

## Files Created

### Hornresp Input Files (9 files)
All generated using `export_to_hornresp()`:

**BC_8NDL51:**
- `input_qtc0.65.txt` - Qtc=0.65 (large box, near Butterworth)
- `input_qtc0.707.txt` - Qtc=0.707 Butterworth (validated ✅)
- `input_qtc0.8.txt` - Qtc=0.8 (slight overdamp)
- `input_qtc1.0.txt` - Qtc=1.0 (critically damped)
- `input_qtc1.1.txt` - Qtc=1.1 (overdamped)
- `input_vb20L.txt` - Non-optimal 20L volume

**BC_15PS100:**
- `input_qtc0.5.txt` - Qtc=0.5 (underdamped, very large box)
- `input_qtc0.707.txt` - Qtc=0.707 Butterworth (validated ✅)
- `input_qtc0.97.txt` - Qtc=0.94 (near critical, min practical volume)
- `input_vb50L.txt` - Non-optimal 50L volume
- `input_vb80L.txt` - Non-optimal 80L volume

### Helper Scripts (in `tasks/`)
- `calculate_sealed_box_volumes.py` - Calculate box volumes for target Qtc
- `generate_hornresp_inputs.py` - Generate all Hornresp input files
- `test_all_sealed_box_sims.py` - Run validation tests for all sim files

## Running Tests

### Test all system parameters (works immediately):
```bash
PYTHONPATH=src pytest tests/validation/test_sealed_box.py::TestSealedBoxQtcAlignmentsBC8NDL51 -v
PYTHONPATH=src pytest tests/validation/test_sealed_box.py::TestSealedBoxQtcAlignmentsBC15PS100 -v
```

### Test electrical impedance (requires correct sim.txt in place):
```bash
# Ensure sim.txt is the correct alignment
cp tests/validation/drivers/bc_8ndl51/sealed_box/sim_qtc0_707.txt \
   tests/validation/drivers/bc_8ndl51/sealed_box/sim.txt

PYTHONPATH=src pytest tests/validation/test_sealed_box.py::TestSealedBoxElectricalImpedanceBC8NDL51 -v
```

### Test all sim files automatically:
```bash
PYTHONPATH=src python tasks/test_all_sealed_box_sims.py
```

## Validation Coverage

- **System parameters**: 9/9 test cases implemented and passing ✅
- **Hornresp impedance**: 2/9 test cases validated (Qtc=0.707 for both drivers) ✅
- **Pending impedance validation**: 7/9 test cases require test infrastructure updates
- **SPL validation**: Known Hornresp limitation (not fixable without Hornresp source)

## Literature Citations

All tests properly cite Small (1972) sealed box theory:
- `literature/thiele_small/small_1972_closed_box.md`
- System parameters: Fc = Fs × √(1 + α), Qtc = Qts × √(1 + α)

## Next Steps

To complete full Hornresp validation for all alignments:

1. ✅ System parameter tests - DONE
2. ✅ Hornresp input files generated - DONE
3. ✅ Two impedance validations completed (Qtc=0.707) - DONE
4. ⏸️ Add impedance validation tests for remaining 7 alignments - PENDING
   - Requires parameterized tests that load specific sim files
   - Tests should verify <10% impedance error for all alignments
5. ⏸️ SPL validation - ON HOLD (Hornresp internal inconsistency)
