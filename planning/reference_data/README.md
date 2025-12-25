# Hornresp Reference Data

This directory contains Hornresp input files and reference data for validating the Viberesp physics model implementation.

## Directory Structure

```
reference_data/
├── inputs/           # Hornresp parameter files
│   └── TC-P1-RAD-01/
│       ├── hornresp_params.txt    # Hornresp input parameters
│       └── setup_notes.md         # Configuration rationale
└── outputs/          # Extracted reference data
    └── TC-P1-RAD-01/
        ├── impedance_data.csv     # Hornresp impedance export
        ├── hornresp_screenshot.png
        ├── extraction_log.txt
        └── validation_results.json
```

## Purpose

Each test case has corresponding Hornresp reference data to validate the physics implementation:

- **Phase 1**: Radiation impedance (circular piston in infinite baffle)
- **Phase 2**: Single-segment horn T-matrices (exponential, conical, etc.)
- **Phase 3**: Driver equivalent circuit modeling
- **Phase 4**: Complete front-loaded horn systems
- **Phase 5**: Multi-segment horns
- **Phase 6**: Advanced features (tapped horns, transmission lines)

## Workflow

1. **Generate Inputs**: Create Hornresp parameter file for test case
2. **Run Hornresp**: Import parameters and generate simulation (manual)
3. **Extract Outputs**: Export impedance, SPL, and other relevant data
4. **Validate**: Compare Viberesp results with Hornresp reference data
5. **Document**: Record validation results and any discrepancies

## Naming Convention

- Input files: `TC-<PHASE>-<CATEGORY>-<NUMBER>_hornresp_params.txt`
- Output files: `TC-<PHASE>-<CATEGORY>-<NUMBER>_<metric>.csv`

## Status Legend

| Status | Description |
|--------|-------------|
| Pending | Test case defined, reference data not yet generated |
| In Progress | Hornresp analysis underway |
| Complete | Reference data collected and validated |
| Failed | Unable to generate valid reference data |

## Current Status

### Phase 1: Radiation Impedance

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC-P1-RAD-01 | Pending | Waiting for manual Hornresp analysis |

---

*Last updated: 2025-12-24*
