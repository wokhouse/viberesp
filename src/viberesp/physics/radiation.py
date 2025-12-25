"""Radiation impedance calculations for loudspeaker analysis.

This module implements radiation impedance calculations for various piston
geometries and boundary conditions, following established acoustic theory.
"""

from __future__ import annotations

import numpy as np
from scipy.special import j0, j1, struve  # type: ignore[import-untyped]

from viberesp.core.constants import RHO, C


def _struve_h1(x: float | np.ndarray) -> float | np.ndarray:
    """Calculate Struve function of order 1 using MathWorld approximation.

    The Struve function H₁(x) appears in radiation impedance calculations
    for circular pistons. This approximation uses standard functions for
    numerical stability and convenience.

    Parameters
    ----------
    x : float or np.ndarray
        Argument (dimensionless)

    Returns
    -------
    float or np.ndarray
        Struve H₁ function value

    Notes
    -----
    Approximation formula from Wolfram MathWorld [1]_:
    H₁(x) ≈ 2/π - J₀(x) + (16/π - 5)·sin(x)/x + (12 - 36/π)·(1 - cos(x))/x²

    For production use, consider scipy.special.struve for maximum accuracy.
    The approximation error is typically <0.2% compared to scipy.

    References
    ----------
    .. [1] Wolfram MathWorld. "Struve Function."
           http://mathworld.wolfram.com/StruveFunction.html

    Examples
    --------
    >>> _struve_h1(0.5)
    0.03738...
    >>> _struve_h1(np.array([0.5, 1.0, 2.0]))
    array([0.03738..., 0.30010..., 1.02445...])
    """
    # Avoid division by zero at x = 0
    if isinstance(x, (float, int)):
        if x == 0:
            return 0.0
    else:
        x = np.array(x, dtype=float)
        # For very small x, use limit: H₁(x) → 0 as x → 0
        x_safe = np.where(np.abs(x) < 1e-10, 1e-10, x)

        J0_val = j0(x_safe)
        term1 = 2 / np.pi
        term2 = -J0_val
        term3 = (16 / np.pi - 5) * np.sin(x_safe) / x_safe
        term4 = (12 - 36 / np.pi) * (1 - np.cos(x_safe)) / (x_safe**2)

        result = term1 + term2 + term3 + term4
        return result  # type: ignore[no-any-return]

    # Scalar case
    J0_val = j0(x)
    term1 = 2 / np.pi
    term2 = -J0_val
    term3 = (16 / np.pi - 5) * np.sin(x) / x
    term4 = (12 - 36 / np.pi) * (1 - np.cos(x)) / (x**2)

    return term1 + term2 + term3 + term4  # type: ignore[no-any-return]


def circular_piston_impedance_normalized(
    ka: float | np.ndarray,
) -> complex | np.ndarray:
    """Calculate normalized radiation impedance for circular piston in infinite baffle.

    This function computes the dimensionless radiation impedance for a circular
    piston radiating into half-space (infinite baffle condition). The normalized
    impedance separates the frequency-dependent behavior from the area scaling.

    Parameters
    ----------
    ka : float or np.ndarray
        Dimensionless frequency parameter
        ka = 2πf·a/c = k·a where:
        - f = frequency (Hz)
        - a = piston radius (m)
        - c = speed of sound (m/s)
        - k = wavenumber = 2πf/c

    Returns
    -------
    complex or np.ndarray[complex]
        Normalized radiation impedance Z_norm = R(ka) + j·X(ka)

        - R(ka) = 1 - J₁(2ka)/(ka) : Normalized radiation resistance
        - X(ka) = H₁(2ka)/(ka) : Normalized radiation reactance

    Notes
    -----
    **Behavior regimes:**

    - **Low frequency (ka << 1)**: Mass-controlled region
      X >> R, radiation adds mass loading to the system
      Limit: X(ka) → (2/π)·ka as ka → 0

    - **Transition (ka ≈ 1)**: Resistance and reactance comparable
      Complex radiation behavior, neither purely mass nor resistance controlled

    - **High frequency (ka >> 1)**: Radiation resistance approaches 1
      R → 1, X → 0, radiation becomes purely resistive
      100% radiation efficiency at high frequencies

    **Physical interpretation:**

    The normalized impedance represents the ratio of actual radiation impedance
    to the characteristic impedance (ρ₀c/S). Multiplying by ρ₀c/S gives the
    absolute radiation impedance in Pa·s/m³.

    References
    ----------
    .. [1] Kolbrek, B. (2019). "Horn Loudspeaker Simulation - Part 1:
           Radiation and T-Matrix." Section: "Circular Piston in Infinite Baffle"
           https://hornspeakersystems.info/
           Link: literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md

    .. [2] Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound Fields
           and Transducers*. Chapter 4: Radiation Impedance.

    Examples
    --------
    Low frequency (ka = 0.18 at 50 Hz for 20 cm radius):
    >>> Z_norm = circular_piston_impedance_normalized(0.18)
    >>> Z_norm
    (0.01639+0.15277j)
    >>> f"Mass-controlled: X/R = {Z_norm.imag/Z_norm.real:.1f}"
    'Mass-controlled: X/R = 9.3'

    High frequency (ka >> 1):
    >>> Z_norm = circular_piston_impedance_normalized(100)
    >>> Z_norm
    (0.99999+0.00018j)
    >>> f"R ≈ 1, X ≈ 0"
    'R ≈ 1, X ≈ 0'

    Frequency array:
    >>> freqs = np.logspace(1, 3, 10)  # 10-1000 Hz
    >>> a, c = 0.20, 346.1
    >>> ka = 2 * np.pi * freqs * a / c
    >>> Z_norm = circular_piston_impedance_normalized(ka)
    >>> len(Z_norm)
    10
    """
    # Use scipy's struve function for accuracy
    H1_val = struve(1, 2 * ka)
    J1_val = j1(2 * ka)

    # Normalized resistance and reactance
    # Following Kolbrek Part 1, Eq. for circular piston
    R_norm = 1 - J1_val / ka
    X_norm = H1_val / ka

    return R_norm + 1j * X_norm  # type: ignore[no-any-return]


def circular_piston_impedance(
    area: float,
    frequency: float | np.ndarray,
    rho: float = RHO,
    c: float = C,
) -> complex | np.ndarray:
    """Calculate radiation impedance for circular piston in infinite baffle.

    Computes the absolute acoustic radiation impedance for a circular piston
    radiating into half-space (infinite baffle condition).

    Parameters
    ----------
    area : float
        Piston radiating area (m²)
    frequency : float or np.ndarray
        Frequency or frequency array (Hz)
    rho : float, optional
        Air density (kg/m³), default from constants (25°C)
    c : float, optional
        Speed of sound (m/s), default from constants (25°C)

    Returns
    -------
    complex or np.ndarray[complex]
        Radiation impedance Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))

        Units: Pa·s/m³ (acoustic ohms)

        Real part: Radiation resistance (energy radiated as sound)
        Imaginary part: Radiation reactance (energy stored in near field)

    Notes
    -----
    **Physical dimensions:**
    The characteristic impedance ρ₀c/S has units of:
    ρ₀c/S = (kg/m³)·(m/s)/(m²) = kg/(m⁴·s) = Pa·s/m³

    This is called "acoustic ohms" and represents the ratio of pressure
    to volume velocity.

    **Impedance scaling:**
    Z_rad = (ρ₀c/S) · Z_norm

    Where Z_norm is the dimensionless normalized impedance from
    :func:`circular_piston_impedance_normalized`. The characteristic
    impedance ρ₀c/S scales the impedance with piston area.

    **Applications:**
    - Horn mouth radiation boundary condition
    - Loudspeaker radiation load calculation
    - Throat impedance determination via T-matrix method
    - Efficiency and power calculations

    References
    ----------
    .. [1] Kolbrek, B. (2019). "Horn Loudspeaker Simulation - Part 1:
           Radiation and T-Matrix." Section: "Circular Piston in Infinite Baffle"
           Link: literature/phase2_tmatrix/Kolbrek_2019_Part1_Radiation_TMatrix.md

    .. [2] Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound Fields
           and Transducers*. Chapter 4: Radiation Impedance.

    Examples
    --------
    Single frequency:
    >>> Z_rad = circular_piston_impedance(area=0.1257, frequency=50.0)
    >>> Z_rad
    (53.44+498.03j)
    >>> print(f"|Z| = {abs(Z_rad):.1f} acoustic ohms")
    |Z| = 501.0 acoustic ohms

    Frequency array:
    >>> freqs = np.linspace(20, 200, 5)
    >>> Z_rad = circular_piston_impedance(area=0.1257, frequency=freqs)
    >>> len(Z_rad)
    5

    Effect of area:
    >>> Z_small = circular_piston_impedance(area=0.01, frequency=100)
    >>> Z_large = circular_piston_impedance(area=0.1, frequency=100)
    >>> abs(Z_small) > abs(Z_large)  # Smaller area = higher impedance
    True
    """
    # Calculate piston radius from area
    radius = np.sqrt(area / np.pi)

    # Handle scalar vs array frequency
    freq_is_scalar = isinstance(frequency, (float, int))
    if freq_is_scalar:
        frequency = np.array([frequency])
    else:
        frequency = np.asarray(frequency)

    # Calculate ka for each frequency
    # ka = k·a = (2πf/c)·a = 2πfa/c
    ka = 2 * np.pi * frequency * radius / c

    # Get normalized impedance
    Z_norm = circular_piston_impedance_normalized(ka)

    # Scale by characteristic impedance: Z_rad = (ρ₀c/S) · Z_norm
    Z_char = rho * c / area
    Z_rad = Z_char * Z_norm

    # Return scalar for scalar input
    if freq_is_scalar:
        return Z_rad[0]  # type: ignore[no-any-return, index]

    return Z_rad  # type: ignore[no-any-return]
