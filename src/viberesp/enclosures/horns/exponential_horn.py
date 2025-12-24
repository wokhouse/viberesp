"""Exponential horn implementation."""

from typing import Dict, Tuple, List
import numpy as np
import warnings

from viberesp.enclosures.horns.base_horn import BaseHorn
from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.core.constants import C, RHO, VOLTAGE_1W_8OHM


class ExponentialHorn(BaseHorn):
    """
    Exponential horn enclosure implementation.

    An exponential horn has a cross-sectional area that increases exponentially
    with distance from the throat:

    S(x) = S_throat * exp(m * x)

    Where:
        S_throat = throat area
        m = flare rate (1/m)
        x = distance from throat

    This implementation uses a simplified model that treats the horn-loaded driver
    as a 2nd-order high-pass system with modified parameters and horn gain.

    Reference:
        - Olson, H.F. "Elements of Acoustical Engineering"
        - Beranek, L.L. "Acoustics"
        - Kolbrek, B. "Horn Theory: An Introduction"
    """

    def __init__(self, driver: ThieleSmallParameters, params: EnclosureParameters):
        """
        Initialize exponential horn.

        Args:
            driver: Thiele-Small parameters for the driver
            params: Enclosure parameters including:
                - throat_area_cm2: Throat area (cm²)
                - mouth_area_cm2: Mouth area (cm²)
                - horn_length_cm: Horn length (cm)
                - flare_rate: Exponential flare rate m (optional)
                - cutoff_frequency: Horn cutoff fc Hz (optional)
                - rear_chamber_volume: Rear chamber volume L (optional)
        """
        # Initialize base class first (sets throat_area, mouth_area, etc.)
        super().__init__(driver, params)

        # Validate mouth size (now that throat_area and mouth_area are set)
        self.validate_mouth_size()

    def _validate_compatibility(self) -> None:
        """
        Check if driver is suitable for exponential horn loading.

        Horns typically require:
        - Low Qts (< 0.4) for tight control
        - Low to moderate Fs (< 80 Hz) for bass applications
        - Throat area matching driver size
        """
        # Qts check
        if self.driver.qts > 0.4:
            warnings.warn(
                f"Driver Qts={self.driver.qts:.3f} > 0.4. "
                f"Horns typically require Qts < 0.4 for optimal loading. "
                f"Consider a driver with lower Qts for better horn performance.",
                UserWarning
            )

        # Fs check
        if self.driver.fs > 80:
            warnings.warn(
                f"Driver Fs={self.driver.fs:.1f} Hz is high for horn loading. "
                f"Horns work best with Fs < 80 Hz for bass applications. "
                f"Consider a lower Fs driver.",
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

    def calculate_throat_impedance(self, frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate throat impedance for infinite exponential horn.

        Uses the infinite horn approximation from Kolbrek:

        Z_A = (ρ₀c/S_t) * (√(1 - m²/(4k²)) + j*m/(2k))

        Above cutoff (f > fc): resistive + reactive
        Below cutoff (f < fc): purely reactive (evanescent waves)

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex acoustic impedance at throat (Pa·s/m³)
        """
        # Get or calculate flare rate from cutoff frequency
        m = self._get_or_calculate_flare_rate()  # flare rate (1/m)
        k = 2 * np.pi * frequencies / C  # wavenumber
        St = self.throat_area  # throat area (m²)

        # Characteristic impedance of air
        Z0 = (RHO * C) / St

        # Calculate impedance
        # Handle cutoff region (below fc, term becomes imaginary)
        # Use maximum to avoid NaN
        k_term = 4 * k**2 - m**2

        # Above cutoff: real resistance
        # Below cutoff: purely reactive
        resistance = np.zeros_like(frequencies)
        above_cutoff = k_term > 0

        if np.any(above_cutoff):
            resistance[above_cutoff] = Z0 * np.sqrt(k_term[above_cutoff]) / (2 * k[above_cutoff])

        reactance = Z0 * m / (2 * k)

        return resistance + 1j * reactance

    def calculate_frequency_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate frequency response using physics-based model.

        Phase 1 Enhancement: Uses acoustic impedance chain method instead
        of empirical 2nd-order high-pass approximation.

        Physics model:
        1. Calculate driver mechanical impedance with horn loading
        2. Calculate electrical impedance with motional branch
        3. Calculate volume velocity at throat
        4. Calculate acoustic pressure at listening position
        5. Convert to SPL

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)
        """
        # Reference pressure (20 μPa)
        P_ref = 20e-6

        # Check if physics model should be used
        use_physics = getattr(self.params, 'use_physics_model', True)

        if not use_physics:
            # Fall back to empirical model (for backward compatibility)
            return self._calculate_empirical_response(frequencies, voltage)

        # Physics-based calculation
        try:
            # Calculate volume velocity at throat
            U_throat = self._calculate_volume_velocity(frequencies, voltage)

            # Calculate acoustic pressure at listening position
            P_r = self._calculate_acoustic_pressure(frequencies, U_throat, distance=1.0)

            # Convert to SPL
            spl_db = 20 * np.log10(np.abs(P_r) / P_ref)

            # Calculate phase
            phase_degrees = np.angle(P_r, deg=True)

            return spl_db, phase_degrees

        except Exception as e:
            # Fallback to empirical model on error
            warnings.warn(
                f"Physics model failed: {e}. Falling back to empirical model.",
                UserWarning
            )
            return self._calculate_empirical_response(frequencies, voltage)

    def _calculate_empirical_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Original empirical model (kept for backward compatibility).

        Simplified model:
        1. Calculate loaded driver parameters (Fs shifts up due to horn loading)
        2. Model as 2nd-order high-pass with loaded parameters
        3. Add horn gain from area ratio

        Transfer function:
        H(s) = s² / (s² + s*(ω₀/Q) + ω₀²)

        Where ω₀ = 2π*fs_loaded and Q = system Q with horn loading

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)
        """
        # Get loaded parameters
        loaded = self.calculate_loaded_parameters()
        fs = loaded['fs_loaded']

        # Calculate system Q for horn-loaded driver
        # Q_horn ≈ Qts * (original Fs / loaded Fs)
        # This approximates the effect of horn loading on system damping
        q_horn = self.driver.qts * (self.driver.fs / fs)

        # Calculate reference efficiency + horn gain
        horn_gain_db = self.calculate_horn_gain()
        spl_ref = self.calculate_sensitivity() + horn_gain_db

        # 2nd-order high-pass transfer function
        w = 2 * np.pi * frequencies
        w0 = 2 * np.pi * fs
        s = 1j * w

        # H(s) = s² / (s² + s*(w0/Q) + w0²)
        H = s**2 / (s**2 + s * (w0 / q_horn) + w0**2)

        magnitude = np.abs(H)
        phase = np.angle(H, deg=True)

        # Convert to dB
        spl_db = 20 * np.log10(magnitude + 1e-10)

        # Normalize to passband (200 Hz - 1 kHz)
        passband_mask = (frequencies >= 200) & (frequencies <= 1000)
        if np.any(passband_mask):
            passband_level = np.mean(spl_db[passband_mask])
            spl_db = spl_db - passband_level

        # Add sensitivity + horn gain
        spl_db = spl_db + spl_ref

        return spl_db, phase


    def calculate_system_q(self) -> float:
        """
        Calculate system Q factor for horn-loaded driver.

        The system Q accounts for horn loading effect:
        Q_horn ≈ Qts * (original Fs / loaded Fs)

        Returns:
            System Q factor
        """
        loaded = self.calculate_loaded_parameters()
        fs_loaded = loaded['fs_loaded']

        q_horn = self.driver.qts * (self.driver.fs / fs_loaded)
        return q_horn

    def calculate_f3(self) -> float:
        """
        Calculate -3dB frequency.

        For the 2nd-order high-pass model with system Q, F3 is found
        numerically by finding where the response is 3dB below passband.

        Returns:
            -3dB frequency (Hz)
        """
        # Use numerical search for F3
        frequencies = np.logspace(1, 3, 1000)  # 10 Hz - 1 kHz

        # Calculate response at reference voltage
        spl_db, _ = self.calculate_frequency_response(frequencies)

        # Find passband level (200-1000 Hz)
        passband_mask = (frequencies >= 200) & (frequencies <= 1000)
        if not np.any(passband_mask):
            return 0.0

        passband_level = np.mean(spl_db[passband_mask])
        target_level = passband_level - 3.0

        # Find frequency where response crosses -3dB
        # Use linear interpolation for accuracy
        below_f3 = spl_db < target_level

        if not np.any(below_f3):
            return frequencies[-1]

        # First crossing
        idx = np.argmax(below_f3)

        if idx == 0:
            return frequencies[0]

        # Linear interpolation
        f1, f2 = frequencies[idx - 1], frequencies[idx]
        spl1, spl2 = spl_db[idx - 1], spl_db[idx]

        f3 = f1 + (f2 - f1) * (target_level - spl1) / (spl2 - spl1)

        return f3

    def calculate_f10(self) -> float:
        """
        Calculate -10dB frequency.

        Uses same numerical method as F3 but with -10dB target.

        Returns:
            -10dB frequency (Hz)
        """
        frequencies = np.logspace(1, 3, 1000)  # 10 Hz - 1 kHz
        spl_db, _ = self.calculate_frequency_response(frequencies)

        # Find passband level
        passband_mask = (frequencies >= 200) & (frequencies <= 1000)
        if not np.any(passband_mask):
            return 0.0

        passband_level = np.mean(spl_db[passband_mask])
        target_level = passband_level - 10.0

        # Find -10dB point
        below_f10 = spl_db < target_level

        if not np.any(below_f10):
            return frequencies[-1]

        idx = np.argmax(below_f10)

        if idx == 0:
            return frequencies[0]

        # Linear interpolation
        f1, f2 = frequencies[idx - 1], frequencies[idx]
        spl1, spl2 = spl_db[idx - 1], spl_db[idx]

        f10 = f1 + (f2 - f1) * (target_level - spl1) / (spl2 - spl1)

        return f10

    def get_design_parameters(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get horn design parameters for optimization.

        Returns dictionary with (value, min, max) tuples for parameters
        that can be optimized.

        Returns:
            Dictionary of designable parameters
        """
        params = {
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
                self.params.horn_length_cm if self.params.horn_length_cm else 100.0,
                50.0,   # min
                300.0   # max
            ),
        }

        # Add flare rate if specified
        if self.params.flare_rate:
            params['flare_rate'] = (
                self.params.flare_rate,
                1.0,    # min (very slow flare)
                20.0    # max (very fast flare)
            )

        # Add rear chamber if present
        if self.params.rear_chamber_volume:
            params['rear_chamber_volume'] = (
                self.params.rear_chamber_volume,
                5.0,    # min
                100.0   # max
            )

        return params

    def get_summary(self) -> Dict[str, any]:
        """
        Get comprehensive summary of horn design and performance.

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

        summary = {
            # Design parameters
            'horn_type': 'exponential',
            'throat_area_cm2': self.params.throat_area_cm2,
            'mouth_area_cm2': self.params.mouth_area_cm2,
            'horn_length_cm': self.params.horn_length_cm,
            'area_ratio': self.mouth_area / self.throat_area if self.throat_area and self.mouth_area else None,
            'flare_rate': self.params.flare_rate,
            'cutoff_frequency_hz': cutoff_freq,
            'rear_chamber_volume_l': self.params.rear_chamber_volume,

            # Driver parameters
            'driver_fs_hz': self.driver.fs,
            'driver_qts': self.driver.qts,
            'loaded_fs_hz': loaded['fs_loaded'],
            'loaded_vas_l': loaded['vas_loaded'],

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
