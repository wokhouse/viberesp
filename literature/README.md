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

2. **Kolbrek's Tutorial Series** (hornspeakersystems.info)
   - Part 1: Radiation and T-Matrix
   - Part 2: Adding a Driver
   - Part 3: Multiple segments and more T-matrices

3. **Aarts & Janssen (2003)** - "Approximation of the Struve function H1"
   - JASA 113(5):2635
   - Radiation impedance calculations

4. **Thiele (1971), Small (1972-1974)** - JAES papers
   - Foundation of Thiele-Small parameters

5. **Webster (1919)** - "Acoustical impedance and the theory of horns"
   - PNAS 5(7):275-282
   - Original horn equation

### Secondary References

- Beranek, *Acoustics* (1954)
- Leach, *Introduction to Electroacoustics* (2003)
- Hélie et al. (2020) - "Passive modelling of the electrodynamic loudspeaker"
- Kulik (2007) - Transfer matrix of conical waveguides
- Tournemenne (2020) - Transfer matrix with viscothermal losses

## File Naming Convention

```
[AuthorLastName]_[Year]_[ShortTitle]_[ext]
Example: Beranek_1954_Acoustics.pdf
```

## RAG Usage

When developing a phase, reference the corresponding literature directory:

```bash
# Phase 1: Radiation impedance
viberesp chat --rag literature/phase1_radiation/

# Phase 2: T-matrix implementation
viberesp chat --rag literature/phase2_tmatrix/
```

## Acquisition Status

| Phase | Status | Notes |
|-------|--------|-------|
| P1: Radiation | ⬜ Not started | Need Aarts & Janssen (2003), Beranek |
| P2: T-Matrix | ⬜ Not started | Need Kolbrek tutorials, Webster (1919) |
| P3: Driver | ⬜ Not started | Need Thiele/Small papers |
| P4: Systems | ⬜ Not started | Need Kolbrek & Dunker book |
| P5: Multi-segment | ⬜ Not started | Need Kulik (2007), Tournemenne (2020) |
| P6: Advanced | ⬜ Not started | Need transmission line references |
| General | ⬜ Not started | Basic acoustics texts |

---

*Last updated: 2025-12-24*
