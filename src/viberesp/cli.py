"""
Viberesp CLI interface.

Provides command-line interface for driver management and Hornresp export.
Based on Click for CLI commands and prompts.

Usage:
    viberesp driver import           # Interactive T/S parameter entry
    viberesp driver list             # List available B&C drivers
    viberesp export <driver>         # Export driver to Hornresp format
"""

import click
from pathlib import Path

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.hornresp.export import export_to_hornresp, batch_export_to_hornresp


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Viberesp - Loudspeaker enclosure design and simulation tool.

    Initial focus on horn-loaded enclosures with validation against Hornresp.
    """
    pass


@cli.group()
def driver():
    """Driver parameter management commands."""
    pass


@driver.command(name="import")
@click.option("--name", prompt="Driver name", help="Name/identifier for the driver")
@click.option("--M-ms", prompt="Moving mass (kg)", type=float, help="M_ms: Moving mass (kg)")
@click.option("--C-ms", prompt="Compliance (m/N)", type=float, help="C_ms: Suspension compliance (m/N)")
@click.option("--R-ms", prompt="Mechanical resistance (N·s/m)", type=float, default=0.0, help="R_ms: Mechanical resistance")
@click.option("--R-e", prompt="DC resistance (ohms)", type=float, help="R_e: Voice coil DC resistance (Ω)")
@click.option("--L-e", prompt="Inductance (H)", type=float, help="L_e: Voice coil inductance (H)")
@click.option("--B-L", prompt="Force factor (T·m)", type=float, help="BL: Force factor (T·m)")
@click.option("--S-d", prompt="Piston area (m²)", type=float, help="S_d: Effective piston area (m²)")
@click.option("--output", "-o", type=click.Path(), help="Output file path (optional)")
def driver_import(name, M_ms, C_ms, R_ms, R_e, L_e, B_L, S_d, output):
    """
    Interactively import driver Thiele-Small parameters.

    Prompts for all required T/S parameters and creates a ThieleSmallParameters
    instance that can be exported to Hornresp format.

    Literature:
        - Small (1972) - Thiele-Small parameter definitions
        - COMSOL (2020) - Lumped parameter model

    Examples:
        $ viberesp driver import
        Driver name: BC_12NDL76
        Moving mass (kg): 0.054
        Compliance (m/N): 0.00019
        ...
    """
    # Create ThieleSmallParameters instance
    driver_params = ThieleSmallParameters(
        M_ms=M_ms,
        C_ms=C_ms,
        R_ms=R_ms,
        R_e=R_e,
        L_e=L_e,
        BL=B_L,
        S_d=S_d
    )

    # Display calculated derived properties
    click.echo(f"\n✓ Driver '{name}' created successfully")
    click.echo(f"\nDerived Properties:")
    click.echo(f"  F_s = {driver_params.F_s:.2f} Hz")
    click.echo(f"  Q_es = {driver_params.Q_es:.3f}")
    click.echo(f"  Q_ms = {driver_params.Q_ms if driver_params.Q_ms != float('inf') else 'inf'}")
    click.echo(f"  Q_ts = {driver_params.Q_ts:.3f}")
    click.echo(f"  V_as = {driver_params.V_as:.4f} m³")

    # Save to file if output path provided
    if output:
        export_to_hornresp(driver_params, name, output, comment=f"Imported via viberesp driver import")
        click.echo(f"\n✓ Exported to {output}")


@driver.command(name="list")
def driver_list():
    """
    List available B&C driver fixtures.

    Shows the 4 B&C drivers included for validation testing:
    - 8NDL51-8 (8" midrange)
    - 12NDL76-4 (12" mid-woofer)
    - 15DS115-8 (15" subwoofer)
    - 18PZW100-8 (18" subwoofer)
    """
    click.echo("\nAvailable B&C Driver Fixtures:")
    click.echo("=" * 60)

    drivers = [
        ("BC_8NDL51", "8\" Midrange", "66 Hz", "5.3 Ω", "215 cm²"),
        ("BC_12NDL76", "12\" Mid-Woofer", "50 Hz", "3.1 Ω", "522 cm²"),
        ("BC_15DS115", "15\" Subwoofer", "33 Hz", "4.9 Ω", "860 cm²"),
        ("BC_18PZW100", "18\" Subwoofer", "37 Hz", "5.1 Ω", "1250 cm²"),
    ]

    for name, description, fs, re, sd in drivers:
        click.echo(f"\n{name} - {description}")
        click.echo(f"  F_s: {fs},  R_e: {re},  S_d: {sd}")

    click.echo("\n" + "=" * 60)
    click.echo("\nUse these driver names with 'viberesp export' command:")
    click.echo("  Example: viberesp export BC_12NDL76 -o output.txt")


@cli.command()
@click.argument("driver_name", type=click.Choice([
    "BC_8NDL51",
    "BC_12NDL76",
    "BC_15DS115",
    "BC_18PZW100"
], case_sensitive=False))
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory or file path")
def export(driver_name, output):
    """
    Export B&C driver to Hornresp format.

    Exports one of the predefined B&C drivers to a Hornresp .txt file
    ready for import into Hornresp for simulation.

    Literature:
        - Hornresp User Manual - File format specification

    Args:
        driver_name: Name of B&C driver (BC_8NDL51, BC_12NDL76, BC_15DS115, BC_18PZW100)
        output: Output file or directory path (default: current directory)

    Examples:
        $ viberesp export BC_12NDL76
        $ viberesp export BC_12NDL76 -o exports/
        $ viberesp export BC_12NDL76 -o bc_12ndl76.txt
    """
    # Import driver factory functions
    from viberesp.driver.bc_drivers import (
        get_bc_8ndl51, get_bc_12ndl76, get_bc_15ds115, get_bc_18pzw100
    )

    # Map driver names to factory functions
    driver_map = {
        "BC_8NDL51": get_bc_8ndl51,
        "BC_12NDL76": get_bc_12ndl76,
        "BC_15DS115": get_bc_15ds115,
        "BC_18PZW100": get_bc_18pzw100,
    }

    # Get driver from factory function
    driver_factory = driver_map[driver_name]
    driver = driver_factory()

    # Determine output path
    output_path = Path(output)
    if output_path.is_dir() or output == ".":
        # Output is a directory, create filename from driver name
        filename = f"{driver_name.lower()}.txt"
        output_file = output_path / filename
    else:
        # Output is a file path
        output_file = output_path

    # Export to Hornresp format
    export_to_hornresp(
        driver,
        driver_name,
        str(output_file),
        comment=f"B&C {driver_name} driver parameters - exported from viberesp"
    )

    click.echo(f"\n✓ Successfully exported {driver_name} to {output_file}")
    click.echo(f"\nImport this file into Hornresp to verify parameters.")


@cli.command()
@click.option("--output", "-o", type=click.Path(), default="./exports", help="Output directory")
def export_all(output):
    """
    Export all B&C drivers to Hornresp format.

    Generates .txt files for all 4 B&C drivers in the specified directory.

    Examples:
        $ viberesp export-all
        $ viberesp export-all -o hornresp_inputs/
    """
    # Import driver factory functions
    from viberesp.driver.bc_drivers import (
        get_bc_8ndl51, get_bc_12ndl76, get_bc_15ds115, get_bc_18pzw100
    )

    # Create list of all drivers
    drivers = [
        (get_bc_8ndl51(), "BC_8NDL51"),
        (get_bc_12ndl76(), "BC_12NDL76"),
        (get_bc_15ds115(), "BC_15DS115"),
        (get_bc_18pzw100(), "BC_18PZW100"),
    ]

    # Batch export
    batch_export_to_hornresp(drivers, output)

    click.echo(f"\n✓ Exported {len(drivers)} drivers to {output}/")
    click.echo("\nExported files:")
    for _, name in drivers:
        click.echo(f"  - {name.lower()}.txt")


def main():
    """Entry point for viberesp CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
