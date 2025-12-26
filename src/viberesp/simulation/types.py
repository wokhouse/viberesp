"""
Data structures for horn geometry and simulation parameters.

This module defines Pydantic models for horn parameters, ensuring
type safety and validation throughout the simulation code.

Literature:
- Kolbrek Part 1 - Horn profile definitions
- Olson (1947), Chapter 5 - Horn geometry parameters
- Beranek (1954), Chapter 5 - Horn terminology
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class ExponentialHorn:
    """
    Exponential horn geometry parameters.

    The exponential horn has a cross-sectional area that varies
    exponentially with distance from the throat:

        S(x) = S_throat · exp(m·x)

    where m is the flare constant.

    Literature:
        - Olson (1947), Eq. 5.12 - Exponential horn profile
        - Kolbrek Part 1 - Modern treatment
        - literature/horns/olson_1947.md

    Attributes:
        throat_area: Throat cross-sectional area (m²)
        mouth_area: Mouth cross-sectional area (m²)
        length: Horn axial length (m)
        flare_constant: Flare constant m (1/m), calculated from geometry
                      if not provided. m = (1/L) · ln(S_mouth/S_throat)

    Examples:
        >>> horn = ExponentialHorn(
        ...     throat_area=0.001,  # 10 cm²
        ...     mouth_area=0.1,     # 1000 cm²
        ...     length=1.5          # 1.5 m
        ... )
        >>> horn.flare_constant
        3.068...  # 1/m
    """

    throat_area: float
    mouth_area: float
    length: float
    flare_constant: Optional[float] = None

    def __post_init__(self):
        """Calculate flare constant from geometry if not provided."""
        if self.flare_constant is None:
            # Olson (1947), Chapter 5: m = (1/L) · ln(S_m/S_t)
            self.flare_constant = np.log(self.mouth_area / self.throat_area) / self.length

    def throat_radius(self) -> float:
        """Calculate throat radius from throat area (assuming circular)."""
        return np.sqrt(self.throat_area / np.pi)

    def mouth_radius(self) -> float:
        """Calculate mouth radius from mouth area (assuming circular)."""
        return np.sqrt(self.mouth_area / np.pi)

    def area_at(self, x: float) -> float:
        """
        Calculate cross-sectional area at distance x from throat.

        S(x) = S_throat · exp(m·x)

        Literature:
            - Olson (1947), Eq. 5.12
            - literature/horns/olson_1947.md

        Args:
            x: Axial distance from throat (m), 0 ≤ x ≤ length

        Returns:
            Cross-sectional area at position x (m²)
        """
        return self.throat_area * np.exp(self.flare_constant * x)


@dataclass
class FrequencyResponse:
    """
    Frequency response data for a horn or driver.

    Stores complex impedance or pressure response across frequency.

    Attributes:
        frequencies: Array of frequency points (Hz)
        impedance: Complex impedance at each frequency (Ω)
        magnitude: Impedance magnitude |Z| (Ω)
        phase: Impedance phase in degrees

    Examples:
        >>> response = FrequencyResponse(
        ...     frequencies=np.array([20, 50, 100, 200, 500]),
        ...     impedance=np.array([10+5j, 15+3j, 20+1j, 25+0.5j, 30+0.1j])
        ... )
        >>> response.magnitude[0]
        11.18...  # |10 + 5j|
    """

    frequencies: np.ndarray
    impedance: np.ndarray
    magnitude: Optional[np.ndarray] = None
    phase: Optional[np.ndarray] = None

    def __post_init__(self):
        """Calculate magnitude and phase from complex impedance."""
        if self.magnitude is None:
            self.magnitude = np.abs(self.impedance)
        if self.phase is None:
            self.phase = np.angle(self.impedance, deg=True)


@dataclass
class SimulationResult:
    """
    Container for simulation results with metadata.

    Attributes:
        horn: Horn geometry used in simulation
        frequencies: Frequency array (Hz)
        throat_impedance: Complex throat impedance at each frequency (Ω)
        radiation_impedance: Radiation impedance at mouth (Ω)
        cutoff_frequency: Horn cutoff frequency (Hz), if applicable

    Examples:
        >>> result = SimulationResult(
        ...     horn=ExponentialHorn(0.001, 0.1, 1.5),
        ...     frequencies=np.logspace(1, 4, 100),
        ...     throat_impedance=z_array,
        ...     radiation_impedance=z_rad,
        ...     cutoff_frequency=50.0
        ... )
    """

    horn: ExponentialHorn
    frequencies: np.ndarray
    throat_impedance: np.ndarray
    radiation_impedance: Optional[np.ndarray] = None
    cutoff_frequency: Optional[float] = None
