# Hornresp File Format Analysis

## ✅ COMPARISON COMPLETE - FILES FIXED

### Files Compared:
- `hornresp_example.txt` - Reference example (exponential horn)
- `exports/BC_12NDL76.txt` - Our exported file (direct radiator)

---

## Issues Found and Fixed

### ✅ Issue 1: Line Endings (CRITICAL)

**Problem:**
- `hornresp_example.txt`: **CRLF** (Windows `\r\n`)
- Original export: **LF** (Unix `\n`)

**Fix Applied:**
- Updated `export_to_hornresp()` to use `newline='\r\n'` when writing files
- All exported files now have CRLF line terminators

**Verification:**
```bash
$ file exports/*.txt
exports/BC_12NDL76.txt:  ASCII text, with CRLF line terminators  ✓
exports/BC_15DS115.txt:  ASCII text, with CRLF line terminators  ✓
exports/BC_18PZW100.txt: ASCII text, with CRLF line terminators  ✓
exports/BC_8NDL51.txt:   ASCII text, with CRLF line terminators  ✓
```

### ✅ Issue 2: Cms Scientific Notation Format

**Problem:**
- Example: `1.00E-06` (2 decimal places: `.2E`)
- Original: `1.900E-04` (3 decimal places: `.3E`)

**Fix Applied:**
- Changed format from `{self.Cms:.3E}` to `{self.Cms:.2E}`
- Now outputs: `1.90E-04` ✓

**Verification:**
```bash
$ grep "Cms =" exports/*.txt
exports/BC_12NDL76.txt:  Cms = 1.90E-04  ✓
exports/BC_15DS115.txt:  Cms = 2.50E-04  ✓
exports/BC_18PZW100.txt: Cms = 1.70E-04  ✓
exports/BC_8NDL51.txt:   Cms = 2.40E-04  ✓
```

### ✅ Issue 3: Direct Radiator Configuration (CRITICAL for Stage 1B)

**Problem:**
- Initial exports used exponential horn parameters (S1=100, S2=5000, Exp=1.30)
- Attempted to use driver area for horn parameters (S1=S2=Sd)
- **Hornresp requirement:** "Unused horn segments must have all parameters set to zero"

**Fix Applied:**
- Set all horn parameters to 0 for direct radiator mode:
  ```
  S1 = 0.00, S2 = 0.00, Exp = 0.00, F12 = 0.00
  S2 = 0.00, S3 = 0.00, Exp = 0.00, F23 = 0.00
  S3 = 0.00, S4 = 0.00, L34 = 0.00, F34 = 0.00
  S4 = 0.00, S5 = 0.00, L45 = 0.00, F45 = 0.00
  ```

### ✅ Issue 4: Radiation Angle and Rear Chamber

**Problem:**
- Initial export used `Ang = 4.00` (4π steradians, full-space)
- Hornresp error: "Vrc cannot equal 0 for direct radiator having solid radiation angle of 4 x pi stradians"
- Full-space requires non-zero rear chamber volume

**Fix Applied:**
- Changed to `Ang = 2.00` (2π steradians, half-space / infinite baffle)
- Set `Vrc = 0.00` (no rear chamber required for half-space)
- This is the standard test condition for bare driver impedance validation

---

## Format Comparison

### Driver Parameter Format

| Parameter | Example Format | Our Format | Status |
|-----------|---------------|------------|--------|
| Sd        | `100.00`      | `522.00`   | ✓ Match |
| Bl        | `1.00`        | `16.50`    | ✓ Match |
| Cms       | `1.00E-06`    | `1.90E-04` | ✓ Fixed |
| Rms       | `0.00`        | `5.20`     | ✓ Match |
| Mmd       | `0.00` (2 dec)| `0.054` (3 dec) | ⚠️ 3 decimals for precision |
| Le        | `0.00` (2 dec)| `0.001` (3 dec) | ⚠️ 3 decimals for precision |
| Re        | `0.01`        | `3.10`     | ✓ Match |
| Nd        | `1`           | `1`        | ✓ Match |

**Note:** Mmd and Le use 3 decimal places for precision on real driver values.
The example shows `0.00` but that's a placeholder zero value. Real measurements
require more precision (e.g., 0.054 kg = 54g, 0.001 H = 1mH).

### Horn Configuration (Direct Radiator)

| Parameter | Example (Horn) | Our Format (Direct Radiator) | Purpose |
|-----------|---------------|------------------------------|---------|
| Ang       | `4.00`        | `2.00`                       | Half-space (2π steradians) |
| S1        | `100.00`      | `0.00`                       | No horn throat |
| S2        | `5000.00`     | `0.00`                       | No horn mouth |
| Exp       | `1.30`        | `0.00`                       | No flare |
| F12       | `150.00`      | `0.00`                       | No horn length |
| Vrc       | `0.001`       | `0.00`                       | No rear chamber |
| Lrc       | `15.00`       | `0.00`                       | No rear chamber length |
| Fr        | `40000.00`    | `0.00`                       | No filling |
| Tal       | `4.00`        | `0.00`                       | No attenuation |

**Default Configuration:** Half-space (2π steradians) infinite baffle mounting,
which is the standard test condition for loudspeaker driver validation.

---

## File Structure

All sections match the Hornresp format:
- ✓ ID and Comment
- ✓ RADIATION, SOURCE AND MOUTH PARAMETER VALUES (Ang=2.00)
- ✓ HORN PARAMETER VALUES (all zeros for direct radiator)
- ✓ TRADITIONAL DRIVER PARAMETER VALUES (real driver T/S parameters)
- ✓ ADVANCED DRIVER PARAMETER VALUES (both models, not used)
- ✓ PASSIVE RADIATOR PARAMETER VALUE (not used)
- ✓ CHAMBER PARAMETER VALUES (all zeros for bare driver)
- ✓ MAXIMUM SPL PARAMETER VALUES
- ✓ ABSORBENT FILLING MATERIAL PARAMETER VALUES
- ✓ ACTIVE BAND PASS FILTER PARAMETER VALUES
- ✓ PASSIVE FILTER PARAMETER VALUES
- ✓ EQUALISER FILTER PARAMETER VALUES
- ✓ STATUS FLAGS
- ✓ OTHER SETTINGS

---

## Exported Drivers

All 4 B&C drivers exported with direct radiator configuration:

| Driver | Sd (cm²) | Fs (Hz) | Purpose |
|--------|----------|---------|---------|
| BC_8NDL51   | 215.00  | ~65  | 8" Midrange |
| BC_12NDL76  | 522.00  | ~50  | 12" Mid-Woofer |
| BC_15DS115  | 860.00  | ~33  | 15" Subwoofer |
| BC_18PZW100 | 1250.00 | ~31  | 18" Subwoofer |

All configured for:
- Half-space radiation (Ang = 2.00)
- Direct radiator (no horn loading)
- Bare driver electrical impedance validation

---

## Validation Data Structure

Validation data is organized in `tests/validation/drivers/` with the following structure:

```
tests/validation/drivers/
├── bc_8ndl51/
│   └── infinite_baffle/
│       ├── bc_8ndl51_inf.txt       # Hornresp input file
│       ├── bc_8ndl51_inf_sim.txt   # Hornresp simulation results
│       └── metadata.json           # Validation metadata
├── bc_12ndl76/
│   └── infinite_baffle/
│       └── ...
└── ...
```

### Naming Convention

**Input files:** `{driver}_{config}.txt` (max 16 chars for Hornresp)
- `bc_8ndl51_inf.txt` - infinite baffle
- `bc_12ndl76_inf.txt` - infinite baffle
- Future: `bc_8ndl51_exp.txt` - exponential horn
- Future: `bc_8ndl51_hyp.txt` - hyperbolic horn

**Output files:** `{driver}_{config}_sim.txt`
- `bc_8ndl51_inf_sim.txt` - simulation results
- `bc_12ndl76_inf_sim.txt` - simulation results

**Metadata:** `metadata.json` in each config directory
```json
{
  "driver": "BC_8NDL51",
  "configuration": "infinite_baffle",
  "date_created": "2025-12-26",
  "date_run": null,
  "hornresp_version": null,
  "notes": "8 inch midrange driver - bare driver electrical impedance validation"
}
```

### Workflow

1. **Export driver:** `viberesp export BC_12NDL76 -o exports/bc_12ndl76_inf.txt`
2. **Copy to Hornresp VM:** Paste file, run simulation
3. **Import results:** Export Hornresp output as `imports/bc_12ndl76_inf_sim.txt`
4. **Move to validation:**
   ```bash
   cp exports/bc_12ndl76_inf.txt tests/validation/drivers/bc_12ndl76/infinite_baffle/
   cp imports/bc_12ndl76_inf_sim.txt tests/validation/drivers/bc_12ndl76/infinite_baffle/
   ```
5. **Update metadata:** Add `date_run` and `hornresp_version` to metadata.json

**Directory Convention:**
- `exports/` - Viberesp parameter outputs (Hornresp input files, gitignored)
- `imports/` - Hornresp simulation results (validation data, gitignored)
- `tests/validation/drivers/` - Permanent validation data (version controlled)

---

## Test with Hornresp

The exported files should now be importable into Hornresp. Try importing:

1. `exports/BC_8NDL51.txt` - 8" Midrange driver
2. `exports/BC_12NDL76.txt` - 12" Mid-Woofer driver
3. `exports/BC_15DS115.txt` - 15" Subwoofer driver
4. `exports/BC_18PZW100.txt` - 18" Subwoofer driver

---

## Troubleshooting

### Error: "Unused horn segments must have all parameters set to zero"

**Cause:** Setting S1, S2, or other horn parameters to non-zero values when Exp = 0, or attempting to use driver area (Sd) for horn throat/mouth in direct radiator mode.

**Symptoms:**
- Trying to configure S1 = Sd for direct radiator
- Setting S2 to non-zero with Exp = 0

**Solution:**
For bare driver (direct radiator) testing, set ALL horn parameters to 0:
```
S1 = 0.00
S2 = 0.00
Exp = 0.00
F12 = 0.00
S3 = 0.00
S4 = 0.00
L34 = 0.00
F34 = 0.00
L45 = 0.00
F45 = 0.00
```

---

### Error: "Vrc cannot equal 0 for direct radiator having solid radiation angle of 4 x pi stradians"

**Cause:** Using `Ang = 4.00` (4π steradians, full-space radiation) with `Vrc = 0.00` (no rear chamber). Hornresp requires a non-zero rear chamber volume for full-space radiation.

**Symptoms:**
- Configuration has `Ang = 4.00` and `Vrc = 0.00`

**Solution:**
Use half-space radiation (2π steradians) for bare driver testing:
```
Ang = 2.00    # Half-space (infinite baffle)
Vrc = 0.00    # No rear chamber required
```

This is the standard test condition for loudspeaker driver validation, representing a driver mounted in an infinite baffle.

---

### File Format Issues

**Problem:** Files not accepted by Hornresp (no error message, just won't import)

**Check 1: Line Endings**
```bash
file your_file.txt
# Should show: "ASCII text, with CRLF line terminators"
# If shows "ASCII text" (Unix LF), need CRLF
```

**Check 2: Cms Format**
```bash
grep "Cms =" your_file.txt
# Should show: "Cms = X.XXE-XX" (2 decimal places)
# Wrong: "Cms = X.XXXE-XX" (3 decimal places)
```

**Check 3: All Horn Parameters Zero**
```bash
grep -E "^S[12345] = |^Exp = |^F[1234][245] = " your_file.txt
# All should be 0.00 for direct radiator
```

---

## Import Checklist

Before importing into Hornresp, verify:

- [ ] File has CRLF line terminators (`file` command)
- [ ] Cms uses 2 decimal places in scientific notation
- [ ] All horn parameters are 0.00 (for direct radiator)
- [ ] Ang = 2.00 (half-space) or Ang = 4.00 with Vrc > 0 (full-space)
- [ ] Driver T/S parameters are within reasonable ranges
- [ ] File name ≤ 16 characters (Hornresp limit)

---

## Common Configuration Patterns

### Bare Driver (Infinite Baffle)
```
Ang = 2.00          # Half-space
S1-S5 = 0.00        # No horn
Vrc = 0.00          # No rear chamber
```

### Horn-Loaded System
```
Ang = 2.00 or 4.00  # Radiation pattern
S1 = throat_area    # Non-zero
S2 = mouth_area     # Non-zero
Exp = flare_constant # Non-zero for exponential
F12 = horn_length   # Non-zero
```

---

## Implementation Details

**Location:** `src/viberesp/hornresp/export.py`

**Key Functions:**
- `export_to_hornresp()` - Export single driver to Hornresp .txt file
- `batch_export_to_hornresp()` - Export multiple drivers
- `HornrespRecord.to_hornresp_format()` - Format driver parameters

**Default Configuration (for Stage 1B bare driver testing):**
```
Ang = 2.00          # Half-space (2π steradians)
S1-S5 = 0.00        # No horn segments
Exp = 0.00          # No flare
F12, F23, F34, F45 = 0.00  # No horn lengths
Vrc = 0.00          # No rear chamber
```

This configuration represents a driver mounted in an infinite baffle,
radiating into half-space, with no horn loading - ideal for validating
the bare driver electrical impedance model against Hornresp.
