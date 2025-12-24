"""Hornresp validation module for Viberesp.

This module provides tools to validate Viberesp simulation outputs
against Hornresp, which serves as a "source of truth" for loudspeaker
enclosure modeling.
"""

from .hornresp_parser import (
    HornrespData,
    HornrespParams,
    hornresp_params_to_ts,
    parse_hornresp_output,
    parse_hornresp_params,
)
from .comparison import ComparisonResult, compare_responses
from .metrics import ValidationMetrics, calculate_validation_metrics
from .plotting import plot_validation, plot_spl_only, plot_hornresp_style

__all__ = [
    # Parser
    'HornrespData',
    'HornrespParams',
    'parse_hornresp_output',
    'parse_hornresp_params',
    'hornresp_params_to_ts',
    # Comparison
    'ComparisonResult',
    'compare_responses',
    # Metrics
    'ValidationMetrics',
    'calculate_validation_metrics',
    # Plotting
    'plot_validation',
    'plot_spl_only',
    'plot_hornresp_style',
]
