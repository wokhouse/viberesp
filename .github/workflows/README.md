# GitHub Actions CI/CD

This directory contains continuous integration workflows for Viberesp.

## Workflows

### CI Workflow (`.github/workflows/ci.yml`)

The main CI pipeline runs on all pushes and pull requests to `main`, `develop`, and `feature/*` branches.

#### Jobs

**1. Test** (Multi-version)
- Runs tests on Python 3.9, 3.10, and 3.11
- Executes `tests/physics/` test suite
- Generates coverage reports
- Uploads coverage to Codecov (Python 3.11 only)

**2. Lint**
- Checks code formatting with `black`
- Checks import sorting with `isort`
- Runs type checking with `mypy` on physics module

**3. Type Check**
- Runs full type checking on `src/viberesp/`
- Catches type errors across the entire codebase

**4. Validate Theoretical**
- Validates Phase 1 radiation impedance implementation
- Runs all 4 TC-P1-RAD test cases
- Verifies behavioral physics (mass-controlled, radiation-controlled regimes)
- Ensures <0.01% error vs Kolbrek theoretical formulas

**5. Coverage Check**
- Enforces minimum 90% code coverage
- Generates coverage summary with missing lines

#### Status Badges

Add these badges to your README:

```markdown
![CI](https://github.com/wokhouse/viberesp/workflows/CI/badge.svg)
![codecov](https://codecov.io/gh/wokhouse/viberesp/branch/main/graph/badge.svg)
```

## Testing Paradigm

### Physics-Based Validation

Viberesp uses a **literature-cited, physics-first** testing approach:

1. **Theoretical Validation**
   - All implementations validated against peer-reviewed formulas
   - Primary: Kolbrek (2019) Part 1 for radiation impedance
   - Tolerance: <0.01% error

2. **Behavioral Validation**
   - Verify correct physics behavior across parameter ranges
   - Example: Low frequency → mass-controlled (X dominates)
   - Example: High frequency → radiation-controlled (R→1, X→0)

3. **Hornresp Comparison**
   - Secondary validation against Hornresp reference data
   - Documents normalization differences
   - Does NOT expect exact match (different definitions)

### Test Structure

```
tests/
├── physics/
│   ├── test_radiation.py          # 25 tests, 100% coverage
│   └── fixtures/
│       ├── tc_p1_rad_01_data.py   # Low frequency (ka=0.18)
│       ├── tc_p1_rad_02_data.py   # Transition (ka≈1)
│       ├── tc_p1_rad_03_data.py   # High frequency (ka>>1)
│       └── tc_p1_rad_04_data.py   # Small piston (50 cm²)
├── test_enclosures/               # (Future: enclosure tests)
├── test_io/                       # (Future: I/O tests)
├── test_optimization/             # (Future: optimization tests)
└── test_simulation/               # (Future: simulation tests)
```

## Code Quality Standards

### Formatting

- **Tool:** `black`
- **Line length:** 100 characters
- **Target versions:** Python 3.9, 3.10, 3.11

Check locally:
```bash
black --check src/viberesp/ tests/
```

Auto-format:
```bash
black src/viberesp/ tests/
```

### Import Sorting

- **Tool:** `isort`
- **Profile:** black
- **Line length:** 100 characters

Check locally:
```bash
isort --check-only src/viberesp/ tests/
```

Auto-sort:
```bash
isort src/viberesp/ tests/
```

### Type Checking

- **Tool:** `mypy`
- **Python version:** 3.9 (minimum)
- **Plugins:** pydantic.mypy

Check locally:
```bash
mypy src/viberesp/
```

### Testing

- **Tool:** `pytest`
- **Coverage:** `pytest-cov`
- **Minimum coverage:** 90%

Run tests locally:
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/viberesp --cov-report=term-missing

# Run specific test class
pytest tests/physics/test_radiation.py::TestTC_P1_RAD_01 -v

# Run specific test
pytest tests/physics/test_radiation.py::TestTC_P1_RAD_01::test_tc_p1_rad_01_theoretical -v
```

## Adding New Tests

When adding new physics features:

1. **Create test fixture** in `tests/physics/fixtures/`
   ```python
   TC_P1_RAD_XX = {
       "name": "Descriptive name",
       "parameters": {...},
       "theoretical": {...},
       "validation": {...}
   }
   ```

2. **Add test class** in `tests/physics/test_*.py`
   ```python
   class TestTC_P1_RAD_XX(TestCase):
       def test_tc_p1_rad_xx_theoretical(self):
           # Validate against formulas
       def test_tc_p1_rad_xx_behavior(self):
           # Validate physics behavior
   ```

3. **Update CI workflow** if needed
   - Add new validation job if testing new parameter regime
   - Update coverage thresholds if expanding module

4. **Document in test fixture**
   - Include literature citations
   - Reference specific equations
   - Document expected behavior

## Local Development

### Pre-commit Hook (Recommended)

Install pre-commit hooks to automatically run checks before pushing:

```bash
pip install pre-commit
pre-commit install
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

### Running CI Locally

Test what CI will run:

```bash
# Format check
black --check src/viberesp/ tests/
isort --check-only src/viberesp/ tests/

# Type check
mypy src/viberesp/

# Tests with coverage
pytest tests/physics/ --cov=src/viberesp/physics --cov-fail-under=90
```

## Troubleshooting

### CI Fails on Black/Isort

**Issue:** Code formatting check fails
**Fix:** Run locally and commit changes:
```bash
black src/viberesp/ tests/
isort src/viberesp/ tests/
git add .
git commit -m "Fix formatting"
```

### CI Fails on Mypy

**Issue:** Type checking errors
**Fix:** Run locally to see detailed errors:
```bash
mypy src/viberesp/
```

Common fixes:
- Add type hints to function signatures
- Import types: `from typing import ...`
- Use `# type: ignore` for false positives

### CI Fails on Coverage

**Issue:** Coverage below 90%
**Fix:** Run coverage report to see missing lines:
```bash
pytest tests/physics/ --cov=src/viberesp/physics --cov-report=term-missing
```

Add tests for uncovered lines or adjust threshold in `.github/workflows/ci.yml`.

### CI Fails on Theoretical Validation

**Issue:** Test doesn't match theoretical formulas
**Fix:**
1. Verify theoretical values are correct (check literature)
2. Check implementation against formulas
3. Update test fixture if theoretical values were wrong
4. Fix implementation if it doesn't match formulas

**DO NOT:** Change test to match broken implementation
**DO:** Fix implementation to match peer-reviewed physics

## Legacy Validation Workflow

The old `.github/workflows/validation.yml` has been removed. It tested the now-removed simulation engine using regression against Hornresp output.

The new physics-based approach:
- ✅ Tests against peer-reviewed formulas
- ✅ Validates correct physics behavior
- ✅ Uses Hornresp for secondary comparison only
- ✅ Documents normalization differences

See `planning/test_cases/phase1_radiation/VALIDATION_REPORT.md` for details on Hornresp comparison strategy.
