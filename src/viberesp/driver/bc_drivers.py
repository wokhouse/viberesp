"""
B&C Speakers driver factory functions.

These functions create ThieleSmallParameters instances for real B&C drivers
with parameters sourced from official datasheets.

Literature:
- B&C Speakers datasheets (official manufacturer specifications)
"""

from viberesp.driver.parameters import ThieleSmallParameters


def get_bc_8ndl51() -> ThieleSmallParameters:
    """
    B&C 8NDL51-8 8" Midrange driver.

    CORRECTED DATASHEET PARAMETERS (validated against Hornresp):
    - Fs: 66 Hz
    - Re: 5.3 Ω
    - Qes: 0.41
    - Qms: 3.6
    - Qts: 0.37
    - Vas: 14 dm³ (14 L)
    - Sd: 220 cm²
    - η0: 1%
    - Xmax: 7 mm
    - Mmd: 26.77 g (driver mass only, excludes radiation mass)
    - Bl: 12.39 T·m (corrected)
    - Le: 0.5 mH
    - Cms: 2.03E-04 m/N (corrected)
    - Rms: 3.30 N·s/m (corrected)
    - EBP: 161 Hz

    Literature: B&C 8NDL51 datasheet
    Validation: tests/validation/drivers/bc_8ndl51/infinite_baffle/8ndl51_correct.txt

    Note: M_md is driver mass only. Radiation mass is calculated internally
    using Beranek (1954) theory to match Hornresp methodology.
    """
    return ThieleSmallParameters(
        M_md=0.02677,   # 26.77g driver mass only (CORRECTED)
        C_ms=2.03e-4,   # 2.03E-04 m/N compliance (CORRECTED)
        R_ms=3.30,      # 3.30 N·s/m mechanical resistance (CORRECTED)
        R_e=5.3,        # 5.3 Ω DC resistance (datasheet)
        L_e=0.5e-3,     # 0.5 mH voice coil inductance (datasheet)
        BL=12.39,       # 12.39 T·m force factor (CORRECTED)
        S_d=0.0220,     # 220 cm² effective area (datasheet)
    )


def get_bc_12ndl76() -> ThieleSmallParameters:
    """
    B&C 12NDL76-4 12" Mid-Woofer driver.

    Datasheet specifications:
    - Fs: 50 Hz
    - Re: 5.3 Ω
    - Qts: 0.2
    - Qes: 0.21
    - Qms: 4.2
    - Vas: 73 dm³ (73 L)
    - Sd: 522 cm²
    - BL: 20.1 T·m
    - Mmd: 53 g (driver mass only, excludes radiation mass)
    - Cms: 0.19 mm/N
    - Rms: 4.0 N·s/m (calculated from Qms)
    - Le: 1.0 mH
    - Xmax: 7 mm

    Literature: B&C 12NDL76 datasheet

    Note: M_md is driver mass only. Radiation mass is calculated internally
    using Beranek (1954) theory to match Hornresp methodology.
    """
    return ThieleSmallParameters(
        M_md=0.053,    # 53g driver mass only (datasheet)
        C_ms=0.00019,  # 0.19 mm/N compliance (datasheet)
        R_ms=4.0,      # Calculated from Qms: Rms = (2π·Fs·Mmd) / Qms
        R_e=5.3,       # 5.3 Ω DC resistance (datasheet)
        L_e=1.0e-3,    # 1.0 mH voice coil inductance (datasheet)
        BL=20.1,       # 20.1 T·m force factor (datasheet)
        S_d=0.0522     # 522 cm² effective area (datasheet)
    )


def get_bc_15ds115() -> ThieleSmallParameters:
    """
    B&C 15DS115-8 15" Subwoofer driver.

    Datasheet specifications:
    - Fs: 33 Hz
    - Re: 4.9 Ω
    - Qts: 0.17
    - Qes: 0.18
    - Qms: 5.2
    - Vas: 94 dm³ (94 L)
    - Sd: 855 cm²
    - BL: 38.7 T·m
    - Mmd: 254 g (driver mass only, excludes radiation mass)
    - Cms: 0.25 mm/N
    - Rms: 10.15 N·s/m (calculated from Qms)
    - Le: 4.5 mH
    - Xmax: 16.5 mm

    Literature: B&C 15DS115 datasheet

    Note: M_md is driver mass only. Radiation mass is calculated internally
    using Beranek (1954) theory to match Hornresp methodology.
    """
    return ThieleSmallParameters(
        M_md=0.254,    # 254g driver mass only
        C_ms=0.00025,  # 0.25 mm/N compliance (datasheet)
        R_ms=10.15,    # Calculated from Qms: Rms = (2π·Fs·Mmd) / Qms
        R_e=4.9,       # 4.9 Ω DC resistance (datasheet)
        L_e=4.5e-3,    # 4.5 mH voice coil inductance (datasheet)
        BL=38.7,       # 38.7 T·m force factor (datasheet)
        S_d=0.0855     # 855 cm² effective area (datasheet)
    )


def get_bc_18pzw100() -> ThieleSmallParameters:
    """
    B&C 18PZW100-8 18" Subwoofer driver.

    Datasheet specifications:
    - Fs: 37 Hz
    - Re: 5.1 Ω
    - Qts: 0.36
    - Qes: 0.38
    - Qms: 7.9
    - Vas: 186 dm³ (186 L)
    - Sd: 1210 cm²
    - BL: 25.5 T·m
    - Mmd: 209 g (driver mass only, excludes radiation mass)
    - Cms: 0.17 mm/N
    - Rms: 6.15 N·s/m (calculated from Qms)
    - Le: 1.58 mH
    - Xmax: 8 mm

    Literature: B&C 18PZW100 datasheet

    Note: M_md is driver mass only. Radiation mass is calculated internally
    using Beranek (1954) theory to match Hornresp methodology.
    """
    return ThieleSmallParameters(
        M_md=0.209,    # 209g driver mass only
        C_ms=0.00017,  # 0.17 mm/N compliance (datasheet)
        R_ms=6.15,     # Calculated from Qms: Rms = (2π·Fs·Mmd) / Qms
        R_e=5.1,       # 5.1 Ω DC resistance (datasheet)
        L_e=1.58e-3,   # 1.58 mH voice coil inductance (datasheet)
        BL=25.5,       # 25.5 T·m force factor (datasheet)
        S_d=0.1210     # 1210 cm² effective area (datasheet)
    )


def get_all_bc_drivers() -> list[tuple[ThieleSmallParameters, str]]:
    """
    Return all 4 B&C drivers as a list of (driver, name) tuples.

    Useful for batch operations and testing.

    Returns:
        List of (ThieleSmallParameters, driver_name) tuples
    """
    return [
        (get_bc_8ndl51(), "BC_8NDL51"),
        (get_bc_12ndl76(), "BC_12NDL76"),
        (get_bc_15ds115(), "BC_15DS115"),
        (get_bc_18pzw100(), "BC_18PZW100"),
    ]
