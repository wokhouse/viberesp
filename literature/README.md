# Literature Collection

This directory holds research papers, books, and reference materials for the Viberesp physics model rewrite. Organized by development phase for RAG-augmented development.

## Directory Structure

```
literature/
├── phase1_radiation/      # Radiation impedance, piston models
├── phase2_tmatrix/        # Transfer matrix method, horn theory
├── phase3_driver/         # Thiele-Small parameters, driver modeling
├── phase4_systems/        # Complete horn systems, chambers
├── phase5_multisegment/   # Multi-segment horns, composite systems
├── phase6_advanced/       # Tapped horns, transmission lines, directivity
└── general_reference/     # General acoustics, foundational texts
```

## Key References

### Primary References (Must-Have)

1. **Kolbrek & Dunker (2019)** - *High Quality Horn Loudspeaker Systems*
   - Definitive reference on horn theory
   - Covers T-matrix method, radiation impedance, all flare types
   - Available: https://hornspeakersystems.info/
   - Purchase: https://www.parts-express.com/High-Quality-Horn-Loudspeaker-Systems-500-032

2. **Kolbrek's Tutorial Series** (hornspeakersystems.info)
   - Part 1: Radiation and T-Matrix ✅ **ACQUIRED**
   - Part 2: Adding a Driver ✅ **ACQUIRED**
   - Part 3: Multiple segments and more T-matrices ✅ **ACQUIRED**

3. **Aarts & Janssen (2003)** - "Approximation of the Struve function H1"
   - JASA 113(5):2635
   - Radiation impedance calculations
   - ℹ️ Optional (SciPy has struve function)

4. **Thiele (1971), Small (1972-1974)** - JAES papers
   - Foundation of Thiele-Small parameters
   - ✅ **Small (1972)** ACQUIRED
   - ℹ️ Thiele (1971) available via AES archive

5. **Webster (1919)** - "Acoustical impedance and the theory of horns"
   - PNAS 5(7):275-282
   - Original horn equation
   - ✅ **Rienstra (2005)** commentary on Webster's equation ACQUIRED

6. **Beranek & Mellow (2012)** - *Acoustics: Sound Fields and Transducers*
   - Updated treatment of Beranek's classic text
   - Chapter 4: Radiation impedance
   - Available: https://www.sciencedirect.com/book/9780123914217/

### Secondary References

- **Hélie (2020)** - "Passive modelling of the electrodynamic loudspeaker" ✅ **ACQUIRED**
- **Kulik (2007)** - "Transfer matrix of conical waveguides" ✅ **ACQUIRED**
- **Ernoult & Kergomard (2020)** - "Transfer matrix with viscothermal losses" ✅ **ACQUIRED**
- **Olson (1957)** - *Acoustical Engineering* ✅ **ACQUIRED** (free PDF)
- Leach, *Introduction to Electroacoustics* (2003)

## File Naming Convention

```
[AuthorLastName]_[Year]_[ShortTitle].md
Example: Small_1972_Closed_Box_Systems.md
```

## Literature Citation Policy

**IMPORTANT**: All implementations MUST cite the specific literature source(s) used.

### Citation Format in Code

```python
def radiation_impedance(area: float, frequency: float) -> complex:
    """
    Calculate radiation impedance for circular piston in infinite baffle.

    References:
        - Kolbrek (2019) Part 1: Radiation and T-Matrix
          https://hornspeakersystems.info/
        - literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md
    """
    # Implementation follows Kolbrek Part 1, Eq. (X)
    ...
```

### Citation Format in Documentation

```markdown
## Throat Impedance Calculation

Based on **Kolbrek (2019) Part 1**, Section "Throat Impedance Calculation":

> Given the radiation impedance at the mouth Z₂, the throat impedance Z₁ is:
> Z₁ = (a·Z₂ + b) / (c·Z₂ + d)

For normalized impedance (as shown in Hornresp):
> Z₁_norm = Z₁ · S₁ / (ρ₀c)

See: `literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md`
```

## RAG Usage

When developing a phase, reference the corresponding literature directory:

```bash
# Phase 1: Radiation impedance
viberesp chat --rag literature/phase1_radiation/

# Phase 2: T-matrix implementation
viberesp chat --rag literature/phase2_tmatrix/

# Phase 3: Driver modeling
viberesp chat --rag literature/phase3_driver/

# All phases
viberesp chat --rag literature/
```

## Acquisition Status

### ✅ **Completed Acquisitions**

| Phase | Literature | Location | Source |
|-------|-----------|----------|--------|
| P2 | Kolbrek Part 1: Radiation & T-Matrix | `phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md` | hornspeakersystems.info |
| P2 | Rienstra (2005): Webster's Horn Equation | `phase2_tmatrix/Rienstra_2005_Websters_Horn_Equation_Revisited.md` | arXiv |
| P2 | Kulik (2007): Conical Waveguides | `phase2_tmatrix/Kulik_2007_Conical_Waveguide_Transfer_Matrix.md` | JASA |
| P3 | Kolbrek Part 2: Adding a Driver | `phase3_driver/Kolbrek_2019_Part2_Adding_Driver.md` | hornspeakersystems.info |
| P3 | Small (1972): Closed-Box Systems | `phase3_driver/Small_1972_Closed_Box_Systems.md` | ReadResearch |
| P3 | Hélie (2020): Passive Loudspeaker Modeling | `phase3_driver/Helie_2020_Passive_Modelling_Electrodynamic_Loudspeaker.md` | Acta Acustica |
| P5 | Kolbrek Part 3: Multiple Segments | `phase5_multisegment/Kolbrek_2019_Part3_Multiple_Segments.md` | hornspeakersystems.info |
| P5 | Ernoult (2020): Viscothermal Losses | `phase5_multisegment/Ernoult_2020_Truncaated_Cone_Viscothermal_Losses.md` | Acta Acustica |

### 🟡 **Partial Coverage**

| Phase | Coverage | Notes |
|-------|----------|-------|
| P1: Radiation | ✅ **Adequate** | Kolbrek Part 1 covers radiation impedance formulas |
| P2: T-Matrix | ✅ **Good** | Exponential (Kolbrek), conical (Kulik), Webster's equation |
| P3: Driver | ✅ **Excellent** | TS parameters (Small), PHS framework (Hélie) |
| P4: Systems | 🟡 Partial | General theory in Kolbrek tutorials, need complete system examples |
| P5: Multi-segment | ✅ **Good** | Matrix multiplication, viscothermal losses (Ernoult) |
| P6: Advanced | ⬜ Not started | Need tapped horn, transmission line references |

### 🔵 **High Priority Acquisition List**

| Literature | Phase | Priority | Access |
|------------|-------|----------|--------|
| **Kolbrek & Dunker (2019) Book** | All | **HIGH** | Purchase ($80) |
| Beranek & Mellow (2012) | P1, P4 | Medium | University library / purchase |
| Thiele (1971) JAES paper | P3 | Medium | AES archive |
| Small (1973-74) Vented-Box | P3 | Medium | DIYAudioProjects |

---

*Last updated: 2025-12-25*

**Next Actions:**
1. ✅ Download Kolbrek tutorial Parts 1-3
2. ✅ Download Small (1972) closed-box paper
3. ✅ Download Hélie (2020) passive modeling paper
4. ✅ Download Kulik (2007) conical waveguide paper
5. ✅ Download Ernoult (2020) viscothermal losses paper
6. ⬜ Purchase Kolbrek & Dunker (2019) book
7. ⬜ Download Small (1973-74) vented-box papers
8. ⬜ Search for tapped horn and transmission line papers (P6)
