# Research Prompt: Fix Loudspeaker SPL Calculation Bug

**Date:** 2025-12-27
**Priority:** CRITICAL - Blocks flatness optimization
**Estimated Complexity:** High (requires deep acoustic theory)

---

## RESEARCH OBJECTIVE

Find the correct physics equations and implementation approach for calculating sound pressure level (SPL) from direct radiator loudspeakers (sealed and ported enclosures) that properly models:

1. **High-frequency rolloff** (mass-controlled response above resonance)
2. **Voice coil inductance effects** on frequency response
3. **Frequency-dependent radiation impedance** for pistons
4. **Accurate diaphragm velocity** from electrical impedance model

**Current Problem:** Our SPL calculation incorrectly increases with frequency (+20 dB from 20-200 Hz) when real subwoofers should rolloff at high frequencies.

---

## SUCCESS CRITERIA

The research agent should provide:

1. ✅ **Correct equations** for SPL from diaphragm velocity that include HF rolloff
2. ✅ **Implementation guidance** with Python code examples
3. ✅ **Literature citations** with specific equation numbers
4. ✅ **Validation approach** - how to verify against Hornresp
5. ✅ **Explanation of what we're doing wrong** in the current code

**Specific Deliverables:**
- Mathematical formulation: `p(f, v_diaphragm, driver_params) → SPL`
- Python implementation showing proper HF rolloff
- Citation of authoritative sources (Beranek, Small, Kinsler, etc.)
- Comparison approach: expected SPL vs frequency for a 15" subwoofer

---

## CONTEXT

**Viberesp Project:**
- Open-source loudspeaker enclosure design tool
- Validates against Hornresp (industry standard)
- Currently accurate for impedance (3.9% error) but SPL has HF bug
- Literature-first development: every function must cite sources

**Current Implementation (Buggy):**
```python
# File: src/viberesp/enclosure/ported_box.py:1148-1161
# Volume velocity: U = u_D · S_d
volume_velocity = u_diaphragm * driver.S_d

# Pressure magnitude at measurement distance
# p = jωρ₀·U / (2πr)  (magnitude only, ignore phase and distance delay)
# Kinsler et al. (1982), Chapter 4, Eq. 4.58 (piston in infinite baffle)
pressure_amplitude = (omega * air_density * abs(volume_velocity)) / \
                     (2 * math.pi * measurement_distance)

# Sound pressure level
# SPL = 20·log₁₀(p/p_ref) where p_ref = 20 μPa
p_ref = 20e-6
spl = 20 * math.log10(pressure_amplitude / p_ref) if pressure_amplitude > 0 else -float('inf')
```

**Problem:** The `omega` factor (where `omega = 2πf`) causes SPL to rise +6 dB/octave, completely overwhelming the driver's natural mass rolloff.

**What We Already Have (Correct):**
- Electrical impedance calculation (Small's Eq. 16 for ported boxes) - validated
- Diaphragm velocity from impedance: `u = F / Z_m` where `F = BL × I`
- Radiation impedance for circular piston (Beranek 1954, Eq. 5.20)
- Driver Thiele-Small parameters (Fs, Qts, Vas, M_ms, C_ms, BL, etc.)

**What's Missing:**
- Proper conversion from diaphragm velocity to SPL that includes HF rolloff
- Correct handling of voice coil inductance (currently using simple jωL model)
- Frequency-dependent mass rolloff from mechanical impedance

---

## RELEVANT CODE/DETAILS

### Driver Parameters Available:
```python
@dataclass
class ThieleSmallParameters:
    M_md: float      # Driver mass only (kg)
    C_ms: float      # Mechanical compliance (m/N)
    R_ms: float      # Mechanical resistance (N·s/m)
    R_e: float       # DC resistance (Ω)
    L_e: float       # Voice coil inductance (H)
    BL: float        # Force factor (T·m)
    S_d: float       # Effective area (m²)
    X_max: float     # Max linear excursion (m)

    # Calculated properties:
    F_s: float       # Resonance frequency (Hz)
    M_ms: float      # Total moving mass including radiation (kg)
    Q_es, Q_ms, Q_ts: float  # Q factors
    V_as: float      # Equivalent volume of compliance (m³)
```

### Current Diaphragm Velocity Calculation:
```python
# From electrical impedance (Small's model, validated accurate)
I_complex = voltage / Ze  # Voice coil current
I_mag = abs(I_complex)
F_mag = driver.BL * I_mag  # Force on diaphragm
u_diaphragm_mag = F_mag / abs(Z_mechanical_total)  # Velocity magnitude
```

### Current Radiation Impedance (Beranek 1954):
```python
# File: src/viberesp/driver/radiation_impedance.py
def radiation_impedance_piston(frequency, S_d, speed_of_sound, air_density):
    """
    Beranek (1954), Eq. 5.20: Z_R = ρc·S·[R₁(2ka) + jX₁(2ka)]
    Returns complex radiation impedance (Pa·s/m³)
    """
    k = 2 * math.pi * frequency / speed_of_sound
    a = math.sqrt(S_d / math.pi)  # Piston radius

    # R₁(x) and X₁(x) are Bessel functions (Struve approximations)
    # Implementation uses Aarts & Janssen (2003) approximation
    ...
```

### Current Voice Coil Model:
```python
# Simple model (lossless inductor):
Z_voice_coil = complex(driver.R_e, omega * driver.L_e)

# Leach model available but not used by default:
# Z_leach = voice_coil_impedance_leach(frequency, driver, leach_K, leach_n)
```

---

## CONSTRAINTS

1. **Must cite literature** - Every equation must reference specific sources (Beranek, Small, Kinsler, etc.)
2. **Numerical accuracy** - Results must match Hornresp within ±2 dB
3. **Python implementation** - Provide working code with numpy/scipy
4. **Efficiency** - Will be called many times during optimization, so vectorize where possible
5. **No new dependencies** - Use numpy, scipy (already in project)
6. **Backward compatible** - API should remain the same, only fix internals

**Key Physics Constraints:**
- Mass-controlled region: SPL falls ~12 dB/octave above Fs
- Compliance-controlled region: Relatively flat below Fs
- Ported box: 4th-order rolloff below Fb
- Sealed box: 2nd-order rolloff below F3

---

## DELIVERABLE

### 1. Root Cause Analysis
- Explain exactly why current code gives rising response
- Show what physics is missing
- Reference literature that explains correct approach

### 2. Correct Formulation
**Mathematical equations for:**
```
SPL(f) = 20·log₁₀(|p(f)| / p_ref)

where p(f) = ? (correct equation with HF rolloff)
```

Must include:
- Frequency-dependent mechanical impedance
- Proper voice coil inductance model
- Radiation impedance effects
- All in terms of driver parameters we have

### 3. Python Implementation
```python
def calculate_spl_from_diaphragm(
    frequency: float,
    diaphragm_velocity: complex,  # m/s
    driver: ThieleSmallParameters,
    measurement_distance: float = 1.0,
    speed_of_sound: float = 343.0,
    air_density: float = 1.18
) -> float:
    """
    Calculate SPL from diaphragm velocity with proper HF rolloff.

    Literature: [CITATION NEEDED]

    Returns:
        SPL in dB at measurement_distance
    """
    # Implementation here
    ...
```

### 4. Validation Approach
- How to test the fix
- Expected SPL curve for reference driver (BC_15DS115)
- Comparison points vs frequency
- What error tolerance is acceptable

### 5. Literature References
**Minimum citations needed:**
- Beranek (1954) - Acoustics
- Small (1972 or 1973) - Direct radiator SPL
- Kinsler et al. (1982) - Fundamentals of Acoustics
- Any other authoritative sources on loudspeaker SPL calculation

---

## CURRENT VALIDATION STATUS

**What Works:**
- ✅ Electrical impedance (3.9% error at peaks)
- ✅ System resonance frequencies
- ✅ Port tuning calculations
- ✅ Dual impedance peaks for ported boxes

**What's Broken:**
- ❌ SPL rises with frequency (+20 dB from 20-200 Hz)
- ❌ No high-frequency rolloff
- ❌ Flatness optimization useless (optimizing wrong curve)

**Hornresp Comparison:**
- Hornresp shows proper mass rolloff at high frequencies
- Viberesp shows linearly rising SPL (wrong)
- Impedance matches well, so diaphragm velocity should be OK
- Problem is in converting velocity → SPL

---

## EXAMPLE OF EXPECTED BEHAVIOR

**For BC_15DS115 in 180L ported box @ 28Hz:**

```
Current (WRONG):
20 Hz:  77 dB
50 Hz:  85 dB
100 Hz: 91 dB
200 Hz: 97 dB  ← Should be lower, not higher!

Correct (expected):
20 Hz:  82 dB  (peak)
50 Hz:  88 dB  (flat region)
100 Hz: 86 dB  (starting to rolloff)
200 Hz: 78 dB  (mass rolloff)
500 Hz: 70 dB  (significant rolloff)
```

---

## WHY THIS MATTERS

1. **Flatness optimization is blocked** - Can't optimize for flat response when SPL curve is wrong
2. **Hornresp validation fails** - SPL doesn't match reference
3. **User trust** - Rising SPL looks wrong to anyone who knows speakers
4. **Downstream features** - Max SPL, power handling, excursion all depend on accurate SPL

---

## RESEARCH STRATEGY SUGGESTIONS

**Key questions to investigate:**

1. **How does Hornresp calculate SPL?** (We can see inputs/outputs, not source)
   - What transfer function do they use?
   - How do they model HF rolloff?

2. **Small's papers** - Does Small (1972/1973) give SPL equations?
   - Focus on direct radiator response
   - Look for velocity → SPL conversion

3. **Beranek (1954)** - Acoustics textbook
   - Chapter on direct radiators
   - Piston radiation formulas
   - Frequency response of piston in baffle

4. **Kinsler et al.** - Fundamentals of Acoustics
   - Radiation impedance effects
   - Directivity patterns (affects SPL)
   - Frequency-dependent effects

5. **Voice coil inductance**
   - Leach (2002) model or similar
   - How to incorporate Le into SPL calculation
   - Frequency-dependent impedance

6. **Alternative approaches**
   - Transfer function methods (analogous to impedance)
   - Equivalent circuit models
   - Numerical vs analytical solutions

---

## CONTACT FOR CLARIFICATION

If the research agent needs clarification on:
- Current codebase structure
- Available parameters
- Validation data
- Specific equations used

**Can access the full codebase at:**
```
https://github.com/wokhouse/viberesp
```

**Key files to review:**
- `src/viberesp/enclosure/ported_box.py` - Current buggy SPL implementation (lines 1148-1161)
- `src/viberesp/driver/radiation_impedance.py` - Beranek Eq. 5.20 implementation
- `src/viberesp/driver/electrical_impedance.py` - Voice coil models
- `src/viberesp/driver/response.py` - Direct radiator response
- `docs/validation/ported_box_spl_analysis.md` - Current validation status
- `docs/validation/ported_box_impedance_fix.md` - Impedance validation (working correctly)

---

## OUTPUT FORMAT

Please provide research results in markdown format with:

1. **Executive Summary** - What's wrong and how to fix it (2-3 sentences)
2. **Root Cause** - Detailed explanation with equations
3. **Solution** - Step-by-step implementation approach
4. **Code** - Working Python implementation
5. **Validation** - How to verify the fix
6. **References** - Complete literature citations with equation numbers

---

**Priority:** CRITICAL - This is blocking flatness optimization which is a key user feature.
**Timeline:** ASAP - Research needed before implementation can begin.
**Impact:** High - Fixes core physics, enables multiple features (flatness, max SPL, etc.)

---

END OF RESEARCH PROMPT
