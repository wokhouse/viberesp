"""Test case drivers for horn optimization validation.

This module provides driver definitions for the TC2-4 test cases used in
validating exponential horn simulation and optimization against Hornresp.

Literature:
- Hornresp validation data: tests/validation/horn_theory/exp_midrange_tc*/
"""

from viberesp.driver.parameters import ThieleSmallParameters


def get_tc2_compression_driver() -> ThieleSmallParameters:
    """
    TC2 compression driver (midrange horn).

    Test case for validating horn simulation and optimization against Hornresp.
    This driver represents a compression driver loaded by an exponential horn
    with no throat or rear chambers.

    Parameters from: tests/validation/horn_theory/exp_midrange_tc2/horn_params.txt

    Driver specifications:
    - Sd = 8.0 cm² (diaphragm area)
    - Mmd = 8.0 g (driver mass only, no radiation mass)
    - Cms = 5.00E-05 m/N (compliance)
    - Rms = 3.0 N·s/m (mechanical resistance)
    - Re = 6.5 Ω (voice coil resistance)
    - Le = 0.1 mH (voice coil inductance)
    - BL = 12.0 T·m (force factor)
    - Fs ≈ 251 Hz (resonance frequency)

    Horn specifications (TC2):
    - Throat area (S1): 5.0 cm²
    - Mouth area (S2): 200.0 cm²
    - Length (L12): 0.5 m
    - Cutoff frequency: ~404 Hz
    - No throat chamber (Vtc = 0)
    - No rear chamber (Vrc = 0)

    Returns:
        ThieleSmallParameters: TC2 compression driver parameters

    Examples:
        >>> from viberesp.driver.test_drivers import get_tc2_compression_driver
        >>> driver = get_tc2_compression_driver()
        >>> driver.F_s
        251.1...  # Hz (resonance frequency)
        >>> driver.S_d
        0.0008  # m² (8.0 cm²)

    Validation:
        TC2 has been validated against Hornresp with excellent agreement:
        - Electrical impedance magnitude: 0.68% error
        - Electrical impedance phase: 0.37° error
        See: tests/validation/horn_theory/exp_midrange_tc2/VALIDATION_SUMMARY.md
    """
    return ThieleSmallParameters(
        M_md=0.008,     # 8.0 g -> 0.008 kg (driver mass only)
        C_ms=5.0e-5,    # 5.00E-05 m/N (mechanical compliance)
        R_ms=3.0,       # 3.0 N·s/m (mechanical resistance)
        R_e=6.5,        # 6.5 Ω (voice coil DC resistance)
        L_e=0.1e-3,     # 0.1 mH -> 0.0001 H (voice coil inductance)
        BL=12.0,        # 12.0 T·m (force factor)
        S_d=0.0008,     # 8.0 cm² -> 0.0008 m² (diaphragm area)
    )


def get_tc3_compression_driver() -> ThieleSmallParameters:
    """
    TC3 compression driver (midrange horn with throat chamber).

    Test case for validating horn simulation with throat chamber compliance.
    Same driver as TC2, but with a 0.5L throat chamber between driver and horn.

    Parameters from: tests/validation/horn_theory/exp_midrange_tc3/horn_params.txt

    Horn specifications (TC3):
    - Same driver and horn as TC2
    - Throat chamber: Vtc = 0.5 L, Atc = 5.0 cm²
    - No rear chamber (Vrc = 0)

    Returns:
        ThieleSmallParameters: TC3 compression driver (same as TC2)

    Examples:
        >>> from viberesp.driver.test_drivers import get_tc3_compression_driver
        >>> driver = get_tc3_compression_driver()
        >>> driver.S_d  # Same as TC2
        0.0008  # m²

    Validation:
        TC3 validation data is available in tests/validation/horn_theory/exp_midrange_tc3/
        Use for testing throat chamber compliance effects.
    """
    # TC3 uses same driver as TC2
    return get_tc2_compression_driver()


def get_tc4_compression_driver() -> ThieleSmallParameters:
    """
    TC4 compression driver (midrange horn with both chambers).

    Test case for validating complete front-loaded horn system with both
    throat and rear chambers.

    Parameters from: tests/validation/horn_theory/exp_midrange_tc4/horn_params.txt

    Horn specifications (TC4):
    - Same driver and horn as TC2
    - Throat chamber: Vtc = 0.5 L, Atc = 5.0 cm²
    - Rear chamber: Vrc = 2.0 L, Lrc = 12.60 cm

    Returns:
        ThieleSmallParameters: TC4 compression driver (same as TC2)

    Examples:
        >>> from viberesp.driver.test_drivers import get_tc4_compression_driver
        >>> driver = get_tc4_compression_driver()
        >>> driver.S_d  # Same as TC2
        0.0008  # m²

    Validation:
        TC4 validation data is available in tests/validation/horn_theory/exp_midrange_tc4/
        Use for testing complete horn system with both chambers.
    """
    # TC4 uses same driver as TC2
    return get_tc2_compression_driver()
