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

    Datasheet specifications from www.bcspeakers.com:
    - Fs: 66 Hz
    - Re: 5.3 Ω
    - Qes: 0.41
    - Qms: 3.6
    - Qts: 0.37
    - Vas: 14 dm³ (14 L)
    - Sd: 220 cm²
    - η0: 1%
    - Xmax: 7 mm
    - Mms: 28 g
    - Bl: 12.4 T·m
    - Le: 0.5 mH
    - EBP: 161 Hz

    Literature: B&C 8NDL51 datasheet
    """
    return ThieleSmallParameters(
        M_ms=0.028,    # 28g moving mass (datasheet)
        C_ms=0.000209,  # Calculated from Fs and Mms: Cms = 1 / ((2π·Fs)² · Mms)
        R_ms=3.22,      # Calculated from Qms: Rms = (2π·Fs·Mms) / Qms
        R_e=5.3,        # 5.3 Ω DC resistance (datasheet)
        L_e=0.5e-3,     # 0.5 mH voice coil inductance (datasheet)
        BL=12.4,        # 12.4 T·m force factor (datasheet - CORRECTED)
        S_d=0.0220,     # 220 cm² effective area (datasheet)
    )


def get_bc_12ndl76() -> ThieleSmallParameters:
    """
    B&C 12NDL76-4 12" Mid-Woofer driver.

    Datasheet specifications:
    - Fs: 50 Hz
    - Re: 3.1 Ω
    - Qts: 0.19
    - Qes: 0.20
    - Qms: 3.25
    - Vas: 67 L
    - Sd: 522 cm²
    - BL: 16.5 T·m
    - Mms: 54 g
    - Cms: 0.19 mm/N
    - Rms: 5.2 N·s/m
    - Le: 0.72 mH

    Literature: B&C 12NDL76 datasheet
    """
    return ThieleSmallParameters(
        M_ms=0.054,    # 54g moving mass
        C_ms=0.00019,  # 0.19 mm/N compliance
        R_ms=5.2,      # 5.2 N·s/m mechanical resistance
        R_e=3.1,       # 3.1 Ω DC resistance
        L_e=0.72e-3,   # 0.72 mH voice coil inductance
        BL=16.5,       # 16.5 T·m force factor
        S_d=0.0522     # 522 cm² effective area
    )


def get_bc_15ds115() -> ThieleSmallParameters:
    """
    B&C 15DS115-8 15" Subwoofer driver.

    Datasheet specifications:
    - Fs: 33 Hz
    - Re: 4.9 Ω
    - Qts: 0.17
    - Qes: 0.18
    - Qms: 4.2
    - Vas: 132 L
    - Sd: 860 cm²
    - BL: 18.5 T·m
    - Mms: 95 g
    - Cms: 0.25 mm/N
    - Rms: 4.7 N·s/m
    - Le: 1.2 mH

    Literature: B&C 15DS115 datasheet
    """
    return ThieleSmallParameters(
        M_ms=0.095,    # 95g moving mass
        C_ms=0.00025,  # 0.25 mm/N compliance
        R_ms=4.7,      # 4.7 N·s/m mechanical resistance
        R_e=4.9,       # 4.9 Ω DC resistance
        L_e=1.2e-3,    # 1.2 mH voice coil inductance
        BL=18.5,       # 18.5 T·m force factor
        S_d=0.0860     # 860 cm² effective area
    )


def get_bc_18pzw100() -> ThieleSmallParameters:
    """
    B&C 18PZW100-8 18" Subwoofer driver.

    Datasheet specifications:
    - Fs: 37 Hz
    - Re: 5.1 Ω
    - Qts: 0.36
    - Qes: 0.38
    - Qms: 6.5
    - Vas: 280 L
    - Sd: 1250 cm²
    - BL: 14.5 T·m
    - Mms: 155 g
    - Cms: 0.17 mm/N
    - Rms: 5.5 N·s/m
    - Le: 2.1 mH

    Literature: B&C 18PZW100 datasheet
    """
    return ThieleSmallParameters(
        M_ms=0.155,    # 155g moving mass
        C_ms=0.00017,  # 0.17 mm/N compliance
        R_ms=5.5,      # 5.5 N·s/m mechanical resistance
        R_e=5.1,       # 5.1 Ω DC resistance
        L_e=2.1e-3,    # 2.1 mH voice coil inductance
        BL=14.5,       # 14.5 T·m force factor
        S_d=0.1250     # 1250 cm² effective area
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
