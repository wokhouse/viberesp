#!/usr/bin/env python3
"""
Apply SPL calibration to transfer functions.

USAGE:
1. Run Hornresp simulations first (see SPL_CALIBRATION_INSTRUCTIONS.md)
2. Get the calibration offset from validate_transfer_function_calibration.py
3. Update CALIBRATION_OFFSET_DB below
4. Run this script to apply the calibration

Then verify with:
    PYTHONPATH=src python3 tasks/validate_transfer_function_calibration.py
"""

import sys
sys.path.insert(0, 'src')

# CALIBRATION OFFSET FROM VALIDATION
# REPLACE THIS VALUE with the output from validate_transfer_function_calibration.py
# Based on validation against Hornresp:
# - BC_8NDL51 (20L): +26.36 dB offset
# - BC_15PS100 (50L): +24.13 dB offset
# Overall average: +25.25 dB
# So we need to SUBTRACT ~25 dB: CALIBRATION_OFFSET_DB = -25.25
CALIBRATION_OFFSET_DB = -25.25  # Negative because viberesp is higher than Hornresp


def apply_sealed_box_calibration():
    """Apply calibration to sealed box transfer function."""
    print("=" * 70)
    print("Applying Calibration to Sealed Box Transfer Function")
    print("=" * 70)

    file_path = "src/viberesp/enclosure/sealed_box.py"

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if calibration is already applied
    if "CALIBRATION_OFFSET_DB" in content and "# CALIBRATION: Adjust reference SPL" in content:
        print("\n⚠ Calibration already applied to sealed box!")
        print("  To update, remove the existing calibration block first.")
        return False

    # Find the line: spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0
    if "spl_ref = 20 * math.log10(pressure_rms / p_ref)" not in content:
        print("\n✗ Could not find the reference SPL calculation line!")
        return False

    # Insert calibration after the spl_ref calculation
    old_text = "spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0"

    new_text = f"""spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0

        # CALIBRATION: Adjust reference SPL to match Hornresp
        # Calibration factor determined from validation tests
        # See: tasks/SPL_CALIBRATION_INSTRUCTIONS.md
        CALIBRATION_OFFSET_DB = {CALIBRATION_OFFSET_DB}
        spl_ref += CALIBRATION_OFFSET_DB"""

    if old_text not in content:
        print("\n✗ Could not find the exact text to replace!")
        return False

    updated_content = content.replace(old_text, new_text, 1)

    # Write back
    with open(file_path, 'w') as f:
        f.write(updated_content)

    print(f"\n✓ Applied calibration to {file_path}")
    print(f"  Calibration offset: {CALIBRATION_OFFSET_DB:+.1f} dB")
    return True


def apply_ported_box_calibration():
    """Apply calibration to ported box transfer function."""
    print("\n" + "=" * 70)
    print("Applying Calibration to Ported Box Transfer Function")
    print("=" * 70)

    file_path = "src/viberesp/enclosure/ported_box.py"

    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if calibration is already applied
    if "CALIBRATION_OFFSET_DB" in content and "# CALIBRATION: Adjust reference SPL" in content:
        print("\n⚠ Calibration already applied to ported box!")
        print("  To update, remove the existing calibration block first.")
        return False

    # Find the line: spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0
    if "spl_ref = 20 * math.log10(pressure_rms / p_ref)" not in content:
        print("\n✗ Could not find the reference SPL calculation line!")
        return False

    # Insert calibration after the spl_ref calculation
    old_text = "spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0"

    new_text = f"""spl_ref = 20 * math.log10(pressure_rms / p_ref) if pressure_rms > 0 else 0

        # CALIBRATION: Adjust reference SPL to match Hornresp
        # Calibration factor determined from validation tests
        # See: tasks/SPL_CALIBRATION_INSTRUCTIONS.md
        CALIBRATION_OFFSET_DB = {CALIBRATION_OFFSET_DB}
        spl_ref += CALIBRATION_OFFSET_DB"""

    if old_text not in content:
        print("\n✗ Could not find the exact text to replace!")
        return False

    updated_content = content.replace(old_text, new_text, 1)

    # Write back
    with open(file_path, 'w') as f:
        f.write(updated_content)

    print(f"\n✓ Applied calibration to {file_path}")
    print(f"  Calibration offset: {CALIBRATION_OFFSET_DB:+.1f} dB")
    return True


def main():
    print("\n" + "=" * 70)
    print("SPL Transfer Function Calibration")
    print("=" * 70)

    print(f"\nCalibration offset: {CALIBRATION_OFFSET_DB:+.1f} dB")
    print("\n⚠ Make sure this value is correct before proceeding!")
    print("  Get the correct value from:")
    print("  PYTHONPATH=src python3 tasks/validate_transfer_function_calibration.py")

    response = input("\nProceed with applying calibration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\nCancelled.")
        return 1

    # Apply calibration
    sealed_ok = apply_sealed_box_calibration()
    ported_ok = apply_ported_box_calibration()

    # Summary
    print("\n" + "=" * 70)
    print("Calibration Applied")
    print("=" * 70)

    if sealed_ok and ported_ok:
        print("\n✓ Calibration applied to both sealed and ported box transfer functions")
        print("\nNext steps:")
        print("1. Verify calibration:")
        print("   PYTHONPATH=src python3 tasks/validate_transfer_function_calibration.py")
        print("\n2. Test with additional drivers:")
        print("   PYTHONPATH=src python3 tasks/test_additional_drivers.py")
        print("\n3. Test flatness optimizer:")
        print("   PYTHONPATH=src python3 tasks/test_optimizer_flatness.py")
        return 0
    elif sealed_ok or ported_ok:
        print("\n⚠ Partial calibration applied")
        return 1
    else:
        print("\n✗ No calibration applied")
        return 1


if __name__ == "__main__":
    sys.exit(main())
