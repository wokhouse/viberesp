# Ported Box Electrical Impedance Model - Partial Fix

**Priority:** High
**Type:** Bug (Partially Fixed)
**Component:** `src/viberesp/enclosure/ported_box.py`
**Function:** `ported_box_electrical_impedance()`
**Date:** 2025-12-27
**Status:** IMPROVED but not fully resolved

## Summary

The ported box electrical impedance calculation produces significantly different results compared to Hornresp, particularly in the frequency range around the port tuning (Fb) and driver resonance (Fs). The impedance peaks characteristic of a vented box enclosure are misaligned, and SPL shows large errors at low frequencies.

## Validation Results

### Test Case
- **Driver:** 15PS100 (B&C 15" Subwoofer)
- **Enclosure:** Vb = 105.5 L, Fb = 37.3 Hz
- **Port:** 13.4 cm diameter × 22.8 cm length
- **Validation Data:** `imports/ported_sim.txt` (Hornresp simulation)
- **Parameter File:** `15PS100_ported_d3_hornresp.txt`

### Errors Observed

#### Electrical Impedance (Ze)
| Frequency | Hornresp | viberesp | Error |
|-----------|----------|----------|-------|
| 20 Hz     | 24.8 Ω   | 6.5 Ω    | **+18.4 Ω** (Hornresp 4x higher) |
| 34 Hz     | 5.3 Ω    | 10.5 Ω   | **+5.3 Ω** (2x difference) |
| 37 Hz (Fs)| 5.5 Ω    | 12.0 Ω   | **+6.5 Ω** (2x difference) |
| 50 Hz     | 14.1 Ω   | 41.6 Ω   | **+27.5 Ω** (3x higher) |
| 100 Hz    | 7.9 Ω    | 7.7 Ω    | ✓ 0.3 Ω (excellent) |
| 500+ Hz   | ~7.5 Ω   | ~7.5 Ω   | ✓ <0.1 Ω (perfect) |

**Overall:** Max error 64.2 Ω, Mean 3.3 Ω, RMS 9.6 Ω

#### SPL Response
| Frequency | Hornresp | viberesp | Error |
|-----------|----------|----------|-------|
| 20 Hz     | 75.6 dB  | 75.2 dB  | ✓ 0.4 dB |
| 34 Hz (Fb)| 93.1 dB  | 80.4 dB  | **+12.7 dB** |
| 37 Hz (Fs)| 93.8 dB  | 80.8 dB  | **+13.0 dB** |
| 50 Hz     | 94.7 dB  | 85.8 dB  | **+8.9 dB** |
| 100 Hz    | 96.2 dB  | 92.4 dB  | ~4 dB (acceptable) |
| 1000 Hz   | 81.7 dB  | 79.1 dB  | ~3 dB (good) |

**Overall:** Max error 14.5 dB, Mean 3.7 dB, RMS 5.1 dB

## Problem Analysis

### What's Working ✓
- High-frequency response (>100 Hz) matches well
- Direct radiator behavior (above box tuning) is correct
- Basic system parameters (F3, α, h) calculate correctly
- Helmholtz resonance formula is accurate

### What's Broken ✗
The **dual-peak impedance characteristic** of ported boxes is incorrect:

**Expected behavior (Hornresp):**
```
Impedance Peak 1 (~20 Hz) → Dip at Fb (~37 Hz) → Peak 2 (~60 Hz)
    24.8 Ω                        5.5 Ω              14 Ω
```

**Actual viberesp behavior:**
```
Peak 1 misaligned, Dip too shallow, Peak 2 at wrong frequency
    6.5 Ω                    10.5 Ω               41.6 Ω
```

### Root Cause (Identified and Partially Fixed)

The issue was in `src/viberesp/enclosure/ported_box.py:417` `ported_box_electrical_impedance()`.

**Original Problem:** The implementation modeled the ported box as a sealed box with modified stiffness, completely missing the port's contribution.

**Fix Implemented (2025-12-27):**
1. **Added port air mass impedance** - `Z_a_port_mass = jω × (ρ₀ × Lp_eff / S_p)`
2. **Added port radiation impedance** - Using `radiation_impedance_piston()` with port area
3. **Implemented parallel impedance combination** - Driver and port impedances combined in acoustic domain per Thiele (1971)
4. **Added box compliance to port branch** - C_mb coupled to both driver and port

**Remaining Issues:**
- Impedance magnitude at second peak is too low (~46 Ω vs ~65 Ω expected)
- Very high error at low frequencies (<20 Hz)
- Phase response still inaccurate
- Equivalent circuit model may need refinement

### Specific Issues to Investigate

1. **Thiele-Small equivalent circuit** for ported box:
   - Check if mechanical impedance calculation includes port mass loading
   - Verify box compliance calculation: `C_mb = C_ms / (1 + α)`
   - Port acoustic impedance should be in parallel with driver radiation impedance

2. **Port impedance formula**:
   ```
   Z_port = jω·ρ₀·S_port² / (Ap·Lpt_eff)  (should be inductive near Fb)
   ```
   where `Lpt_eff` includes end corrections

3. **Impedance transformation**:
   ```
   Ze = Re + jωLe + (BL)² / (Z_mechanical_driver || Z_mechanical_port)
   ```
   The parallel combination may be incorrect

4. **Literature to review**:
   - Thiele (1971) - "Loudspeakers in Vented Boxes, Part 1 & 2"
     - Figure 3: Equivalent circuit for vented box
     - Equation 9: Input impedance formula
   - Small (1972) - Closed-box (similar theory, different port model)
   - Beranek (1954) - Port impedance and end corrections

## Validation Commands

```bash
# Re-run validation
PYTHONPATH=src python3 scripts/validate_ported_box.py imports/ported_sim.txt

# Quick test of specific frequency
PYTHONPATH=src python3 << 'EOF'
from viberesp.driver.bc_drivers import get_bc_15ps100
from viberesp.enclosure.ported_box import ported_box_electrical_impedance

driver = get_bc_15ps100()
result = ported_box_electrical_impedance(
    37.3, driver,
    Vb=0.10554,
    Fb=37.3,
    port_area=0.014017,
    port_length=0.2278,
    voltage=2.83
)
print(f"Ze at Fb (37.3 Hz): {result['Ze_magnitude']:.2f} Ω")
print(f"Expected (Hornresp): ~5.5 Ω")
print(f"Error: {result['Ze_magnitude'] - 5.5:.2f} Ω")
EOF
```

## Expected Fix

After correction, viberesp should match Hornresp to within:
- **Electrical Impedance:** <5% error across all frequencies
- **SPL:** <3 dB error across all frequencies

The dual-peak impedance shape should match Hornresp exactly, with:
- First peak at ~0.5-0.6 × Fb
- Minimum impedance at Fb (port tuning)
- Second peak at ~1.5-2.0 × Fb

## Related Files

- Implementation: `src/viberesp/enclosure/ported_box.py:417`
- Validation script: `scripts/validate_ported_box.py`
- Reference data: `imports/ported_sim.txt`
- Driver: `src/viberesp/driver/bc_drivers.py:get_bc_15ps100()`
- Literature: `literature/thiele_small/thiele_1971_vented_boxes.md`

## Acceptance Criteria

1. Fix `ported_box_electrical_impedance()` to match Hornresp impedance curve
2. Validate against `imports/ported_sim.txt` with:
   - Max Ze error < 10% of value
   - SPL error < 3 dB at all frequencies
3. Add unit tests for impedance peak locations and magnitudes
4. Update docstring with Thiele (1971) equation references
5. Document the equivalent circuit model used

## Notes

- The system parameter calculations (`calculate_ported_box_system_parameters`) work correctly
- The issue is specifically in the **complete electro-mechano-acoustical simulation**
- Sealed box validation should be checked for comparison (may work better)
- This is a critical fix for Phase 1 validation goals

## Commands for Another Agent

```bash
# 1. Quick validation check
cd /Users/fungj/vscode/viberesp
PYTHONPATH=src python3 << 'EOF'
from viberesp.driver.bc_drivers import get_bc_15ps100
from viberesp.enclosure.ported_box import ported_box_electrical_impedance

driver = get_bc_15ps100()

# Test at Fb (should be impedance minimum)
result = ported_box_electrical_impedance(
    37.3, driver, Vb=0.10554, Fb=37.3,
    port_area=0.014017, port_length=0.2278, voltage=2.83
)
print(f"Ze at Fb: {result['Ze_magnitude']:.2f} Ω (expected ~5.5 Ω)")

# Test at first impedance peak (~20 Hz)
result = ported_box_electrical_impedance(
    20.0, driver, Vb=0.10554, Fb=37.3,
    port_area=0.014017, port_length=0.2278, voltage=2.83
)
print(f"Ze at 20 Hz: {result['Ze_magnitude']:.2f} Ω (expected ~25 Ω)")

# Test at second impedance peak (~60 Hz)
result = ported_box_electrical_impedance(
    60.0, driver, Vb=0.10554, Fb=37.3,
    port_area=0.014017, port_length=0.2278, voltage=2.83
)
print(f"Ze at 60 Hz: {result['Ze_magnitude']:.2f} Ω (expected ~15-20 Ω)")
EOF

# 2. Run full validation
PYTHONPATH=src python3 scripts/validate_ported_box.py imports/ported_sim.txt

# 3. Check literature
cat literature/thiele_small/thiele_1971_vented_boxes.md | grep -A 10 "impedance"
```
