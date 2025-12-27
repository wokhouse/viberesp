# BC_8NDL51 Ported Box Validation - 2.5" Port

**Driver:** B&C 8NDL51-8 8" Midrange
**Alignment:** B4 Butterworth (maximally flat)
**Box Volume:** 31.65 L
**Tuning Frequency:** 65.3 Hz
**Port:** 2.5" diameter × 4.29 cm length

## Validation Steps

### 1. Import into Hornresp

1. Open Hornresp
2. File → Open
3. Navigate to this directory
4. Open `BC_8NDL51_ported_2.5in.txt`

### 2. Verify Parameters

Check that the following parameters are correctly loaded:

**Driver Parameters:**
- Sd = 220.00 cm²
- Bl = 7.30 T·m
- Cms = 1.50E-04 m/N
- Rms = 2.44 N·s/m
- Mmd = 26.286 g
- Le = 0.150 mH
- Re = 2.60 Ω

**Enclosure Parameters:**
- Ang = 0.5 x Pi (hemisphere radiation)
- Vrc = 31.65 L (rear chamber volume)
- Fr = 65.30 Hz (port tuning frequency)
- Ap = 31.67 cm² (port area)
- Lpt = 4.29 cm (port length)

### 3. Run Simulation

1. Tools → Loudspeaker Wizard
2. Accept default settings (or configure as desired)
3. Click "Calculate" to generate response

### 4. Export Results

1. File → Save As
2. Save as `sim.txt` in this directory
3. This file contains impedance, SPL, and other response data

### 5. Compare with Viberesp

Use the viberesp validation framework:

```bash
viberesp validate compare BC_8NDL51 ported/Vb31.6L_Fb65.3Hz_2.5in
```

Expected tolerances:
- Fb: ±0.5 Hz
- Vb: ±0.5 L
- Port length: ±0.5 cm
- Ze magnitude: <5% general, <10% near peaks
- Ze phase: <10° general, <15° near peaks

## System Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| α | 0.319 | Compliance ratio (Vas/Vb) |
| h | 0.871 | Tuning ratio (Fb/Fs) |
| Qtc | 0.707 | System total Q (Butterworth) |
| F3 | 65.3 Hz | -3dB frequency (equals Fb for B4) |

## Alignment Classification

**Butterworth B4 (maximally flat) ✓**

This alignment provides maximally flat amplitude response in the passband
with no peaking. The -3dB frequency occurs exactly at the port tuning
frequency (F3 = Fb).

## Literature

- Thiele (1971) - "Loudspeakers in Vented Boxes" Parts 1 & 2
- Small (1972) - Closed-Box Loudspeaker Systems Part I
- `literature/thiele_small/thiele_1971_vented_boxes.md`
