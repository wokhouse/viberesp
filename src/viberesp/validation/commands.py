"""
Validation CLI commands for viberesp.

Provides command-line interface for managing validation data,
generating Hornresp files, and running validation comparisons.

Literature:
- Hornresp User Manual - File format and validation procedures
- ROADMAP Phase 5 - Validation framework
"""

import click
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from viberesp.hornresp.export import export_to_hornresp
from viberesp.hornresp.results_parser import load_hornresp_sim_file
from viberesp.validation.compare import (
    compare_electrical_impedance,
    compare_electrical_impedance_phase,
    compare_spl,
    generate_validation_report
)


def get_validation_base_path() -> Path:
    """Get the base path for validation data."""
    return Path(__file__).parent.parent.parent / "tests" / "validation"


def get_driver_path(driver_name: str) -> Path:
    """Get the path to a driver's validation directory."""
    return get_validation_base_path() / "drivers" / driver_name.lower()


def get_enclosure_path(driver_name: str, enclosure_type: str) -> Path:
    """Get the path to a driver's enclosure validation directory."""
    return get_driver_path(driver_name) / enclosure_type


def load_driver_json(driver_name: str) -> dict:
    """Load driver.json for a given driver."""
    driver_path = get_driver_path(driver_name)
    driver_file = driver_path / "driver.json"

    if not driver_file.exists():
        raise click.ClickException(f"Driver file not found: {driver_file}")

    with open(driver_file, 'r') as f:
        return json.load(f)


def load_test_cases_json(driver_name: str, enclosure_type: str) -> dict:
    """Load test_cases.json for a given driver/enclosure combination."""
    enclosure_path = get_enclosure_path(driver_name, enclosure_type)
    test_cases_file = enclosure_path / "test_cases.json"

    if not test_cases_file.exists():
        raise click.ClickException(f"Test cases file not found: {test_cases_file}")

    with open(test_cases_file, 'r') as f:
        return json.load(f)


def get_driver_from_json(driver_data: dict):
    """Import driver from viberesp.driver.bc_drivers based on driver name."""
    from viberesp.driver.bc_drivers import (
        get_bc_8ndl51,
        get_bc_12ndl76,
        get_bc_15ds115,
        get_bc_15ps100,
        get_bc_18pzw100,
    )

    driver_map = {
        "BC_8NDL51": get_bc_8ndl51,
        "BC_12NDL76": get_bc_12ndl76,
        "BC_15DS115": get_bc_15ds115,
        "BC_15PS100": get_bc_15ps100,
        "BC_18PZW100": get_bc_18pzw100,
    }

    driver_name = driver_data["driver_name"]
    if driver_name not in driver_map:
        raise click.ClickException(f"Unknown driver: {driver_name}")

    return driver_map[driver_name]()


# ============================================================================
# CLI Commands
# ============================================================================

@click.command(name="generate-input")
@click.argument("driver_name")
@click.argument("enclosure_type")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory (default: results/)")
def validate_generate_input(driver_name: str, enclosure_type: str, output_dir: Optional[str]):
    """
    Generate Hornresp input.txt files from test_cases.json.

    Generates Hornresp input files for all test cases defined in test_cases.json.
    Each test case gets its own input.txt file in the results/{test_case_id}/ directory.

    DRIVER_NAME: Driver name (e.g., bc_8ndl51)
    ENCLOSURE_TYPE: Enclosure type (infinite_baffle, sealed_box, ported_box)

    Example:
        viberesp validate generate-input bc_8ndl51 sealed_box
    """
    driver_name_normalized = driver_name.lower().replace("-", "_")

    # Load test cases
    test_cases_data = load_test_cases_json(driver_name_normalized, enclosure_type)

    # Load driver parameters
    driver_data = load_driver_json(driver_name_normalized)
    driver = get_driver_from_json(driver_data)

    # Determine output directory
    if output_dir:
        base_output_path = Path(output_dir)
    else:
        base_output_path = get_enclosure_path(driver_name_normalized, enclosure_type) / "results"

    click.echo(f"Generating Hornresp input files for {driver_name} / {enclosure_type}")
    click.echo(f"Output directory: {base_output_path}")
    click.echo()

    generated_count = 0
    for test_case in test_cases_data["test_cases"]:
        test_case_id = test_case["test_case_id"]
        params = test_case["parameters"]
        description = test_case["description"]

        # Create output directory
        output_path = base_output_path / test_case_id
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        output_file = output_path / "input.txt"

        # Generate input.json for reference
        input_json = {
            "test_case_id": test_case_id,
            "driver": driver_name.upper(),
            "enclosure_type": enclosure_type,
            "enclosure_parameters": params,
            "generated_at": datetime.now().isoformat(),
        }

        with open(output_path / "input.json", 'w') as f:
            json.dump(input_json, f, indent=2)

        # Export to Hornresp format
        export_kwargs = {}
        if enclosure_type == "infinite_baffle":
            export_kwargs["enclosure_type"] = "infinite_baffle"
        elif enclosure_type == "sealed_box":
            export_kwargs["enclosure_type"] = "sealed_box"
            export_kwargs["Vb_liters"] = params.get("Vb_liters")
            if params.get("QL"):
                export_kwargs["QL"] = params["QL"]
        elif enclosure_type == "ported_box":
            export_kwargs["enclosure_type"] = "ported_box"
            export_kwargs["Vb_liters"] = params.get("Vb_liters")
            export_kwargs["Fb_hz"] = params.get("Fb_hz")
            export_kwargs["port_area_cm2"] = params.get("port_area_cm2")
            export_kwargs["port_length_cm"] = params.get("port_length_cm")
            if params.get("QL"):
                export_kwargs["QL"] = params["QL"]
        else:
            click.echo(f"⚠ Unknown enclosure type: {enclosure_type}, skipping {test_case_id}")
            continue

        export_to_hornresp(
            driver=driver,
            driver_name=f"{driver_name}_{test_case_id}"[:48],  # Hornresp limit
            output_path=str(output_file),
            comment=f"{description} | {test_case_id}",
            **export_kwargs
        )

        click.echo(f"✓ Generated: {output_file}")
        generated_count += 1

    click.echo()
    click.echo(f"✓ Generated {generated_count} input files")


@click.command(name="parse-output")
@click.argument("driver_name")
@click.argument("enclosure_type")
@click.option("--input-dir", "-i", type=click.Path(), help="Input directory (default: results/)")
def validate_parse_output(driver_name: str, enclosure_type: str, input_dir: Optional[str]):
    """
    Parse Hornresp sim.txt files to sim.json.

    Parses Hornresp simulation output files and converts them to JSON format
    for programmatic access and validation comparisons.

    DRIVER_NAME: Driver name (e.g., bc_8ndl51)
    ENCLOSURE_TYPE: Enclosure type (infinite_baffle, sealed_box, ported_box)

    Example:
        viberesp validate parse-output bc_8ndl51 sealed_box
    """
    driver_name_normalized = driver_name.lower().replace("-", "_")

    # Load test cases to know which test cases to parse
    test_cases_data = load_test_cases_json(driver_name_normalized, enclosure_type)

    # Determine input directory
    if input_dir:
        base_input_path = Path(input_dir)
    else:
        base_input_path = get_enclosure_path(driver_name_normalized, enclosure_type) / "results"

    click.echo(f"Parsing Hornresp sim.txt files for {driver_name} / {enclosure_type}")
    click.echo(f"Input directory: {base_input_path}")
    click.echo()

    parsed_count = 0
    for test_case in test_cases_data["test_cases"]:
        test_case_id = test_case["test_case_id"]
        sim_file = base_input_path / test_case_id / "sim.txt"

        if not sim_file.exists():
            click.echo(f"⚠ File not found: {sim_file}")
            continue

        try:
            # Parse Hornresp simulation file
            sim_data = load_hornresp_sim_file(str(sim_file))

            # Create sim.json
            sim_json = {
                "test_case_id": test_case_id,
                "metadata": {
                    "hornresp_version": "unknown",  # Not in sim.txt format
                    "date_parsed": datetime.now().isoformat(),
                    "source_file": str(sim_file),
                    "frequency_range": {
                        "start_hz": float(sim_data.frequency[0]),
                        "end_hz": float(sim_data.frequency[-1]),
                        "num_points": len(sim_data.frequency)
                    }
                },
                "data": {
                    "frequency": sim_data.frequency.tolist(),
                    "ra": sim_data.ra.tolist(),
                    "xa": sim_data.xa.tolist(),
                    "za": sim_data.za.tolist(),
                    "spl": sim_data.spl.tolist(),
                    "ze": sim_data.ze_ohms.tolist(),
                    "zephase": sim_data.zephase_deg.tolist(),
                    "xg": sim_data.xg.tolist(),
                    "eg": sim_data.eg.tolist(),
                }
            }

            output_file = base_input_path / test_case_id / "sim.json"
            with open(output_file, 'w') as f:
                json.dump(sim_json, f, indent=2)

            click.echo(f"✓ Parsed: {output_file}")
            parsed_count += 1

        except Exception as e:
            click.echo(f"✗ Error parsing {sim_file}: {e}")

    click.echo()
    click.echo(f"✓ Parsed {parsed_count} files")


@click.command(name="run")
@click.argument("driver_name")
@click.argument("enclosure_type")
@click.option("--test-case", "-t", help="Specific test case ID (default: all)")
@click.option("--metrics", "-m", multiple=True, default=["ze", "phase", "spl"],
              help="Metrics to validate (default: ze, phase, spl)")
def validate_run(driver_name: str, enclosure_type: str, test_case: Optional[str], metrics: tuple):
    """
    Run validation comparisons and generate validation.json.

    Compares viberesp simulation results against Hornresp reference data
    and generates validation.json files with pass/fail status and error metrics.

    DRIVER_NAME: Driver name (e.g., bc_8ndl51)
    ENCLOSURE_TYPE: Enclosure type (infinite_baffle, sealed_box, ported_box)
    --test-case: Optional specific test case ID

    Example:
        viberesp validate run bc_8ndl51 sealed_box
        viberesp validate run bc_8ndl51 ported_box --test-case bc_8ndl51_ported_b4
    """
    driver_name_normalized = driver_name.lower().replace("-", "_")

    # Load test cases
    test_cases_data = load_test_cases_json(driver_name_normalized, enclosure_type)

    # Load driver
    driver_data = load_driver_json(driver_name_normalized)
    driver = get_driver_from_json(driver_data)

    results_path = get_enclosure_path(driver_name_normalized, enclosure_type) / "results"

    click.echo(f"Running validation for {driver_name} / {enclosure_type}")
    click.echo()

    # Filter test cases if specific one requested
    test_cases_to_validate = test_cases_data["test_cases"]
    if test_case:
        test_cases_to_validate = [tc for tc in test_cases_to_validate if tc["test_case_id"] == test_case]
        if not test_cases_to_validate:
            raise click.ClickException(f"Test case not found: {test_case}")

    validated_count = 0

    for test_case in test_cases_to_validate:
        test_case_id = test_case["test_case_id"]

        # Load sim.json
        sim_json_file = results_path / test_case_id / "sim.json"
        if not sim_json_file.exists():
            click.echo(f"⚠ Skipping {test_case_id}: sim.json not found")
            continue

        with open(sim_json_file, 'r') as f:
            sim_data = json.load(f)

        import numpy as np
        frequencies = np.array(sim_data["data"]["frequency"])
        ze_hornresp = np.array(sim_data["data"]["ze"])
        zephase_hornresp = np.array(sim_data["data"]["zephase"])
        spl_hornresp = np.array(sim_data["data"]["spl"])

        # Run viberesp simulation (placeholder - actual implementation depends on enclosure type)
        # For now, we'll create a placeholder validation result
        click.echo(f"⚠ {test_case_id}: Viberesp simulation not yet implemented")

        # TODO: Implement actual viberesp simulation based on enclosure type
        # This would call the appropriate enclosure simulation function
        # ze_viberesp = calculate_electrical_impedance(driver, enclosure_params, frequencies)
        # spl_viberesp = calculate_spl(driver, enclosure_params, frequencies)

        # Placeholder: Create validation.json with "skipped" status
        validation_json = {
            "test_case_id": test_case_id,
            "validation_date": datetime.now().strftime("%Y-%m-%d"),
            "viberesp_version": "0.1.0",
            "hornresp_version": sim_data["metadata"]["hornresp_version"],
            "status": "skipped",
            "metrics": {
                "ze_magnitude": {"passed": None, "note": "Viberesp simulation not yet implemented"},
                "ze_phase": {"passed": None, "note": "Viberesp simulation not yet implemented"},
                "spl": {"passed": None, "note": "Viberesp simulation not yet implemented"}
            },
            "notes": "Viberesp simulation calculations not yet integrated with validation workflow"
        }

        output_file = results_path / test_case_id / "validation.json"
        with open(output_file, 'w') as f:
            json.dump(validation_json, f, indent=2)

        click.echo(f"✓ Generated: {output_file}")
        validated_count += 1

    click.echo()
    click.echo(f"✓ Validated {validated_count} test cases")


@click.command(name="status")
@click.option("--driver", "-d", help="Filter by driver name")
@click.option("--enclosure", "-e", help="Filter by enclosure type")
@click.option("--detailed", is_flag=True, help="Show detailed validation results")
def validate_status(driver: Optional[str], enclosure: Optional[str], detailed: bool):
    """
    Query and display validation status.

    Shows the current validation status for all drivers, test cases, and metrics.
    Use --detailed to see full error metrics and pass/fail information.

    Examples:
        viberesp validate status
        viberesp validate status --driver bc_8ndl51
        viberesp validate status --driver bc_8ndl51 --enclosure sealed_box --detailed
    """
    base_path = get_validation_base_path() / "drivers"

    # Collect all drivers
    if driver:
        drivers_to_check = [base_path / driver.lower()]
    else:
        drivers_to_check = [d for d in base_path.iterdir() if d.is_dir()]

    click.echo("=" * 60)
    click.echo("VALIDATION STATUS")
    click.echo("=" * 60)
    click.echo()

    for driver_path in sorted(drivers_to_check):
        if not driver_path.exists():
            continue

        driver_name = driver_path.name
        driver_json_file = driver_path / "driver.json"

        # Load driver metadata
        if driver_json_file.exists():
            with open(driver_json_file, 'r') as f:
                driver_data = json.load(f)
            validation_status = driver_data.get("validation_status", "unknown")
            enclosures = driver_data.get("enclosures_validated", [])
        else:
            validation_status = "no_metadata"
            enclosures = []

        click.echo(f"Driver: {driver_name.upper()}")
        click.echo(f"  Status: {validation_status}")

        # Filter enclosures if specified
        if enclosure:
            enclosures_to_check = [driver_path / enclosure]
        else:
            enclosures_to_check = [driver_path / e for e in enclosures if (driver_path / e).exists()]

        for enclosure_path in sorted(enclosures_to_check):
            if not enclosure_path.exists():
                continue

            enclosure_type = enclosure_path.name
            test_cases_file = enclosure_path / "test_cases.json"

            if not test_cases_file.exists():
                click.echo(f"  {enclosure_type}: No test cases defined")
                continue

            with open(test_cases_file, 'r') as f:
                test_cases_data = json.load(f)

            # Count test cases by status
            total = len(test_cases_data["test_cases"])
            passed = sum(1 for tc in test_cases_data["test_cases"] if tc["status"] == "passed")
            failed = sum(1 for tc in test_cases_data["test_cases"] if tc["status"] == "failed")
            pending = sum(1 for tc in test_cases_data["test_cases"] if tc["status"] == "pending")

            click.echo(f"  {enclosure_type}:")
            click.echo(f"    Total: {total} | Passed: {passed} | Failed: {failed} | Pending: {pending}")

            # Show detailed results if requested
            if detailed:
                results_path = enclosure_path / "results"
                for tc in test_cases_data["test_cases"]:
                    tc_id = tc["test_case_id"]
                    status = tc["status"]

                    # Load validation.json if exists
                    validation_json_file = results_path / tc_id / "validation.json"
                    if validation_json_file.exists():
                        with open(validation_json_file, 'r') as f:
                            validation_data = json.load(f)

                        click.echo(f"      {tc_id}: {status}")

                        if validation_data.get("metrics"):
                            for metric_name, metric_data in validation_data["metrics"].items():
                                passed = metric_data.get("passed")
                                if passed is True:
                                    click.echo(f"        ✓ {metric_name}")
                                elif passed is False:
                                    click.echo(f"        ✗ {metric_name}")
                                elif passed is None:
                                    note = metric_data.get("note", "skipped")
                                    click.echo(f"        ⊘ {metric_name}: {note}")
                    else:
                        click.echo(f"      {tc_id}: {status} (no validation data)")

        click.echo()

    click.echo("=" * 60)


@click.command(name="migrate")
@click.argument("driver_name")
@click.option("--dry-run", is_flag=True, help="Show migration plan without executing")
@click.option("--backup", is_flag=True, help="Create backup before migrating")
def validate_migrate(driver_name: str, dry_run: bool, backup: bool):
    """
    Migrate existing validation data to new format.

    Converts legacy validation data (README.md tables, input_*.txt files)
    to the new standardized JSON-based format.

    DRIVER_NAME: Driver name (e.g., bc_8ndl51)

    Examples:
        viberesp validate migrate bc_8ndl51 --dry-run
        viberesp validate migrate bc_8ndl51 --backup
    """
    click.echo("Migration command not yet implemented")
    click.echo("This will be implemented in Phase 1.4")
    click.echo()
    click.echo("Planned functionality:")
    click.echo("  - Parse README.md for test cases")
    click.echo("  - Create driver.json and test_cases.json")
    click.echo("  - Reorganize files into results/ directories")
    click.echo("  - Flatten ql/ subdirectories")
    click.echo("  - Create input.json for each test case")
