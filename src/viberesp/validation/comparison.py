"""Compare Viberesp and Hornresp frequency responses.

This module handles interpolation, alignment, and comparison of frequency
response data between Viberesp and Hornresp.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ComparisonResult:
    """Result of comparing Viberesp and Hornresp responses.

    Attributes:
        common_freq: Common frequency grid for comparison
        viberesp_spl_aligned: Viberesp SPL aligned to Hornresp
        hornresp_spl: Hornresp SPL on common grid
        spl_difference: Difference (Viberesp - Hornresp) in dB
        viberesp_phase_aligned: Viberesp phase aligned (if available)
        hornresp_phase: Hornresp phase on common grid (if available)
        phase_difference: Phase difference (Viberesp - Hornresp) in degrees
        passband_offset: SPL offset applied for alignment in dB
    """

    common_freq: np.ndarray
    viberesp_spl_aligned: np.ndarray
    hornresp_spl: np.ndarray
    spl_difference: np.ndarray
    viberesp_phase_aligned: Optional[np.ndarray]
    hornresp_phase: Optional[np.ndarray]
    phase_difference: Optional[np.ndarray]
    passband_offset: float


def create_log_frequency_grid(
    freq_min: float,
    freq_max: float,
    points_per_decade: int = 24,
) -> np.ndarray:
    """Create logarithmically spaced frequency grid.

    Args:
        freq_min: Minimum frequency in Hz
        freq_max: Maximum frequency in Hz
        points_per_decade: Number of points per decade

    Returns:
        Array of frequency values
    """
    n_decades = np.log10(freq_max) - np.log10(freq_min)
    n_points = int(n_decades * points_per_decade) + 1
    return np.logspace(np.log10(freq_min), np.log10(freq_max), n_points)


def interpolate_to_common_grid(
    frequencies: np.ndarray,
    values: np.ndarray,
    common_freq: np.ndarray,
    log_space: bool = True,
) -> np.ndarray:
    """Interpolate values to common frequency grid.

    Args:
        frequencies: Original frequency values
        values: Original values (SPL or phase)
        common_freq: Target frequency grid
        log_space: If True, interpolate in log space

    Returns:
        Interpolated values on common grid
    """
    if log_space:
        # Interpolate in log space
        return np.interp(
            np.log10(common_freq),
            np.log10(frequencies),
            values,
            left=np.nan,
            right=np.nan,
        )
    else:
        return np.interp(common_freq, frequencies, values, left=np.nan, right=np.nan)


def calculate_passband_offset(
    viberesp_freq: np.ndarray,
    viberesp_spl: np.ndarray,
    hornresp_freq: np.ndarray,
    hornresp_spl: np.ndarray,
    passband_min: float = 200,
    passband_max: float = 500,
) -> float:
    """Calculate SPL offset to align passband responses.

    The offset is the mean difference in the passband range.
    Positive offset means Viberesp is lower than Hornresp.

    Args:
        viberesp_freq: Viberesp frequency array
        viberesp_spl: Viberesp SPL array
        hornresp_freq: Hornresp frequency array
        hornresp_spl: Hornresp SPL array
        passband_min: Passband minimum frequency in Hz
        passband_max: Passband maximum frequency in Hz

    Returns:
        Offset in dB to add to Viberesp for alignment
    """
    # Find indices within passband - use different variable names to avoid scoping issues
    vib_mask = (viberesp_freq >= passband_min) & (viberesp_freq <= passband_max)
    hr_mask = (hornresp_freq >= passband_min) & (hornresp_freq <= passband_max)

    has_vib = np.any(vib_mask)
    has_hr = np.any(hr_mask)

    if not has_vib or not has_hr:
        return 0.0

    # Extract passband values
    vib_spl_pb = viberesp_spl[vib_mask]
    hr_spl_pb = hornresp_spl[hr_mask]

    # Interpolate Viberesp to Hornresp frequencies for comparison
    hr_freq_pb = hornresp_freq[hr_mask]
    vib_freq_pb = viberesp_freq[vib_mask]
    vib_interp = np.interp(hr_freq_pb, vib_freq_pb, vib_spl_pb)

    # Calculate mean difference
    offset_val = np.mean(hr_spl_pb - vib_interp)

    return offset_val


def unwrap_phase_difference(phase1: np.ndarray, phase2: np.ndarray) -> np.ndarray:
    """Calculate phase difference handling wraparound at ±180°.

    Args:
        phase1: First phase array in degrees
        phase2: Second phase array in degrees

    Returns:
        Phase difference wrapped to ±180°
    """
    diff = phase1 - phase2
    # Wrap to ±180°
    return (diff + 180) % 360 - 180


def compare_responses(
    viberesp_freq: np.ndarray,
    viberesp_spl: np.ndarray,
    viberesp_phase: Optional[np.ndarray],
    hornresp_freq: np.ndarray,
    hornresp_spl: np.ndarray,
    hornresp_phase: Optional[np.ndarray],
    freq_min: float = 20,
    freq_max: float = 500,
    passband_min: float = 200,
    passband_max: float = 500,
) -> ComparisonResult:
    """Compare Viberesp and Hornresp frequency responses.

    This function:
    1. Creates a common log-spaced frequency grid
    2. Interpolates both datasets to the common grid
    3. Calculates and applies passband SPL offset
    4. Computes SPL and phase differences

    Args:
        viberesp_freq: Viberesp frequency array (Hz)
        viberesp_spl: Viberesp SPL array (dB)
        viberesp_phase: Viberesp phase array (degrees), optional
        hornresp_freq: Hornresp frequency array (Hz)
        hornresp_spl: Hornresp SPL array (dB)
        hornresp_phase: Hornresp phase array (degrees), optional
        freq_min: Minimum frequency for comparison
        freq_max: Maximum frequency for comparison
        passband_min: Passband minimum for SPL alignment
        passband_max: Passband maximum for SPL alignment

    Returns:
        ComparisonResult with aligned data and differences
    """
    # Create common frequency grid
    common_freq = create_log_frequency_grid(freq_min, freq_max)

    # Calculate passband offset
    offset = calculate_passband_offset(
        viberesp_freq,
        viberesp_spl,
        hornresp_freq,
        hornresp_spl,
        passband_min,
        passband_max,
    )

    # Apply offset to Viberesp SPL
    viberesp_spl_shifted = viberesp_spl + offset

    # Interpolate SPL to common grid
    viberesp_spl_interp = interpolate_to_common_grid(
        viberesp_freq,
        viberesp_spl_shifted,
        common_freq,
    )
    hornresp_spl_interp = interpolate_to_common_grid(
        hornresp_freq,
        hornresp_spl,
        common_freq,
    )

    # Calculate SPL difference
    spl_diff = viberesp_spl_interp - hornresp_spl_interp

    # Handle phase comparison if both datasets have phase
    viberesp_phase_interp = None
    hornresp_phase_interp = None
    phase_diff = None

    if viberesp_phase is not None and hornresp_phase is not None:
        viberesp_phase_interp = interpolate_to_common_grid(
            viberesp_freq,
            viberesp_phase,
            common_freq,
        )
        hornresp_phase_interp = interpolate_to_common_grid(
            hornresp_freq,
            hornresp_phase,
            common_freq,
        )
        phase_diff = unwrap_phase_difference(viberesp_phase_interp, hornresp_phase_interp)

    return ComparisonResult(
        common_freq=common_freq,
        viberesp_spl_aligned=viberesp_spl_interp,
        hornresp_spl=hornresp_spl_interp,
        spl_difference=spl_diff,
        viberesp_phase_aligned=viberesp_phase_interp,
        hornresp_phase=hornresp_phase_interp,
        phase_difference=phase_diff,
        passband_offset=offset,
    )
