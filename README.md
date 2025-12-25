# Viberesp

> **Loudspeaker enclosure design and driver database tool**

Viberesp is a Python tool for managing loudspeaker driver databases and exporting enclosure parameters to Hornresp format.

## Features

- **Driver Database**: Add, list, and manage loudspeaker drivers with Thiele-Small parameters
- **Hornresp Export**: Generate Hornresp-compatible parameter files for various enclosure types
- **Statistics**: View database statistics and driver parameter ranges

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/viberesp.git
cd viberesp

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev,docs]"
```

## Usage

### Driver Database

```bash
# Add a driver
viberesp driver add 18DS115 \
    --manufacturer "B&C" \
    --model "18DS115" \
    --fs 32 \
    --vas 158 \
    --qes 0.38 \
    --qms 6.52 \
    --sd 1210 \
    --re 5.0 \
    --bl 39.0 \
    --xmax 16.5 \
    --mms 330 \
    --cms 0.0824 \
    --rms 14.72

# List all drivers
viberesp driver list

# Show driver details
viberesp driver show 18DS115

# Remove a driver
viberesp driver remove 18DS115

# Export drivers to JSON
viberesp driver export drivers_backup.json

# Import drivers from JSON
viberesp driver import drivers_backup.json

# Show database statistics
viberesp stats
```

### Export to Hornresp

```bash
# Export sealed enclosure parameters
viberesp export hornresp 18DS115 -e sealed \
    --volume 50 \
    --output sealed_design.txt

# Export exponential horn parameters
viberesp export hornresp 18DS115 -e exponential_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --output horn_design.txt

# Export front-loaded horn with comment
viberesp export hornresp 18DS115 -e front_loaded_horn \
    --throat-area 500 \
    --mouth-area 4800 \
    --horn-length 200 \
    --cutoff 36 \
    --rear-chamber 100 \
    --front-chamber 6 \
    --output f118_design.txt \
    --comment "F118-style front-loaded horn"
```

The exported Hornresp parameter file can be loaded into Hornresp for detailed acoustic simulation.

## Thiele-Small Parameters

Viberesp uses the standard Thiele-Small parameters:

| Parameter | Description | Units |
|-----------|-------------|-------|
| Fs | Free-air resonance frequency | Hz |
| Vas | Equivalent compliance volume | L |
| Qes | Electrical Q factor | - |
| Qms | Mechanical Q factor | - |
| Qts | Total Q factor | - |
| Sd | Effective diaphragm area | m² |
| Re | Voice coil DC resistance | Ω |
| Bl | Force factor (magnetic field × coil length) | T·m |
| Xmax | Maximum linear excursion | mm |
| Mms | Moving mass | g |
| Cms | Mechanical compliance | m/N |
| Rms | Mechanical resistance | N·s/m |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev,docs]"

# Format code
black src/

# Sort imports
isort src/

# Type check
mypy src/

# Run tests
pytest tests/ -v
```

## Enclosure Types Supported for Export

- **Sealed**: Acoustic suspension enclosures
- **Ported**: Bass reflex enclosures
- **Exponential Horn**: Horn with exponential flare profile
- **Front-Loaded Horn**: Horn with front and rear chambers

## License

MIT License - see LICENSE file for details.

## References

- Hornresp by David McBean: http://www.hornresp.net/
- Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
- Small, R.H. (1972). "Direct Radiator Loudspeaker System Analysis"
