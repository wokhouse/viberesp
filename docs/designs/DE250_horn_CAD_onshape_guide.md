# Onshape Horn Profile Setup Guide

**Horn:** BC_DE250 2-Segment Exponential Horn
**Profile:** 100-point CSV file provided

---

## Method 1: Import CSV as Curve (Recommended - Easiest)

### Step 1: Prepare the CSV File

The CSV file needs to be in Onshape format:
```
x,y,z
0,13.363,0
4.169,13.769,0
8.338,14.187,0
...
```

**Convert your profile CSV:**

```python
# Run this to convert the profile to Onshape format
import pandas as pd
import numpy as np

# Read profile
df = pd.read_csv('tasks/results/DE250_horn_profile.csv', comment='#')

# Create Onshape format (x = axial, y = radius, z = 0)
onshape_df = pd.DataFrame({
    'x': df['x_mm'],
    'y': df['radius_mm'],
    'z': 0.0
})

# Save
onshape_df.to_csv('tasks/results/DE250_horn_onshape.csv', index=False)
print("✓ Exported to DE250_horn_onshape.csv")
```

**Or use this quick conversion:**

```bash
# In your terminal
cd tasks/results
# Skip header comments, keep data columns
tail -n +6 DE250_horn_profile.csv | cut -d',' -f1,2 > DE250_horn_onshape_temp.csv
# Add header
echo "x,y" | cat - DE250_horn_onshape_temp.csv > DE250_horn_onshape.csv
```

### Step 2: Import to Onshape

1. **Open your Onshape document**
2. **Create new Part Studio**
3. **Features → Import** (or right-click in Part Studio → Import)
4. **Select CSV file** → DE250_horn_onshape.csv
5. **Options:**
   - Units: Millimeters
   - Import as: Curve
   - Create sketch: No

This creates a 3D curve through all your points.

### Step 3: Create Sketch from Curve

1. **New Sketch** → Select plane (e.g., Front plane)
2. **Use → Project** → Select the imported curve
3. This projects the curve into your sketch
4. **Finish Sketch**

### Step 4: Revolve to Create Solid

1. **Revolve** → Select the sketch profile
2. **Axis:** Draw centerline or select origin axis
3. **Angle:** 360°
4. **Revolve**

### Step 5: Add Wall Thickness (Shell)

1. **Shell** → Select the mouth face (remove it)
2. **Thickness:** 10-15 mm (your choice)
3. This creates a hollow horn with open mouth

---

## Method 2: Sketch Spline Through Points (More Control)

### Step 1: Create Sketch

1. **New Sketch** → Select Front plane (or Right plane)

### Step 2: Import Points as Construction Geometry

**Option A: Manual Entry (for key points only)**

1. **Construction Point** → Create these points:
   - (0, 13.36) - Throat
   - (52, 18.2) - 1/4
   - (102, 27.0) - 1/2
   - (153, 40.1) - 3/4
   - (204.3, 57.87) - Middle ← **Critical**
   - (258, 68.9) - Seg 2, 1/4
   - (311, 83.7) - Seg 2, 1/2
   - (365, 104.2) - Seg 2, 3/4
   - (418, 134.06) - Mouth

2. Use **Smart Dimension** to verify locations

**Option B: Import all points (recommended)**

1. **Insert → CSV** from sketch toolbar
2. Select `DE250_horn_profile.csv`
3. Onshape places points automatically

### Step 3: Create Fit Point Spline

1. **Fit Point Spline** tool
2. **Click all points** in order from throat to mouth
3. **Check:**
   - Curve is smooth
   - No kinks at middle junction
   - Passes through all points

### Step 4: Add Centerline and Revolve

1. **Line** → Draw horizontal centerline
2. **Revolve** → Select spline profile
3. **Axis:** Centerline
4. **Angle:** 360°

---

## Method 3: Two Separate Splines with Tangency (If Method 2 Fails)

If the single spline creates weird artifacts, split it at the middle:

### Step 1: Create Two Sets of Points

**Spline 1 (Throat to Middle):**
- Use points from x=0 to x=204.3 (first 50 points)
- End at (204.3, 57.87)

**Spline 2 (Middle to Mouth):**
- Use points from x=204.3 to x=418 (last 50 points)
- Start at (204.3, 57.87)

### Step 2: Create Splines

1. **Fit Point Spline** → Through first 50 points
2. **Fit Point Spline** → Through last 50 points
3. Both should meet at (204.3, 57.87)

### Step 3: Add Tangency Constraint

1. **Select both splines**
2. **Add constraint → Tangent** (or Collinear if that's not available)
3. **Select the shared endpoint** (middle)
4. This ensures smooth transition

### Step 4: Revolve

Same as before - revolve both profiles together.

---

## Onshape-Specific Tips

### Sketch Relations

**At throat (start):**
- Add **Horizontal** relation to the first spline point
- This ensures dr/dx = 0 (purely axial)

**At middle (junction):**
- Select both spline endpoints
- **Merge** or **Coincident** constraint
- Add **Tangent** or **Curvature continuity** if available

### Verification

**Use Measure Tool:**

1. **Measure** → Select curve at key x-locations
2. **Verify:**
   - x=0: r=13.36 ±0.1
   - x=204.3: r=57.87 ±0.5 ← **Most critical**
   - x=418: r=134.06 ±1.0

**Add construction points at these locations** to verify easily.

### Shell and Wall Thickness

**Recommended approach:**

1. **Revolve** creates solid
2. **Shell** → Select:
   - Mouth face (remove - leave open)
   - Throat face (remove - for driver mounting)
3. **Thickness:** 10-15 mm

**Alternative:**
- Sketch offset curve outward by 10 mm
- Revolve as surface
- Thicken to solid

### Adding Mounting Features

**Throat Mount:**
1. **Extrude** from throat face
2. **Thickness:** 15 mm
3. **Hole Pattern** → Match BC_DE250 bolt pattern

**Mouth Flange:**
1. **Extrude** from mouth edge
2. **Width:** 20-25 mm
3. **Bolt holes** → For mounting to enclosure

---

## Common Onshape Issues and Solutions

### Issue: Spline has weird waves

**Cause:** Too many control points causing oscillation

**Solution:**
- Use **Fit Point Spline** not **Control Point Spline**
- Or reduce points: use every 5th point from CSV

### Issue: Can't import CSV

**Workaround:**
1. Open CSV in text editor
2. Copy x,y columns (skip header)
3. Paste into Onshape sketch
4. Points created automatically

### Issue: Revolve fails

**Cause:** Curve is not closed or doesn't touch axis

**Solution:**
1. Add **Line** from curve end to axis
2. Or add **Point** on axis at throat (0, 0)
3. Connect spline to this point

### Issue: Shell fails

**Cause:** Wall too thin or complex geometry

**Solution:**
1. Increase shell thickness to 15 mm
2. Or use **Thicken** instead of Shell
3. Or add walls manually (offset sketch)

---

## Complete Onshape Workflow (Recommended)

```
1. Convert CSV → Onshape format (x, y, z)
2. Import as curve (Features → Import)
3. New Sketch → Project curve
4. Draw centerline
5. Revolve sketch profile 360°
6. Shell (remove mouth and throat faces)
7. Add mounting flanges (extrude)
8. Export STL for 3D printing (if applicable)
```

---

## Keyboard Shortcuts (Onshape)

- **C**: Circle
- **L**: Line
- **S:** Spline
- **Q:** Smart Dimension
- **Shift + Click:** Multiple select
- **Ctrl + Z:** Undo
- **Escape:** Exit current tool

---

## Export for Manufacturing

**3D Printing:**
1. Right-click Part Studio → Export
2. Format: STL
3. Resolution: Fine (0.1-0.2 mm)

**CNC Machining:**
1. Export as STEP or IGES
2. Import into CAM software (Fusion 360, Mastercam)
3. Setup roughing/finishing operations

**Templates for hand building:**
1. Create drawing → Export PDF
2. Print at 100% scale
3. Use as template for cutting material

---

## Video Walkthrough Summary

1. **Import CSV** (2 min)
2. **Project to sketch** (1 min)
3. **Revolve to solid** (1 min)
4. **Shell hollow** (1 min)
5. **Add mounting features** (3 min)

**Total time:** ~8-10 minutes for complete CAD model

---

## Next Steps After CAD

1. **Verify dimensions** against optimization targets
2. **Add assembly features** (driver mounting, enclosure mounting)
3. **Create drawing** for fabrication
4. **Export** for manufacturing (STL for print, STEP for CNC)

---

## Files Reference

- **Profile data:** `tasks/results/DE250_horn_profile.csv`
- **Design JSON:** `tasks/results/DE250_8NDL51_two_way_design.json`
- **Dimensions:** `docs/designs/DE250_horn_CAD_dimensions.md`
- **This guide:** `docs/designs/DE250_horn_CAD_onshape_guide.md`

---

**Pro Tip:** Use Onshape's "Version history" to save different iterations (e.g., "v1 - Single spline", "v2 - Two splines") so you can compare and revert if needed.
