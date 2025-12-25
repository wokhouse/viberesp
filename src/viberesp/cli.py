"""Viberesp CLI - Loudspeaker enclosure optimization tool.

NOTE: Physics model under rewrite - only driver database and Hornresp export are functional.
"""

import click
import json
from pathlib import Path

from viberesp.core.models import (
    ThieleSmallParameters,
    EnclosureParameters,
    EnclosureType,
    DriverType
)
from viberesp.io.driver_db import DriverDatabase
from viberesp.validation.hornresp_exporter import export_hornresp_params


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Viberesp: Loudspeaker enclosure optimization tool.

    ⚠️  Physics model rewrite in progress.

    Working commands:
      - driver: Manage driver database
      - export hornresp: Export parameters to Hornresp format

    Non-functional (being rewritten):
      - simulate
      - scan
      - validate
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
@click.option('--cms', type=float, help='Mechanical compliance (m/N) - required for Hornresp export')
@click.option('--rms', type=float, help='Mechanical resistance (N*s/m)')
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
# Export Commands
# ========================================

@cli.group()
def export():
    """Export design parameters to external tools."""
    pass


@export.command('hornresp')
@click.argument('driver_name')
@click.option('--enclosure-type', '-e', type=click.Choice(['sealed', 'ported', 'exponential_horn', 'front_loaded_horn']),
              default='sealed', help='Enclosure type')
@click.option('--volume', '-v', type=float, help='Box volume (L) [required for sealed/ported]')
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
@click.option('--front-chamber', type=float, help='Front chamber volume (L) [for front_loaded_horn]')
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file path')
@click.option('--comment', '-c', type=str, help='Optional comment for the design')
def export_hornresp_cmd(driver_name, enclosure_type, volume, output, comment, **kwargs):
    """Export enclosure parameters to Hornresp format.

    Generates a Hornresp-compatible parameter file for the specified driver and enclosure.

    Examples:
        viberesp export hornresp 18DS115 -e sealed --volume 50 -o design.txt

        viberesp export hornresp 18DS115 -e front_loaded_horn \\
            --throat-area 500 --mouth-area 4800 --horn-length 200 \\
            --rear-chamber 100 --front-chamber 6 -o horn_design.txt
    """
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

    if enclosure_type == 'ported' and kwargs.get('tuning') is None:
        click.echo("✗ --tuning required for ported enclosures", err=True)
        raise click.Abort()

    if enclosure_type in ['exponential_horn', 'front_loaded_horn']:
        for param in ['throat_area', 'mouth_area', 'horn_length']:
            if kwargs.get(param) is None:
                click.echo(f"✗ --{param.replace('_', '-')} required for horn enclosures", err=True)
                raise click.Abort()

    if enclosure_type == 'front_loaded_horn' and kwargs.get('rear_chamber') is None:
        click.echo("✗ --rear-chamber required for front-loaded horn enclosures", err=True)
        raise click.Abort()

    # Build enclosure parameters dict
    params_dict = {
        'enclosure_type': enclosure_type,
        'vb': volume if volume is not None else 0.0,
    }

    # Add optional parameters
    if kwargs.get('depth'):
        params_dict['depth_cm'] = kwargs.get('depth')

    if enclosure_type == 'ported':
        params_dict['fb'] = kwargs.get('tuning')
        params_dict['port_diameter'] = kwargs.get('port_diameter')
        params_dict['number_of_ports'] = kwargs.get('num_ports', 1)

    if enclosure_type == 'exponential_horn':
        params_dict['throat_area_cm2'] = kwargs.get('throat_area')
        params_dict['mouth_area_cm2'] = kwargs.get('mouth_area')
        params_dict['horn_length_cm'] = kwargs.get('horn_length')
        params_dict['flare_rate'] = kwargs.get('flare_rate')
        params_dict['cutoff_frequency'] = kwargs.get('cutoff')
        params_dict['rear_chamber_volume'] = kwargs.get('rear_chamber')

    if enclosure_type == 'front_loaded_horn':
        params_dict['throat_area_cm2'] = kwargs.get('throat_area')
        params_dict['mouth_area_cm2'] = kwargs.get('mouth_area')
        params_dict['horn_length_cm'] = kwargs.get('horn_length')
        params_dict['flare_rate'] = kwargs.get('flare_rate')
        params_dict['cutoff_frequency'] = kwargs.get('cutoff')
        params_dict['rear_chamber_volume'] = kwargs.get('rear_chamber')
        params_dict['front_chamber_volume'] = kwargs.get('front_chamber')

    # Build default comment if not provided
    if comment is None:
        driver_info = f"{driver.manufacturer or 'Unknown'} {driver.model_number or driver_name}".strip()
        comment = f"{driver_info} - {enclosure_type}"

    # Auto-calculate Cms if needed
    if driver.cms is None:
        if driver.vas is not None and driver.sd is not None:
            click.echo(f"ℹ Auto-calculating Cms from Vas and Sd...")
        else:
            click.echo(
                f"\n✗ Driver missing Cms (mechanical compliance) and cannot auto-calculate.\n"
                f"   Add Cms using: viberesp driver add {driver_name} --cms <value>",
                err=True
            )
            raise click.Abort()

    # Validate Mmd
    if driver.mms is None:
        click.echo(
            f"\n✗ Driver missing Mmd (moving mass).\n"
            f"   Add Mmd using: viberesp driver add {driver_name} --mms <value>",
            err=True
        )
        raise click.Abort()

    try:
        export_hornresp_params(
            driver=driver,
            params=params_dict,
            enclosure_type=enclosure_type,
            output_path=str(output),
            comment=comment
        )
        click.echo(f"✓ Exported Hornresp parameters to {output}")

        # Show summary
        click.echo(f"\nExport Summary:")
        click.echo(f"  Driver: {driver_name}")
        click.echo(f"  Type: {enclosure_type}")
        if enclosure_type == 'sealed':
            click.echo(f"  Volume: {volume} L")
        elif enclosure_type == 'ported':
            click.echo(f"  Volume: {volume} L")
            click.echo(f"  Tuning: {kwargs.get('tuning')} Hz")
        elif enclosure_type in ['exponential_horn', 'front_loaded_horn']:
            click.echo(f"  Throat: {kwargs.get('throat_area')} cm²")
            click.echo(f"  Mouth: {kwargs.get('mouth_area')} cm²")
            click.echo(f"  Length: {kwargs.get('horn_length')} cm")
            if kwargs.get('cutoff'):
                click.echo(f"  Cutoff: {kwargs.get('cutoff')} Hz")
            if enclosure_type == 'front_loaded_horn':
                click.echo(f"  Rear Chamber: {kwargs.get('rear_chamber')} L")
                if kwargs.get('front_chamber'):
                    click.echo(f"  Front Chamber: {kwargs.get('front_chamber')} L")

    except Exception as e:
        click.echo(f"✗ Export failed: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
