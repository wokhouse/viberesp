"""Viberesp CLI - Loudspeaker enclosure optimization tool."""

import click
import json
from pathlib import Path
import sys
import numpy as np

from viberesp.core.models import (
    ThieleSmallParameters,
    EnclosureParameters,
    EnclosureType,
    DriverType
)
from viberesp.enclosures.sealed import SealedEnclosure
from viberesp.enclosures.horns import ExponentialHorn
from viberesp.simulation.frequency_response import (
    FrequencyResponseSimulator,
    compare_enclosures
)
from viberesp.io.driver_db import DriverDatabase
from viberesp.io.frd_parser import FRDParser
from viberesp.utils.plotting import (
    check_matplotlib,
    plot_frequency_response,
    plot_multiple_responses
)
from viberesp.validation import (
    parse_hornresp_output,
    parse_hornresp_params,
    compare_responses,
    calculate_validation_metrics,
    plot_validation,
)

# Check matplotlib availability
MATPLOTLIB_AVAILABLE = check_matplotlib()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Viberesp: Loudspeaker enclosure optimization tool.

    Design and optimize speaker enclosures using Thiele-Small parameters
    and multi-objective optimization algorithms.
    """
    pass


# ========================================
# Driver Management Commands
# ========================================

@cli.group()
def driver():
    """Manage driver database."""
    pass


@driver.command()
@click.argument('name')
@click.option('--manufacturer', '-m', help='Manufacturer name')
@click.option('--model', '-M', help='Model number')
@click.option('--fs', type=float, required=True, help='Resonance frequency (Hz)')
@click.option('--vas', type=float, required=True, help='Equivalent compliance volume (L)')
@click.option('--qes', type=float, required=True, help='Electrical Q')
@click.option('--qms', type=float, required=True, help='Mechanical Q')
@click.option('--sd', type=float, required=True, help='Diaphragm area (cm²)')
@click.option('--re', type=float, required=True, help='Voice coil resistance (ohms)')
@click.option('--bl', type=float, required=True, help='Force factor (T*m)')
@click.option('--xmax', type=float, help='Max excursion (mm)')
@click.option('--le', type=float, help='Voice coil inductance (mH)')
@click.option('--mms', type=float, help='Moving mass (g)')
@click.option('--pe', type=float, help='Thermal power rating (W)')
@click.option('--type', 'driver_type', type=click.Choice(['woofer', 'midrange', 'tweeter', 'full_range', 'subwoofer']),
              help='Driver type')
def add(name, manufacturer, model, driver_type, **kwargs):
    """Add a new driver to the database."""
    try:
        # Build parameters dict
        params = {
            'manufacturer': manufacturer,
            'model_number': model,
            'driver_type': driver_type,
        }

        # Add T/S parameters (filter out None values)
        for key, value in kwargs.items():
            if value is not None:
                params[key] = value

        driver = ThieleSmallParameters(**params)

        # Add to database
        db = DriverDatabase()
        db.add_driver(name, driver)

        click.echo(f"✓ Added driver '{name}' to database")

        # Show calculated values
        click.echo(f"\nCalculated Parameters:")
        click.echo(f"  Qts: {driver.qts:.3f}")
        click.echo(f"  EBP: {driver.ebp:.1f}")
        click.echo(f"  Recommended: {driver.get_recommended_enclosure()}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@driver.command()
@click.option('--manufacturer', '-m', help='Filter by manufacturer')
@click.option('--min-fs', type=float, help='Minimum resonance frequency')
@click.option('--max-fs', type=float, help='Maximum resonance frequency')
@click.option('--min-qts', type=float, help='Minimum total Q')
@click.option('--max-qts', type=float, help='Maximum total Q')
@click.option('--enclosure', type=click.Choice(['sealed', 'ported', 'any']), help='Filter by enclosure recommendation')
def list(manufacturer, min_fs, max_fs, min_qts, max_qts, enclosure):
    """List all drivers in database."""
    db = DriverDatabase()

    # Convert enclosure filter
    enclosure_type = None if enclosure == 'any' else enclosure

    drivers = db.search_drivers(
        manufacturer=manufacturer,
        min_fs=min_fs,
        max_fs=max_fs,
        min_qts=min_qts,
        max_qts=max_qts,
        enclosure_type=enclosure_type
    )

    if not drivers:
        click.echo("No drivers found")
        return

    # Format header
    click.echo(f"\n{len(drivers)} driver(s) found:\n")
    click.echo("{:<30} {:<20} {:>10} {:>10} {:>10} {:>15}".format(
        "Name", "Manufacturer", "Fs (Hz)", "Vas (L)", "Qts", "Recommended"
    ))
    click.echo("-" * 100)

    for name, driver in drivers.items():
        qts = driver.qts
        rec = driver.get_recommended_enclosure()

        click.echo("{:<30} {:<20} {:>10.1f} {:>10.1f} {:>10.3f} {:>15}".format(
            name,
            driver.manufacturer or '-',
            driver.fs,
            driver.vas,
            qts,
            rec
        ))


@driver.command()
@click.argument('name')
@click.option('--json', 'as_json', is_flag=True, help='Output as JSON')
def show(name, as_json):
    """Show detailed driver information."""
    db = DriverDatabase()
    driver = db.get_driver(name)

    if driver is None:
        click.echo(f"✗ Driver '{name}' not found", err=True)
        raise click.Abort()

    if as_json:
        data = driver.model_dump_with_derived()
        click.echo(json.dumps(data, indent=2))
        return

    # Display formatted output
    qts = driver.qts

    click.echo(f"\n{'='*60}")
    click.echo(f"Driver: {name}")
    if driver.manufacturer:
        click.echo(f"Manufacturer: {driver.manufacturer}")
    if driver.model_number:
        click.echo(f"Model: {driver.model_number}")
    click.echo(f"{'='*60}\n")

    click.echo("Thiele-Small Parameters:")
    click.echo(f"  Fs (resonance freq):    {driver.fs:.2f} Hz")
    click.echo(f"  Vas (compliance):       {driver.vas:.2f} L")
    click.echo(f"  Qes (electrical Q):     {driver.qes:.3f}")
    click.echo(f"  Qms (mechanical Q):     {driver.qms:.3f}")
    click.echo(f"  Qts (total Q):          {qts:.3f}")
    click.echo(f"  Sd (diaphragm area):    {driver.sd*10000:.1f} cm²")
    click.echo(f"  Re (DC resistance):     {driver.re:.2f} Ω")
    click.echo(f"  Bl (force factor):      {driver.bl:.2f} T*m")

    if driver.xmax:
        click.echo(f"  Xmax (max excursion):   {driver.xmax:.1f} mm")
        if driver.vd:
            click.echo(f"  Vd (displacement):      {driver.vd:.2f} L")
    if driver.le:
        click.echo(f"  Le (inductance):        {driver.le:.2f} mH")
    if driver.mms:
        click.echo(f"  Mms (moving mass):      {driver.mms:.1f} g")
    if driver.pe:
        click.echo(f"  Pe (power handling):    {driver.pe:.1f} W")

    click.echo(f"\nCalculated:")
    click.echo(f"  EBP: {driver.ebp:.1f}")
    click.echo(f"  Recommended enclosure: {driver.get_recommended_enclosure()}")


@driver.command()
@click.argument('name')
def remove(name):
    """Remove a driver from the database."""
    db = DriverDatabase()

    if db.remove_driver(name):
        click.echo(f"✓ Removed driver '{name}' from database")
    else:
        click.echo(f"✗ Driver '{name}' not found", err=True)
        raise click.Abort()


@driver.command()
@click.argument('output_path')
def export(output_path):
    """Export all drivers to a JSON file."""
    db = DriverDatabase()
    db.export_drivers(output_path)
    count = len(db.list_drivers())
    click.echo(f"✓ Exported {count} driver(s) to {output_path}")


@driver.command()
@click.argument('input_path')
@click.option('--overwrite', is_flag=True, help='Overwrite existing drivers')
def import_cmd(input_path, overwrite):
    """Import drivers from a JSON file."""
    db = DriverDatabase()
    count = db.import_drivers(input_path, overwrite=overwrite)
    click.echo(f"✓ Imported {count} driver(s) from {input_path}")


# ========================================
# Simulation Commands
# ========================================

@cli.command()
@click.argument('driver_name')
@click.argument('enclosure_type', type=click.Choice(['sealed', 'ported', 'exponential_horn']))
@click.option('--volume', '-v', type=float, required=False, help='Box volume (L) [required for sealed/ported]')
@click.option('--depth', '-d', type=float, help='Enclosure internal depth (cm)')
@click.option('--tuning', '-f', type=float, help='Port tuning frequency (Hz) [for ported]')
@click.option('--port-diameter', '-D', type=float, help='Port diameter (cm) [for ported]')
@click.option('--num-ports', '-n', type=int, default=1, help='Number of ports')
@click.option('--throat-area', type=float, help='Throat area (cm²) [for horns]')
@click.option('--mouth-area', type=float, help='Mouth area (cm²) [for horns]')
@click.option('--horn-length', type=float, help='Horn length (cm) [for horns]')
@click.option('--flare-rate', type=float, help='Exponential flare rate m (1/m) [for horns]')
@click.option('--cutoff', '-fc', type=float, help='Horn cutoff frequency (Hz) [for horns]')
@click.option('--rear-chamber', type=float, help='Rear chamber volume (L) [for horns]')
@click.option('--output', '-o', type=click.Path(), help='Save results to JSON file')
@click.option('--plot', '-p', is_flag=True, help='Show frequency response plot')
@click.option('--export-plot', type=click.Path(), help='Save plot to file')
def simulate(driver_name, enclosure_type, volume, **kwargs):
    """Simulate enclosure frequency response."""
    # Load driver
    db = DriverDatabase()
    driver = db.get_driver(driver_name)

    if driver is None:
        click.echo(f"✗ Driver '{driver_name}' not found", err=True)
        click.echo("Available drivers:")
        for name in db.list_drivers():
            click.echo(f"  - {name}")
        raise click.Abort()

    # Validate required parameters based on enclosure type
    if enclosure_type in ['sealed', 'ported'] and volume is None:
        click.echo(f"✗ --volume required for {enclosure_type} enclosures", err=True)
        raise click.Abort()

    if enclosure_type == 'ported':
        tuning = kwargs.get('tuning')
        if tuning is None:
            click.echo("✗ --tuning required for ported enclosures", err=True)
            raise click.Abort()

    if enclosure_type == 'exponential_horn':
        # Check required horn parameters
        throat_area = kwargs.get('throat_area')
        mouth_area = kwargs.get('mouth_area')
        horn_length = kwargs.get('horn_length')

        if throat_area is None:
            click.echo("✗ --throat-area required for horn enclosures", err=True)
            raise click.Abort()
        if mouth_area is None:
            click.echo("✗ --mouth-area required for horn enclosures", err=True)
            raise click.Abort()
        if horn_length is None:
            click.echo("✗ --horn-length required for horn enclosures", err=True)
            raise click.Abort()

    # Create enclosure parameters
    params_dict = {
        'enclosure_type': enclosure_type,
        'vb': volume if volume is not None else 0.0,
    }

    # Add depth if provided
    depth = kwargs.get('depth')
    if depth is not None:
        params_dict['depth_cm'] = depth

    # Ported enclosure parameters
    if enclosure_type == 'ported':
        params_dict['fb'] = kwargs.get('tuning')
        params_dict['port_diameter'] = kwargs.get('port_diameter')
        params_dict['number_of_ports'] = kwargs.get('num_ports', 1)

    # Horn enclosure parameters
    if enclosure_type == 'exponential_horn':
        params_dict['throat_area_cm2'] = kwargs.get('throat_area')
        params_dict['mouth_area_cm2'] = kwargs.get('mouth_area')
        params_dict['horn_length_cm'] = kwargs.get('horn_length')
        params_dict['flare_rate'] = kwargs.get('flare_rate')
        params_dict['cutoff_frequency'] = kwargs.get('cutoff')
        params_dict['rear_chamber_volume'] = kwargs.get('rear_chamber')

    try:
        enclosure_params = EnclosureParameters(**params_dict)
    except Exception as e:
        click.echo(f"✗ Invalid enclosure parameters: {e}", err=True)
        raise click.Abort()

    # Create enclosure instance
    if enclosure_type == 'sealed':
        enclosure = SealedEnclosure(driver, enclosure_params)
    elif enclosure_type == 'exponential_horn':
        enclosure = ExponentialHorn(driver, enclosure_params)
    else:
        click.echo(f"✗ Enclosure type '{enclosure_type}' not yet implemented", err=True)
        raise click.Abort()

    # Simulate
    simulator = FrequencyResponseSimulator(enclosure)
    response = simulator.calculate_response()
    metrics = simulator.calculate_metrics(response)

    # Display results
    click.echo(f"\n{enclosure_type.replace('_', ' ').title()} Enclosure Simulation")
    click.echo(f"Driver: {driver_name}")

    # Show enclosure-specific parameters
    if enclosure_type == 'exponential_horn':
        throat_area = kwargs.get('throat_area')
        mouth_area = kwargs.get('mouth_area')
        horn_length = kwargs.get('horn_length')
        flare_rate = kwargs.get('flare_rate')
        cutoff = kwargs.get('cutoff')
        rear_chamber = kwargs.get('rear_chamber')

        click.echo(f"Throat Area: {throat_area:.1f} cm²")
        click.echo(f"Mouth Area: {mouth_area:.1f} cm²")
        click.echo(f"Horn Length: {horn_length:.1f} cm")
        if flare_rate:
            click.echo(f"Flare Rate: {flare_rate:.2f} m⁻¹")
        if cutoff:
            click.echo(f"Cutoff Frequency: {cutoff:.1f} Hz")
        if rear_chamber:
            click.echo(f"Rear Chamber: {rear_chamber:.1f} L")
    else:
        click.echo(f"Volume: {volume:.1f} L")
        if depth is not None:
            click.echo(f"Depth: {depth:.1f} cm")
            # Calculate approximate front panel area
            # Area (cm²) = Volume (L) × 1000 / depth (cm)
            front_area_cm2 = (volume * 1000) / depth
            side_length_cm = np.sqrt(front_area_cm2)
            click.echo(f"  → Front panel area: ~{front_area_cm2:.0f} cm²")
            click.echo(f"  → If square: ~{side_length_cm:.1f} × {side_length_cm:.1f} cm")

    if enclosure_type == 'ported' and kwargs.get('tuning'):
        click.echo(f"Tuning: {kwargs.get('tuning'):.1f} Hz")

    click.echo(f"\nPerformance Metrics:")
    click.echo(f"  F3 (-3dB):      {metrics['f3']:.1f} Hz")
    click.echo(f"  F10 (-10dB):    {metrics['f10']:.1f} Hz")
    click.echo(f"  Passband Ripple: {metrics['passband_ripple_db']:.2f} dB")
    click.echo(f"  Sensitivity:    {metrics['sensitivity_db']:.1f} dB (1W/1m)")
    click.echo(f"  Bandwidth:      {metrics['bandwidth_octaves']:.1f} octaves")

    # Save to JSON
    output = kwargs.get('output')
    if output:
        result_data = simulator.to_dict()
        result_data['driver'] = driver_name
        result_data['enclosure'] = enclosure_type
        result_data['parameters'] = params_dict

        with open(output, 'w') as f:
            json.dump(result_data, f, indent=2)

        click.echo(f"\n✓ Results saved to {output}")

    # Plot
    if kwargs.get('plot') or kwargs.get('export_plot'):
        if not MATPLOTLIB_AVAILABLE:
            click.echo("✗ Matplotlib not available for plotting", err=True)
            return

        plot_frequency_response(
            response['frequency'],
            response['spl_db'],
            f3=metrics['f3'],
            f10=metrics['f10'],
            title=f"{enclosure_type.title()} Enclosure - {driver_name}",
            show=kwargs.get('plot', False),
            save_path=kwargs.get('export_plot')
        )


@cli.command()
@click.argument('driver_name')
@click.option('--min-vb', type=float, default=10, help='Minimum box volume (L)')
@click.option('--max-vb', type=float, default=100, help='Maximum box volume (L)')
@click.option('--steps', '-n', type=int, default=5, help='Number of volumes to test')
def scan(driver_name, min_vb, max_vb, steps):
    """Scan multiple box volumes and compare performance."""
    # Load driver
    db = DriverDatabase()
    driver = db.get_driver(driver_name)

    if driver is None:
        click.echo(f"✗ Driver '{driver_name}' not found", err=True)
        raise click.Abort()

    # Generate volume range
    volumes = np.linspace(min_vb, max_vb, steps)
    results = []

    for vb in volumes:
        params = EnclosureParameters(
            enclosure_type=EnclosureType.SEALED,
            vb=vb
        )

        enclosure = SealedEnclosure(driver, params)
        simulator = FrequencyResponseSimulator(enclosure)
        response = simulator.calculate_response()
        metrics = simulator.calculate_metrics(response)

        results.append({
            'vb': vb,
            'f3': metrics['f3'],
            'sensitivity': metrics['sensitivity_db'],
            'qtc': enclosure.calculate_system_q()
        })

    # Display results
    click.echo(f"\nVolume Scan for {driver_name}:")
    click.echo("\n{:>10} {:>10} {:>12} {:>10}".format(
        "Volume (L)", "F3 (Hz)", "Sensitivity", "Qtc"
    ))
    click.echo("-" * 50)

    for r in results:
        click.echo("{:>10.1f} {:>10.1f} {:>12.1f} {:>10.3f}".format(
            r['vb'], r['f3'], r['sensitivity'], r['qtc']
        ))


@cli.command()
def stats():
    """Show driver database statistics."""
    db = DriverDatabase()
    stats = db.get_statistics()

    click.echo(f"\nDriver Database Statistics:")
    click.echo(f"  Total Drivers: {stats['total_drivers']}")

    if stats['manufacturers']:
        click.echo(f"\n  Manufacturers:")
        for mfr, count in sorted(stats['manufacturers'].items()):
            click.echo(f"    {mfr}: {count}")

    if stats['enclosure_recommendations']:
        click.echo(f"\n  Enclosure Recommendations:")
        for enc_type, count in stats['enclosure_recommendations'].items():
            click.echo(f"    {enc_type}: {count}")

    click.echo(f"\n  Parameter Ranges:")
    click.echo(f"    Fs: {stats['fs_range'][0]:.1f} - {stats['fs_range'][1]:.1f} Hz")
    click.echo(f"    Qts: {stats['qts_range'][0]:.3f} - {stats['qts_range'][1]:.3f}")
    click.echo(f"    Vas: {stats['vas_range'][0]:.1f} - {stats['vas_range'][1]:.1f} L")


# ========================================
# Validation Commands
# ========================================

@cli.group()
def validate():
    """Validate simulation output against reference tools."""
    pass


@validate.command('hornresp')
@click.argument('driver_name')
@click.argument('hornresp_file', type=click.Path(exists=True))
@click.option('--volume', '-v', type=float, required=True, help='Enclosure volume in liters')
@click.option('--freq-min', type=float, default=20, help='Minimum frequency for comparison (Hz)')
@click.option('--freq-max', type=float, default=500, help='Maximum frequency for comparison (Hz)')
@click.option('--params-file', type=click.Path(exists=True), help='Hornresp parameter file')
@click.option('--show-plot', is_flag=True, help='Display validation plot')
@click.option('--export-plot', type=click.Path(), help='Save plot to file')
@click.option('--output', '-o', type=click.Path(), help='Save metrics to JSON file')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def validate_hornresp(driver_name, hornresp_file, volume, freq_min, freq_max,
                      params_file, show_plot, export_plot, output, verbose):
    """Validate Viberesp simulation against Hornresp output.

    Compares Viberesp simulation results with Hornresp reference data
    for the same driver and enclosure configuration.

    Example:
        viberesp validate hornresp 12BG100 hornresp_output.txt --volume 40
    """
    try:
        # Load driver
        db = DriverDatabase()
        driver = db.get_driver(driver_name)

        if driver is None:
            click.echo(f"✗ Driver '{driver_name}' not found", err=True)
            raise click.Abort()

        # Parse Hornresp output
        click.echo(f"Parsing Hornresp output: {hornresp_file}")
        hornresp_data = parse_hornresp_output(hornresp_file)
        click.echo(f"  Loaded {len(hornresp_data)} frequency points")

        # Parse Hornresp parameters if provided
        if params_file:
            click.echo(f"Parsing Hornresp parameters: {params_file}")
            hornresp_params = parse_hornresp_params(params_file)
            if verbose:
                click.echo(f"  Sd: {hornresp_params.sd} cm²")
                click.echo(f"  Bl: {hornresp_params.bl}")
                click.echo(f"  Mmd: {hornresp_params.mmd} g")
                click.echo(f"  Vrc: {hornresp_params.vrc} L")

        # Create Viberesp enclosure
        enclosure_params = EnclosureParameters(
            enclosure_type='sealed',
            vb=volume,
        )
        enclosure = SealedEnclosure(driver, enclosure_params)

        # Calculate Viberesp response
        simulator = FrequencyResponseSimulator(enclosure)
        viberesp_response = simulator.calculate_response()

        # Convert to numpy arrays for comparison
        viberesp_freq = np.array(viberesp_response['frequency'])
        viberesp_spl = np.array(viberesp_response['spl_db'])

        # Get phase if available
        viberesp_phase = np.array(viberesp_response['phase_degrees']) if 'phase_degrees' in viberesp_response else None

        # Run comparison
        click.echo("Running comparison...")
        comparison = compare_responses(
            viberesp_freq=viberesp_freq,
            viberesp_spl=viberesp_spl,
            viberesp_phase=viberesp_phase,
            hornresp_freq=hornresp_data.frequencies,
            hornresp_spl=hornresp_data.spl,
            hornresp_phase=hornresp_data.phase,
            freq_min=freq_min,
            freq_max=freq_max,
        )

        # Calculate metrics
        metrics = calculate_validation_metrics(comparison)

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("Hornresp Validation Results")
        click.echo("=" * 60)
        click.echo(f"Driver: {driver_name}")
        click.echo(f"Volume: {volume:.1f} L")
        click.echo(f"Frequency Range: {freq_min}-{freq_max} Hz\n")

        click.echo(f"Overall Agreement: {metrics.agreement_score:.1f}%\n")

        click.echo("SPL Magnitude Errors:")
        click.echo(f"  RMSE: {metrics.rmse:.3f} dB")
        click.echo(f"  MAE:  {metrics.mae:.3f} dB")
        click.echo(f"  Max:  {metrics.max_error:.3f} dB @ {metrics.max_error_freq:.1f} Hz\n")

        click.echo("Band-Specific RMSE:")
        click.echo(f"  Passband (200-500Hz): {metrics.passband_rmse:.3f} dB")
        click.echo(f"  Bass (20-200Hz):      {metrics.bass_rmse:.3f} dB\n")

        if metrics.f3_viberesp and metrics.f3_hornresp:
            click.echo(f"F3 Frequency:")
            click.echo(f"  Viberesp:  {metrics.f3_viberesp:.2f} Hz")
            click.echo(f"  Hornresp:  {metrics.f3_hornresp:.2f} Hz")
            click.echo(f"  Error:     {metrics.f3_error:.2f} Hz\n")

        click.echo(f"Correlation: {metrics.correlation:.4f}")
        click.echo(f"Passband Offset Applied: {comparison.passband_offset:.3f} dB")

        if verbose:
            click.echo("\nDetailed Statistics:")
            click.echo(f"  Min difference: {np.nanmin(comparison.spl_difference):.3f} dB")
            click.echo(f"  Max difference: {np.nanmax(comparison.spl_difference):.3f} dB")
            click.echo(f"  Std deviation: {np.nanstd(comparison.spl_difference):.3f} dB")

        # Save metrics to JSON
        if output:
            result = {
                'driver': driver_name,
                'volume': volume,
                'frequency_range': {'min': freq_min, 'max': freq_max},
                'metrics': {
                    'agreement_score': metrics.agreement_score,
                    'rmse': metrics.rmse,
                    'mae': metrics.mae,
                    'max_error': {
                        'value': metrics.max_error,
                        'frequency': metrics.max_error_freq,
                    },
                    'passband_rmse': metrics.passband_rmse,
                    'bass_rmse': metrics.bass_rmse,
                    'f3_viberesp': metrics.f3_viberesp,
                    'f3_hornresp': metrics.f3_hornresp,
                    'f3_error': metrics.f3_error,
                    'correlation': metrics.correlation,
                },
                'passband_offset': comparison.passband_offset,
            }

            with open(output, 'w') as f:
                json.dump(result, f, indent=2)

            click.echo(f"\n✓ Metrics saved to {output}")

        # Generate plot
        if export_plot or show_plot:
            if not MATPLOTLIB_AVAILABLE:
                click.echo("✗ Matplotlib not available for plotting", err=True)
            else:
                plot_validation(
                    comparison=comparison,
                    metrics=metrics,
                    driver_name=driver_name,
                    volume=volume,
                    output_path=export_plot,
                    show=show_plot,
                )

        # Success indicator
        if metrics.rmse < 1.0 and metrics.correlation > 0.99:
            click.echo("\n✓ Validation passed - Excellent agreement!")
        elif metrics.rmse < 2.0 and metrics.correlation > 0.95:
            click.echo("\n⚠ Validation acceptable - Good agreement")
        else:
            click.echo("\n✗ Validation warning - Poor agreement")

    except FileNotFoundError as e:
        click.echo(f"✗ File not found: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"✗ Validation error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


if __name__ == '__main__':
    cli()
