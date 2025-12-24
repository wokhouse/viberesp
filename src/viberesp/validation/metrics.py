"""Calculate validation metrics for comparing Viberesp and Hornresp.

This module provides quantitative metrics to assess agreement between
simulations, including RMSE, MAE, F3 error, correlation, and overall
agreement score.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats


@dataclass
class ValidationMetrics:
    """Comprehensive validation metrics.

    Attributes:
        rmse: Root Mean Square Error (dB)
        mae: Mean Absolute Error (dB)
        max_error: Maximum absolute error (dB)
        max_error_freq: Frequency of maximum error (Hz)
        passband_rmse: RMSE in passband (dB)
        bass_rmse: RMSE in bass region (dB)
        f3_viberesp: Viberesp -3dB frequency (Hz)
        f3_hornresp: Hornresp -3dB frequency (Hz)
        f3_error: Difference in F3 frequencies (Hz)
        correlation: Pearson correlation coefficient
        agreement_score: Overall agreement score (0-100%)
    """

    rmse: float
    mae: float
    max_error: float
    max_error_freq: float
    passband_rmse: float
    bass_rmse: float
    f3_viberesp: Optional[float]
    f3_hornresp: Optional[float]
    f3_error: Optional[float]
    correlation: float
    agreement_score: float


def calculate_rmse(values: np.ndarray) -> float:
    """Calculate Root Mean Square Error.

    Args:
        values: Array of error values

    Returns:
        RMSE
    """
    return np.sqrt(np.mean(values**2))


def calculate_mae(values: np.ndarray) -> float:
    """Calculate Mean Absolute Error.

    Args:
        values: Array of error values

    Returns:
        MAE
    """
    return np.mean(np.abs(values))


def calculate_correlation(
    viberesp_spl: np.ndarray,
    hornresp_spl: np.ndarray,
) -> float:
    """Calculate Pearson correlation coefficient.

    Args:
        viberesp_spl: Viberesp SPL values
        hornresp_spl: Hornresp SPL values

    Returns:
        Correlation coefficient
    """
    # Remove NaN values
    mask = ~(np.isnan(viberesp_spl) | np.isnan(hornresp_spl))
    if np.sum(mask) < 2:
        return 0.0

    correlation, _ = stats.pearsonr(
        viberesp_spl[mask],
        hornresp_spl[mask],
    )
    return correlation


def find_f3_frequency(
    frequencies: np.ndarray,
    spl: np.ndarray,
    reference_level: float,
) -> Optional[float]:
    """Find -3dB cutoff frequency.

    The F3 frequency is where the response is 3dB below the reference level.
    For a high-pass (sealed enclosure), we search upward from minimum frequency.

    Args:
        frequencies: Frequency array (Hz)
        spl: SPL array (dB)
        reference_level: Reference SPL level in dB

    Returns:
        F3 frequency in Hz, or None if not found
    """
    target_level = reference_level - 3

    # Find where SPL crosses target level
    # For high-pass, we look for upward crossing
    for i in range(len(spl) - 1):
        if spl[i] <= target_level < spl[i + 1]:
            # Linear interpolation for precise frequency
            frac = (target_level - spl[i]) / (spl[i + 1] - spl[i])
            return frequencies[i] + frac * (frequencies[i + 1] - frequencies[i])

    return None


def calculate_band_rmse(
    differences: np.ndarray,
    frequencies: np.ndarray,
    freq_min: float,
    freq_max: float,
) -> float:
    """Calculate RMSE for a specific frequency band.

    Args:
        differences: SPL difference array
        frequencies: Frequency array
        freq_min: Band minimum frequency
        freq_max: Band maximum frequency

    Returns:
        RMSE in the specified band
    """
    mask = (frequencies >= freq_min) & (frequencies <= freq_max)
    band_diff = differences[mask]

    if len(band_diff) == 0:
        return np.nan

    return calculate_rmse(band_diff)


def calculate_agreement_score(metrics: ValidationMetrics) -> float:
    """Calculate overall agreement score (0-100%).

    The score is based on:
    - RMSE (primary factor): <0.5dB is excellent, >2dB is poor
    - Correlation: >0.99 is excellent
    - F3 error: <1Hz is excellent

    Args:
        metrics: ValidationMetrics object

    Returns:
        Agreement score from 0 to 100
    """
    # RMSE score: 0-50 points
    if metrics.rmse < 0.5:
        rmse_score = 50
    elif metrics.rmse < 1.0:
        rmse_score = 40
    elif metrics.rmse < 1.5:
        rmse_score = 25
    elif metrics.rmse < 2.0:
        rmse_score = 10
    else:
        rmse_score = 0

    # Correlation score: 0-30 points
    if metrics.correlation > 0.995:
        corr_score = 30
    elif metrics.correlation > 0.99:
        corr_score = 25
    elif metrics.correlation > 0.98:
        corr_score = 15
    elif metrics.correlation > 0.95:
        corr_score = 5
    else:
        corr_score = 0

    # F3 error score: 0-20 points
    f3_score = 0
    if metrics.f3_error is not None:
        if abs(metrics.f3_error) < 1:
            f3_score = 20
        elif abs(metrics.f3_error) < 2:
            f3_score = 15
        elif abs(metrics.f3_error) < 3:
            f3_score = 10
        elif abs(metrics.f3_error) < 5:
            f3_score = 5

    return rmse_score + corr_score + f3_score


def calculate_validation_metrics(
    comparison,
    passband_min: float = 200,
    passband_max: float = 500,
    bass_min: float = 20,
    bass_max: float = 200,
) -> ValidationMetrics:
    """Calculate comprehensive validation metrics from comparison result.

    Args:
        comparison: ComparisonResult object
        passband_min: Passband minimum frequency (Hz)
        passband_max: Passband maximum frequency (Hz)
        bass_min: Bass region minimum frequency (Hz)
        bass_max: Bass region maximum frequency (Hz)

    Returns:
        ValidationMetrics object with all calculated metrics
    """
    # Remove NaN values from differences
    mask = ~np.isnan(comparison.spl_difference)
    valid_diff = comparison.spl_difference[mask]
    valid_freq = comparison.common_freq[mask]

    if len(valid_diff) == 0:
        raise ValueError("No valid data points for metrics calculation")

    # Basic metrics
    rmse = calculate_rmse(valid_diff)
    mae = calculate_mae(valid_diff)
    max_error_idx = np.argmax(np.abs(valid_diff))
    max_error = abs(valid_diff[max_error_idx])
    max_error_freq = valid_freq[max_error_idx]

    # Band-specific RMSE
    passband_rmse = calculate_band_rmse(
        comparison.spl_difference,
        comparison.common_freq,
        passband_min,
        passband_max,
    )
    bass_rmse = calculate_band_rmse(
        comparison.spl_difference,
        comparison.common_freq,
        bass_min,
        bass_max,
    )

    # Correlation
    correlation = calculate_correlation(
        comparison.viberesp_spl_aligned,
        comparison.hornresp_spl,
    )

    # F3 frequencies
    # Use maximum SPL as reference for high-pass filter
    viberesp_max = np.nanmax(comparison.viberesp_spl_aligned)
    hornresp_max = np.nanmax(comparison.hornresp_spl)

    f3_viberesp = find_f3_frequency(
        comparison.common_freq,
        comparison.viberesp_spl_aligned,
        viberesp_max,
    )
    f3_hornresp = find_f3_frequency(
        comparison.common_freq,
        comparison.hornresp_spl,
        hornresp_max,
    )

    f3_error = None
    if f3_viberesp is not None and f3_hornresp is not None:
        f3_error = f3_viberesp - f3_hornresp

    # Create metrics object
    metrics = ValidationMetrics(
        rmse=rmse,
        mae=mae,
        max_error=max_error,
        max_error_freq=max_error_freq,
        passband_rmse=passband_rmse,
        bass_rmse=bass_rmse,
        f3_viberesp=f3_viberesp,
        f3_hornresp=f3_hornresp,
        f3_error=f3_error,
        correlation=correlation,
        agreement_score=0.0,  # Will be calculated
    )

    # Calculate overall agreement score
    metrics.agreement_score = calculate_agreement_score(metrics)

    return metrics
