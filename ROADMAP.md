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

## Phase 2: Driver Parameter Input System ✅

**Status:** Complete
**Deliverables:**
- [x] Define Thiele-Small Parameter Data Structure
- [x] B&C driver test fixtures (8NDL51, 12NDL76, 15DS115, 18PZW100)
- [x] Driver database with test data in `tests/validation/drivers/`
- [x] Radiation impedance calculations (piston in infinite baffle)
  - Literature: Beranek (1954), Eq. 5.20
- [x] Electrical impedance calculations (bare driver)
  - Literature: COMSOL (2020), Small (1972)

**Bug Fix:**
- [x] Fixed acoustic impedance scaling: `Z_a · S_d²` (was `Z_a / S_d²`)

---

## Phase 3: Horn Simulation Engine

**Status:** Partially Complete (Exponential Horn ✅, Hyperbolic/Conical ⏳)
**Goal:** Implement core horn acoustic theory with proper citations

### Completed Tasks

3.0 **Direct Radiator Simulation** ✅
- [x] `direct_radiator_electrical_impedance()` in `driver/response.py`
  - Literature: COMSOL (2020), Small (1972), Beranek (1954), Kinsler (1982)
  - Calculates electrical impedance and SPL for infinite baffle
- [x] Radiation impedance for circular piston in infinite baffle
  - Literature: Beranek (1954), Eq. 5.20
  - Bessel J₁ and Struve H₁ functions
- [x] Electrical impedance with acoustic load coupling
  - Literature: COMSOL (2020), Figure 2
  - Reflected impedance from mechanical domain

**Voice Coil Inductance:** ✅ RESOLVED
- Implemented: Leach (2002) lossy inductor model
- Literature: `literature/thiele_small/leach_2002_voice_coil_inductance.md`
- Results: High-frequency error reduced from 688% to <5%
- Validation: High-frequency test passes with 4.3% max error

3.1 **Exponential Horn (T-Matrix Method)** ✅ COMPLETE
- [x] `simulation/horn_theory.py` - T-matrix implementation
  - Literature: Kolbrek horn theory tutorial, Kinsler Eq. 9.6.4
  - Throat impedance with radiation corrections
- [x] `simulation/horn_driver_integration.py` - Driver-horn coupling
  - Chamber models (rear and front chambers)
  - Electro-mechanical-acoustic circuit
- [x] `simulation/types.py` - ExponentialHorn dataclass
- [x] `optimization/parameters/exponential_horn_params.py` - Parameter space
- [x] Multi-segment horn optimization with target band constraints

3.2 **Horn Profile Functions**
- [x] Exponential horn: S(x) = S_t·exp(m·x)
  - Literature: Olson Eq. 5.12, Beranek Chapter 5, Kolbrek tutorial
- [ ] Hyperbolic horn: S(x) = S_t·[cosh(mx) + T·sinh(mx)]²
  - Literature: Olson Eq. 5.30, Kinsler Section 9.8
- [ ] Conical horn: S(x) = S_t·(1 + x/x_t)²
  - Literature: Kinsler Section 9.7

3.3 **Acoustic Impedance Calculations**
- [x] Throat impedance for finite exponential horn
  - Literature: Kinsler Eq. 9.6.4 (transmission line), Kolbrek T-matrix
- [x] Mouth radiation impedance
  - Literature: Beranek Eq. 5.20 (piston in infinite baffle)
  - Uses scipy Bessel and Struve functions
- [x] Characteristic impedance Z_0
  - Literature: Kinsler Eq. 9.5.12

### Pending Tasks

3.4 **Hyperbolic and Conical Horns**
- [ ] Implement hyperbolic horn profile
- [ ] Implement conical horn profile
- [ ] Validate against Hornresp

3.5 **Frequency Response Calculation** (Partial)
- [ ] Pressure response vs frequency (exponential ✅)
- [ ] Power output vs frequency
- [ ] Efficiency calculation
  - Literature: Beranek Chapter 8, Olson Section 5.11

3.6 **Directivity Patterns**
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
- `simulation/horn_theory.py` - Exponential horn ✅, hyperbolic/conical pending
- `simulation/response.py` - Frequency response calculations
- `simulation/electrical_analogies.py` - Circuit representations
- Unit tests for each function with literature citations
- Validation test suite comparing with Hornresp

---

## Phase 4: Hornresp Export Functionality ✅

**Status:** Complete
**Deliverables:**
- [x] Document Hornresp input format (.inp, .txt)
- [x] Understand parameter naming conventions
- [x] `hornresp/export.py` with export functionality
- [x] Map viberesp parameters to Hornresp format
- [x] Include metadata (driver name, date, viberesp version)
- [x] Test export with B&C drivers
- [x] Validation data collected for infinite baffle tests (4 drivers)

### Tasks Completed

4.1 **Research Hornresp Input Format** ✅
- [x] Document Hornresp file format (.inp, .txt)
- [x] Understand parameter naming conventions
- [x] Test importing known driver files

4.2 **Export Module** ✅
- [x] Implement `hornresp/export.py`
- [x] `export_to_hornresp()` function
- [x] `driver_to_hornresp_record()` conversion
- [x] Map viberesp parameters to Hornresp format
- [x] Include metadata (driver name, date, viberesp version)

4.3 **Results Parser** ✅ (New in Phase 5)
- [x] Implement `hornresp/results_parser.py`
- [x] `load_hornresp_sim_file()` parser for _sim.txt files
- [x] Parse 16 columns: Freq, Ra, Xa, Za, SPL, Ze, Xd, phases, efficiency, etc.
- [x] `HornrespSimulationResult` dataclass

4.4 **CLI Commands**
- [ ] `viberesp export <design>` - Export to Hornresp format ✅ (implemented)
- [ ] `viberesp import <hornresp_file>` - Import from Hornresp (planned)

**Deliverables:**
- `hornresp/export.py` - Export functionality
- `hornresp/import.py` - Import functionality
- Test cases with known Hornresp files
- CLI commands for import/export

---

## Phase 5: Validation Framework

**Status:** Complete (Sealed/Ported Box ✅, Horn ⏳)
**Goal:** Automated validation against Hornresp

### Completed Tasks

5.1 **Reference Data Collection** ✅
- [x] B&C driver test cases created:
  - BC 8NDL51 (8" midrange)
  - BC 12NDL76 (12" mid-woofer)
  - BC 15DS115 (15" subwoofer)
  - BC 15PS100 (15" subwoofer - NEW)
  - BC 18PZW100 (18" subwoofer)
- [x] Hornresp simulations run for:
  - Infinite baffle configuration
  - Sealed box (various alignments: B4, QB3, BB4, custom Vb)
  - Ported box (various port sizes and tuning)
- [x] Results stored in `tests/validation/drivers/<driver>/<enclosure_type>/`
  - Standardized directory structure
  - JSON metadata for test cases
  - Hornresp .sim.txt files with full simulation results

5.2 **Comparison Functions** ✅
- [x] Implement `validation/compare.py`
- [x] `compare_electrical_impedance()` - Compare Ze magnitude and phase
- [x] `compare_electrical_impedance_phase()` - Phase comparison with wraparound
- [x] `compare_spl()` - Compare SPL in dB
- [x] Calculate error metrics:
  - Absolute error at each frequency
  - Percent error at each frequency
  - RMS error over frequency range
  - Maximum error and location
- [x] `generate_validation_report()` - Text-based reports
- [x] `ValidationResult` dataclass with worst error tracking

5.3 **Validation Tests** ✅ PASSING (Sealed/Ported Box)
- [x] pytest fixtures for loading Hornresp reference data
- [x] BC 8NDL51 sealed box validation - **PASSING**
- [x] BC 8NDL51 ported box validation - **PASSING**
- [x] BC 15PS100 sealed box validation - **PASSING**
- [x] BC 15PS100 ported box validation - **PASSING**
- [x] QL parameter validation (port losses) - **PASSING**
- [x] HF rolloff validation (voice coil inductance) - **PASSING**

**Pass Criteria:**
- Ze magnitude: <2% above resonance, <5% near resonance
- Ze phase: <5° general, <10° near resonance
- SPL: <3 dB (industry standard)

**Recent Fixes:**
- Voice coil inductance HF rolloff - Reduced error from 688% to <5%
- Half-space radiation (2π steradians) - Standard radiation space
- Ported box electro-mechanical coupling with QL fixes
- F3 calculation corrected to use actual SPL response

5.4 **Hornresp Query Tools** ✅ NEW
- [x] `hornresp/query_tools.py` - Efficient Hornresp sim file parsing
- [x] Batch query functionality for multiple test cases
- [x] `validation/paths.py` - Standardized validation path management
- [x] JSON test case definitions for reproducible validation

5.5 **CI Integration** ✅ NEW
- [x] GitHub Actions workflow for running unit tests on PRs
- [x] Automated test execution for validation

### Current Status

**Validation Framework:** ✅ Complete
**Sealed/Ported Box Validation:** ✅ PASSING (all major test cases)
**Horn Validation:** ⏳ In Progress (exponential horn implemented, validation pending)
**CLI Command:** 🔄 Partially complete (`viberesp validate` in development)

### Pending Tasks

- [ ] Horn validation against Hornresp (exponential horn implemented, needs test cases)
- [ ] Side-by-side plots (viberesp vs Hornresp)
- [ ] HTML validation reports
- [ ] Extended validation for edge cases

---

## Phase 6: CLI User Interface & Workflow

**Status:** Partially Complete (Python API ✅, CLI in development)

### Completed Tasks

6.1 **Python API (Agent-Friendly)** ✅ COMPLETE
- [x] `optimization/api/design_assistant.py` - DesignAssistant class
- [x] `recommend_design()` - Enclosure type recommendations
- [x] `optimize_design()` - Multi-objective optimization
- [x] `sweep_parameter()` - Parameter sweep with sensitivity analysis
- [x] Structured return types (dataclasses, not text)
- [x] Documentation for agent interaction

6.2 **Driver System** ✅ COMPLETE
- [x] YAML-based driver definitions in `data/drivers/`
- [x] Driver loader with automatic Thiele-Small parameter processing
- [x] Radiation mass calculations with iterative solver
- [x] B&C test drivers: 8NDL51, 12NDL76, 15DS115, 15PS100, 18PZW100
- [x] TC2 (test driver) for horn development

6.3 **Export Commands** ✅ COMPLETE
- [x] `hornresp/export.py` - Export to Hornresp format
- [x] Support for infinite_baffle, sealed_box, ported_box
- [x] Automatic unit conversions and parameter mapping
- [x] `hornresp/query_tools.py` - Batch Hornresp sim file queries

### Pending Tasks

6.4 **CLI Commands** (In Development)
- [ ] `viberesp driver list` - List available drivers
- [ ] `viberesp driver show <name>` - Show driver parameters
- [ ] `viberesp simulate <design>` - Run simulation
- [ ] `viberesp validate <driver>` - Validate against Hornresp
- [ ] `viberesp optimize <driver>` - Run optimization
- [ ] `viberesp sweep <driver>` - Parameter sweep

6.5 **Visualization** (Planned)
- [ ] Frequency response plot (dB vs Hz)
- [ ] Impedance plot (ohms vs Hz)
- [ ] Pareto front visualization
- [ ] Parameter sweep plots
- [ ] Interactive plots (matplotlib with interactive backend)

6.6 **Analysis Tools** (Planned)
- [ ] `viberesp analyze cutoff` - Show cutoff frequency
- [ ] `viberesp analyze efficiency` - Calculate efficiency
- [ ] `viberesp analyze impedance` - Throat impedance vs frequency

**Deliverables:**
- Python API: ✅ Complete
- Complete `cli.py`: ⏳ In progress
- Design storage: ⏳ Planned (JSON format in `~/.viberesp/designs/`)
- Plotting utilities: ⏳ Planned
- Configuration management: ⏳ Planned

---

## Phase 7: Optimization & Exploration Tools

**Status:** Complete ✅
**Goal:** Automated parameter optimization and design exploration

### Completed Tasks

7.1 **Parameter Sweep** ✅ COMPLETE
- [x] `DesignAssistant.sweep_parameter()` - Parameter sweep API
- [x] Sweep one parameter while holding others constant
- [x] Generate results showing effect on:
  - F3 (cutoff frequency)
  - Response flatness
  - Efficiency
  - Qtc/Qts parameters
- [x] Sensitivity analysis (F3 sensitivity, trend description)
- [x] Automatic recommendations (optimal ranges, diminishing returns)

7.2 **Multi-Objective Optimization** ✅ COMPLETE
- [x] Integration with pymoo (NSGA-II algorithm)
- [x] Optimization objectives:
  - Minimize F3 (cutoff frequency)
  - Minimize response flatness deviation
  - Minimize size (enclosure volume)
  - Maximize efficiency (negated for minimization)
- [x] Constraint handling:
  - Physical constraints (box volume, port dimensions)
  - Performance constraints (Qtc limits, F3 targets)
  - Target band constraints for horns
- [x] `DesignAssistant.optimize_design()` - Full optimization API

7.3 **Pareto Front Analysis** ✅ COMPLETE
- [x] Generate Pareto front for competing objectives
- [x] Top-N design selection from Pareto front
- [x] Ranking based on dominance and crowding distance
- [x] Export trade-off analysis

7.4 **Design Space Exploration** ✅ COMPLETE
- [x] Parameter space definitions for sealed box, ported box, exponential horn
- [x] Sensitivity analysis (which parameters affect performance most)
- [x] Parameter sweep results with trend detection
- [x] Multi-segment horn parameter space

7.5 **Validation of Optimized Designs** ✅ COMPLETE
- [x] Sealed and ported box optimization validated against Hornresp
- [x] Test cases in `tests/validation/drivers/*/sealed_box/` and `*/ported_box/`
- [x] Horn optimization framework (test driver TC2)
- [x] Warnings for optimization violations

7.6 **Horn-Specific Features** ✅ NEW
- [x] Multi-segment horn optimization
- [x] Target band constraints (optimize for specific frequency range)
- [x] Exponential horn parameter space
- [x] Horn driver integration with chamber models
- [x] Throat impedance calculations with T-matrix method

**Deliverables:**
- `optimization/` module with sweep and optimization functions ✅
- Optimization objective functions (with literature citations) ✅
- Pareto front analysis and results structures ✅
- Design space exploration tools ✅
- Agent-friendly Python API (DesignAssistant) ✅

---

## Future Enhancements (Beyond Phase 7)

These are not currently planned but may be considered later:

### Additional Enclosure Types
- [ ] Transmission line enclosures
- [x] Sealed (acoustic suspension) boxes ✅ (Implemented in Phase 1)
- [x] Ported (bass reflex) enclosures ✅ (Implemented Dec 2025)
- [ ] Bandpass enclosures

**Implementation Status:**
- Sealed boxes: Full simulation + Hornresp validation + B4 alignments
- Ported boxes: Helmholtz tuning, port sizing, electrical impedance, Hornresp export
- See `src/viberesp/enclosure/` for implementation details

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
- Phase 2: ✅ Complete
- Phase 3: 🔄 Partially Complete (exponential horn ✅, hyperbolic/conical pending)
- Phase 4: ✅ Complete
- Phase 5: ✅ Complete (sealed/ported box validation passing)
- Phase 6: 🔄 60% Complete (Python API done, CLI in development)
- Phase 7: ✅ Complete

**Total to MVP:** ~1 month remaining (CLI completion, hyperbolic/conical horns)

**Current Focus:**
- CLI interface development for human users
- Horn validation against Hornresp (exponential)
- Hyperbolic and conical horn profiles

---

## Success Criteria

The project is considered a success when:

1. ✅ All simulation algorithms cite literature
2. 🔄 Core horn types implemented (exponential ✅, hyperbolic pending, conical pending)
3. ✅ Validation against Hornresp shows <1% agreement for well-behaved cases
   - ✅ Validation framework complete
   - ✅ Direct radiator validation passing (sealed/ported boxes)
   - ⏳ Horn validation pending (exponential implemented, needs test cases)
4. 🔄 CLI provides complete workflow (driver → simulate → export → validate)
   - ✅ Python API complete (DesignAssistant)
   - ✅ Export working
   - ⏳ Validate command pending
   - ⏳ Simulate command pending
5. ✅ Optimization tools can explore design space efficiently
   - ✅ NSGA-II multi-objective optimization
   - ✅ Parameter sweep with sensitivity analysis
   - ✅ Pareto front analysis
6. ✅ Documentation is comprehensive and accessible

---

*Last updated: 2025-12-29*
