# Viberesp Project-Specific Instructions

This file contains project-specific instructions for Claude Code when working on the viberesp codebase.

## Project Overview

Viberesp is a CLI tool for loudspeaker enclosure design and simulation, with initial focus on **horn-loaded enclosures**. The simulation engine implements acoustic theory from first principles and validates results against Hornresp (the industry-standard horn simulation tool).

**Key workflow:**
1. Import driver parameters (manual entry via CLI)
2. Explore enclosure types and variables
3. Export to Hornresp for validation
4. Iterate based on validation results

## CRITICAL: Literature Citation Requirements

### ALL Simulation Code MUST Cite Literature

**This is the most important rule in this project:**

Every function in the `src/viberesp/simulation/` module that implements acoustic theory **MUST** cite the literature it implements.

### Citation Format

Every simulation function must include:

1. **Docstring with literature citations** - Reference specific literature files and equation numbers
2. **Inline comments** - Link to specific equations from the literature
3. **Validation requirements** - State how the implementation will be validated against Hornresp

#### Example - Correct Citation Format

```python
def calculate_horn_cutoff(flare_constant: float, speed_of_sound: float = 343.0) -> float:
    """
    Calculate the cutoff frequency of an exponential horn.

    The cutoff frequency is the frequency below which the horn acts as a
    high-pass filter and does not efficiently propagate sound waves.

    Based on Olson (1947), Equation 5.18 and Beranek (1954), Chapter 5.
    Both sources derive the same expression from the horn equation.

    Literature:
    - literature/horns/olson_1947.md - Exponential horn theory, Eq. 5.18
    - literature/horns/beranek_1954.md - Horn impedance, Chapter 5
    - literature/horns/kinsler_1982.md - Derivation from wave equation

    Args:
        flare_constant: Horn flare constant m (1/m), where S(x) = S_t · exp(m·x)
        speed_of_sound: Speed of sound in air (m/s), default 343 m/s at 20°C

    Returns:
        Cutoff frequency f_c (Hz), below which the horn does not propagate efficiently

    Validation:
        Compare with Hornresp's cutoff frequency calculation for identical
        flare constant. Expected agreement: <0.1% deviation.

    Examples:
        >>> calculate_horn_cutoff(flare_constant=4.6)
        250.0  # Hz (for m=4.6, c=343)
    """
    # Olson (1947), Eq. 5.18: f_c = c·m/(2π)
    # Beranek (1954), Chapter 5: Same expression derived from horn equation
    return (speed_of_sound * flare_constant) / (2 * math.pi)
```

### What Requires Citations

**MUST cite literature:**
- All acoustic impedance calculations
- Horn profile equations (exponential, hyperbolic, conical)
- Frequency response calculations
- Directivity patterns
- Throat/mouth impedance transformations
- Cutoff frequency formulas
- Efficiency calculations
- Power handling estimates

**Does NOT require citations:**
- CLI interface code (click commands, prompts)
- File I/O operations
- Data validation
- Testing infrastructure
- Plotting/visualization code
- Configuration management

### Code Review Criteria

When reviewing simulation code, check:

1. [ ] Does the function have a docstring?
2. [ ] Does the docstring include a "Literature:" section?
3. [ ] Are specific literature files referenced?
4. [ ] Are equation numbers cited (e.g., "Olson Eq. 5.18")?
5. [ ] Do inline comments reference the literature?
6. [ ] Is there a validation section describing how to verify against Hornresp?
7. [ ] Does the implementation match the cited equations?

**Pull requests without proper citations will be rejected.**

## Development Workflow

### Literature-First Development

When implementing a new simulation feature:

1. **Start with literature/** - Read the relevant reference files
2. **Identify the equations** - Find the specific equations to implement
3. **Write the docstring first** - Include full citations before coding
4. **Implement the equations** - Translate math to code
5. **Validate against Hornresp** - Create test cases comparing results
6. **Document any discrepancies** - Explain any deviations from reference

### Validation Against Hornresp

Every simulation algorithm must be validated against Hornresp:

1. Create test cases with known horn parameters
2. Run viberesp simulation
3. Run Hornresp with identical parameters
4. Compare results (impedance, frequency response, etc.)
5. Document agreement percentage
6. Investigate and explain any discrepancies >1%

Acceptable tolerances:
- Well above cutoff (f > 2·f_c): <1% deviation
- Near cutoff (f ≈ 1.2·f_c to 2·f_c): <2% deviation
- Close to cutoff (f ≈ f_c): <5% deviation (numerical sensitivity)
- Below cutoff (f < f_c): qualitative agreement only

## Code Structure Conventions

### Directory Organization

```
src/viberesp/
├── cli.py                   # CLI entry point (click commands)
├── driver/                  # Driver parameter handling
│   └── parameters.py        # Thiele-Small parameter data structures
├── simulation/              # SIMULATION CODE MUST CITE LITERATURE
│   ├── horn_theory.py       # Horn acoustic models (cite literature/horns/)
│   ├── electrical_analogies.py  # Circuit representations
│   └── response.py          # Frequency response calculation
├── hornresp/                # Hornresp integration
│   └── export.py            # Export to Hornresp format
└── validation/              # Validation framework
    └── compare.py           # Compare viberesp vs Hornresp results
```

### Import Conventions

- Use absolute imports: `from viberesp.simulation import horn_theory`
- Keep simulation modules independent of CLI code
- Validation code should import both simulation and hornresp modules

### Naming Conventions

- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Module names: `snake_case`

For physics functions, use descriptive names:
- `calculate_horn_impedance()` (not `calc_z()`)
- `exponential_horn_area()` (not `exp_area()`)
- `cutoff_frequency()` (not `fc()`)

## Testing Requirements

### Unit Tests

All simulation functions must have unit tests:

```python
def test_calculate_horn_cutoff():
    """Test cutoff frequency calculation against Olson Eq. 5.18"""
    # Test case from Olson (1947), Section 5.6
    m = 4.6  # flare constant (1/m)
    c = 343.0  # speed of sound (m/s)
    fc_expected = 250.0  # Hz

    fc_calculated = calculate_horn_cutoff(m, c)

    assert abs(fc_calculated - fc_expected) < 0.1  # <0.1% tolerance
```

### Validation Tests

Create validation tests comparing with Hornresp:

```python
def test_exponential_horn_vs_hornresp():
    """Validate exponential horn impedance against Hornresp"""
    # Define horn parameters
    horn_params = ExponentialHorn(
        throat_area=0.001,  # m²
        mouth_area=0.1,     # m²
        length=1.5,         # m
    )

    # Calculate impedance with viberesp
    z_viberesp = calculate_throat_impedance(horn_params, frequency=500)

    # Load Hornresp reference data
    z_hornresp = load_hornresp_reference("test_data/exp_horn_001.csv")

    # Compare
    assert abs(z_viberesp - z_hornresp) / z_hornresp < 0.01  # <1% deviation
```

### Test Data Organization

Store Hornresp reference data in `tests/validation_data/`:

```
tests/validation_data/
├── exponential_horns/
│   ├── exp_horn_001.csv     # Frequency, impedance, phase from Hornresp
│   ├── exp_horn_002.csv
│   └── ...
└── hyperbolic_horns/
    └── ...
```

## Documentation Standards

### Docstring Format

Use Google-style docstrings with extensions:

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of what the function does.

    Longer description explaining the physics and theory if needed.
    Mention any assumptions or limitations.

    Based on Author (Year), Equation X.Y and possibly other sources.

    Literature:
    - literature/path/to/reference1.md - Description of what's used
    - literature/path/to/reference2.md - Additional relevant info

    Args:
        param1: Description with units (e.g., meters, Hz)
        param2: Description with units

    Returns:
        Description of return value with units

    Raises:
        ValueError: Description of when error occurs

    Validation:
        How to validate against Hornresp, expected tolerance

    Examples:
        >>> function_name(1.0, 2.0)
        42.0
    """
```

### Physical Constants

Define constants with citations:

```python
# Standard conditions at 20°C, 1 atm
# From Kinsler et al. (1982), Chapter 1
SPEED_OF_SOUND = 343.0  # m/s
AIR_DENSITY = 1.18  # kg/m³
```

## Optimization and Exploration

### Future Features (Roadmap Phases 6-7)

When implementing optimization and parameter exploration:

1. Maintain citation requirements for all simulation code
2. Optimization algorithms (pymoo) don't need citations, but objective functions do
3. Document which literature provides the optimization criteria (e.g., "maximize efficiency at 80 Hz per Beranek Chapter 8")

### Parameter Sweep Conventions

When exploring parameter space:

- Store results with full parameter metadata
- Include literature citations for each calculation
- Validate spot checks against Hornresp
- Warn if parameters violate assumptions from literature (e.g., horn too short for cutoff frequency)

## Common Pitfalls

### Units

**Always include units in documentation and variable names:**
- `area_m2` not `area`
- `length_m` not `length`
- `frequency_hz` not `frequency`

### Reference Frame

Clarify coordinate system:
- `x = 0` at throat or mouth? (Convention: x=0 at throat)
- Positive x direction toward mouth

### Frequency Range

Document valid frequency ranges:
- Exponential horn theory valid for f > f_c
- Below cutoff, results are qualitative (evanescent waves)
- Very high frequencies may need directivity corrections

### Finite vs Infinite Horns

Be explicit about which model you're implementing:
- Infinite horn: Olson (1947) analytical solutions
- Finite horn: Beranek (1954) with mouth corrections, Kinsler (1982) transmission line approach

## When in Doubt

1. **Read the literature** - Check `literature/horns/` for relevant equations
2. **Cite your sources** - Even if uncertain, cite the literature you're using
3. **Validate against Hornresp** - When viberesp and Hornresp disagree, investigate why
4. **Ask for clarification** - It's better to ask than to implement without citations

## Resources

- `literature/README.md` - Overview of citation system
- `ROADMAP.md` - Development phases
- Hornresp manual: http://www.hornresp.net/
- Olson (1947) - Classic horn theory
- Beranek (1954) - Finite horn corrections
- Kinsler (1982) - Rigorous derivations

---

**Remember: The goal is to create a simulation tool grounded in established acoustic theory, with every algorithm traceable to the literature. This is what makes viberesp trustworthy and useful for horn design.**
