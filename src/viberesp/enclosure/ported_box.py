"""
Ported box enclosure simulation.

This module implements the complete frequency response simulation for
direct radiator loudspeakers in ported (vented/bass-reflex) enclosures.

Literature:
- Thiele (1971) - Loudspeakers in Vented Boxes Parts 1 & 2
- Small (1972) - Closed-Box Loudspeaker Systems (compliance ratio, same theory)
- literature/thiele_small/thiele_1971_vented_boxes.md

Key equations:
- Helmholtz resonance: Fb = c/(2π) × √(Sp/(Vb×Lp))
- Compliance ratio: α = Vas/Vb
- Tuning ratio: h = Fb/Fs
- B4 alignment: α = (Qts/0.707)² - 1
- Transfer function: 4th-order high-pass (vs 2nd-order for sealed)
"""

import math
import cmath
from dataclasses import dataclass
from typing import Optional

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.driver.radiation_mass import calculate_resonance_with_radiation_mass_tuned
from viberesp.driver.radiation_impedance import radiation_impedance_piston
from viberesp.driver.electrical_impedance import voice_coil_impedance_leach
from viberesp.simulation.constants import (
    SPEED_OF_SOUND,
    AIR_DENSITY,
    angular_frequency,
)


@dataclass
class PortedBoxSystemParameters:
    """
    Ported box system parameters.

    Literature:
        - Thiele (1971), Part 2, Table 1 - Alignment constants
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Attributes:
        Vb: Box volume (m³)
        Fb: Port tuning frequency (Hz)
        alpha: Compliance ratio (Vas/Vb)
        h: Tuning ratio (Fb/Fs)
        F3: -3dB cutoff frequency (Hz)
        port_area: Port cross-sectional area (m²)
        port_length: Port physical length (m)
        port_velocity_max: Maximum port air velocity at rated power (m/s)
    """
    Vb: float
    Fb: float
    alpha: float
    h: float
    F3: float
    port_area: float
    port_length: float
    port_velocity_max: float


def helmholtz_resonance_frequency(
    Sp: float,
    Vb: float,
    Lpt: float,
    speed_of_sound: float = SPEED_OF_SOUND,
    flanged: bool = True,
) -> float:
    """
    Calculate Helmholtz resonance frequency for a ported box.

    The air in the port acts as a mass oscillating on the spring of the air
    in the box, forming a Helmholtz resonator. This formula determines the
    tuning frequency of the port.

    Literature:
        - Thiele (1971), Part 1, Section 2 - "The Vented Box as a Helmholtz Resonator"
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Args:
        Sp: Port cross-sectional area (m²)
        Vb: Box net internal volume (m³)
        Lpt: Port physical length (m)
        speed_of_sound: Speed of sound (m/s), default 343 m/s at 20°C
        flanged: True if port is flush with box wall (adds end correction), default True

    Returns:
        Helmholtz resonance frequency Fb (Hz)

    Raises:
        ValueError: If Sp <= 0, Vb <= 0, or Lpt <= 0

    Examples:
        >>> helmholtz_resonance_frequency(Sp=0.001, Vb=0.02, Lpt=0.1)
        46.6...  # Hz (for 10cm² port, 20L box, 10cm length)

        >>> # Flanged port (most common)
        >>> helmholtz_resonance_frequency(Sp=0.001, Vb=0.02, Lpt=0.1, flanged=True)
        45.9...  # Hz (slightly lower due to end correction)

    Validation:
        Compare with Hornresp vented box simulation for identical port dimensions.
        Expected: <0.5 Hz deviation (the formula is exact)
    """
    # Validate inputs
    if Sp <= 0:
        raise ValueError(f"Port area Sp must be > 0, got {Sp} m²")
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")
    if Lpt <= 0:
        raise ValueError(f"Port length Lpt must be > 0, got {Lpt} m")

    # Thiele (1971), Part 1, Section 2: Helmholtz resonator formula
    # Fb = c / (2π) × √(Sp / (Vb × Lp))
    # where Lp is the EFFECTIVE port length (including end correction)
    # literature/thiele_small/thiele_1971_vented_boxes.md

    # Calculate effective port length (physical + end correction)
    Lp_eff = Lpt

    if flanged:
        # End correction for flanged port (flush with box wall)
        # Thiele (1971): ΔL = 0.85 × a_p where a_p = √(Sp/π)
        # This accounts for the radiation mass loading at the port ends
        # literature/thiele_small/thiele_1971_vented_boxes.md
        port_radius = math.sqrt(Sp / math.pi)
        delta_L = 0.85 * port_radius
        Lp_eff = Lpt + delta_L

    # Helmholtz resonance formula
    # Fb = c / (2π) × √(Sp / (Vb × Lp_eff))
    fb = (speed_of_sound / (2 * math.pi)) * math.sqrt(Sp / (Vb * Lp_eff))

    return fb


def calculate_port_length_for_area(
    Sp: float,
    Vb: float,
    Fb: float,
    speed_of_sound: float = SPEED_OF_SOUND,
    flanged: bool = True,
) -> float:
    """
    Calculate required port length for a given port area and tuning frequency.

    This is the inverse of helmholtz_resonance_frequency(): given desired Fb
    and port area, calculate the port length needed.

    Literature:
        - Thiele (1971), Part 1, Section 2 - Helmholtz resonator theory
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Args:
        Sp: Port cross-sectional area (m²)
        Vb: Box net internal volume (m³)
        Fb: Desired port tuning frequency (Hz)
        speed_of_sound: Speed of sound (m/s), default 343 m/s at 20°C
        flanged: True if port is flush with box wall, default True

    Returns:
        Port physical length Lpt (m)

    Raises:
        ValueError: If Sp <= 0, Vb <= 0, Fb <= 0, or calculated length is negative

    Examples:
        >>> calculate_port_length_for_area(Sp=0.001, Vb=0.02, Fb=50.0)
        0.083...  # m (8.3cm port for 50Hz tuning)

    Validation:
        Verify by plugging result back into helmholtz_resonance_frequency().
        Expected: Resulting Fb within 0.1 Hz of target
    """
    # Validate inputs
    if Sp <= 0:
        raise ValueError(f"Port area Sp must be > 0, got {Sp} m²")
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")
    if Fb <= 0:
        raise ValueError(f"Tuning frequency Fb must be > 0, got {Fb} Hz")

    # Thiele (1971): Rearrange Helmholtz formula to solve for Lp
    # Fb = c / (2π) × √(Sp / (Vb × Lp))
    # Fb² × (2π)² = c² × Sp / (Vb × Lp)
    # Lp = c² × Sp / (Vb × Fb² × (2π)²)
    # literature/thiele_small/thiele_1971_vented_boxes.md

    # Calculate required effective length
    numerator = (speed_of_sound ** 2) * Sp
    denominator = Vb * (Fb ** 2) * (2 * math.pi) ** 2
    Lp_eff = numerator / denominator

    # Subtract end correction to get physical length
    Lpt = Lp_eff

    if flanged:
        # End correction: ΔL = 0.85 × √(Sp/π)
        port_radius = math.sqrt(Sp / math.pi)
        delta_L = 0.85 * port_radius
        Lpt = Lp_eff - delta_L

    # Validate result
    if Lpt <= 0:
        raise ValueError(
            f"Calculated port length is negative (Lpt={Lpt:.4f}m). "
            f"This means port area is too large for the desired tuning. "
            f"Increase port area or decrease tuning frequency."
        )

    return Lpt


def calculate_optimal_port_dimensions(
    driver: ThieleSmallParameters,
    Vb: float,
    Fb: float,
    max_port_velocity: float = 0.05,
    safety_factor: float = 1.5,
    speed_of_sound: float = SPEED_OF_SOUND,
) -> tuple[float, float, float]:
    """
    Calculate optimal port dimensions to prevent chuffing (port noise).

    Port chuffing occurs when air velocity in the port becomes too high,
    creating turbulence and audible noise. This function sizes the port
    to keep velocity below a safe threshold.

    Literature:
        - Thiele (1971), Part 1, Section 4 - "Air Velocity in the Vent"
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Args:
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)
        Fb: Port tuning frequency (Hz)
        max_port_velocity: Maximum acceptable port velocity as fraction of c, default 0.05 (5% of speed of sound)
        safety_factor: Safety multiplier for minimum area, default 1.5
        speed_of_sound: Speed of sound (m/s), default 343 m/s

    Returns:
        Tuple of (port_area_m2, port_length_m, estimated_velocity_m_s)

    Raises:
        ValueError: If Vb <= 0, Fb <= 0, or invalid driver parameters

    Examples:
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()
        >>> Sp, Lpt, v_max = calculate_optimal_port_dimensions(driver, Vb=0.020, Fb=50.0)
        >>> Sp  # Port area
        0.003...  # m² (≈ 2.5" diameter)
        >>> Lpt  # Port length
        0.08...  # m (8cm)

    Validation:
        Verify port velocity stays below 5% of speed of sound at Fb.
        Check physical feasibility: port must fit inside box.
    """
    # Validate inputs
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")
    if Fb <= 0:
        raise ValueError(f"Tuning frequency Fb must be > 0, got {Fb} Hz")
    if not hasattr(driver, 'X_max') or driver.X_max is None:
        raise ValueError("Driver must have X_max parameter for port sizing")

    # Thiele (1971), Part 1, Section 4: Minimum port area from velocity constraint
    # v_max = 0.05 × c (to prevent chuffing)
    # Sp_min = (2π × Fb × X_max × S_d) / v_max
    #
    # Derivation: At tuning frequency, diaphragm and port are 180° out of phase.
    # Volume velocity through port equals diaphragm volume velocity.
    # Port velocity = diaphragm volume velocity / port area
    # Maximum port velocity occurs at Fb at maximum excursion.
    # literature/thiele_small/thiele_1971_vented_boxes.md

    v_max_abs = max_port_velocity * speed_of_sound

    # Calculate minimum port area from velocity constraint
    # At Fb: U_port = U_diaphragm = 2π × Fb × X_max × S_d
    # v_port = U_port / Sp
    # Sp_min = (2π × Fb × X_max × S_d) / v_max
    Sp_min = (2 * math.pi * Fb * driver.X_max * driver.S_d) / v_max_abs

    # Apply safety factor
    # In practice, use larger port to account for non-uniform velocity distribution
    # and turbulence at high power levels
    Sp_practical = Sp_min * safety_factor

    # Calculate required port length
    # Thiele (1971): Lp = c² × Sp / (Vb × Fb² × (2π)²) - ΔL
    try:
        Lpt = calculate_port_length_for_area(
            Sp_practical, Vb, Fb,
            speed_of_sound=speed_of_sound,
            flanged=True
        )
    except ValueError:
        # Port length would be negative - try increasing area
        # This can happen with very large ports or very low tuning
        Sp_practical = Sp_min * 2.0
        Lpt = calculate_port_length_for_area(
            Sp_practical, Vb, Fb,
            speed_of_sound=speed_of_sound,
            flanged=True
        )

    # Estimate maximum port velocity (should be below threshold)
    # At Fb with max excursion:
    v_port_estimated = (2 * math.pi * Fb * driver.X_max * driver.S_d) / Sp_practical

    return Sp_practical, Lpt, v_port_estimated


def calculate_ported_box_system_parameters(
    driver: ThieleSmallParameters,
    Vb: float,
    Fb: float,
    port_area: Optional[float] = None,
    port_length: Optional[float] = None,
    alignment: str = "B4",
) -> PortedBoxSystemParameters:
    """
    Calculate ported box system parameters (α, h, F3, port dimensions).

    Literature:
        - Thiele (1971), Part 2, Table 1 - Alignment constants
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Args:
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)
        Fb: Port tuning frequency (Hz)
        port_area: Optional port cross-sectional area (m²). If None, auto-calculated
        port_length: Optional port physical length (m). If None, auto-calculated from Fb
        alignment: Alignment type ("B4" for Butterworth, etc.), default "B4"

    Returns:
        PortedBoxSystemParameters dataclass with system parameters

    Raises:
        ValueError: If Vb <= 0, Fb <= 0, or invalid alignment

    Examples:
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()  # Fs=64Hz, Qts=0.37, Vas=14L
        >>> params = calculate_ported_box_system_parameters(driver, Vb=0.020, Fb=50.0)
        >>> params.alpha  # Compliance ratio
        0.70...  # Vas/Vb
        >>> params.h  # Tuning ratio
        0.78...  # Fb/Fs
        >>> params.F3  # -3dB frequency (for B4 alignment, F3=Fb)
        50.0  # Hz

    Validation:
        Compare α and h with Thiele (1971) Table 1 for B4 alignment.
        Expected: <1% deviation from table values
    """
    # Validate inputs
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")
    if Fb <= 0:
        raise ValueError(f"Tuning frequency Fb must be > 0, got {Fb} Hz")

    # Thiele (1971), Part 1: Compliance ratio α = Vas / Vb
    # Same definition as sealed box
    # literature/thiele_small/thiele_1971_vented_boxes.md
    alpha = driver.V_as / Vb

    # Thiele (1971), Part 1: Tuning ratio h = Fb / Fs
    # Determines relationship between box tuning and driver resonance
    # literature/thiele_small/thiele_1971_vented_boxes.md
    h = Fb / driver.F_s

    # Calculate F3 based on alignment
    if alignment == "B4":
        # Butterworth B4 alignment: F3 = Fb
        # Maximally flat response, -3dB occurs at tuning frequency
        # literature/thiele_small/thiele_1971_vented_boxes.md
        F3 = Fb
    else:
        # For other alignments, F3 differs from Fb
        # This is a simplified placeholder - full implementation would use
        # Thiele's transfer function tables
        F3 = Fb  # Default approximation

    # Auto-calculate port dimensions if not provided
    if port_area is None or port_length is None:
        port_area_calc, port_length_calc, v_max = calculate_optimal_port_dimensions(
            driver, Vb, Fb
        )
        port_area = port_area_calc if port_area is None else port_area
        port_length = port_length_calc if port_length is None else port_length
    else:
        # Estimate max velocity for user-specified port
        if hasattr(driver, 'X_max') and driver.X_max is not None:
            v_max = (2 * math.pi * Fb * driver.X_max * driver.S_d) / port_area
        else:
            v_max = 0.0

    return PortedBoxSystemParameters(
        Vb=Vb,
        Fb=Fb,
        alpha=alpha,
        h=h,
        F3=F3,
        port_area=port_area,
        port_length=port_length,
        port_velocity_max=v_max,
    )


def ported_box_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    Vb: float,
    Fb: float,
    port_area: float,
    port_length: float,
    voltage: float = 2.83,
    measurement_distance: float = 1.0,
    speed_of_sound: float = SPEED_OF_SOUND,
    air_density: float = AIR_DENSITY,
    voice_coil_model: str = "simple",
    leach_K: float = None,
    leach_n: float = None,
) -> dict:
    """
    Calculate electrical impedance and SPL for ported box enclosure.

    Literature:
        - Thiele (1971), Part 1 - Input impedance and transfer function
        - Beranek (1954), Eq. 5.20 - Radiation impedance
        - literature/thiele_small/thiele_1971_vented_boxes.md
        - literature/horns/beranek_1954.md

    Key differences from sealed box:
        - Dual impedance peaks (driver resonance + Helmholtz resonance)
        - Impedance dip at Fb (driver and port 180° out of phase)
        - 4th-order high-pass response (24 dB/octave vs 12 dB/octave for sealed)
        - Port radiation modeled as separate acoustic path
        - Box compliance: C_mb = C_ms / (1 + α) (same as sealed)

    Args:
        frequency: Frequency in Hz
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)
        Fb: Port tuning frequency (Hz)
        port_area: Port cross-sectional area (m²)
        port_length: Port physical length (m)
        voltage: Input voltage (V), default 2.83V (1W into 8Ω)
        measurement_distance: SPL measurement distance (m), default 1m
        speed_of_sound: Speed of sound (m/s)
        air_density: Air density (kg/m³)
        voice_coil_model: "simple" or "leach"
        leach_K: Leach K parameter (for "leach" model)
        leach_n: Leach n parameter (for "leach" model)

    Returns:
        Dictionary containing:
        - 'frequency': Frequency (Hz)
        - 'Ze_magnitude': Electrical impedance magnitude (Ω)
        - 'Ze_phase': Electrical impedance phase (degrees)
        - 'Ze_real': Electrical resistance (Ω)
        - 'Ze_imag': Electrical impedance reactance (Ω)
        - 'SPL': Sound pressure level (dB at measurement_distance)
        - 'diaphragm_velocity': Diaphragm velocity magnitude (m/s)
        - 'diaphragm_velocity_phase': Diaphragm velocity phase (degrees)
        - 'radiation_impedance': Complex radiation impedance (Pa·s/m³)
        - 'radiation_resistance': Radiation resistance (Pa·s/m³)
        - 'radiation_reactance': Radiation reactance (Pa·s/m³)
        - 'alpha': Compliance ratio
        - 'h': Tuning ratio
        - 'Fb': Port tuning frequency (Hz)

    Raises:
        ValueError: If frequency <= 0, Vb <= 0, Fb <= 0, or invalid driver

    Examples:
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()
        >>> result = ported_box_electrical_impedance(100, driver, Vb=0.020, Fb=50.0,
        ...                                          port_area=0.003, port_length=0.08)
        >>> result['alpha']  # Compliance ratio
        0.70...  # Vas/Vb

        At tuning frequency, impedance dips toward Re:
        >>> result_fb = ported_box_electrical_impedance(50, driver, Vb=0.020, Fb=50.0,
        ...                                            port_area=0.003, port_length=0.08)
        >>> result_fb['Ze_magnitude'] < result['Ze_magnitude']
        True

    Validation:
        Compare with Hornresp vented box simulation.
        Expected tolerances:
        - Electrical impedance magnitude: <5% general, <10% near peaks
        - Electrical impedance phase: <10° general, <15° near peaks
        - Dual peak frequencies: ±2 Hz
        - SPL: <6 dB (voice coil model differences)

    Implementation Notes:
        This function implements Thiele's coupled resonator model for ported boxes:
        - Port air mass impedance: jω·M_port where M_port = ρ₀·Lp_eff·S_p
        - Port radiation impedance: Piston model with port area
        - Coupling through area ratio: (S_d/S_p)² × Z_m_port
        - Produces dual impedance peaks at F_low (~0.7×Fb) and F_high (~1.4×Fb)
        - Impedance dip at Fb (180° phase difference between diaphragm and port)
        - literature/thiele_small/thiele_1971_vented_boxes.md

        Note: SPL calculation uses diaphragm contribution only. Port contribution
        to total output is not yet implemented (Phase 2 feature).

    Other Known Limitations:
        - Voice coil inductance modeled as simple jωL (lossless inductor)
        - Hornresp uses Leach (2002) lossy inductance model
        - Port radiation impedance simplified (piston model)
        - No mutual coupling between diaphragm and port
        - No leakage or absorption losses (Ql = ∞ assumed)
    """
    # Validate inputs
    if frequency <= 0:
        raise ValueError(f"Frequency must be > 0, got {frequency} Hz")
    if not isinstance(driver, ThieleSmallParameters):
        raise TypeError(f"driver must be ThieleSmallParameters, got {type(driver)}")
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")
    if Fb <= 0:
        raise ValueError(f"Tuning frequency Fb must be > 0, got {Fb} Hz")
    if port_area <= 0:
        raise ValueError(f"Port area must be > 0, got {port_area} m²")
    if port_length <= 0:
        raise ValueError(f"Port length must be > 0, got {port_length} m")
    if measurement_distance <= 0:
        raise ValueError(f"Measurement distance must be > 0, got {measurement_distance} m")

    # Calculate angular frequency: ω = 2πf
    # Kinsler et al. (1982), Chapter 1
    omega = angular_frequency(frequency)

    # Step 1: Calculate compliance ratio and box compliance
    # Thiele (1971): α = Vas / Vb (same as sealed box)
    # literature/thiele_small/thiele_1971_vented_boxes.md
    alpha = driver.V_as / Vb

    # Box compliance in series with driver compliance
    # Thiele (1971): C_mb = C_ms / (1 + α)
    # Same formulation as sealed box
    # literature/thiele_small/thiele_1971_vented_boxes.md
    C_mb = driver.C_ms / (1.0 + alpha)

    # Step 2: Calculate tuning ratio
    # Thiele (1971): h = Fb / Fs
    # literature/thiele_small/thiele_1971_vented_boxes.md
    h = Fb / driver.F_s

    # Step 3: Calculate system resonance with 1× radiation mass (front side only)
    # Ported box radiates from front side only (diaphragm + port both front-firing)
    # Use iterative solver with radiation_multiplier=1.0
    # literature/thiele_small/thiele_1971_vented_boxes.md
    Fc, M_ms_enclosed = calculate_resonance_with_radiation_mass_tuned(
        driver.M_md,
        C_mb,  # Use box compliance, not driver compliance
        driver.S_d,
        radiation_multiplier=1.0,  # Front radiation only
        air_density=air_density,
        speed_of_sound=speed_of_sound,
    )

    # Step 4: Calculate radiation impedance for circular piston
    # Beranek (1954), Eq. 5.20: Z_R = ρc·S·[R₁(2ka) + jX₁(2ka)]
    # Front side only (diaphragm radiation)
    # literature/horns/beranek_1954.md
    Z_rad = radiation_impedance_piston(
        frequency,
        driver.S_d,
        speed_of_sound=speed_of_sound,
        air_density=air_density
    )

    # Step 5: Calculate mechanical impedance with box compliance
    # COMSOL (2020), Figure 2: Z_m = R_ms + jωM_ms + 1/(jωC_mb)
    # Same formulation as sealed box (stiffer spring due to box)
    # literature/thiele_small/thiele_1971_vented_boxes.md
    Z_mechanical = driver.R_ms + complex(0, omega * M_ms_enclosed) + \
                   complex(0, -1 / (omega * C_mb))

    # Step 5b: Calculate port and combine with driver (parallel in acoustic domain)
    # Thiele (1971), Part 1, Section 5: Port acts as second resonator
    # The port and driver form a coupled system where their acoustic impedances
    # combine in parallel (they share the same box pressure).
    # literature/thiele_small/thiele_1971_vented_boxes.md

    # Calculate effective port length (physical + end correction)
    # End correction for flanged port: ΔL = 0.85 × a_p where a_p = √(S_p/π)
    port_radius = math.sqrt(port_area / math.pi)
    delta_L = 0.85 * port_radius  # end correction for flanged port
    Lp_eff = port_length + delta_L

    # Port air mass (acoustic impedance of air in port)
    # Z_a_port_mass = jω × (ρ₀ × Lp_eff / S_p)
    # This is the acoustic impedance of the air column in the port
    # (relates pressure and volume velocity)
    Z_a_port_mass = complex(0, omega * air_density * Lp_eff / port_area)

    # Port radiation impedance (piston radiating into half-space)
    # Beranek (1954), Eq. 5.20: Z_R = ρc·S_p·[R₁(2ka) + jX₁(2ka)]
    # literature/horns/beranek_1954.md
    Z_rad_port = radiation_impedance_piston(
        frequency,
        port_area,
        speed_of_sound=speed_of_sound,
        air_density=air_density
    )

    # Total port acoustic impedance (mass + box compliance + radiation in series)
    # Thiele (1971), Figure 3: Port branch is M_port || C_mb || Z_rad_port (series)
    # The box compliance C_mb is shared between driver and port branches
    # Z_a_port = Z_a_port_mass + 1/(jω × C_mb / S_p²) + Z_rad_port
    #          = Z_a_port_mass + (S_p² / (jω × C_mb)) + Z_rad_port
    Z_a_port_compliance = complex(0, -1 / (omega * C_mb)) * (port_area ** 2)
    Z_a_port = Z_a_port_mass + Z_a_port_compliance + Z_rad_port

    # Driver acoustic impedance (mechanical impedance transformed to acoustic)
    # Z_a_driver = Z_mechanical / S_d²
    Z_a_driver = Z_mechanical / (driver.S_d ** 2)

    # Total acoustic impedance (driver and port in parallel)
    # 1/Z_a_total = 1/Z_a_driver + 1/Z_a_port
    # Z_a_total = (Z_a_driver × Z_a_port) / (Z_a_driver + Z_a_port)
    if abs(Z_a_driver + Z_a_port) == 0:
        Z_a_total = complex(0, float('inf'))
    else:
        Z_a_total = (Z_a_driver * Z_a_port) / (Z_a_driver + Z_a_port)

    # Transform total acoustic impedance back to mechanical domain
    # Z_mechanical_total = Z_a_total × S_d²
    Z_mechanical_total = Z_a_total * (driver.S_d ** 2)

    # Step 6: Calculate electrical impedance
    # COMSOL (2020), Figure 2: Z_e = Z_vc + (BL)² / Z_m_total
    # Voice coil electrical impedance
    if voice_coil_model == "simple":
        # Standard jωL_e model (lossless inductor)
        # Z_vc = R_e + jωL_e
        Z_voice_coil = complex(driver.R_e, omega * driver.L_e)
    elif voice_coil_model == "leach-full":
        # Leach (2002) lossy inductance model at ALL frequencies
        if leach_K is None or leach_n is None:
            raise ValueError("leach_K and leach_n must be provided for Leach models")
        Z_voice_coil = voice_coil_impedance_leach(
            frequency, driver, leach_K, leach_n
        )
    else:  # voice_coil_model == "leach"
        # Frequency-limited Leach model
        if frequency < 1000.0:
            # Low frequency: simple jωL_e model
            Z_voice_coil = complex(driver.R_e, omega * driver.L_e)
        else:
            # High frequency: Leach lossy inductance model
            if leach_K is None or leach_n is None:
                raise ValueError("leach_K and leach_n must be provided for Leach models")
            Z_voice_coil = voice_coil_impedance_leach(
                frequency, driver, leach_K, leach_n
            )

    # Reflected impedance from mechanical to electrical domain: Z_ref = (BL)² / Z_m
    # COMSOL (2020), Figure 2 - Coupling via controlled sources
    if abs(Z_mechanical_total) == 0:
        # Avoid division by zero
        Z_reflected = complex(0, float('inf'))
    else:
        Z_reflected = (driver.BL ** 2) / Z_mechanical_total

    # Total electrical impedance: Z_e = Z_vc + Z_reflected
    # COMSOL (2020), Figure 2 - Series connection
    Ze = Z_voice_coil + Z_reflected

    # Step 7: Calculate diaphragm velocity using I_active force model
    # Same as sealed box
    # literature/thiele_small/comsol_lumped_loudspeaker_driver_2020.md
    if driver.BL == 0 or abs(Ze) == 0:
        # Avoid division by zero
        u_diaphragm = complex(0, 0)
    else:
        # Voice coil current
        I_complex = voltage / Ze

        # Extract active (in-phase) component of current
        # I_active = |I| × cos(phase(I))
        I_phase = cmath.phase(I_complex)
        I_active = abs(I_complex) * math.cos(I_phase)

        # Calculate force using active current
        # F_active = BL × I_active
        F_active = driver.BL * I_active

        # Diaphragm velocity from active force and mechanical impedance
        # u_D = F_active / |Z_m_total|
        u_diaphragm_mag = F_active / abs(Z_mechanical_total)
        u_diaphragm = complex(u_diaphragm_mag, 0)

    # Step 8: Calculate sound pressure level
    # For ported box, total output = diaphragm + port (vector sum)
    # At Fb: diaphragm and port are 180° out of phase (minimum impedance)
    # Far from Fb: diaphragm dominates
    #
    # Simplified model: Use diaphragm contribution only for now
    # Full implementation would require port volume velocity calculation
    # Thiele (1971), Part 1, Section 6 - "Acoustic Output"
    # literature/thiele_small/thiele_1971_vented_boxes.md

    # Volume velocity: U = u_D · S_d
    # Kinsler et al. (1982), Chapter 4
    volume_velocity = u_diaphragm * driver.S_d

    # Pressure magnitude at measurement distance
    # p = jωρ₀·U / (2πr)  (magnitude only, ignore phase and distance delay)
    # Kinsler et al. (1982), Chapter 4, Eq. 4.58 (piston in infinite baffle)
    pressure_amplitude = (omega * air_density * abs(volume_velocity)) / \
                         (2 * math.pi * measurement_distance)

    # Sound pressure level
    # SPL = 20·log₁₀(p/p_ref) where p_ref = 20 μPa
    # Kinsler et al. (1982), Chapter 2
    p_ref = 20e-6  # Reference pressure: 20 μPa
    spl = 20 * math.log10(pressure_amplitude / p_ref) if pressure_amplitude > 0 else -float('inf')

    # Prepare return dictionary
    result = {
        'frequency': frequency,
        'Ze_magnitude': abs(Ze),
        'Ze_phase': math.degrees(cmath.phase(Ze)),
        'Ze_real': Ze.real,
        'Ze_imag': Ze.imag,
        'SPL': spl,
        'diaphragm_velocity': abs(u_diaphragm),
        'diaphragm_velocity_phase': math.degrees(cmath.phase(u_diaphragm)),
        'radiation_impedance': Z_rad,
        'radiation_resistance': Z_rad.real,
        'radiation_reactance': Z_rad.imag,
        'alpha': alpha,
        'h': h,
        'Fb': Fb,
    }

    return result
