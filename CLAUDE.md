# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Viberesp is a Python application for loudspeaker enclosure design and optimization using Thiele-Small parameters. It provides both CLI and Python API interfaces for simulating different enclosure types.

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

# Run specific test file
pytest tests/test_specific.py
```

## Architecture

### Module Structure

The codebase follows a layered architecture centered on acoustic simulation:

```
src/viberesp/
├── cli.py                    # Click-based CLI entry point
├── core/
│   ├── models.py            # Pydantic models: ThieleSmallParameters, EnclosureParameters
│   └── constants.py         # Physical constants (rho, c, air properties)
├── enclosures/
│   ├── base.py              # Abstract BaseEnclosure class
│   ├── sealed.py            # SealedEnclosure implementation
│   └── [ported, passive radiator, etc.]
├── simulation/
│   └── frequency_response.py # FrequencyResponseSimulator - unified response calculator
├── optimization/
│   └── (pymoo-based multi-objective optimization)
└── io/
    ├── driver_db.py         # JSON driver database management
    └── frd_parser.py        # FRD/ZMA measurement file parsing
```

### Key Design Patterns

1. **Abstract Base Class Pattern**: `BaseEnclosure` defines the interface all enclosure types must implement, including `calculate_system_response()` for computing transfer functions.

2. **Pydantic Data Validation**: All T/S parameters use Pydantic models for validation. Units are carefully managed - `vas` is in liters, `sd` is in m². The system validates physical feasibility (e.g., Qts must be derived from Qes/Qms).

3. **Enclosure Type Enum**: `EnclosureType` enum provides type-safe enclosure specification with string conversion for CLI.

4. **Unified Simulation**: `FrequencyResponseSimulator` works with any enclosure type via the base class interface, computing magnitude/phase responses and performance metrics (F3, F10, sensitivity, group delay).

### Acoustic Calculations

All enclosure calculations follow established Thiele/Small formulas:
- Sealed enclosures: 2nd-order high-pass based on Qtc and Fc
- Frequency response computed over 10 Hz - 20 kHz range (configurable)
- Metrics include F3, F10 cutoffs, SPL at 2.83V, peak SPL

### Driver Database

Drivers stored in JSON (location configurable via environment or default). CLI commands provide add/list/show operations. Database stores manufacturer, model name, and all T/S parameters.

## Code Conventions

- **Line length**: 100 characters (configured in black/isort)
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public methods/classes
- **Import style**: isort with black profile
- **Python version**: 3.9+ (code supports 3.9-3.11, local env may be 3.13)

## Adding New Enclosure Types

When adding a new enclosure type:
1. Inherit from `BaseEnclosure` in `enclosures/base.py`
2. Implement `calculate_system_response()` returning complex transfer function
3. Add type to `EnclosureType` enum in `core/models.py`
4. Register in CLI factory in `cli.py`
5. Add unit tests in `tests/`

## CLI Structure

The Click-based CLI has these main command groups:
- `viberesp driver` - Manage driver database (add, list, show, remove)
- `viberesp simulate` - Run single enclosure simulation with optional plotting
- `viberesp scan` - Parameter sweep across volume/tuning ranges
- `viberesp optimize` - Multi-objective optimization (planned)

## Testing Status

Tests directory exists but is currently empty. When adding tests:
- Place in `tests/` directory
- Name files `test_*.py`
- Use pytest fixtures for common setup (driver parameters, enclosures)
- Target coverage configured in pytest.ini_options

## Dependencies

Key dependencies:
- **NumPy/SciPy**: Array operations and signal processing
- **Pydantic**: Data validation and settings management
- **Click**: CLI framework
- **Matplotlib**: Frequency response plotting
- **Pymoo**: Multi-objective optimization (NSGA-II, etc.)
- **Pandas**: CSV/FRD file parsing
