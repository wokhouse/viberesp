"""
Hornresp integration module.

Provides functionality to export viberesp designs to Hornresp format
for validation and simulation.

Literature:
- Hornresp User Manual - http://www.hornresp.net/
"""

from viberesp.hornresp.export import (
    export_to_hornresp,
    export_front_loaded_horn_to_hornresp,
    batch_export_to_hornresp,
    HornrespRecord,
    driver_to_hornresp_record,
)

__all__ = [
    "export_to_hornresp",
    "export_front_loaded_horn_to_hornresp",
    "batch_export_to_hornresp",
    "HornrespRecord",
    "driver_to_hornresp_record",
]
