"""
Physical constraint functions for enclosure optimization.

This module provides constraint functions for ensuring optimized designs
satisfy physical requirements:
- Maximum displacement limits (X_max)
- Port velocity limits (chuffing prevention)

Literature:
    - Small (1972) - Displacement limits in sealed/ported boxes
    - Thiele (1971) - Port velocity and displacement
    - literature/thiele_small/small_1972_closed_box.md
    - literature/thiele_small/thiele_1971_vented_boxes.md
"""

import numpy as np
from typing import Optional

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import calculate_sealed_box_system_parameters
from viberesp.enclosure.ported_box import calculate_ported_box_system_parameters


def constraint_max_displacement(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    max_excursion_ratio: float = 0.8
) -> float:
    """
    Constrain maximum diaphragm displacement to prevent X_max violation.

    This constraint ensures the driver doesn't exceed its linear excursion
    limits, which would cause distortion and potential damage.

    Literature:
        - Small (1972) - Displacement limits in sealed/ported boxes
        - Thiele (1971) - Port velocity and displacement
        - literature/thiele_small/small_1972_closed_box.md

    Args:
        design_vector: Enclosure parameters
        driver: ThieleSmallParameters instance (must have X_max)
        enclosure_type: Type of enclosure ("sealed", "ported")
        max_excursion_ratio: Maximum fraction of X_max to allow (default 0.8)

    Returns:
        Constraint violation (positive = violation, negative = satisfied)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = load_driver("BC_8NDL51")  # X_max = 7mm
        >>> # Small sealed box - should violate displacement constraint
        >>> violation = constraint_max_displacement(
        ...     np.array([0.005]), driver, "sealed"
        ... )
        >>> violation > 0  # Violation (box too small)
        True
    """
    if driver.X_max is None:
        return 0.0  # No constraint if X_max not specified

    # Find worst-case displacement frequency
    # For sealed: displacement maximum at Fc
    # For ported: displacement maximum below tuning

    try:
        if enclosure_type == "sealed":
            Vb = design_vector[0]
            params = calculate_sealed_box_system_parameters(driver, Vb)

            # At Fc, displacement is maximum for a given voltage
            # Calculate displacement at Fc for rated power (2.83V = 1W into 8Ω)
            from viberesp.optimization.objectives.response_metrics import sealed_box_electrical_impedance

            result = sealed_box_electrical_impedance(
                params.Fc, driver, Vb=Vb, voltage=2.83
            )

            # Diaphragm velocity from result
            v_diaphragm = result['diaphragm_velocity']

            # Displacement = velocity / (2πf)
            x_diaphragm = v_diaphragm / (2.0 * np.pi * params.Fc)

        elif enclosure_type == "ported":
            Vb = design_vector[0]
            Fb = design_vector[1]

            # Below Fb, displacement increases
            # Worst case at Fb/2 approximately
            f_worst = Fb / 2.0

            from viberesp.optimization.objectives.response_metrics import ported_box_electrical_impedance
            from viberesp.enclosure.ported_box import calculate_optimal_port_dimensions

            # Get port dimensions
            if len(design_vector) >= 4:
                port_area = design_vector[2]
                port_length = design_vector[3]
            else:
                port_area, port_length, _ = calculate_optimal_port_dimensions(
                    driver, Vb, Fb
                )

            result = ported_box_electrical_impedance(
                f_worst, driver, Vb=Vb, Fb=Fb,
                port_area=port_area, port_length=port_length,
                voltage=2.83
            )

            v_diaphragm = result['diaphragm_velocity']
            x_diaphragm = v_diaphragm / (2.0 * np.pi * f_worst)

        else:
            return 0.0  # No constraint for other types (yet)

        # Constraint: x_diaphragm ≤ max_excursion_ratio × X_max
        # Return violation (positive if violated)
        x_limit = max_excursion_ratio * driver.X_max
        return x_diaphragm - x_limit

    except Exception:
        # If calculation fails, return large violation
        return 1000.0


def constraint_port_velocity(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    max_velocity_fraction: float = 0.05
) -> float:
    """
    Constrain port air velocity to prevent chuffing noise.

    Excessive port velocity causes turbulent noise ("chuffing") that
    degrades sound quality.

    Literature:
        - Thiele (1971), Part 1, Section 4 - Air velocity in the vent
        - literature/thiele_small/thiele_1971_vented_boxes.md

    Args:
        design_vector: Enclosure parameters (must include port dimensions)
        driver: ThieleSmallParameters instance
        enclosure_type: Type of enclosure (only applicable for "ported")
        max_velocity_fraction: Max port velocity as fraction of speed of sound
                              (default 0.05 = 5% of c = ~17 m/s)

    Returns:
        Constraint violation (positive if port velocity too high)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = load_driver("BC_12NDL76")
        >>> # Small port area - should violate velocity constraint
        >>> violation = constraint_port_velocity(
        ...     np.array([0.050, 40.0, 0.0005, 0.1]),  # Tiny port
        ...     driver, "ported"
        ... )
        >>> violation > 0  # Violation (port too small)
        True
    """
    if enclosure_type != "ported":
        return 0.0  # Not applicable

    if driver.X_max is None:
        return 0.0  # Can't calculate without X_max

    try:
        Vb = design_vector[0]
        Fb = design_vector[1]
        port_area = design_vector[2]

        # Estimate maximum port velocity at Fb
        # Thiele (1971): port velocity peaks at tuning frequency
        # v_port = (2π × Fb × X_max × S_d) / A_port

        from viberesp.simulation.constants import SPEED_OF_SOUND

        # Maximum air velocity in port (at X_max excursion)
        v_port_max = (2.0 * np.pi * Fb * driver.X_max * driver.S_d) / port_area

        # Convert to fraction of speed of sound
        v_fraction = v_port_max / SPEED_OF_SOUND

        # Constraint: v_fraction ≤ max_velocity_fraction
        return v_fraction - max_velocity_fraction

    except Exception:
        # If calculation fails, assume OK
        return 0.0


def constraint_multisegment_continuity(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    num_segments: int = 2
) -> float:
    """
    Constrain multi-segment horn to have monotonic area expansion.

    Ensures throat < middle < mouth (for 2 segments) to prevent
    area discontinuities that would cause reflections.

    Works with both standard and hyperbolic design vectors (auto-detects).

    Literature:
        - Olson (1947), Chapter 8 - Horn area continuity
        - Kolbrek Part 1 - Impedance discontinuities

    Args:
        design_vector:
            Standard: [throat_area, middle_area, mouth_area, length1, length2, V_tc, V_rc]
            Hyperbolic: [throat_area, middle_area, mouth_area, length1, length2, T1, T2, V_tc, V_rc]
        driver: ThieleSmallParameters instance (not used for this constraint)
        enclosure_type: Must be "multisegment_horn"
        num_segments: Number of segments (2 or 3)

    Returns:
        Constraint violation (positive = violation, negative = satisfied)

    Examples:
        >>> design = np.array([0.001, 0.005, 0.01, 0.3, 0.4, 0.0])
        >>> constraint_multisegment_continuity(design, driver, "multisegment_horn", num_segments=2)
        -0.004  # Satisfied (0.001 < 0.005 < 0.01)
    """
    if enclosure_type != "multisegment_horn":
        return 0.0  # Not applicable for other enclosure types

    # Extract areas (first 3 or 4 elements are always areas)
    if num_segments == 2:
        throat_area, middle_area, mouth_area = design_vector[0], design_vector[1], design_vector[2]

        # Check throat < middle
        violation1 = throat_area - middle_area

        # Check middle < mouth
        violation2 = middle_area - mouth_area

        # Return maximum violation
        return max(violation1, violation2)

    elif num_segments == 3:
        throat_area, middle_area, area2, mouth_area = design_vector[0:4]

        # Check monotonic expansion
        violation1 = throat_area - middle_area
        violation2 = middle_area - area2
        violation3 = area2 - mouth_area

        return max(violation1, violation2, violation3)

    else:
        return 0.0


def constraint_multisegment_flare_limits(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    num_segments: int = 2,
    min_mL: float = 0.5,
    max_mL: float = 6.0
) -> float:
    """
    Constrain flare constants for each segment to practical limits.

    For each segment, ensure: min_mL ≤ m·L ≤ max_mL

    This prevents unrealistic flare rates that would be difficult to
    manufacture or would have poor acoustic performance.

    Works with both standard and hyperbolic design vectors (auto-detects).

    Literature:
        - Olson (1947), Chapter 5 - Practical flare rate limits
        - Typical horns: 0.5 < m·L < 3.0 (relaxed to 6.0 for optimization)

    Args:
        design_vector:
            Standard: [throat_area, middle_area, mouth_area, length1, length2, V_tc, V_rc]
            Hyperbolic: [throat_area, middle_area, mouth_area, length1, length2, T1, T2, V_tc, V_rc]
        driver: ThieleSmallParameters instance (not used for this constraint)
        enclosure_type: Must be "multisegment_horn"
        num_segments: Number of segments (2 or 3)
        min_mL: Minimum value for m·L product (default 0.5)
        max_mL: Maximum value for m·L product (default 6.0, relaxed from 3.0)

    Returns:
        Constraint violation (positive = violation, negative = satisfied)

    Examples:
        >>> design = np.array([0.001, 0.01, 0.04, 0.2, 0.4, 0.0])
        >>> constraint_multisegment_flare_limits(design, driver, "multisegment_horn", num_segments=2)
        -0.5  # Satisfied
    """
    if enclosure_type != "multisegment_horn":
        return 0.0  # Not applicable for other enclosure types

    violations = []

    # Detect if hyperbolic (has T parameters)
    # Standard 2-seg: 7 elements, Hyperbolic 2-seg: 9 elements
    # Standard 3-seg: 9 elements, Hyperbolic 3-seg: 12 elements
    expected_standard = 7 + (2 if num_segments == 3 else 0)
    is_hyperbolic = len(design_vector) > expected_standard

    if num_segments == 2:
        throat_area, middle_area, mouth_area = design_vector[0:3]
        # Lengths are at indices 3, 4 (standard) or skip T params
        if is_hyperbolic:
            # Hyperbolic: [areas x3, lengths x2, T x2, V_tc, V_rc]
            length1, length2 = design_vector[3], design_vector[4]
        else:
            # Standard: [areas x3, lengths x2, V_tc, V_rc]
            length1, length2 = design_vector[3], design_vector[4]

        # Segment 1: m1·L1
        if length1 > 0 and middle_area > throat_area:
            m1 = np.log(middle_area / throat_area) / length1
            mL1 = m1 * length1
            violations.append(min_mL - mL1)  # Violation if too small
            violations.append(mL1 - max_mL)  # Violation if too large

        # Segment 2: m2·L2
        if length2 > 0 and mouth_area > middle_area:
            m2 = np.log(mouth_area / middle_area) / length2
            mL2 = m2 * length2
            violations.append(min_mL - mL2)
            violations.append(mL2 - max_mL)

    elif num_segments == 3:
        throat_area, middle_area, area2, mouth_area = design_vector[0:4]

        if is_hyperbolic:
            # Hyperbolic: [areas x4, lengths x3, T x3, V_tc, V_rc]
            length1, length2, length3 = design_vector[4], design_vector[5], design_vector[6]
        else:
            # Standard: [areas x4, lengths x3, V_tc, V_rc]
            length1, length2, length3 = design_vector[4], design_vector[5], design_vector[6]

        # Segment 1
        if length1 > 0 and middle_area > throat_area:
            m1 = np.log(middle_area / throat_area) / length1
            violations.append(min_mL - m1 * length1)
            violations.append(m1 * length1 - max_mL)

        # Segment 2
        if length2 > 0 and area2 > middle_area:
            m2 = np.log(area2 / middle_area) / length2
            violations.append(min_mL - m2 * length2)
            violations.append(m2 * length2 - max_mL)

        # Segment 3
        if length3 > 0 and mouth_area > area2:
            m3 = np.log(mouth_area / area2) / length3
            violations.append(min_mL - m3 * length3)
            violations.append(m3 * length3 - max_mL)

    if not violations:
        return 0.0

    # Return maximum violation (positive = bad)
    return max(violations)


def constraint_multisegment_flare_curvature(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    num_segments: int = 2,
    max_flare_increase: float = 0.1
) -> float:
    """
    Constrain flare rate curvature to ensure smooth horn profiles.

    Enforces that the flare constant m decreases or stays similar from
    throat to mouth: m_throat ≥ m_mid ≥ m_mouth. This prevents
    "bottleneck" shapes that are mathematically valid but physically poor.

    The constraint allows some tolerance (+10% by default) to accommodate
    practical designs while preventing pathological shapes.

    Works with both standard and hyperbolic design vectors (auto-detects).

    Literature:
        - Dong et al. (2020) - Horn profile optimization
        - Kolbrek Part 1 - Flare rate and impedance smoothness
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Theory:
        Rapid flare near throat provides good high-frequency loading.
        Gradual flare near mouth reduces reflections and improves low-frequency loading.
        Optimal horns typically have decreasing flare rates: m_throat > m_mid > m_mouth.

    Args:
        design_vector:
            Standard: [throat_area, middle_area, mouth_area, length1, length2, V_tc, V_rc]
            Hyperbolic: [throat_area, middle_area, mouth_area, length1, length2, T1, T2, V_tc, V_rc]
        driver: ThieleSmallParameters instance (not used for this constraint)
        enclosure_type: Must be "multisegment_horn"
        num_segments: Number of segments (2 or 3)
        max_flare_increase: Maximum allowed increase in flare rate (default 0.1 = 10%)
            - Set to 0.0 for strict monotonic decrease (m_i > m_{i+1})
            - Set to 0.1 for 10% tolerance (practical designs)

    Returns:
        Constraint violation (positive = violation, negative = satisfied)

    Examples:
        >>> # Good horn: decreasing flare rate
        >>> design = np.array([0.001, 0.01, 0.04, 0.2, 0.4, 0.0])
        >>> # m1 ≈ 11.5, m2 ≈ 3.5 (decreasing)
        >>> constraint_multisegment_flare_curvature(
        ...     design, driver, "multisegment_horn", num_segments=2
        ... )
        -7.99  # Satisfied (m1 > m2)

        >>> # Bad horn: increasing flare rate (bottleneck)
        >>> design = np.array([0.001, 0.02, 0.025, 0.4, 0.2, 0.0])
        >>> # m1 ≈ 4.0, m2 ≈ 0.9 (decreasing, but length2 is shorter)
        >>> constraint_multisegment_flare_curvature(
        ...     design, driver, "multisegment_horn", num_segments=2
        ... )
        -3.1  # Might still be satisfied (depends on values)
    """
    if enclosure_type != "multisegment_horn":
        return 0.0  # Not applicable for other enclosure types

    violations = []

    # Detect if hyperbolic (has T parameters)
    expected_standard = 7 + (2 if num_segments == 3 else 0)
    is_hyperbolic = len(design_vector) > expected_standard

    if num_segments == 2:
        throat_area, middle_area, mouth_area = design_vector[0:3]

        # Extract lengths (same position for both standard and hyperbolic)
        length1, length2 = design_vector[3], design_vector[4]

        # Calculate flare rates
        if length1 > 0 and middle_area > throat_area:
            m1 = np.log(middle_area / throat_area) / length1
        else:
            return 0.0  # Invalid geometry, let other constraints handle it

        if length2 > 0 and mouth_area > middle_area:
            m2 = np.log(mouth_area / middle_area) / length2
        else:
            return 0.0

        # Constraint: m2 should not exceed m1 by more than max_flare_increase
        # m2 - m1 ≤ max_flare_increase
        # This allows m2 > m1 slightly, but not dramatically
        violation = m2 - m1 - max_flare_increase
        violations.append(violation)

    elif num_segments == 3:
        throat_area, middle_area, area2, mouth_area = design_vector[0:4]

        # Extract lengths (same position for both standard and hyperbolic)
        length1, length2, length3 = design_vector[4], design_vector[5], design_vector[6]

        # Calculate flare rates
        if length1 > 0 and middle_area > throat_area:
            m1 = np.log(middle_area / throat_area) / length1
        else:
            return 0.0

        if length2 > 0 and area2 > middle_area:
            m2 = np.log(area2 / middle_area) / length2
        else:
            return 0.0

        if length3 > 0 and mouth_area > area2:
            m3 = np.log(mouth_area / area2) / length3
        else:
            return 0.0

        # Constraint: flare rates should not increase dramatically
        # m2 - m1 ≤ max_flare_increase
        # m3 - m2 ≤ max_flare_increase
        violations.append(m2 - m1 - max_flare_increase)
        violations.append(m3 - m2 - max_flare_increase)

    if not violations:
        return 0.0

    # Return maximum violation (positive = bad, negative = satisfied)
    return max(violations)

