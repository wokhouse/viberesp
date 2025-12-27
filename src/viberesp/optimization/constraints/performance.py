"""
Performance constraint functions for enclosure optimization.

This module provides constraint functions for ensuring optimized designs
meet performance requirements:
- F3 limits (bass extension)
- Qtc ranges (transient response)
- Bandwidth requirements

Literature:
    - Small (1972) - F3 definition and calculation
    - Thiele (1971) - Alignment selection and system parameters
    - literature/thiele_small/small_1972_closed_box.md
    - literature/thiele_small/thiele_1971_vented_boxes.md
"""

import numpy as np

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.optimization.objectives.response_metrics import objective_f3
from viberesp.enclosure.sealed_box import calculate_sealed_box_system_parameters


def constraint_f3_limit(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    max_f3: float = 100.0
) -> float:
    """
    Constrain F3 to be below specified limit.

    This is useful for ensuring a minimum level of bass extension.

    Literature:
        - Small (1972) - F3 definition and calculation

    Args:
        design_vector: Enclosure parameters
        driver: ThieleSmallParameters instance
        enclosure_type: Type of enclosure ("sealed", "ported")
        max_f3: Maximum allowed F3 in Hz (default 100 Hz)

    Returns:
        Constraint violation (positive if F3 > max_f3)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = get_bc_12ndl76()
        >>> # Require F3 < 80 Hz
        >>> violation = constraint_f3_limit(
        ...     np.array([0.020]), driver, "sealed", max_f3=80
        ... )
        >>> # If violation > 0, F3 is higher than 80 Hz (constraint failed)
    """
    try:
        f3 = objective_f3(design_vector, driver, enclosure_type)
        return f3 - max_f3
    except Exception:
        return 1000.0  # Large violation if calculation fails


def constraint_f3_target(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    target_f3: float = 60.0,
    tolerance: float = 5.0
) -> float:
    """
    Constrain F3 to be close to target value.

    This is useful when you want a specific bass extension target.

    Literature:
        - Small (1972) - F3 calculation

    Args:
        design_vector: Enclosure parameters
        driver: ThieleSmallParameters instance
        enclosure_type: Type of enclosure
        target_f3: Target F3 in Hz (default 60 Hz)
        tolerance: Allowed deviation from target in Hz (default 5 Hz)

    Returns:
        Maximum constraint violation (positive if outside tolerance range)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = get_bc_8ndl51()
        >>> # Target F3 = 70 Hz ± 5 Hz
        >>> violation = constraint_f3_target(
        ...     np.array([0.010]), driver, "sealed",
        ...     target_f3=70, tolerance=5
        ... )
        >>> # If |violation| <= 0, F3 is in [65, 75] Hz range
    """
    try:
        f3 = objective_f3(design_vector, driver, enclosure_type)

        # Two-sided constraint: target - tolerance <= F3 <= target + tolerance
        violation_low = (target_f3 - tolerance) - f3  # Positive if F3 too low
        violation_high = f3 - (target_f3 + tolerance)  # Positive if F3 too high

        # Return maximum violation (must be <= 0 for satisfaction)
        return max(violation_low, violation_high, 0.0)

    except Exception:
        return 1000.0


def constraint_qtc_range(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    qtc_min: float = 0.5,
    qtc_max: float = 1.2
) -> float:
    """
    Constrain system Qtc to be within acceptable range.

    Qtc affects transient response and bass character:
    - Qtc < 0.5: Overdamped (poor transient response, weak bass)
    - Qtc 0.5-0.71: Critically damped to Butterworth (tight, accurate bass)
    - Qtc 0.71-1.0: Slightly underdamped (warm bass, good transient)
    - Qtc > 1.2: Underdamped (boomy, ringing, poor transient)

    Literature:
        - Small (1972) - Qtc and its effect on transient response
        - literature/thiele_small/small_1972_closed_box.md

    Args:
        design_vector: Enclosure parameters (only for sealed boxes)
        driver: ThieleSmallParameters instance
        enclosure_type: Must be "sealed"
        qtc_min: Minimum acceptable Qtc (default 0.5)
        qtc_max: Maximum acceptable Qtc (default 1.2)

    Returns:
        Maximum constraint violation (positive if outside range)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = get_bc_8ndl51()
        >>> # Require Butterworth alignment (Qtc = 0.707 ± 0.05)
        >>> violation = constraint_qtc_range(
        ...     np.array([0.010]), driver, "sealed",
        ...     qtc_min=0.65, qtc_max=0.75
        ... )
        >>> # If violation <= 0, Qtc is in [0.65, 0.75] range
    """
    if enclosure_type != "sealed":
        return 0.0  # Not applicable for other enclosures

    try:
        Vb = design_vector[0]
        params = calculate_sealed_box_system_parameters(driver, Vb)

        # Return maximum violation (positive if outside range)
        violation_low = qtc_min - params.Qtc
        violation_high = params.Qtc - qtc_max

        return max(violation_low, violation_high, 0.0)

    except Exception:
        return 1000.0


def constraint_volume_limit(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    max_volume_liters: float = 50.0
) -> float:
    """
    Constrain enclosure volume to be below maximum limit.

    This is useful for space-constrained applications.

    Literature:
        - Small (1972) - Box volume definitions

    Args:
        design_vector: Enclosure parameters
        driver: ThieleSmallParameters instance
        enclosure_type: Type of enclosure ("sealed", "ported")
        max_volume_liters: Maximum allowed volume in liters (default 50L)

    Returns:
        Constraint violation (positive if volume > max_volume)
        pymoo expects constraints to be ≤ 0 (negative = satisfied)

    Examples:
        >>> driver = get_bc_15ds115()
        >>> # Maximum 100L enclosure
        >>> violation = constraint_volume_limit(
        ...     np.array([0.080]), driver, "sealed",
        ...     max_volume_liters=100
        ... )
        >>> # If violation <= 0, volume is <= 100L
    """
    from viberesp.optimization.objectives.size_metrics import objective_enclosure_volume

    try:
        volume_m3 = objective_enclosure_volume(design_vector, driver, enclosure_type)
        volume_liters = volume_m3 * 1000.0

        return volume_liters - max_volume_liters

    except Exception:
        return 1000.0
