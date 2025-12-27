"""
Enclosure modeling for viberesp.

This module implements acoustic simulation for loudspeaker enclosures,
including sealed (closed-box) systems.

Literature:
- Small (1972) - Closed-Box Loudspeaker Systems Part I: Analysis
- literature/thiele_small/small_1972_closed_box.md
"""

from viberesp.enclosure.sealed_box import (
    SealedBoxSystemParameters,
    calculate_sealed_box_system_parameters,
    sealed_box_electrical_impedance,
)

__all__ = [
    "SealedBoxSystemParameters",
    "calculate_sealed_box_system_parameters",
    "sealed_box_electrical_impedance",
]

