"""Sealed (closed box) enclosure implementation."""

from typing import Dict, Tuple
import numpy as np
import warnings

from viberesp.enclosures.base import BaseEnclosure
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.core.constants import (
    QTC_BUTTERWORTH, QTC_BESSEL, QTC_MAX, QTC_WARNING,
    VOLTAGE_1W_8OHM
)


class SealedEnclosure(BaseEnclosure):
    """
    Sealed (acoustic suspension) enclosure.

    Mathematical model: 2nd-order high-pass filter

    The sealed box is modeled as a 2nd-order system with:
    - System resonance: Fc = Fs × sqrt(α + 1)
    - System Q: Qtc = Qts × sqrt(α + 1)
    - Transfer function: H(s) = s² / (s² + s×(ωc/Qtc) + ωc²)

    References:
        - Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
        - Small, R.H. (1972). "Closed-Box Loudspeaker Systems"
    """

    def _validate_compatibility(self) -> None:
        """Check driver suitability for sealed enclosure."""
        qts = self.driver.qts

        # High Qts drivers (>0.7) can produce peaked response
        if qts > 0.7:
            warnings.warn(
                f"Driver Qts={qts:.3f} > 0.7. "
                f"Consider larger box volume to reduce Qtc, "
                f"or driver may be better suited for sealed box. "
                f"Qtc will be approximately {qts * np.sqrt(self.calculate_compliance_ratio() + 1):.3f}.",
                UserWarning
            )

        # Very low Qts (<0.2) may require very large box
        if qts < 0.2:
            alpha = self.calculate_compliance_ratio()
            qtc = qts * np.sqrt(alpha + 1)
            if qtc < 0.5:
                warnings.warn(
                    f"Driver Qts={qts:.3f} is very low. "
                    f"For optimal Qtc (~0.7), consider larger box volume. "
                    f"Current Qtc≈{qtc:.3f}.",
                    UserWarning
                )

        # Check EBP for sealed box suitability
        if self.driver.ebp > 100:
            warnings.warn(
                f"Driver EBP={self.driver.ebp:.1f} > 100. "
                f"This driver may be better suited for ported enclosure.",
                UserWarning
            )

    def calculate_system_q(self) -> float:
        """
        Calculate system Q factor (Qtc).

        Qtc = Qts × sqrt(α + 1)

        Where:
            α = Vas / Vb (compliance ratio)
            Qts = total Q factor of driver

        Returns:
            System Qtc (unitless)
        """
        alpha = self.calculate_compliance_ratio()
        qts = self.driver.qts
        qtc = qts * np.sqrt(alpha + 1)

        # Check Qtc and warn if needed
        self._check_qtc_warning(qtc)

        return qtc

    def calculate_f3(self) -> float:
        """
        Calculate -3dB frequency using the correct formula.

        Uses the established formula for sealed box systems:
        F3 = Fc × sqrt(X + sqrt(X² + 1))
        where X = 1/(2×Qtc²) - 1

        This is the theoretically correct method derived from the 2nd-order
        high-pass filter transfer function.

        For Qtc=0.707 (Butterworth): F3 ≈ Fc
        For Qtc<0.707: F3 is above Fc
        For Qtc>0.707: F3 is below Fc (due to peaking)

        Returns:
            -3dB frequency (Hz)
        """
        qtc = self.calculate_system_q()
        return self._get_f3_from_qtc(qtc)

    def calculate_f10(self) -> float:
        """
        Calculate -10dB frequency (approximate).

        For sealed boxes, F10 is typically about 0.5-0.6 × F3,
        depending on Qtc.

        Returns:
            -10dB frequency (Hz)
        """
        f3 = self.calculate_f3()
        qtc = self.calculate_system_q()

        # Approximate relationship: F10 ≈ F3 / 2 for typical Qtc
        # More precisely depends on Qtc
        if qtc < QTC_BESSEL:
            return f3 * 0.6
        elif qtc < QTC_BUTTERWORTH:
            return f3 * 0.55
        else:
            # Higher Qtc extends bass but has steeper rolloff
            return f3 * 0.5

    def calculate_frequency_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate sealed box frequency response.

        Uses 2nd-order high-pass filter transfer function:
        H(s) = s² / (s² + s×(ωc/Qtc) + ωc²)

        Where:
            s = jω (Laplace variable)
            ωc = 2π×Fc
            Fc = Fs × sqrt(α + 1)
            Qtc = Qts × sqrt(α + 1)

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)
        """
        qtc = self.calculate_system_q()
        fc = self.calculate_box_frequency()
        wc = 2 * np.pi * fc

        # Angular frequency array
        w = 2 * np.pi * frequencies

        # 2nd-order high-pass filter transfer function
        # H(s) = s² / (s² + s×(wc/Qtc) + wc²)
        s = 1j * w

        numerator = s**2
        denominator = s**2 + s * (wc / qtc) + wc**2

        H = numerator / denominator

        # Extract magnitude and phase
        magnitude = np.abs(H)
        phase = np.angle(H, deg=True)

        # Convert magnitude to dB
        # Normalize to passband (high-frequency asymptote approaches 0dB)
        spl_db = 20 * np.log10(magnitude + 1e-10)

        # Find passband level (at high frequencies, typically 200-1000 Hz)
        passband_mask = frequencies > 200
        if np.any(passband_mask):
            passband_level = np.mean(spl_db[passband_mask])
            spl_db = spl_db - passband_level

        # Add sensitivity reference
        spl_ref = self.calculate_sensitivity()

        # Adjust for voltage if not 2.83V
        if voltage != VOLTAGE_1W_8OHM:
            # SPL scales with voltage: 20*log10(V/2.83)
            voltage_correction = 20 * np.log10(voltage / VOLTAGE_1W_8OHM)
            spl_ref = spl_ref + voltage_correction

        spl_db = spl_db + spl_ref

        return spl_db, phase

    def get_design_parameters(self) -> Dict:
        """
        Return parameters for optimization.

        Returns:
            Dict with parameter names as keys and (value, min, max) tuples
        """
        return {
            'vb': (
                self.params.vb,
                1.0,      # Min: 1L
                500.0     # Max: 500L (for most applications)
            )
        }

    def calculate_max_spl(self, power_w: float, distance_m: float = 1.0) -> float:
        """
        Calculate maximum SPL at specified power and distance.

        Args:
            power_w: Input power (W)
            distance_m: Listening distance (m)

        Returns:
            Maximum SPL (dB)
        """
        # Sensitivity at 1W/1m
        sensitivity = self.calculate_sensitivity()

        # Power law: SPL increases by 10*log10(power)
        power_gain = 10 * np.log10(power_w)

        # Distance law: SPL decreases by 20*log10(distance)
        distance_loss = 20 * np.log10(distance_m)

        max_spl = sensitivity + power_gain - distance_loss

        return max_spl

    def calculate_box_volume_for_qtc(self, target_qtc: float) -> float:
        """
        Calculate required box volume for target Qtc.

        Qtc = Qts × sqrt(Vas/Vb + 1)
        Solving for Vb:
        Vb = Vas / ((Qtc/Qts)² - 1)

        Args:
            target_qtc: Desired system Qtc

        Returns:
            Required box volume (L)
        """
        qts = self.driver.qts

        if target_qtc <= qts:
            raise ValueError(
                f"Target Qtc={target_qtc:.3f} must be > Qts={qts:.3f}. "
                f"Impossible to achieve with any box volume."
            )

        q_ratio = (target_qtc / qts) ** 2
        vb = self.driver.vas / (q_ratio - 1)

        return vb

    def get_alignment_type(self) -> str:
        """
        Determine alignment type based on Qtc.

        Returns:
            Alignment type name
        """
        qtc = self.calculate_system_q()

        if qtc < QTC_BESSEL:
            return "Sub-Bessel (underdamped, weak bass)"
        elif qtc < 0.6:
            return "Bessel-like (good transient, lean bass)"
        elif qtc < QTC_BUTTERWORTH:
            return "Approaching Butterworth (good compromise)"
        elif qtc == QTC_BUTTERWORTH:
            return "Butterworth (maximally flat)"
        elif qtc < QTC_MAX:
            return "Chebyshev/BB4 (extended bass, some peaking)"
        elif qtc < QTC_WARNING:
            return "High Q (significant peaking, boomy)"
        else:
            return "Very High Q (severely peaked, one-note bass)"
