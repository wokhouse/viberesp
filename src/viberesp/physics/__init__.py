"""Viberesp physics calculations module.

This module contains physics-based acoustic calculations for loudspeaker
simulation, including radiation impedance, transfer matrices, and driver models.
"""

from viberesp.physics.radiation import (
    circular_piston_impedance,
    circular_piston_impedance_normalized,
)

__all__ = [
    "circular_piston_impedance",
    "circular_piston_impedance_normalized",
]
