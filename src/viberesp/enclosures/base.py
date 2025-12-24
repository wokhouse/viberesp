"""Abstract base class for all enclosure types."""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional
import numpy as np
import warnings

from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.core.constants import (
    C, RHO,
    QTC_BUTTERWORTH, QTC_BESSEL, QTC_MIN, QTC_MAX, QTC_WARNING,
    VOLTAGE_1W_8OHM
)


class BaseEnclosure(ABC):
    """
    Abstract base class for all loudspeaker enclosure types.

    All enclosure implementations (sealed, ported, bandpass, etc.) must
    inherit from this class and implement the required methods.

    The base class provides common calculations and enforces a consistent
    interface across all enclosure types.
    """

    def __init__(self, driver: ThieleSmallParameters, params: EnclosureParameters):
        """
        Initialize enclosure with driver parameters and design parameters.

        Args:
            driver: Thiele-Small parameters for the driver
            params: Enclosure design parameters
        """
        self.driver = driver
        self.params = params
        self._validate_compatibility()

    @abstractmethod
    def _validate_compatibility(self) -> None:
        """
        Check if driver is suitable for this enclosure type.

        Should raise warnings or errors if driver parameters are outside
        recommended ranges for this enclosure type.

        Examples:
            - Sealed: Qts > 0.7 warning
            - Ported: Qts > 0.5 warning
        """
        pass

    @abstractmethod
    def calculate_frequency_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate SPL magnitude and phase vs frequency.

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)

        Note:
            SPL should be normalized to passband (0dB reference)
            and referenced to specified voltage at 1m distance.
        """
        pass

    @abstractmethod
    def calculate_system_q(self) -> float:
        """
        Calculate system Q factor.

        Returns:
            System Q (Qtc for sealed, Qlcb for ported, etc.)
        """
        pass

    @abstractmethod
    def calculate_f3(self) -> float:
        """
        Calculate -3dB frequency.

        Returns:
            Frequency where response is -3dB relative to passband (Hz)
        """
        pass

    @abstractmethod
    def calculate_f10(self) -> float:
        """
        Calculate -10dB frequency.

        Returns:
            Frequency where response is -10dB relative to passband (Hz)
        """
        pass

    @abstractmethod
    def get_design_parameters(self) -> Dict:
        """
        Return all design parameters as dict for optimization.

        Returns:
            Dict with parameter names as keys and (value, min, max) tuples
        """
        pass

    # ===== Common Calculations =====

    def calculate_compliance_ratio(self) -> float:
        """
        Calculate compliance ratio (α).

        α = Vas / Vb

        Ratio of driver compliance to box compliance.
        Higher values = stiffer box relative to driver.

        Returns:
            Compliance ratio (unitless)
        """
        return self.driver.vas / self.params.vb

    def calculate_box_frequency(self) -> float:
        """
        Calculate box resonance frequency (Fc).

        Fc = Fs * sqrt(α + 1)

        For sealed boxes, this is the system resonant frequency.

        Returns:
            Box resonance frequency (Hz)
        """
        alpha = self.calculate_compliance_ratio()
        return self.driver.fs * np.sqrt(alpha + 1)

    def calculate_sensitivity(self) -> float:
        """
        Calculate driver reference sensitivity at 1W/1m.

        From Small (1972): Reference efficiency calculation
        no = (4π²/c³) × fs³ × Vas

        SPL(1W/1m) = 112.02 + 10*log10(no)

        Returns:
            Sensitivity in dB (1W/1m)
        """
        # Convert Vas from L to m³
        vas_m3 = self.driver.vas * 0.001

        # Reference efficiency (Small's formula)
        no = (4 * np.pi**2 / C**3) * (self.driver.fs**3 * vas_m3)

        # Convert to SPL
        spl = 112.02 + 10 * np.log10(no + 1e-10)

        return spl

    def calculate_reference_efficiency(self) -> float:
        """
        Calculate reference efficiency as percentage.

        Returns:
            Efficiency (0-100%)
        """
        # Convert Vas from L to m³
        vas_m3 = self.driver.vas * 0.001

        # Reference efficiency
        no = (4 * np.pi**2 / C**3) * (self.driver.fs**3 * vas_m3)

        return no * 100.0

    def _check_qtc_warning(self, qtc: float) -> None:
        """Warn if system Q is outside optimal range."""
        if qtc < QTC_MIN:
            warnings.warn(
                f"Qtc={qtc:.3f} below {QTC_MIN}. "
                f"Response may be underdamped with weak bass.",
                UserWarning
            )
        elif qtc > QTC_WARNING:
            warnings.warn(
                f"Qtc={qtc:.3f} above {QTC_WARNING}. "
                f"Response will be very peaked and boomy.",
                UserWarning
            )
        elif qtc > QTC_MAX:
            warnings.warn(
                f"Qtc={qtc:.3f} above {QTC_MAX}. "
                f"Response will be peaked.",
                UserWarning
            )

    def _get_f3_from_qtc(self, qtc: float) -> float:
        """
        Calculate F3 frequency from Qtc using empirical relationships.

        Based on Thiele's alignment tables for sealed boxes.

        Args:
            qtc: System Q factor

        Returns:
            -3dB frequency (Hz)
        """
        fc = self.calculate_box_frequency()

        # Empirical relationship between Qtc and F3/Fc ratio
        # From Thiele's alignment tables
        if qtc <= 0.5:
            # Very low Q: F3 is significantly above Fc
            f3_ratio = 1.55 - 0.5 * qtc
        elif qtc <= QTC_BUTTERWORTH:  # 0.707
            # approaching Butterworth
            f3_ratio = 1.0 + 0.3 * (QTC_BUTTERWORTH - qtc) / (QTC_BUTTERWORTH - 0.5)
        elif qtc <= 1.0:
            # Above Butterworth but reasonable
            f3_ratio = 1.0 + 0.15 * (qtc - QTC_BUTTERWORTH) / (1.0 - QTC_BUTTERWORTH)
        else:
            # High Q: F3 is lower due to peaking
            f3_ratio = 1.15 + 0.35 * (qtc - 1.0)

        return fc * f3_ratio

    def get_summary(self) -> Dict:
        """
        Get summary of enclosure design and predicted performance.

        Returns:
            Dict with key parameters and metrics
        """
        summary = {
            'enclosure_type': self.params.enclosure_type,
            'driver': {
                'manufacturer': self.driver.manufacturer,
                'model': self.driver.model_number,
                'fs': self.driver.fs,
                'vas': self.driver.vas,
                'qts': self.driver.qts,
                'sd_cm2': self.driver.sd * 10000,
            },
            'enclosure': {
                'vb_l': self.params.vb,
                'alpha': self.calculate_compliance_ratio(),
            },
            'performance': {
                'f3_hz': self.calculate_f3(),
                'f10_hz': self.calculate_f10(),
                'sensitivity_db': self.calculate_sensitivity(),
                'efficiency_percent': self.calculate_reference_efficiency(),
            }
        }

        # Add system Q if applicable
        try:
            summary['performance']['system_q'] = self.calculate_system_q()
        except NotImplementedError:
            pass

        # Add box frequency
        try:
            summary['performance']['fc_hz'] = self.calculate_box_frequency()
        except NotImplementedError:
            pass

        return summary

    def __repr__(self) -> str:
        """String representation of enclosure."""
        return (
            f"{self.__class__.__name__}("
            f"driver={self.driver.manufacturer or 'Unknown'} "
            f"{self.driver.model_number or 'Unknown'}, "
            f"Vb={self.params.vb:.1f}L)"
        )


class EnclosureValidationError(Exception):
    """Raised when driver parameters are invalid for enclosure type."""
    pass


class EnclosureSimulationError(Exception):
    """Raised when simulation calculation fails."""
    pass
