"""Parse Hornresp output files for validation.

This module parses Hornresp tabular output and parameter files to extract
frequency response data and driver parameters for validation against Viberesp.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class HornrespData:
    """Container for parsed Hornresp frequency response data.

    Attributes:
        frequencies: Array of frequency values in Hz
        spl: Array of SPL values in dB
        phase: Array of phase values in degrees (WPhase)
        delay: Array of delay values in milliseconds
    """

    frequencies: np.ndarray
    spl: np.ndarray
    phase: np.ndarray
    delay: np.ndarray

    def __len__(self) -> int:
        return len(self.frequencies)


@dataclass
class HornrespParams:
    """Container for parsed Hornresp driver parameters.

    Attributes:
        sd: Effective piston area in cm²
        bl: Force factor in T·m
        cms: Mechanical compliance in m/N
        rms: Mechanical resistance in N·s/m
        mmd: Moving mass in grams
        le: Voice coil inductance in mH
        re: Voice coil resistance in ohms
        nd: Number of drivers
        vrc: Rear chamber volume in liters
        lrc: Rear chamber length in cm
        vtc: Front chamber volume in liters
        atc: Front chamber throat area in cm²
        eg: Input voltage in volts
        s1: Throat area in cm² (for horns)
        s2: Mouth area in cm² (for horns)
        exp: Horn length in cm (exponential horn)
        f12: Cutoff frequency in Hz (for horns)
    """

    sd: float
    bl: float
    cms: float
    rms: float
    mmd: float
    le: float
    re: float
    nd: int
    vrc: float
    lrc: float
    vtc: float
    atc: float
    eg: float
    s1: Optional[float] = None
    s2: Optional[float] = None
    exp: Optional[float] = None
    f12: Optional[float] = None


def parse_hornresp_output(file_path: str | Path) -> HornrespData:
    """Parse Hornresp tabular output file.

    Hornresp outputs tab-separated data with 17 columns:
    - Col 0: Frequency (Hz)
    - Col 4: SPL (dB)
    - Col 7: WPhase (degrees) - use WPhase for sealed enclosures
    - Col 10: Delay (msec)

    Args:
        file_path: Path to Hornresp output file

    Returns:
        HornrespData containing parsed arrays

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Hornresp output file not found: {file_path}")

    lines = file_path.read_text().strip().split('\n')

    # Skip header and empty line
    if len(lines) < 3:
        raise ValueError(f"File appears to have insufficient data lines: {file_path}")

    data_lines = lines[2:]  # Skip header and empty line

    frequencies = []
    spl_values = []
    phase_values = []
    delay_values = []

    for line in data_lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')
        if len(parts) < 11:
            continue  # Skip malformed lines

        try:
            freq = float(parts[0])
            spl = float(parts[4])
            phase = float(parts[7])
            delay = float(parts[10])

            frequencies.append(freq)
            spl_values.append(spl)
            phase_values.append(phase)
            delay_values.append(delay)
        except (ValueError, IndexError) as e:
            # Skip lines with parsing errors
            continue

    if not frequencies:
        raise ValueError(f"No valid data found in file: {file_path}")

    return HornrespData(
        frequencies=np.array(frequencies),
        spl=np.array(spl_values),
        phase=np.array(phase_values),
        delay=np.array(delay_values),
    )


def parse_hornresp_params(file_path: str | Path) -> HornrespParams:
    """Parse Hornresp parameter file.

    Hornresp parameter files use the format:
    ```
    Sd = 522.00
    Bl = 23.69
    Cms = 1.06E-04
    ...
    S1 = 400.00
    S2 = 20000.00
    Exp = 220.00
    F12 = 48.68
    ```

    Args:
        file_path: Path to Hornresp parameter file

    Returns:
        HornrespParams containing parsed values

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required parameters are missing
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Hornresp parameter file not found: {file_path}")

    content = file_path.read_text()

    # Parse values using regex
    patterns = {
        'sd': r'Sd\s*=\s*([\d.E+-]+)',
        'bl': r'Bl\s*=\s*([\d.E+-]+)',
        'cms': r'Cms\s*=\s*([\d.E+-]+)',
        'rms': r'Rms\s*=\s*([\d.E+-]+)',
        'mmd': r'Mmd\s*=\s*([\d.E+-]+)',
        'le': r'Le\s*=\s*([\d.E+-]+)',
        're': r'Re\s*=\s*([\d.E+-]+)',
        'nd': r'Nd\s*=\s*(\d+)',
        'vrc': r'Vrc\s*=\s*([\d.E+-]+)',
        'lrc': r'Lrc\s*=\s*([\d.E+-]+)',
        'vtc': r'Vtc\s*=\s*([\d.E+-]+)',
        'atc': r'Atc\s*=\s*([\d.E+-]+)',
        'eg': r'Eg\s*=\s*([\d.E+-]+)',
    }

    # Horn parameters (optional)
    horn_patterns = {
        's1': r'S1\s*=\s*([\d.E+-]+)',
        's2': r'S2\s*=\s*([\d.E+-]+)',
        'exp': r'Exp\s*=\s*([\d.E+-]+)',
        'f12': r'F12\s*=\s*([\d.E+-]+)',
    }

    parsed = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            parsed[key] = float(match.group(1))
        else:
            raise ValueError(f"Required parameter '{key}' not found in {file_path}")

    # Parse optional horn parameters
    horn_parsed = {}
    for key, pattern in horn_patterns.items():
        match = re.search(pattern, content)
        if match:
            horn_parsed[key] = float(match.group(1))

    return HornrespParams(
        sd=parsed['sd'],
        bl=parsed['bl'],
        cms=parsed['cms'],
        rms=parsed['rms'],
        mmd=parsed['mmd'],
        le=parsed['le'],
        re=parsed['re'],
        nd=int(parsed['nd']),
        vrc=parsed['vrc'],
        lrc=parsed['lrc'],
        vtc=parsed['vtc'],
        atc=parsed['atc'],
        eg=parsed['eg'],
        s1=horn_parsed.get('s1'),
        s2=horn_parsed.get('s2'),
        exp=horn_parsed.get('exp'),
        f12=horn_parsed.get('f12'),
    )


def hornresp_params_to_ts(params: HornrespParams) -> dict:
    """Convert Hornresp parameters to Viberesp Thiele-Small format.

    Hornresp provides Cms and Mmd directly. Viberesp uses Vas, which needs
    to be calculated from Cms, Sd, and air density.

    Fs (resonance frequency) = 1 / (2π × sqrt(Cms × Mmd))

    Args:
        params: HornrespParams object

    Returns:
        Dictionary with Viberesp-compatible T/S parameters
    """
    # Constants
    rho = 1.18  # Air density in kg/m³
    c = 343.5  # Speed of sound in m/s

    # Convert Sd from cm² to m²
    sd_m2 = params.sd / 10000

    # Convert Mmd from grams to kg
    mmd_kg = params.mmd / 1000

    # Calculate resonance frequency
    fs = 1 / (2 * np.pi * np.sqrt(params.cms * mmd_kg))

    # Calculate equivalent volume of compliance (Vas)
    # Vas = rho × c² × Sd² × Cms
    vas_m3 = rho * c**2 * sd_m2**2 * params.cms
    vas_liters = vas_m3 * 1000

    return {
        'fs': fs,
        'vas': vas_liters,
        'sd': sd_m2,
        're': params.re,
        'bl': params.bl,
        'mmd': mmd_kg * 1000,  # Convert back to grams
        'le': params.le,
        'cms': params.cms,
    }
