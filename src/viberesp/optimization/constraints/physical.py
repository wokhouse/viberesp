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
        >>> driver = get_bc_8ndl51()  # X_max = 7mm
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
                port_area, port_length = calculate_optimal_port_dimensions(
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
        >>> driver = get_bc_12ndl76()
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
