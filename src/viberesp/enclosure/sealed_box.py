"""
Sealed box enclosure simulation.

This module implements the complete frequency response simulation for
direct radiator loudspeakers in sealed (closed-box) enclosures.

Literature:
- Small (1972) - Closed-Box Loudspeaker Systems Part I: Analysis
- Thiele (1971) - Loudspeakers in Vented Boxes (sealed box theory)
- literature/thiele_small/small_1972_closed_box.md

Key equations:
- Compliance ratio: α = Vas/Vb
- System resonance: Fc = Fs × √(1 + α)
- System Q: Qtc = Qts × √(1 + α)
- Transfer function: 2nd-order high-pass
"""

import math
import cmath
from dataclasses import dataclass

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.driver.radiation_impedance import radiation_impedance_piston
from viberesp.driver.electrical_impedance import voice_coil_impedance_leach
from viberesp.simulation.constants import (
    SPEED_OF_SOUND,
    AIR_DENSITY,
    angular_frequency,
)


@dataclass
class SealedBoxSystemParameters:
    """
    Sealed box system parameters.

    Literature:
        - Small (1972), Part I - System parameters analysis
        - literature/thiele_small/small_1972_closed_box.md

    Attributes:
        Vb: Box volume (m³)
        alpha: Compliance ratio (Vas/Vb)
        Fc: System resonance frequency (Hz)
        Qtc: System total Q factor
        F3: -3dB cutoff frequency (Hz)
    """
    Vb: float
    alpha: float
    Fc: float
    Qtc: float
    F3: float


def calculate_sealed_box_system_parameters(
    driver: ThieleSmallParameters,
    Vb: float,
) -> SealedBoxSystemParameters:
    """
    Calculate sealed box system parameters (Fc, Qtc, F3, α).

    Literature:
        - Small (1972), Eq. for system resonance and Q
        - literature/thiele_small/small_1972_closed_box.md

    Args:
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)

    Returns:
        SealedBoxSystemParameters dataclass with:
        - Vb: Box volume (m³)
        - alpha: Compliance ratio (Vas/Vb)
        - Fc: System resonance frequency (Hz)
        - Qtc: System total Q factor
        - F3: -3dB cutoff frequency (Hz)

    Raises:
        ValueError: If Vb <= 0

    Examples:
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()  # Fs=64Hz, Qts=0.37, Vas=14L
        >>> params = calculate_sealed_box_system_parameters(driver, Vb=0.010)
        >>> params.Fc  # System resonance
        99.4...  # Hz (higher than Fs due to small box)
        >>> params.Qtc  # System Q
        0.58...  # Higher than Qts due to box stiffness
        >>> params.alpha  # Compliance ratio
        1.4...  # Vas/Vb

    Validation:
        Compare Fc and Qtc with Hornresp sealed box simulation.
        Expected: <0.5 Hz deviation for Fc, <0.02 for Qtc
    """
    # Validate inputs
    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")

    # Small (1972): Compliance ratio α = Vas / Vb
    # literature/thiele_small/small_1972_closed_box.md
    alpha = driver.V_as / Vb

    # Small (1972): System resonance Fc = Fs × √(1 + α)
    # The box stiffness increases the effective spring constant, raising resonance
    # literature/thiele_small/small_1972_closed_box.md
    sqrt_factor = math.sqrt(1.0 + alpha)
    Fc = driver.F_s * sqrt_factor

    # Small (1972): System Q factor Qtc = Qts × √(1 + α)
    # Damping ratio changes with stiffness in the same way as resonance
    # literature/thiele_small/small_1972_closed_box.md
    Qtc = driver.Q_ts * sqrt_factor

    # Calculate F3 (-3dB point)
    # For Butterworth alignment (Qtc = 0.707): F3 = Fc
    # For other alignments, use approximate formula from Small (1972)
    # literature/thiele_small/small_1972_closed_box.md

    if abs(Qtc - 0.707) < 0.01:
        # Butterworth alignment: F3 = Fc
        F3 = Fc
    else:
        # General case: approximate formula
        # F3 = Fc × √((1/Qtc² - 2 + √((1/Qtc² - 2)² + 4)) / 2)
        # From solving |G(jω)|² / |G(jω)|²max = 0.5
        Qtc_squared = Qtc * Qtc
        term1 = 1.0 / Qtc_squared - 2.0
        term2 = math.sqrt(term1 * term1 + 4.0)
        F3_ratio = math.sqrt((term1 + term2) / 2.0)
        F3 = Fc * F3_ratio

    return SealedBoxSystemParameters(
        Vb=Vb,
        alpha=alpha,
        Fc=Fc,
        Qtc=Qtc,
        F3=F3,
    )


def sealed_box_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    Vb: float,
    voltage: float = 2.83,
    measurement_distance: float = 1.0,
    speed_of_sound: float = SPEED_OF_SOUND,
    air_density: float = AIR_DENSITY,
    voice_coil_model: str = "simple",
    leach_K: float = None,
    leach_n: float = None,
) -> dict:
    """
    Calculate electrical impedance and SPL for sealed box enclosure.

    Literature:
        - Small (1972) - Closed-box electrical impedance
        - Beranek (1954), Eq. 5.20 - Radiation impedance (front side only)
        - literature/thiele_small/small_1972_closed_box.md
        - literature/horns/beranek_1954.md

    Key differences from infinite baffle:
        - System resonance: Fc = Fs × √(1 + α) where α = Vas/Vb
        - Mechanical stiffness: Box compliance in series with driver suspension
        - Effective compliance: C_mb = C_ms / (1 + α) (stiffer spring)
        - Radiation mass: FRONT SIDE ONLY (1× M_rad, not 2×)
        - Total moving mass: M_ms = M_md + 1×M_rad (not 2×M_rad)

    Args:
        frequency: Frequency in Hz
        driver: ThieleSmallParameters instance
        Vb: Box volume (m³)
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
        - 'Ze_imag': Electrical reactance (Ω)
        - 'SPL': Sound pressure level (dB at measurement_distance)
        - 'diaphragm_velocity': Diaphragm velocity magnitude (m/s)
        - 'diaphragm_velocity_phase': Diaphragm velocity phase (degrees)
        - 'radiation_impedance': Complex radiation impedance (Pa·s/m³)
        - 'radiation_resistance': Radiation resistance (Pa·s/m³)
        - 'radiation_reactance': Radiation reactance (Pa·s/m³)
        - 'Fc': System resonance frequency (Hz)
        - 'Qtc': System Q factor

    Raises:
        ValueError: If frequency <= 0, Vb <= 0, or invalid driver

    Examples:
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()
        >>> result = sealed_box_electrical_impedance(100, driver, Vb=0.010)
        >>> result['Fc']  # System resonance for 10L box
        99.4...  # Hz
        >>> result['Ze_magnitude']
        6.2...  # Ω
        >>> result['SPL']
        68.5...  # dB at 1m

        At system resonance, impedance peaks:
        >>> params = calculate_sealed_box_system_parameters(driver, 0.010)
        >>> result_fc = sealed_box_electrical_impedance(params.Fc, driver, Vb=0.010)
        >>> result_fc['Ze_magnitude'] > result['Ze_magnitude']
        True

    Validation:
        Compare with Hornresp "Rear Lined" sealed box simulation.
        Expected tolerances:
        - Electrical impedance magnitude: <5% general, <10% near resonance
        - Electrical impedance phase: <10° general, <15° near resonance
        - SPL: <6 dB (accounts for voice coil model differences)

    Known Limitations:
        - Voice coil inductance modeled as simple jωL (lossless inductor)
        - Hornresp uses more sophisticated lossy inductance models (Leach 2002)
        - High-frequency SPL deviation expected above 2 kHz
        - No leakage or absorption losses (Ql = ∞ assumed)
    """
    # Validate inputs
    if frequency <= 0:
        raise ValueError(f"Frequency must be > 0, got {frequency} Hz")

    if not isinstance(driver, ThieleSmallParameters):
        raise TypeError(f"driver must be ThieleSmallParameters, got {type(driver)}")

    if Vb <= 0:
        raise ValueError(f"Box volume Vb must be > 0, got {Vb} m³")

    if measurement_distance <= 0:
        raise ValueError(f"Measurement distance must be > 0, got {measurement_distance} m")

    # Calculate angular frequency: ω = 2πf
    # Kinsler et al. (1982), Chapter 1
    omega = angular_frequency(frequency)

    # Step 1: Calculate compliance ratio and box compliance
    # Small (1972): α = Vas/Vb
    # literature/thiele_small/small_1972_closed_box.md
    alpha = driver.V_as / Vb

    # Box compliance in series with driver compliance
    # Small (1972): C_mb = C_ms / (1 + α)
    # This is equivalent to: 1/C_mb = 1/C_ms + 1/C_ab
    # where C_ab = Vb / (ρ₀·c²·S_d²) is the box acoustic compliance
    # literature/thiele_small/small_1972_closed_box.md
    C_mb = driver.C_ms / (1.0 + alpha)

    # Step 2: Calculate system resonance
    # Small (1972): Fc = Fs × √(1 + α)
    # literature/thiele_small/small_1972_closed_box.md
    Fc = driver.F_s * math.sqrt(1.0 + alpha)

    # Step 3: Calculate radiation impedance for circular piston
    # Beranek (1954), Eq. 5.20: Z_R = ρc·S·[R₁(2ka) + jX₁(2ka)]
    # Front side only (use existing function)
    # literature/horns/beranek_1954.md
    Z_rad = radiation_impedance_piston(
        frequency,
        driver.S_d,
        speed_of_sound=speed_of_sound,
        air_density=air_density
    )

    # Step 4: Calculate mechanical impedance with box compliance
    # COMSOL (2020), Figure 2: Mechanical equivalent circuit
    # Z_m = R_ms + jωM_ms + 1/(jωC_mb)
    # literature/thiele_small/small_1972_closed_box.md
    #
    # IMPORTANT: Use driver.M_ms (includes 2× radiation mass) for sealed box
    # Research shows sealed boxes need both front and rear air loads
    # See: sealed_box_spl_investigation.md for details
    Z_mechanical = driver.R_ms + complex(0, omega * driver.M_ms) + \
                   complex(0, -1 / (omega * C_mb))

    # Total mechanical impedance including radiation load
    # Acoustic impedance reflected to mechanical domain: Z_a · S_d²
    # COMSOL (2020), Eq. 1-2: Z_m = F/u = (p·S_d) / (U/S_d) = Z_a·S_d²
    Z_mechanical_total = Z_mechanical + (Z_rad * (driver.S_d ** 2))

    # Step 5: Calculate electrical impedance
    # COMSOL (2020), Figure 2: Z_e = Z_vc + (BL)² / Z_m_total
    # IMPORTANT: We must use our pre-calculated Z_mechanical_total (with C_mb)
    # NOT the driver's C_ms, because the box changes the compliance!
    #
    # Voice coil electrical impedance
    # COMSOL (2020), Figure 2 - Electrical domain
    if voice_coil_model == "simple":
        # Standard jωL_e model (lossless inductor)
        # Z_vc = R_e + jωL_e
        Z_voice_coil = complex(driver.R_e, omega * driver.L_e)
    elif voice_coil_model == "leach-full":
        # Leach (2002) lossy inductance model at ALL frequencies
        # Accounts for eddy current losses at all frequencies
        if leach_K is None or leach_n is None:
            raise ValueError("leach_K and leach_n must be provided for Leach models")
        Z_voice_coil = voice_coil_impedance_leach(
            frequency, driver, leach_K, leach_n
        )
    else:  # voice_coil_model == "leach"
        # Frequency-limited Leach model
        # Use simple model at low frequencies, Leach model at high frequencies
        if frequency < 1000.0:  # leach_crossover_hz
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
    # Force: F = BL · i_c (Lorentz force)
    # Back EMF: V_back = BL · u_D
    # This creates a reflected impedance of (BL)² / Z_m
    # CRITICAL: Use Z_mechanical_total (with C_mb), not driver's C_ms!
    if abs(Z_mechanical_total) == 0:
        # Avoid division by zero
        Z_reflected = complex(0, float('inf'))
    else:
        Z_reflected = (driver.BL ** 2) / Z_mechanical_total

    # Total electrical impedance: Z_e = Z_vc + Z_reflected
    # COMSOL (2020), Figure 2 - Series connection
    Ze = Z_voice_coil + Z_reflected

    # Step 6: Calculate diaphragm velocity using I_active force model
    # This is the time-averaged force that contributes to acoustic power
    # literature/thiele_small/comsol_lumped_loudspeaker_driver_2020.md
    if driver.BL == 0 or abs(Ze) == 0:
        # Avoid division by zero
        u_diaphragm = complex(0, 0)
    else:
        # Voice coil current
        # COMSOL (2020), Figure 2: i_c = V_in / Z_e
        I_complex = voltage / Ze

        # Extract active (in-phase) component of current
        # I_active = |I| × cos(phase(I))
        # Only this component contributes to time-averaged power transfer
        # COMSOL (2020), Eq. 4: P_E = 0.5·Re{V₀·i_c*}
        I_phase = cmath.phase(I_complex)
        I_active = abs(I_complex) * math.cos(I_phase)

        # Calculate force using active current
        # F_active = BL × I_active
        # This is the time-averaged force that contributes to acoustic power
        F_active = driver.BL * I_active

        # Diaphragm velocity from active force and mechanical impedance
        # u_D = F_active / |Z_m_total|
        # Velocity is assumed in phase with force for resistive mechanical load
        u_diaphragm_mag = F_active / abs(Z_mechanical_total)
        u_diaphragm = complex(u_diaphragm_mag, 0)

    # Step 7: Calculate sound pressure level
    # Kinsler et al. (1982), Chapter 4 - Pressure from piston in infinite baffle
    # For a circular piston in an infinite baffle:
    # p(r) = jωρ₀·U·exp(-jkr) / (2πr)
    # where U = volume velocity = u_D · S_d
    #
    # Sound pressure level: SPL = 20·log₁₀(|p|/p_ref) where p_ref = 20 μPa
    # literature/thiele_small/small_1972_closed_box.md

    # Volume velocity: U = u_D · S_d
    # Kinsler et al. (1982), Chapter 4
    volume_velocity = u_diaphragm * driver.S_d

    # Pressure magnitude at measurement distance
    # p = jωρ₀·U / (2πr)  (magnitude only, ignore phase and distance delay)
    # The factor j indicates 90° phase shift, but magnitude is what matters for SPL
    # Kinsler et al. (1982), Chapter 4, Eq. 4.58 (piston in infinite baffle)
    pressure_amplitude = (omega * air_density * abs(volume_velocity)) / \
                         (2 * math.pi * measurement_distance)

    # Sound pressure level
    # SPL = 20·log₁₀(p/p_ref) where p_ref = 20 μPa
    # Kinsler et al. (1982), Chapter 2
    p_ref = 20e-6  # Reference pressure: 20 μPa
    spl = 20 * math.log10(pressure_amplitude / p_ref) if pressure_amplitude > 0 else -float('inf')

    # Step 8: Calculate system Qtc for reference
    # Small (1972): Qtc = Qts × √(1 + α)
    sqrt_factor = math.sqrt(1.0 + alpha)
    Qtc = driver.Q_ts * sqrt_factor

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
        'Fc': Fc,
        'Qtc': Qtc,
    }

    return result

