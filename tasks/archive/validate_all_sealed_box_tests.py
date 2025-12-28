#!/usr/bin/env python3
"""
Run validation tests for all available sealed box Hornresp simulation files.

This script:
1. Finds all sim_*.txt files in sealed_box directories
2. Temporarily copies each to sim.txt
3. Runs the corresponding validation test
4. Reports results for all test cases

Usage:
  PYTHONPATH=src python tasks/validate_all_sealed_box_tests.py
"""

import sys
import subprocess
from pathlib import Path
import shutil
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def find_sim_files():
    """Find all sim_*.txt files in sealed_box directories."""
    validation_dir = Path("tests/validation/drivers")
    sim_files = []

    for sim_file in validation_dir.glob("*/sealed_box/sim_*.txt"):
        driver = sim_file.parent.parent.name
        test_case = sim_file.stem.replace("sim_", "")
        sim_files.append((driver, test_case, sim_file))

    return sorted(sim_files)


def parse_test_case_name(test_case):
    """Parse test case name to extract parameters."""
    # Match patterns like "qtc0_65", "qtc0_707", "vbl20", etc.
    match = re.match(r'(qtc|vb)[l_]?([\d\.]+)', test_case)
    if match:
        param_type = match.group(1)
        value = match.group(2).replace('_', '.')
        return f"{param_type.upper()}={value}"
    return test_case


def run_validation_test(driver, test_case, sim_file):
    """Run validation test for a specific sim file."""
    sealed_box_dir = sim_file.parent
    backup_file = sealed_box_dir / "sim.txt.backup"

    # Backup existing sim.txt if it exists
    if (sealed_box_dir / "sim.txt").exists():
        shutil.copy(sealed_box_dir / "sim.txt", backup_file)

    # Copy the sim file to sim.txt
    shutil.copy(sim_file, sealed_box_dir / "sim.txt")

    try:
        # Determine which test class to run
        driver_name = driver.replace("_", "").replace("bc", "BC").upper()

        # Run pytest for the specific driver's tests
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                f"tests/validation/test_sealed_box.py::TestSealedBoxQtcAlignments{driver_name} -v",
                "-x",  # Stop on first failure
            ],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "PYTHONPATH": "src"}
        )

        success = result.returncode == 0

        return {
            "driver": driver,
            "test_case": test_case,
            "success": success,
            "output": result.stdout + result.stderr,
        }

    finally:
        # Restore backup
        if backup_file.exists():
            shutil.move(backup_file, sealed_box_dir / "sim.txt")
        else:
            (sealed_box_dir / "sim.txt").unlink()


def main():
    """Run validation tests for all available sim files."""
    print("=" * 80)
    print("Sealed Box Validation Test Runner")
    print("=" * 80)

    sim_files = find_sim_files()

    if not sim_files:
        print("\nNo sim_*.txt files found in sealed_box directories.")
        return

    print(f"\nFound {len(sim_files)} simulation files:")
    print("-" * 80)

    results = []

    for driver, test_case, sim_file in sim_files:
        formatted_name = parse_test_case_name(test_case)
        print(f"\n{'=' * 80}")
        print(f"Testing: {driver.upper()} - {formatted_name}")
        print(f"File: {sim_file}")
        print("-" * 80)

        try:
            result = run_validation_test(driver, test_case, sim_file)
            results.append(result)

            if result["success"]:
                print(f"✅ PASSED")
            else:
                print(f"❌ FAILED")
                # Show error summary
                lines = result["output"].split("\n")
                for line in lines:
                    if "FAILED" in line or "AssertionError" in line or "error" in line.lower():
                        print(f"  {line}")

        except Exception as e:
            print(f"⚠️ ERROR: {e}")
            results.append({
                "driver": driver,
                "test_case": test_case,
                "success": False,
                "output": str(e),
            })

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed

    print(f"\nTotal tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print("\nFailed tests:")
        for r in results:
            if not r["success"]:
                formatted_name = parse_test_case_name(r["test_case"])
                print(f"  - {r['driver']}: {formatted_name}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
