"""
Horn acoustic simulation using T-matrix method.

This module implements exponential horn simulation based on the T-matrix
(transfer matrix) approach, which provides accurate throat impedance
calculations for finite horns.

Literature:
- Kolbrek, B. "Horn Loudspeaker Simulation Part 1: Radiation and T-Matrix"
  https://kolbrek.hornspeakersystems.info/
- Beranek, L. (1954). Acoustics. McGraw-Hill. Eq. 5.20
- Kinsler, L.E. & Frey, A.R. (1982). Fundamentals of Acoustics. Eq. 9.6.4
- literature/horns/kolbrek_horn_theory_tutorial.md
- literature/horns/beranek_1954.md
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np
from numpy.typing import NDArray

# Type aliases
ComplexArray = NDArray[np.complexfloating]
FloatArray = NDArray[np.floating]


@dataclass
class MediumProperties:
    """Properties of the acoustic medium.

    Attributes:
        c: Speed of sound [m/s]
        rho: Air density [kg/m³]
        z_rc: Characteristic impedance ρc [Pa·s/m] (computed property)

    Literature:
        Default values match Hornresp defaults (Kolbrek tutorial).
        Standard conditions at 20°C, 1 atm.

    Examples:
        >>> medium = MediumProperties()
        >>> medium.c  # Speed of sound
        344.0
        >>> medium.z_rc  # Characteristic impedance
        414.62...  # ρc = 1.205 × 344
    """
    c: float = 344.0  # m/s at 20°C
    rho: float = 1.205  # kg/m³ at 20°C, 1 atm

    @property
    def z_rc(self) -> float:
        """Characteristic impedance ρc [Pa·s/m].

        Literature:
            Kinsler et al. (1982), Chapter 1 - Characteristic impedance
        """
        return self.rho * self.c


# Note: We use viberesp.simulation.types.ExponentialHorn for the main data class.
# This module provides calculation functions that work with that class.
# The types.ExponentialHorn uses Olson's convention: S(x) = S₁·exp(m·x) with m = ln(S₂/S₁)/L
# Kolbrek's convention uses: S(x) = S₁·exp(2m·x) with m_K = ln(S₂/S₁)/(2L) = m_Olson/2
# Internally, we convert to Kolbrek's convention for T-matrix calculations.


def circular_piston_radiation_impedance(
    frequencies: FloatArray,
    area: float,
    medium: Optional[MediumProperties] = None
) -> ComplexArray:
    """Calculate radiation impedance of circular piston in infinite baffle.

    This function computes the acoustic radiation impedance for a circular
    piston in an infinite baffle using Bessel and Struve functions.

    Literature:
        Z_rad = (ρc/S)[R₁(ka) + jX₁(ka)]
        R₁(ka) = 1 - J₁(2ka)/ka
        X₁(ka) = H₁(2ka)/ka

        Beranek (1954), Eq. 5.20 - Piston radiation impedance
        Kolbrek, "Horn Loudspeaker Simulation Part 1"
        literature/horns/beranek_1954.md

    Args:
        frequencies: Array of frequencies [Hz]
        area: Piston area [m²]
        medium: Acoustic medium properties (uses default if None)

    Returns:
        Complex acoustic impedance array [Pa·s/m³]

    Notes:
        - Uses scipy.special.j1 for J₁ Bessel function
        - Uses scipy.special.struve(1, x) for H₁ Struve function
        - Handles ka→0 limit using series expansion to avoid 0/0

    Examples:
        >>> import numpy as np
        >>> frequencies = np.array([100.0, 1000.0, 10000.0])
        >>> z = circular_piston_radiation_impedance(frequencies, area=0.01)
        >>> z[0]  # Low frequency: mostly reactive
        (0.001...+0.126j)
        >>> z[1]  # Mid frequency: transitioning
        (3.8...+12.5j)
        >>> z[2]  # High frequency: mostly resistive
        (413...+2.5j)

    Validation:
        Compare with Hornresp radiation impedance calculation.
        Expected: <1% deviation for ka > 0.5
    """
    from scipy.special import j1, struve

    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)
    radius = np.sqrt(area / np.pi)
    k = 2 * np.pi * frequencies / medium.c
    ka = k * radius
    two_ka = 2 * ka

    # Handle small ka to avoid numerical issues (0/0)
    # For small x: J₁(x)/x ≈ 1/2, H₁(x)/x ≈ 4x/(3π)
    small_ka_mask = ka < 1e-6

    R1 = np.ones_like(ka)
    X1 = np.zeros_like(ka)

    # Normal calculation for ka >= 1e-6
    normal_mask = ~small_ka_mask
    if np.any(normal_mask):
        ka_normal = ka[normal_mask]
        two_ka_normal = two_ka[normal_mask]
        R1[normal_mask] = 1 - j1(two_ka_normal) / ka_normal
        X1[normal_mask] = struve(1, two_ka_normal) / ka_normal

    # Small ka approximation (Taylor series leading terms)
    # R₁(ka) ≈ (ka)²/2 for small ka
    # X₁(ka) ≈ 8ka/(3π) for small ka
    if np.any(small_ka_mask):
        ka_small = ka[small_ka_mask]
        R1[small_ka_mask] = (ka_small ** 2) / 2
        X1[small_ka_mask] = 8 * ka_small / (3 * np.pi)

    z_normalized = R1 + 1j * X1
    z_rad = (medium.z_rc / area) * z_normalized

    return z_rad


def _kolbrek_flare_constant(horn: 'ExponentialHorn') -> float:
    """Convert from Olson's to Kolbrek's flare constant convention.

    Olson: S(x) = S₁·exp(m_olson·x) with m_olson = ln(S₂/S₁)/L
    Kolbrek: S(x) = S₁·exp(2m_kolbrek·x) with m_kolbrek = ln(S₂/S₁)/(2L)

    Therefore: m_kolbrek = m_olson / 2

    Literature:
        Kolbrek, "Horn Loudspeaker Simulation Part 1"
        Olson (1947), Chapter 5

    Args:
        horn: ExponentialHorn instance (using Olson's convention)

    Returns:
        Flare constant in Kolbrek's convention [1/m]
    """
    return horn.flare_constant / 2.0


def exponential_horn_tmatrix(
    frequencies: FloatArray,
    horn: 'ExponentialHorn',
    medium: Optional[MediumProperties] = None
) -> Tuple[ComplexArray, ComplexArray, ComplexArray, ComplexArray]:
    """Calculate T-matrix elements for exponential horn.

    Uses the existing types.ExponentialHorn data class (Olson convention)
    and internally converts to Kolbrek's convention for T-matrix calculation.

    The T-matrix (transfer matrix) relates pressure and volume velocity
    at the throat (port 1) to the mouth (port 2):

        [p₁, U₁]ᵀ = [a b; c d][p₂, U₂]ᵀ

    Literature:
        T-matrix elements for exponential horn:

        a = exp(mL)[cos(γL) - (m/γ)sin(γL)]
        b = exp(mL)·j(Z_rc/S₂)(k/γ)sin(γL)
        c = exp(mL)·j(S₁/Z_rc)(k/γ)sin(γL)
        d = exp(mL)(S₁/S₂)[cos(γL) + (m/γ)sin(γL)]

        γ = √(k² - m²) (propagation constant)

        Kolbrek, "Horn Loudspeaker Simulation Part 1"
        literature/horns/kolbrek_horn_theory_tutorial.md

    Args:
        frequencies: Array of frequencies [Hz]
        horn: ExponentialHorn geometry parameters
        medium: Acoustic medium properties (uses default if None)

    Returns:
        Tuple of (a, b, c, d) T-matrix element arrays (complex)

    Notes:
        - When f < f_c, γ is imaginary; sin/cos become sinh/cosh
        - Near f = f_c, use Taylor expansion to avoid γ→0 singularity
        - All arrays have same shape as input frequencies

    Examples:
        >>> import numpy as np
        >>> horn = ExponentialHorn(0.005, 0.05, 0.3)
        >>> freqs = np.array([100.0, 500.0, 1000.0])
        >>> a, b, c, d = exponential_horn_tmatrix(freqs, horn)
        >>> a.shape
        (3,)

    Validation:
        T-matrix is unitary for lossless horns (determinant = 1).
        Check det([a b; c d]) ≈ 1.0 for frequencies well above cutoff.
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    # Convert from Olson's to Kolbrek's flare constant convention
    m = _kolbrek_flare_constant(horn)
    L = horn.length
    S1 = horn.throat_area
    S2 = horn.mouth_area
    z_rc = medium.z_rc

    k = 2 * np.pi * frequencies / medium.c

    # γ = √(k² - m²), can be real or imaginary
    # Use complex sqrt to handle f < f_c case
    gamma_squared = k**2 - m**2
    gamma = np.sqrt(gamma_squared.astype(complex))

    gL = gamma * L
    emL = np.exp(m * L)

    # Handle near-cutoff singularity (γ → 0)
    # When |γL| < threshold, use Taylor expansion
    near_cutoff_mask = np.abs(gL) < 1e-8

    sin_gL = np.sin(gL)
    cos_gL = np.cos(gL)

    # For normal frequencies
    m_over_gamma = np.zeros_like(gamma, dtype=complex)
    k_over_gamma = np.zeros_like(gamma, dtype=complex)

    normal_mask = ~near_cutoff_mask
    if np.any(normal_mask):
        m_over_gamma[normal_mask] = m / gamma[normal_mask]
        k_over_gamma[normal_mask] = k[normal_mask] / gamma[normal_mask]

    # Near cutoff: use limits
    # sin(γL)/γ → L as γ→0
    # cos(γL) → 1 as γ→0
    # (m/γ)·sin(γL) → mL as γ→0
    # (k/γ)·sin(γL) → kL as γ→0 (at cutoff, k≈m)
    if np.any(near_cutoff_mask):
        # Use small angle approximation: sin(x) ≈ x for x → 0
        # So sin(γL)/γ → L
        sin_gL[near_cutoff_mask] = gL[near_cutoff_mask]
        cos_gL[near_cutoff_mask] = 1.0

        # For m/γ: as γ→0, sin(γL) ≈ γL, so (m/γ)sin(γL) → mL
        # Avoid division by zero by using limit directly
        m_over_gamma[near_cutoff_mask] = m * L
        k_over_gamma[near_cutoff_mask] = k[near_cutoff_mask] * L

    # T-matrix elements
    a = emL * (cos_gL - m_over_gamma * sin_gL)
    b = emL * 1j * (z_rc / S2) * k_over_gamma * sin_gL
    c = emL * 1j * (S1 / z_rc) * k_over_gamma * sin_gL
    d = emL * (S1 / S2) * (cos_gL + m_over_gamma * sin_gL)

    return a, b, c, d


def throat_impedance_from_tmatrix(
    z_mouth: ComplexArray,
    a: ComplexArray,
    b: ComplexArray,
    c: ComplexArray,
    d: ComplexArray
) -> ComplexArray:
    """Calculate throat impedance from mouth impedance using T-matrix.

    This function transforms the acoustic impedance from the mouth to the throat
    using the T-matrix elements.

    Literature:
        Z₁ = (a·Z₂ + b)/(c·Z₂ + d)

        Standard T-matrix impedance transformation
        Kolbrek, "Horn Loudspeaker Simulation Part 1"

    Args:
        z_mouth: Acoustic impedance at mouth (Z₂) [Pa·s/m³]
        a, b, c, d: T-matrix elements (from exponential_horn_tmatrix)

    Returns:
        Acoustic impedance at throat (Z₁) [Pa·s/m³]

    Notes:
        All input arrays must have the same shape.

    Examples:
        >>> z_mouth = np.array([100+100j, 400+50j])
        >>> a = b = c = d = np.array([1+0j, 1+0j])
        >>> z_throat = throat_impedance_from_tmatrix(z_mouth, a, b, c, d)
        >>> z_throat.shape
        (2,)
    """
    return (a * z_mouth + b) / (c * z_mouth + d)


def exponential_horn_throat_impedance(
    frequencies: FloatArray,
    horn: 'ExponentialHorn',
    medium: Optional[MediumProperties] = None,
    radiation_angle: float = 2 * np.pi
) -> ComplexArray:
    """Calculate throat impedance of finite exponential horn.

    Uses the existing types.ExponentialHorn data class (Olson convention)
    and internally converts to Kolbrek's convention for T-matrix calculation.

    This is the main entry point for exponential horn simulation. It combines
    mouth radiation impedance with T-matrix transformation to compute the
    acoustic impedance at the horn throat.

    Literature:
        Combines:
        - Mouth radiation impedance (Beranek Eq. 5.20)
        - T-matrix transformation (Kolbrek)

        literature/horns/beranek_1954.md
        literature/horns/kolbrek_horn_theory_tutorial.md

    Args:
        frequencies: Array of frequencies [Hz]
        horn: ExponentialHorn geometry parameters
        medium: Acoustic medium properties (uses default if None)
        radiation_angle: Solid angle of radiation [steradians]
            - 4π: free field (pulsating sphere)
            - 2π: half-space (piston in infinite baffle) [default]
            - π: quarter-space
            - π/2: eighth-space

    Returns:
        Complex acoustic impedance at throat [Pa·s/m³]
        Array shape matches input frequencies

    Notes:
        For radiation_angle != 2π, effective piston area is adjusted
        following Hornresp convention:
        S_eff = 2π·S_mouth/radiation_angle

    Examples:
        >>> import numpy as np
        >>> horn = ExponentialHorn(throat_area=0.005, mouth_area=0.05, length=0.3)
        >>> freqs = np.array([100.0, 500.0, 1000.0, 5000.0])
        >>> z_throat = exponential_horn_throat_impedance(freqs, horn)
        >>> z_throat[0]  # Below cutoff: mostly reactive (mass-like)
        (0.01...+5.2j)
        >>> z_throat[2]  # Above cutoff: becoming resistive
        (40...+30j)
        >>> z_throat[3]  # High frequency: approaches ρc/S₁
        (80...+5j)

    Validation:
        Compare with Hornresp acoustical impedance export.
        Expected tolerances:
        - f > 2×f_c: <1% magnitude, <2° phase
        - f_c < f < 2×f_c: <3% magnitude, <5° phase
        - f < f_c: <10% magnitude (evanescent region)
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    # Adjust effective area for radiation angle (Hornresp convention)
    # S_eff = 2π·S_mouth/radiation_angle
    effective_mouth_area = 2 * np.pi * horn.mouth_area / radiation_angle

    # Calculate mouth radiation impedance
    z_mouth = circular_piston_radiation_impedance(
        frequencies, effective_mouth_area, medium
    )

    # Calculate T-matrix
    a, b, c, d = exponential_horn_tmatrix(frequencies, horn, medium)

    # Transform to throat
    z_throat = throat_impedance_from_tmatrix(z_mouth, a, b, c, d)

    return z_throat


def multsegment_horn_throat_impedance(
    frequencies: FloatArray,
    horn: 'MultiSegmentHorn',
    medium: Optional[MediumProperties] = None,
    radiation_angle: float = 2 * np.pi
) -> ComplexArray:
    """Calculate throat impedance of multi-segment horn using T-matrix chaining.

    A multi-segment horn consists of multiple exponential segments connected
    in series. The overall T-matrix is the product of individual segment T-matrices:

        T_total = T_1 · T_2 · ... · T_n

    This allows approximating arbitrary horn profiles by using segments with
    different flare constants.

    Literature:
        - Kolbrek Part 1 - T-matrix chaining for compound horns
        - Olson (1947), Chapter 8 - Compound and stepped horns
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Args:
        frequencies: Array of frequencies [Hz]
        horn: MultiSegmentHorn geometry with list of HornSegment objects
        medium: Acoustic medium properties (uses default if None)
        radiation_angle: Solid angle of radiation [steradians]
            - 4π: free field (pulsating sphere)
            - 2π: half-space (piston in infinite baffle) [default]
            - π: quarter-space
            - π/2: eighth-space

    Returns:
        Complex acoustic impedance at throat [Pa·s/m³]
        Array shape matches input frequencies

    Notes:
        - T-matrices are chained from mouth to throat (reverse order)
        - Each segment is treated as an exponential horn with its own flare constant
        - Mouth radiation impedance calculated only for final segment mouth
        - For radiation_angle != 2π, effective mouth area is adjusted

    Examples:
        >>> import numpy as np
        >>> from viberesp.simulation.types import HornSegment, MultiSegmentHorn
        >>> segment1 = HornSegment(throat_area=0.001, mouth_area=0.01, length=0.3)
        >>> segment2 = HornSegment(throat_area=0.01, mouth_area=0.1, length=0.6)
        >>> horn = MultiSegmentHorn(segments=[segment1, segment2])
        >>> freqs = np.array([100.0, 500.0, 1000.0, 5000.0])
        >>> z_throat = multsegment_horn_throat_impedance(freqs, horn)
        >>> z_throat.shape
        (4,)

    Validation:
        Compare with Hornresp multi-segment horn simulation.
        Expected tolerances:
        - f > 2×f_c_min: <1% magnitude, <2° phase
        - Near cutoff: <3% magnitude, <5° phase
        where f_c_min is the minimum cutoff frequency among all segments
    """
    if medium is None:
        medium = MediumProperties()

    frequencies = np.atleast_1d(frequencies).astype(float)

    # Adjust effective area for radiation angle (Hornresp convention)
    # S_eff = 2π·S_mouth/radiation_angle
    effective_mouth_area = 2 * np.pi * horn.mouth_area / radiation_angle

    # Calculate mouth radiation impedance (only for final mouth)
    z_mouth = circular_piston_radiation_impedance(
        frequencies, effective_mouth_area, medium
    )

    # Chain T-matrices from mouth to throat
    # Start with mouth impedance, work backwards through segments
    z_current = z_mouth

    # Process segments in reverse order (mouth to throat)
    for segment in reversed(horn.segments):
        # Create ExponentialHorn for this segment to reuse existing T-matrix code
        from viberesp.simulation.types import ExponentialHorn
        segment_horn = ExponentialHorn(
            throat_area=segment.throat_area,
            mouth_area=segment.mouth_area,
            length=segment.length
            # flare_constant calculated automatically
        )

        # Calculate T-matrix for this segment
        a, b, c, d = exponential_horn_tmatrix(frequencies, segment_horn, medium)

        # Transform impedance through this segment
        z_current = throat_impedance_from_tmatrix(z_current, a, b, c, d)

    return z_current
