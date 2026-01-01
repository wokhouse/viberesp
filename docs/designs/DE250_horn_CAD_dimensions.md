# BC_DE250 Horn Profile - CAD Dimensions

**Optimization Date:** 2026-01-01
**Optimization Objectives:** Wavefront sphericity + Impedance smoothness

## Horn Profile Type

**2-Segment Exponential Horn** with optimized expansion rates
- Segment 1: Throat → Middle
- Segment 2: Middle → Mouth

---

## Critical Dimensions (all in mm)

### Radii at Key Locations

| Location | Radius (mm) | Diameter (mm) | Area (cm²) |
|----------|-------------|---------------|------------|
| **Throat** | **13.36** | **26.72** | 5.61 |
| **Middle** (junction) | **57.89** | **115.78** | 105.20 |
| **Mouth** | **133.99** | **267.98** | 564.64 |

### Axial Lengths

| Dimension | Length (mm) | Length (cm) |
|-----------|-------------|-------------|
| **Segment 1** (throat → middle) | **204.3** | 20.43 |
| **Segment 2** (middle → mouth) | **213.7** | 21.37 |
| **Total Horn Length** | **418.0** | 41.80 |

---

## Construction Details

### Segment 1 (Throat → Middle)
- **Start Radius:** 13.36 mm (throat)
- **End Radius:** 57.89 mm (middle)
- **Axial Length:** 204.3 mm
- **Flare Constant:** m1 = 14.35 m⁻¹
- **Profile:** Exponential expansion
  - Formula: r(x) = r_throat × exp(m1 × x / 2)
  - Where x = distance from throat (0 to 0.2043 m)

### Segment 2 (Middle → Mouth)
- **Start Radius:** 57.89 mm (middle)
- **End Radius:** 133.99 mm (mouth)
- **Axial Length:** 213.7 mm
- **Flare Constant:** m2 = 3.92 m⁻¹ (calculated from geometry)
- **Profile:** Exponential expansion
  - Formula: r(x) = r_middle × exp(m2 × x / 2)
  - Where x = distance from middle (0 to 0.2137 m)

---

## Throat Interface

**Driver Mounting:**
- Accepts standard 1" (25.4 mm) exit compression driver
- Throat diameter: 26.72 mm (slightly larger than driver for smooth transition)
- Recommend: Use adapter plate from 25.4 mm driver to 26.72 mm throat

**Throat Chamber Volume:**
- V_tc = 10.7 cm³
- This is the volume between driver diaphragm and horn throat
- For CAD: Include small chamber if modeling complete system

---

## Mouth Interface

**Mouth Diameter:** 267.98 mm (≈ 268 mm)
**Mouth Circumference:** 841 mm

**Directivity Cutoff:**
- At 783 Hz (horn cutoff), wavelength = 438 mm
- Mouth circumference = 841 mm ≈ 1.92 × wavelength
- This provides good directivity control above cutoff

---

## CAD Construction Notes

### Recommended Approach

1. **Create Profile Curve:**
   - Draw exponential curve for each segment
   - Segment 1: r(x) = 13.36 × exp(14.35 × x / 2) for x ∈ [0, 204.3mm]
   - Segment 2: r(x) = 57.89 × exp(3.92 × x / 2) for x ∈ [0, 213.7mm]

2. **Revolve Profile:**
   - Revolve curve around central axis
   - Creates axisymmetric horn body

3. **Wall Thickness:**
   - Recommend 10-15 mm wall thickness for structural rigidity
   - Can be thicker at mouth for mounting flange

4. **Surface Finish:**
   - **Critical:** Smooth internal surfaces
   - Recommend CNC machining or careful hand finishing
   - Surface roughness < 0.8 mm Ra recommended

5. **Driver Mounting:**
   - Create flat mounting plate at throat
   - Thickness: 10-15 mm
   - Bolt pattern: Match BC_DE250 mounting holes
   - Include gasket groove for airtight seal

6. **Mouth Flange:**
   - Add 20-25 mm wide flange at mouth
   - Allows mounting to enclosure/baffle
   - Provides stiffness for large mouth opening

### Tolerances

| Dimension | Recommended Tolerance |
|-----------|----------------------|
| Throat radius | ±0.1 mm (critical for impedance) |
| Middle radius | ±0.5 mm |
| Mouth radius | ±1.0 mm (less critical) |
| Axial lengths | ±1.0 mm |
| Surface finish (internal) | Ra < 0.8 mm |

---

## Material Recommendations

**Preferred (in order of quality):**
1. **Aluminum 6061-T6** - Can be CNC machined, excellent surface finish
2. **Hardwoods** - Maple, cherry, or oak with very smooth finishing
3. **Plastics** - ABS or acrylic CNC machined
4. **Composites** - Carbon fiber or fiberglass (requires mold)

**Avoid:**
- Rough internal surfaces (cause turbulence)
- Sharp transitions at segment junction
- Porous materials that absorb sound

---

## Validation After Construction

**Checklist:**
- [ ] Measure throat diameter (target: 26.7 ± 0.2 mm)
- [ ] Measure mouth diameter (target: 268 ± 2 mm)
- [ ] Check axial lengths (204 mm + 214 mm)
- [ ] Verify smooth internal surfaces (no rough spots)
- [ ] Test fit compression driver at throat
- [ ] Verify airtight seal

---

## Design Reference

**Source File:** `tasks/results/DE250_8NDL51_two_way_design.json`
**Optimization Method:** NSGA-II (Pymoo)
**Objectives:** Wavefront sphericity, Impedance smoothness
**Generations:** 50
**Population:** 50
**Design Rank:** #1 (Pareto front)

---

## Quick Reference (for CNC/Manual Machining)

```
SEGMENT 1 (Throat → Middle):
  Start:  r = 13.36 mm (throat)
  End:    r = 57.89 mm (middle)
  Length: L = 204.3 mm
  Curve:  Exponential with m1 = 14.35 m⁻¹

SEGMENT 2 (Middle → Mouth):
  Start:  r = 57.89 mm (middle)
  End:    r = 133.99 mm (mouth)
  Length: L = 213.7 mm
  Curve:  Exponential with m2 = 3.92 m⁻¹

TOTAL LENGTH: 418.0 mm
MOUTH DIAMETER: 268.0 mm
THROAT DIAMETER: 26.7 mm
```

---

**Notes:**
- The transition between segments should be smooth (no sharp edges)
- Consider adding a small radius (2-3 mm) at the segment junction
- Internal surface quality is more important than external appearance
- Wall thickness can vary (thinner at mouth, thicker at throat for mounting)
