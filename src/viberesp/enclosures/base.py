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
        Calculate F3 frequency from Qtc using the correct formula.

        Based on the established formula for sealed box systems:
        F3 = Fc × sqrt(X + sqrt(X² + 1))
        where X = 1/(2×Qtc²) - 1

        This formula is derived from the transfer function of a 2nd-order
        high-pass filter and is the theoretically correct method.

        Reference: https://www.diyaudio.com/community/threads/relationship-between-fcb-f-3-and-qtc-in-a-closed-box-sub.1792/

        Args:
            qtc: System Q factor

        Returns:
            -3dB frequency (Hz)
        """
        fc = self.calculate_box_frequency()

        # Calculate the intermediate variable X
        # X = 1/(2*Qtc²) - 1
        X = 1.0 / (2.0 * qtc ** 2) - 1.0

        # Calculate F3/Fc ratio using the correct formula
        # F3/Fc = sqrt(X + sqrt(X² + 1))
        f3_ratio = np.sqrt(X + np.sqrt(X ** 2 + 1.0))

        return fc * f3_ratio

    def _calculate_f3_numerical(
        self,
        frequencies: np.ndarray,
        spl_db: np.ndarray
    ) -> float:
        """
        Calculate F3 frequency by finding -3dB crossing point.

        Uses numerical method to find where the magnitude response crosses -3dB
        relative to the maximum SPL level. This matches the approach used by
        Hornresp and provides more accurate results than empirical formulas.

        For high-pass filters, looks for upward crossing (from below to above).

        Args:
            frequencies: Frequency array in Hz
            spl_db: SPL array in dB (absolute or normalized)

        Returns:
            F3 frequency in Hz
        """
        # Use maximum SPL as reference (matches Hornresp's approach)
        ref_level = np.max(spl_db)
        target_level = ref_level - 3.0

        # Find -3dB upward crossing for high-pass filters
        # Search from low to high frequency
        for i in range(len(spl_db) - 1):
            if spl_db[i] <= target_level < spl_db[i + 1]:
                # Linear interpolation for accuracy
                frac = (target_level - spl_db[i]) / (spl_db[i + 1] - spl_db[i])
                return frequencies[i] + frac * (frequencies[i + 1] - frequencies[i])

        # No crossing found - return min or max frequency
        if spl_db[0] > target_level:
            return frequencies[0]
        else:
            return frequencies[-1]

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
