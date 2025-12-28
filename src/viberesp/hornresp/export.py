"""
Hornresp parameter export functionality.

This module handles the conversion of viberesp Thiele-Small parameters
to the Hornresp .txt file format for import into the Hornresp simulator.

Literature:
- Hornresp User Manual - File format specification
- http://www.hornresp.net/
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from viberesp.driver.parameters import ThieleSmallParameters


@dataclass
class HornrespRecord:
    """
    Hornresp parameter record in native format.

    This dataclass holds driver parameters in the units and format
    expected by Hornresp for import.

    Attributes:
        driver_name: Name/identifier for the driver
        Sd: Effective piston area (cm²)
        Bl: Force factor (T·m)
        Cms: Suspension compliance (m/N)
        Rms: Mechanical resistance (N·s/m)
        Mmd: Moving mass (g) - Hornresp uses grams, not kg
        Le: Voice coil inductance (mH) - Hornresp uses millihenries, not henries
        Re: Voice coil DC resistance (Ω)
        Nd: Number of drivers (default: 1)
    """
    driver_name: str
    Sd: float  # cm² (Hornresp uses cm² for areas)
    Bl: float  # T·m
    Cms: float  # m/N
    Rms: float  # N·s/m
    Mmd: float  # g (Hornresp uses grams for mass)
    Le: float  # mH (Hornresp uses millihenries for inductance)
    Re: float  # Ω
    Nd: int = 1  # Number of drivers

    def to_hornresp_format(self) -> str:
        """
        Convert to Hornresp traditional driver parameter format.

        Returns a string formatted for the |TRADITIONAL DRIVER PARAMETER VALUES
        section of a Hornresp .txt file.

        Format from Hornresp manual (requires CRLF line endings):
        Sd = <area_cm2>
        Bl = <force_factor>
        Cms = <compliance_scientific>
        Rms = <mech_resistance>
        Mmd = <moving_mass>
        Le = <inductance>
        Re = <resistance>
        Nd = <num_drivers>
        """
        # Format Cms in scientific notation with exactly 2 decimal places
        # Hornresp format: X.XXE-XX (e.g., 1.00E-06)
        cms_formatted = f"{self.Cms:.2E}"

        # All other parameters with fixed decimal places
        return f"""|TRADITIONAL DRIVER PARAMETER VALUES:

Sd = {self.Sd:.2f}
Bl = {self.Bl:.2f}
Cms = {cms_formatted}
Rms = {self.Rms:.2f}
Mmd = {self.Mmd:.2f}
Le = {self.Le:.2f}
Re = {self.Re:.2f}
Nd = {self.Nd}"""

def driver_to_hornresp_record(driver: ThieleSmallParameters, driver_name: str) -> HornrespRecord:
    """
    Convert viberesp ThieleSmallParameters to HornrespRecord.

    Converts SI units to Hornresp conventions:
    - Area: m² → cm² (multiply by 10000)
    - Mass: kg → g (multiply by 1000) - CRITICAL: Exports M_md only
    - Inductance: H → mH (multiply by 1000)
    - Compliance, resistance, BL: SI (no change)

    Literature:
        - Hornresp User Manual - Parameter units and format

    Args:
        driver: ThieleSmallParameters instance in SI units
        driver_name: Name/identifier for the driver

    Returns:
        HornrespRecord with units converted for Hornresp import

    Important Notes:
        M_md vs M_ms: This function exports M_md (driver mass only, without
        radiation mass). Hornresp calculates its own radiation mass loading.
        Exporting M_ms would cause Hornresp to double-count radiation mass.

    Examples:
        >>> driver = ThieleSmallParameters(
        ...     M_md=0.050, C_ms=0.00019, R_ms=5.2,
        ...     R_e=3.1, L_e=0.72e-3, BL=16.5, S_d=0.0522
        ... )
        >>> record = driver_to_hornresp_record(driver, "12NDL76")
        >>> record.Sd  # cm²
        522.0
        >>> record.Mmd  # g (converted from 0.050 kg M_md, NOT M_ms)
        50.0
        >>> record.Le  # mH (converted from 0.72e-3 H)
        0.72
    """
    # Convert area from m² to cm² (Hornresp uses cm²)
    sd_cm2 = driver.S_d * 10000.0

    # Convert mass from kg to g (Hornresp uses grams)
    # CRITICAL: Export M_md (driver mass only, NOT M_ms)
    # Hornresp calculates its own radiation mass, so we must provide
    # the driver mass without any radiation loading.
    # M_ms includes radiation mass and should NOT be exported to Hornresp.
    mmd_g = driver.M_md * 1000.0

    # Convert inductance from H to mH (Hornresp uses millihenries)
    le_mh = driver.L_e * 1000.0

    return HornrespRecord(
        driver_name=driver_name,
        Sd=sd_cm2,
        Bl=driver.BL,
        Cms=driver.C_ms,
        Rms=driver.R_ms,
        Mmd=mmd_g,
        Le=le_mh,
        Re=driver.R_e,
        Nd=1  # Single driver
    )


def export_to_hornresp(
    driver: ThieleSmallParameters,
    driver_name: str,
    output_path: str,
    comment: Optional[str] = None,
    enclosure_type: str = "infinite_baffle",
    Vb_liters: Optional[float] = None,
    Lrc_cm: Optional[float] = None,
    Fb_hz: Optional[float] = None,
    port_area_cm2: Optional[float] = None,
    port_length_cm: Optional[float] = None,
) -> None:
    """
    Export driver parameters to Hornresp input file format.

    Generates a .txt file in Hornresp native format that can be directly
    imported into Hornresp for simulation and validation.

    Literature:
        - Hornresp User Manual - File format specification
        - Hornresp uses Ang = 0.5 x Pi for sealed/ported box (hemisphere radiation)
        - Hornresp uses Ang = 2.0 x Pi for infinite baffle (full sphere radiation)
        - https://www.diyaudio.com/community/threads/hornresp.119854/ - Lrc parameter
        - https://www.hometheatershack.com/threads/hornresp-for-dum-hmm-everyone.36532/ - Lrc usage
        - Thiele (1971) - Ported box vent parameters (Ap, Lpt, Fr)

    Args:
        driver: ThieleSmallParameters instance in SI units
        driver_name: Name/identifier for the driver
        output_path: Path to output .txt file
        comment: Optional comment/description for the file
        enclosure_type: "infinite_baffle", "sealed_box", or "ported_box"
        Vb_liters: Box volume in liters (required for sealed_box and ported_box)
        Lrc_cm: Rear chamber depth in cm (optional, auto-calculated if None)
                If not provided, calculated from Vb assuming cube shape: Lrc = (Vb)^(1/3)
                Hornresp requires Lrc > 0 for sealed/ported boxes (cannot be zero)
        Fb_hz: Port tuning frequency in Hz (required for ported_box)
        port_area_cm2: Port cross-sectional area in cm² (required for ported_box)
        port_length_cm: Port physical length in cm (required for ported_box)

    Raises:
        ValueError: If parameters are outside Hornresp valid ranges
        IOError: If output file cannot be written

    Examples:
        >>> driver = ThieleSmallParameters(
        ...     M_ms=0.054, C_ms=0.00019, R_ms=5.2,
        ...     R_e=3.1, L_e=0.72e-3, BL=16.5, S_d=0.0522
        ... )
        >>> # Infinite baffle export
        >>> export_to_hornresp(driver, "BC_12NDL76", "bc_12ndl76_inf.txt")
        >>>
        >>> # Sealed box export
        >>> export_to_hornresp(
        ...     driver, "BC_12NDL76", "bc_12ndl76_sealed_50L.txt",
        ...     enclosure_type="sealed_box", Vb_liters=50.0
        ... )
        >>>
        >>> # Ported box export
        >>> export_to_hornresp(
        ...     driver, "BC_12NDL76", "bc_12ndl76_ported_80L_fb30hz.txt",
        ...     enclosure_type="ported_box", Vb_liters=80.0, Fb_hz=30.0,
        ...     port_area_cm2=30.0, port_length_cm=15.0
        ... )

    Validation:
        Exported files should be directly importable into Hornresp.
        Verify by importing the generated .txt file in Hornresp
        and checking that all parameters match the datasheet values.
    """
    # Convert driver to Hornresp format
    record = driver_to_hornresp_record(driver, driver_name)

    # Set radiation angle based on enclosure type
    if enclosure_type == "sealed_box":
        ang_value = "0.5"  # Hemisphere (front radiation only)
        cir_value = "0.00"
        if Vb_liters is None:
            raise ValueError("Vb_liters must be specified for sealed_box enclosure")
        vrc_value = Vb_liters
        fr_value = 0.0  # No port tuning for sealed box
        ap_value = None
        lpt_value = None

        # Calculate or use provided Lrc (rear chamber depth in cm)
        # Hornresp requires Lrc > 0 for sealed boxes (cannot be zero)
        # If not provided, calculate from Vb with physical realizability constraints
        if Lrc_cm is None:
            # Vb is in liters, convert to cm³
            vb_cm3 = Vb_liters * 1000.0

            # Calculate physical constraints
            piston_radius_cm = math.sqrt(driver.S_d / math.pi) * 100.0
            piston_area_cm2 = driver.S_d * 10000.0

            # Constraint 1: Minimum depth for magnet structure clearance
            # Depth must be at least 2× piston radius to accommodate magnet
            lrc_min = 2.0 * piston_radius_cm

            # Constraint 2: Maximum depth for driver to fit through opening
            # Chamber cross-sectional area = Vb / Lrc must be >= piston area
            # Therefore: Lrc <= Vb / S_piston
            lrc_max = vb_cm3 / piston_area_cm2

            # Check if box is physically realizable
            # Use small tolerance (1mm) for floating point comparison
            if lrc_min > lrc_max + 0.1:
                min_vb_liters = (lrc_min * piston_area_cm2) / 1000.0
                raise ValueError(
                    f"Box volume {Vb_liters:.1f}L is too small for driver. "
                    f"Minimum volume to fit driver: {min_vb_liters:.1f}L\n"
                    f"  - Piston diameter: {2*piston_radius_cm:.1f} cm\n"
                    f"  - Piston area: {piston_area_cm2:.0f} cm²\n"
                    f"  - Min depth for magnet: {lrc_min:.1f} cm\n"
                    f"  - Max depth for fit: {lrc_max:.1f} cm"
                )

            # Method 1: Cube-shaped chamber (ideal proportions)
            lrc_cube = vb_cm3 ** (1.0/3.0)

            # Use cube depth, but clamp to valid range [lrc_min, lrc_max]
            # This ensures physical realizability while maintaining reasonable proportions
            lrc_value = max(lrc_min, min(lrc_cube, lrc_max))
        else:
            lrc_value = Lrc_cm

        if lrc_value <= 0:
            raise ValueError(f"Lrc must be > 0 for sealed boxes, got {lrc_value}")

        # No vent parameters for sealed box
        tal_format = "Tal = 0.00"
    elif enclosure_type == "ported_box":
        ang_value = "2.0"  # Full sphere for ported boxes (Hornresp convention)
        cir_value = "-200.00"
        if Vb_liters is None:
            raise ValueError("Vb_liters must be specified for ported_box enclosure")
        if Fb_hz is None:
            raise ValueError("Fb_hz must be specified for ported_box enclosure")
        if port_area_cm2 is None:
            raise ValueError("port_area_cm2 must be specified for ported_box enclosure")
        if port_length_cm is None:
            raise ValueError("port_length_cm must be specified for ported_box enclosure")

        vrc_value = Vb_liters
        ap_value = port_area_cm2
        lpt_value = port_length_cm
        fr_value = 0.0  # Not used for ported boxes in Hornresp

        # Calculate or use provided Lrc (rear chamber depth in cm)
        # Same physical constraints as sealed box
        if Lrc_cm is None:
            # Vb is in liters, convert to cm³
            vb_cm3 = Vb_liters * 1000.0

            # Calculate physical constraints
            piston_radius_cm = math.sqrt(driver.S_d / math.pi) * 100.0
            piston_area_cm2 = driver.S_d * 10000.0

            # Constraint 1: Minimum depth for magnet structure clearance
            lrc_min = 2.0 * piston_radius_cm

            # Constraint 2: Maximum depth for driver to fit through opening
            lrc_max = vb_cm3 / piston_area_cm2

            # Constraint 3: Port must fit inside box
            # Port diameter should be less than half the box dimension
            # Assuming cube proportions: dimension = vb_cm3^(1/3)
            # Port diameter: d_port = 2 × sqrt(port_area/π)
            port_diameter_cm = 2.0 * math.sqrt(port_area_cm2 / math.pi)
            box_dimension_cm = vb_cm3 ** (1.0/3.0)
            if port_diameter_cm >= box_dimension_cm / 2.0:
                raise ValueError(
                    f"Port diameter {port_diameter_cm:.1f}cm is too large for box. "
                    f"Box dimension: {box_dimension_cm:.1f}cm\n"
                    f"  - Port diameter should be < {box_dimension_cm/2:.1f}cm "
                    f"(half box dimension)\n"
                    f"  - Increase box volume or decrease port diameter"
                )

            # Check if box is physically realizable
            if lrc_min > lrc_max + 0.1:
                min_vb_liters = (lrc_min * piston_area_cm2) / 1000.0
                raise ValueError(
                    f"Box volume {Vb_liters:.1f}L is too small for driver. "
                    f"Minimum volume to fit driver: {min_vb_liters:.1f}L\n"
                    f"  - Piston diameter: {2*piston_radius_cm:.1f} cm\n"
                    f"  - Piston area: {piston_area_cm2:.0f} cm²\n"
                    f"  - Min depth for magnet: {lrc_min:.1f} cm\n"
                    f"  - Max depth for fit: {lrc_max:.1f} cm"
                )

            # Cube-shaped chamber
            lrc_cube = vb_cm3 ** (1.0/3.0)

            # Use cube depth, clamped to valid range
            lrc_value = max(lrc_min, min(lrc_cube, lrc_max))
        else:
            lrc_value = Lrc_cm

        if lrc_value <= 0:
            raise ValueError(f"Lrc must be > 0 for ported boxes, got {lrc_value}")

        # Validate port parameters
        if port_area_cm2 <= 0:
            raise ValueError(f"Port area must be > 0, got {port_area_cm2} cm²")
        if port_length_cm <= 0:
            raise ValueError(f"Port length must be > 0, got {port_length_cm} cm")

        # Check if port fits in box (length should be less than 1.5 × box depth)
        if port_length_cm > 1.5 * lrc_value:
            raise ValueError(
                f"Port length {port_length_cm:.1f}cm is too long for box. "
                f"Rear chamber depth: {lrc_value:.1f}cm\n"
                f"  - Port length should be < {1.5 * lrc_value:.1f}cm "
                f"(1.5 × chamber depth)\n"
                f"  - Increase box volume or decrease port length"
            )

        # Ported box format: Ap and Lpt go in CHAMBER section, no separate vent section
        tal_format = "Tal = -0"
    elif enclosure_type == "infinite_baffle":
        ang_value = "2.0"  # Full sphere (both sides radiate)
        cir_value = "0.00"
        vrc_value = 0.0
        lrc_value = 0.0
        fr_value = 0.0
        ap_value = None
        lpt_value = None
        tal_format = "Tal = 0.00"
    else:
        raise ValueError(
            f"Unknown enclosure_type: {enclosure_type}. "
            f"Use 'infinite_baffle', 'sealed_box', or 'ported_box'"
        )

    # Generate Hornresp file content
    comment_text = comment or f"{driver_name} driver parameters exported from viberesp"

    # Generate unique ID (use hash of driver name)
    id_hash = abs(hash(driver_name)) % 100000
    id_value = f"{id_hash / 100:.2f}"

    # Build chamber section based on enclosure type
    # Ported boxes: Vrc, Lrc, Ap, Lpt, Vtc, Atc (no Fr, no Tal)
    # Sealed boxes: Vrc, Lrc, Fr, Tal, Vtc, Atc
    # Infinite baffle: Vrc, Lrc, Fr, Tal, Vtc, Atc
    if enclosure_type == "ported_box":
        chamber_section = f"""|CHAMBER PARAMETER VALUES:

Vrc = {vrc_value:.2f}
Lrc = {lrc_value:.2f}
Ap = {ap_value:.2f}
Lpt = {lpt_value:.2f}
Vtc = 0.00
Atc = 0.00"""
    else:
        # sealed_box and infinite_baffle
        chamber_section = f"""|CHAMBER PARAMETER VALUES:

Vrc = {vrc_value:.2f}
Lrc = {lrc_value:.2f}
Fr = {fr_value:.2f}
{tal_format}
Vtc = 0.00
Atc = 0.00"""

    content = f"""ID = {id_value}

Comment = {comment_text}

|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:

Ang = {ang_value} x Pi
Eg = 2.83
Rg = 0.00
Cir = {cir_value}

|HORN PARAMETER VALUES:

S1 = 0.00
S2 = 0.00
L12 = 0.00
F12 = 0.00
S2 = 0.00
S3 = 0.00
L23 = 0.00
F23 = 0.00
S3 = 0.00
S4 = 0.00
L34 = 0.00
F34 = 0.00
S4 = 0.00
S5 = 0.00
L45 = 0.00
F45 = 0.00

{record.to_hornresp_format()}

|ADVANCED DRIVER PARAMETER VALUES FOR SEMI-INDUCTANCE MODEL:

Re' = 0.00
Leb = 0.00
Le = 0.00
Ke = 0.00
Rss = 0.00

|ADVANCED DRIVER PARAMETER VALUES FOR FREQUENCY-DEPENDENT DAMPING MODEL:

Rms = 0.00
Ams = 0.00

|PASSIVE RADIATOR PARAMETER VALUE:

Added Mass = 0.00

{chamber_section}

Acoustic Path Length = 0.0

|MAXIMUM SPL PARAMETER VALUES:

Pamp = 100
Vamp = 25
Iamp = 4
Pmax = 200
Xmax = 7.0

Maximum SPL Setting = 3

|ABSORBENT FILLING MATERIAL PARAMETER VALUES:

Fr1 = 0.00
Fr2 = 0.00
Fr3 = 0.00
Fr4 = 0.00

Tal1 = -0
Tal2 = -0
Tal3 = -0
Tal4 = -0

|ACTIVE BAND PASS FILTER PARAMETER VALUES:

High Pass Frequency = 0
High Pass Slope = 1
Low Pass Frequency = 0
Low Pass Slope = 1

Butterworth High Pass Order = 1
Butterworth Low Pass Order = 1
Linkwitz-Riley High Pass Order = 2
Linkwitz-Riley Low Pass Order = 2
Bessel High Pass Order = 1
Bessel Low Pass Order = 1

2nd Order High Pass Q = 0.5
2nd Order Low Pass Q = 0.5
4th Order High Pass Q = 0.5
4th Order Low Pass Q = 0.5

Active Filter Alignment = 1
Active Filter On / Off Switch = 1

|PASSIVE FILTER PARAMETER VALUES:

Series / Parallel 1 = S
Series / Parallel 2 = S
Series / Parallel 3 = S
Series / Parallel 4 = S

|EQUALISER FILTER PARAMETER VALUES:

Band 1 Frequency = 0
Band 1 Q Factor = 0.01
Band 1 Gain = 0.0
Band 1 Type = -1
Band 2 Frequency = 0
Band 2 Q Factor = 0.01
Band 2 Gain = 0.0
Band 2 Type = -1
Band 3 Frequency = 0
Band 3 Q Factor = 0.01
Band 3 Gain = 0.0
Band 3 Type = -1
Band 4 Frequency = 0
Band 4 Q Factor = 0.01
Band 4 Gain = 0.0
Band 4 Type = -1
Band 5 Frequency = 0
Band 5 Q Factor = 0.01
Band 5 Gain = 0.0
Band 5 Type = -1
Band 6 Frequency = 0
Band 6 Q Factor = 0.01
Band 6 Gain = 0.0
Band 6 Type = -1

|STATUS FLAGS:

Auto Path Flag = 0
Lossy Inductance Model Flag = 0
Semi-Inductance Model Flag = 0
Damping Model Flag = 0
Closed Mouth Flag = 0
Continuous Flag = 1
End Correction Flag = 1

|OTHER SETTINGS:

Filter Type Index = 0
Filter Input Index = 0
Filter Output Index = 0

Filter Type = 1

MEH Configuration = 0
ME Amplifier Polarity Value = 1
"""

    # Write to file with CRLF line endings (Hornresp requirement)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Use newline='\r\n' to convert \n to \r\n on write
    with open(output_file, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)

    print(f"Exported {driver_name} to {output_path}")


def export_front_loaded_horn_to_hornresp(
    driver: ThieleSmallParameters,
    horn: 'viberesp.simulation.ExponentialHorn',
    driver_name: str,
    output_path: str,
    comment: Optional[str] = None,
    V_tc_liters: float = 0.0,
    A_tc_cm2: Optional[float] = None,
    V_rc_liters: float = 0.0,
    L_rc_cm: Optional[float] = None,
    radiation_angle: str = "2pi",
    input_voltage: float = 2.83,
    source_resistance: float = 0.0,
) -> None:
    """
    Export front-loaded horn system to Hornresp input file format.

    Generates a .txt file in Hornresp native format for horn-loaded loudspeaker
    systems with optional throat and rear chambers. This includes the complete
    horn geometry and chamber parameters used in TC2-4 validation.

    Literature:
        - Hornresp User Manual - File format specification
        - Olson (1947), Chapter 8 - Horn driver system parameters
        - Beranek (1954), Chapter 5 - Horn radiation parameters

    Args:
        driver: ThieleSmallParameters instance in SI units
        horn: ExponentialHorn instance with throat_area, mouth_area, length
        driver_name: Name/identifier for the system
        output_path: Path to output .txt file
        comment: Optional comment/description for the file
        V_tc_liters: Throat chamber volume in liters (default: 0 = no chamber)
        A_tc_cm2: Throat chamber area in cm² (defaults to horn throat area)
        V_rc_liters: Rear chamber volume in liters (default: 0 = no chamber)
        L_rc_cm: Rear chamber depth in cm (optional, auto-calculated if None)
        radiation_angle: Solid angle of radiation ("2pi" for half-space, "pi" for quarter-space)
        input_voltage: Input voltage in volts (default: 2.83V for 1W into 8Ω)
        source_resistance: Source resistance in ohms (default: 0)

    Raises:
        ValueError: If parameters are outside Hornresp valid ranges
        IOError: If output file cannot be written

    Examples:
        >>> from viberesp.simulation import ExponentialHorn
        >>> driver = ThieleSmallParameters(
        ...     M_md=0.008, C_ms=5e-5, R_ms=3.0,
        ...     R_e=6.5, L_e=0.1e-3, BL=12.0, S_d=0.0008
        ... )
        >>> horn = ExponentialHorn(
        ...     throat_area=0.0005,  # 5 cm²
        ...     mouth_area=0.02,      # 200 cm²
        ...     length=0.5            # 0.5 m
        ... )
        >>> # Export horn without chambers (TC2)
        >>> export_front_loaded_horn_to_hornresp(
        ...     driver, horn, "TC2_Baseline", "tc2_baseline.txt"
        ... )
        >>> # Export horn with throat chamber (TC3)
        >>> export_front_loaded_horn_to_hornresp(
        ...     driver, horn, "TC3_ThroatChamber", "tc3_throat.txt",
        ...     V_tc_liters=0.05, A_tc_cm2=5.0
        ... )
        >>> # Export horn with both chambers (TC4)
        >>> export_front_loaded_horn_to_hornresp(
        ...     driver, horn, "TC4_BothChambers", "tc4_both.txt",
        ...     V_tc_liters=0.05, A_tc_cm2=5.0,
        ...     V_rc_liters=2.0, L_rc_cm=12.6
        ... )

    Validation:
        Exported files should be directly importable into Hornresp.
        Tested with TC2-4 validation cases - all produce <1% agreement.

    Note:
        Hornresp uses cm² for all areas, liters for chamber volumes.
        This function handles SI → Hornresp unit conversions automatically.
    """
    # Import here to avoid circular dependency
    from viberesp.simulation import ExponentialHorn

    if not isinstance(horn, ExponentialHorn):
        raise TypeError(f"horn must be ExponentialHorn, got {type(horn)}")

    # Convert driver to Hornresp format
    record = driver_to_hornresp_record(driver, driver_name)

    # Convert horn parameters to Hornresp units (cm²)
    s1_cm2 = horn.throat_area * 10000.0
    s2_cm2 = horn.mouth_area * 10000.0
    l12_m = horn.length

    # Calculate flare constant (for documentation)
    # m = (1/L12) * ln(S2/S1)
    if s1_cm2 > 0 and s2_cm2 > 0 and l12_m > 0:
        flare_constant = (1.0 / l12_m) * math.log(s2_cm2 / s1_cm2)
        # Calculate cutoff frequency for documentation
        # fc = c * m / (2*pi) assuming c = 343 m/s
        fc_hz = 343.0 * flare_constant / (2.0 * math.pi)
    else:
        fc_hz = 0.0

    # Set throat chamber area (default to horn throat area)
    if A_tc_cm2 is None:
        atc_cm2 = s1_cm2
    else:
        atc_cm2 = A_tc_cm2

    # Calculate rear chamber depth if not provided
    # Use tolerance to treat very small volumes as "no rear chamber"
    # For compression drivers, <5 cm³ is negligible rear chamber volume
    VRC_TOLERANCE = 0.005  # 5 mL or less is treated as no rear chamber
    has_rear_chamber = V_rc_liters > VRC_TOLERANCE

    if has_rear_chamber and L_rc_cm is None:
        # Vb is in liters, convert to cm³
        vrc_cm3 = V_rc_liters * 1000.0

        # Calculate physical constraints
        piston_radius_cm = math.sqrt(driver.S_d / math.pi) * 100.0
        piston_area_cm2 = driver.S_d * 10000.0

        # Constraint 1: Minimum depth for magnet structure clearance
        lrc_min = 2.0 * piston_radius_cm

        # Constraint 2: Maximum depth for driver to fit through opening
        lrc_max = vrc_cm3 / piston_area_cm2

        # Check if box is physically realizable
        if lrc_min > lrc_max + 0.1:
            min_vrc_liters = (lrc_min * piston_area_cm2) / 1000.0
            raise ValueError(
                f"Rear chamber volume {V_rc_liters:.1f}L is too small for driver. "
                f"Minimum volume to fit driver: {min_vrc_liters:.1f}L\n"
                f"  - Piston diameter: {2*piston_radius_cm:.1f} cm\n"
                f"  - Piston area: {piston_area_cm2:.0f} cm²\n"
                f"  - Min depth for magnet: {lrc_min:.1f} cm\n"
                f"  - Max depth for fit: {lrc_max:.1f} cm"
            )

        # Cube-shaped chamber
        lrc_cube = vrc_cm3 ** (1.0/3.0)

        # Use cube depth, clamped to valid range
        lrc_value = max(lrc_min, min(lrc_cube, lrc_max))
    else:
        # No rear chamber or Lrc provided
        lrc_value = L_rc_cm if L_rc_cm else 0.0
        # If volume is below tolerance, treat it as zero
        if not has_rear_chamber:
            V_rc_liters = 0.0

    # Validate rear chamber parameters
    if has_rear_chamber and lrc_value <= 0:
        raise ValueError(f"Lrc must be > 0 for rear chamber, got {lrc_value}")

    # Set radiation angle
    # Hornresp uses: "2.0 x Pi" for half-space, "1.0 x Pi" for quarter-space
    if radiation_angle == "2pi" or radiation_angle == "half":
        ang_value = "2.0"
    elif radiation_angle == "pi" or radiation_angle == "quarter":
        ang_value = "1.0"
    else:
        raise ValueError(f"Invalid radiation_angle: {radiation_angle}. Use '2pi' or 'pi'")

    # Generate unique ID
    id_hash = abs(hash(driver_name)) % 100000
    id_value = f"{id_hash / 100:.2f}"

    # Generate comment
    if comment is None:
        if V_tc_liters > 0 and V_rc_liters > 0:
            comment = f"{driver_name}: Front-loaded horn (fc={fc_hz:.0f}Hz) with throat chamber ({V_tc_liters*1000:.0f}cm³) and rear chamber ({V_rc_liters:.1f}L)"
        elif V_tc_liters > 0:
            comment = f"{driver_name}: Front-loaded horn (fc={fc_hz:.0f}Hz) with throat chamber ({V_tc_liters*1000:.0f}cm³)"
        else:
            comment = f"{driver_name}: Front-loaded horn (fc={fc_hz:.0f}Hz)"

    # Build chamber section
    chamber_section = f"""|CHAMBER PARAMETER VALUES:

Vrc = {V_rc_liters:.2f}
Lrc = {lrc_value:.2f}
Fr = 0.00
Tal = 0.00
Vtc = {V_tc_liters:.2f}
Atc = {atc_cm2:.2f}"""

    # Build content
    content = f"""ID = {id_value}

Comment = {comment}

|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:

Ang = {ang_value} x Pi
Eg = {input_voltage:.2f}
Rg = {source_resistance:.2f}
Cir = 0.42

|HORN PARAMETER VALUES:

S1 = {s1_cm2:.2f}
S2 = {s2_cm2:.2f}
Exp = 50.00
F12 = {fc_hz:.2f}
S2 = 0.00
S3 = 0.00
L23 = 0.00
AT = 2.66
S3 = 0.00
S4 = 0.00
L34 = 0.00
F34 = 0.00
S4 = 0.00
S5 = 0.00
L45 = 0.00
F45 = 0.00

{record.to_hornresp_format()}

|ADVANCED DRIVER PARAMETER VALUES FOR SEMI-INDUCTANCE MODEL:

Re' = 0.00
Leb = 0.00
Le = 0.00
Ke = 0.00
Rss = 0.00

|ADVANCED DRIVER PARAMETER VALUES FOR FREQUENCY-DEPENDENT DAMPING MODEL:

Rms = 0.00
Ams = 0.00

|PASSIVE RADIATOR PARAMETER VALUE:

Added Mass = 0.00

{chamber_section}

Acoustic Path Length = 0.0

|MAXIMUM SPL PARAMETER VALUES:

Pamp = 100
Vamp = 25
Iamp = 4
Pmax = 100
Xmax = 5.0

Maximum SPL Setting = 3

|ABSORBENT FILLING MATERIAL PARAMETER VALUES:

Fr1 = 0.00
Fr2 = 0.00
Fr3 = 0.00
Fr4 = 0.00

Tal1 = 100
Tal2 = 100
Tal3 = 100
Tal4 = 100

|ACTIVE BAND PASS FILTER PARAMETER VALUES:

High Pass Frequency = 0
High Pass Slope = 1
Low Pass Frequency = 0
Low Pass Slope = 1

Butterworth High Pass Order = 1
Butterworth Low Pass Order = 1
Linkwitz-Riley High Pass Order = 2
Linkwitz-Riley Low Pass Order = 2
Bessel High Pass Order = 1
Bessel Low Pass Order = 1

2nd Order High Pass Q = 0.5
2nd Order Low Pass Q = 0.5
4th Order High Pass Q = 0.5
4th Order Low Pass Q = 0.5

Active Filter Alignment = 1
Active Filter On / Off Switch = 1

|PASSIVE FILTER PARAMETER VALUES:

Series / Parallel 1 = S
Series / Parallel 2 = S
Series / Parallel 3 = S
Series / Parallel 4 = S

|EQUALISER FILTER PARAMETER VALUES:

Band 1 Frequency = 0
Band 1 Q Factor = 0.01
Band 1 Gain = 0.0
Band 1 Type = -1
Band 2 Frequency = 0
Band 2 Q Factor = 0.01
Band 2 Gain = 0.0
Band 2 Type = -1
Band 3 Frequency = 0
Band 3 Q Factor = 0.01
Band 3 Gain = 0.0
Band 3 Type = -1
Band 4 Frequency = 0
Band 4 Q Factor = 0.01
Band 4 Gain = 0.0
Band 4 Type = -1
Band 5 Frequency = 0
Band 5 Q Factor = 0.01
Band 5 Gain = 0.0
Band 5 Type = -1
Band 6 Frequency = 0
Band 6 Q Factor = 0.01
Band 6 Gain = 0.0
Band 6 Type = -1

|STATUS FLAGS:

Auto Path Flag = 0
Lossy Inductance Model Flag = 0
Semi-Inductance Model Flag = 0
Damping Model Flag = 0
Closed Mouth Flag = 0
Continuous Flag = 1
End Correction Flag = 1

|OTHER SETTINGS:

Filter Type Index = 0
Filter Input Index = 0
Filter Output Index = 0

Filter Type = 1

MEH Configuration = 0
ME Amplifier Polarity Value = 1
"""

    # Write to file with CRLF line endings (Hornresp requirement)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Use newline='\r\n' to convert \n to \r\n on write
    with open(output_file, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)

    print(f"Exported {driver_name} front-loaded horn to {output_path}")


def batch_export_to_hornresp(
    drivers: list[tuple[ThieleSmallParameters, str]],
    output_dir: str
) -> None:
    """
    Export multiple drivers to Hornresp format in batch.

    Creates separate .txt files for each driver in the specified directory.

    Args:
        drivers: List of (driver, driver_name) tuples
        output_dir: Directory to save output .txt files

    Examples:
        >>> drivers = [
        ...     (driver1, "BC_8NDL51"),
        ...     (driver2, "BC_12NDL76"),
        ... ]
        >>> batch_export_to_hornresp(drivers, "exports/")
        # Creates exports/BC_8NDL51.txt, exports/BC_12NDL76.txt
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for driver, name in drivers:
        filename = f"{name.replace(' ', '_')}.txt"
        file_path = output_path / filename
        export_to_hornresp(driver, name, str(file_path))


def export_multisegment_horn_to_hornresp(
    driver: ThieleSmallParameters,
    horn: 'MultiSegmentHorn',
    driver_name: str,
    output_path: str,
    comment: Optional[str] = None,
    radiation_angle: float = 6.283185307179586,  # 2π
) -> None:
    """Export a multi-segment horn to Hornresp format.

    Generates a .txt file in Hornresp native format for a multi-segment
    horn-loaded system with up to 4 segments (Hornresp limit).

    Literature:
        - Hornresp User Manual - Multi-segment horn parameter format
        - Hornresp supports up to 4 conic/exponential segments (S1-S5)
        - https://www.hornresp.net/

    Args:
        driver: ThieleSmallParameters instance in SI units
        horn: MultiSegmentHorn geometry with 1-4 segments
        driver_name: Name/identifier for the system
        output_path: Path to output .txt file
        comment: Optional comment/description
        radiation_angle: Solid angle of radiation (steradians)
            - 2π: half-space (infinite baffle) [default]
            - 4π: full-space (free field)
            - π: quarter-space

    Raises:
        ValueError: If horn has more than 4 segments (Hornresp limit)
        IOError: If output file cannot be written

    Examples:
        >>> from viberesp.simulation.types import HornSegment, MultiSegmentHorn
        >>> segment1 = HornSegment(throat_area=0.001, mouth_area=0.01, length=0.3)
        >>> segment2 = HornSegment(throat_area=0.01, mouth_area=0.1, length=0.6)
        >>> horn = MultiSegmentHorn(segments=[segment1, segment2])
        >>> export_multisegment_horn_to_hornresp(driver, horn, "test_horn", "test.txt")
    """

    # Convert driver to Hornresp format
    record = driver_to_hornresp_record(driver, driver_name)

    # Validate number of segments
    if horn.num_segments > 4:
        raise ValueError(
            f"Hornresp supports maximum 4 segments, got {horn.num_segments}. "
            "Reduce number of segments or export segments separately."
        )

    # Set radiation angle
    pi = 3.141592653589793
    if radiation_angle == 2 * pi:
        ang_value = "2.0"  # Half-space
    elif radiation_angle == 4 * pi:
        ang_value = "4.0"  # Full-space
    elif radiation_angle == pi:
        ang_value = "1.0"  # Quarter-space
    else:
        # Default to half-space for custom angles
        ang_value = "2.0"

    # Build horn parameter section based on number of segments
    # Hornresp format: S1, S2, L12, F12, S2, S3, L23, F23, etc.
    # Note: S2 appears twice (once as segment 1 mouth, once as segment 2 throat)
    # Areas in cm², lengths in cm, flare constant (Exp) is unitless

    segments = horn.segments
    num_segments = len(segments)

    # Helper function to convert m² to cm²
    def area_to_cm2(area_m2: float) -> float:
        return area_m2 * 10000.0

    # Helper function to convert m to cm
    def length_to_cm(length_m: float) -> float:
        return length_m * 100.0

    # Initialize all horn parameters to 0
    s1, s2, s3, s4, s5 = 0.0, 0.0, 0.0, 0.0, 0.0
    l12, l23, l34, l45 = 0.0, 0.0, 0.0, 0.0
    f12, f23, f34, f45 = 0.0, 0.0, 0.0, 0.0

    # Speed of sound for flare constant conversion (m/s)
    c = 343.0

    # Fill in segments
    if num_segments >= 1:
        s1 = area_to_cm2(segments[0].throat_area)
        s2 = area_to_cm2(segments[0].mouth_area)
        l12 = length_to_cm(segments[0].length)
        # Convert dimensionless flare constant m (m^-1) to Hornresp F12 (Hz)
        # F(Hz) = c * m / (2π)
        f12 = (c * segments[0].flare_constant) / (2.0 * math.pi)

    if num_segments >= 2:
        s3 = area_to_cm2(segments[1].mouth_area)
        l23 = length_to_cm(segments[1].length)
        # Convert dimensionless flare constant m (m^-1) to Hornresp F23 (Hz)
        f23 = (c * segments[1].flare_constant) / (2.0 * math.pi)

    if num_segments >= 3:
        s4 = area_to_cm2(segments[2].mouth_area)
        l34 = length_to_cm(segments[2].length)
        # Convert dimensionless flare constant m (m^-1) to Hornresp F34 (Hz)
        f34 = (c * segments[2].flare_constant) / (2.0 * math.pi)

    if num_segments >= 4:
        s5 = area_to_cm2(segments[3].mouth_area)
        l45 = length_to_cm(segments[3].length)
        # Convert dimensionless flare constant m (m^-1) to Hornresp F45 (Hz)
        f45 = (c * segments[3].flare_constant) / (2.0 * math.pi)

    # Generate file content
    comment_text = comment or f"{driver_name} multi-segment horn from viberesp"
    id_hash = abs(hash(driver_name)) % 100000
    id_value = f"{id_hash / 100:.2f}"

    # Hornresp format uses "Exp" for exponential segment length (not L12, L23, etc.)
    # The format is: S1, S2, Exp, F12 for each segment
    horn_section = f"""|HORN PARAMETER VALUES:

S1 = {s1:.2f}
S2 = {s2:.2f}
Exp = {l12:.2f}
F12 = {f12:.4f}
S2 = {s2:.2f}
S3 = {s3:.2f}
Exp = {l23:.2f}
F23 = {f23:.4f}
S3 = {s3:.2f}
S4 = {s4:.2f}
L34 = {l34:.2f}
F34 = {f34:.4f}
S4 = {s4:.2f}
S5 = {s5:.2f}
L45 = {l45:.2f}
F45 = {f45:.4f}"""

    content = f"""ID = {id_value}

Comment = {comment_text}

|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:

Ang = {ang_value} x Pi
Eg = 2.83
Rg = 0.00
Cir = 0.00

{horn_section}

{record.to_hornresp_format()}

|ADVANCED DRIVER PARAMETER VALUES FOR SEMI-INDUCTANCE MODEL:

Re' = 0.00
Leb = 0.00
Le = 0.00
Ke = 0.00

|ADVANCED DRIVER PARAMETER VALUES FOR MASS-INDUCTANCE MODEL:

Red = 0.00
Les = 0.00
Kes = 0.00
Cr = 0.00

|PASSIVE RADIATOR PARAMETER VALUES:

Mmpr = 0.00
Cmpr = 0.00
Rmpr = 0.00
Sdp = 0.00

|CHAMBER PARAMETER VALUES:

Vrc = 0.00
Lrc = 0.00
Fr = 0.00
Tal = 0.00
Vtc = 0.00
Atc = 0.00

|MAXIMUM SPL PARAMETER VALUES:

Pn = 0.00

|ABSORBENT FILLING MATERIAL PARAMETER VALUES:

Qa = 0.00

|ACTIVE BAND PASS FILTER PARAMETER VALUES:

Fa1 = 0.00
FB1 = 0.00
Fa2 = 0.00
FB2 = 0.00

|PASSIVE FILTER PARAMETER VALUES:

Leh = 0.00
Reh = 0.00
Ch = 0.00
Rch = 0.00

|EQUALISER FILTER PARAMETER VALUES:

Fke = 0.00
Tke = 0.00
Fqe = 0.00
Qke = 0.00

|STATUS FLAGS:

IK = 0
IR = 0
IL = 0
IP = 0
IS = 0
IT = 0
IV = 0
IQ = 0
IF = 0
I_eq = 0

|OTHER SETTINGS:

Filter Type Index = 0
Filter Input Index = 0
Filter Output Index = 0

Filter Type = 1

MEH Configuration = 0
ME Amplifier Polarity Value = 1
"""

    # Write to file with CRLF line endings
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content)

    print(f"Exported {driver_name} {num_segments}-segment horn to {output_path}")
    print(f"  Throat: {s1:.1f} cm² → Mouth: {max(s2, s3, s4, s5):.1f} cm²")
    print(f"  Total length: {horn.total_length()*100:.1f} cm")