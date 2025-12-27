# Sealed Box Exports

This directory contains Hornresp input files for sealed (closed-box) enclosure simulations.

## Directory Structure

```
sealed_boxes/
└── BC_8NDL51/                    # B&C 8NDL51-8 8" Midrange driver
    ├── BC_8NDL51_qtc0.707.txt    # Butterworth alignment (maximally flat)
    ├── BC_8NDL51_qtc1.000.txt    # Slightly underdamped (Qtc=1.0)
    └── (README.md - this file)
```

## BC_8NDL51 Sealed Box Configurations

**Driver Parameters:**
- Fs: 75.0 Hz
- Qts: 0.616
- Vas: 10.1 L
- Sd: 220 cm²

### Alignment Variants

| File | Qtc | Vb (L) | Fc (Hz) | F3 (Hz) | Description |
|------|-----|--------|---------|---------|-------------|
| `BC_8NDL51_qtc0.707.txt` | 0.707 | 31.65 | 86.1 | 86.1 | Butterworth (maximally flat) |
| `BC_8NDL51_qtc1.000.txt` | 1.000 | 10.00 | 119.0 | 119.0 | Slightly underdamped |

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

See `tests/validation_data/sealed_boxes/BC_8NDL51/` for complete validation
data including metadata, expected parameters, and detailed instructions.

## Literature

- Small (1972) - "Closed-Box Loudspeaker Systems Part I: Analysis"
- `literature/thiele_small/small_1972_closed_box.md`
