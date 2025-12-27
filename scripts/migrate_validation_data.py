#!/usr/bin/env python3
"""
Migration script to convert validation data from old flat structure to new nested structure.

Old structure:
    tests/validation/drivers/bc_8ndl51/sealed_box/
    ├── metadata.json (with configurations array)
    ├── bc_8ndl51_sealed_box_small_box.txt
    └── bc_8ndl51_sealed_box_ideal_box.txt

New structure:
    tests/validation/drivers/bc_8ndl51/
    ├── infinite_baffle/
    │   ├── metadata.json
    │   └── sim.txt
    └── sealed/
        ├── Vb8.9L/
        │   ├── metadata.json
        │   └── sim.txt
        └── Vb31.6L/
            ├── metadata.json
            └── sim.txt

Usage:
    python scripts/migrate_validation_data.py [--driver DRIVER] [--dry-run] [--backup]
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def load_old_metadata(driver_dir: Path, enclosure: str) -> Dict:
    """Load old metadata.json from flat structure."""
    metadata_path = driver_dir / enclosure / "metadata.json"
    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        return json.load(f)


def migrate_driver(
    driver_name: str,
    validation_base: Path,
    dry_run: bool = False,
    backup: bool = True
) -> List[str]:
    """
    Migrate a single driver's validation data from old to new structure.

    Args:
        driver_name: Driver directory name (e.g., "bc_8ndl51")
        validation_base: Base path to validation data
        dry_run: If True, show what would be done without making changes
        backup: If True, backup old data before migration

    Returns:
        List of migration actions performed
    """
    actions = []
    driver_dir = validation_base / driver_name

    if not driver_dir.exists():
        print(f"❌ Driver directory not found: {driver_dir}")
        return actions

    print(f"\n{'='*70}")
    print(f"Migrating: {driver_name}")
    print(f"{'='*70}")

    # Process each enclosure type
    for enclosure_dir in sorted(driver_dir.iterdir()):
        if not enclosure_dir.is_dir():
            continue

        enclosure = enclosure_dir.name

        # Skip already migrated new structure
        if enclosure in ["infinite_baffle", "sealed", "ported", "horn"]:
            # Check if it's the new structure (has subdirs like Vb31.6L)
            has_subdirs = any(d.is_dir() for d in enclosure_dir.iterdir() if not d.name.startswith("."))
            if has_subdirs:
                print(f"✓ Skipping {enclosure}/ (already migrated)")
                continue

        # Load old metadata
        metadata = load_old_metadata(driver_dir, enclosure)
        if metadata is None:
            continue

        configurations = metadata.get("configurations", [])
        if not configurations:
            # No configurations array, might be infinite_baffle or single config
            sim_file = metadata.get("sim_file")
            if sim_file:
                # Single configuration, migrate it
                old_sim_path = enclosure_dir / sim_file
                if old_sim_path.exists():
                    if enclosure == "infinite_baffle" or enclosure == "infinite_baffle":
                        new_enclosure = "infinite_baffle"
                    else:
                        # Extract volume from filename if possible
                        import re
                        vb_match = re.search(r'Vb([\d.]+)L', sim_file)
                        if vb_match:
                            vb_L = float(vb_match.group(1))
                            new_enclosure = f"sealed/Vb{vb_L}L"
                        else:
                            print(f"⚠ Skipping {enclosure}/{sim_file} (cannot extract Vb)")
                            continue

                    new_dir = driver_dir / new_enclosure
                    action = f"Move {enclosure}/{sim_file} → {new_enclosure}/sim.txt"
                    actions.append(action)
                    print(f"  {action}")

                    if not dry_run:
                        new_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(old_sim_path, new_dir / "sim.txt")

                        # Create simplified metadata
                        new_metadata = {k: v for k, v in metadata.items() if k != "sim_file"}
                        if enclosure == "sealed_box":
                            # Try to get Vb from old metadata
                            Vb = metadata.get("Vb")
                            if Vb:
                                new_metadata["Vb_L"] = Vb * 1000  # Convert m³ to L
                            new_metadata["configuration"] = "sealed"
                        elif enclosure == "infinite_baffle":
                            new_metadata["configuration"] = "infinite_baffle"

                        with open(new_dir / "metadata.json", "w") as f:
                            json.dump(new_metadata, f, indent=2)

            continue

        # Process configurations array
        for config in configurations:
            label = config.get("label", "unknown")
            sim_file = config.get("sim_file")
            Vb_L = config.get("Vb_L")

            if not sim_file:
                print(f"⚠ Skipping config '{label}' (no sim_file)")
                continue

            old_sim_path = enclosure_dir / sim_file
            if not old_sim_path.exists():
                print(f"⚠ Skipping config '{label}' (sim file not found: {sim_file})")
                continue

            # Determine new structure path
            # Old: sealed_box -> New: sealed
            enclosure_old = enclosure  # e.g., "sealed_box"
            if enclosure_old == "sealed_box":
                enclosure_new = "sealed"
            elif enclosure_old == "infinite_baffle":
                enclosure_new = "infinite_baffle"
            else:
                enclosure_new = enclosure_old

            # Build new directory path
            if Vb_L:
                config_dir_name = f"Vb{Vb_L}L"
            else:
                # Try to extract from label or filename
                if "ideal" in label.lower():
                    config_dir_name = "Vb31.6L"  # Default for ideal
                elif "large" in label.lower():
                    config_dir_name = "Vb87.8L"
                elif "small" in label.lower() or "min" in label.lower():
                    config_dir_name = "Vb8.9L"
                elif "medium" in label.lower() or "med" in label.lower():
                    config_dir_name = "Vb20.0L"
                else:
                    print(f"⚠ Skipping config '{label}' (cannot determine Vb)")
                    continue

            new_dir = driver_dir / enclosure_new / config_dir_name
            action = f"Move {enclosure}/{sim_file} → {enclosure_new}/{config_dir_name}/sim.txt"
            actions.append(action)
            print(f"  ✓ {action}")

            if not dry_run:
                new_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_sim_path, new_dir / "sim.txt")

                # Create simplified metadata
                new_metadata = {
                    "driver": metadata.get("driver"),
                    "manufacturer": metadata.get("manufacturer", "B&C Speakers"),
                    "configuration": enclosure_new,
                    "date_created": metadata.get("date_created", datetime.now().strftime("%Y-%m-%d")),
                    "date_run": metadata.get("date_run", datetime.now().strftime("%Y-%m-%d")),
                    "hornresp_version": metadata.get("hornresp_version", "unknown"),
                    "voice_coil_model": metadata.get("voice_coil_model", "simple"),
                    "validation_status": metadata.get("validation_status", "ready"),
                }

                # Add configuration-specific parameters
                if enclosure_new == "sealed" and Vb_L:
                    new_metadata["Vb_L"] = Vb_L

                with open(new_dir / "metadata.json", "w") as f:
                    json.dump(new_metadata, f, indent=2)

    # Backup old structure if requested
    if backup and not dry_run:
        for enclosure_dir in driver_dir.iterdir():
            if not enclosure_dir.is_dir():
                continue

            enclosure = enclosure_dir.name

            # Only backup old structure directories
            if enclosure in ["sealed_box", "infinite_baffle"]:
                backup_dir = driver_dir / f"{enclosure}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                if not backup_dir.exists():
                    action = f"Backup {enclosure}/ → {backup_dir.name}/"
                    actions.append(action)
                    print(f"  {action}")
                    shutil.copytree(enclosure_dir, backup_dir)

                    # Remove old structure after backup
                    shutil.rmtree(enclosure_dir)
                    print(f"  ✓ Removed old {enclosure}/ directory")

    print(f"\n✓ Migrated {len([a for a in actions if 'Move' in a])} configuration(s)")
    return actions


def main():
    parser = argparse.ArgumentParser(
        description="Migrate validation data from old to new structure"
    )
    parser.add_argument(
        "--driver", "-d",
        help="Driver to migrate (e.g., bc_8ndl51). Default: all drivers"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--backup", "-b",
        action="store_true",
        default=True,
        help="Backup old data before migration (default: True)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup"
    )

    args = parser.parse_args()

    # Determine base path
    script_dir = Path(__file__).parent
    validation_base = script_dir.parent / "tests" / "validation" / "drivers"

    if not validation_base.exists():
        print(f"❌ Validation data directory not found: {validation_base}")
        return 1

    # Determine which drivers to migrate
    if args.driver:
        drivers = [args.driver.lower()]
    else:
        drivers = sorted([d.name for d in validation_base.iterdir() if d.is_dir()])

    if not drivers:
        print("❌ No driver directories found")
        return 1

    # Show dry-run mode
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")

    # Migrate each driver
    for driver in drivers:
        migrate_driver(driver, validation_base, args.dry_run, args.backup and not args.no_backup)

    print(f"\n{'='*70}")
    print("Migration complete!")
    print(f"{'='*70}")
    print("\nNext steps:")
    print("  1. Review the new structure using: viberesp validate list")
    print("  2. Test validation: viberesp validate compare bc_8ndl51 sealed/Vb31.6L")
    print("  3. If everything looks good, you can remove the backup directories")

    return 0


if __name__ == "__main__":
    exit(main())
