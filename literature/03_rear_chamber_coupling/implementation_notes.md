# Rear Chamber Coupling: Implementation Notes

**Target**: Improve 9 dB RMSE error in case2
**File**: `src/viberesp/enclosures/horns/exponential_horn.py`
**Priority**: 🟢 **Medium** - Smallest error of the three priorities

---

## Current Problem

**case2** (horn with rear chamber): 9.21 dB RMSE

**Issue**: Rear chamber coupling to horn throat may not be modeled correctly.

---

## Rear Chamber Physics

### What is the Rear Chamber?

In horn-loaded loudspeakers:
- **Driver** mounts in a chamber **behind** the horn throat
- **Rear chamber** provides compliance (spring) for driver
- **Driver** pushes into throat through chamber

```
        Horn
         ↑
    ┌────┴────┐
    │ Throat  │
    └────┬────┘
         ↑
    ┌────┴────┐
    │ Driver  │
    └────┬────┘
         ↑
    ┌────┴────┐
    │ Rear    │
    │ Chamber │
    └─────────┘
```

---

### Impedance Topology

**Key insight**: Rear chamber is in **parallel** with throat load (similar to front chamber).

```
        ┌─── Z_rear_chamber ──┐
Driver ─┤                   ├─── Throat ──── Horn
        └───────────────────┘
```

**Combined impedance**:

```
Z_total = (Z_throat × Z_rear) / (Z_throat + Z_rear)
```

---

## Rear Chamber Impedance

The rear chamber acts as an acoustic compliance:

```
Z_rear = 1 / (jω × C_rear)
```

Where the acoustic compliance is:

```
C_rear = V_rear / (ρ₀ × c²)
```

**Implementation**:

```python
def calculate_rear_chamber_impedance(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate rear chamber acoustic impedance.

    Models rear chamber as acoustic compliance.

    Args:
        frequencies: Frequency array (Hz)

    Returns:
        Complex impedance (Pa·s/m³)
    """
    omega = 2 * np.pi * frequencies
    rho = 1.184  # kg/m³
    c = 343.0    # m/s

    # Rear chamber volume (convert L to m³)
    V_rear = self.rear_chamber_volume / 1000

    # Acoustic compliance
    C_rear = V_rear / (rho * c**2)

    # Chamber impedance (compliance)
    Z_rear = 1 / (1j * omega * C_rear)

    return Z_rear
```

---

## Driver-to-Chamber Coupling

### Mechanical Impedance with Rear Chamber

The driver sees the combined load:

```
Z_mechanical = R_ms + jωM_ms + 1/(jωC_ms) + S_d² × Z_acoustic
```

Where `Z_acoustic` is the **parallel combination**:

```
Z_acoustic = (Z_throat × Z_rear) / (Z_throat + Z_rear)
```

**Key point**: Rear chamber compliance is **in parallel** with throat impedance.

---

### Volume Velocity Division

At the rear chamber/throat junction:

```
U_driver = U_throat + U_rear
```

Where:
- `U_throat = Z_acoustic / Z_throat × U_driver`
- `U_rear = Z_acoustic / Z_rear × U_driver`

**Fraction going to throat**:

```
U_throat / U_driver = Z_rear / (Z_throat + Z_rear)
```

---

## Implementation Strategy

### Change 1: Add Rear Chamber Impedance Calculation

**Location**: New method in `ExponentialHorn` class

```python
def calculate_rear_chamber_impedance(self, frequencies: np.ndarray) -> np.ndarray:
    """Calculate rear chamber impedance (compliance)."""
    omega = 2 * np.pi * frequencies
    rho = 1.184
    c = 343.0

    if self.rear_chamber_volume is None:
        # No rear chamber - infinite impedance (open circuit)
        return np.inf * np.ones_like(frequencies, dtype=complex)

    V_rear = self.rear_chamber_volume / 1000  # L → m³
    C_rear = V_rear / (rho * c**2)

    Z_rear = 1 / (1j * omega * C_rear)

    return Z_rear
```

---

### Change 2: Modify calculate_system_response()

**Location**: Update impedance calculation in system response

**Current** (may be wrong):

```python
# May be treating rear chamber incorrectly
Z_acoustic = Z_throat  # Missing rear chamber
```

**Should be**:

```python
# Calculate throat and rear chamber impedances
Z_throat = self.calculate_throat_impedance(frequencies)
Z_rear = self.calculate_rear_chamber_impedance(frequencies)

# Parallel combination
Z_acoustic = (Z_throat * Z_rear) / (Z_throat + Z_rear)
```

---

### Change 3: Handle No Rear Chamber

When `rear_chamber_volume = None`:

```python
if self.rear_chamber_volume is None:
    # No rear chamber - driver directly coupled to throat
    Z_acoustic = Z_throat
else:
    # With rear chamber - parallel combination
    Z_rear = self.calculate_rear_chamber_impedance(frequencies)
    Z_acoustic = (Z_throat * Z_rear) / (Z_throat + Z_rear)
```

---

## Validation

### Test Against case2

**case2 parameters**:
```
Throat area: 600 cm²
Mouth area: 4800 cm²
Horn length: 200 cm
Rear chamber: 1 L
Cutoff: 35 Hz
```

**Expected behavior**:
- Low frequency: Rear chamber compliance dominates
- High frequency: Throat impedance dominates
- Transition around 50-100 Hz

**Validation test**:

```bash
PYTHONPATH=src pytest tests/validation/test_synthetic_cases.py::test_synthetic_case_validation[case2_horn_rear_chamber] -v

# Expected: RMSE < 5 dB (vs 9.21 dB current)
```

---

## Common Mistakes

### ❌ Mistake 1: Series Instead of Parallel

```python
Z_total = Z_throat + Z_rear  # WRONG
Z_total = (Z_throat * Z_rear) / (Z_throat + Z_rear)  # CORRECT
```

---

### ❌ Mistake 2: Forgetting S_d² Scaling

```python
Z_mechanical = Z_mech_driver + Z_rear  # WRONG
Z_mechanical = Z_mech_driver + S_d**2 * Z_acoustic  # CORRECT
```

The acoustic impedance must be scaled by `S_d²` to convert to mechanical impedance.

---

### ❌ Mistake 3: Wrong Compliance Direction

```python
Z_rear = j * omega * C_rear  # WRONG (that's mass-like)
Z_rear = 1 / (j * omega * C_rear)  # CORRECT (compliance)
```

---

## Expected Impact

### case2 (Rear Chamber)

| Metric | Current | Target |
|--------|---------|--------|
| RMSE | 9.21 dB | 2-4 dB |
| Correlation | 0.00 | >0.95 |
| F3 error | None | <2 Hz |

**Key improvements**:
- Correct impedance topology (parallel)
- Proper low-frequency behavior
- Accurate driver-to-horn coupling

---

## Comparison with Front Chamber

| Aspect | Rear Chamber | Front Chamber |
|--------|--------------|---------------|
| **Location** | Behind driver | In front of throat |
| **Type** | Pure compliance | Compliance + modes |
| **Coupling** | Parallel to throat | Parallel to throat |
| **Complexity** | Simple (one mode) | Complex (multi-mode) |

**Key similarity**: Both are **parallel** to throat impedance.

---

## References

1. **Olson, "Acoustical Engineering"** - Rear chamber compliance
2. **Beranek & Mellow** - Acoustic impedance circuits
3. **Small papers** - Enclosure compliance modeling
4. **Kolbrek AES 2018** - Front chamber (for comparison)

---

## Summary

Rear chamber coupling is relatively straightforward:

1. **Rear chamber = acoustic compliance**: `Z = 1/(jωC)`
2. **Parallel topology**: `Z_total = (Z_throat × Z_rear) / (Z_throat + Z_rear)`
3. **Scale by S_d²**: Convert acoustic to mechanical impedance

**Implementation effort**: Low (1-2 hours)

**Expected improvement**: 9 → 2-4 dB RMSE

---

## Next Steps

1. ✅ Understand rear chamber physics
2. ⏳ Implement `calculate_rear_chamber_impedance()`
3. ⏳ Fix impedance topology in `calculate_system_response()`
4. ⏳ Validate against case2
5. ⏳ Move to foundation topics (radiation impedance, complete system)
