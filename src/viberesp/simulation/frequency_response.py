"""Frequency response simulator for all enclosure types."""

from typing import Dict, Tuple, Optional, List
import numpy as np

from viberesp.enclosures.base import BaseEnclosure
from viberesp.core.constants import (
    FREQ_MIN, FREQ_MAX, FREQ_POINTS_PER_DECADE,
    PASSBAND_MIN, VOLTAGE_1W_8OHM
)


class FrequencyResponseSimulator:
    """
    Unified frequency response calculator for all enclosure types.

    Handles frequency range generation, response calculation,
    and performance metrics extraction.
    """

    def __init__(
        self,
        enclosure: BaseEnclosure,
        freq_range: Optional[Tuple[float, float]] = None,
        points_per_decade: int = None
    ):
        """
        Initialize simulator for an enclosure.

        Args:
            enclosure: Enclosure instance to simulate
            freq_range: (min_freq, max_freq) in Hz
            points_per_decade: Resolution (default: 24)
        """
        self.enclosure = enclosure
        self.freq_range = freq_range or (FREQ_MIN, FREQ_MAX)
        self.points_per_decade = points_per_decade or FREQ_POINTS_PER_DECADE

        # Generate logarithmic frequency array
        self.frequencies = self._generate_frequencies()

    def _generate_frequencies(self) -> np.ndarray:
        """Generate logarithmic frequency sweep."""
        f_min, f_max = self.freq_range
        n_decades = np.log10(f_max) - np.log10(f_min)
        n_points = int(n_decades * self.points_per_decade)
        return np.logspace(np.log10(f_min), np.log10(f_max), n_points)

    def calculate_response(
        self,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Dict[str, np.ndarray]:
        """
        Calculate complete frequency response.

        Args:
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            Dict with 'frequency', 'spl_db', 'phase', 'group_delay'
        """
        spl_db, phase = self.enclosure.calculate_frequency_response(
            self.frequencies,
            voltage
        )

        # Calculate group delay from phase
        group_delay = self._calculate_group_delay(phase)

        return {
            'frequency': self.frequencies,
            'spl_db': spl_db,
            'phase': phase,
            'group_delay': group_delay
        }

    def _calculate_group_delay(self, phase: np.ndarray) -> np.ndarray:
        """
        Calculate group delay from phase response.

        Group delay = -d(φ)/d(ω) = -1/(2π) × d(φ)/df

        Args:
            phase: Phase in degrees

        Returns:
            Group delay in milliseconds
        """
        # Unwrap phase to remove 2π discontinuities
        phase_unwrapped = np.unwrap(np.deg2rad(phase))

        # Calculate derivative with respect to frequency
        dphi_df = np.gradient(phase_unwrapped, self.frequencies)

        # Group delay in seconds
        group_delay_seconds = -dphi_df / (2 * np.pi)

        # Convert to milliseconds
        return group_delay_seconds * 1000

    def calculate_metrics(
        self,
        response_data: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, float]:
        """
        Calculate key performance metrics from frequency response.

        Metrics include:
        - F3: -3dB frequency
        - F10: -10dB frequency
        - Passband ripple: Deviation from flat in passband
        - Sensitivity: SPL at 1kHz
        - Bandwidth: Frequency range in octaves

        Args:
            response_data: Pre-calculated response (optional)

        Returns:
            Dict of metrics
        """
        if response_data is None:
            response_data = self.calculate_response()

        freq = response_data['frequency']
        spl = response_data['spl_db']

        # Calculate normalized SPL (relative to passband)
        passband_mask = freq >= PASSBAND_MIN

        if not np.any(passband_mask):
            # If no passband data, use highest frequencies
            passband_mask = freq >= np.percentile(freq, 80)

        reference_level = np.mean(spl[passband_mask])
        spl_normalized = spl - reference_level

        # -3dB and -10dB frequencies
        f3 = self._find_bandwidth_frequency(freq, spl_normalized, -3)
        f10 = self._find_bandwidth_frequency(freq, spl_normalized, -10)

        # Passband ripple
        passband_spl = spl_normalized[passband_mask]
        ripple = np.max(passband_spl) - np.min(passband_spl)

        # Bandwidth in octaves (from 20Hz to F3)
        bandwidth_octaves = np.log2(max(f3, 20) / 20) if f3 > 20 else 0

        # Sensitivity at 1kHz (or nearest frequency)
        idx_1k = np.argmin(np.abs(freq - 1000))
        sensitivity = spl[idx_1k]

        # Find peak SPL and frequency
        peak_idx = np.argmax(spl)
        peak_spl = spl[peak_idx]
        peak_freq = freq[peak_idx]

        # Calculate average SPL in bass region (20-200Hz)
        bass_mask = (freq >= 20) & (freq <= 200)
        bass_spl = np.mean(spl[bass_mask]) if np.any(bass_mask) else sensitivity

        return {
            'f3': f3,
            'f10': f10,
            'passband_ripple_db': ripple,
            'bandwidth_octaves': bandwidth_octaves,
            'sensitivity_db': sensitivity,
            'peak_spl_db': peak_spl,
            'peak_freq_hz': peak_freq,
            'bass_avg_db': bass_spl,
        }

    def _find_bandwidth_frequency(
        self,
        frequencies: np.ndarray,
        spl: np.ndarray,
        level_db: float
    ) -> float:
        """
        Find frequency where SPL drops to specified level.

        Uses linear interpolation for accuracy.

        For high-pass filters (response rises with frequency), finds the
        upward crossing where SPL transitions from below to above threshold.

        Args:
            frequencies: Frequency array (Hz)
            spl: SPL array (dB, normalized to passband)
            level_db: Target SPL level (e.g., -3 for -3dB point)

        Returns:
            Frequency where SPL = level_db (Hz)
        """
        # Find where SPL drops below threshold
        below_threshold = spl < level_db

        if not np.any(below_threshold):
            # Never drops to this level
            return frequencies[-1]

        # For high-pass filters, find the LAST transition from below to above
        # Search from low to high frequency for upward crossing
        for i in range(len(spl) - 1):
            if spl[i] <= level_db < spl[i + 1]:
                # Linear interpolation for accuracy
                f1, f2 = frequencies[i], frequencies[i + 1]
                spl1, spl2 = spl[i], spl[i + 1]
                fraction = (level_db - spl1) / (spl2 - spl1)
                return f1 + fraction * (f2 - f1)

        # If no upward crossing found, check first/last points
        if spl[0] > level_db:
            # Already above threshold at lowest frequency
            return frequencies[0]
        else:
            # Never reaches threshold
            return frequencies[-1]

    def to_dict(
        self,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Dict:
        """
        Export simulation results to dictionary for JSON serialization.

        Args:
            voltage: Input voltage

        Returns:
            Dict with all results (Python lists, not numpy arrays)
        """
        response = self.calculate_response(voltage)
        metrics = self.calculate_metrics(response)

        return {
            'frequency': response['frequency'].tolist(),
            'spl_db': response['spl_db'].tolist(),
            'phase': response['phase'].tolist(),
            'group_delay_ms': response['group_delay'].tolist(),
            'metrics': metrics
        }

    def get_summary(self) -> str:
        """
        Get human-readable summary of simulation results.

        Returns:
            Formatted summary string
        """
        response = self.calculate_response()
        metrics = self.calculate_metrics(response)

        summary = f"""
{'='*60}
Frequency Response Summary
{'='*60}

Enclosure: {self.enclosure.params.enclosure_type}
Box Volume: {self.enclosure.params.vb:.1f} L

Performance Metrics:
  F3 (-3dB):      {metrics['f3']:.1f} Hz
  F10 (-10dB):    {metrics['f10']:.1f} Hz
  Passband Ripple: {metrics['passband_ripple_db']:.2f} dB
  Sensitivity:    {metrics['sensitivity_db']:.1f} dB (1W/1m)
  Bandwidth:      {metrics['bandwidth_octaves']:.1f} octaves

Peak Response:
  {metrics['peak_spl_db']:.1f} dB at {metrics['peak_freq_hz']:.1f} Hz

Bass Response (20-200Hz):
  Average: {metrics['bass_avg_db']:.1f} dB

{'='*60}
"""
        return summary.strip()


def compare_enclosures(
    enclosures: List[BaseEnclosure],
    freq_range: Optional[Tuple[float, float]] = None
) -> Dict:
    """
    Compare multiple enclosures and return metrics for each.

    Args:
        enclosures: List of enclosure instances
        freq_range: Frequency range (Hz)

    Returns:
        Dict with comparison results
    """
    results = {}

    for i, enclosure in enumerate(enclosures):
        simulator = FrequencyResponseSimulator(enclosure, freq_range)
        response = simulator.calculate_response()
        metrics = simulator.calculate_metrics(response)

        enclosure_name = f"{enclosure.params.enclosure_type}_{i}"
        results[enclosure_name] = {
            'params': enclosure.get_summary(),
            'response': response,
            'metrics': metrics
        }

    return results
