# Viberesp

> **Loudspeaker enclosure design tool - Physics model rewrite in progress**

⚠️ **This codebase is currently undergoing a complete physics model rewrite. The simulation features are non-functional.**

## Status

The Viberesp physics model and simulation engine are being completely rewritten due to fundamental errors discovered in the initial implementation assumptions.

**What Works:**
- ✅ Driver database management (`viberesp driver add/list/show/remove`)
- ✅ Export parameters to Hornresp format (`viberesp export hornresp`)

**What Doesn't Work:**
- ❌ Enclosure simulation (`viberesp simulate`)
- ❌ Parameter sweeps (`viberesp scan`)
- ❌ Validation against Hornresp (`viberesp validate`)

## What Remains

The codebase retains the infrastructure scaffolding for the rewrite:

- **Core Models**: Pydantic models for Thiele-Small parameters
- **CLI Framework**: Click-based command structure
- **Driver Database**: JSON-based driver management
- **Hornresp Exporter**: Export enclosure parameters to Hornresp format
- **Testing Structure**: Pytest framework (empty, ready for new tests)

## What Was Removed

The following have been completely removed for the rewrite:

- All enclosure implementations (sealed, horns, etc.)
- Frequency response simulator
- Hornresp validation code (parser, comparison, metrics, plotting)
- Literature documentation and research notes
- All test fixtures and baseline metrics

See `REWRITE_NOTES.md` for detailed information about the cleanup.

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

## Usage (Working Features Only)

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
```

### Export to Hornresp

```bash
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

# Run tests (currently empty - will be repopulated after rewrite)
pytest tests/ -v
```

## Rewrite Roadmap

1. ✅ Clean up existing code (remove physics model, literature, fixtures)
2. ⏳ Design new physics model architecture
3. ⏳ Implement new simulation engine
4. ⏳ Rebuild enclosure implementations
5. ⏳ Create new test fixtures
6. ⏳ Add validation framework

## Contributing

The codebase is currently in a rewrite phase. Contributions are welcome but should focus on the new physics model architecture rather than trying to fix the old implementation (which has been removed).

## License

MIT License - see LICENSE file for details.

## References

- Hornresp by David McBean: http://www.hornresp.net/
- Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
- Small, R.H. (1972). "Direct Radiator Loudspeaker System Analysis"
