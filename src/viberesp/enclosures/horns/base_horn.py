"""Base class for horn-type enclosures."""

from abc import abstractmethod
from typing import Dict, Tuple, List, Optional
import numpy as np
import warnings

from viberesp.enclosures.base import BaseEnclosure
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.core.constants import C, RHO

# Unit conversion constants
CM2_TO_M2 = 1e-4  # cm² to m²
CM_TO_M = 0.01    # cm to m


class BaseHorn(BaseEnclosure):
    """
    Abstract base class for horn-type enclosures.

    Horn enclosures provide acoustic impedance transformation between
    the driver and the listening space, resulting in improved efficiency
    and controlled directivity.

    This base class implements shared horn calculations including:
    - Throat impedance calculation
    - Cutoff frequency calculation
    - Mouth size validation
    - Horn loading effects on driver parameters
    """

    def __init__(self, driver: ThieleSmallParameters, params: EnclosureParameters):
        """
        Initialize horn enclosure.

        Args:
            driver: Thiele-Small parameters for the driver
            params: Enclosure design parameters including horn-specific fields
        """
        # Convert horn parameters from cm²/cm to m²/m for calculations
        # Set these BEFORE calling super().__init__() because _validate_compatibility() needs them
        self.throat_area = (
            params.throat_area_cm2 * CM2_TO_M2
            if params.throat_area_cm2 else None
        )
        self.mouth_area = (
            params.mouth_area_cm2 * CM2_TO_M2
            if params.mouth_area_cm2 else None
        )
        self.horn_length = (
            params.horn_length_cm * CM_TO_M
            if params.horn_length_cm else None
        )

        # Validate required horn parameters
        if self.throat_area is None:
            raise ValueError("throat_area_cm2 is required for horn enclosures")

        if self.mouth_area is None:
            raise ValueError("mouth_area_cm2 is required for horn enclosures")

        if self.horn_length is None:
            raise ValueError("horn_length_cm is required for horn enclosures")

        # Now call parent init (which calls _validate_compatibility)
        super().__init__(driver, params)

    @abstractmethod
    def calculate_throat_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate acoustic impedance at horn throat.

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex impedance array (Pa·s/m³)
        """
        pass

    def calculate_cutoff_frequency(self) -> float:
        """
        Calculate horn cutoff frequency.

        For exponential horns, the cutoff frequency is related to the flare rate:
        fc = (m * c) / (4π)

        If cutoff_frequency is explicitly provided in parameters, it's used directly.
        Otherwise, it's calculated from the flare rate.

        Returns:
            Cutoff frequency fc (Hz)

        Raises:
            ValueError: If cutoff cannot be determined
        """
        # Use explicit cutoff if provided
        if self.params.cutoff_frequency:
            return self.params.cutoff_frequency

        # Calculate from flare rate (exponential horn)
        if self.params.flare_rate:
            m = self.params.flare_rate
            fc = (m * C) / (4 * np.pi)
            return fc

        raise ValueError(
            "Cutoff frequency must be specified or derived from flare_rate"
        )

    def _get_or_calculate_flare_rate(self) -> float:
        """
        Get flare rate from parameters or calculate from cutoff frequency.

        For exponential horns: fc = (m * c) / (4π)
        Therefore: m = (fc * 4π) / c

        Returns:
            Flare rate m (1/m)

        Raises:
            ValueError: If neither flare_rate nor cutoff_frequency is available
        """
        if self.params.flare_rate:
            return self.params.flare_rate

        if self.params.cutoff_frequency:
            # Calculate flare rate from cutoff frequency
            fc = self.params.cutoff_frequency
            m = (fc * 4 * np.pi) / C
            return m

        raise ValueError(
            "Either flare_rate or cutoff_frequency must be specified"
        )

    def calculate_effective_length(self) -> float:
        """
        Calculate effective horn length with end correction.

        The effective length of a horn includes both the physical length
        and an end correction that accounts for the radiation impedance
        at the mouth. For a circular mouth, the end correction is:

        delta_L = 0.85 * sqrt(mouth_area / (4 * pi))

        This correction accounts for the fact that the acoustic pressure
        extends beyond the physical mouth of the horn.

        Returns:
            Effective horn length (m)
        """
        # Get physical length
        physical_length = self.horn_length if self.horn_length else 0.0

        # Check if end correction is enabled (default: True)
        # Using getattr for backward compatibility in case older params don't have this field
        end_correction_enabled = getattr(self.params, 'end_correction', True)

        if not end_correction_enabled or not self.mouth_area:
            return physical_length

        # Calculate end correction for circular mouth
        # The factor 0.85 is appropriate for a circular piston in an infinite baffle
        # For other mouth shapes, different correction factors may apply
        mouth_radius = np.sqrt(self.mouth_area / np.pi)
        end_correction = 0.85 * mouth_radius

        return physical_length + end_correction

    def validate_mouth_size(self) -> None:
        """
        Check if mouth size is adequate for cutoff frequency.

        For smooth frequency response, the mouth circumference should be
        at least one wavelength at the cutoff frequency. This translates to:

        k * rm >= 0.7

        Where k is the wavenumber and rm is the mouth radius.

        Issues a warning if mouth is too small.
        """
        if self.mouth_area is None:
            return

        try:
            fc = self.calculate_cutoff_frequency()
        except ValueError:
            return

        # Calculate mouth radius
        mouth_radius = np.sqrt(self.mouth_area / np.pi)

        # Calculate wavenumber at cutoff
        k_rm = (2 * np.pi * fc / C) * mouth_radius

        # Check minimum mouth size (k_rm >= 0.7 for smooth response)
        if k_rm < 0.7:
            warnings.warn(
                f"Mouth too small for smooth response at {fc:.1f} Hz. "
                f"k_rm = {k_rm:.2f} (recommended: k_rm >= 0.7). "
                f"Increase mouth area to at least "
                f"{(0.7 * C / (2 * np.pi * fc))**2 * np.pi / CM2_TO_M2:.0f} cm² "
                f"for current cutoff frequency.",
                UserWarning
            )
        elif k_rm < 1.0:
            # Mild warning for marginal mouth size
            warnings.warn(
                f"Mouth size is marginal (k_rm = {k_rm:.2f}). "
                f"Consider increasing mouth area for smoother response.",
                UserWarning
            )

    def calculate_horn_gain(self) -> float:
        """
        Calculate theoretical horn gain from area ratio.

        The horn provides approximately:
        gain = 10 * log10(mouth_area / throat_area)

        This is an approximation assuming ideal impedance transformation
        and no losses.

        Returns:
            Horn gain in dB
        """
        if self.throat_area and self.mouth_area:
            area_ratio = self.mouth_area / self.throat_area
            horn_gain_db = 10 * np.log10(area_ratio)
            return horn_gain_db
        return 0.0

    def calculate_loaded_parameters(self) -> Dict[str, float]:
        """
        Calculate driver parameters with horn loading.

        Horn loading changes the effective mechanical load on the driver:
        - Adds radiation mass load at throat (increases effective moving mass)
        - This shifts Fs upward
        - Vas is effectively reduced by rear chamber compliance (if present)

        Returns:
            Dictionary with loaded parameters:
            - 'fs_loaded': Loaded resonance frequency (Hz)
            - 'vas_loaded': Loaded compliance volume (L)
        """
        try:
            fc = self.calculate_cutoff_frequency()
        except ValueError:
            # If no cutoff, assume no loading effect
            return {
                'fs_loaded': self.driver.fs,
                'vas_loaded': self.driver.vas
            }

        # Horn adds radiation mass, shifting Fs upward
        # Simplified model: fs_loaded = fs * sqrt(1 + (c / (2*pi*fc*St))^2)
        if self.throat_area:
            mass_loading_factor = (C / (2 * np.pi * fc * self.throat_area))**2
            fs_loaded = self.driver.fs * np.sqrt(1 + mass_loading_factor)
        else:
            fs_loaded = self.driver.fs

        # Vas effectively reduced by rear chamber compliance
        # If rear chamber exists, treat as sealed box
        if self.params.rear_chamber_volume:
            alpha = self.driver.vas / self.params.rear_chamber_volume
            vas_loaded = self.driver.vas / (alpha + 1)
        else:
            vas_loaded = self.driver.vas

        return {
            'fs_loaded': fs_loaded,
            'vas_loaded': vas_loaded
        }

    def calculate_finite_horn_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate throat impedance for finite exponential horn.

        This method accounts for the finite length of the horn and mouth
        reflections, which become significant near the cutoff frequency.

        For a finite exponential horn, the throat impedance includes:
        - Propagation effects through the horn length
        - Mouth radiation impedance
        - Standing wave patterns due to reflections

        Uses transmission line approximation:
        Z_throat = Z_characteristic × coth(γ × L_eff)

        Where γ is the complex propagation constant accounting for flare rate.

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex acoustic impedance at throat (Pa·s/m³)
        """
        # Get or calculate flare rate
        m = self._get_or_calculate_flare_rate()  # flare rate (1/m)
        k = 2 * np.pi * frequencies / C  # wavenumber
        St = self.throat_area  # throat area (m²)

        # Get effective horn length (with end correction if enabled)
        L_eff = self.calculate_effective_length()

        # Characteristic impedance of air at throat
        Z0 = (RHO * C) / St

        # For finite exponential horn, use hyperbolic functions
        # to account for mouth reflections and finite length effects

        # Calculate complex propagation constant for exponential horn
        # gamma = sqrt(m^2/4 - k^2) for exponential horns
        gamma_term = m**2 / 4 - k**2

        # Above cutoff: gamma is imaginary (propagating wave)
        # Below cutoff: gamma is real (evanescent wave)
        gamma = np.zeros_like(frequencies, dtype=complex)

        above_cutoff = gamma_term < 0
        below_cutoff = gamma_term >= 0

        # Above cutoff: propagating mode
        if np.any(above_cutoff):
            gamma[above_cutoff] = 1j * np.sqrt(-gamma_term[above_cutoff])

        # Below cutoff: evanescent mode
        if np.any(below_cutoff):
            gamma[below_cutoff] = np.sqrt(gamma_term[below_cutoff])

        # Calculate throat impedance using transmission line model
        # Z_throat = Z0 × coth(γ × L_eff)
        # This accounts for finite length and mouth reflections

        gamma_L = gamma * L_eff

        # Avoid overflow in coth for large arguments
        # Use: coth(z) = 1/tanh(z)
        # For large z, tanh(z) → 1, so coth(z) → 1

        tanh_gamma_L = np.tanh(gamma_L)

        # Avoid division by zero
        tanh_gamma_L = np.where(np.abs(tanh_gamma_L) < 1e-10, 1e-10, tanh_gamma_L)

        # Throat impedance
        Z_throat = Z0 / tanh_gamma_L

        return Z_throat
