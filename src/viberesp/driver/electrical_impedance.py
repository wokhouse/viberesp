"""
Electrical impedance calculations for loudspeaker drivers.

This module implements the electrical impedance model for moving-coil
loudspeakers, including the coupling between electrical, mechanical,
and acoustic domains via the force factor BL.

Literature:
- COMSOL (2020), Figure 2 - Electro-mechano-acoustical equivalent circuit
- Small (1972) - Electrical impedance model
- Leach (1991) - Voice coil inductance model
- literature/thiele_small/comsol_lumped_loudspeaker_driver_2020.md
"""

import math
import cmath

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.simulation.constants import angular_frequency


def electrical_impedance_bare_driver(
    frequency: float,
    driver: ThieleSmallParameters,
    acoustic_load: complex = 0j,
    voice_coil_inductance_model: str = "constant"
) -> complex:
    """
    Calculate driver electrical impedance with mechanical/acoustic load.

    This function implements the complete electro-mechano-acoustical model
    of a moving-coil loudspeaker driver. The electrical impedance consists
    of three parts:

    1. Voice coil impedance: Z_vc = R_e + jωL_e
    2. Reflected mechanical impedance: Z_mech = (BL)² / Z_m
    3. Reflected acoustic impedance: Z_ac = (BL)² · Z_a / S_d²

    Literature:
        - COMSOL (2020), Figure 2 - Equivalent circuit model
        - Small (1972) - Electrical impedance analysis
        - literature/thiele_small/comsol_lumped_loudspeaker_driver_2020.md

    Equation:
        Z_e = R_e + jωL_e + (BL)² / Z_m_total

    where:
        Z_m_total = Z_mechanical + Z_acoustic_reflected
        Z_mechanical = R_ms + jωM_ms + 1/(jωC_ms)
        Z_acoustic_reflected = Z_a / S_d²
        ω = 2πf (angular frequency)

    Args:
        frequency: Frequency in Hz
        driver: ThieleSmallParameters instance
        acoustic_load: Acoustic radiation impedance (Pa·s/m³), default 0
                     (bare driver in vacuum, no acoustic load)
        voice_coil_inductance_model: "constant" or "leach" (for future implementation)

    Returns:
        Complex electrical impedance (Ω)
        - Real part: Resistance (Ω)
        - Imag part: Reactance (Ω)

    Examples:
        >>> from viberesp.driver.parameters import ThieleSmallParameters
        >>> driver = ThieleSmallParameters(
        ...     M_ms=0.054, C_ms=0.00019, R_ms=5.2,
        ...     R_e=3.1, L_e=0.72e-3, BL=16.5, S_d=0.0522
        ... )
        >>> Z = electrical_impedance_bare_driver(100, driver)
        >>> Z.real  # Resistance at 100 Hz
        >>> Z.imag  # Reactance at 100 Hz

        At resonance (F_s), impedance should show a peak:
        >>> Z_res = electrical_impedance_bare_driver(driver.F_s, driver)
        >>> abs(Z_res)  # Maximum impedance at F_s

    Validation:
        Compare with Hornresp electrical impedance for bare driver.
        Check impedance peak at F_s matches expected value.
    """
    # Validate inputs
    if frequency <= 0:
        raise ValueError(f"Frequency must be > 0, got {frequency} Hz")

    if not isinstance(driver, ThieleSmallParameters):
        raise TypeError(f"driver must be ThieleSmallParameters, got {type(driver)}")

    # Calculate angular frequency: ω = 2πf
    # Kinsler et al. (1982), Chapter 1
    omega = angular_frequency(frequency)

    # Voice coil electrical impedance: Z_vc = R_e + jωL_e
    # COMSOL (2020), Figure 2 - Electrical domain
    Z_voice_coil = complex(driver.R_e, omega * driver.L_e)

    # Mechanical impedance: Z_m = R_ms + jωM_ms + 1/(jωC_ms)
    # COMSOL (2020), Figure 2 - Mechanical domain
    # Mass: jωM_ms (inductive in impedance analogy)
    # Compliance: 1/(jωC_ms) (capacitive in impedance analogy)
    # Resistance: R_ms (resistive in impedance analogy)
    if frequency == 0:
        # DC case: mechanical impedance is infinite (compliance dominates)
        Z_mechanical = complex(0, float('inf'))
    else:
        Z_mechanical = driver.R_ms + complex(0, omega * driver.M_ms) + complex(0, -1 / (omega * driver.C_ms))

    # Acoustic impedance reflected to mechanical side: Z_a / S_d²
    # COMSOL (2020), Eq. 1-2 - Mechano-acoustic coupling
    # Force on diaphragm: F_D = ∫(Δp · n_z) dA ≈ p · S_d
    # This creates an impedance scaling of 1/S_d²
    Z_acoustic_reflected = acoustic_load / (driver.S_d ** 2)

    # Total mechanical impedance (including acoustic load)
    Z_mechanical_total = Z_mechanical + Z_acoustic_reflected

    # Reflected impedance from mechanical to electrical domain: Z_ref = (BL)² / Z_m
    # COMSOL (2020), Figure 2 - Coupling via controlled sources
    # Force: F = BL · i_c (Lorentz force)
    # Back EMF: V_back = BL · u_D
    # This creates a reflected impedance of (BL)² / Z_m
    if abs(Z_mechanical_total) == 0:
        # Avoid division by zero
        Z_reflected = complex(0, float('inf'))
    else:
        Z_reflected = (driver.BL ** 2) / Z_mechanical_total

    # Total electrical impedance: Z_e = Z_vc + Z_reflected
    # COMSOL (2020), Figure 2 - Series connection
    Z_electrical = Z_voice_coil + Z_reflected

    return Z_electrical


def electrical_impedance_at_resonance(driver: ThieleSmallParameters) -> complex:
    """
    Calculate electrical impedance at driver resonance frequency.

    At resonance (ω = ω_s = 1/√(M_ms·C_ms)), the mechanical mass and
    compliance reactances cancel, leaving only the mechanical resistance
    and acoustic load.

    Literature:
        - Small (1972) - Impedance at resonance
        - COMSOL (2020), Figure 2

    Args:
        driver: ThieleSmallParameters instance

    Returns:
        Complex electrical impedance at F_s (Ω)

    Examples:
        >>> driver = ThieleSmallParameters(0.05, 0.0002, 5, 8, 0.001, 10, 0.05)
        >>> Z_res = electrical_impedance_at_resonance(driver)
        >>> Z_res.real > driver.R_e  # Peak resistance at resonance
        True
    """
    return electrical_impedance_bare_driver(driver.F_s, driver, acoustic_load=0j)


def electrical_impedance_high_frequency_limit(
    driver: ThieleSmallParameters,
    frequency: float = 10000.0
) -> complex:
    """
    Calculate electrical impedance at high frequency (ω → ∞).

    At high frequency, the mechanical impedance is dominated by the mass
    (jωM_ms >> 1/jωC_ms), and the reflected impedance becomes negligible.

    Literature:
        - Small (1972) - High-frequency behavior

    Args:
        driver: ThieleSmallParameters instance
        frequency: High frequency to evaluate at (Hz), default 10 kHz

    Returns:
        Complex electrical impedance at high frequency (Ω)

    Examples:
        >>> driver = ThieleSmallParameters(0.05, 0.0002, 5, 8, 0.001, 10, 0.05)
        >>> Z_hf = electrical_impedance_high_frequency_limit(driver)
        >>> abs(Z_hf.real - driver.R_e) < 1  # Approaches R_e
        True
    """
    return electrical_impedance_bare_driver(frequency, driver, acoustic_load=0j)
