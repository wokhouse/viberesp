# Viberesp Development Roadmap

This roadmap outlines the development phases for viberesp, a CLI tool for horn-loaded loudspeaker simulation and design.

## Project Vision

Create a validated loudspeaker simulation tool that:
- Implements horn theory from first principles with proper literature citations
- Validates results against Hornresp at every development stage
- Provides interactive exploration of enclosure parameters
- Exports designs to Hornresp format for cross-checking

---

## Phase 1: Literature Review & Algorithm Selection ✅

**Status:** Complete
**Deliverables:**
- [x] Literature directory structure created
- [x] Foundational references documented (Olson 1947, Beranek 1954, Kinsler 1982)
- [x] Citation system established in `CLAUDE.md`
- [x] Key equations identified for implementation

**Key Algorithms Selected:**
- Exponential horn profile: Olson Eq. 5.12, Beranek Chapter 5
- Horn cutoff frequency: Olson Eq. 5.18
- Throat impedance: Kinsler Eq. 9.6.4 (transmission line approach)
- Mouth impedance: Beranek Eq. 5.20 (piston radiation)
- Finite horn corrections: Beranek Chapter 5, Kinsler Section 9.6

**Next:** Implement these algorithms with proper citations

---

## Phase 2: Driver Parameter Input System

**Status:** Pending
**Goal:** Create CLI interface for manual entry of Thiele-Small parameters

### Tasks

2.1 **Define Thiele-Small Parameter Data Structure**
- Create `driver/parameters.py` with Pydantic models
- Include all essential T/S parameters:
  - Fs: Resonance frequency (Hz)
  - Re: DC resistance (ohms)
  - Qes, Qms, Qts: Electrical/mechanical/total Q
  - Vas: Equivalent volume (L or m³)
  - Sd: Cone area (m²)
  - Bl: Force factor (T·m)
  - Mms: Moving mass (g)
  - Cms: Compliance (m/N)
  - Rms: Mechanical resistance (N·s/m)

2.2 **CLI Entry Commands**
- Implement `viberesp driver import` with interactive prompts
- Input validation (range checking, physical constraints)
- Unit conversion support (inches ↔ meters, liters ↔ m³)
- Save/load driver profiles to/from JSON

2.3 **Driver Database**
- Store saved driver profiles in `~/.viberesp/drivers/`
- List available drivers: `viberesp driver list`
- View driver details: `viberesp driver show <name>`
- Export/import driver profiles for sharing

**Literature:** Thiele (1971), Small (1972) - See `literature/thiele_small/` (to be created)

**Validation:**
- Test with known driver parameters (e.g., from manufacturer datasheets)
- Verify calculated parameters (e.g., check Qts = Qes·Qms/(Qes+Qms))

---

## Phase 3: Horn Simulation Engine

**Status:** Pending
**Goal:** Implement core horn acoustic theory with proper citations

### Tasks

3.1 **Horn Profile Functions**
- [ ] Exponential horn: S(x) = S_t·exp(m·x)
  - Literature: Olson Eq. 5.12, Beranek Chapter 5
- [ ] Hyperbolic horn: S(x) = S_t·[cosh(mx) + T·sinh(mx)]²
  - Literature: Olson Eq. 5.30, Kinsler Section 9.8
- [ ] Conical horn: S(x) = S_t·(1 + x/x_t)²
  - Literature: Kinsler Section 9.7

3.2 **Cutoff Frequency Calculations**
- [ ] Exponential horn cutoff: f_c = c·m/(2π)
  - Literature: Olson Eq. 5.18
- [ ] Hyperbolic horn cutoff (depends on taper parameter T)
- [ ] Validate against Hornresp for various flare constants

3.3 **Acoustic Impedance Calculations**
- [ ] Throat impedance for finite exponential horn
  - Literature: Kinsler Eq. 9.6.4 (transmission line)
  - Input: horn geometry, frequency
  - Output: complex impedance Z_t
- [ ] Mouth radiation impedance
  - Literature: Beranek Eq. 5.20 (piston in infinite baffle)
  - Implement Bessel and Struve functions (use scipy.special)
- [ ] Characteristic impedance Z_0
  - Literature: Kinsler Eq. 9.5.12

3.4 **Frequency Response Calculation**
- [ ] Pressure response vs frequency
- [ ] Power output vs frequency
- [ ] Efficiency calculation
  - Literature: Beranek Chapter 8, Olson Section 5.11

3.5 **Directivity Patterns**
- [ ] Directivity index vs frequency
  - Literature: Beranek Chapter 8
- [ ] Polar plot generation (for visualization)

**Validation:**
- Create test cases with known horn geometries
- Compare impedance curves with Hornresp
- Verify cutoff frequency within <0.1%
- Verify impedance magnitude within <1% for f > 1.5·f_c
- Investigate and explain any discrepancies >1%

**Deliverables:**
- `simulation/horn_theory.py` - All horn profile functions
- `simulation/response.py` - Frequency response calculations
- `simulation/electrical_analogies.py` - Circuit representations
- Unit tests for each function with literature citations
- Validation test suite comparing with Hornresp

---

## Phase 4: Hornresp Export Functionality

**Status:** Pending
**Goal:** Export viberesp designs to Hornresp input format

### Tasks

4.1 **Research Hornresp Input Format**
- [ ] Document Hornresp file format (.inp, .txt)
- [ ] Understand parameter naming conventions
- [ ] Test importing known horn files

4.2 **Export Module**
- [ ] Implement `hornresp/export.py`
- [ ] Function: `export_to_hornresp(horn_params, driver_params, filename)`
- [ ] Map viberesp parameters to Hornresp format
- [ ] Include metadata (driver name, date, viberesp version)

4.3 **Import Function**
- [ ] Implement `hornresp/import.py`
- [ ] Parse Hornresp files into viberesp data structures
- [ ] Validate imported parameters

4.4 **CLI Commands**
- [ ] `viberesp export <design>` - Export to Hornresp format
- [ ] `viberesp import <hornresp_file>` - Import from Hornresp

**Deliverables:**
- `hornresp/export.py` - Export functionality
- `hornresp/import.py` - Import functionality
- Test cases with known Hornresp files
- CLI commands for import/export

---

## Phase 5: Validation Framework

**Status:** Pending
**Goal:** Automated validation against Hornresp

### Tasks

5.1 **Reference Data Collection**
- [ ] Create test cases covering:
  - Various horn lengths (0.5m, 1m, 2m, 5m)
  - Various flare constants (small, medium, large)
  - Exponential and hyperbolic profiles
  - Frequency ranges from below cutoff to well above
- [ ] Run Hornresp for all test cases
- [ ] Store results in `tests/validation_data/`

5.2 **Comparison Functions**
- [ ] Implement `validation/compare.py`
- [ ] Compare impedance curves (magnitude and phase)
- [ ] Compare frequency response (dB vs frequency)
- [ ] Calculate error metrics:
  - Relative error at each frequency
  - RMS error over frequency range
  - Maximum error
- [ ] Generate comparison plots

5.3 **Automated Validation Tests**
- [ ] pytest fixtures for loading reference data
- [ ] Parametrized tests for multiple configurations
- [ ] Pass/fail criteria based on tolerances from `CLAUDE.md`

5.4 **Reporting**
- [ ] HTML validation reports
- [ ] Side-by-side plots (viberesp vs Hornresp)
- [ ] Error analysis tables
- [ ] CI integration (GitHub Actions)

**Deliverables:**
- `validation/compare.py` - Comparison functions
- `tests/validation/` - Automated validation tests
- Validation report templates
- CI workflow for continuous validation

---

## Phase 6: CLI User Interface & Workflow

**Status:** Pending
**Goal:** Complete CLI for interactive horn design

### Tasks

6.1 **Design Commands**
- [ ] `viberesp design new` - Start new design
  - Prompt for driver selection
  - Prompt for horn type (exponential, hyperbolic, conical)
  - Interactive parameter entry
- [ ] `viberesp design show <name>` - Display design details
- [ ] `viberesp design list` - List saved designs
- [ ] `viberesp design delete <name>` - Delete design

6.2 **Simulation Commands**
- [ ] `viberesp simulate <design>` - Run simulation
  - Calculate frequency response
  - Calculate impedance
  - Generate plots
- [ ] `viberesp simulate --frequency-range <fmin> <fmax>`
- [ ] `viberesp simulate --output <format>` (csv, json, plot)

6.3 **Visualization**
- [ ] Frequency response plot (dB vs Hz)
- [ ] Impedance plot (ohms vs Hz)
- [ ] Horn profile visualization (cross-section)
- [ ] Directivity polar plots
- [ ] Interactive plots (matplotlib with interactive backend)

6.4 **Analysis Tools**
- [ ] `viberesp analyze cutoff` - Show cutoff frequency
- [ ] `viberesp analyze efficiency` - Calculate efficiency
- [ ] `viberesp analyze directivity` - Show directivity index
- [ ] `viberesp analyze impedance` - Throat impedance vs frequency

6.5 **Configuration**
- [ ] Configuration file: `~/.viberesp/config.yaml`
- [ ] Default parameters (temperature, air density)
- [ ] Plotting preferences (colors, figure size)
- [ ] Simulation tolerances

**Deliverables:**
- Complete `cli.py` with all commands
- Design storage (JSON format in `~/.viberesp/designs/`)
- Plotting utilities
- Configuration management

---

## Phase 7: Optimization & Exploration Tools

**Status:** Pending
**Goal:** Automated parameter optimization and design exploration

### Tasks

7.1 **Parameter Sweep**
- [ ] `viberesp sweep parameter <name> --range <min> <max> --steps <n>`
- [ ] Sweep one parameter while holding others constant
- [ ] Generate results showing effect on:
  - Cutoff frequency
  - Efficiency
  - Frequency response
  - Impedance
- [ ] Plot sweep results

7.2 **Multi-Objective Optimization**
- [ ] Integration with pymoo (already in dependencies)
- [ ] Define optimization objectives:
  - Minimize cutoff frequency
  - Maximize efficiency
  - Minimize horn size (volume)
  - Maximize bandwidth
- [ ] Constraints:
  - Maximum horn length
  - Maximum mouth size
  - Minimum throat size (driver compatibility)
- [ ] `viberesp optimize <design> --objectives <obj1,obj2,...>`

7.3 **Pareto Front Analysis**
- [ ] Generate Pareto front for competing objectives
- [ ] Interactive exploration of Pareto-optimal designs
- [ ] Export trade-off analysis

7.4 **Design Space Exploration**
- [ ] Monte Carlo sampling of parameter space
- [ ] Sensitivity analysis (which parameters affect performance most)
- [ ] Design feasibility maps

7.5 **Validation of Optimized Designs**
- [ ] Automatically validate optimized designs against Hornresp
- [ ] Warn if optimization results violate assumptions
- [ ] Track validation statistics across optimization runs

**Deliverables:**
- `optimization/` module with sweep and optimization functions
- Optimization objective functions (with literature citations)
- Pareto front visualization
- Design exploration reports

---

## Future Enhancements (Beyond Phase 7)

These are not currently planned but may be considered later:

### Additional Enclosure Types
- [ ] Transmission line enclosures
- [ ] Sealed (acoustic suspension) boxes
- [ ] Ported (bass reflex) enclosures
- [ ] Bandpass enclosures

### Advanced Horn Features
- [ ] Folded horns (folding geometry)
- [ ] Multi-segment horns (different profiles in sections)
- [ ] Rear-loaded horns (open-back driver + front horn)
- [ ] Unity horn / synergy horn designs

### Driver Modeling
- [ ] Large-signal parameters (Bl(x), Cms(x))
- [ ] Nonlinear distortion prediction
- [ ] Thermal modeling (power compression)

### Visualization
- [ ] 3D horn geometry rendering
- [ ] Interactive parameter adjustment with real-time plots
- [ ] Directivity balloon plots

### Integration
- [ ] Web interface (Flask/Django)
- [ ] CAD export (STL for 3D printing)
- [ ] Integration with measurement tools (Clio, ARTA)

---

## Contribution Guidelines

We welcome contributions! Please ensure:

1. **All simulation code cites literature** per `CLAUDE.md`
2. **New features are validated against Hornresp** where applicable
3. **Tests are included** for new functionality
4. **Documentation is updated** (README, ROADMAP, docstrings)
5. **Code follows style guidelines** (black, isort, mypy passing)

## Timeline Estimates

These are rough order-of-magnitude estimates for planning purposes:

- Phase 1: ✅ Complete
- Phase 2: 1-2 weeks (driver input system)
- Phase 3: 3-4 weeks (simulation engine - core of the project)
- Phase 4: 1 week (Hornresp import/export)
- Phase 5: 2-3 weeks (validation framework)
- Phase 6: 2 weeks (CLI polish and visualization)
- Phase 7: 3-4 weeks (optimization and exploration)

**Total to MVP:** ~3-4 months

---

## Success Criteria

The project is considered a success when:

1. ✅ All simulation algorithms cite literature
2. ⏳ All core horn types implemented (exponential, hyperbolic, conical)
3. ⏳ Validation against Hornresp shows <1% agreement for well-behaved cases
4. ⏳ CLI provides complete workflow (driver → simulate → export → validate)
5. ⏳ Optimization tools can explore design space efficiently
6. ⏳ Documentation is comprehensive and accessible

---

*Last updated: 2025-12-25*
