# Ported Box Exports

This directory contains Hornresp input files for ported (vented/bass reflex) enclosure simulations.

## Directory Structure

```
ported_boxes/
└── BC_8NDL51/                    # B&C 8NDL51-8 8" Midrange driver
    ├── BC_8NDL51_vb31.6L_fb65Hz_2.5in.txt   # B4 alignment, 2.5" port
    ├── BC_8NDL51_vb31.6L_fb65Hz_3in.txt     # B4 alignment, 3" port
    └── summary.md                  # Summary of all cases
```

## BC_8NDL51 Ported Box Configurations

**Driver Parameters:**
- Fs: 75.0 Hz
- Qts: 0.616
- Vas: 10.1 L
- Sd: 220 cm²

**Alignment:** B4 Butterworth (maximally flat response)
- Target Qtc: 0.707
- Vb: 31.65 L
- Fb: 65.3 Hz
- F3: 65.3 Hz

### Port Variants

| File | Port Diameter | Port Area | Port Length | Tuning |
|------|--------------|-----------|-------------|--------|
| `BC_8NDL51_vb31.6L_fb65Hz_2.5in.txt` | 2.5" (6.35cm) | 31.67 cm² | 4.29 cm | 65.3 Hz |
| `BC_8NDL51_vb31.6L_fb65Hz_3in.txt` | 3.0" (7.62cm) | 45.60 cm² | 6.83 cm | 65.3 Hz |

Both configurations target the same B4 alignment with identical box volume
and tuning frequency, differing only in port dimensions.

## Usage

1. Import into Hornresp:
   ```
   File → Open → Select <filename>.txt
   ```

2. Run simulation:
   ```
   Tools → Loudspeaker Wizard → Calculate
   ```

3. Export results for validation:
   ```
   File → Save As → sim.txt
   ```

## Validation

See `tests/validation_data/ported_boxes/BC_8NDL51/` for complete validation
data including metadata, expected parameters, and detailed instructions.

## Literature

- Thiele (1971) - "Loudspeakers in Vented Boxes" Parts 1 & 2
- `literature/thiele_small/thiele_1971_vented_boxes.md`
