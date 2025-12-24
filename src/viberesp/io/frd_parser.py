"""FRD (Frequency Response Data) file parser."""

import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FRDParser:
    """
    Parse FRD (Frequency Response Data) files.

    FRD Format:
    - Lines starting with * are comments/headers
    - Data: frequency(Hz) magnitude(dB) [phase(degrees)]
    - Phase is optional
    - Whitespace-separated values

    Example:
        * Frequency Response Data
        * Measured on 2024-01-01
        20.0      -12.5    -45.2
        25.0      -10.3    -38.1
        31.5      -8.2     -30.5
        ...
    """

    @staticmethod
    def parse(file_path: str) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Parse FRD file and return frequency, magnitude, and phase arrays.

        Args:
            file_path: Path to FRD file

        Returns:
            (frequency, magnitude_db, phase_degrees)
            phase_degrees is None if not present in file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"FRD file not found: {file_path}")

        frequencies = []
        magnitudes = []
        phases = []
        has_phase = False

        line_number = 0
        data_lines = 0

        try:
            with open(path, 'r') as f:
                for line in f:
                    line_number += 1
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('*'):
                        continue

                    # Parse data line
                    parts = line.split()

                    if len(parts) < 2:
                        logger.warning(
                            f"Line {line_number}: Insufficient columns "
                            f"({len(parts)} < 2). Skipping."
                        )
                        continue

                    try:
                        freq = float(parts[0])
                        mag = float(parts[1])

                        # Validate frequency range
                        if freq <= 0:
                            logger.warning(
                                f"Line {line_number}: Invalid frequency {freq} Hz. Skipping."
                            )
                            continue

                        frequencies.append(freq)
                        magnitudes.append(mag)

                        # Phase is optional
                        if len(parts) >= 3:
                            phase = float(parts[2])
                            phases.append(phase)
                            has_phase = True

                        data_lines += 1

                    except ValueError as e:
                        logger.warning(
                            f"Line {line_number}: Failed to parse values: {e}. Skipping."
                        )
                        continue

        except Exception as e:
            raise ValueError(f"Error reading FRD file: {e}")

        if data_lines == 0:
            raise ValueError(f"No valid data found in FRD file: {file_path}")

        if len(frequencies) != len(magnitudes):
            raise ValueError("Frequency and magnitude array length mismatch")

        if has_phase and len(frequencies) != len(phases):
            logger.warning("Phase data incomplete. Ignoring phase.")
            has_phase = False

        freq_array = np.array(frequencies)
        mag_array = np.array(magnitudes)
        phase_array = np.array(phases) if has_phase else None

        logger.info(
            f"Parsed {data_lines} data points from {file_path} "
            f"(phase: {'yes' if has_phase else 'no'})"
        )

        return freq_array, mag_array, phase_array

    @staticmethod
    def save(
        file_path: str,
        frequency: np.ndarray,
        magnitude: np.ndarray,
        phase: Optional[np.ndarray] = None,
        comments: Optional[List[str]] = None
    ) -> None:
        """
        Save frequency response data to FRD file.

        Args:
            file_path: Output file path
            frequency: Frequency array (Hz)
            magnitude: SPL magnitude array (dB)
            phase: Phase array (degrees), optional
            comments: List of comment lines for header
        """
        if len(frequency) != len(magnitude):
            raise ValueError("Frequency and magnitude arrays must have same length")

        if phase is not None and len(frequency) != len(phase):
            raise ValueError("Frequency and phase arrays must have same length")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            # Write comments/header
            if comments:
                for comment in comments:
                    f.write(f"* {comment}\n")
            else:
                f.write("* Frequency Response Data\n")
                f.write(f"* Generated by viberesp\n")
                f.write(f"* Points: {len(frequency)}\n")

            # Write data
            for i in range(len(frequency)):
                if phase is not None:
                    f.write(f"{frequency[i]:.2f} {magnitude[i]:.3f} {phase[i]:.2f}\n")
                else:
                    f.write(f"{frequency[i]:.2f} {magnitude[i]:.3f}\n")

        logger.info(f"Saved {len(frequency)} data points to {file_path}")

    @staticmethod
    def resample(
        frequency: np.ndarray,
        magnitude: np.ndarray,
        new_freq: np.ndarray
    ) -> np.ndarray:
        """
        Resample frequency response data to new frequency points.

        Uses linear interpolation in log-frequency space.

        Args:
            frequency: Original frequency array (Hz)
            magnitude: Original magnitude array (dB)
            new_freq: New frequency array (Hz)

        Returns:
            Resampled magnitude array (dB)
        """
        # Interpolate in log space
        log_freq = np.log10(frequency)
        log_new_freq = np.log10(new_freq)

        mag_resampled = np.interp(log_new_freq, log_freq, magnitude)

        return mag_resampled

    @staticmethod
    def merge(
        frd_files: List[str],
        output_path: str
    ) -> None:
        """
        Merge multiple FRD files into one.

        Combines all data points and sorts by frequency.

        Args:
            frd_files: List of FRD file paths
            output_path: Output FRD file path
        """
        all_freq = []
        all_mag = []
        all_phase = []
        has_phase = False

        for frd_file in frd_files:
            freq, mag, phase = FRDParser.parse(frd_file)
            all_freq.extend(freq.tolist())
            all_mag.extend(mag.tolist())

            if phase is not None:
                all_phase.extend(phase.tolist())
                has_phase = True

        # Sort by frequency
        sorted_indices = np.argsort(all_freq)
        sorted_freq = np.array(all_freq)[sorted_indices]
        sorted_mag = np.array(all_mag)[sorted_indices]

        sorted_phase = None
        if has_phase:
            sorted_phase = np.array(all_phase)[sorted_indices]

        # Remove duplicates (keep first occurrence)
        unique_mask = np.concatenate(([True], np.diff(sorted_freq) != 0))
        sorted_freq = sorted_freq[unique_mask]
        sorted_mag = sorted_mag[unique_mask]

        if sorted_phase is not None:
            sorted_phase = sorted_phase[unique_mask]

        FRDParser.save(output_path, sorted_freq, sorted_mag, sorted_phase)

        logger.info(f"Merged {len(frd_files)} files into {output_path}")


class ZMAParser:
    """
    Parse ZMA (Impedance Data) files.

    ZMA Format:
    - Lines starting with * are comments/headers
    - Data: frequency(Hz) resistance(ohms) reactance(ohms)
    - Or: frequency(Hz) magnitude(ohms) phase(degrees)
    - Whitespace-separated values

    Example:
        * Impedance Data
        20.0      45.2     12.3
        25.0      52.1     18.5
        31.5      68.3     25.7
        ...
    """

    @staticmethod
    def parse(file_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Parse ZMA file and return frequency, resistance, and reactance.

        Args:
            file_path: Path to ZMA file

        Returns:
            (frequency, resistance_ohms, reactance_ohms)

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"ZMA file not found: {file_path}")

        frequencies = []
        resistances = []
        reactances = []

        line_number = 0
        data_lines = 0

        try:
            with open(path, 'r') as f:
                for line in f:
                    line_number += 1
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('*'):
                        continue

                    # Parse data line
                    parts = line.split()

                    if len(parts) < 3:
                        logger.warning(
                            f"Line {line_number}: Insufficient columns "
                            f"({len(parts)} < 3). Skipping."
                        )
                        continue

                    try:
                        freq = float(parts[0])
                        r = float(parts[1])
                        x = float(parts[2])

                        # Validate frequency range
                        if freq <= 0:
                            logger.warning(
                                f"Line {line_number}: Invalid frequency {freq} Hz. Skipping."
                            )
                            continue

                        frequencies.append(freq)
                        resistances.append(r)
                        reactances.append(x)
                        data_lines += 1

                    except ValueError as e:
                        logger.warning(
                            f"Line {line_number}: Failed to parse values: {e}. Skipping."
                        )
                        continue

        except Exception as e:
            raise ValueError(f"Error reading ZMA file: {e}")

        if data_lines == 0:
            raise ValueError(f"No valid data found in ZMA file: {file_path}")

        freq_array = np.array(frequencies)
        r_array = np.array(resistances)
        x_array = np.array(reactances)

        logger.info(f"Parsed {data_lines} data points from {file_path}")

        return freq_array, r_array, x_array

    @staticmethod
    def calculate_impedance_magnitude(
        resistance: np.ndarray,
        reactance: np.ndarray
    ) -> np.ndarray:
        """
        Calculate impedance magnitude from resistance and reactance.

        Z = sqrt(R² + X²)

        Args:
            resistance: Resistance array (ohms)
            reactance: Reactance array (ohms)

        Returns:
            Impedance magnitude array (ohms)
        """
        return np.sqrt(resistance**2 + reactance**2)

    @staticmethod
    def calculate_impedance_phase(
        resistance: np.ndarray,
        reactance: np.ndarray
    ) -> np.ndarray:
        """
        Calculate impedance phase from resistance and reactance.

        φ = arctan(X/R)

        Args:
            resistance: Resistance array (ohms)
            reactance: Reactance array (ohms)

        Returns:
            Phase array (degrees)
        """
        phase_rad = np.arctan2(reactance, resistance)
        return np.rad2deg(phase_rad)

    @staticmethod
    def extract_ts_parameters(
        frequency: np.ndarray,
        resistance: np.ndarray,
        reactance: np.ndarray
    ) -> dict:
        """
        Extract Thiele-Small parameters from impedance data.

        This is a simplified extraction. For accurate results,
        use dedicated measurement software.

        Args:
            frequency: Frequency array (Hz)
            resistance: Resistance array (ohms)
            reactance: Reactance array (ohms)

        Returns:
            Dict with extracted parameters (Fs, Re, Qms, Qes, Qts)
        """
        # Find impedance peak (Fs)
        z_mag = ZMAParser.calculate_impedance_magnitude(resistance, reactance)
        peak_idx = np.argmax(z_mag)
        fs = frequency[peak_idx]
        z_max = z_mag[peak_idx]

        # Minimum impedance (Re, DC resistance)
        # Usually at high frequency where inductive dominates
        re = np.min(resistance)

        # Calculate bandwidth at -3dB from peak
        z_minus_3db = z_max / np.sqrt(2)

        # Find frequencies where impedance crosses this level
        above_threshold = z_mag > z_minus_3db

        if not np.any(above_threshold):
            logger.warning("Could not find -3dB bandwidth points")
            return {}

            # Find crossing points
        crossings = np.where(np.diff(above_threshold.astype(int)) != 0)[0]

        if len(crossings) < 2:
            logger.warning("Could not find both -3dB bandwidth points")
            return {}

        f1 = frequency[crossings[0]]
        f2 = frequency[crossings[1]]

        # Calculate Q values
        # Qms = Fs × sqrt(Rmax/Re) / (f2 - f1)
        # Qes = Qms / (Rmax/Re - 1)
        r_ratio = z_max / re

        qms = fs * np.sqrt(r_ratio) / (f2 - f1)
        qes = qms / (r_ratio - 1)
        qts = (qes * qms) / (qes + qms)

        return {
            'fs': fs,
            're': re,
            'qms': qms,
            'qes': qes,
            'qts': qts,
            'z_max': z_max,
        }

    @staticmethod
    def save(
        file_path: str,
        frequency: np.ndarray,
        resistance: np.ndarray,
        reactance: np.ndarray,
        comments: Optional[List[str]] = None
    ) -> None:
        """
        Save impedance data to ZMA file.

        Args:
            file_path: Output file path
            frequency: Frequency array (Hz)
            resistance: Resistance array (ohms)
            reactance: Reactance array (ohms)
            comments: List of comment lines for header
        """
        if len(frequency) != len(resistance) or len(frequency) != len(reactance):
            raise ValueError("All arrays must have same length")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            # Write comments/header
            if comments:
                for comment in comments:
                    f.write(f"* {comment}\n")
            else:
                f.write("* Impedance Data\n")
                f.write(f"* Generated by viberesp\n")
                f.write(f"* Points: {len(frequency)}\n")

            # Write data
            for i in range(len(frequency)):
                f.write(f"{frequency[i]:.2f} {resistance[i]:.3f} {reactance[i]:.3f}\n")

        logger.info(f"Saved {len(frequency)} data points to {file_path}")
