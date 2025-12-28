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
from viberesp.simulation.types import ExponentialHorn
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
from viberesp.optimization.parameters.exponential_horn_params import calculate_horn_cutoff_frequency
from viberesp.simulation.horn_theory import multsegment_horn_throat_impedance
from viberesp.simulation.types import HornSegment, MultiSegmentHorn
from viberesp.optimization.parameters.multisegment_horn_params import decode_multisegment_design
from viberesp.simulation.constants import SPEED_OF_SOUND


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
            - Exponential horn: [throat_area, mouth_area, length, V_rc] (m², m², m, m³)
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle", "exponential_horn"
        frequency_points: Frequency array for interpolation (not used for sealed/ported/horns)

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

    elif enclosure_type == "exponential_horn":
        # For exponential horn, F3 is the cutoff frequency
        # Literature: Olson (1947), Eq. 5.18 - f_c = c·m/(2π)
        # Horns act as high-pass filters below cutoff frequency
        throat_area = design_vector[0]
        mouth_area = design_vector[1]
        length = design_vector[2]
        # V_rc not used for cutoff calculation (design_vector[3])

        # Calculate cutoff frequency using Olson's formula
        fc = calculate_horn_cutoff_frequency(throat_area, mouth_area, length)

        return fc  # Minimize cutoff frequency for better bass extension

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
            - Exponential horn: [throat_area, mouth_area, length, V_rc] (m², m², m, m³)
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle", "exponential_horn"
        frequency_range: (f_min, f_max) in Hz for flatness calculation
        n_points: Number of frequency points to evaluate
        voltage: Input voltage for SPL calculation (default 2.83V)

    Returns:
        Standard deviation of SPL (dB) over frequency range (lower is better)

    Note:
        Uses log-spaced frequencies to match human hearing perception.
        Ported box evaluation excludes frequencies below Fb to avoid
        steep rolloff region dominating the metric.
        Horn evaluation excludes frequencies below 1.5×Fc to avoid
        cutoff region dominating the metric (Olson 1947).

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

    # For exponential horn, adjust frequency range to exclude cutoff region
    elif enclosure_type == "exponential_horn" and len(design_vector) >= 3:
        throat_area = design_vector[0]
        mouth_area = design_vector[1]
        length = design_vector[2]

        # Calculate cutoff frequency
        fc = calculate_horn_cutoff_frequency(throat_area, mouth_area, length)

        # Determine appropriate frequency range based on horn type
        # Bass horns (Fc < 100 Hz): Evaluate up to 5×Fc (bass range)
        # Midrange horns (100 ≤ Fc < 500 Hz): Evaluate up to 20×Fc (full passband)
        # Tweeter horns (Fc ≥ 500 Hz): Evaluate up to 20 kHz
        if fc < 100:
            # Bass horn: 20-500 Hz range
            f_max = max(frequency_range[1], fc * 5)
        elif fc < 500:
            # Midrange horn: Extend to 20×Fc to cover full passband
            # Literature: Beranek (1954) - Horn passband extends to ~20×Fc
            f_max = max(frequency_range[1], fc * 20, 5000)
        else:
            # Tweeter horn: Extend to 20 kHz
            f_max = 20000

        # Start at 1.5×Fc to avoid cutoff rolloff dominating metric
        # Literature: Olson (1947) - Horn response is flat above 1.5×Fc
        f_min = max(frequency_range[0], fc * 1.5)

        # Ensure f_min < f_max for valid range
        if f_min < f_max:
            frequencies = np.logspace(
                np.log10(f_min),
                np.log10(f_max),
                n_points  # Use full n_points for wide range
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
                    port_area, port_length, _ = calculate_optimal_port_dimensions(
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
            elif enclosure_type == "exponential_horn":
                throat_area = design_vector[0]
                mouth_area = design_vector[1]
                length = design_vector[2]
                V_rc = design_vector[3] if len(design_vector) >= 4 else 0.0

                # Create horn system
                horn = ExponentialHorn(throat_area, mouth_area, length)
                flh = FrontLoadedHorn(driver, horn, V_rc=V_rc)

                # Calculate SPL at this frequency
                spl = flh.spl_response(freq, voltage=voltage)
                result = {'SPL': spl}
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


def objective_response_slope(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    frequency_range: Tuple[float, float] = (20.0, 500.0),
    n_points: int = 100,
    voltage: float = 2.83
) -> float:
    """
    Calculate frequency response slope (dB/decade) for minimization.

    This measures the overall slope of the frequency response on a log-frequency
    scale. A perfectly flat response has 0 dB/decade slope. Exponential horns
    typically have -15 to -25 dB/decade slope due to high-frequency rolloff.

    This function fits a line to SPL vs log(frequency) and returns the absolute
    slope value, which should be minimized for flatter response.

    Literature:
        - Olson (1947), Chapter 8 - High-frequency horn behavior
        - Beranek (1954), Chapter 5 - Horn directivity and beaming
        - Keele (1975) - Horn profile comparisons

    Args:
        design_vector: Enclosure parameters
            - Sealed: [Vb] (m³)
            - Ported: [Vb, Fb, port_area, port_length] (m³, Hz, m², m)
            - Exponential horn: [throat_area, mouth_area, length, V_rc] (m², m², m, m³)
        driver: ThieleSmallParameters instance
        enclosure_type: "sealed", "ported", "infinite_baffle", "exponential_horn"
        frequency_range: (f_min, f_max) in Hz for slope calculation
        n_points: Number of frequency points to evaluate
        voltage: Input voltage for SPL calculation (default 2.83V)

    Returns:
        Absolute slope in dB/decade (lower is better, target < 3 dB/decade)

    Note:
        Uses log-spaced frequencies to match human hearing perception.
        Slope is calculated as: SPL = slope * log10(frequency) + intercept
        Returns absolute value of slope (minimizes both upward and downward slopes)

    Examples:
        >>> driver = get_bc_8ndl51()
        >>> # Calculate slope from 1-10 kHz
        >>> slope = objective_response_slope(
        ...     np.array([0.0002, 0.04, 0.6, 0.0]), driver, "exponential_horn",
        ...     frequency_range=(1000, 10000), n_points=50
        ... )
        >>> slope
        15.3  # dB/decade (typical for exponential horns)
    """
    # Generate frequency array (log-spaced)
    frequencies = np.logspace(
        np.log10(frequency_range[0]),
        np.log10(frequency_range[1]),
        n_points
    )

    # For exponential horn, adjust frequency range to exclude cutoff region
    if enclosure_type == "exponential_horn" and len(design_vector) >= 3:
        throat_area = design_vector[0]
        mouth_area = design_vector[1]
        length = design_vector[2]

        # Calculate cutoff frequency
        fc = calculate_horn_cutoff_frequency(throat_area, mouth_area, length)

        # Determine appropriate frequency range based on horn type
        if fc < 100:
            f_max = max(frequency_range[1], fc * 5)
        elif fc < 500:
            f_max = max(frequency_range[1], fc * 20, 5000)
        else:
            f_max = 20000

        f_min = max(frequency_range[0], fc * 1.5)

        # Ensure f_min < f_max for valid range
        if f_min < f_max:
            frequencies = np.logspace(
                np.log10(f_min),
                np.log10(f_max),
                n_points
            )

    # Calculate SPL at each frequency
    spl_values = []
    for freq in frequencies:
        try:
            if enclosure_type == "exponential_horn":
                throat_area = design_vector[0]
                mouth_area = design_vector[1]
                length = design_vector[2]
                V_rc = design_vector[3] if len(design_vector) >= 4 else 0.0

                # Create horn system
                horn = ExponentialHorn(throat_area, mouth_area, length)
                flh = FrontLoadedHorn(driver, horn, V_rc=V_rc)

                # Calculate SPL at this frequency
                spl = flh.spl_response(freq, voltage=voltage)
                spl_values.append(spl)
            else:
                # For other enclosure types, slope is less critical
                # Use existing flatness calculation
                return 0.0

        except Exception as e:
            import warnings
            warnings.warn(f"SPL calculation failed at {freq:.1f}Hz: {e}")
            spl_values.append(np.nan)

    spl_values = np.array(spl_values)

    # Remove NaN values
    valid_mask = ~np.isnan(spl_values)
    if np.sum(valid_mask) == 0:
        return 1000.0  # Large penalty if all calculations failed

    freq_valid = frequencies[valid_mask]
    spl_valid = spl_values[valid_mask]

    # Fit line: SPL = slope * log10(frequency) + intercept
    # Use linear regression on log-frequency scale
    log_freq = np.log10(freq_valid)
    coeffs = np.polyfit(log_freq, spl_valid, 1)

    slope = coeffs[0]  # dB per decade (log10 frequency)
    intercept = coeffs[1]

    # Return absolute slope (minimize both upward and downward slopes)
    # Target: < 3 dB/decade for acceptable response
    return abs(slope)


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
                    port_area, port_length, _ = calculate_optimal_port_dimensions(
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
    voltage: float = 2.83,
    measurement_distance: float = 1.0,
    use_transfer_function_spl: bool = True
) -> dict:
    """
    Calculate sealed box electrical impedance and SPL at a single frequency.

    Args:
        frequency: Frequency in Hz
        driver: ThieleSmallParameters instance
        Vb: Box volume in m³
        voltage: Input voltage in V
        measurement_distance: Measurement distance in m
        use_transfer_function_spl: If True, use calibrated transfer function SPL
            (required for -25.25 dB offset matching Hornresp)
    """
    from viberesp.enclosure.sealed_box import sealed_box_electrical_impedance as sb_impedance
    return sb_impedance(frequency, driver, Vb, voltage=voltage,
                        measurement_distance=measurement_distance,
                        use_transfer_function_spl=use_transfer_function_spl)


def ported_box_electrical_impedance(
    frequency: float,
    driver: ThieleSmallParameters,
    Vb: float,
    Fb: float,
    port_area: float,
    port_length: float,
    voltage: float = 2.83,
    measurement_distance: float = 1.0,
    use_transfer_function_spl: bool = True
) -> dict:
    """
    Calculate ported box electrical impedance and SPL at a single frequency.

    Args:
        frequency: Frequency in Hz
        driver: ThieleSmallParameters instance
        Vb: Box volume in m³
        Fb: Port tuning frequency in Hz
        port_area: Port cross-sectional area in m²
        port_length: Port length in m
        voltage: Input voltage in V
        measurement_distance: Measurement distance in m
        use_transfer_function_spl: If True, use calibrated transfer function SPL
            (required for -25.25 dB offset matching Hornresp)
    """
    from viberesp.enclosure.ported_box import ported_box_electrical_impedance as pb_impedance
    return pb_impedance(frequency, driver, Vb, Fb, port_area, port_length,
                        voltage=voltage, measurement_distance=measurement_distance,
                        use_transfer_function_spl=use_transfer_function_spl)


def objective_wavefront_sphericity(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    num_segments: int = 2,
    n_points: int = 50
) -> float:
    """
    Calculate wavefront sphericity deviation for multi-segment horn.

    For a spherical wave horn (tractrix), the wavefronts are spherical shells
    with constant radius of curvature. This measures how much the horn's
    expansion deviates from maintaining spherical wavefronts.

    Literature:
        - Keele (1975) - Tractrix horn derivation from spherical wavefront requirement
        - Kolbrek Part 2 - Spherical wave horns and wavefront curvature
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Theory:
        A spherical wave horn maintains wavefronts that are portions of a sphere.
        The wavefront radius R is related to the cutoff frequency:
            R = c / (2π * f_c)
        For tractrix horns, the wavefront radius is constant throughout the horn.
        For exponential horns, wavefronts are plane (infinite radius of curvature).

        This objective measures the RMS deviation from constant wavefront radius,
        which correlates to diffraction and high-frequency smoothness.

    Args:
        design_vector: Horn parameters
            - For multisegment_horn: [throat_area, middle_area, mouth_area, length1, length2, V_rc]
        driver: ThieleSmallParameters instance
        enclosure_type: Must be "multisegment_horn"
        num_segments: Number of horn segments (2 or 3)
        n_points: Number of axial positions to evaluate

    Returns:
        RMS deviation from spherical wavefront (lower is better)
        Returns 0 for perfect spherical wave, higher values for exponential/conical

    Raises:
        ValueError: If enclosure_type is not "multisegment_horn"

    Examples:
        >>> driver = get_tc2_compression_driver()
        >>> design = np.array([0.000212, 0.010, 0.04084, 0.20, 0.394, 0.0])
        >>> sphericity = objective_wavefront_sphericity(
        ...     design, driver, "multisegment_horn", num_segments=2
        ... )
        >>> sphericity
        0.15  # RMS deviation (example value)
    """
    if enclosure_type != "multisegment_horn":
        raise ValueError(
            f"objective_wavefront_sphericity only supports 'multisegment_horn', "
            f"got '{enclosure_type}'"
        )

    # Decode design to horn geometry
    params = decode_multisegment_design(design_vector, driver, num_segments)

    # Build segments list
    segments = []
    for throat_area, mouth_area, length in params['segments']:
        segments.append(HornSegment(throat_area, mouth_area, length))

    horn = MultiSegmentHorn(segments=segments)
    total_length = horn.total_length()

    # Calculate reference wavefront radius at mouth
    # For spherical wave horn, radius at mouth: R_mouth ≈ c / (2π * f_c)
    # where f_c is the minimum cutoff among all segments
    flare_constants = params['flare_constants']
    m_max = max(flare_constants) if flare_constants else 0

    if m_max > 0:
        # Reference wavefront radius (would be constant for tractrix)
        # Using the largest flare constant (most restrictive segment)
        f_c = (SPEED_OF_SOUND * m_max) / (2 * np.pi)
        R_reference = SPEED_OF_SOUND / (2 * np.pi * f_c) if f_c > 0 else total_length
    else:
        R_reference = total_length

    # Calculate wavefront radius deviation along horn length
    # For exponential segment i: local wavefront radius r_i(x) = 1/m_i
    # where m_i is the local flare constant
    deviations = []

    for i in range(n_points):
        x = (i / (n_points - 1)) * total_length if n_points > 1 else 0

        # Find which segment contains position x
        cumulative_length = 0.0
        segment_idx = 0
        for seg_idx, seg in enumerate(segments):
            if x <= cumulative_length + seg.length:
                segment_idx = seg_idx
                break
            cumulative_length += seg.length

        # Local flare constant at this position
        m_local = segments[segment_idx].flare_constant

        # For exponential horn, local wavefront radius ≈ 1/m
        # For tractrix (spherical wave), this would be constant = R_reference
        if m_local > 0:
            R_local = 1.0 / m_local
        else:
            R_local = R_reference

        # Normalized deviation from spherical wavefront
        deviation = (R_local - R_reference) / R_reference
        deviations.append(deviation)

    # Return RMS deviation (lower is better)
    deviations = np.array(deviations)
    return float(np.sqrt(np.mean(deviations ** 2)))


def objective_impedance_smoothness(
    design_vector: np.ndarray,
    driver: ThieleSmallParameters,
    enclosure_type: str,
    num_segments: int = 2,
    frequency_range: Tuple[float, float] = (100, 10000),
    n_points: int = 100
) -> float:
    """
    Calculate throat impedance smoothness for multi-segment horn.

    Measures how smooth the throat impedance is vs frequency. Peaks and dips
    in throat impedance indicate resonances that color the sound. A smooth
    impedance curve indicates cleaner, more neutral sound.

    Literature:
        - Olson (1947) - Impedance variations cause sound coloration
        - Beranek (1954) - Smooth impedance = natural sound
        - Kolbrek Part 1 - Throat impedance and mouth reflections

    Theory:
        Throat impedance variations occur due to:
        1. Mouth reflections (impedance mismatch)
        2. Segment junction reflections (flare rate changes)
        3. Standing waves within the horn

        This objective measures the peak-to-peak variation of the real part
        of throat impedance across frequency. Lower variation = fewer
        resonances = cleaner sound.

    Args:
        design_vector: Horn parameters
            - For multisegment_horn: [throat_area, middle_area, mouth_area, length1, length2, V_rc]
        driver: ThieleSmallParameters instance
        enclosure_type: Must be "multisegment_horn"
        num_segments: Number of horn segments (2 or 3)
        frequency_range: (f_min, f_max) in Hz for evaluation
        n_points: Number of frequency points to evaluate

    Returns:
        Peak-to-peak variation of throat resistance in ohms (lower is better)

    Raises:
        ValueError: If enclosure_type is not "multisegment_horn"

    Examples:
        >>> driver = get_tc2_compression_driver()
        >>> design = np.array([0.000212, 0.010, 0.04084, 0.20, 0.394, 0.0])
        >>> smoothness = objective_impedance_smoothness(
        ...     design, driver, "multisegment_horn",
        ...     frequency_range=(200, 5000), n_points=50
        ... )
        >>> smoothness
        15.3  # ohms peak-to-peak (example value)
    """
    if enclosure_type != "multisegment_horn":
        raise ValueError(
            f"objective_impedance_smoothness only supports 'multisegment_horn', "
            f"got '{enclosure_type}'"
        )

    # Decode design to horn geometry
    params = decode_multisegment_design(design_vector, driver, num_segments)

    # Build segments list
    segments = []
    for throat_area, mouth_area, length in params['segments']:
        segments.append(HornSegment(throat_area, mouth_area, length))

    horn = MultiSegmentHorn(segments=segments)

    # Generate frequency array (log-spaced)
    frequencies = np.logspace(
        np.log10(frequency_range[0]),
        np.log10(frequency_range[1]),
        n_points
    )

    # Calculate throat impedance across frequency range
    try:
        z_throat = multsegment_horn_throat_impedance(frequencies, horn)
    except Exception as e:
        import warnings
        warnings.warn(f"Throat impedance calculation failed: {e}")
        return 1000.0  # Large penalty for failed calculation

    # Extract real part (resistance)
    resistance = np.real(z_throat)

    # Remove NaN values
    valid_mask = ~np.isnan(resistance)
    if np.sum(valid_mask) == 0:
        return 1000.0  # Large penalty if all calculations failed

    resistance_valid = resistance[valid_mask]

    # Calculate peak-to-peak variation
    # This measures the impedance ripple caused by reflections
    peak_to_peak = np.max(resistance_valid) - np.min(resistance_valid)

    # Normalize by mean resistance to account for different throat sizes
    mean_resistance = np.mean(resistance_valid)
    if mean_resistance > 0:
        normalized_variation = peak_to_peak / mean_resistance
    else:
        normalized_variation = peak_to_peak

    return float(normalized_variation)


def multisegment_horn_objectives(
    design: np.ndarray,
    driver: ThieleSmallParameters,
    num_segments: int = 2,
    objectives: list = None
) -> list:
    """
    Multi-objective evaluation for multi-segment horn optimization.

    Evaluates a multi-segment horn design across multiple physics-based
    objectives that correlate to "clean, not harsh" sound quality.

    Literature:
        - Keele (1975) - Wavefront sphericity and diffraction
        - Olson (1947) - Impedance smoothness and coloration
        - Beranek (1954) - Frequency response flatness
        - literature/horns/kolbrek_horn_theory_tutorial.md

    Objectives:
        1. Wavefront Sphericity: Minimize deviation from spherical wavefronts
           - Lower deviation = less diffraction = smoother highs
           - Tractrix horns excel here (spherical wavefronts by design)

        2. Impedance Smoothness: Minimize throat impedance variation
           - Lower variation = fewer resonances = cleaner midrange
           - Gradual flare reduces reflections

        3. SPL Slope: Minimize dB/decade slope (already exists)
           - Flatter response = natural sound

        4. SPL Residuals: Minimize std dev around trend (already exists)
           - Less ripple = smoother response

    Args:
        design: Optimization array [throat_area, middle_area, mouth_area,
                length1, length2, V_rc] for 2-segment, or additional
                [area2, length3] for 3-segment
        driver: ThieleSmallParameters for the driver
        num_segments: Number of horn segments (2 or 3)
        objectives: List of objective names to evaluate
            Default: ["wavefront_sphericity", "impedance_smoothness"]
            Available: "wavefront_sphericity", "impedance_smoothness",
                       "response_slope", "response_flatness"

    Returns:
        List of objective values (to be minimized)

    Examples:
        >>> driver = get_tc2_compression_driver()
        >>> design = np.array([0.000212, 0.010, 0.04084, 0.20, 0.394, 0.0])
        >>> objectives = multisegment_horn_objectives(
        ...     design, driver, num_segments=2,
        ...     objectives=["wavefront_sphericity", "impedance_smoothness"]
        ... )
        >>> objectives
        [0.15, 12.3]  # [sphericity_deviation, impedance_variation]

    Notes:
        This function allows the optimizer to discover horn profiles based
        on physics rather than tradition. If wavefront sphericity is
        important, tractrix-like profiles will emerge naturally. If
        impedance smoothness is important, gradual flares will be favored.
    """
    if objectives is None:
        objectives = ["wavefront_sphericity", "impedance_smoothness"]

    results = []
    enclosure_type = "multisegment_horn"

    for obj_name in objectives:
        if obj_name == "wavefront_sphericity":
            val = objective_wavefront_sphericity(
                design, driver, enclosure_type, num_segments
            )
            results.append(val)

        elif obj_name == "impedance_smoothness":
            val = objective_impedance_smoothness(
                design, driver, enclosure_type, num_segments
            )
            results.append(val)

        elif obj_name == "response_slope":
            val = objective_response_slope(
                design, driver, enclosure_type,
                frequency_range=(200, 5000),  # Midrange range
                n_points=50
            )
            results.append(val)

        elif obj_name == "response_flatness":
            val = objective_response_flatness(
                design, driver, enclosure_type,
                frequency_range=(200, 5000),  # Midrange range
                n_points=50
            )
            results.append(val)

        else:
            import warnings
            warnings.warn(f"Unknown objective: {obj_name}")
            results.append(1000.0)  # Large penalty

    return results
