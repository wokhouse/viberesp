"""Front-loaded horn with rear chamber implementation."""

from typing import Dict, Tuple
import numpy as np
import warnings

from viberesp.enclosures.horns.base_horn import BaseHorn
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.core.constants import C, RHO, VOLTAGE_1W_8OHM


class FrontLoadedHorn(BaseHorn):
    """
    Front-loaded horn with rear chamber.

    A front-loaded horn (FLH) is a traditional PA speaker design where the driver
    is mounted between a sealed rear chamber and a horn-loaded front chamber.

    Key differences from ExponentialHorn:
    - Rear chamber is REQUIRED (not optional)
    - Models combined sealed box + horn physics
    - System Q dominated by rear chamber compliance
    - Driver mounted between two chambers (not directly at throat)

    Physical System:
        Rear Chamber (sealed) ← Driver → Front Chamber → Horn Throat → Mouth
                         (Vrc)           (Vfc, optional)     (St)          (Sm)

    The system response combines:
    1. Sealed box high-pass from rear chamber (2nd-order)
    2. Horn loading effect (impedance transformation + gain)
    3. Front chamber compliance (optional, acts as high-pass)

    References:
        - Beranek, L.L. "Acoustics"
        - Klippel, "Loudspeaker Nonlinearities - Causes and Parameters"
        - Hornresp documentation
    """

    def __init__(self, driver: ThieleSmallParameters, params: EnclosureParameters):
        """
        Initialize front-loaded horn.

        Args:
            driver: Thiele-Small parameters for the driver
            params: Enclosure parameters including:
                - rear_chamber_volume: Rear chamber volume L (REQUIRED)
                - throat_area_cm2: Throat area (cm²)
                - mouth_area_cm2: Mouth area (cm²)
                - horn_length_cm: Horn length (cm)
                - front_chamber_volume: Front chamber volume L (optional)
                - flare_rate: Exponential flare rate (optional)
                - cutoff_frequency: Horn cutoff fc Hz (optional)

        Raises:
            ValueError: If rear_chamber_volume is not specified
        """
        # Validate rear chamber is required for FLH
        if params.rear_chamber_volume is None:
            raise ValueError(
                "rear_chamber_volume is required for front-loaded horn enclosures. "
                "Unlike ExponentialHorn where the rear chamber is optional, "
                "FrontLoadedHorn requires a sealed rear chamber."
            )

        # Validate front chamber size if provided
        if params.front_chamber_volume and params.rear_chamber_volume:
            if params.front_chamber_volume > 0.5 * params.rear_chamber_volume:
                warnings.warn(
                    f"Front chamber ({params.front_chamber_volume:.1f} L) is "
                    f"larger than 50% of rear chamber ({params.rear_chamber_volume:.1f} L). "
                    f"Large front chambers can introduce unwanted resonances. "
                    f"Consider reducing front chamber size.",
                    UserWarning
                )

        # Initialize base class (sets throat_area, mouth_area, etc.)
        super().__init__(driver, params)

        # Validate mouth size
        self.validate_mouth_size()

    def _validate_compatibility(self) -> None:
        """
        Check if driver is suitable for front-loaded horn loading.

        Front-loaded horns typically require:
        - Low to moderate Qts (0.2-0.5) for tight control
        - Low to moderate Fs (< 100 Hz) for bass applications
        - Throat area matching driver size (0.5-1.5× Sd)
        - Appropriate rear chamber size (α = Vas/Vrc should be reasonable)
        """
        # Qts check - wider range than exponential horn due to rear chamber control
        qts = self.driver.qts
        if qts < 0.2:
            warnings.warn(
                f"Driver Qts={qts:.3f} is very low. "
                f"Front-loaded horns typically work best with Qts between 0.2-0.5. "
                f"Consider a larger rear chamber to achieve optimal Qtc.",
                UserWarning
            )
        elif qts > 0.5:
            warnings.warn(
                f"Driver Qts={qts:.3f} is high for front-loaded horn. "
                f"Consider Qts < 0.5 for optimal performance. "
                f"Rear chamber will help control the driver, but response may be peaked.",
                UserWarning
            )

        # Fs check
        if self.driver.fs > 100:
            warnings.warn(
                f"Driver Fs={self.driver.fs:.1f} Hz is high for front-loaded horn. "
                f"Horns work best with Fs < 100 Hz for bass applications.",
                UserWarning
            )

        # Throat size check
        if self.throat_area and self.driver.sd:
            throat_ratio = self.throat_area / self.driver.sd
            if throat_ratio < 0.5:
                warnings.warn(
                    f"Throat area ({self.throat_area*1e4:.1f} cm²) is "
                    f"{throat_ratio:.2f}x driver Sd. "
                    f"Throat should be >= 0.5x Sd to avoid compression.",
                    UserWarning
                )
            elif throat_ratio > 1.5:
                warnings.warn(
                    f"Throat area ({self.throat_area*1e4:.1f} cm²) is "
                    f"{throat_ratio:.2f}x driver Sd. "
                    f"Throat > 1.5x Sd may cause mismatch losses.",
                    UserWarning
                )

        # Rear chamber size check - compliance ratio
        alpha = self.driver.vas / self.params.rear_chamber_volume
        if alpha < 0.5:
            warnings.warn(
                f"Rear chamber is very large (α={alpha:.2f}). "
                f"This may result in under-damped response with weak bass. "
                f"Consider a smaller rear chamber for better control.",
                UserWarning
            )
        elif alpha > 5.0:
            warnings.warn(
                f"Rear chamber is very small (α={alpha:.2f}). "
                f"This may result in over-damped response with high Fc. "
                f"Consider a larger rear chamber for lower cutoff.",
                UserWarning
            )

    def calculate_throat_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate throat impedance for front-loaded horn.

        Uses the same infinite exponential horn model as ExponentialHorn,
        as the throat physics are identical. The front chamber (if present)
        slightly modifies this, but the effect is small for typical designs.

        Uses Kolbrek infinite horn approximation:
        Z_A = (ρ₀c/S_t) * (√(1 - m²/(4k²)) + j*m/(2k))

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex acoustic impedance at throat (Pa·s/m³)

        Raises:
            ValueError: If flare_rate is not specified
        """
        if not self.params.flare_rate:
            raise ValueError(
                "flare_rate required for throat impedance calculation. "
                "Specify either flare_rate or cutoff_frequency."
            )

        m = self.params.flare_rate  # flare rate (1/m)
        k = 2 * np.pi * frequencies / C  # wavenumber
        St = self.throat_area  # throat area (m²)

        # Characteristic impedance of air
        Z0 = (RHO * C) / St

        # Calculate impedance
        # Handle cutoff region (below fc, term becomes imaginary)
        k_term = 4 * k**2 - m**2

        # Above cutoff: real resistance
        # Below cutoff: purely reactive
        resistance = np.zeros_like(frequencies)
        above_cutoff = k_term > 0

        if np.any(above_cutoff):
            resistance[above_cutoff] = Z0 * np.sqrt(k_term[above_cutoff]) / (2 * k[above_cutoff])

        reactance = Z0 * m / (2 * k)

        return resistance + 1j * reactance

    def _calculate_high_pass_response(
        self,
        frequencies: np.ndarray,
        fc: float,
        q: float
    ) -> np.ndarray:
        """
        Calculate 2nd-order high-pass filter response.

        Transfer function: H(s) = s² / (s² + s×(ω₀/Q) + ω₀²)

        Args:
            frequencies: Array of frequencies (Hz)
            fc: Cutoff frequency (Hz)
            q: Quality factor

        Returns:
            Complex transfer function array
        """
        w = 2 * np.pi * frequencies
        w0 = 2 * np.pi * fc
        s = 1j * w

        H = s**2 / (s**2 + s * (w0 / q) + w0**2)
        return H

    def _calculate_horn_response(
        self,
        frequencies: np.ndarray,
        fs_loaded: float,
        fc_horn: float,
        horn_gain_db: float
    ) -> np.ndarray:
        """
        Calculate horn loading effect on frequency response.

        The horn loads the driver, shifting the effective resonance upward
        and providing gain. This is modeled as a smooth transition
        around the horn cutoff frequency.

        Args:
            frequencies: Array of frequencies (Hz)
            fs_loaded: Horn-loaded resonance frequency (Hz)
            fc_horn: Horn cutoff frequency (Hz)
            horn_gain_db: Horn gain (dB)

        Returns:
            Complex transfer function array representing horn effect
        """
        # Convert gain from dB to linear
        gain_factor = 10**(horn_gain_db / 20)

        # Smooth transition at horn cutoff
        w = 2 * np.pi * frequencies
        wc = 2 * np.pi * fc_horn

        # High-pass shaping for horn loading
        # Below cutoff: minimal effect
        # Above cutoff: apply horn gain
        H = (1j * w / wc) / (1 + 1j * w / wc)

        # Blend with unity gain below cutoff
        H = H * gain_factor + (1 - H)

        return H

    def _calculate_front_chamber_response(
        self,
        frequencies: np.ndarray
    ) -> np.ndarray:
        """
        Calculate front chamber compliance effect.

        The front chamber (if present) acts as a high-pass filter in series
        with the horn. The cutoff frequency depends on the throat area
        and chamber volume.

        fc_front ≈ c / (2π) × √(St / (Vfc × L_eff))

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex transfer function array (1.0 if no front chamber)
        """
        if not self.params.front_chamber_volume:
            return np.ones_like(frequencies, dtype=complex)

        # Front chamber volume (convert L to m³)
        Vfc = self.params.front_chamber_volume * 0.001
        St = self.throat_area
        L_eff = self.horn_length * 0.1  # Approximate effective length

        # Calculate front chamber cutoff
        fc_front = (C / (2 * np.pi)) * np.sqrt(St / (Vfc * L_eff + 1e-10))

        # First-order high-pass
        w = 2 * np.pi * frequencies
        wc = 2 * np.pi * fc_front
        H = (1j * w / wc) / (1 + 1j * w / wc)

        return H

    def calculate_frequency_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate frequency response for front-loaded horn.

        Combines three cascaded systems:
        1. Rear chamber sealed box (2nd-order high-pass)
        2. Horn loading effect (gain + loading)
        3. Front chamber compliance (optional high-pass)

        H_total = H_rear × H_horn × H_front_chamber

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)
        """
        # Step 1: Calculate rear chamber sealed box response
        alpha = self.driver.vas / self.params.rear_chamber_volume
        fc_rear = self.driver.fs * np.sqrt(alpha + 1)
        qtc = self.driver.qts * np.sqrt(alpha + 1)

        H_rear = self._calculate_high_pass_response(frequencies, fc_rear, qtc)

        # Step 2: Calculate horn loading effect
        horn_gain_db = self.calculate_horn_gain()
        loaded_params = self.calculate_loaded_parameters()
        fs_loaded = loaded_params['fs_loaded']

        try:
            fc_horn = self.calculate_cutoff_frequency()
        except ValueError:
            fc_horn = fs_loaded  # Fallback to loaded Fs

        H_horn = self._calculate_horn_response(frequencies, fs_loaded, fc_horn, horn_gain_db)

        # Step 3: Apply front chamber filtering (if present)
        H_front = self._calculate_front_chamber_response(frequencies)

        # Step 4: Combine responses
        H_total = H_rear * H_horn * H_front

        # Convert to dB SPL
        magnitude = np.abs(H_total)
        phase = np.angle(H_total, deg=True)

        spl_db = 20 * np.log10(magnitude + 1e-10)

        # Normalize to passband (200 Hz - 1 kHz)
        passband_mask = (frequencies >= 200) & (frequencies <= 1000)
        if np.any(passband_mask):
            passband_level = np.mean(spl_db[passband_mask])
            spl_db = spl_db - passband_level

        # Add sensitivity + horn gain
        spl_ref = self.calculate_sensitivity() + horn_gain_db
        spl_db = spl_db + spl_ref

        return spl_db, phase

    def calculate_system_q(self) -> float:
        """
        Calculate system Q factor for front-loaded horn.

        The system Q is dominated by the rear chamber compliance:
        Qtc = Qts × sqrt(α + 1)

        Horn loading slightly increases effective Q (reduces damping).
        Apply correction factor based on horn loading.

        Returns:
            System Q factor
        """
        # Rear chamber compliance dominates system Q
        alpha = self.driver.vas / self.params.rear_chamber_volume
        qtc_rear = self.driver.qts * np.sqrt(alpha + 1)

        # Horn loading slightly increases effective Q (reduces damping)
        loaded_params = self.calculate_loaded_parameters()
        loading_factor = loaded_params['fs_loaded'] / self.driver.fs

        # System Q is higher due to horn loading
        qtc_system = qtc_rear * loading_factor

        return qtc_system

    def calculate_f3(self) -> float:
        """
        Calculate -3dB frequency.

        Uses numerical method to find where response crosses -3dB
        relative to passband level.

        Returns:
            -3dB frequency (Hz)
        """
        frequencies = np.logspace(1, 3, 1000)  # 10 Hz - 1 kHz
        spl_db, _ = self.calculate_frequency_response(frequencies)

        return self._calculate_f3_numerical(frequencies, spl_db)

    def calculate_f10(self) -> float:
        """
        Calculate -10dB frequency.

        Uses numerical method to find where response crosses -10dB.

        Returns:
            -10dB frequency (Hz)
        """
        frequencies = np.logspace(1, 3, 1000)  # 10 Hz - 1 kHz
        spl_db, _ = self.calculate_frequency_response(frequencies)

        # Use maximum SPL as reference
        ref_level = np.max(spl_db)
        target_level = ref_level - 10.0

        # Find -10dB crossing
        for i in range(len(spl_db) - 1):
            if spl_db[i] <= target_level < spl_db[i + 1]:
                # Linear interpolation
                frac = (target_level - spl_db[i]) / (spl_db[i + 1] - spl_db[i])
                return frequencies[i] + frac * (frequencies[i + 1] - frequencies[i])

        # No crossing found
        if spl_db[0] > target_level:
            return frequencies[0]
        else:
            return frequencies[-1]

    def calculate_loaded_parameters(self) -> Dict[str, float]:
        """
        Calculate driver parameters with front-loaded horn configuration.

        Horn loading increases effective Fs (mass loading at throat).
        Rear chamber reduces effective Vas (compliance loading).

        Returns:
            Dictionary with loaded parameters:
            - 'fs_loaded': Loaded resonance frequency (Hz)
            - 'vas_loaded': Loaded compliance volume (L)
            - 'alpha_rear': Compliance ratio of rear chamber
        """
        try:
            fc = self.calculate_cutoff_frequency()
        except ValueError:
            # If no cutoff, assume no loading effect
            fc = self.driver.fs

        # Horn loading increases Fs (mass loading at throat)
        # fs_loaded = fs * sqrt(1 + (c / (2*pi*fc*St))^2)
        if self.throat_area:
            mass_loading_factor = (C / (2 * np.pi * fc * self.throat_area))**2
            fs_loaded = self.driver.fs * np.sqrt(1 + mass_loading_factor)
        else:
            fs_loaded = self.driver.fs

        # Vas effectively reduced by rear chamber compliance (required for FLH)
        alpha = self.driver.vas / self.params.rear_chamber_volume
        vas_loaded = self.driver.vas / (alpha + 1)

        return {
            'fs_loaded': fs_loaded,
            'vas_loaded': vas_loaded,
            'alpha_rear': alpha,
        }

    def get_design_parameters(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get horn design parameters for optimization.

        Returns dictionary with (value, min, max) tuples for parameters
        that can be optimized.

        Returns:
            Dictionary of designable parameters
        """
        params = {
            'rear_chamber_volume': (
                self.params.rear_chamber_volume,
                5.0,    # min
                100.0   # max
            ),
            'throat_area_cm2': (
                self.params.throat_area_cm2 if self.params.throat_area_cm2 else 50.0,
                10.0,   # min
                200.0   # max
            ),
            'mouth_area_cm2': (
                self.params.mouth_area_cm2 if self.params.mouth_area_cm2 else 1000.0,
                200.0,  # min
                5000.0  # max
            ),
            'horn_length_cm': (
                self.params.horn_length_cm if self.params.horn_length_cm2 else 100.0,
                50.0,   # min
                300.0   # max
            ),
        }

        # Add front chamber if present
        if self.params.front_chamber_volume:
            params['front_chamber_volume'] = (
                self.params.front_chamber_volume,
                0.5,    # min (very small)
                10.0    # max
            )

        # Add flare rate if specified
        if self.params.flare_rate:
            params['flare_rate'] = (
                self.params.flare_rate,
                1.0,    # min (very slow flare)
                20.0    # max (very fast flare)
            )

        return params

    def get_summary(self) -> Dict[str, any]:
        """
        Get comprehensive summary of front-loaded horn design and performance.

        Returns:
            Dictionary with design parameters and performance metrics
        """
        loaded = self.calculate_loaded_parameters()

        # Calculate key metrics
        f3 = self.calculate_f3()
        f10 = self.calculate_f10()
        q_system = self.calculate_system_q()
        horn_gain = self.calculate_horn_gain()

        try:
            cutoff_freq = self.calculate_cutoff_frequency()
        except ValueError:
            cutoff_freq = None

        # Calculate rear chamber metrics
        alpha = self.driver.vas / self.params.rear_chamber_volume
        fc_rear = self.driver.fs * np.sqrt(alpha + 1)

        summary = {
            # Design parameters
            'horn_type': 'front_loaded',
            'rear_chamber_volume_l': self.params.rear_chamber_volume,
            'front_chamber_volume_l': self.params.front_chamber_volume,
            'throat_area_cm2': self.params.throat_area_cm2,
            'mouth_area_cm2': self.params.mouth_area_cm2,
            'horn_length_cm': self.params.horn_length_cm,
            'area_ratio': self.mouth_area / self.throat_area if self.throat_area and self.mouth_area else None,
            'flare_rate': self.params.flare_rate,
            'cutoff_frequency_hz': cutoff_freq,

            # Driver parameters
            'driver_fs_hz': self.driver.fs,
            'driver_qts': self.driver.qts,
            'loaded_fs_hz': loaded['fs_loaded'],
            'loaded_vas_l': loaded['vas_loaded'],

            # Rear chamber metrics
            'compliance_ratio_alpha': alpha,
            'rear_fc_hz': fc_rear,

            # Performance metrics
            'system_q': q_system,
            'f3_hz': f3,
            'f10_hz': f10,
            'horn_gain_db': horn_gain,
            'sensitivity_db': self.calculate_sensitivity() + horn_gain,

            # Validation info
            'mouth_size_adequate': self._check_mouth_size(),
        }

        return summary

    def _check_mouth_size(self) -> bool:
        """Check if mouth size meets minimum requirement."""
        if self.mouth_area is None:
            return False

        try:
            fc = self.calculate_cutoff_frequency()
            mouth_radius = np.sqrt(self.mouth_area / np.pi)
            k_rm = (2 * np.pi * fc / C) * mouth_radius
            return k_rm >= 0.7
        except ValueError:
            return False
