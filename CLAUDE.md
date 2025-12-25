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
