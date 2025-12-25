# Reference Driver Definitions

Three standard drivers for Hornresp validation testing.

## Driver A: Generic 12-inch Woofer

**Application**: Bass Horn Testing

| Parameter | Value | Unit |
|-----------|-------|------|
| Sd | 507 | cm² |
| Re | 6.5 | Ω |
| Bl | 12.0 | T·m |
| Mmd | 85 | g |
| Cms | 0.35 | mm/N |
| Rms | 4.5 | Ns/m |
| Le | 1.2 | mH |
| fs | 29.2 | Hz |
| Qms | 5.47 | |
| Qes | 0.42 | |
| Qts | 0.39 | |
| Vas | 198 | L |

## Driver B: Generic 8-inch Midrange

**Application**: Midbass Horn Testing

| Parameter | Value | Unit |
|-----------|-------|------|
| Sd | 220 | cm² |
| Re | 5.6 | Ω |
| Bl | 8.5 | T·m |
| Mmd | 18 | g |
| Cms | 0.85 | mm/N |
| Rms | 1.8 | Ns/m |
| Le | 0.6 | mH |
| fs | 40.8 | Hz |
| Qms | 4.08 | |
| Qes | 0.55 | |
| Qts | 0.49 | |
| Vas | 45 | L |

## Driver C: Generic 15-inch Pro Woofer

**Application**: High-Output Bass Horn Testing

| Parameter | Value | Unit |
|-----------|-------|------|
| Sd | 855 | cm² |
| Re | 5.2 | Ω |
| Bl | 18.5 | T·m |
| Mmd | 145 | g |
| Cms | 0.22 | mm/N |
| Rms | 8.0 | Ns/m |
| Le | 1.8 | mH |
| fs | 28.1 | Hz |
| Qms | 3.21 | |
| Qes | 0.28 | |
| Qts | 0.26 | |
| Vas | 285 | L |

## Usage

Load these drivers in test cases:

```python
import json

with open('planning/test_cases/drivers/driver_a.json') as f:
    driver = json.load(f)

params = {
    'Sd': driver['thiele_small']['Sd'],
    'Re': driver['thiele_small']['Re'],
    # ... etc
}
```
