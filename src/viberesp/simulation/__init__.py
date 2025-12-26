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

__all__ = [
    # Constants
    "SPEED_OF_SOUND",
    "AIR_DENSITY",
    "ATMOSPHERIC_PRESSURE",
    "CHARACTERISTIC_IMPEDANCE_AIR",
    "PI",
    # Functions
    "wavenumber",
    "angular_frequency",
    "wavelength",
    # Data structures
    "ExponentialHorn",
    "FrequencyResponse",
    "SimulationResult",
]
