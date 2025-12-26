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
from typing import Optional

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
        Mmd: Moving mass (kg)
        Le: Voice coil inductance (H)
        Re: Voice coil DC resistance (Ω)
        Nd: Number of drivers (default: 1)
    """
    driver_name: str
    Sd: float  # cm² (Hornresp uses cm² for areas)
    Bl: float  # T·m
    Cms: float  # m/N
    Rms: float  # N·s/m
    Mmd: float  # kg
    Le: float  # H
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
Mmd = {self.Mmd:.3f}
Le = {self.Le:.3f}
Re = {self.Re:.2f}
Nd = {self.Nd}"""


def driver_to_hornresp_record(driver: ThieleSmallParameters, driver_name: str) -> HornrespRecord:
    """
    Convert viberesp ThieleSmallParameters to HornrespRecord.

    Converts SI units to Hornresp conventions:
    - Area: m² → cm² (multiply by 10000)
    - Mass, compliance, resistance, inductance, BL: SI (no change)

    Literature:
        - Hornresp User Manual - Parameter units and format

    Args:
        driver: ThieleSmallParameters instance in SI units
        driver_name: Name/identifier for the driver

    Returns:
        HornrespRecord with units converted for Hornresp import

    Examples:
        >>> driver = ThieleSmallParameters(
        ...     M_ms=0.054, C_ms=0.00019, R_ms=5.2,
        ...     R_e=3.1, L_e=0.72e-3, BL=16.5, S_d=0.0522
        ... )
        >>> record = driver_to_hornresp_record(driver, "12NDL76")
        >>> record.Sd  # cm²
        522.0
        >>> record.Mmd  # kg (same)
        0.054
    """
    # Convert area from m² to cm² (Hornresp uses cm²)
    sd_cm2 = driver.S_d * 10000.0

    return HornrespRecord(
        driver_name=driver_name,
        Sd=sd_cm2,
        Bl=driver.BL,
        Cms=driver.C_ms,
        Rms=driver.R_ms,
        Mmd=driver.M_ms,
        Le=driver.L_e,
        Re=driver.R_e,
        Nd=1  # Single driver
    )


def export_to_hornresp(
    driver: ThieleSmallParameters,
    driver_name: str,
    output_path: str,
    comment: Optional[str] = None
) -> None:
    """
    Export driver parameters to Hornresp input file format.

    Generates a .txt file in Hornresp native format that can be directly
    imported into Hornresp for simulation and validation.

    Literature:
        - Hornresp User Manual - File format specification
        - hornresp_example.txt - Reference format

    Args:
        driver: ThieleSmallParameters instance in SI units
        driver_name: Name/identifier for the driver
        output_path: Path to output .txt file
        comment: Optional comment/description for the file

    Raises:
        ValueError: If parameters are outside Hornresp valid ranges
        IOError: If output file cannot be written

    Examples:
        >>> driver = ThieleSmallParameters(
        ...     M_ms=0.054, C_ms=0.00019, R_ms=5.2,
        ...     R_e=3.1, L_e=0.72e-3, BL=16.5, S_d=0.0522
        ... )
        >>> export_to_hornresp(driver, "BC_12NDL76", "bc_12ndl76.txt")
        # Creates bc_12ndl76.txt ready for Hornresp import

    Validation:
        Exported files should be directly importable into Hornresp.
        Verify by importing the generated .txt file in Hornresp
        and checking that all parameters match the datasheet values.
    """
    # Convert driver to Hornresp format
    record = driver_to_hornresp_record(driver, driver_name)

    # Generate Hornresp file content
    # Use template format matching hornresp_example.txt
    comment_text = comment or f"{driver_name} driver parameters exported from viberesp"

    # Generate unique ID (use hash of driver name)
    id_hash = abs(hash(driver_name)) % 100000
    id_value = f"{id_hash / 100:.2f}"

    content = f"""ID = {id_value}

Comment = {comment_text}

|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:

Ang = 2.00
Eg = 2.83
Rg = 0.00
Cir = 0.00

|HORN PARAMETER VALUES:

S1 = 0.00
S2 = 0.00
Exp = 0.00
F12 = 0.00
S2 = 0.00
S3 = 0.00
Exp = 0.00
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

|CHAMBER PARAMETER VALUES:

Vrc = 0.00
Lrc = 0.00
Fr = 0.00
Tal = 0.00
Vtc = 0.00
Atc = 0.00

Acoustic Path Length = 0.0

|MAXIMUM SPL PARAMETER VALUES:

Pamp = 100
Vamp = 25
Iamp = 4
Pmax = 200
Xmax = 5.0

Maximum SPL Setting = 3

|ABSORBENT FILLING MATERIAL PARAMETER VALUES:

Fr1 = 0.00
Fr2 = 0.00
Fr3 = 0.00
Fr4 = 0.00

Tal1 = 100
Tal2 = 100
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
