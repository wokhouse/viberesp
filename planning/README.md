# Planning Directory

This directory contains implementation plans, test cases, and validation reports for the Viberesp physics model rewrite.

## Directory Structure

```
planning/
├── test_cases/           # Hornresp validation test cases
├── implementation_notes/  # Development notes and decisions
└── validation_reports/   # Test results and comparison data
```

## Development Phases

### Phase 1: Radiation Impedance Module
**Status**: Not Started
**Goal**: Implement circular piston radiation impedance in an infinite baffle
**Key Formula**: $Z_{norm} = R(ka) + jX(ka)$ where $R = 1 - \frac{J_1(2ka)}{ka}$

**Test Cases**: TC-P1-RAD-01 through TC-P1-RAD-05

### Phase 2: Single Horn Segment T-Matrices
**Status**: Not Started
**Goal**: Implement transfer matrices for exponential and conical horns
**Key Formula**: $M = \begin{bmatrix} a & b \\ c & d \end{bmatrix}$

**Test Cases**: TC-P2-EXP, TC-P2-CON, TC-P2-HYP, TC-P2-TRA, TC-P2-LEC

### Phase 3: Driver Equivalent Circuit
**Status**: Not Started
**Goal**: Model moving-coil driver using Thiele-Small parameters
**Key Formula**: Convert electrical/mechanical domains to acoustic domain

**Test Cases**: TC-P3-DRV-01 through TC-P3-DRV-06

### Phase 4: Complete Front-Loaded Horn System
**Status**: Not Started
**Goal**: Combine driver, chambers, and horn into complete system

**Test Cases**: TC-P4-FLH-01 through TC-P4-FLH-07

### Phase 5: Multi-Segment Horns
**Status**: Not Started
**Goal**: Support composite horns with matrix multiplication

**Test Cases**: TC-P5-MS-01 through TC-P5-MS-04

### Phase 6: Advanced Features
**Status**: Not Started
**Goal**: Tapped horns, back-loaded horns, transmission lines

**Test Cases**: TC-P6-TH, TC-P6-BLH, TC-P6-OD, TC-P6-TL

## Validation Criteria

| Metric | Tolerance | Priority |
|--------|-----------|----------|
| SPL Response | ±0.5 dB | Critical |
| Impedance Magnitude | ±3% | High |
| Impedance Phase | ±2° | Medium |
| Resonance Frequency | ±1% | Critical |
| Cutoff Frequency | ±2% | High |

## Reference Drivers

Three standard drivers defined for validation:
- **Driver A**: Generic 12-inch woofer (bass horns)
- **Driver B**: Generic 8-inch midrange (midbass horns)
- **Driver C**: Generic 15-inch pro woofer (high-output)

See `test_cases/drivers/` for full specifications.

## Open-Source References

| Project | Language | Notes |
|---------|----------|-------|
| loudspeaker-tmatrix | Python | T-matrix with Streamlit UI |
| Kolbrek/horns | Octave/Matlab | Reference implementation |
| Scimpy | Python | TS parameter modeling |
| SpeakerSim | Java | General speaker simulation |
| spkrd | C++/GTK | Modern design tool |

---

*Last updated: 2025-12-24*
