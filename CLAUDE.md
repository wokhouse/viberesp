# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Viberesp is a Python application for loudspeaker enclosure design and optimization using Thiele-Small parameters. **NOTE: This codebase is currently undergoing a complete physics model rewrite.**

## Development Commands

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies (includes test, linting tools)
pip install -e ".[dev,docs]"

# Format code
black src/

# Sort imports
isort src/

# Type check
mypy src/

# Run tests with coverage
pytest --cov=src/viberesp
```

## Architecture

### Current State (Post-Cleanup)

The codebase has been cleaned up for a physics model rewrite. **The simulation engine is currently non-functional.**

**What Remains (Infrastructure Scaffolding):**
- `src/viberesp/core/` - Pydantic models and constants (to be rewritten)
- `src/viberesp/cli.py` - Click CLI framework structure (to be rewritten)
- `src/viberesp/io/` - Driver database and FRD parsing utilities (skeleton)
- `src/viberesp/validation/hornresp_exporter.py` - Export to Hornresp format (functional)
- `src/viberesp/utils/` - Plotting utilities (skeleton)
- `tests/` - Testing framework structure (empty)

**What Was Removed (For Rewrite):**
- All enclosure implementations (`enclosures/`)
- Frequency response simulator (`simulation/`)
- Hornresp validation code (parser, comparison, metrics)
- Literature documentation (`literature/`, `.viberesp/literature/`)
- All test fixtures (`tests/fixtures/`)

See `REWRITE_NOTES.md` for details on what was removed and why.

## Code Conventions

- **Line length**: 100 characters (configured in black/isort)
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public methods/classes
- **Import style**: isort with black profile
- **Python version**: 3.9+

### Literature Citation Policy (CRITICAL)

**ALL implementations MUST directly cite the literature source(s) used.**

This is a physics-based project where every formula, algorithm, and implementation decision should be traceable to the research literature.

#### Citation Format in Code

```python
def radiation_impedance(area: float, frequency: float) -> complex:
    """
    Calculate radiation impedance for circular piston in infinite baffle.

    References:
        - Kolbrek (2019) Part 1: Radiation and T-Matrix
          https://hornspeakersystems.info/
        - literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md

    Implementation follows Kolbrek Part 1, Eq. (X) for normalized radiation impedance.
    """
    # Formula from Kolbrek Part 1: Z_norm = R(ka) + jX(ka)
    ...
```

#### Required Citation Elements

1. **Primary literature source** (paper, book, or tutorial)
2. **Specific section/equation reference** (e.g., "Eq. (12)", "Section 3.2")
3. **Link to local markdown file** in `literature/` directory
4. **Implementation notes** explaining any deviations or approximations

#### Examples

```python
# GOOD: Complete citation with references
def exponential_horn_matrix(k, Zrc, S1, S2, L):
    """
    Calculate transfer matrix for exponential horn segment.

    References:
        - Kolbrek (2019) Part 1, Section "Exponential Horn T-Matrix"
        - literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md

    Implements Kolbrek Part 1, Eq. (13)-(16) for T-matrix elements.
    Uses numpy for Bessel functions j1 and struve H1.
    """
    # From Kolbrek Part 1: m = ln(S2/S1) / (2L)
    m = np.log(S2/S1) / (2*L)
    ...

# BAD: No citation (DO NOT DO THIS)
def exponential_horn_matrix(k, Zrc, S1, S2, L):
    """Calculate exponential horn transfer matrix."""
    m = np.log(S2/S1) / (2*L)  # Where does this formula come from?
    ...
```

#### Literature Directory Structure

The `literature/` directory contains:
- **Phase-organized papers**: `phase1_radiation/`, `phase2_tmatrix/`, etc.
- **Markdown summaries**: Extracted formulas, implementation notes
- **RAG-ready content**: For AI-assisted development

See `literature/README.md` for complete catalog and acquisition status.

## Rewrite Status

The physics model and simulation engine are being completely rewritten due to fundamental errors in the initial implementation assumptions.

**Next Steps:**
1. Design new physics model architecture
2. Implement new simulation engine
3. Rebuild enclosure implementations
4. Create new test fixtures
5. Add validation framework

**What Still Works:**
- Hornresp parameter export: `viberesp export hornresp` command
- Driver database: `viberesp driver` commands

**What Doesn't Work:**
- Simulation: `viberesp simulate` command (non-functional)
- Validation: `viberesp validate` command (removed)
- All enclosure calculations (removed)

## Hornresp Export (Still Functional)

The Hornresp exporter remains functional and can be used to export enclosure parameters to Hornresp format:

```bash
# Export exponential horn
viberesp export hornresp <driver_name> -e exponential_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --output horn.txt
```

See `README.md` for usage examples.
