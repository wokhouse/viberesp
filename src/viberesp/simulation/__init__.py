"""
Viberesp simulation module for horn-loaded loudspeaker systems.

This module implements acoustic theory for horn simulation with
continuous validation against Hornresp.

Literature:
- literature/horns/olson_1947.md - Exponential horn theory
- literature/horns/beranek_1954.md - Radiation impedance
- literature/horns/kolbrek_horn_theory_tutorial.md - Modern treatment
- literature/transmission_lines/chabassier_tournemenne_2018_tmatrix.md - T-matrix method
"""

from viberesp.simulation.constants import (
    AIR_DENSITY,
    ATMOSPHERIC_PRESSURE,
    CHARACTERISTIC_IMPEDANCE_AIR,
    PI,
    SPEED_OF_SOUND,
    angular_frequency,
    wavelength,
    wavenumber,
)
from viberesp.simulation.types import ExponentialHorn, FrequencyResponse, SimulationResult

# Horn theory functions (T-matrix method)
from viberesp.simulation.horn_theory import (
    MediumProperties,
    circular_piston_radiation_impedance,
    exponential_horn_throat_impedance,
    exponential_horn_tmatrix,
    throat_impedance_from_tmatrix,
)

__all__ = [
    # Constants
    "SPEED_OF_SOUND",
    "AIR_DENSITY",
    "ATMOSPHERIC_PRESSURE",
    "CHARACTERISTIC_IMPEDANCE_AIR",
    "PI",
    # Functions from constants
    "wavenumber",
    "angular_frequency",
    "wavelength",
    # Horn theory functions
    "MediumProperties",
    "circular_piston_radiation_impedance",
    "exponential_horn_throat_impedance",
    "exponential_horn_tmatrix",
    "throat_impedance_from_tmatrix",
    # Data structures
    "ExponentialHorn",
    "FrequencyResponse",
    "SimulationResult",
]
