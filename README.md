# Viberesp

> **Quick enclosure exploration tool for Hornresp validation**

Viberesp is a Python tool for rapidly exploring enclosure designs for a given driver using Thiele-Small parameters. It provides fast preliminary simulations that can be exported to Hornresp for detailed validation and refinement.

## Design Philosophy

**Viberesp is not a replacement for Hornresp** — it's a complement:

- **Viberesp**: Rapid parameter sweeps, multi-objective optimization, quick "what-if" exploration
- **Hornresp**: Detailed acoustic simulation, diffraction effects, validated accuracy

**Typical workflow:**
1. Add your driver to Viberesp's database
2. Explore enclosure parameters quickly (volume sweeps, horn dimensions)
3. Export promising designs to Hornresp format
4. Validate in Hornresp for detailed simulation
5. Iterate back to Viberesp for further exploration

## Features

- **Driver Database**: Manage loudspeaker drivers with Thiele-Small parameters
- **Enclosure Simulation**: Frequency response modeling for:
  - Sealed enclosures
  - **Exponential horn enclosures** (with physics-based or empirical models)
  - **Front-loaded horn enclosures** (with front/rear chamber support)
  - Ported enclosures (coming soon)
  - Passive radiator enclosures (coming soon)
  - Transmission line enclosures (coming soon)
  - Bandpass enclosures (coming soon)
  - Tapped horn enclosures (coming soon)
- **Hornresp Integration**:
  - Export designs to Hornresp parameter format
  - Validate Viberesp output against Hornresp simulations
  - Generate comparison plots and metrics
- **Multi-Objective Optimization**: Find optimal enclosure parameters using genetic algorithms (coming soon)
- **FRD/ZMA File Support**: Import measurement data
- **Visualization**: Frequency response plots and performance metrics

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/viberesp.git
cd viberesp

# Install in development mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[dev,docs]"
```

## Quick Start

### 1. Add a Driver

```bash
viberesp driver add 18DS115 \
    --manufacturer "B&C" \
    --model "18DS115" \
    --fs 32 \
    --vas 158 \
    --qes 0.38 \
    --qms 6.52 \
    --sd 1210 \
    --re 5.0 \
    --bl 39.0 \
    --xmax 16.5 \
    --mms 330 \
    --cms 0.0824 \
    --rms 14.72
```

### 2. Explore Horn Designs

```bash
# Quick simulation with default physics model
viberesp simulate 18DS115 exponential_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --plot

# Parameter sweep: find optimal mouth area
viberesp scan 18DS115 exponential_horn \
    --param mouth_area_cm2 \
    --min 3000 --max 6000 --steps 10 \
    --throat-area 500 \
    --horn-length 200 \
    --cutoff 36
```

### 3. Export to Hornresp

```bash
# Export promising design for Hornresp validation
viberesp export hornresp 18DS115 -e front_loaded_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --front-chamber 6 \
    --output f118_design.txt \
    --comment "F118-style front-loaded horn"
```

Load `f118_design.txt` in Hornresp and run detailed simulation.

### 4. Validate Against Hornresp

```bash
# Compare Viberesp output with Hornresp simulation
viberesp validate hornresp 18DS115 hornresp_output.txt \
    -e front_loaded_horn \
    --params-file f118_design.txt \
    --hornresp-style \
    --export-plot validation_comparison.png
```

This generates RMSE, F3 error, and correlation metrics to verify Viberesp accuracy.

## Thiele-Small Parameters

Viberesp uses the standard Thiele-Small parameters to characterize loudspeaker drivers:

| Parameter | Description | Units |
|-----------|-------------|-------|
| Fs | Free-air resonance frequency | Hz |
| Vas | Equivalent compliance volume | L |
| Qes | Electrical Q factor | - |
| Qms | Mechanical Q factor | - |
| Qts | Total Q factor (Qts = Qes × Qms / (Qes + Qms)) | - |
| Sd | Effective diaphragm area | m² |
| Re | Voice coil DC resistance | Ω |
| Bl | Force factor (magnetic field × coil length) | T·m |
| Xmax | Maximum linear excursion | mm |
| Mms | Moving mass | g |

## Python API

### Basic Simulation

```python
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.horns import FrontLoadedHorn

# Define driver
driver = ThieleSmallParameters(
    fs=32.0,
    vas=158.0,
    qes=0.38,
    qms=6.52,
    sd=0.121,  # 1210 cm²
    re=5.0,
    bl=39.0,
    mms=330.0,
    cms=8.24e-5,
    rms=14.72
)

# Create front-loaded horn
params = EnclosureParameters(
    enclosure_type="front_loaded_horn",
    throat_area_cm2=500,
    mouth_area_cm2=4800,
    horn_length_cm=200,
    cutoff_frequency=36,
    rear_chamber_volume=100,
    front_chamber_volume=6,
    front_chamber_area_cm2=500,
    front_chamber_modes=3,
    radiation_model="beranek"
)

enclosure = FrontLoadedHorn(driver, params)

# Simulate
import numpy as np
frequencies = np.logspace(1, 3.3, 600)  # 10 Hz - 2 kHz
spl_db, phase_degrees = enclosure.calculate_frequency_response(frequencies)

print(f"F3: {enclosure.calculate_f3():.1f} Hz")
print(f"Sensitivity: {enclosure.calculate_sensitivity():.1f} dB")
```

### Export to Hornresp

```python
from viberesp.validation.hornresp_exporter import export_hornresp_params

# Export design for Hornresp validation
export_hornresp_params(
    driver=driver,
    params={
        'throat_area_cm2': 500,
        'mouth_area_cm2': 4800,
        'horn_length_cm': 200,
        'cutoff_frequency': 36,
        'rear_chamber_volume': 100,
        'front_chamber_volume': 6,
    },
    enclosure_type='front_loaded_horn',
    output_path='f118_design.txt',
    comment='F118-style front-loaded horn'
)
```

### Validate Against Hornresp

```python
from viberesp.validation import (
    parse_hornresp_output,
    compare_responses,
    calculate_validation_metrics,
    plot_hornresp_style
)

# Parse Hornresp simulation output
hornresp_data = parse_hornresp_output('hornresp_sim.txt')

# Compare with Viberesp
comparison = compare_responses(
    viberesp_freq=frequencies,
    viberesp_spl=spl_db,
    hornresp_freq=hornresp_data.frequencies,
    hornresp_spl=hornresp_data.spl
)

# Calculate validation metrics
metrics = calculate_validation_metrics(comparison)
print(f"RMSE: {metrics.rmse:.2f} dB")
print(f"Correlation: {metrics.correlation:.3f}")

# Generate Hornresp-style comparison plot
plot_hornresp_style(
    comparison=comparison,
    data_source='both',
    output_path='validation.png'
)
```

## Enclosure Types

### Horn Enclosures (Exponential, Front-Loaded)

**High-efficiency enclosures using acoustic impedance transformation**

- **Exponential Horn**: Simple flare profile, predictable cutoff frequency
- **Front-Loaded Horn**: Horn with front/rear chambers for additional tuning
- Physics-based model: Acoustic impedance chain from driver to listener
- Empirical model: 2nd-order high-pass with horn gain (fallback)
- Ideal for: PA systems, bass horns, high-efficiency subwoofers

**Key Parameters:**
- `throat_area_cm2`: Throat cross-sectional area
- `mouth_area_cm2`: Mouth cross-sectional area
- `horn_length_cm`: Horn axial length
- `cutoff_frequency`: Horn cutoff frequency fc
- `rear_chamber_volume`: Rear chamber volume (optional)
- `front_chamber_volume`: Front chamber volume (front-loaded only)

**Validation Status:**
- Physics model under active development
- Export to Hornresp for validated designs recommended
- Target: RMSE < 5 dB vs Hornresp

### Sealed (Acoustic Suspension)

- Simplest design
- 2nd-order high-pass response
- Tight, accurate bass
- Lower efficiency
- Requires larger box for low F3
- Validated against Thiele/Small theory

### Ported (Bass Reflex)

- Extended low-frequency response
- 4th-order high-pass response
- Higher efficiency
- More complex design
- Port tuning critical
- Coming soon

### Passive Radiator

- Similar to ported but uses passive cone instead of port
- No port noise issues
- Typically more expensive
- Coming soon

### Transmission Line

- Quarter-wave resonator
- Extended bass with small footprint
- Complex design and construction
- Coming soon

### Bandpass

- 4th/6th/8th order filtering
- High efficiency in passband
- Narrow bandwidth
- Complex design
- Coming soon

## Optimization (Coming Soon)

Multi-objective optimization will balance:
- Frequency response flatness
- Bass extension (F3)
- Efficiency (SPL)
- Box size

```bash
# Find optimal horn parameters for a driver
viberesp optimize 18DS115 exponential_horn \
    --max-horn-length 250 \
    --min-throat-area 400 \
    --bass-weight 1.5 \
    --flatness-weight 1.0 \
    --generations 200
```

## Hornresp Workflow

Viberesp is designed to complement Hornresp, not replace it:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Viberesp      │─────>│   Hornresp       │─────>│   Build     │
│   (Explore)     │      │   (Validate)     │      │   (Test)    │
└─────────────────┘      └──────────────────┘      └─────────────┘
       ▲                                                        │
       └────────────────────────────────────────────────────────┘
                    Iterate based on measurements
```

**When to use Viberesp:**
- Rapid parameter exploration (sweeps across volume, tuning, dimensions)
- Initial design screening before detailed Hornresp simulation
- Multi-objective optimization (when implemented)
- Quick "what-if" analysis

**When to use Hornresp:**
- Final validation of promising designs
- Detailed acoustic simulation with diffraction effects
- Multi-segment horns and folded horns
- Room interaction and array modeling

## Testing

Viberesp includes automated tests to validate simulation accuracy against Hornresp reference data.

### Running Tests

```bash
# Run all validation tests
pytest tests/validation/ -v

# Check for regressions (strict - fails if metrics degrade)
pytest tests/validation/test_regression.py::test_regression_no_degradation -v

# Track improvements
pytest tests/validation/test_regression.py::test_regression_improvement_tracking -v -s
```

### Test Infrastructure

The test suite includes:

- **Synthetic Test Cases**: 4 progressively complex horn designs
  - Case 1: Straight exponential horn (no chambers)
  - Case 2: Horn + rear chamber
  - Case 3: Horn + front chamber
  - Case 4: Complete F118-style system

- **Regression Testing**: Ensures simulation quality doesn't degrade
  - Strict: Tests fail if RMSE increases or correlation decreases
  - Tracks improvements over time
  - Baseline history for trend analysis

- **Validation Metrics**: RMSE, F3 error, correlation, MAE

Current baseline metrics (starting point for tracking improvements):
```
Case                          RMSE (dB)    Correlation
case1_straight_horn            13.56        -0.21
case2_horn_rear_chamber         9.22         0.00
case3_horn_front_chamber        34.39         0.33
case4_complete_system           35.83         0.22
```

Note: The current physics model has poor agreement with Hornresp. This establishes the baseline for tracking future physics model improvements.

### Updating Baselines

After improving the physics model with literature backing:

```bash
# 1. Generate new baselines
PYTHONPATH=src python3 tools/generate_baselines.py

# 2. Review the improvements (metrics should get better)
git diff tests/fixtures/baselines/

# 3. Commit with explanation
git commit -m "Improve front chamber Helmholtz model

Added standing wave modes 1-3 to front chamber impedance
calculation based on Beranek (1954) pipe theory.

Improvements:
- case3 RMSE: 34.39 → 12.5 dB
- case4 RMSE: 35.83 → 15.2 dB

References:
- Beranek, L.L. 'Acoustics', §5.15"
"
```

See `tests/fixtures/hornresp/synthetic/README.md` for detailed test case documentation.

## Physics Model Status

The horn physics model is under active development:

**Implemented:**
- Acoustic impedance chain method (driver → throat → horn → mouth → listener)
- Mouth radiation impedance (Beranek circular piston model)
- Finite horn transmission line model
- Multi-mode front chamber Helmholtz resonance
- Rear chamber compliance modeling

**Current Status:**
- RMSE: 9-35 dB vs Hornresp (baseline established 2024-12-24)
- Target: RMSE < 5 dB vs Hornresp
- Use empirical model or export to Hornresp for validated designs

## License

MIT License - see LICENSE file for details.

## References

- Hornresp by David McBean: http://www.hornresp.net/
- Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
- Small, R.H. (1972). "Direct Radiator Loudspeaker System Analysis"
- Beranek, L.L. "Acoustics"
- Olson, H.F. "Elements of Acoustical Engineering"
- Kolbrek, B. "Horn Theory: An Introduction"
- [Thiele-Small Parameters (Wikipedia)](https://en.wikipedia.org/wiki/Thiele/Small_parameters)
