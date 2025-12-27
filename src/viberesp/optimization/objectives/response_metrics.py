"""
Objective functions for evaluating enclosure frequency response performance.

This module implements objective functions for multi-objective optimization:
- F3: -3dB cutoff frequency (minimize for better bass extension)
- Response flatness: Frequency response variation (minimize for smoother sound)

Literature:
    - Small (1972) - Closed-box system parameters, F3 definition
    - Thiele (1971) - Vented box alignments and F3 calculation
    - Beranek (1954), Chapter 8 - Bandwidth and flatness definitions
    - literature/thiele_small/small_1972_closed_box.md
    - literature/thiele_small/thiele_1971_vented_boxes.md
    - literature/horns/beranek_1954.md
"""

import numpy as np
from typing import Tuple

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.enclosure.sealed_box import calculate_sealed_box_system_parameters, SealedBoxSystemParameters
from viberesp.enclosure.ported_box import calculate_ported_box_system_parameters, PortedBoxSystemParameters
from viberesp.driver.response import direct_radiator_electrical_impedance


def objective_f3(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    frequency_points: np.ndarray = None
) -> float:
    """
    Calculate -3dB cutoff frequency for minimization.

    The F3 frequency is where the SPL response has dropped by 3dB from
    the reference level in the passband. Lower F3 indicates better
    bass extension.

    Literature:
        - Small (1972) - F3 definition for sealed/ported boxes
        - Thiele (1971) - Vented box F3 calculation
        - Olson (1947), Eq. 5.18 - Horn cutoff frequency
        - literature/thiele_small/small_1972_closed_box.md
        - literature/thiele_small/thiele_1971_vented_boxes.md
        - literature/horns/olson_1947.md

    Args:
        design_vector: Enclosure parameters
            - Sealed: [Vb] (m³)
            - Ported: [Vb, Fb] (m³, Hz)
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle"
        frequency_points: Frequency array for interpolation (not used for sealed/ported)

    Returns:
        F3 frequency in Hz (to be minimized)

    Validation:
        Compare with Hornresp F3 calculation.
        Expected: <1% deviation for simple enclosures, <2% for horns

    Examples:
        >>> # Sealed box with 10L volume
        >>> driver = ThieleSmallParameters(M_md=0.026, C_ms=0.001, R_ms=3.0,
        ...                                  R_e=8.0, L_e=1e-3, BL=12.0, S_d=0.035)
        >>> objective_f3(np.array([0.010]), driver, "sealed")
        75.3  # Hz (example value)
    """
    if enclosure_type == "sealed":
        # For sealed box, F3 is calculated directly from system parameters
        Vb = design_vector[0]

        # Calculate system parameters
        params = calculate_sealed_box_system_parameters(driver, Vb)

        return params.F3

    elif enclosure_type == "ported":
        # For ported box, F3 is calculated from system parameters
        Vb = design_vector[0]
        Fb = design_vector[1]

        # Calculate system parameters
        params = calculate_ported_box_system_parameters(driver, Vb, Fb)

        return params.F3

    elif enclosure_type == "infinite_baffle" or enclosure_type == "direct_radiator":
        # For infinite baffle, F3 ≈ Fs (driver resonance)
        return driver.F_s

    else:
        raise ValueError(f"Unsupported enclosure type: {enclosure_type}")


def objective_response_flatness(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    frequency_range: Tuple[float, float] = (20.0, 500.0),
    n_points: int = 100,
    voltage: float = 2.83
) -> float:
    """
    Calculate frequency response variation (standard deviation) for minimization.

    Lower values indicate flatter frequency response, which is generally
    desirable for accurate sound reproduction.

    Literature:
        - Small (1972) - Frequency response transfer functions
        - Beranek (1954), Chapter 8 - Bandwidth and flatness definitions
        - literature/thiele_small/small_1972_closed_box.md

    Args:
        design_vector: Enclosure parameters
            - Sealed: [Vb] (m³)
            - Ported: [Vb, Fb, port_area, port_length] (m³, Hz, m², m)
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle"
        frequency_range: (f_min, f_max) in Hz for flatness calculation
        n_points: Number of frequency points to evaluate
        voltage: Input voltage for SPL calculation (default 2.83V)

    Returns:
        Standard deviation of SPL (dB) over frequency range (lower is better)

    Note:
        Uses log-spaced frequencies to match human hearing perception.
        Ported box evaluation excludes frequencies below Fb to avoid
        steep rolloff region dominating the metric.

    Examples:
        >>> driver = get_bc_8ndl51()
        >>> objective_response_flatness(
        ...     np.array([0.010]), driver, "sealed",
        ...     frequency_range=(40, 200), n_points=50
        ... )
        1.23  # dB standard deviation (example value)
    """
    # Generate frequency array (log-spaced)
    frequencies = np.logspace(
        np.log10(frequency_range[0]),
        np.log10(frequency_range[1]),
        n_points
    )

    # For ported box, adjust frequency range to exclude deep rolloff below Fb
    if enclosure_type == "ported" and len(design_vector) >= 2:
        Fb = design_vector[1]
        f_min = max(frequency_range[0], Fb * 0.8)  # Start slightly below Fb
        if f_min < frequency_range[1]:
            frequencies = np.logspace(
                np.log10(f_min),
                np.log10(frequency_range[1]),
                max(n_points // 2, 20)  # Fewer points for reduced range
            )

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        try:
            if enclosure_type == "sealed":
                Vb = design_vector[0]
                result = sealed_box_electrical_impedance(
                    freq, driver, Vb=Vb, voltage=voltage
                )
            elif enclosure_type == "ported":
                Vb = design_vector[0]
                Fb = design_vector[1]
                # For sweep, may not have port parameters yet
                if len(design_vector) >= 4:
                    port_area = design_vector[2]
                    port_length = design_vector[3]
                    result = ported_box_electrical_impedance(
                        freq, driver, Vb=Vb, Fb=Fb,
                        port_area=port_area, port_length=port_length,
                        voltage=voltage
                    )
                else:
                    # Simplified calculation without port detail
                    from viberesp.enclosure.ported_box import calculate_optimal_port_dimensions
                    port_area, port_length = calculate_optimal_port_dimensions(
                        driver, Vb, Fb
                    )
                    result = ported_box_electrical_impedance(
                        freq, driver, Vb=Vb, Fb=Fb,
                        port_area=port_area, port_length=port_length,
                        voltage=voltage
                    )
            elif enclosure_type == "infinite_baffle" or enclosure_type == "direct_radiator":
                result = direct_radiator_electrical_impedance(
                    freq, driver, voltage=voltage
                )
            else:
                raise ValueError(f"Unsupported enclosure type: {enclosure_type}")

            spl_values.append(result['SPL'])

        except Exception as e:
            # Fill with NaN on failure
            import warnings
            warnings.warn(f"SPL calculation failed at {freq:.1f}Hz: {e}")
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Remove NaN values
    valid_mask = ~np.isnan(spl_values)
    if np.sum(valid_mask) == 0:
        return 1000.0  # Large penalty if all calculations failed

    spl_valid = spl_values[valid_mask]

    # Calculate flatness as standard deviation
    # Beranek (1954), Chapter 8 - Flatness criterion
    flatness_metric = np.std(spl_valid)

    return flatness_metric


def objective_max_spl(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    frequency_range: Tuple[float, float] = (40.0, 200.0),
    n_points: int = 50,
    voltage: float = 2.83
) -> float:
    """
    Calculate maximum SPL in frequency range (for maximization).

    This is a helper function for efficiency calculations. Returns the
    maximum SPL achieved in the specified frequency range.

    Literature:
        - Beranek (1954), Chapter 8 - Power output and efficiency
        - Small (1972) - SPL calculations for sealed/ported boxes

    Args:
        design_vector: Enclosure parameters
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle"
        frequency_range: (f_min, f_max) in Hz for evaluation
        n_points: Number of frequency points to evaluate
        voltage: Input voltage for SPL calculation (default 2.83V)

    Returns:
        Maximum SPL in dB (to be maximized)
    """
    # Generate frequency array (log-spaced)
    frequencies = np.logspace(
        np.log10(frequency_range[0]),
        np.log10(frequency_range[1]),
        n_points
    )

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        try:
            if enclosure_type == "sealed":
                Vb = design_vector[0]
                result = sealed_box_electrical_impedance(
                    freq, driver, Vb=Vb, voltage=voltage
                )
            elif enclosure_type == "ported":
                Vb = design_vector[0]
                Fb = design_vector[1]
                if len(design_vector) >= 4:
                    port_area = design_vector[2]
                    port_length = design_vector[3]
                    result = ported_box_electrical_impedance(
                        freq, driver, Vb=Vb, Fb=Fb,
                        port_area=port_area, port_length=port_length,
                        voltage=voltage
                    )
                else:
                    from viberesp.enclosure.ported_box import calculate_optimal_port_dimensions
                    port_area, port_length = calculate_optimal_port_dimensions(
                        driver, Vb, Fb
                    )
                    result = ported_box_electrical_impedance(
                        freq, driver, Vb=Vb, Fb=Fb,
                        port_area=port_area, port_length=port_length,
                        voltage=voltage
                    )
            elif enclosure_type == "infinite_baffle" or enclosure_type == "direct_radiator":
                result = direct_radiator_electrical_impedance(
                    freq, driver, voltage=voltage
                )
            else:
                raise ValueError(f"Unsupported enclosure type: {enclosure_type}")

            spl_values.append(result['SPL'])

        except Exception:
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Remove NaN values
    valid_mask = ~np.isnan(spl_values)
    if np.sum(valid_mask) == 0:
        return 0.0

    return np.max(spl_values[valid_mask])


# Import response calculation functions
def sealed_box_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    Vb: float,
    voltage: float = 2.83
) -> dict:
    """Calculate sealed box electrical impedance and SPL at a single frequency."""
    from viberesp.enclosure.sealed_box import sealed_box_electrical_impedance as sb_impedance
    return sb_impedance(frequency, driver, Vb, voltage=voltage)


def ported_box_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    Vb: float,
    Fb: float,
    port_area: float,
    port_length: float,
    voltage: float = 2.83
) -> dict:
    """Calculate ported box electrical impedance and SPL at a single frequency."""
    from viberesp.enclosure.ported_box import ported_box_electrical_impedance as pb_impedance
    return pb_impedance(frequency, driver, Vb, Fb, port_area, port_length, voltage=voltage)
