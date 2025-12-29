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
from typing import List, Optional, Union

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
class HornSegment:
    """
    Single segment of a multi-segment horn with exponential flare.

    Each segment has constant flare constant m, defining an exponential
    expansion from throat to mouth of that segment.

    Literature:
        - Olson (1947), Eq. 5.12 - Exponential horn profile
        - Kolbrek Part 1 - Multi-segment horns via T-matrix chaining
        - literature/horns/olson_1947.md

    Attributes:
        throat_area: Throat cross-sectional area of this segment (m²)
        mouth_area: Mouth cross-sectional area of this segment (m²)
        length: Axial length of this segment (m)
        flare_constant: Flare constant m (1/m), calculated from geometry
                      if not provided. m = (1/L) · ln(S_mouth/S_throat)

    Examples:
        >>> segment = HornSegment(
        ...     throat_area=0.001,  # 10 cm²
        ...     mouth_area=0.01,    # 100 cm²
        ...     length=0.5          # 50 cm
        ... )
        >>> segment.flare_constant
        4.605...  # 1/m
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
        Calculate cross-sectional area at distance x from segment throat.

        S(x) = S_throat · exp(m·x)

        Args:
            x: Axial distance from segment throat (m), 0 ≤ x ≤ length

        Returns:
            Cross-sectional area at position x (m²)
        """
        return self.throat_area * np.exp(self.flare_constant * x)


@dataclass
class MultiSegmentHorn:
    """
    Horn composed of multiple exponential segments.

    A multi-segment horn allows approximating arbitrary horn profiles
    by chaining together exponential segments with different flare constants.
    This enables discovery of optimal profiles beyond standard exponential,
    tractrix, or hyperbolic shapes.

    Literature:
        - Kolbrek Part 1 - T-matrix chaining for multi-segment horns
        - Olson (1947), Chapter 8 - Compound horns
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Attributes:
        segments: List of horn segments, ordered from throat to mouth.
                  Each segment's mouth must match next segment's throat.

    Examples:
        >>> segment1 = HornSegment(throat_area=0.001, mouth_area=0.01, length=0.3)
        >>> segment2 = HornSegment(throat_area=0.01, mouth_area=0.1, length=0.6)
        >>> horn = MultiSegmentHorn(segments=[segment1, segment2])
        >>> horn.total_length()
        0.9
        >>> horn.throat_area
        0.001
        >>> horn.mouth_area
        0.1
    """

    segments: List[HornSegment]

    def __post_init__(self):
        """Validate segment continuity."""
        if len(self.segments) < 1:
            raise ValueError("MultiSegmentHorn must have at least one segment")

        # Check that segments are continuous (mouth area matches next throat)
        for i in range(len(self.segments) - 1):
            if not np.isclose(self.segments[i].mouth_area, self.segments[i + 1].throat_area):
                raise ValueError(
                    f"Segment {i} mouth area ({self.segments[i].mouth_area}) "
                    f"must match segment {i+1} throat area ({self.segments[i+1].throat_area})"
                )

    @property
    def throat_area(self) -> float:
        """Overall horn throat area (m²)."""
        return self.segments[0].throat_area

    @property
    def mouth_area(self) -> float:
        """Overall horn mouth area (m²)."""
        return self.segments[-1].mouth_area

    @property
    def num_segments(self) -> int:
        """Number of segments in the horn."""
        return len(self.segments)

    def total_length(self) -> float:
        """Calculate total horn length (sum of all segments)."""
        return sum(seg.length for seg in self.segments)

    def throat_radius(self) -> float:
        """Calculate overall horn throat radius (assuming circular)."""
        return np.sqrt(self.throat_area / np.pi)

    def mouth_radius(self) -> float:
        """Calculate overall horn mouth radius (assuming circular)."""
        return np.sqrt(self.mouth_area / np.pi)

    def area_at(self, x: float) -> float:
        """
        Calculate cross-sectional area at distance x from overall horn throat.

        Finds the appropriate segment and calculates area within that segment.

        Args:
            x: Axial distance from horn throat (m), 0 ≤ x ≤ total_length()

        Returns:
            Cross-sectional area at position x (m²)
        """
        if x < 0 or x > self.total_length():
            raise ValueError(f"x={x} is outside horn length [0, {self.total_length()}]")

        # Find which segment contains position x
        cumulative_length = 0.0
        for segment in self.segments:
            if x <= cumulative_length + segment.length:
                # x is within this segment
                x_local = x - cumulative_length
                return segment.area_at(x_local)
            cumulative_length += segment.length

        # Shouldn't reach here if x is within bounds
        return self.mouth_area

    def segment_boundaries(self) -> List[float]:
        """
        Get axial positions of segment boundaries.

        Returns:
            List of positions [0, L1, L1+L2, ..., total_length]
        """
        boundaries = [0.0]
        cumulative_length = 0.0
        for segment in self.segments:
            cumulative_length += segment.length
            boundaries.append(cumulative_length)
        return boundaries


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
        horn: Horn geometry used in simulation (ExponentialHorn or MultiSegmentHorn)
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

    horn: Union[ExponentialHorn, MultiSegmentHorn]
    frequencies: np.ndarray
    throat_impedance: np.ndarray
    radiation_impedance: Optional[np.ndarray] = None
    cutoff_frequency: Optional[float] = None
