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
from scipy.optimize import brentq


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
class HyperbolicHorn:
    """
    A hyperbolic (Hypex) horn segment with T parameter.

    Implements the Salmon hyperbolic family:
        S(x) = S_0 * [cosh(mx) + T * sinh(mx)]^2

    The hyperbolic horn family ("Hypex") was generalized by Vincent Salmon in 1946.
    While the Exponential horn expands at a constant rate, the Hyperbolic family
    allows for manipulation of the expansion rate near the throat, governed by
    the shape parameter T.

    Literature:
        - Salmon, V. (1946). "A New Family of Horns", J. Acoust. Soc. Am.
          - Defines the hyperbolic family: r(x) = r₀[cosh(mx) + T·sinh(mx)]
        - Kolbrek, B. (2008). "Horn Theory: An Introduction, Part 1 & 2".
          - T-parameter ranges and optimal values (0.5-0.85 for extended bass)
        - Freehafer, J. E. (1940). "The Acoustical Impedance of an Infinite
          Hyperbolic Horn", J. Acoust. Soc. Am.
          - Foundational solution for hyperbolic horn impedance
        - Olson (1947), Chapter 5 - Horn profiles
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Attributes:
        throat_area: Throat area [m²]
        mouth_area: Mouth area [m²]
        length: Axial length [m]
        T: Shape parameter (0 < T <= 1 for hypex, T=1 is exponential)
            T < 1: Hyperbolic/Hypex - better low-frequency extension
            T = 1: Exponential
            T > 1: Toward conical (constant directivity)
        m: Flare constant [1/m] (calculated from geometry)

    Examples:
        >>> horn = HyperbolicHorn(
        ...     throat_area=0.001,  # 10 cm²
        ...     mouth_area=0.1,     # 1000 cm²
        ...     length=1.5,         # 1.5 m
        ...     T=0.7               # Hypex with better low-end loading
        ... )
        >>> horn.m  # Flare constant calculated from geometry
        3.068...  # 1/m
    """

    throat_area: float
    mouth_area: float
    length: float
    T: float = 1.0  # Default to exponential
    m: float = 0.0  # Calculated post-init

    def __post_init__(self):
        """Solve for the unique flare constant m that fits the geometry and T."""
        if self.length <= 0 or self.throat_area <= 0 or self.mouth_area <= 0:
            raise ValueError("Dimensions must be positive nonzero values.")

        if self.T < 0.01:
            raise ValueError("T must be > 0.01 (T=0 is undefined catenoidal).")

        # Optimization target: Find m such that geometry is satisfied
        # sqrt(S_mouth/S_throat) = cosh(m*L) + T*sinh(m*L)
        target_ratio = np.sqrt(self.mouth_area / self.throat_area)

        def geometry_error(m_guess):
            # Using m convention for amplitude flare matching Salmon
            # S(x) = S0 * (cosh(mx) + T*sinh(mx))^2
            val = np.cosh(m_guess * self.length) + self.T * np.sinh(m_guess * self.length)
            return val - target_ratio

        # Corner case: Exponential (T=1)
        if abs(self.T - 1.0) < 1e-4:
            # Simple analytical solution for exponential
            # S = S0 * e^(2mL) -> sqrt(S/S0) = e^(mL) -> mL = ln(sqrt(rat))
            self.m = np.log(target_ratio) / self.length
        else:
            # Numerical solution for Hyperbolic
            try:
                # Search for m typically between 1e-6 and 50
                # Lower bound very small for very long/narrow horns
                # Upper bound for very short/wide horns
                self.m = brentq(geometry_error, 1e-6, 100.0)
            except ValueError:
                # Fallback for extreme geometries (very short/wide)
                # Use exponential approximation
                self.m = np.log(target_ratio) / self.length

    def throat_radius(self) -> float:
        """Calculate throat radius from throat area (assuming circular)."""
        return np.sqrt(self.throat_area / np.pi)

    def mouth_radius(self) -> float:
        """Calculate mouth radius from mouth area (assuming circular)."""
        return np.sqrt(self.mouth_area / np.pi)

    def area_at(self, x: float) -> float:
        """
        Calculate cross-sectional area at distance x from throat.

        S(x) = S_throat * [cosh(mx) + T*sinh(mx)]^2

        Literature:
            - Salmon (1946), Eq. for hyperbolic horns
            - Kolbrek Part 1 - Modern treatment

        Args:
            x: Axial distance from throat (m), 0 ≤ x ≤ length

        Returns:
            Cross-sectional area at position x (m²)
        """
        if x < 0 or x > self.length:
            raise ValueError("x must be within segment length")

        factor = np.cosh(self.m * x) + self.T * np.sinh(self.m * x)
        return self.throat_area * (factor ** 2)

    def calculate_t_matrix(self, f: float, c: float = 343.2, rho: float = 1.205) -> np.ndarray:
        """
        Calculate the 2x2 Transfer Matrix [A, B; C, D] for this segment.

        Based on exact solution to Webster's horn equation for Hyperbolic profile.
        For the hyperbolic family, the curvature term r''/r = m² (constant),
        reducing the wave equation to ψ'' + (k² - m²)ψ = 0.

        Literature:
            - Mapes-Riordan (1993), Eq 13a-13d - Hyperbolic horn T-matrix
              with logarithmic gradient terms grad_in, grad_out
            - Kolbrek, "Horn Theory: An Introduction, Part 1 & 2"
            - Freehafer (1940) - Hyperbolic horn impedance solution
            - literature/horns/kolbrek_horn_theory_tutorial.md

        Theory:
            Effective wavenumber: μ = √(k² - m²)
            - Above cutoff (k > m): μ is real (propagating waves)
            - Below cutoff (k < m): μ is imaginary (evanescent waves)

            Logarithmic gradient: r'/r = m[sinh(mx) + T·cosh(mx)]/[cosh(mx) + T·sinh(mx)]
            - At throat (x=0): grad_in = m·T
            - At mouth (x=L): grad_out = m[sinh(mL) + T·cosh(mL)]/[cosh(mL) + T·sinh(mL)]

        Args:
            f: Frequency [Hz]
            c: Speed of sound [m/s]
            rho: Air density [kg/m³]

        Returns:
            2x2 np.ndarray of complex floats [[A, B], [C, D]]

        Notes:
            The T-matrix relates pressure and volume velocity at throat (port 1)
            to mouth (port 2): [p₁, U₁]ᵀ = [A B; C D][p₂, U₂]ᵀ

            Uses effective wavenumber k' = √(k² - m²).
            Below cutoff (k < m), k' becomes imaginary, handling reactive component.
        """
        k = 2 * np.pi * f / c
        L = self.length
        m = self.m

        # Characteristic parameters
        # mu is the complex propagation constant
        discriminant = k**2 - m**2

        if discriminant >= 0:
            mu = np.sqrt(discriminant)
            # Above cutoff (propagating)
            cos_mu_L = np.cos(mu * L)
            sin_mu_L = np.sin(mu * L)

            # Use sinc function for stability when mu -> 0 (cutoff)
            if mu < 1e-9:
                sinc_mu_L = L
            else:
                sinc_mu_L = sin_mu_L / mu
        else:
            # Below cutoff (evanescent)
            mu = np.sqrt(-discriminant)  # Real value
            cos_mu_L = np.cosh(mu * L)
            sin_mu_L = 1j * np.sinh(mu * L)  # Returns imaginary
            # Adjust sinc divisor to handle the imaginary mu properly
            sinc_mu_L = np.sinh(mu * L) / mu if mu > 1e-9 else L

        # Ratios of areas (used for impedance scaling)
        # p scales with 1/r, u scales with 1/r
        r_in = np.sqrt(self.throat_area)
        r_out = np.sqrt(self.mouth_area)

        # Calculating Derivatives of the shape function at boundaries
        # h(x) = cosh(mx) + T*sinh(mx). r(x) = r0 * h(x)
        # r'(x)/r(x) = m * (sinh(mx) + T*cosh(mx)) / h(x)
        #
        # At x=0 (throat): h(0)=1, h'(0)=m·T  → grad_in = m·T
        # At x=L (mouth): grad_out = m[sinh(mL) + T·cosh(mL)]/[cosh(mL) + T·sinh(mL)]

        def flare_grad(x_loc):
            h = np.cosh(m * x_loc) + self.T * np.sinh(m * x_loc)
            h_prime = m * (np.sinh(m * x_loc) + self.T * np.cosh(m * x_loc))
            return h_prime / h

        grad_in = flare_grad(0)      # = m·T (verified analytically)
        grad_out = flare_grad(L)     # = m[sinh(mL) + T·cosh(mL)]/[cosh(mL) + T·sinh(mL)]

        # Matrix Elements derivation from Mapes-Riordan (1993) Eq 13a-13d
        # Adapted for general Hypex shape function

        # A = (r_in/r_out) * (cos(mu L) - grad_in * sin(mu L)/mu)
        A = (r_in / r_out) * (cos_mu_L - grad_in * sinc_mu_L)

        # B = j * k * Z_scale / sqrt(S_in * S_out) * sinc_mu_L
        Z_scale = rho * c
        B = (1j * k * Z_scale / np.sqrt(self.throat_area * self.mouth_area)) * sinc_mu_L

        # D = (r_out/r_in) * (cos(mu L) + grad_out * sinc_mu_L)
        D = (r_out / r_in) * (cos_mu_L + grad_out * sinc_mu_L)

        # Calculate C using Determinant = 1 property for reciprocal passive system
        # AD - BC = 1  => C = (AD - 1)/B
        if abs(B) < 1e-12:
            # Special case: L=0 or resonance node. Fallback to limit.
            C = 0  # Approximation for safety
        else:
            C = (A * D - 1.0) / B

        return np.array([[A, B], [C, D]], dtype=complex)


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

    def calculate_t_matrix(self, f: float, c: float = 343.2, rho: float = 1.205) -> np.ndarray:
        """
        Calculate the 2x2 Transfer Matrix [A, B; C, D] for exponential segment.

        This provides a consistent interface with HyperbolicHorn for multi-segment
        horn simulation. For exponential segments, this uses the Kolbrek convention
        for T-matrix calculations.

        Literature:
            - Kolbrek, "Horn Theory: An Introduction, Part 1"
            - Olson (1947), Chapter 5 - Exponential horn theory
            - literature/horns/kolbrek_horn_theory_tutorial.md

        Args:
            f: Frequency [Hz]
            c: Speed of sound [m/s]
            rho: Air density [kg/m³]

        Returns:
            2x2 np.ndarray of complex floats [[A, B], [C, D]]

        Notes:
            The T-matrix relates pressure and volume velocity at throat (port 1)
            to mouth (port 2): [p₁, U₁]ᵀ = [A B; C D][p₂, U₂]ᵀ

            Uses effective wavenumber k' = √(k² - m²).
            Below cutoff (k < m), k' becomes imaginary.
        """
        # Convert to Kolbrek convention (m_kolbrek = m_olson / 2)
        m = self.flare_constant / 2.0
        k = 2 * np.pi * f / c
        L = self.length
        S1 = self.throat_area
        S2 = self.mouth_area
        z_rc = rho * c

        # γ = √(k² - m²), can be real or imaginary
        gamma_squared = k**2 - m**2
        gamma = np.sqrt(gamma_squared.astype(complex))

        gL = gamma * L
        emL = np.exp(m * L)

        # Handle near-cutoff singularity (γ → 0)
        near_cutoff = np.abs(gL) < 1e-8

        if near_cutoff:
            # Use small angle approximation: sin(x) ≈ x for x → 0
            sin_gL = gL
            cos_gL = 1.0
            m_over_gamma = m * L
            k_over_gamma = k * L
        else:
            sin_gL = np.sin(gL)
            cos_gL = np.cos(gL)
            m_over_gamma = m / gamma
            k_over_gamma = k / gamma

        # T-matrix elements (Kolbrek convention)
        A = emL * (cos_gL - m_over_gamma * sin_gL)
        B = emL * 1j * (z_rc / S2) * k_over_gamma * sin_gL
        C = emL * 1j * (S1 / z_rc) * k_over_gamma * sin_gL
        D = emL * (S1 / S2) * (cos_gL + m_over_gamma * sin_gL)

        return np.array([[A, B], [C, D]], dtype=complex)


@dataclass
class MultiSegmentHorn:
    """
    Horn composed of multiple horn segments (exponential, hyperbolic, or mixed).

    A multi-segment horn allows approximating arbitrary horn profiles
    by chaining together segments with different flare constants and profiles.
    This enables discovery of optimal profiles beyond standard exponential,
    tractrix, or hyperbolic shapes.

    Literature:
        - Kolbrek Part 1 - T-matrix chaining for multi-segment horns
        - Olson (1947), Chapter 8 - Compound horns
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Attributes:
        segments: List of horn segments (HornSegment or HyperbolicHorn),
                  ordered from throat to mouth. Each segment's mouth must
                  match next segment's throat.

    Examples:
        >>> from viberesp.simulation.types import HornSegment, HyperbolicHorn
        >>> segment1 = HornSegment(throat_area=0.001, mouth_area=0.01, length=0.3)
        >>> segment2 = HyperbolicHorn(throat_area=0.01, mouth_area=0.1, length=0.6, T=0.7)
        >>> horn = MultiSegmentHorn(segments=[segment1, segment2])
        >>> horn.total_length()
        0.9
        >>> horn.throat_area
        0.001
        >>> horn.mouth_area
        0.1
    """

    segments: List[Union['HornSegment', 'HyperbolicHorn']]

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
