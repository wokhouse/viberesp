"""Horn enclosure implementations for viberesp.

This module provides horn-type loudspeaker enclosures including exponential
horns, tapped horns, and front-loaded horns.

Horn enclosures provide improved efficiency and controlled directivity
through acoustic impedance transformation between the driver and the
listening space.
"""

from viberesp.enclosures.horns.base_horn import BaseHorn
from viberesp.enclosures.horns.exponential_horn import ExponentialHorn
from viberesp.enclosures.horns.front_loaded_horn import FrontLoadedHorn

__all__ = [
    "BaseHorn",
    "ExponentialHorn",
    "FrontLoadedHorn",
]
