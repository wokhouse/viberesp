# JBL Mass Break Frequency Formula

**Formula**: f_mass = (BL² / Re) / (π × Mms)

## Description

The JBL mass break frequency formula is used to calculate the frequency above which the driver response rolls off at 6 dB/octave due to the motor's inability to accelerate the moving mass. This formula is **specifically designed for compression drivers in horn-loaded systems**.

## Applicability

**✅ USE FOR:**
- Horn-loaded compression drivers
- High-frequency compression drivers with phase plugs
- Professional PA compression drivers

**❌ DO NOT USE FOR:**
- Direct radiators (sealed boxes, ported boxes)
- Woofers and subwoofers
- Midrange drivers in direct radiator applications

**Why?** The JBL formula assumes a specific motor structure and loading condition found in compression drivers. For direct radiators, the optimal mass break frequency must be determined empirically from Hornresp validation, not calculated from this formula.

## Formula Derivation

The mass break frequency represents the point where:
- The motor force capability (BL²/Re) equals the inertial load (π × Mms)
- Above this frequency, the motor cannot efficiently accelerate the diaphragm
- Response rolls off at 6 dB/octave (first-order low-pass)

## Validation Findings

### BC_8NDL51 (Direct Radiator - NOT applicable)
- JBL formula: f_mass = 217.8 Hz
- **Actual optimal**: f_mass = 450 Hz (determined from Hornresp validation)
- Error: Using JBL formula gives 2× error in HF roll-off point

### BC_15PS100 (Direct Radiator - NOT applicable)
- JBL formula: f_mass = 157.1 Hz
- **Actual optimal**: f_mass = 300 Hz (determined from Hornresp validation)
- Error: Using JBL formula gives ~2× error in HF roll-off point

### Pattern Observed
For direct radiators, the optimal f_mass correlates with system resonance:
- f_mass ≈ 4.5×Fc to 5.7×Fc (varies by driver)
- This is **NOT** predicted by the JBL formula

## Literature Sources

- Small (1973), "Vented-Box Loudspeaker Systems Part I", JAES
- JBL Professional - Tech Note: Characteristics of High-Frequency Compression Drivers
- Research validation: docs/validation/mass_controlled_rolloff_research.md (archived)

## Implementation Notes

**For Horn-Loaded Systems:**
```python
f_mass = (BL² / Re) / (π × Mms)
```

**For Direct Radiators (Sealed/Ported Boxes):**
```python
# DO NOT use JBL formula
# Instead, determine empirically from Hornresp validation:
# f_mass ≈ 4.5×Fc to 5.7×Fc (driver-specific)
# Test values from 200-800 Hz and validate against Hornresp
```

## Related Concepts

- **Voice coil inductance roll-off**: f_Le = Re / (2π × Le)
- **Combined HF roll-off**: When f_mass ≈ f_Le, creates 12 dB/octave roll-off
- **Direct radiator HF behavior**: Requires empirical validation, not theoretical formulas

## Validation Methodology

To find optimal f_mass for direct radiators:
1. Run Hornresp simulation for target enclosure
2. Extract SPL values at key frequencies (100, 500, 1000, 5000, 10000, 20000 Hz)
3. Test f_mass values from 200-800 Hz
4. Select f_mass with minimum max/avg error vs Hornresp
5. Expected tolerance: <3 dB max error, <1.5 dB avg error

**References:**
- Hornresp validation data for BC_8NDL51 sealed box
- Hornresp validation data for BC_15PS100 sealed box
- sealed_box.py implementation notes
