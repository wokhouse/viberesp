"""
Validation framework for comparing viberesp results with Hornresp.

This module provides comparison metrics and validation tools for
ensuring viberesp simulations match Hornresp reference data.

Literature:
- ROADMAP Phase 5 - Validation framework
"""

from viberesp.validation.compare import (
    ValidationResult,
    compare_electrical_impedance,
    compare_spl,
    compare_electrical_impedance_phase,
    generate_validation_report,
)

__all__ = [
    "ValidationResult",
    "compare_electrical_impedance",
    "compare_spl",
    "compare_electrical_impedance_phase",
    "generate_validation_report",
]
