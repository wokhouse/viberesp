# Physics Model Rewrite Notes

**Date**: 2025-12-24
**Branch**: `rewrite/physics-model-cleanup`
**Status**: Cleanup complete, ready for new implementation

## Overview

The Viberesp physics model and simulation engine have been completely removed due to fundamental errors discovered in the initial implementation assumptions. This cleanup provides a clean slate for a whole-cloth rewrite.

## What Was Removed

### 1. Physics Simulation Code

**`src/viberesp/enclosures/`** - All enclosure implementations
- `base.py` - Abstract BaseEnclosure class (174 lines)
- `sealed.py` - SealedEnclosure implementation
- `horns/base_horn.py` - BaseHorn abstract class (286 lines)
- `horns/exponential_horn.py` - Complex physics model (472 lines)
- `horns/front_loaded_horn.py` - FrontLoadedHorn implementation (287 lines)

**`src/viberesp/simulation/`** - Frequency response simulator
- `frequency_response.py` - Unified simulator (215 lines)

**`src/viberesp/optimization/`** - Optimization code (if any existed)

### 2. Validation Code

**`src/viberesp/validation/`** - Removed validation infrastructure
- `hornresp_parser.py` - Parse Hornresp output
- `comparison.py` - Compare responses
- `metrics.py` - Validation metrics
- `plotting.py` - Validation plotting

**Kept**:
- `hornresp_exporter.py` - Export Viberesp params to Hornresp format
- `__init__.py` - Module structure

### 3. Literature Documentation

**`literature/`** - All research documentation
- 5 research categories with implementation notes
- Key references to Kolbrek, AES papers, etc.
- Physics model documentation

**`.viberesp/literature/`** - Additional research notes
- Investigation findings

### 4. Test Fixtures

**`tests/fixtures/`** - All test fixtures
- `drivers/` - Driver JSON files
- `hornresp/` - Hornresp simulation data
- `baselines/` - Baseline metrics

**Test implementation files removed**:
- `tests/validation/test_synthetic_cases.py`
- `tests/validation/test_regression.py`
- `tests/test_enclosures.py`
- `tests/test_simulation.py`

## What Remains

### Infrastructure Scaffolding

**`src/viberesp/core/`** - Core data models (to be rewritten)
- `models.py` - Pydantic models structure
- `constants.py` - Physical constants

**`src/viberesp/cli.py`** - Click CLI framework (to be rewritten)

**`src/viberesp/io/`** - IO utilities (skeleton)
- `driver_db.py` - Database management structure
- `frd_parser.py` - FRD parsing structure

**`src/viberesp/utils/`** - Utilities (skeleton)
- `plotting.py` - Plotting utilities structure

**`src/viberesp/validation/`** - Validation exporter (functional)
- `hornresp_exporter.py` - Export to Hornresp format

**`tests/`** - Testing structure (empty, ready for new tests)

### Project Configuration

- `pyproject.toml` - Python packaging
- `.github/workflows/` - CI/CD structure (may need updates)

## Why the Rewrite?

### Fundamental Errors in Initial Assumptions

The previous physics model implementation had several critical issues:

1. **Impedance Topology Errors**: Incorrect acoustic impedance chain topology
2. **Mass Loading Calibration**: Required arbitrary calibration factors (4.0→1.0)
3. **Helmholtz Resonance**: Incorrect parallel/series combination of chamber impedances
4. **Mouth Reflection Model**: Incomplete finite horn transmission line model
5. **Validation Results**: Poor agreement with Hornresp (9-35 dB RMSE)

### Attempted Fixes Didn't Work

Multiple iterations of fixes were attempted:
- Phase 1: Front chamber Helmholtz resonance implementation
- Impedance topology corrections
- Mass loading factor adjustments
- Multi-mode standing wave implementations

Despite these efforts, the fundamental errors remained, with validation metrics showing:
- case3 (front chamber): 15.73 dB RMSE (down from 34.39, still unacceptable)
- case4 (complete system): 13.95 dB RMSE (down from 35.83, still unacceptable)

### Decision: Complete Rewrite

Given the depth of the issues, it was determined that:
- Patching the existing model would be more complex than rewriting
- The initial assumptions were fundamentally flawed
- A fresh start with correct acoustic theory would be faster

## Next Steps

1. **Design New Physics Model Architecture**
   - Research correct acoustic impedance chain topology
   - Design proper horn transmission line model
   - Plan chamber impedance combination rules

2. **Implement New Simulation Engine**
   - Correct mechanical impedance calculation
   - Proper electrical impedance with motional branch
   - Accurate volume velocity computation

3. **Rebuild Enclosure Implementations**
   - Sealed enclosures (2nd-order high-pass)
   - Exponential horns (finite transmission line)
   - Front-loaded horns (chamber coupling)

4. **Create New Test Fixtures**
   - Synthetic test cases for validation
   - Driver database for testing
   - Baseline metrics tracking

5. **Add Validation Framework**
   - Hornresp comparison tools
   - Metrics calculation (RMSE, MAE, F3, correlation)
   - Regression testing infrastructure

## Post-Cleanup State

### Directory Structure

```
src/viberesp/
├── cli.py                    # Click-based CLI (skeleton)
├── core/
│   ├── models.py            # Pydantic models (to be rewritten)
│   └── constants.py         # Physical constants
├── enclosures/
│   └── __init__.py          # Empty module (new implementations)
├── simulation/
│   └── __init__.py          # Empty module (new implementation)
├── validation/
│   ├── hornresp_exporter.py # Export to Hornresp (functional)
│   └── __init__.py
├── io/
│   ├── driver_db.py         # Driver database (skeleton)
│   └── frd_parser.py        # FRD parsing (skeleton)
└── utils/
    └── plotting.py          # Plotting utilities (skeleton)

tests/
├── __init__.py              # Empty module
└── validation/
    ├── __init__.py          # Empty module
    └── conftest.py          # Pytest fixtures structure (may be removed)

tools/                        # Can be repurposed
```

### What Still Works

- ✅ Driver database: `viberesp driver add/list/show/remove`
- ✅ Hornresp export: `viberesp export hornresp`

### What Doesn't Work

- ❌ Enclosure simulation: `viberesp simulate`
- ❌ Parameter sweeps: `viberesp scan`
- ❌ Validation: `viberesp validate`
- ❌ All enclosure calculations

## References (For Future Implementation)

The literature that was removed contained references to:
- Kolbrek, B. "Horn Theory: An Introduction"
- Beranek, L.L. "Acoustics"
- Olson, H.F. "Elements of Acoustical Engineering"
- Thiele, A.N. (1971) "Loudspeakers in Vented Boxes"
- Small, R.H. (1972) "Direct Radiator Loudspeaker System Analysis"
- AES papers on horn theory and impedance modeling

These should be re-consulted during the rewrite.

## Commit Message

```
Remove physics model and literature for complete rewrite

Fundamental errors discovered in initial assumptions regarding:
- Acoustic impedance chain topology
- Mass loading calibration requirements
- Helmholtz resonance impedance combinations
- Finite horn transmission line modeling

Removing all simulation code and literature to prepare
for whole-cloth rewrite with correct acoustic theory.

Kept:
- Infrastructure scaffolding (CLI, IO, testing structure)
- Hornresp parameter exporter (functional)
- Project configuration (pyproject.toml, CI/CD)

Removed:
- All enclosure implementations (enclosures/)
- Frequency response simulator (simulation/)
- Hornresp validation code (parser, comparison, metrics, plotting)
- Literature documentation (literature/, .viberesp/literature/)
- All test fixtures (tests/fixtures/)

Next: Design new physics model architecture from first principles
```

## Branch Status

- ✅ Created: `rewrite/physics-model-cleanup`
- ✅ Removed: All physics simulation code
- ✅ Removed: All validation code (except exporter)
- ✅ Removed: All literature documentation
- ✅ Removed: All test fixtures
- ✅ Created: Stub files for infrastructure
- ✅ Updated: Documentation (CLAUDE.md, README.md, REWRITE_NOTES.md)
- ✅ Ready: For new physics model implementation
