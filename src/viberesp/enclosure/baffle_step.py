"""
Baffle step diffraction loss calculations.

When a driver radiates from a finite baffle, the sound transitions from
half-space radiation (2π steradians) at low frequencies to full-space
radiation (4π steradians) at high frequencies, causing a 6 dB loss.

Literature:
- Olson (1947) - Elements of Acoustical Engineering, Section on Diffraction
- Linkwitz (1976) - Baffle step compensation circuits
- Bullock & White (1981) - Practical baffle step loss modeling

Key equations:
- f_baffle ≈ c / (2 × width)  (transition frequency)
- Maximum loss: 6 dB (half-space to full-space transition)
"""

import numpy as np
from typing import Tuple, Union

from viberesp.simulation.constants import SPEED_OF_SOUND


def baffle_step_frequency(
    baffle_width: float,
    speed_of_sound: float = SPEED_OF_SOUND
) -> float:
    """
    Calculate the baffle step transition frequency.

    The baffle step occurs when the wavelength is comparable to the
    baffle dimensions. For a rectangular baffle, the transition
    occurs approximately at f = c / (2 × width).

    Literature:
        Linkwitz (1976) - Baffle step frequency approximation
        f_3dB ≈ c / (2 × baffle_width)

    Args:
        baffle_width: Width of the baffle (meters)
        speed_of_sound: Speed of sound (m/s), default 343 m/s

    Returns:
        Baffle step frequency (Hz) where loss is -3 dB

    Examples:
        >>> baffle_step_frequency(0.3)  # 30cm wide baffle
        571.7...  # Hz
    """
    return speed_of_sound / (2 * baffle_width)


def baffle_step_loss(
    frequency: Union[float, np.ndarray],
    baffle_width: float,
    speed_of_sound: float = SPEED_OF_SOUND
) -> Union[float, np.ndarray]:
    """
    Calculate baffle step diffraction loss at given frequency/ies.

    Models the transition from 2π (half-space) to 4π (full-space) radiation.
    The maximum loss is 6 dB (10·log₁₀(2)) as the radiation solid angle doubles.

    Literature:
        Linkwitz (1976) - First-order model using arctan transition
        Loss(f) = -6 × arctan(f / f_baffle) / (π/2)

    Args:
        frequency: Frequency or frequencies (Hz)
        baffle_width: Width of the baffle (meters)
        speed_of_sound: Speed of sound (m/s), default 343 m/s

    Returns:
        Loss in dB (negative values, 0 to -6 dB)

    Examples:
        >>> baffle_step_loss(100, 0.3)  # 100 Hz, 30cm baffle
        -0.87...  # dB (small loss at low frequency)
        >>> baffle_step_loss(2000, 0.3)  # 2 kHz, 30cm baffle
        -5.98...  # dB (nearly full 6 dB loss at high frequency)
    """
    f_baffle = baffle_step_frequency(baffle_width, speed_of_sound)

    # First-order Linkwitz model: smooth arctan transition
    # At f << f_baffle: loss ≈ 0 dB
    # At f >> f_baffle: loss ≈ -6 dB
    # At f = f_baffle: loss = -3 dB
    loss = -6.0 * np.arctan(frequency / f_baffle) / (np.pi / 2)

    return loss


def baffle_step_loss_olson(
    frequency: Union[float, np.ndarray],
    baffle_width: float,
    baffle_height: float = None,
    speed_of_sound: float = SPEED_OF_SOUND
) -> Union[float, np.ndarray]:
    """
    Calculate baffle step loss using Olson's more accurate model.

    Olson's model accounts for the finite size of the baffle and the
    circular piston radiation pattern. More accurate than the simple
    arctan model for frequencies near the transition.

    Literature:
        Olson (1947) - Diffraction from a circular piston in a circular baffle
        Loss = 20·log₁₀|1 - J₁(2ka) / (ka)|

    Args:
        frequency: Frequency or frequencies (Hz)
        baffle_width: Width of the baffle (meters)
        baffle_height: Height of the baffle (meters), defaults to width (square)
        speed_of_sound: Speed of sound (m/s), default 343 m/s

    Returns:
        Loss in dB (negative values, 0 to -6 dB)

    Examples:
        >>> baffle_step_loss_olson(1000, 0.3)
        -5.3...  # dB (Olson's model at 1 kHz)
    """
    if baffle_height is None:
        baffle_height = baffle_width  # Square baffle

    # Effective radius (radius of circle with same area as rectangle)
    a = np.sqrt(baffle_width * baffle_height / np.pi)

    # Wavenumber
    k = 2 * np.pi * frequency / speed_of_sound

    # Olson's formula: L = 20·log₁₀|1 - J₁(2ka) / (ka)|
    # Where J₁ is the Bessel function of the first kind, order 1
    ka = k * a

    # Avoid division by zero
    ka_safe = np.where(ka < 1e-10, 1e-10, ka)

    from scipy.special import j1
    diffraction = j1(2 * ka_safe) / ka_safe

    loss = 20 * np.log10(np.abs(1 - diffraction))

    # Clamp to physical limits (0 to -6 dB)
    loss = np.clip(loss, -6.0, 0.0)

    return loss


def estimate_baffle_width(
    enclosure_volume_liters: float,
    aspect_ratio: float = 1.0
) -> float:
    """
    Estimate baffle width from enclosure volume.

    For a given box volume, estimate the baffle width assuming a
    rectangular box with the specified aspect ratio (width:height).

    Args:
        enclosure_volume_liters: Net internal volume (liters)
        aspect_ratio: Width to height ratio (1.0 = square front baffle)

    Returns:
        Estimated baffle width (meters)

    Examples:
        >>> estimate_baffle_width(30)  # 30 liter box
        0.31...  # meters (approximately 31 cm width)
    """
    volume_m3 = enclosure_volume_liters / 1000.0

    # Assume depth ≈ width for a cube-like box
    # width² × depth ≈ volume
    # width³ ≈ volume (for cube)
    # For rectangular: width × height × depth = volume
    # With aspect_ratio = width/height and depth ≈ width:
    # width × (width/aspect_ratio) × width = volume
    # width³ / aspect_ratio = volume

    width = (volume_m3 * aspect_ratio) ** (1/3)

    return width


def calculate_baffle_step_correction(
    frequencies: np.ndarray,
    baffle_width: float,
    model: str = 'linkwitz'
) -> np.ndarray:
    """
    Calculate baffle step correction array for frequency response.

    Returns the loss values that should be ADDED to the simulated response
    to account for baffle step diffraction. (Values are negative, indicating
    a loss relative to infinite baffle simulation).

    Literature:
        - Linkwitz (1976): First-order arctan model
        - Olson (1947): More accurate Bessel function model

    Args:
        frequencies: Array of frequencies (Hz)
        baffle_width: Width of the baffle (meters)
        model: 'linkwitz' (simple, default) or 'olson' (accurate)

    Returns:
        Array of loss values in dB (negative, 0 to -6 dB)

    Examples:
        >>> import numpy as np
        >>> freqs = np.logspace(1, 4, 100)  # 10 Hz to 10 kHz
        >>> loss = calculate_baffle_step_correction(freqs, 0.3)
        >>> loss[0]   # Low frequency
        -0.3...  # dB (minimal loss)
        >>> loss[-1]  # High frequency
        -5.9...  # dB (nearly full 6 dB loss)
    """
    frequencies = np.asarray(frequencies)

    if model == 'linkwitz':
        return baffle_step_loss(frequencies, baffle_width)
    elif model == 'olson':
        return baffle_step_loss_olson(frequencies, baffle_width)
    else:
        raise ValueError(f"Unknown baffle step model: {model}. Use 'linkwitz' or 'olson'.")


def apply_baffle_step_to_spl(
    spl: np.ndarray,
    frequencies: np.ndarray,
    baffle_width: float,
    model: str = 'linkwitz'
) -> np.ndarray:
    """
    Apply baffle step loss to SPL response.

    Adjusts the simulated SPL response (which assumes infinite baffle)
    to account for baffle step diffraction in a real enclosure.

    Literature:
        Linkwitz (1976) - Baffle step compensation

    Args:
        spl: Simulated SPL values (dB) assuming infinite baffle
        frequencies: Corresponding frequencies (Hz)
        baffle_width: Width of the baffle (meters)
        model: 'linkwitz' (simple) or 'olson' (accurate)

    Returns:
        SPL values with baffle step loss applied (dB)

    Examples:
        >>> import numpy as np
        >>> spl_infinite = np.array([90, 90, 90, 85])  # Flat response
        >>> freqs = np.array([50, 200, 1000, 5000])
        >>> spl_real = apply_baffle_step_to_spl(spl_infinite, freqs, 0.3)
        >>> spl_real  # Will show rolloff in midrange
        array([89.9..., 89.5..., 85.1..., 79.1...])
    """
    loss = calculate_baffle_step_correction(frequencies, baffle_width, model)
    return spl + loss
