# BC_15DS115 Validation Designs - Quick Comparison

**3 designs for Hornresp validation spanning the design space**

---

## Design Comparison Table

| Parameter | Compact (60L) | B4 (254L) | Optimal (300L) |
|-----------|---------------|-----------|----------------|
| **Approach** | Old Model | Classic Literature | Improved Model ⭐ |
| Vb (L) | 60 | 254 | 300 |
| Fb (Hz) | 34 | 33 | 27 |
| α (ratio) | 4.23 | 1.00 | 0.85 |
| h (ratio) | 1.03 | 1.00 | 0.82 |
| Port (cm²) | 209.3 | 209.3 | 209.3 |
| Length (cm) | 19.2 | 15.9 | 21.6 |

---

## Performance Predictions

### Flatness (Standard Deviation)

| Frequency Range | Compact | B4 | Optimal | Winner |
|-----------------|---------|----|---------|--------|
| Deep Bass (20-40 Hz) | 5.9 dB | 7.3 dB | **5.4 dB** | Optimal ⭐ |
| Bass (20-80 Hz) | 4.9 dB | 5.4 dB | **3.9 dB** | Optimal ⭐ |
| Midbass (40-120 Hz) | **0.5 dB** | 0.7 dB | **0.5 dB** | Compact/Optimal |
| Overall (20-200 Hz) | 4.2 dB | 4.3 dB | **3.1 dB** | Optimal ⭐ |

### SPL Response (2.83V, 1m)

| Frequency | Compact | B4 | Optimal |
|-----------|---------|----|---------|
| 20 Hz | 73 dB | 82 dB | **83 dB** ⭐ |
| 30 Hz | 89 dB | 99 dB | **101 dB** |
| 40 Hz | 90 dB | 95 dB | **96 dB** |
| 80 Hz | 90 dB | 94 dB | **95 dB** |
| 200 Hz | 93 dB | 97 dB | **98 dB** |
| 500 Hz | 94 dB | 98 dB | **98 dB** |

**Key:**
- Optimal has +10 dB deep bass vs Compact
- All show HF roll-off at 200 Hz (-7.77 dB)
- Midbass similar across all designs

---

## Expected Hornresp Results

### Impedance Curve

**Dual peaks should be visible:**

| Design | Fb | Lower Peak | Dip (≈Re) | Upper Peak |
|--------|----|------------|-----------|------------|
| Compact (60L) | 34 Hz | ~24 Hz | 34 Hz @ 5Ω | ~48 Hz |
| B4 (254L) | 33 Hz | ~23 Hz | 33 Hz @ 5Ω | ~46 Hz |
| Optimal (300L) | 27 Hz | ~19 Hz | 27 Hz @ 5Ω | ~38 Hz |

**Validation points:**
- ✓ Dip at Fb ≈ 5Ω (close to Re = 4.9Ω)
- ✓ Two distinct peaks
- ✓ Peak spacing: Fb/√2 and Fb×√2

### Frequency Response Shape

**Compact (60L, 34Hz):**
```
SPL (dB)
100 |                    ______
 95 |              _____/
 90 |         _____/
 85 |    ____/
    |___/
 80 |
    +-----------------------------> Freq (Hz)
    20   40   60   80  100  200  500
```
- Lower deep bass (stiff box)
- Flattest midbass
- Earlier roll-off

**B4 (254L, 33Hz):**
```
SPL (dB)
100 |              ____
 95 |          __/    \__________
 90 |    ____/
    |___/
 85 |
    +-----------------------------> Freq (Hz)
    20   40   60   80  100  200  500
```
- Bass boost at 30-40 Hz
- Higher deep bass
- More variation

**Optimal (300L, 27Hz):**
```
SPL (dB)
102 |          ____
 98 |      __/      \__________
 94 |   __/
    |__/
 90 |
    +-----------------------------> Freq (Hz)
    20   40   60   80  100  200  500
```
- Highest deep bass
- Flattest overall
- Bass boost balances HF roll-off

---

## Validation Checklist

### Import Verification

For each file, verify in Hornresp:

- [ ] **Vrc** (box volume) matches Vb in liters
- [ ] **Ap** (port area) = 209.3 cm²
- [ ] **Lpt** (port length) matches design
- [ ] **Mmd** = 64.86 g (driver mass only!)
- [ ] **Cms** = 2.50E-04 (scientific notation)

### Simulation Results

**For each design, check:**

- [ ] Deep bass output: Optimal > B4 > Compact
- [ ] Midbass flatness: All similar (σ ≈ 0.5-0.7 dB)
- [ ] HF roll-off: -7 to -8 dB at 200 Hz
- [ ] Impedance dip: ≈ 5Ω at tuning frequency
- [ ] Dual peaks: Visible and correctly spaced

### Overall Success

**Validation successful if:**

1. [ ] **Rankings correct** (Optimal flattest overall)
2. [ ] **HF roll-off visible** (validates improved model)
3. [ ] **Deep bass differs by ~10 dB** (Compact vs Optimal)
4. [ ] **Midbass similar** (all σ < 1 dB)
5. [ ] **Impedance curves** show dual peaks

---

## File Locations

```
tasks/validation/
├── BC15DS115_compact_60L_34Hz.txt      ← Old model approach
├── BC15DS115_B4_254L_33Hz.txt          ← Classic B4
├── BC15DS115_optimal_300L_27Hz.txt     ← Improved model ⭐
├── VALIDATION_GUIDE.md                 ← Detailed guide
└── DESIGN_COMPARISON.md                ← This file
```

---

## Import Instructions

**In Hornresp:**
1. File → Import
2. Select .txt file
3. Click "Load"
4. Verify parameters in chamber section
5. Tools → Response Wizard
6. Set: 20-500 Hz, 2.83V, 1m
7. Calculate and export

---

## Expected Time

**Setup:** 5 minutes per file (3 files = 15 min)
**Simulation:** 1 minute per file
**Analysis:** 15-30 minutes
**Total:** ~45 minutes

---

## Key Validation Insight

> **The improved model changes the optimal design from 60L → 300L**
>
> This is NOT a mistake - it's the physics of HF roll-off!
>
> Large box bass boost compensates for voice coil inductance effects,
> creating a flatter overall response. Hornresp validation will confirm this.

---

**Purpose:** Quick reference for validation
**Status:** Ready for Hornresp import
**Date:** 2025-12-27
