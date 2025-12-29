"""
Horn driver integration models.

This module implements the electromechanical coupling between loudspeaker
drivers and horn-loaded enclosures, including throat chambers and rear chambers.

Literature:
- Olson (1947), Chapter 8 - Horn driver systems
- Beranek (1954), Chapter 5 - Acoustic compliance, electromechanical analogies
- Small (1972) - Thiele-Small analysis for horn-loaded drivers
- literature/horns/olson_1947.md
- literature/horns/beranek_1954.md
- literature/thiele_small/small_1972_closed_box.md
"""

from __future__ import annotations

import math
import cmath
from typing import Optional, Tuple
import numpy as np
from numpy.typing import NDArray
from viberesp.simulation.horn_theory import (
    exponential_horn_throat_impedance,
    multsegment_horn_throat_impedance,
    circular_piston_radiation_impedance,
    MediumProperties,
)
from viberesp.simulation.constants import (
    SPEED_OF_SOUND,
    AIR_DENSITY,
    CHARACTERISTIC_IMPEDANCE_AIR,
    angular_frequency,
)

# Type aliases
ComplexArray = NDArray[np.complexfloating]
FloatArray = NDArray[np.floating]


def throat_chamber_impedance(
    frequencies: FloatArray,
    V_tc: float,
    A_tc: float,
    medium: Optional[MediumProperties] = None
) -> ComplexArray:
    """Calculate acoustic impedance of a throat chamber.

    The throat chamber is a compliance volume between the driver diaphragm
    and the horn throat. It acts as a series acoustic compliance.

    Literature:
        - Olson (1947), Chapter 8 - Throat chamber compliance
        - Beranek (1954), Chapter 5 - Acoustic compliance of cavities
        - literature/horns/olson_1947.md
        - literature/horns/beranek_1954.md

    Acoustic compliance of a cavity:
        C_tc = V_tc / (ρ·c²)

    Acoustic impedance of compliance:
        Z_tc = 1 / (jω·C_tc) = -j / (ω·C_tc)

    Args:
        frequencies: Array of frequencies [Hz]
        V_tc: Throat chamber volume [m³]
        A_tc: Throat chamber area [m²] (typically equals horn throat area)
        medium: Acoustic medium properties (uses default if None)

    Returns:
        Complex acoustic impedance array [Pa·s/m³]
        Series compliance impedance (purely reactive)

    Raises:
        ValueError: If V_tc <= 0 or A_tc <= 0

    Examples:
        >>> import numpy as np
        >>> freqs = np.array([100.0, 500.0, 1000.0])
        >>> z_tc = throat_chamber_impedance(freqs, V_tc=0.001, A_tc=0.005)
        >>> z_tc[0]  # Low frequency: high impedance (stiff spring)
        (-...j)
        >>> z_tc[2]  # High frequency: low impedance
        (-...j)

    Validation:
        Compare with Hornresp throat chamber impedance calculation.
        Expected: <1% deviation for all frequencies above 20 Hz.
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    if V_tc <= 0:
        raise ValueError(f"Throat chamber volume V_tc must be > 0, got {V_tc} m³")

    if A_tc <= 0:
        raise ValueError(f"Throat chamber area A_tc must be > 0, got {A_tc} m²")

    # Acoustic compliance of cavity
    # Beranek (1954), Chapter 5: C = V / (ρ·c²)
    # literature/horns/beranek_1954.md
    C_tc = V_tc / (medium.rho * medium.c ** 2)

    # Angular frequency: ω = 2πf
    omega = 2 * np.pi * frequencies

    # Acoustic impedance of compliance (series element)
    # Z_tc = 1 / (jω·C) = -j / (ω·C)
    # Purely reactive (compliance behaves like spring)
    Z_tc = -1j / (omega * C_tc)

    return Z_tc


def rear_chamber_impedance(
    frequencies: FloatArray,
    V_rc: float,
    S_d: float,
    medium: Optional[MediumProperties] = None
) -> ComplexArray:
    """Calculate acoustic impedance of a rear chamber (sealed box).

    The rear chamber is the enclosure volume behind the driver diaphragm.
    It adds compliance to the rear of the driver, similar to a sealed box.

    Literature:
        - Small (1972) - Closed-box systems
        - Beranek (1954), Chapter 5 - Acoustic compliance
        - literature/thiele_small/small_1972_closed_box.md
        - literature/horns/beranek_1954.md

    Acoustic compliance of rear chamber:
        C_rc = V_rc / (ρ·c²)

    Acoustic impedance (seen from rear of diaphragm):
        Z_rc = 1 / (jω·C_rc) + Z_rad_rear

    where Z_rad_rear is the radiation impedance on the rear side.
    For a front-loaded horn with no rear radiation, Z_rad_rear = 0.

    Args:
        frequencies: Array of frequencies [Hz]
        V_rc: Rear chamber volume [m³]
        S_d: Diaphragm area [m²]
        medium: Acoustic medium properties (uses default if None)

    Returns:
        Complex acoustic impedance array [Pa·s/m³]
        Compliance impedance in parallel with rear radiation

    Raises:
        ValueError: If V_rc <= 0 or S_d <= 0

    Examples:
        >>> import numpy as np
        >>> freqs = np.array([100.0, 500.0, 1000.0])
        >>> z_rc = rear_chamber_impedance(freqs, V_rc=0.010, S_d=0.022)
        >>> z_rc[0]  # Low frequency: high compliance impedance
        (-...j)

    Validation:
        Compare with Hornresp rear chamber impedance calculation.
        Expected: <1% deviation for all frequencies above 20 Hz.
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    if V_rc <= 0:
        raise ValueError(f"Rear chamber volume V_rc must be > 0, got {V_rc} m³")

    if S_d <= 0:
        raise ValueError(f"Diaphragm area S_d must be > 0, got {S_d} m²")

    # Acoustic compliance of rear chamber
    # Beranek (1954), Chapter 5: C = V / (ρ·c²)
    # literature/horns/beranek_1954.md
    C_rc = V_rc / (medium.rho * medium.c ** 2)

    # Angular frequency: ω = 2πf
    omega = 2 * np.pi * frequencies

    # Acoustic impedance of compliance (shunt element to ground)
    # Z_rc = 1 / (jω·C) = -j / (ω·C)
    # Purely reactive (compliance behaves like spring)
    Z_rc = -1j / (omega * C_rc)

    return Z_rc


def horn_system_acoustic_impedance(
    frequencies: FloatArray,
    horn: 'ExponentialHorn | MultiSegmentHorn',
    V_tc: float = 0.0,
    A_tc: Optional[float] = None,
    V_rc: float = 0.0,
    S_d: Optional[float] = None,
    medium: Optional[MediumProperties] = None,
    radiation_angle: float = 2 * np.pi
) -> Tuple[ComplexArray, ComplexArray]:
    """Calculate total acoustic impedance seen by driver diaphragm in horn system.

    Combines throat chamber, horn throat impedance, and rear chamber impedance
    to calculate the total acoustic load on the driver.

    Supports both single-segment ExponentialHorn and multi-segment MultiSegmentHorn.

    Literature:
        - Olson (1947), Chapter 8 - Complete horn driver systems
        - Beranek (1954), Chapter 5 - Acoustic impedance combinations
        - literature/horns/olson_1947.md
        - literature/horns/beranek_1954.md

    Impedance model:
        Front: Z_front = Z_tc + Z_horn_throat
        Rear: Z_rear = Z_rc || Z_rad_rear (parallel combination)
        Total: Z_acoustic = Z_front + Z_rear

    where:
        Z_tc = throat chamber compliance impedance (if V_tc > 0)
        Z_horn_throat = horn throat impedance from T-matrix
        Z_rc = rear chamber compliance impedance (if V_rc > 0)
        Z_rad_rear = rear radiation impedance (typically 0 for front-loaded)

    Args:
        frequencies: Array of frequencies [Hz]
        horn: ExponentialHorn or MultiSegmentHorn geometry parameters
        V_tc: Throat chamber volume [m³], default 0 (no throat chamber)
        A_tc: Throat chamber area [m²], defaults to horn.throat_area
        V_rc: Rear chamber volume [m³], default 0 (no rear chamber)
        S_d: Diaphragm area [m²] (required if V_rc > 0)
        medium: Acoustic medium properties (uses default if None)
        radiation_angle: Solid angle of radiation [steradians]

    Returns:
        Tuple of (Z_front, Z_rear) complex acoustic impedance arrays [Pa·s/m³]
        - Z_front: Total front impedance (throat chamber + horn)
        - Z_rear: Total rear impedance (rear chamber || radiation)

    Raises:
        ValueError: If V_rc > 0 but S_d is not provided

    Examples:
        >>> import numpy as np
        >>> from viberesp.simulation.types import ExponentialHorn
        >>> horn = ExponentialHorn(0.005, 0.05, 0.3)
        >>> freqs = np.array([100.0, 500.0, 1000.0])
        >>> Z_front, Z_rear = horn_system_acoustic_impedance(freqs, horn)
        >>> Z_front.shape
        (3,)

    Validation:
        Compare with Hornresp acoustical impedance export.
        Expected: <2% magnitude, <3° phase for f > 2×f_c
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    # Set default throat chamber area (equals horn throat area)
    if A_tc is None:
        A_tc = horn.throat_area

    # Calculate horn throat impedance (T-matrix method)
    # Check horn type and use appropriate impedance calculation
    horn_type = type(horn).__name__
    if horn_type == "MultiSegmentHorn":
        # Multi-segment horn: chain T-matrices for each segment
        Z_horn_throat = multsegment_horn_throat_impedance(
            frequencies, horn, medium
        )
    else:
        # Single-segment exponential horn
        Z_horn_throat = exponential_horn_throat_impedance(
            frequencies, horn, medium, radiation_angle
        )

    # Add throat chamber compliance (series element)
    if V_tc > 0:
        Z_tc = throat_chamber_impedance(frequencies, V_tc, A_tc, medium)
        Z_front = Z_tc + Z_horn_throat
    else:
        Z_front = Z_horn_throat

    # Calculate rear impedance
    if V_rc > 0:
        if S_d is None:
            raise ValueError("S_d must be provided if V_rc > 0")

        Z_rc = rear_chamber_impedance(frequencies, V_rc, S_d, medium)

        # Rear radiation impedance (piston in half-space for open back)
        # For sealed rear chamber, no radiation (Z_rad_rear = 0)
        Z_rad_rear = np.zeros_like(frequencies, dtype=complex)

        # Parallel combination: 1/Z_total = 1/Z_rc + 1/Z_rad
        # If Z_rad_rear = 0, then Z_rear = Z_rc (pure compliance)
        Z_rear = Z_rc  # Simplified for front-loaded horn
    else:
        Z_rear = np.zeros_like(frequencies, dtype=complex)

    return Z_front, Z_rear


def horn_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    horn: 'ExponentialHorn',
    V_tc: float = 0.0,
    A_tc: Optional[float] = None,
    V_rc: float = 0.0,
    voltage: float = 2.83,
    medium: Optional[MediumProperties] = None,
    radiation_angle: float = 2 * np.pi
) -> dict:
    """Calculate electrical impedance for driver loaded by horn.

    Implements the complete electromechanical model for a horn-loaded driver,
    including throat chamber, rear chamber, and horn impedance.

    Literature:
        - Small (1972) - Electromechanical analogies
        - Beranek (1954), Chapter 5 - Electromechanical circuits
        - Olson (1947), Chapter 8 - Horn driver electrical impedance
        - literature/thiele_small/small_1972_closed_box.md
        - literature/horns/olson_1947.md
        - literature/horns/beranek_1954.md

    Electromechanical model:
        Electrical domain:
            Z_e = R_e + jωL_e + (BL)² / Z_mechanical

        Mechanical domain:
            Z_mechanical = R_ms + jωM_md + 1/(jωC_ms) + Z_acoustic_radiation

        Acoustic domain:
            Z_acoustic_radiation = S_d² × (Z_front + Z_rear)

    where Z_front and Z_rear are calculated by horn_system_acoustic_impedance().

    Args:
        frequency: Frequency [Hz]
        driver: ThieleSmallParameters instance
        horn: ExponentialHorn geometry parameters
        V_tc: Throat chamber volume [m³], default 0
        A_tc: Throat chamber area [m²], defaults to horn.throat_area
        V_rc: Rear chamber volume [m³], default 0
        voltage: Input voltage [V], default 2.83V
        medium: Acoustic medium properties (uses default if None)
        radiation_angle: Solid angle of radiation [steradians]

    Returns:
        Dictionary containing:
        - 'frequency': Frequency (Hz)
        - 'Ze_magnitude': Electrical impedance magnitude (Ω)
        - 'Ze_phase': Electrical impedance phase (degrees)
        - 'Ze_real': Electrical resistance (Ω)
        - 'Ze_imag': Electrical reactance (Ω)
        - 'diaphragm_velocity': Diaphragm velocity magnitude (m/s)
        - 'diaphragm_displacement': Diaphragm displacement magnitude (m)
        - 'Z_front': Front acoustic impedance (Pa·s/m³)
        - 'Z_rear': Rear acoustic impedance (Pa·s/m³)

    Raises:
        ValueError: If frequency <= 0 or invalid parameters

    Examples:
        >>> from viberesp.simulation.types import ExponentialHorn
        >>> from viberesp.driver.bc_drivers import get_bc_8ndl51
        >>> driver = get_bc_8ndl51()
        >>> horn = ExponentialHorn(0.001, 0.01, 0.3)
        >>> result = horn_electrical_impedance(500, driver, horn)
        >>> result['Ze_magnitude']
        7.2...  # Ω

    Validation:
        Compare with Hornresp electrical impedance export.
        Expected: <2% magnitude, <5° phase for frequencies > F_s/2
    """
    # Validate inputs (handle both scalar and array inputs)
    if np.any(frequency <= 0):
        if np.isscalar(frequency):
            raise ValueError(f"Frequency must be > 0, got {frequency} Hz")
        else:
            raise ValueError(f"All frequencies must be > 0, min={np.min(frequency)} Hz")

    # Local import to avoid circular dependency
    from viberesp.driver.parameters import ThieleSmallParameters

    if not isinstance(driver, ThieleSmallParameters):
        raise TypeError(f"driver must be ThieleSmallParameters, got {type(driver)}")

    if medium is None:
        medium = MediumProperties()

    # Calculate angular frequency
    omega = angular_frequency(frequency)

    # Calculate acoustic impedances
    frequencies = np.array([frequency])
    Z_front, Z_rear = horn_system_acoustic_impedance(
        frequencies, horn, V_tc, A_tc, V_rc, driver.S_d, medium, radiation_angle
    )

    # Total acoustic impedance (at throat)
    Z_acoustic = Z_front[0] + Z_rear[0]

    # Reflect acoustic impedance to mechanical domain
    # IMPORTANT: For compression drivers, Z_acoustic is calculated at the throat (area S1)
    # not at the diaphragm (area Sd). We must scale by throat area, not diaphragm area.
    #
    # Z_mechanical_acoustic = Z_acoustic_at_throat × S1²
    #
    # The compression ratio (Sd/S1) affects the pressure transformation, but
    # the acoustic impedance calculation already accounts for this.
    #
    # Literature:
    # - Beranek (1954), Chapter 8 - Compression driver loading
    # - Olson (1947), Chapter 8 - Horn driver impedance transformation
    Z_mechanical_acoustic = Z_acoustic * (horn.throat_area ** 2)

    # Calculate mechanical impedance
    # Z_mechanical = R_ms + jωM_md + 1/(jωC_ms)
    # COMSOL (2020), Figure 2
    Z_mechanical_driver = (driver.R_ms +
                          complex(0, omega * driver.M_md) +
                          complex(0, -1 / (omega * driver.C_ms)))

    # Total mechanical impedance
    Z_mechanical_total = Z_mechanical_driver + Z_mechanical_acoustic

    # Voice coil electrical impedance
    # Z_vc = R_e + jωL_e
    # COMSOL (2020), Figure 2
    Z_voice_coil = complex(driver.R_e, omega * driver.L_e)

    # Reflected impedance from mechanical to electrical domain
    # Z_reflected = (BL)² / Z_mechanical_total
    # COMSOL (2020), Figure 2
    if abs(Z_mechanical_total) == 0:
        # Avoid division by zero
        Z_reflected = complex(0, float('inf'))
    else:
        Z_reflected = (driver.BL ** 2) / Z_mechanical_total

    # Total electrical impedance
    # Z_e = Z_vc + Z_reflected
    # COMSOL (2020), Figure 2
    Ze = Z_voice_coil + Z_reflected

    # Calculate diaphragm velocity
    # F = BL × I, v = F / Z_mechanical_total
    if driver.BL == 0 or abs(Ze) == 0:
        u_diaphragm = complex(0, 0)
    else:
        # Voice coil current (complex phasor)
        I_complex = voltage / Ze

        # Force on diaphragm
        F_complex = driver.BL * I_complex

        # Diaphragm velocity
        u_diaphragm = F_complex / Z_mechanical_total

    # Diaphragm displacement: X = v / (jω)
    if omega == 0:
        x_diaphragm = complex(0, 0)
    else:
        x_diaphragm = u_diaphragm / complex(0, omega)

    # Prepare return dictionary
    result = {
        'frequency': frequency,
        'Ze_magnitude': abs(Ze),
        'Ze_phase': math.degrees(cmath.phase(Ze)),
        'Ze_real': Ze.real,
        'Ze_imag': Ze.imag,
        'diaphragm_velocity': abs(u_diaphragm),
        'diaphragm_displacement': abs(x_diaphragm),
        'Z_front': Z_front[0],
        'Z_rear': Z_rear[0],
    }

    return result
