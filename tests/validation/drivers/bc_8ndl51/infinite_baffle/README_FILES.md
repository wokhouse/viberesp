# BC 8NDL51 Hornresp Validation Files

## ✅ Ready for Hornresp

### `8ndl51_corrected.txt` - USE THIS FILE
**Corrected Hornresp input file with all datasheet parameters**

**Key Parameters:**
- Sd = 220.00 cm²
- Bl = 12.40 T·m ✅ (matches datasheet)
- Cms = 2.09E-04 m/N
- Rms = 3.22 N·s/m
- **Mmd = 0.028 kg** (28 g) ✅
- **Le = 0.0005 H** (0.5 mH) ✅
- Re = 5.30 Ω

**Expected Results:**
- Resonance: **~66 Hz** (matches datasheet Fs = 66 Hz)
- Peak Ze: **~50 Ω** at resonance
- High-freq Ze: **>6 Ω** at 20 kHz (includes inductance)

---

## Files in Directory

| File | Purpose | Status |
|------|---------|--------|
| `8ndl51_corrected.txt` | ✅ **USE THIS** - Corrected datasheet parameters | Ready for Hornresp |
| `8ndl51_man.txt` | Old manual input (Le=0) | Outdated |
| `8ndl51_man_sim.txt` | Old simulation (Le=0, no inductance) | Outdated |

---

## Next Steps

### 1. Load into Hornresp
```
File > Open > 8ndl51_corrected.txt
```

### 2. Verify Parameters
```
Tools > Driver Parameters
```
Should show:
- Mmd = 0.028 (28g)
- Le = 0.0005 (0.5 mH)
- fs ≈ 66 Hz (calculated)

### 3. Run Simulation
```
Tools > Loudspeaker Simulator > Calculate
```

### 4. Save Results
```
File > Save As > 8ndl51_corrected_sim.txt
```

### 5. Update Validation Test
Once you generate the simulation, rename the file:
```bash
mv 8ndl51_corrected_sim.txt 8ndl51_man_sim.txt
```

Then run validation:
```bash
PYTHONPATH=src pytest tests/validation/test_infinite_baffle.py -v
```

---

## Parameter Comparison

### Old (Wrong) vs New (Correct)

| Parameter | `8ndl51_man.txt` | `8ndl51_corrected.txt` | Datasheet |
|-----------|-------------------|----------------------|-----------|
| Mmd | 26.77 | **28.0** | 28 g ✅ |
| Cms | 2.03E-04 | **2.09E-04** | calculated |
| Rms | 3.30 | **3.22** | calculated |
| Bl | 12.39 | **12.40** | 12.4 T·m ✅ |
| **Le** | **0.00** ❌ | **0.0005** ✅ | 0.5 mH |
| Re | 5.30 | 5.30 | 5.3 Ω ✅ |
| Sd | 220.00 | 220.00 | 220 cm² ✅ |

---

## What Was Fixed

1. ✅ **Bl value**: Corrected from 7.5 to 12.4 T·m (was wrong in bc_drivers.py)
2. ✅ **Mms value**: Corrected from 25g to 28g (datasheet value)
3. ✅ **Le value**: Added 0.5 mH inductance (was 0 in manual input)
4. ✅ **Cms, Rms**: Recalculated from datasheet Q factors
5. ✅ **File format**: CRLF line endings for Hornresp compatibility

---

## Expected Validation Results

With corrected parameters (Le=0.5mH):

| Frequency | Viberesp (Simple Model) | Hornresp (Expected) |
|-----------|-------------------------|---------------------|
| 20 Hz | ~7 Ω | ~7 Ω |
| 66 Hz (resonance) | **~50 Ω** | **~50 Ω** |
| 20 kHz | **~63 Ω** | **~63 Ω** |

**High-frequency validation** will show that the simple jωL model overestimates impedance. This is where the Leach (2002) model will be needed.

---

## About Other Drivers

You mentioned: "let's assume all other params are incorrect for the other drivers"

**Recommendation:**
1. Manually input all drivers in Hornresp using datasheet values
2. Export each to a `{driver}_corrected.txt` file
3. Generate new `{driver}_corrected_sim.txt` files
4. Update `bc_drivers.py` with correct parameters for each driver

**Drivers to update:**
- BC 12NDL76 (12" mid-woofer)
- BC 15DS115 (15" subwoofer)
- BC 18PZW100 (18" subwoofer)

---
**Created:** 2025-12-26
**Status:** Ready for Hornresp import
