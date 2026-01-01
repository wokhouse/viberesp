# DXF Import Guide for Onshape

**File:** `tasks/results/DE250_horn_profile.dxf`
**Format:** DXF R12 (widely compatible)
**Content:** 100-point horn profile polyline + centerline

---

## Importing DXF into Onshape

### Method 1: Direct Import to Part Studio

1. **Open your Onshape document**
2. **Create new Part Studio**
3. **Click "Import"** (or right-click in graphics area → Import)
4. **Select file:** `DE250_horn_profile.dxf`
5. **Options:**
   - Units: Millimeters (should auto-detect)
   - Import to: New sketch or new part

**Result:** Sketch with polyline and centerline

### Method 2: Import to Sketch

1. **New Sketch** → Select plane (Front or Right)
2. **Sketch toolbar → "Insert"** (or "Import DXF")
3. **Select file:** `DE250_horn_profile.dxf`
4. **Options:**
   - Scale: 1.0
   - Units: mm

**Result:** Sketch entities you can edit

---

## Post-Import Steps

### 1. Convert Polyline to Spline (Recommended)

**Why:** The DXF imports as a POLYLINE (straight segments). For smooth horn:

1. **Select the imported polyline**
2. **Right-click → Convert to spline** (if available)
3. Or: **Delete polyline** and **create new Fit Point Spline** through the vertices

### Alternative: Use Polyline Directly

- 100 points = 4.2 mm spacing
- Already quite smooth for most purposes
- Can revolve directly without conversion

### 2. Verify Profile

**Measure key points:**
- Throat: x=0, y=13.36 mm
- Middle: x=204.3, y=57.87 mm ← **Critical**
- Mouth: x=418, y=134.06 mm

### 3. Revolve to 3D

1. **Select profile curve**
2. **Revolve tool**
3. **Axis:** Centerline (included in DXF)
4. **Angle:** 360°
5. **Confirm**

### 4. Shell (Make Hollow)

1. **Shell feature**
2. **Remove faces:** Mouth and throat
3. **Thickness:** 10-15 mm

---

## DXF File Contents

**Entities included:**
- ✅ Horn profile (100 points as POLYLINE)
- ✅ Centerline (reference for revolution)
- ✅ Text annotations (title, notes)

**Layer:** All entities on layer "0" (default)

**Units:** Millimeters

**Size:** ~418 mm long × ~270 mm tall

---

## Troubleshooting

### Issue: DXF won't import

**Solution 1:**
- Check file size (should be ~4.2 KB)
- Re-export if needed

**Solution 2:**
- Open in AutoCAD/LibreCAD first
- Save as DXF R12 or R2000
- Then import to Onshape

### Issue: Profile looks jagged

**Cause:** Polyline with straight segments

**Solution:**
1. Select polyline → Convert to spline
2. Or use higher point count (re-export from Python)

### Issue: Wrong scale

**Check:**
- Throat radius should be 13.36 mm
- Total length should be 418 mm

**Fix:**
- If too small: Import again with correct units (mm)
- If too large: Check scaling factor in import dialog

### Issue: Can't revolve

**Cause:** Profile doesn't form closed region or touch axis

**Solution:**
1. Add line from profile end to axis
2. Or use "Surface revolve" instead of "Solid revolve"
3. Then thicken surface

---

## Alternative Export Formats

If DXF doesn't work well, try these:

### CSV (Already created)
- File: `DE250_horn_onshape.csv`
- Import as: CSV points or curve

### JSON
- File: `DE250_8NDL51_two_way_design.json`
- Contains all optimized parameters
- Recreate profile manually in CAD

### STEP (Coming soon)
- Can export from Onshape after creating model
- Use for manufacturing/CNC

---

## Verification Checklist

After importing DXF:

- [ ] Throat radius: 13.36 ± 0.1 mm
- [ ] Middle radius: 57.87 ± 0.5 mm at x=204.3 mm
- [ ] Mouth radius: 134.06 ± 1.0 mm at x=418 mm
- [ ] Total length: 418 mm
- [ ] Centerline present (for revolution reference)
- [ ] Profile is smooth (no kinks)

---

## Next Steps

1. **Import DXF** into Onshape
2. **Convert to spline** (optional but recommended)
3. **Revolve** to create 3D solid
4. **Shell** to create hollow horn
5. **Add mounting features** (flanges, bolt holes)
6. **Export** for manufacturing (STL for 3D print, STEP for CNC)

---

## File Locations

**DXF file:** `tasks/results/DE250_horn_profile.dxf`
**CSV file:** `tasks/results/DE250_horn_onshape.csv`
**Full design:** `tasks/results/DE250_8NDL51_two_way_design.json`
**CAD guide:** `docs/designs/DE250_horn_CAD_onshape_guide.md`

---

**Quick test:** Open DXF in a viewer first (LibreCAD, DWG TrueView, etc.) to verify it looks correct before importing to Onshape.
