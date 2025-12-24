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
│   ├── horns/
│   │   ├── base_horn.py     # BaseHorn abstract class with shared horn logic
│   │   ├── exponential_horn.py # ExponentialHorn implementation
│   │   └── front_loaded_horn.py # FrontLoadedHorn implementation
│   └── [ported, passive radiator, etc.]
├── simulation/
│   └── frequency_response.py # FrequencyResponseSimulator - unified response calculator
├── validation/
│   ├── hornresp_parser.py   # Parse Hornresp output and parameter files
│   ├── hornresp_exporter.py # Export Viberesp parameters to Hornresp format
│   ├── comparison.py        # Compare Viberesp and Hornresp responses
│   ├── metrics.py           # Calculate validation metrics (RMSE, MAE, F3, etc.)
│   └── plotting.py          # Generate validation plots (comprehensive and Hornresp-style)
├── optimization/
│   └── (pymoo-based multi-objective optimization)
├── io/
│   ├── driver_db.py         # JSON driver database management
│   └── frd_parser.py        # FRD/ZMA measurement file parsing
└── utils/
    └── plotting.py          # Plotting utilities for frequency response
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

## Horn Enclosures

Horn enclosures provide acoustic impedance transformation between the driver and listening space, resulting in improved efficiency and controlled directivity.

### Horn Architecture

The horn implementation follows a hierarchical structure:

```
BaseEnclosure (abstract)
    └── BaseHorn (abstract)
        └── ExponentialHorn (concrete)
        └── TappedHorn (planned)
        └── FrontLoadedHorn (planned)
```

### Horn Parameters (in EnclosureParameters)

- **throat_area_cm2**: Throat cross-sectional area (cm²) - Required
- **mouth_area_cm2**: Mouth cross-sectional area (cm²) - Required
- **horn_length_cm**: Horn axial length (cm) - Required
- **flare_rate**: Exponential flare rate m (1/m) - Optional
- **cutoff_frequency**: Horn cutoff frequency fc (Hz) - Optional
- **horn_type**: Flare type (exponential, hyperbolic, conical, tractrix) - Optional
- **t_value**: Hyperbolic horn T parameter - Optional
- **tap_position_cm**: Driver tap position from throat (tapped horns) - Optional
- **rear_chamber_volume**: Rear chamber volume (L) - Optional
- **front_chamber_volume**: Front chamber volume (L) - Optional
- **front_chamber_area_cm2**: Front chamber area (cm²) - For front_loaded_horn
- **rear_chamber_length_cm**: Rear chamber length (cm) - For front_loaded_horn
- **front_chamber_modes**: Number of front chamber pipe modes (0=Helmholtz only, 3=with standing waves) - Default: 0
- **radiation_model**: Radiation impedance model ('simple' or 'beranek') - Default: 'simple'
- **use_physics_model**: Use physics-based impedance model (True) or empirical model (False) - Default: True

### Physics-Based vs Empirical Models

Horn enclosures support two frequency response calculation methods:

#### Physics Model (Default)

The physics model uses an **acoustic impedance chain** method:

```
Driver Force → Volume Velocity → Throat Impedance → Horn Transfer → Mouth Pressure → SPL
```

**Key equations:**
1. **Driver Mechanical Impedance:**
   ```
   Z_m = R_ms + jωM_ms + 1/(jωC_ms) + S_d² × Z_acoustic
   ```

2. **Electrical Impedance with Motional Branch:**
   ```
   Z_e = R_e + jωL_e + (B*l)² / Z_m
   ```

3. **Volume Velocity at Throat:**
   ```
   U_throat = (B*l × V_in) / (Z_e × Z_m) × S_d
   ```

4. **Mouth Pressure:**
   ```
   P_mouth = U_throat × Z_throat × sqrt(area_ratio) × (Z_mouth / |Z_mouth|)
   ```

5. **SPL Calculation:**
   ```
   SPL = 20 × log10(|P_mouth| / P_ref)
   ```

**Features:**
- Beranek circular piston radiation impedance model
- Finite horn transmission line with mouth reflections
- Multi-mode front chamber Helmholtz resonance
- Rear chamber compliance in parallel with throat load

#### Empirical Model (Fallback)

The empirical model uses a **parameterized 2nd-order high-pass** approach:

- Loaded driver parameters (Fs shifted by horn loading)
- Horn gain from area ratio
- Empirical peak frequency and sharpness coefficients
- Helmholtz resonance for front chambers

**Usage:**

```python
# Use physics model (default, more accurate in theory)
params = EnclosureParameters(
    enclosure_type='exponential_horn',
    throat_area_cm2=600,
    mouth_area_cm2=4800,
    horn_length_cm=200,
    cutoff_frequency=35,
    use_physics_model=True,  # Physics-based model
    radiation_model='beranek',
    ...
)

# Use empirical model (tested, fallback)
params = EnclosureParameters(
    enclosure_type='exponential_horn',
    throat_area_cm2=600,
    mouth_area_cm2=4800,
    horn_length_cm=200,
    cutoff_frequency=35,
    use_physics_model=False,  # Empirical model
    ...
)
```

**Note:** The physics model is currently under active development. The empirical model provides more reliable results for validation against Hornresp at this time.

### BaseHorn Class

The `BaseHorn` abstract class extends `BaseEnclosure` with shared horn functionality:

- **calculate_throat_impedance()**: Calculate acoustic impedance at horn throat (abstract)
- **calculate_cutoff_frequency()**: Calculate horn cutoff from flare rate or explicit parameter
- **validate_mouth_size()**: Check mouth size vs cutoff (k_rm >= 0.7 requirement)
- **calculate_horn_gain()**: Calculate theoretical gain from area ratio: `10*log10(mouth/throat)` dB
- **calculate_loaded_parameters()**: Calculate driver parameters with horn loading effect

### ExponentialHorn Class

The `ExponentialHorn` implements two calculation methods (selected via `use_physics_model`):

**Physics Model** (use_physics_model=True):
1. **Driver Validation**: Checks Qts < 0.4, Fs < 80 Hz, throat sizing
2. **Throat Impedance**: Finite exponential horn with auto-calculated flare rate
3. **Mechanical/Electrical Impedance**: Full driver model with acoustic loading
4. **Volume Velocity**: Calculated from force balance: `U = (B*l × V) / (Z_e × Z_m) × S_d`
5. **Acoustic Pressure**: Mouth pressure from throat impedance transformation
6. **Fallback**: Automatically switches to empirical model on calculation error

**Empirical Model** (use_physics_model=False):
1. **Driver Validation**: Same as physics model
2. **Throat Impedance**: Infinite exponential horn model (Kolbrek formula)
3. **Horn Loading**: Increases effective Fs, reduces Vas with rear chamber
4. **Frequency Response**: 2nd-order high-pass with loaded parameters + horn gain
5. **Performance Metrics**: F3, F10, system Q, sensitivity with horn gain

### Horn Design Guidelines

**Driver Selection:**
- **Qts**: < 0.4 for tight control (warns if higher)
- **Fs**: < 80 Hz for bass applications
- **Throat size**: 0.5-1.5× driver Sd to avoid mismatch

**Mouth Sizing:**
- Minimum: k_rm >= 0.7 at cutoff for smooth response
- Recommended: k_rm >= 1.0 for optimal performance
- Where k_rm = (2π×fc/c) × mouth_radius

**CLI Usage:**

```bash
# Simulate exponential horn
viberesp simulate <driver_name> exponential_horn \
    --throat-area 50 \
    --mouth-area 1000 \
    --horn-length 120 \
    --flare-rate 4.0 \
    --cutoff 75 \
    --rear-chamber 20 \
    --plot
```

### Acoustic Equations

**Infinite Exponential Horn Throat Impedance:**
```
Z_A = (ρ₀c/S_t) × (√(1 - m²/(4k²)) + j×m/(2k))
```

**Horn Loading Effect:**
```
fs_loaded = fs × √(1 + (c / (2π×fc×S_throat))²)
Q_horn ≈ Qts × (fs / fs_loaded)
```

**Horn Gain:**
```
horn_gain_db = 10 × log10(mouth_area / throat_area)
```

### Validation Against Hornresp

Horn implementations are validated against Hornresp reference designs:
- Success criteria: Within 3-5 dB in passband
- Cutoff frequency prediction: < 2 Hz error
- Mouth reflection ripple analysis
- Reference designs in `tests/fixtures/hornresp_*.txt`

**CLI Usage:**

```bash
# Validate sealed enclosure against Hornresp output
viberesp validate hornresp <driver_name> <hornresp_output.txt> \
    --volume 40 \
    --export-plot validation_comparison.png

# Validate horn enclosure with Hornresp-style clean plot
viberesp validate hornresp <driver_name> <hornresp_output.txt> \
    -e exponential_horn \
    --params-file hornresp_params.txt \
    --hornresp-style \
    --export-plot hornresp_style_validation.png

# Validate front-loaded horn with comprehensive metrics
viberesp validate hornresp <driver_name> <hornresp_output.txt> \
    -e front_loaded_horn \
    --params-file params.txt \
    --export-plot full_validation.png \
    --output validation_metrics.json
```

**Validation Plot Styles:**

1. **Default (Comprehensive)**: 2×2 subplot layout with:
   - SPL overlay comparison (Viberesp vs Hornresp)
   - SPL difference with reference bands (±0.5, ±1, ±2 dB)
   - Phase comparison (if data available)
   - Metrics summary panel (RMSE, MAE, F3 error, correlation)

2. **Hornresp-Style** (`--hornresp-style`): Single clean plot with:
   - Red solid line for Viberesp data
   - Gray dashed line for Hornresp reference (comparison)
   - Semilog frequency axis matching Hornresp
   - Clean minimal grid
   - No metrics overlay or reference bands
   - Similar visual appearance to Hornresp software

**Python API Usage:**

```python
from viberesp.validation import (
    parse_hornresp_output,
    parse_hornresp_params,
    compare_responses,
    calculate_validation_metrics,
    plot_hornresp_style,
)

# Parse Hornresp data
hornresp_data = parse_hornresp_output('hornresp_sim.txt')
hornresp_params = parse_hornresp_params('params.txt')

# Run comparison
comparison = compare_responses(
    viberesp_freq=frequencies,
    viberesp_spl=spl_db,
    hornresp_freq=hornresp_data.frequencies,
    hornresp_spl=hornresp_data.spl,
)

# Calculate metrics
metrics = calculate_validation_metrics(comparison)

# Generate Hornresp-style plot (single curve)
plot_hornresp_style(
    comparison=comparison,
    data_source='viberesp',  # or 'hornresp' or 'both'
    output_path='hornresp_style.png',
)
```

### Future Horn Types

- **Tapped Horn**: Driver tapped at specific point, interference patterns
- **Multi-Segment**: Folded horns, tractrix profiles
- **Enhanced Physics**: Full Webster equation, mouth reflections

## CLI Structure

The Click-based CLI has these main command groups:
- `viberesp driver` - Manage driver database (add, list, show, remove)
- `viberesp simulate` - Run single enclosure simulation with optional plotting
- `viberesp scan` - Parameter sweep across volume/tuning ranges
- `viberesp validate` - Validate simulation output against reference tools (Hornresp)
- `viberesp export` - Export design parameters to external tools (Hornresp)
- `viberesp optimize` - Multi-objective optimization (planned)

### Simulate Command

The `viberesp simulate` command runs enclosure simulations and displays performance metrics.

**Visualization Options:**
- `--plot` / `-p`: Show frequency response plot interactively
- `--export-plot`: Save plot to file instead of displaying
- `--suppress-visualization`: Suppress interactive plot display (useful for automated runs, agent exploration, or CI/CD)

When `--suppress-visualization` is set, the plot will not be displayed interactively even if `--plot` is specified. This is particularly useful for:
- Automated testing where user interaction is not possible
- Agent/programmatic exploration where blocking on plot windows hinders workflow
- Batch simulations where you only want to save plots to files

**Examples:**

```bash
# Simulate with interactive plot (blocks until window closed)
viberesp simulate 12BG100 sealed --volume 40 --plot

# Simulate and save plot without interactive display
viberesp simulate 12BG100 sealed --volume 40 --export-plot response.png

# Simulate with --plot flag but suppress visualization (non-blocking)
viberesp simulate 12BG100 sealed --volume 40 --plot --suppress-visualization

# Simulate with both export and suppressed visualization
viberesp simulate 12BG100 sealed --volume 40 \
    --plot \
    --export-plot response.png \
    --suppress-visualization
```

### Export to Hornresp

The `export hornresp` command generates Hornresp-compatible parameter files from Viberesp driver and enclosure parameters. Auto-calculates Cms (mechanical compliance) from Vas and Sd if missing.

**CLI Usage:**

```bash
# Export sealed enclosure
viberesp export hornresp <driver_name> -e sealed \
    --volume 40 \
    --output sealed_horn.txt

# Export exponential horn
viberesp export hornresp <driver_name> -e exponential_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --output exponential_horn.txt

# Export front-loaded horn with comment
viberesp export hornresp 18DS115 -e front_loaded_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --front-chamber 6 \
    --output f118_style_horn.txt \
    --comment "B&C 18DS115 F118-style front-loaded horn"
```

**Parameters:**
- `--enclosure-type` / `-e`: Enclosure type (sealed, ported, exponential_horn, front_loaded_horn)
- `--volume` / `-v`: Box volume in liters [required for sealed/ported]
- `--throat-area`: Throat area in cm² [required for horns]
- `--mouth-area`: Mouth area in cm² [required for horns]
- `--horn-length`: Horn length in cm [required for horns]
- `--cutoff` / `-fc`: Horn cutoff frequency in Hz [for horns]
- `--rear-chamber`: Rear chamber volume in liters [for horns]
- `--front-chamber`: Front chamber volume in liters [for front_loaded_horn]
- `--output` / `-o`: Output file path [required]
- `--comment` / `-c`: Optional description for the design

**Auto-Calculation:**
- Cms is auto-calculated from Vas and Sd using: `Cms = Vas / (ρ₀ × c² × Sd²)`
- Rms is auto-calculated from Qms, Mmd, and Cms if missing: `Rms = (1/Qms) × sqrt(Mmd/Cms)`

**Integrated Validate-Export:**

The `validate hornresp` command supports `--export-viberesp-params` to export Viberesp parameters during validation:

```bash
# Validate and export Viberesp parameters in one step
viberesp validate hornresp <driver_name> <hornresp_output.txt> \
    -e front_loaded_horn \
    --params-file hornresp_params.txt \
    --export-viberesp-params viberesp_params.txt \
    --hornresp-style \
    --export-plot validation.png
```

This workflow allows direct comparison between Viberesp and Hornresp parameter files.

**Python API Usage:**

```python
from viberesp.validation.hornresp_exporter import export_hornresp_params
from viberesp.io.driver_db import DriverDatabase

# Load driver
db = DriverDatabase()
driver = db.get_driver('18DS115')

# Define enclosure parameters
params = {
    'throat_area_cm2': 500,
    'mouth_area_cm2': 4800,
    'horn_length_cm': 200,
    'cutoff_frequency': 36,
    'rear_chamber_volume': 100,
    'front_chamber_volume': 6,
}

# Export to Hornresp format
export_hornresp_params(
    driver=driver,
    params=params,
    enclosure_type='front_loaded_horn',
    output_path='18DS115_horn.txt',
    comment='F118-style front-loaded horn'
)
```

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
