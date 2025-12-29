"""Viberesp driver module.

Provides Thiele-Small parameter definitions for various loudspeaker drivers
and test cases used in validation.
"""

# Test case drivers for horn validation
from viberesp.driver.test_drivers import (
    get_tc2_compression_driver,
    get_tc3_compression_driver,
    get_tc4_compression_driver,
)

__all__ = [
    "get_tc2_compression_driver",
    "get_tc3_compression_driver",
    "get_tc4_compression_driver",
]
