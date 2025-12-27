#!/usr/bin/env python3
"""
Run validation tests for all sealed box sim files.
"""

import subprocess
import sys
from pathlib import Path

# Sim files to test
bc8ndl51_tests = [
    ("sim_qtc0_65.txt", "Qtc=0.65"),
    ("sim_qtc0_8.txt", "Qtc=0.8"),
    ("sim_qtc1.txt", "Qtc=1.0"),
    ("sim_qtc1_1.txt", "Qtc=1.1"),
    ("sim_vbl20.txt", "Vb=20L"),
]

bc15ps100_tests = [
    ("sim_qtc0_5.txt", "Qtc=0.5"),
    ("sim_qtc0_97.txt", "Qtc=0.94"),
    ("sim_vbl50.txt", "Vb=50L"),
    ("sim_vbl80.txt", "Vb=80L"),
]


def test_driver(driver, tests):
    """Run tests for a driver."""
    base_dir = Path(f"tests/validation/drivers/{driver}/sealed_box")

    print(f"\n{'=' * 80}")
    print(f"Testing {driver.upper()}")
    print(f"{'=' * 80}\n")

    results = []

    for sim_file, test_name in tests:
        sim_path = base_dir / sim_file
        if not sim_path.exists():
            print(f"⚠️  SKIP: {test_name} - {sim_file} not found")
            continue

        print(f"\n{'─' * 80}")
        print(f"Testing: {test_name}")
        print(f"File: {sim_file}")
        print(f"{'─' * 80}")

        # Copy sim file to sim.txt
        sim_txt = base_dir / "sim.txt"
        import shutil
        shutil.copy(sim_path, sim_txt)

        # Run the test
        test_class = f"TestSealedBoxQtcAlignments{driver.replace('_', '').replace('bc', 'BC').upper()}"
        result = subprocess.run(
            [
                "python", "-m", "pytest",
                f"tests/validation/test_sealed_box.py::{test_class}",
                "-v", "--tb=line", "-x"
            ],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "PYTHONPATH": "src"}
        )

        # Parse output
        lines = result.stdout.split("\n")
        passed = []
        failed = []
        errors = []

        for line in lines:
            if "PASSED" in line:
                passed.append(line.strip())
            elif "FAILED" in line:
                failed.append(line.strip())
            elif "ERROR" in line:
                errors.append(line.strip())

        # Print results
        if result.returncode == 0:
            print(f"✅ PASSED - {len(passed)} tests")
            for p in passed[:5]:  # Show first 5
                print(f"  {p}")
            if len(passed) > 5:
                print(f"  ... and {len(passed) - 5} more")
            results.append((test_name, True))
        else:
            print(f"❌ FAILED")
            for f in failed[:3]:
                print(f"  {f}")
            for e in errors[:3]:
                print(f"  {e}")
            results.append((test_name, False))

    # Summary for this driver
    print(f"\n{'=' * 80}")
    print(f"{driver.upper()} Summary")
    print(f"{'=' * 80}")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    for name, p in results:
        status = "✅" if p else "❌"
        print(f"  {status} {name}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("SEALED BOX VALIDATION - ALL SIM FILES")
    print("=" * 80)

    test_driver("bc_8ndl51", bc8ndl51_tests)
    test_driver("bc_15ps100", bc15ps100_tests)

    print("\n" + "=" * 80)
    print("COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
