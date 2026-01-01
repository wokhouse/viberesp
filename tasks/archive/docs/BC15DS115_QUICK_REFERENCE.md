# BC_15DS115 Ported Box Design - Quick Reference

**Date:** 2025-12-27
**Study:** Improved simulation model with HF roll-off

---

## Top 3 Designs

### 🏆 Best Overall Flatness (20-200 Hz)
**Extra Large (300L, 27Hz)**
- Flatness: σ = **3.12 dB** ⭐
- F3: 10 Hz
- Port: 209.3 cm² × 21.6 cm
- Use: Home theater, maximum performance

### 🥇 Best Compromise (Size + Performance)
**Very Large (180L, 29Hz)**
- Flatness: σ = 3.42 dB
- F3: 10 Hz
- Port: 209.3 cm² × 20.3 cm
- Use: Music + movies, good balance

### 🎯 Best Compact (Space Constrained)
**Small (60L, 34Hz)**
- Flatness: σ = 4.18 dB
- F3: 10 Hz (theoretical)
- Port: 209.3 cm² × 19.2 cm
- Use: Desktop/bookshelf, space-limited

---

## Comparison with Old Model

| Model | Best Design | Vb | Fb | Flatness (σ) | Notes |
|-------|-------------|----|----|--------------|-------|
| **Old** | Very Small | 50 L | 35 Hz | 4.37 dB | No HF roll-off |
| **New** | Extra Large | 300 L | 27 Hz | **3.12 dB** | With HF roll-off ⭐ |

**Why the change?** HF roll-off (-7.77 dB @ 200 Hz) compensates bass boost in large boxes.

---

## Design Recommendations

```
Qts = 0.061 (VERY LOW)

This driver has an extremely strong motor (high BL).
Traditional alignments don't apply well.

Recommended approach: Go LARGE
- Larger boxes = flatter overall response
- Bass boost balances HF roll-off
- Don't use classic B4 (not optimal)
```

---

## Port Design

**All designs use same port area** (calculated for Xmax = 16.5mm):
- **Area:** 209.3 cm²
- **Equivalent to:**
  - 6.3" diameter round port
  - 3" × 7" slot port
  - 4" diameter (would need 2 ports)

**Port length varies with tuning:**
- 27 Hz: 21.6 cm
- 29 Hz: 20.3 cm
- 33 Hz: 15.9 cm (B4)
- 34 Hz: 19.2 cm

**Note:** All ports are flanged (end correction included in calculation).

---

## HF Roll-off Details

```
At 200 Hz:
- Mass roll-off: -0.5 dB (f_mass = 1046 Hz)
- Inductance roll-off: -7.3 dB (f_Le = 173 Hz)
- Total: -7.77 dB

This is SIGNIFICANT and must be included in simulations.
```

---

## Validation Files

Exported to Hornresp format for validation:
- `tasks/BC15DS115_300L_27Hz_optimal.txt` - Best overall
- `tasks/BC15DS115_180L_29Hz_compromise.txt` - Compromise
- `tasks/BC15DS115_254L_33Hz_B4.txt` - Classic B4 (for reference)

---

## Full Documentation

See `tasks/BC15DS115_IMPROVED_MODEL_COMPARISON.md` for complete analysis.

---

**Key Takeaway:** The improved simulation model with HF roll-off completely changes optimal designs for the BC_15DS115. Large boxes (150-300L) are now recommended instead of small boxes (50-80L).
