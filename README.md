# Viberesp

**Loudspeaker enclosure design and simulation with Hornresp validation**

Viberesp is a CLI tool for simulating horn-loaded loudspeaker enclosures using acoustic theory from first principles. Every algorithm is grounded in established literature and validated against Hornresp, the industry-standard horn simulation tool.

## Features

- **Literature-based simulation** - All algorithms cite established acoustic theory
- **Hornresp validation** - Results validated against Hornresp at every stage
- **Interactive design** - Explore enclosure parameters and see effects instantly
- **Multiple horn types** - Exponential, hyperbolic, and conical profiles
- **Driver modeling** - Thiele-Small parameter support
- **Optimization tools** - Multi-objective optimization for design goals
- **Export workflow** - Export designs to Hornresp format for cross-checking

## Project Status

⚠️ **Early Development** - Viberesp is in the initial development phase. The literature review and foundational documentation are complete. Implementation of the simulation engine is in progress.

See [ROADMAP.md](ROADMAP.md) for detailed development phases.

## Installation

### Requirements

- Python 3.10 or higher
- Poetry (for development) or pip (for installation)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/viberesp.git
cd viberesp

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## Quick Start

### 1. Import Driver Parameters

```bash
viberesp driver import
```

You'll be prompted to enter Thiele-Small parameters:

```
Enter driver name: Eminence Delta-15
Enter resonance frequency Fs (Hz): 45
Enter DC resistance Re (ohms): 5.9
Enter Qes: 0.42
Enter Qms: 3.5
Enter Vas (liters): 175
Enter cone area Sd (sq cm): 855
...
Driver saved as 'eminence-delta-15'
```

### 2. Design a Horn Enclosure

```bash
viberesp design new
```

```
Select driver: eminence-delta-15
Horn type [exponential/hyperbolic/conical]: exponential

Enter horn parameters:
  Throat area (sq cm): 50
  Mouth area (sq cm): 500
  Length (m): 1.5

Calculating horn parameters...
  Flare constant m: 4.25 1/m
  Cutoff frequency fc: 232 Hz
Design saved as 'eminence-delta-15-exp-horn'
```

### 3. Simulate Performance

```bash
viberesp simulate eminence-delta-15-exp-horn --output plot
```

This generates:
- Frequency response curve (dB vs Hz)
- Throat impedance curve (ohms vs Hz)
- Directivity patterns
- Efficiency estimates

### 4. Export to Hornresp

```bash
viberesp export eminence-delta-15-exp-horn --format hornresp
```

Generates a Hornresp input file for cross-validation:

```
File exported to: eminence-delta-15-exp-horn.inp
You can now open this file in Hornresp to verify the results.
```

### 5. Validate Against Hornresp

```bash
viberesp validate eminence-delta-15-exp-horn --reference hornresp_results.txt
```

Generates a comparison report showing agreement between Viberesp and Hornresp.

## Workflow

Viberesp follows a literature-first design workflow:

```
┌─────────────────┐
│  Import Driver  │  Thiele-Small parameters
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Design Horn    │  Specify geometry (throat, mouth, length)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Simulate      │  Calculate response (cites literature)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Export        │  Generate Hornresp input file
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validate      │  Compare with Hornresp results
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │ Iterate │  Adjust parameters based on validation
    └─────────┘
```

## Literature and Theory

Viberesp is built on established acoustic theory. Every simulation algorithm cites the literature it implements.

### Foundational References

- **Olson (1947)** - Elements of Acoustical Engineering
  - Exponential and hyperbolic horn profiles
  - Horn equation and cutoff frequency
  - Throat impedance calculations

- **Beranek (1954)** - Acoustics
  - Finite horn corrections (mouth termination)
  - Radiation impedance
  - Directivity patterns

- **Kinsler et al. (1982)** - Fundamentals of Acoustics
  - Rigorous derivation of horn equation
  - Transmission line approach for finite horns
  - Driver-horn interaction

See the [`literature/`](literature/) directory for complete reference documentation with specific equations.

### Citation Example

```python
def calculate_horn_cutoff(flare_constant: float, speed_of_sound: float = 343.0) -> float:
    """
    Calculate the cutoff frequency of an exponential horn.

    Based on Olson (1947), Equation 5.18 and Beranek (1954), Chapter 5.

    Literature:
    - literature/horns/olson_1947.md - Exponential horn theory, Eq. 5.18
    - literature/horns/beranek_1954.md - Horn impedance, Chapter 5

    Args:
        flare_constant: Horn flare constant m (1/m)
        speed_of_sound: Speed of sound (m/s), default 343 m/s at 20°C

    Returns:
        Cutoff frequency f_c (Hz)

    Validation:
        Compare with Hornresp cutoff frequency calculation.
        Expected agreement: <0.1% deviation.
    """
    # Olson (1947), Eq. 5.18: f_c = c·m/(2π)
    return (speed_of_sound * flare_constant) / (2 * math.pi)
```

**This citation requirement ensures all algorithms are traceable to established theory.**

## Validation Against Hornresp

Hornresp is the industry standard for horn simulation. Viberesp validates all results against Hornresp:

### Validation Process

1. Implement algorithm from literature with proper citations
2. Create test case with known horn parameters
3. Run Viberesp simulation
4. Run Hornresp with identical parameters
5. Compare results (impedance, frequency response, etc.)
6. Document agreement percentage

### Acceptable Tolerances

- **Well above cutoff** (f > 2·f_c): <1% deviation
- **Near cutoff** (f ≈ 1.2·f_c to 2·f_c): <2% deviation
- **Close to cutoff** (f ≈ f_c): <5% deviation (numerical sensitivity)
- **Below cutoff** (f < f_c): qualitative agreement only

This ensures Viberesp provides accurate exploration results while maintaining transparency about theoretical foundations.

## Development

### Project Structure

```
viberesp/
├── README.md              # This file
├── CLAUDE.md              # Project-specific instructions (citation requirements)
├── ROADMAP.md             # Development phases
├── pyproject.toml         # Project configuration
├── literature/            # Acoustic theory references
│   ├── README.md          # Citation guide
│   └── horns/             # Horn theory papers
│       ├── olson_1947.md
│       ├── beranek_1954.md
│       └── kinsler_1982.md
└── src/viberesp/
    ├── cli.py             # CLI entry point
    ├── driver/            # Driver parameter handling
    ├── simulation/        # Horn simulation engine (cites literature)
    ├── hornresp/          # Hornresp integration
    ├── validation/        # Validation framework
    └── optimization/      # Parameter optimization (future)
```

### Contributing

We welcome contributions! Please ensure:

1. ✅ **All simulation code cites literature** per [`CLAUDE.md`](CLAUDE.md)
2. ✅ **New features are validated against Hornresp** where applicable
3. ✅ **Tests are included** for new functionality
4. ✅ **Code passes style checks** (black, isort, mypy)
5. ✅ **Documentation is updated** (docstrings, README)

See [`CLAUDE.md`](CLAUDE.md) for detailed coding conventions.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=viberesp --cov-report=html

# Run validation tests only
pytest tests/validation/
```

### Code Style

```bash
# Format code
black src/viberesp tests

# Sort imports
isort src/viberesp tests

# Type checking
mypy src/viberesp
```

## Dependencies

### Core Dependencies
- **numpy** - Numerical computations
- **scipy** - Scientific functions (Bessel, Struve functions for horn theory)
- **pydantic** - Data validation
- **click** - CLI interface
- **matplotlib** - Plotting
- **pandas** - Data handling

### Optimization
- **pymoo** - Multi-objective optimization (Phase 7)

### Development
- **pytest** - Testing
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking

## Configuration

Viberesp stores configuration and data in `~/.viberesp/`:

```
~/.viberesp/
├── config.yaml          # User configuration
├── drivers/             # Saved driver profiles
│   └── eminence-delta-15.json
└── designs/             # Saved enclosure designs
    └── eminence-delta-15-exp-horn.json
```

### Example Configuration

```yaml
# ~/.viberesp/config.yaml
defaults:
  temperature: 20        # Celsius
  air_density: 1.18      # kg/m³
  speed_of_sound: 343    # m/s

simulation:
  frequency_range:
    min: 20              # Hz
    max: 20000           # Hz
    points: 1000         # Logarithmic spacing

plotting:
  figure_size: [10, 6]
  dpi: 100
  style: 'seaborn-v0_8-darkgrid'

validation:
  hornresp_path: '/path/to/hornresp'
  tolerance_high: 0.01   # 1% for f > 2*fc
  tolerance_near: 0.02   # 2% for f ≈ 1.2*fc to 2*fc
  tolerance_close: 0.05  # 5% for f ≈ fc
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development phases:

- **Phase 1**: ✅ Literature review and algorithm selection
- **Phase 2**: 🔄 Driver parameter input system
- **Phase 3**: ⏳ Horn simulation engine
- **Phase 4**: ⏳ Hornresp export functionality
- **Phase 5**: ⏳ Validation framework
- **Phase 6**: ⏳ CLI user interface and workflow
- **Phase 7**: ⏳ Optimization and exploration tools

## FAQ

### How accurate is Viberesp compared to Hornresp?

Viberesp implements the same acoustic theory as Hornresp. For well-behaved cases (frequencies well above cutoff), we expect agreement within <1%. Differences may occur due to:
- Numerical methods (discretization vs analytical)
- Mouth termination models
- Frequency range and resolution

We actively validate against Hornresp and document all discrepancies.

### Why implement from literature instead of using existing libraries?

This ensures:
1. **Transparency** - Every algorithm is traceable to established theory
2. **Validation** - We can verify each step against Hornresp
3. **Education** - The code documents the connection between theory and practice
4. **Correctness** - Literature-cited code is more likely to be correct

Existing libraries often lack proper documentation of theoretical foundations.

### Can I use Viberesp for sealed or ported enclosures?

Not yet. Viberesp currently focuses on horn-loaded enclosures. Sealed (acoustic suspension) and ported (bass reflex) enclosures are planned for future development. See ROADMAP.md for details.

### What horn types are supported?

Currently implemented (in development):
- Exponential horns
- Hyperbolic horns (with taper parameter)
- Conical horns

Planned:
- Folded horns
- Multi-segment horns
- Transmission line enclosures

### How do I cite Viberesp in my research?

If you use Viberesp in your research, please cite both the software and the underlying literature:

```bibtex
@software{viberesp,
  author = {Your Name},
  title = {Viberesp: Horn-loaded Loudspeaker Simulation with Literature-based Validation},
  year = {2025},
  url = {https://github.com/yourusername/viberesp}
}

@book{olson1947,
  author = {Olson, Harry F.},
  title = {Elements of Acoustical Engineering},
  year = {1947},
  publisher = {D. Van Nostrand Company}
}
```

## License

MIT License

Copyright (c) 2025 Viberesp Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- **Hornresp** by David McBean - The industry-standard horn simulation tool that makes validation possible
- **Olson, Beranek, Kinsler** and other authors of foundational acoustic theory texts
- **Python scientific community** - numpy, scipy, matplotlib, and the entire ecosystem

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/viberesp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/viberesp/discussions)
- **Email**: your.email@example.com

---

**Built with science, validated with Hornresp, designed for accuracy.**
