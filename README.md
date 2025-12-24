# Viberesp

Loudspeaker enclosure design and optimization using Thiele-Small parameters.

## Features

- **Driver Database**: Manage loudspeaker drivers with Thiele-Small parameters
- **Enclosure Simulation**: Accurate frequency response modeling for:
  - Sealed enclosures
  - Ported (bass reflex) enclosures (coming soon)
  - Passive radiator enclosures (coming soon)
  - Transmission line enclosures (coming soon)
  - Bandpass enclosures (coming soon)
  - Tapped horn enclosures (coming soon)
- **Multi-Objective Optimization**: Find optimal enclosure parameters using genetic algorithms (coming soon)
- **FRD/ZMA File Support**: Import measurement data
- **Visualization**: Frequency response plots and performance metrics

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/viberesp.git
cd viberesp

# Install in development mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[dev,docs]"
```

## Quick Start

### Add a Driver

```bash
viberesp driver add my-woofer \
    --manufacturer "Example Audio" \
    --model "W10-200" \
    --fs 35 \
    --vas 80 \
    --qes 0.4 \
    --qms 3.5 \
    --sd 350 \
    --re 6.5 \
    --bl 8.5 \
    --xmax 15 \
    --type woofer
```

### List Drivers

```bash
viberesp driver list
viberesp driver list --manufacturer "Example Audio"
viberesp driver show my-woofer
```

### Simulate Enclosure

```bash
# Sealed enclosure simulation
viberesp simulate my-woofer sealed --volume 50 --plot

# Save results
viberesp simulate my-woofer sealed --volume 50 --output results.json --export-plot response.png
```

### Scan Multiple Volumes

```bash
viberesp scan my-woofer --min-vb 20 --max-vb 100 --steps 10
```

## Thiele-Small Parameters

Viberesp uses the standard Thiele-Small parameters to characterize loudspeaker drivers:

| Parameter | Description | Units |
|-----------|-------------|-------|
| Fs | Free-air resonance frequency | Hz |
| Vas | Equivalent compliance volume | L |
| Qes | Electrical Q factor | - |
| Qms | Mechanical Q factor | - |
| Qts | Total Q factor (Qts = Qes × Qms / (Qes + Qms)) | - |
| Sd | Effective diaphragm area | m² |
| Re | Voice coil DC resistance | Ω |
| Bl | Force factor (magnetic field × coil length) | T·m |
| Xmax | Maximum linear excursion | mm |
| Mms | Moving mass | g |

## Python API

```python
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.sealed import SealedEnclosure
from viberesp.simulation.frequency_response import FrequencyResponseSimulator

# Define driver
driver = ThieleSmallParameters(
    fs=35.0,
    vas=80.0,
    qes=0.4,
    qms=3.5,
    sd=0.035,  # 350 cm²
    re=6.5,
    bl=8.5,
    xmax=15.0
)

# Create sealed enclosure
params = EnclosureParameters(
    enclosure_type="sealed",
    vb=50.0  # 50 liters
)

enclosure = SealedEnclosure(driver, params)

# Simulate
simulator = FrequencyResponseSimulator(enclosure)
response = simulator.calculate_response()
metrics = simulator.calculate_metrics(response)

print(f"F3: {metrics['f3']:.1f} Hz")
print(f"Sensitivity: {metrics['sensitivity_db']:.1f} dB")
```

## Enclosure Types

### Sealed (Acoustic Suspension)

- Simplest design
- 2nd-order high-pass response
- Tight, accurate bass
- Lower efficiency
- Requires larger box for low F3

### Ported (Bass Reflex)

- Extended low-frequency response
- 4th-order high-pass response
- Higher efficiency
- More complex design
- Port tuning critical

### Passive Radiator

- Similar to ported but uses passive cone instead of port
- No port noise issues
- Typically more expensive

### Transmission Line

- Quarter-wave resonator
- Extended bass with small footprint
- Complex design and construction

### Bandpass

- 4th/6th/8th order filtering
- High efficiency in passband
- Narrow bandwidth
- Complex design

## Optimization (Coming Soon)

Multi-objective optimization will balance:
- Frequency response flatness
- Bass extension (F3)
- Efficiency (SPL)
- Box size

```bash
viberesp optimize my-woofer sealed \
    --max-volume 100 \
    --bass-weight 1.5 \
    --flatness-weight 1.0 \
    --generations 200
```

## License

MIT License - see LICENSE file for details.

## References

- Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
- Small, R.H. (1972). "Direct Radiator Loudspeaker System Analysis"
- Hornresp Manual by David McBean
- [Thiele-Small Parameters (Wikipedia)](https://en.wikipedia.org/wiki/Thiele/Small_parameters)
