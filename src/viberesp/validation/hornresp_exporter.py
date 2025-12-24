"""Export Viberesp parameters to Hornresp format.

This module generates Hornresp-compatible parameter files from Viberesp
driver and enclosure parameters for easy import into Hornresp.
"""

import math
from pathlib import Path
from typing import Dict, Optional, Tuple

from viberesp.core.models import ThieleSmallParameters


def _calculate_cms_from_vas(vas_liters: float, sd_cm2: float) -> float:
    """Calculate mechanical compliance Cms from Vas and Sd.

    Formula: Cms = Vas / (ρ₀ × c² × Sd²)

    Args:
        vas_liters: Equivalent compliance volume in liters
        sd_cm2: Diaphragm area in cm²

    Returns:
        Cms in m/N
    """
    rho = 1.18  # air density kg/m³
    c = 343.5   # speed of sound m/s

    # Convert to SI units
    vas_m3 = vas_liters / 1000
    sd_m2 = sd_cm2 / 10000

    # Calculate Cms
    cms = vas_m3 / (rho * c**2 * sd_m2**2)
    return cms


def export_hornresp_params(
    driver: ThieleSmallParameters,
    params: Dict,
    enclosure_type: str,
    output_path: str,
    comment: Optional[str] = None
) -> None:
    """Export Viberesp parameters to Hornresp format.

    Generates a complete Hornresp parameter file with all sections.
    Auto-calculates Cms from Vas/Sd if missing. Requires Mmd field.

    Args:
        driver: Thiele-Small driver parameters
        params: Dictionary of enclosure parameters from CLI
        enclosure_type: Type of enclosure ('sealed', 'ported', 'exponential_horn', etc.)
        output_path: Path for output file
        comment: Optional description for Comment field

    Raises:
        ValueError: If required Mmd field is missing
    """
    # Auto-calculate Cms from Vas and Sd if missing
    if driver.cms is None:
        if driver.vas is None or driver.sd is None:
            raise ValueError(
                "Driver missing Cms (mechanical compliance) and cannot auto-calculate. "
                "Add either Cms using: viberesp driver add <name> --cms <value> "
                "or ensure Vas and Sd are present."
            )
        driver.cms = _calculate_cms_from_vas(driver.vas, driver.sd * 10000)

    # Validate required fields
    if driver.mms is None:
        raise ValueError(
            "Driver missing Mmd (moving mass). "
            "Add Mmd using: viberesp driver add <name> --mms <value>"
        )

    # Build file contents
    lines = []

    # Header
    lines.append(f"ID = 55.30")
    lines.append("")
    if comment:
        lines.append(f"Comment = {comment}")
    else:
        lines.append(f"Comment = {enclosure_type}")
    lines.append("")

    # Radiation and source parameters
    lines.append("|RADIATION, SOURCE AND MOUTH PARAMETER VALUES:")
    lines.append("")
    lines.append("Ang = 0.5 x Pi")
    lines.append("Eg = 2.83")
    lines.append("Rg = 0.00")
    lines.append("Cir = 0.00")
    lines.append("")

    # Horn parameters
    lines.append("|HORN PARAMETER VALUES:")
    lines.append("")
    horn_lines = _get_horn_parameters(params, enclosure_type)
    for key, value in horn_lines:
        lines.append(f"{key} = {value}")
    lines.append("")

    # Traditional driver parameters
    lines.append("|TRADITIONAL DRIVER PARAMETER VALUES:")
    lines.append("")
    driver_params = _get_driver_parameters(driver)
    for key, value in driver_params.items():
        lines.append(f"{key} = {value}")
    lines.append("")

    # Advanced driver parameters (semi-inductance model)
    lines.append("|ADVANCED DRIVER PARAMETER VALUES FOR SEMI-INDUCTANCE MODEL:")
    lines.append("")
    lines.append("Re' = 0.00")
    lines.append("Leb = 0.00")
    lines.append("Le = 0.00")
    lines.append("Ke = 0.00")
    lines.append("Rss = 0.00")
    lines.append("")

    # Advanced driver parameters (damping model)
    lines.append("|ADVANCED DRIVER PARAMETER VALUES FOR FREQUENCY-DEPENDENT DAMPING MODEL:")
    lines.append("")
    lines.append("Rms = 0.00")
    lines.append("Ams = 0.00")
    lines.append("")

    # Passive radiator
    lines.append("|PASSIVE RADIATOR PARAMETER VALUE:")
    lines.append("")
    lines.append("Added Mass = 0.00")
    lines.append("")

    # Chamber parameters
    lines.append("|CHAMBER PARAMETER VALUES:")
    lines.append("")
    chamber_params = _get_chamber_parameters(params, enclosure_type)
    for key, value in chamber_params.items():
        lines.append(f"{key} = {value}")
    lines.append("")
    lines.append("Acoustic Path Length = 0.0")
    lines.append("")

    # Maximum SPL parameters
    lines.append("|MAXIMUM SPL PARAMETER VALUES:")
    lines.append("")
    lines.append(f"Pamp = {int(driver.pe) if driver.pe else 100}")
    lines.append(f"Vamp = 25")
    lines.append(f"Iamp = 4")
    lines.append(f"Pmax = {int(driver.pe) if driver.pe else 100}")
    lines.append(f"Xmax = {driver.xmax if driver.xmax else 0.0}")
    lines.append("")
    lines.append("Maximum SPL Setting = 3")
    lines.append("")

    # Absorbent filling material
    lines.append("|ABSORBENT FILLING MATERIAL PARAMETER VALUES:")
    lines.append("")
    lines.append("Fr1 = 0.00")
    lines.append("Fr2 = 0.00")
    lines.append("Fr3 = 0.00")
    lines.append("Fr4 = 0.00")
    lines.append("")
    lines.append("Tal1 = 100")
    lines.append("Tal2 = 100")
    lines.append("Tal3 = -0")
    lines.append("Tal4 = -0")
    lines.append("")

    # Active band pass filter parameters
    lines.append("|ACTIVE BAND PASS FILTER PARAMETER VALUES:")
    lines.append("")
    lines.append("High Pass Frequency = 0")
    lines.append("High Pass Slope = 1")
    lines.append("Low Pass Frequency = 0")
    lines.append("Low Pass Slope = 1")
    lines.append("")
    lines.append("Butterworth High Pass Order = 1")
    lines.append("Butterworth Low Pass Order = 1")
    lines.append("Linkwitz-Riley High Pass Order = 2")
    lines.append("Linkwitz-Riley Low Pass Order = 2")
    lines.append("Bessel High Pass Order = 1")
    lines.append("Bessel Low Pass Order = 1")
    lines.append("")
    lines.append("2nd Order High Pass Q = 0.5")
    lines.append("2nd Order Low Pass Q = 0.5")
    lines.append("4th Order High Pass Q = 0.5")
    lines.append("4th Order Low Pass Q = 0.5")
    lines.append("")
    lines.append("Active Filter Alignment = 1")
    lines.append("Active Filter On / Off Switch = 1")
    lines.append("")

    # Passive filter parameters
    lines.append("|PASSIVE FILTER PARAMETER VALUES:")
    lines.append("")
    lines.append("Series / Parallel 1 = S")
    lines.append("Series / Parallel 2 = S")
    lines.append("Series / Parallel 3 = S")
    lines.append("Series / Parallel 4 = S")
    lines.append("")

    # Equalizer filter parameters
    lines.append("|EQUALISER FILTER PARAMETER VALUES:")
    lines.append("")
    for i in range(1, 7):
        lines.append(f"Band {i} Frequency = 0")
        lines.append(f"Band {i} Q Factor = 0.01")
        lines.append(f"Band {i} Gain = 0.0")
        lines.append(f"Band {i} Type = -1")
    lines.append("")

    # Status flags
    lines.append("|STATUS FLAGS:")
    lines.append("")
    lines.append("Auto Path Flag = 0")
    lines.append("Lossy Inductance Model Flag = 0")
    lines.append("Semi-Inductance Model Flag = 0")
    lines.append("Damping Model Flag = 0")
    lines.append("Closed Mouth Flag = 0")
    lines.append("Continuous Flag = 1")
    lines.append("End Correction Flag = 1")
    lines.append("")

    # Other settings
    lines.append("|OTHER SETTINGS:")
    lines.append("")
    lines.append("Filter Type Index = 0")
    lines.append("Filter Input Index = 0")
    lines.append("Filter Output Index = 0")
    lines.append("")
    lines.append("Filter Type = 1")
    lines.append("")
    lines.append("MEH Configuration = 0")
    lines.append("ME Amplifier Polarity Value = 1")
    lines.append("")

    # Write to file (Hornresp requires CRLF line endings)
    output_path = Path(output_path)
    output_path.write_text("\r\n".join(lines))


def _get_horn_parameters(params: Dict, enclosure_type: str) -> list[tuple[str, str]]:
    """Get horn parameters based on enclosure type.

    Returns a list of (key, value) tuples to preserve order with duplicates.
    """
    if enclosure_type in ['sealed', 'ported']:
        return [
            ('S1', '0.00'),
            ('S2', '0.00'),
            ('Exp', '0.00'),
            ('F12', '0.00'),
            ('S2', '0.00'),
            ('S3', '0.00'),
            ('Exp', '0.10'),
            ('F23', '0.00'),
            ('S3', '0.00'),
            ('S4', '0.00'),
            ('L34', '0.00'),
            ('F34', '0.00'),
            ('S4', '0.00'),
            ('S5', '0.00'),
            ('L45', '0.00'),
            ('F45', '0.00'),
        ]

    # Horn enclosures
    s1 = params.get('throat_area_cm2', 0)
    s2 = params.get('mouth_area_cm2', 0)
    exp = params.get('horn_length_cm', 0)
    f12 = params.get('cutoff_frequency', 0)

    # Calculate flare rate from cutoff if not provided
    if f12 and not exp:
        fc = f12
        # flare rate m = 2*pi*fc/c
        c = 343.5  # speed of sound in m/s
        m = 2 * math.pi * fc / c

    return [
        ('S1', f'{s1:.2f}'),
        ('S2', f'{s2:.2f}'),
        ('Exp', f'{exp:.2f}'),
        ('F12', f'{f12:.2f}'),
        ('S2', f'{s2:.2f}'),
        ('S3', f'{s2:.2f}'),
        ('Exp', '0.10'),
        ('F23', '0.00'),
        ('S3', '0.00'),
        ('S4', '0.00'),
        ('L34', '0.00'),
        ('F34', '0.00'),
        ('S4', '0.00'),
        ('S5', '0.00'),
        ('L45', '0.00'),
        ('F45', '0.00'),
    ]


def _get_driver_parameters(driver: ThieleSmallParameters) -> Dict[str, str]:
    """Get traditional driver parameters in Hornresp format."""
    # Convert Sd from m² to cm²
    sd_cm2 = driver.sd * 10000

    # Calculate Rms if not provided
    if driver.rms:
        rms = driver.rms
    else:
        # Calculate from Qms: Qms = (1/Rms) * sqrt(Mmd/Cms)
        # Rms = (1/Qms) * sqrt(Mmd/Cms)
        if driver.qms and driver.cms and driver.mms:
            mmd_kg = driver.mms / 1000  # convert g to kg
            rms = (1 / driver.qms) * math.sqrt(mmd_kg / driver.cms)
        else:
            rms = 0.0

    # Format Cms in scientific notation if very small (3 significant digits for Hornresp)
    if driver.cms < 0.001:
        cms_str = f'{driver.cms:.2E}'
    else:
        cms_str = f'{driver.cms:.5f}'

    return {
        'Sd': f'{sd_cm2:.2f}',
        'Bl': f'{driver.bl:.2f}',
        'Cms': cms_str,
        'Rms': f'{rms:.2f}',
        'Mmd': f'{driver.mms:.2f}',
        'Le': f'{driver.le if driver.le else 0:.2f}',
        'Re': f'{driver.re:.2f}',
        'Nd': '1',
    }


def _get_chamber_parameters(params: Dict, enclosure_type: str) -> Dict[str, str]:
    """Get chamber parameters based on enclosure type."""
    if enclosure_type == 'sealed':
        vrc = params.get('volume_liters', 0)
        return {
            'Vrc': f'{vrc:.2f}',
            'Lrc': '15.00',
            'Fr': '40000.00',
            'Tal': '4.00',
            'Vtc': '0.00',
            'Atc': '0.00',
        }

    if enclosure_type == 'ported':
        vrc = params.get('volume_liters', 0)
        return {
            'Vrc': f'{vrc:.2f}',
            'Lrc': '15.00',
            'Fr': '40000.00',
            'Tal': '4.00',
            'Vtc': '0.00',
            'Atc': '0.00',
        }

    if enclosure_type == 'exponential_horn':
        vrc = params.get('rear_chamber_volume', 0)
        return {
            'Vrc': f'{vrc:.2f}',
            'Lrc': '15.00',
            'Fr': '40000.00',
            'Tal': '4.00',
            'Vtc': '0.00',
            'Atc': '0.00',
        }

    if enclosure_type == 'front_loaded_horn':
        vrc = params.get('rear_chamber_volume', 0)
        vtc = params.get('front_chamber_volume', 0)
        # Use throat area for Atc (front chamber throat)
        atc = params.get('throat_area_cm2', 0)
        return {
            'Vrc': f'{vrc:.2f}',
            'Lrc': '15.00',
            'Fr': '40000.00',
            'Tal': '4.00',
            'Vtc': f'{vtc:.2f}',
            'Atc': f'{atc:.2f}',
        }

    # Default
    return {
        'Vrc': '0.00',
        'Lrc': '15.00',
        'Fr': '40000.00',
        'Tal': '4.00',
        'Vtc': '0.00',
        'Atc': '0.00',
    }


def _calculate_rms_from_qms(cms: float, mmd: float, qms: float) -> float:
    """Calculate mechanical resistance Rms from Qms.

    Formula: Qms = (1 / Rms) * sqrt(Mmd / Cms)
    Therefore: Rms = (1 / Qms) * sqrt(Mmd / Cms)

    Args:
        cms: Mechanical compliance (m/N)
        mmd: Moving mass (g)
        qms: Mechanical Q

    Returns:
        Rms in N·s/m
    """
    mmd_kg = mmd / 1000  # convert g to kg
    return (1 / qms) * math.sqrt(mmd_kg / cms)
