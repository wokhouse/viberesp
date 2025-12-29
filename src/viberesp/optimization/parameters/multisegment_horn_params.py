"""Multi-segment horn parameter space for optimization.

This module defines parameter ranges and typical values for optimizing
multi-segment exponential horn loudspeaker systems.

Multi-segment horns allow the optimizer to discover profiles beyond
standard exponential, tractrix, or hyperbolic shapes by varying the
flare rate along the horn length.

Literature:
- Olson (1947), Chapter 8 - Compound and stepped horns
- Kolbrek Part 1 - T-matrix chaining for multi-segment horns
- literature/horns/olson_1947.md
- literature/horns/kolbrek_horn_theory_tutorial.md
"""

import numpy as np
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.optimization.parameters.parameter_space import (
    ParameterRange,
    EnclosureParameterSpace,
)
from viberesp.simulation.constants import SPEED_OF_SOUND


def get_multisegment_horn_parameter_space(
    driver: ThieleSmallParameters,
    preset: str = "midrange_horn",
    num_segments: int = 2
) -> EnclosureParameterSpace:
    """
    Get parameter space for multi-segment horn optimization.

    For a 2-segment horn, optimizes 7 parameters:
    - throat_area: Horn throat area (driver coupling)
    - middle_area: Area at segment junction (segment 1 mouth = segment 2 throat)
    - mouth_area: Horn mouth area (radiation)
    - length1: Length of segment 1 (throat → middle)
    - length2: Length of segment 2 (middle → mouth)
    - V_tc: Throat chamber volume (compliance)
    - V_rc: Rear chamber volume (compliance)

    For a 3-segment horn, optimizes 9 parameters (add area2, length3).

    Fixed parameters (not optimized):
    - radiation_angle: 2π (half-space)

    The flare constants m1, m2 are calculated from geometry:
        m1 = ln(middle_area / throat_area) / length1
        m2 = ln(mouth_area / middle_area) / length2

    This allows the optimizer to discover optimal flare rate profiles
    without being constrained to standard horn types.

    Literature:
        - Olson (1947), Chapter 8 - Compound horns
        - Kolbrek Part 1 - Multi-segment horn theory
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Args:
        driver: ThieleSmallParameters for the driver
        preset: Design preset ("bass_horn", "midrange_horn", "fullrange_horn")
        num_segments: Number of horn segments (2 or 3)

    Returns:
        EnclosureParameterSpace: Parameter space definition

    Raises:
        ValueError: If preset or num_segments is not recognized

    Examples:
        >>> from viberesp.driver.test_drivers import get_tc2_compression_driver
        >>> driver = get_tc2_compression_driver()
        >>> param_space = get_multisegment_horn_parameter_space(
        ...     driver, preset="midrange_horn", num_segments=2
        ... )
        >>> param_space.get_parameter_names()
        ['throat_area', 'middle_area', 'mouth_area', 'length1', 'length2', 'V_rc']
    """
    if num_segments not in [2, 3]:
        raise ValueError(
            f"num_segments must be 2 or 3, got {num_segments}. "
            "Hornresp supports maximum 4 segments, but optimization "
            "with 2-3 segments provides sufficient flexibility."
        )

    # Driver parameters for scaling
    S_d = driver.S_d  # Diaphragm area [m²]
    V_as = driver.V_as  # Equivalent volume of suspension [m³]

    # Define preset-specific ranges
    # Literature: Olson (1947), Chapter 5 - Practical horn dimensions
    if preset == "bass_horn":
        # Bass horn: Large mouth, long length, low cutoff frequency
        # Target cutoff: 40-80 Hz
        throat_min = 0.1 * S_d
        throat_max = 0.3 * S_d
        middle_min = 0.05  # m²
        middle_max = 0.5  # m²
        mouth_min = 0.3  # m²
        mouth_max = 1.5  # m²
        length_min = 1.5  # m
        length_max = 3.0  # m
        # Throat chamber: Bass horns typically use direct coupling or small chamber
        V_tc_min = 0.0  # No throat chamber (direct coupling preferred for bass)
        V_tc_max = 0.00002  # 20 cm³ (small chamber, max 25 cm length for smallest throat)
        V_rc_min = 0.5 * V_as
        V_rc_max = 2.0 * V_as

    elif preset == "midrange_horn":
        # Midrange horn: Medium size, moderate cutoff frequency
        # Target cutoff: 200-500 Hz
        # Mouth size: Large enough for proper loading (Beranek 1954)
        # Literature: Mouth circumference ≥ wavelength at cutoff for flat response <3 dB
        # For Fc ≈ 350-450 Hz: need mouth_area ≥ 400-500 cm² (23-25 cm diameter)
        throat_min = 0.2 * S_d
        throat_max = 0.5 * S_d
        middle_min = 0.01  # m² (100 cm²)
        middle_max = 0.04  # m² (400 cm²)
        mouth_min = 0.04  # m² (400 cm², radius ~11.3 cm)
        mouth_max = 0.06  # m² (600 cm², radius ~13.8 cm)
        length_min = 0.15  # m (each segment minimum 15 cm)
        length_max = 0.6  # m (each segment maximum 60 cm, total up to 1.2 m)
        # Throat chamber: Practical limits for compression driver phase plugs
        # Length should be 2-8 cm for typical compression drivers
        # Set conservative bound: 0-15 cm³ (max 9.4 cm length for smallest throat)
        V_tc_min = 0.0  # No throat chamber (direct coupling)
        V_tc_max = 0.000015  # 15 cm³ (practical for compression driver phase plugs)
        V_rc_min = 0.0  # No rear chamber
        V_rc_max = 1.0 * V_as  # Optional rear chamber

    elif preset == "fullrange_horn":
        # Full-range horn: Compact, wider bandwidth
        # Target cutoff: 100-500 Hz
        throat_min = 0.15 * S_d
        throat_max = 0.4 * S_d
        middle_min = 0.01  # m²
        middle_max = 0.1  # m²
        mouth_min = 0.02  # m² (radius ~8 cm)
        mouth_max = 0.2  # m² (radius ~25 cm)
        length_min = 0.2  # m
        length_max = 0.8  # m
        # Throat chamber: Practical limits for fullrange drivers
        V_tc_min = 0.0
        V_tc_max = 0.00002  # 20 cm³ (practical for fullrange)
        V_rc_min = 0.0
        V_rc_max = 1.5 * V_as

    else:
        raise ValueError(
            f"Unknown preset: {preset}. "
            f"Choose from: 'bass_horn', 'midrange_horn', 'fullrange_horn'"
        )

    # Build parameter list based on num_segments
    parameters = [
        ParameterRange(
            name="throat_area",
            min_value=throat_min,
            max_value=throat_max,
            units="m²",
            description="Horn throat area (driver coupling)"
        ),
        ParameterRange(
            name="middle_area",
            min_value=middle_min,
            max_value=middle_max,
            units="m²",
            description="Area at segment junction (segment 1 mouth = segment 2 throat)"
        ),
        ParameterRange(
            name="mouth_area",
            min_value=mouth_min,
            max_value=mouth_max,
            units="m²",
            description="Horn mouth area (radiation)"
        ),
        ParameterRange(
            name="length1",
            min_value=length_min,
            max_value=length_max,
            units="m",
            description="Segment 1 length (throat → middle)"
        ),
        ParameterRange(
            name="length2",
            min_value=length_min,
            max_value=length_max,
            units="m",
            description="Segment 2 length (middle → mouth)"
        ),
        ParameterRange(
            name="V_tc",
            min_value=V_tc_min,
            max_value=V_tc_max,
            units="m³",
            description="Throat chamber volume (compliance)"
        ),
        ParameterRange(
            name="V_rc",
            min_value=V_rc_min,
            max_value=V_rc_max,
            units="m³",
            description="Rear chamber volume (compliance)"
        ),
    ]

    # Add third segment parameters if requested
    if num_segments == 3:
        parameters.insert(3, ParameterRange(
            name="area2",
            min_value=middle_min,
            max_value=max(middle_max, mouth_min),
            units="m²",
            description="Area at segment 2-3 junction"
        ))
        parameters.insert(-1, ParameterRange(
            name="length3",
            min_value=length_min,
            max_value=length_max,
            units="m",
            description="Segment 3 length (area2 → mouth)"
        ))

    # Define typical ranges for reference designs
    # These are useful for initial population seeding in optimization
    typical_ranges = {
        "bass_horn": {
            "throat_area": (0.15 * S_d, 0.25 * S_d),
            "middle_area": (0.2, 0.4),
            "mouth_area": (0.5, 1.0),
            "length1": (1.0, 1.5),
            "length2": (1.0, 1.5),
            "V_tc": (0.0, 0.2 * V_tc_max),
            "V_rc": (0.8 * V_as, 1.2 * V_as),
        },
        "midrange_horn": {
            # Typical: fast flare near throat, gradual near mouth
            "throat_area": (0.3 * S_d, 0.4 * S_d),
            "middle_area": (0.015, 0.025),
            "mouth_area": (0.045, 0.055),
            "length1": (0.18, 0.25),  # Short throat segment
            "length2": (0.35, 0.50),  # Longer mouth segment
            "V_tc": (0.0, 0.2 * V_tc_max),
            "V_rc": (0.0, 0.2 * V_as),
        },
        "fullrange_horn": {
            "throat_area": (0.2 * S_d, 0.3 * S_d),
            "middle_area": (0.03, 0.08),
            "mouth_area": (0.08, 0.15),
            "length1": (0.3, 0.5),
            "length2": (0.4, 0.7),
            "V_tc": (0.0, 0.2 * V_tc_max),
            "V_rc": (0.3 * V_as, 0.8 * V_as),
        },
    }

    # Add 3-segment typical ranges
    if num_segments == 3:
        typical_ranges["midrange_horn_3seg"] = {
            "throat_area": (0.3 * S_d, 0.4 * S_d),
            "middle_area": (0.010, 0.020),
            "area2": (0.025, 0.040),
            "mouth_area": (0.045, 0.055),
            "length1": (0.15, 0.25),
            "length2": (0.20, 0.30),
            "length3": (0.25, 0.40),
            "V_tc": (0.0, 0.2 * V_tc_max),
            "V_rc": (0.0, 0.2 * V_as),
        }

    # Define constraints to apply
    # Literature: Olson (1947) - Mouth size, flare rate, displacement limits
    constraints = [
        "segment_continuity",  # Ensure throat < middle < mouth (monotonic expansion)
        "mouth_size",  # Mouth ≥ λ/2 at minimum cutoff
        "flare_constant_limits",  # Each segment: 0.5 < m·L < 3.0
        "max_displacement",  # Diaphragm protection
    ]

    return EnclosureParameterSpace(
        enclosure_type="multisegment_horn",
        parameters=parameters,
        typical_ranges=typical_ranges,
        constraints=constraints,
    )


def decode_multisegment_design(
    design: np.ndarray,
    driver: ThieleSmallParameters,
    num_segments: int = 2
) -> dict:
    """
    Decode optimization array into multi-segment horn parameters.

    Converts the flat optimization array into a structured dictionary
    with horn geometry parameters for building a MultiSegmentHorn.

    Args:
        design: Optimization array [throat_area, middle_area, mouth_area,
                length1, length2, V_tc, V_rc] for 2-segment, or with additional
                [area2, length3] for 3-segment
        driver: ThieleSmallParameters for the driver
        num_segments: Number of segments (2 or 3)

    Returns:
        Dictionary with horn parameters:
        - throat_area, mouth_area: Overall horn dimensions
        - segments: List of (throat_area, mouth_area, length) tuples
        - V_rc: Rear chamber volume
        - flare_constants: List of m for each segment

    Examples:
        >>> design = np.array([0.000212, 0.010, 0.04084, 0.20, 0.394, 0.0])
        >>> params = decode_multisegment_design(design, driver, num_segments=2)
        >>> params['flare_constants']
        [19.27, 3.57]
    """
    if num_segments == 2:
        throat_area, middle_area, mouth_area, length1, length2, V_tc, V_rc = design

        # Build segment list
        segments = [
            (throat_area, middle_area, length1),  # Segment 1
            (middle_area, mouth_area, length2),     # Segment 2
        ]

        # Calculate flare constants
        m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
        m2 = np.log(mouth_area / middle_area) / length2 if length2 > 0 else 0
        flare_constants = [m1, m2]

    elif num_segments == 3:
        (throat_area, middle_area, area2, mouth_area,
         length1, length2, length3, V_tc, V_rc) = design

        # Build segment list
        segments = [
            (throat_area, middle_area, length1),  # Segment 1
            (middle_area, area2, length2),        # Segment 2
            (area2, mouth_area, length3),         # Segment 3
        ]

        # Calculate flare constants
        m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
        m2 = np.log(area2 / middle_area) / length2 if length2 > 0 else 0
        m3 = np.log(mouth_area / area2) / length3 if length3 > 0 else 0
        flare_constants = [m1, m2, m3]

    else:
        raise ValueError(f"num_segments must be 2 or 3, got {num_segments}")

    return {
        'throat_area': throat_area,
        'mouth_area': mouth_area,
        'segments': segments,
        'V_tc': V_tc,
        'V_rc': V_rc,
        'flare_constants': flare_constants,
        'total_length': sum(seg[2] for seg in segments),
    }


def calculate_multisegment_horn_cutoff(
    throat_area: float,
    middle_area: float,
    mouth_area: float,
    length1: float,
    length2: float,
    c: float = SPEED_OF_SOUND
) -> tuple:
    """
    Calculate cutoff frequencies for each segment.

    Each segment has its own cutoff based on its flare constant:
        f_c = c·m/(2π)

    The overall horn cutoff is the maximum of segment cutoffs
    (highest frequency = most restrictive).

    Literature:
        - Olson (1947), Eq. 5.18 - f_c = c·m/(2π)
        - literature/horns/olson_1947.md

    Args:
        throat_area: Horn throat area [m²]
        middle_area: Area at segment junction [m²]
        mouth_area: Horn mouth area [m²]
        length1: Segment 1 length [m]
        length2: Segment 2 length [m]
        c: Speed of sound [m/s], default 343 m/s

    Returns:
        Tuple of (fc1, fc2, fc_overall) in Hz

    Examples:
        >>> fc1, fc2, fc_overall = calculate_multisegment_horn_cutoff(
        ...     0.000212, 0.010, 0.04084, 0.20, 0.394
        ... )
        >>> print(f"Segment 1: {fc1:.0f} Hz, Segment 2: {fc2:.0f} Hz")
        >>> print(f"Overall: {fc_overall:.0f} Hz")
    """
    # Segment 1 flare constant and cutoff
    m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
    fc1 = (c * m1) / (2 * np.pi) if m1 > 0 else float('inf')

    # Segment 2 flare constant and cutoff
    m2 = np.log(mouth_area / middle_area) / length2 if length2 > 0 else 0
    fc2 = (c * m2) / (2 * np.pi) if m2 > 0 else float('inf')

    # Overall cutoff is the maximum (most restrictive segment)
    fc_overall = max(fc1, fc2)

    return fc1, fc2, fc_overall


def calculate_multisegment_horn_volume(
    throat_area: float,
    middle_area: float,
    mouth_area: float,
    length1: float,
    length2: float
) -> float:
    """
    Calculate total volume of 2-segment exponential horn.

    For each segment: V_segment = (S₂ - S₁) / m

    Literature:
        - Olson (1947), Chapter 5 - Horn geometry

    Args:
        throat_area: Horn throat area [m²]
        middle_area: Area at segment junction [m²]
        mouth_area: Horn mouth area [m²]
        length1: Segment 1 length [m]
        length2: Segment 2 length [m]

    Returns:
        Total horn volume [m³]

    Examples:
        >>> V = calculate_multisegment_horn_volume(
        ...     0.000212, 0.010, 0.04084, 0.20, 0.394
        ... )
        >>> print(f"{V*1000:.1f} liters")
    """
    # Segment 1 volume
    if length1 > 0 and middle_area > throat_area:
        m1 = np.log(middle_area / throat_area) / length1
        v1 = (middle_area - throat_area) / m1
    else:
        v1 = (throat_area + middle_area) / 2 * length1

    # Segment 2 volume
    if length2 > 0 and mouth_area > middle_area:
        m2 = np.log(mouth_area / middle_area) / length2
        v2 = (mouth_area - middle_area) / m2
    else:
        v2 = (middle_area + mouth_area) / 2 * length2

    return v1 + v2
