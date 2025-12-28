"""
Parameter space definitions for enclosure optimization.

This module provides parameter bounds and design space definitions for
different enclosure types:
- Sealed box: Vb range based on driver Vas
- Ported box: Vb, Fb, port dimensions
- Horn: Throat area, mouth area, length, flare constant
- Folded horn: Multi-segment parameters

Parameter ranges are based on practical design limits from literature.
"""

from viberesp.optimization.parameters.parameter_space import (
    ParameterRange,
    EnclosureParameterSpace,
)
from viberesp.optimization.parameters.sealed_box_params import get_sealed_box_parameter_space
from viberesp.optimization.parameters.ported_box_params import get_ported_box_parameter_space
from viberesp.optimization.parameters.exponential_horn_params import (
    get_exponential_horn_parameter_space,
    calculate_horn_cutoff_frequency,
    calculate_horn_volume,
)

__all__ = [
    "ParameterRange",
    "EnclosureParameterSpace",
    "get_sealed_box_parameter_space",
    "get_ported_box_parameter_space",
    "get_exponential_horn_parameter_space",
    "calculate_horn_cutoff_frequency",
    "calculate_horn_volume",
]
