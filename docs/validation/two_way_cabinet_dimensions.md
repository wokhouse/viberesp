# Cabinet Dimensions: Two-Way Time-Aligned Horn System

**System:** BC_10NW64 (LF) + BC_DE250 (HF) with Exponential Horn
**Date:** 2025-12-30
**Status:** Ready for Construction

---

## Quick Reference

| Parameter | Value |
|-----------|-------|
| Horn Length (time alignment) | **760 mm** |
| Horn Mouth Diameter | **356 mm** |
| LF Enclosure Volume (Vb) | **26.5 L** |
| Port Tuning (Fb) | **70 Hz** |
| Crossover Frequency | **800 Hz** |
| HF Padding (L-pad) | **-17.5 dB** |

---

## Cabinet Option 1: Vertical Tower

**Recommended for:** Floorstanding home audio

### Overall Dimensions

```
Front View:
┌──────────────────────┐
│         500          │  Width: 500 mm
│  ┌───────────────┐   │  Height: 1000 mm
│  │               │   │  (excluding horn)
│  │   ╔═══════╗   │   │  Total depth with
│  │   ║  HF   ║   │   │  horn protrusion:
│  │   ╚═══════╝   │   │  1110 mm
│  │               │   │
│  │      ●        │   │
│  │   (LF)        │   │
│  │               │   │
│  │   ║    ║      │   │
│  │  (P1) (P2)    │   │
│  └───────────────┘   │
│                      │
└──────────────────────┘
```

### Detailed Cut List (18 mm MDF)

**Front Baffle (1 piece):**
- Dimensions: 500 mm W × 1000 mm H × 18 mm
- Cutouts:
  - HF horn throat: 44 mm diameter (centered horizontally, 200 mm from top)
  - LF driver: 235 mm diameter (centered horizontally, 400 mm from top)
  - Port 1: 100 mm diameter (center: 200 mm from left, 600 mm from top)
  - Port 2: 100 mm diameter (center: 300 mm from left, 600 mm from top)

**Side Panels (2 pieces):**
- Dimensions: 464 mm W × 1000 mm H × 18 mm
- (Width accounts for front/rear panel thickness)

**Top Panel (1 piece):**
- Dimensions: 464 mm W × 500 mm D × 18 mm

**Bottom Panel (1 piece):**
- Dimensions: 464 mm W × 500 mm D × 18 mm

**Rear Panel (1 piece):**
- Dimensions: 500 mm W × 1000 mm H × 18 mm
- Cutout: Terminal cup (if rear-mounted)

**Internal Bracing (4 pieces):**
- Cross-braces: 464 mm × 464 mm × 18 mm
- Window cutouts: 300 mm × 300 mm (centered)
- Mounting positions: 250 mm, 500 mm, 750 mm from top

**Ports (2 pieces):**
- Material: PVC or ABS pipe
- Diameter: 100 mm (inner)
- Length: 228 mm each
- Flare ends (recommended)

### Internal Volume Calculation

```
Internal dimensions (gross):
- Width: 464 mm (500 - 18 - 18)
- Height: 964 mm (1000 - 18 - 18)
- Depth: 464 mm (500 - 18 - 18)

Gross volume: 207.5 L

Displacements:
- LF driver: ~2.5 L
- Ports: ~3.6 L (2 × 1.8 L)
- Bracing: ~5 L
- Damping: ~2 L

Net volume (Vb): ~195 L

Usable volume: Set to 26.5 L using internal divider/baffle
```

**Note:** The large gross volume is divided internally to achieve the required 26.5 L net volume for the LF driver. The remaining volume can be used for:
- Horn structure (if partially enclosed)
- Sealed chambers
- Damping material

---

## Cabinet Option 2: Compact Cube

**Recommended for:** Studio monitor or bookshelf (on stands)

### Overall Dimensions

```
Front View:
┌─────────────────┐
│      400        │  Width: 400 mm
│  ┌───────────┐  │  Height: 600 mm
│  │  ╔═════╗  │  │  (excluding horn)
│  │  ║  HF ║  │  │  Total depth with
│  │  ╚═════╝  │  │  horn: 1160 mm
│  │           │  │
│  │    ●      │  │
│  │  (LF)     │  │
│  │           │  │
│  │  ║   ║    │  │
│  └───────────┘  │
└─────────────────┘
```

### Detailed Cut List (18 mm MDF)

**Front Baffle (1 piece):**
- Dimensions: 400 mm W × 600 mm H × 18 mm
- Cutouts:
  - HF horn throat: 44 mm diameter (centered horizontally, 150 mm from top)
  - LF driver: 235 mm diameter (centered horizontally, 350 mm from top)
  - Port 1: 100 mm diameter (center: 150 mm from left, 480 mm from top)
  - Port 2: 100 mm diameter (center: 250 mm from left, 480 mm from top)

**Side Panels (2 pieces):**
- Dimensions: 364 mm W × 600 mm H × 18 mm

**Top Panel (1 piece):**
- Dimensions: 364 mm W × 400 mm D × 18 mm

**Bottom Panel (1 piece):**
- Dimensions: 364 mm W × 400 mm D × 18 mm

**Rear Panel (1 piece):**
- Dimensions: 400 mm W × 600 mm H × 18 mm
- Cutout: Terminal cup

**Internal Bracing (2 pieces):**
- Cross-braces: 364 mm × 364 mm × 18 mm
- Window cutouts: 200 mm × 200 mm
- Mounting positions: 200 mm, 400 mm from top

**Ports (2 pieces):**
- Diameter: 100 mm (inner)
- Length: 228 mm each

### Internal Volume Calculation

```
Internal dimensions (gross):
- Width: 364 mm
- Height: 564 mm
- Depth: 364 mm

Gross volume: 74.8 L

Displacements:
- LF driver: ~2.5 L
- Ports: ~3.6 L
- Bracing: ~2 L
- Damping: ~1 L

Net volume (Vb): Set to 26.5 L using internal divider
```

---

## Horn Construction

### Option A: Stacked Wood Rings

**Materials:**
- 18 mm MDF or plywood
- Wood glue (PVA)
- Clamps
- Router (for flare profiling)

**Process:**
1. Cut 20 rings with progressively larger diameter
2. Route inner edge to exponential curve
3. Stack and glue rings sequentially
4. Sand smooth when complete
5. Wrap in veneer or finish

**Ring Dimensions (example):**
```
Ring 1 (throat mount):   44 mm ID × 150 mm OD
Ring 2:                  55 mm ID × 160 mm OD
Ring 3:                  67 mm ID × 170 mm OD
...
Ring 20 (mouth flange):  356 mm ID × 400 mm OD

Thickness: 18 mm per ring
Total length: 20 × 18 = 360 mm
(Additional extensions to reach 760 mm)
```

### Option B: Fiberglass Mold

**Materials:**
- Fiberglass cloth and resin
- Mold (plug or CNC-routed foam)
- Release agent
- Gelcoat (for finish)

**Process:**
1. Create mold (plug) of horn interior
2. Apply release agent
3. Lay up fiberglass in 4-6 layers
4. Cure and demold
5. Trim and sand
6. Mount to baffle flange

### Option C: Hybrid Construction

**Throat section** (first 300 mm):
- Solid wood rings
- Precise throat alignment

**Mouth section** (remaining 460 mm):
- Fiberglass or bendable plywood
- Lighter weight
- Easier to form large flare

---

## Driver Placement Details

### HF Driver (DE250) Mounting

```
Throat plate:
┌────────────────────┐
│        ╔════╗      │
│        ║44mm║      │ ← 44 mm hole (1" throat)
│        ║    ║      │
│   150mm║    ║      │
│        ╚════╝      │
└────────────────────┘
         │
         │ Attach horn structure here
         ↓
```

**Throat plate:**
- Material: 18 mm MDF or solid wood
- Thickness: 18 mm minimum
- Mounting bolts: 4× M4 or #10-32 (typically included with driver)

### LF Driver (10NW64) Mounting

```
Driver cutout: 235 mm diameter
Mounting holes: 8 holes on 267 mm bolt circle
(Refer to driver frame for exact pattern)

Recess: 6-8 mm (if flush mounting desired)
```

**Mounting hardware:**
- 8× M6 or 1/4"-20 bolts (30 mm length)
- T-nuts or threaded inserts (embedded in baffle)
- Gasket: Foam or rubber seal (prevents air leaks)

---

## Port Installation

### Flared Port Construction

**Option 1: Commercial flared ports**
- Parts Express precision ports
- Flare both ends
- Length: Adjustable

**Option 2: DIY flare**

```
Front flare:
    ╱─────╲
   │       │
   │ 100mm │  ← Port tube (PVC)
   │       │
    ╲─────╱  ← Router or sand flare

Mounting: Flush with front baffle
Sealing: Silicone or epoxy
```

**Port entry clearance:**
- Minimum 50 mm from internal walls
- Minimum 100 mm from driver cone
- No obstructions within 1.5 × port diameter

---

## Crossover Implementation

### Passive LR4 Crossover

**Component values for 800 Hz LR4:**
*(Note: These are preliminary - use crossover design software for exact values)*

**Low-pass section (LF):**
- L1: 1.5 mH (air core)
- L2: 1.5 mH (air core)
- C1: 12 µF (polypropylene)
- C2: 12 µF (polypropylene)

**High-pass section (HF):**
- C3: 4.7 µF (polypropylene)
- C4: 4.7 µF (polypropylene)
- L3: 0.47 mH (air core)
- L4: 0.47 mH (air core)

**HF L-pad (attenuation):**
- R1 (series): 8 Ω, 10W (non-inductive)
- R2 (parallel): 8 Ω, 5W (non-inductive)
- Adjust to achieve -17.5 dB padding

**Impedance correction:**
- Not typically needed for ported LF
- HF may need Zobel if impedance rise is problematic

### Active Crossover (DSP)

**Recommended settings:**
- Crossover: LR4 @ 800 Hz
- HF gain: -17.5 dB
- LF delay: 0 ms (physically aligned via horn protrusion)
- EQ: Individual driver response correction (if needed)

---

## Construction Sequence

### Phase 1: Cabinet Body

1. **Cut all panels** to final dimensions
2. **Route driver cutouts** in front baffle
3. **Mount terminal cup** in rear panel
4. **Assemble cabinet body** (except front baffle)
   - Glue and screw joints
   - Clamp until dry
6. **Install internal bracing**
7. **Seal all internal joints** with silicone
8. **Add damping material** (acoustic foam, 25-50 mm on walls)

### Phase 2: Ports and Drivers

1. **Install ports** in front baffle
   - Glue or mechanical fastening
   - Seal with silicone
2. **Wire LF driver** to terminal cup
3. **Mount LF driver** to front baffle
   - Use gasket for seal
4. **Test LF driver** for proper operation

### Phase 3: Horn Assembly

1. **Construct horn body** (choose method A, B, or C)
2. **Mount compression driver** to throat plate
3. **Attach horn** to throat plate
4. **Test HF driver** for proper operation
5. **Wire HF driver** through crossover or to terminal cup

### Phase 4: Crossover

**Passive:**
1. **Build crossover board**
2. **Mount inside cabinet** (rear wall or base)
3. **Wire drivers to crossover**
4. **Wire crossover to terminals**
5. **Secure all wiring** with cable ties

**Active:**
1. **Set up DSP/amplifier** externally
2. **Wire drivers to external amp channels**
3. **Configure DSP settings**

### Phase 5: Finishing

1. **Sand all surfaces** (progressive grits: 80 → 150 → 220)
2. **Apply finish**
   - Veneer: Contact cement, sand, clear coat
   - Paint: Primer, 2-3 coats, sand between coats
   - Oil/wax: For natural wood look
3. **Install grille** (optional)
4. **Add feet or spikes**

---

## Measurement and Validation

### Required Equipment

- Measurement microphone (calibrated)
- Audio interface
- Measurement software (REW, VituixCAD, etc.)
- Test signal source (sweeps, MLS, etc.)

### Measurement Checklist

**Before final assembly:**
- [ ] LF driver impedance sweep
- [ ] HF driver impedance sweep
- [ ] Individual driver frequency responses (nearfield)
- [ ] Port tuning verification

**After assembly:**
- [ ] System impedance
- [ ] On-axis frequency response (1m)
- [ ] Off-axis responses (15°, 30°, 45°)
- [ ] Harmonic distortion
- [ ] Impulse response (verify time alignment)
- [ ] Port noise check (high power)

### Target Performance

| Metric | Target | Measured |
|--------|--------|----------|
| System F3 | 65 Hz | ___ Hz |
| F10 | 45 Hz | ___ Hz |
| Passband ripple | ±2 dB | ___ dB |
| Max SPL | >105 dB | ___ dB |
| Impedance min | >4 Ω | ___ Ω |
| Crossover dip | <1 dB | ___ dB |
| THD @ 100 Hz | <5% | ___ % |
| THD @ 1 kHz | <1% | ___ % |

---

## Parts List

### Drivers
- [ ] 2× BC_10NW64 LF drivers (or equivalent 10" woofer)
- [ ] 2× BC_DE250 HF compression drivers (1" exit)

### Crossover Components (Passive)
- [ ] 2× 1.5 mH inductors (air core, 14 AWG)
- [ ] 2× 0.47 mH inductors (air core, 18 AWG)
- [ ] 4× 12 µF capacitors (polypropylene, 250V)
- [ ] 4× 4.7 µF capacitors (polypropylene, 250V)
- [ ] 4× 8 Ω non-inductive resistors (10W and 5W)
- [ ] PCB or terminal board
- [ ] Wire (14-16 AWG internal)

### Cabinet Hardware
- [ ] Wood screws (#8 × 40 mm - assembly)
- [ ] Machine screws (M6 × 30 mm - LF driver)
- [ ] T-nuts or threaded inserts (8 per LF driver)
- [ ] Bolts for HF driver (usually included)
- [ ] Terminal cup (binding posts)
- [ ] Gasket material (foam tape)
- [ ] Port tubes (2× 100mm PVC, 228 mm length)

### Materials
- [ ] MDF or plywood (18 mm thickness)
  - Tower: ~2.5 sheets (1220 × 2440 mm)
  - Cube: ~1.5 sheets
- [ ] Wood glue (PVA, 1 liter)
- [ ] Silicone caulk (clear or black)
- [ ] Acoustic damping foam (1-2 sheets)
- [ ] Wood veneer or finish materials

### Horn Construction
- [ ] Additional MDF for rings (if using stacked ring method)
  - ~1 sheet for 2 horns
- OR [ ] Fiberglass cloth and resin (if molding)
- OR [ ] Bendable plywood (if forming)

### Tools Required
- [ ] Circular saw or table saw
- [ ] Jigsaw (for driver cutouts)
- [ ] Router (optional, for flare profiling)
- [ ] Drill and bits
- [ ] Clamps (6-10 bar clamps)
- [ ] Sandpaper (assorted grits)
- [ ] Square and measuring tools
- [ ] Soldering iron (for crossover)

---

## Cost Estimate (Per Pair)

**Rough estimates (USD):**

| Item | Cost |
|------|------|
| LF drivers (2×) | $200-300 |
| HF drivers (2×) | $300-400 |
| Cabinet materials | $150-200 |
| Horn construction | $100-200 |
| Crossover parts (passive) | $150-250 |
| Hardware & misc | $50-100 |
| **Total** | **$950-1450** |

*(Active system: Add $300-500 for DSP/amplification)*

---

## Safety Notes

1. **Dust protection:** Wear mask when cutting MDF
2. **Ventilation:** Use finish materials in well-ventilated area
3. **Lifting:** Large panels can be heavy - get help
4. **Electrical:** Disconnect power when wiring
5. **Hearing protection:** When testing at high levels

---

## Troubleshooting

**Problem: Cabinet buzzes or rattles**
- Solution: Add internal bracing, tighten joints, check driver mounting

**Problem: Port noise (chuffing)**
- Solution: Larger ports, flared ends, reduce tuning frequency

**Problem: Crossover dip remains**
- Solution: Verify horn alignment, check crossover wiring, measure phase

**Problem: LF driver bottoming out**
- Solution: Reduce power, add subsonic filter, increase box size

**Problem: HF driver too bright**
- Solution: Adjust HF padding, add foam absorption in horn mouth

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Status:** Ready for Construction
