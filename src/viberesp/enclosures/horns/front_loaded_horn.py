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
        Calculate throat impedance for front-loaded horn using finite horn model.

        Phase 1 Enhancement: Now uses proper finite horn transmission line model
        with mouth radiation impedance boundary condition.

        The throat impedance accounts for:
        - Finite horn length effects (transmission line)
        - Mouth radiation impedance (Beranek circular piston model)
        - Proper impedance transformation from mouth to throat

        Uses transmission line impedance transformation:
        Z_throat = Z_char × coth(γ×L) + Z_mouth / sinh²(γ×L)

        Where:
        - Z_char is characteristic impedance at throat
        - γ is complex propagation constant
        - Z_mouth is mouth radiation impedance
        - L is effective horn length

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex acoustic impedance at throat (Pa·s/m³)

        Raises:
            ValueError: If flare_rate is not specified
        """
        # Get mouth radiation impedance (Beranek model if enabled)
        Z_mouth = self.calculate_mouth_radiation_impedance(frequencies)

        # Calculate characteristic impedance at throat
        Z_char = self._calculate_characteristic_impedance()

        # Calculate propagation constant
        gamma = self._calculate_propagation_constant(frequencies)

        # Get effective horn length (with end correction if enabled)
        L_eff = self.calculate_effective_length()

        # Calculate hyperbolic functions for transmission line
        # Z_throat = Z_char × coth(γ×L) + Z_mouth / sinh²(γ×L)
        gamma_L = gamma * L_eff

        # Avoid overflow in hyperbolic functions
        # Use identities: coth(z) = cosh(z)/sinh(z), 1/sinh²(z) = cosh(z)/sinh(z) × 1/sinh(z)

        sinh_gamma_L = np.sinh(gamma_L)
        cosh_gamma_L = np.cosh(gamma_L)

        # Avoid division by zero
        sinh_gamma_L = np.where(np.abs(sinh_gamma_L) < 1e-10, 1e-10, sinh_gamma_L)

        # coth(γ×L) = cosh(γ×L) / sinh(γ×L)
        coth_gamma_L = cosh_gamma_L / sinh_gamma_L

        # Calculate throat impedance with mouth loading
        # First term: characteristic impedance times coth(γL)
        term1 = Z_char * coth_gamma_L

        # Second term: mouth impedance divided by sinh²(γL)
        term2 = Z_mouth / (sinh_gamma_L ** 2)

        Z_throat = term1 + term2

        return Z_throat

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
        fc_horn: float,
        horn_gain_db: float
    ) -> np.ndarray:
        """
        Calculate horn loading effect on frequency response.

        The horn provides gain above its cutoff frequency through
        acoustic impedance transformation. Below cutoff, the horn
        provides minimal loading and radiation is attenuated.

        This models the horn as:
        - Below fc: Attenuation (horn acts as reactive load)
        - Above fc: Full horn gain with smooth transition

        Args:
            frequencies: Array of frequencies (Hz)
            fc_horn: Horn cutoff frequency (Hz)
            horn_gain_db: Horn gain (dB)

        Returns:
            Complex transfer function array representing horn effect
        """
        # Convert gain from dB to linear
        gain_factor = 10**(horn_gain_db / 20)

        # Smooth transition at horn cutoff (2nd-order for realistic roll-off)
        w = 2 * np.pi * frequencies
        wc = 2 * np.pi * fc_horn
        s = 1j * w

        # 2nd-order high-pass Butterworth response for horn loading
        # This gives a -12dB/octave roll-off below cutoff
        H = s**2 / (s**2 + s * (wc / 0.707) + wc**2)

        # Apply horn gain above cutoff
        # Use absolute value to get magnitude, then apply gain smoothly
        H_mag = np.abs(H)
        H = H_mag * (gain_factor - 1) + 1

        return H.astype(complex)

    def _calculate_modal_response(
        self,
        frequencies: np.ndarray,
        f_n: float,
        Q_n: float
    ) -> np.ndarray:
        """
        Calculate single modal response for a resonant mode.

        Uses 2nd-order resonator transfer function:
        H_n(f) = (f/f_n)² / [(1 - (f/f_n)²) + j(f/f_n)/Q_n]

        Args:
            frequencies: Array of frequencies (Hz)
            f_n: Modal resonance frequency (Hz)
            Q_n: Modal quality factor

        Returns:
            Complex modal response array
        """
        # Frequency ratio
        f_ratio = frequencies / f_n

        # Avoid division by zero
        f_ratio = np.where(f_ratio < 1e-10, 1e-10, f_ratio)

        # 2nd-order resonator transfer function
        # H(s) = s² / (s² + s×(ω₀/Q) + ω₀²)
        # In frequency domain with s = jω:
        # H(jω) = -(ω/ω₀)² / [-(ω/ω₀)² + j(ω/ω₀)/Q + 1]

        numer = -f_ratio**2
        denom = -f_ratio**2 + 1j * f_ratio / Q_n + 1

        H_n = numer / denom

        return H_n

    def _calculate_effective_chamber_length(self) -> float:
        """
        Calculate effective acoustic length of front chamber.

        Converts chamber volume to equivalent cylindrical pipe length
        for standing wave calculations.

        For a volume V and throat area S_throat:
        L_eff = V / S_throat

        This represents the length of a constant-area pipe with the
        same volume as the front chamber.

        Returns:
            Effective chamber length (m)
        """
        if not self.params.front_chamber_volume:
            return 0.0

        # Get throat area (m²)
        if self.params.front_chamber_area_cm2:
            throat_area_m2 = self.params.front_chamber_area_cm2 * 1e-4
        elif self.throat_area:
            throat_area_m2 = self.throat_area
        else:
            return 0.0

        # Convert volume to m³
        volume_m3 = self.params.front_chamber_volume * 0.001

        # Effective length = Volume / Area
        L_eff = volume_m3 / throat_area_m2

        return L_eff

    def _calculate_standing_wave_q(self, mode_number: int) -> float:
        """
        Calculate Q factor for standing wave mode in front chamber.

        Higher modes have lower Q due to increased radiation losses
        and wall damping. Q scales approximately as 1/(2n+1).

        Args:
            mode_number: Standing wave mode number (1 or 2)

        Returns:
            Q factor for the mode
        """
        # Base Q for fundamental Helmholtz mode
        # This depends on horn throat loading
        if self.throat_area:
            Z0 = (RHO * C) / self.throat_area
        else:
            Z0 = RHO * C / 0.01

        # Q decreases with mode number due to increased losses
        # Empirical scaling: Q_n ≈ Q_base / (2n + 1)
        q_base = 5.0  # Typical Q for front chamber modes
        q_mode = q_base / (2 * mode_number + 1)

        return q_mode

    def _calculate_rear_chamber_impedance(
        self,
        frequencies: np.ndarray
    ) -> np.ndarray:
        """
        Calculate rear chamber acoustic impedance.

        Models rear chamber as sealed box compliance:
        Z_rc = 1 / (jω × C_rc)

        Where C_rc = V_rc / (ρ₀ × c²)

        The rear chamber acts as a compliance in parallel with the horn throat load,
        affecting the driver's mechanical impedance and system response.

        Args:
            frequencies: Frequency array (Hz)

        Returns:
            Complex rear chamber impedance (Pa·s/m³)
        """
        if self.params.rear_chamber_volume <= 0:
            return np.inf * np.ones_like(frequencies, dtype=complex)

        # Rear chamber compliance (m³/Pa)
        # C = V / (ρ₀ × c²)
        V_rc = self.params.rear_chamber_volume / 1000  # L → m³
        C_rc = V_rc / (RHO * C**2)

        # Angular frequency
        omega = 2 * np.pi * frequencies

        # Rear chamber impedance (purely compliant)
        # Z = 1 / (jωC)
        Z_rc = 1 / (1j * omega * C_rc)

        return Z_rc

    def _calculate_driver_mechanical_impedance(
        self,
        frequencies: np.ndarray,
        Z_acoustic_load: np.ndarray
    ) -> np.ndarray:
        """
        Calculate driver mechanical impedance with acoustic loading.

        Phase 1 Enhancement: Includes rear chamber AND front chamber compliance in parallel with throat load.

        Z_m = R_ms + jωM_ms + 1/(jωC_ms) + S_d² × Z_acoustic_combined

        Where Z_acoustic_combined combines throat, rear chamber, and front chamber impedances in parallel:
        1/Z_acoustic_combined = 1/Z_throat + 1/Z_rc + 1/Z_fc

        This properly models the acoustic circuit where the driver diaphragm sees all three
        acoustic loads simultaneously (throat path, rear chamber compliance, front chamber compliance).

        Args:
            frequencies: Frequency array (Hz)
            Z_acoustic_load: Acoustic impedance at throat (Pa·s/m³)

        Returns:
            Complex mechanical impedance (N·s/m)
        """
        omega = 2 * np.pi * frequencies

        # Mechanical resistance
        R_ms = self.driver.rms

        # Moving mass
        M_ms = self.driver.mms / 1000  # g → kg

        # Mechanical compliance
        C_ms = self.driver.cms

        # Diaphragm area (m²)
        S_d = self.driver.sd

        # Combine rear chamber AND front chamber in parallel with throat load
        # Start with throat impedance
        Z_acoustic_combined = Z_acoustic_load

        # Add rear chamber compliance (already correct)
        if self.params.rear_chamber_volume > 0:
            Z_rc = self._calculate_rear_chamber_impedance(frequencies)
            # Parallel combination: Z_total = (Z1 * Z2) / (Z1 + Z2)
            Z_acoustic_combined = (Z_acoustic_combined * Z_rc) / (Z_acoustic_combined + Z_rc)

        # NEW: Add front chamber compliance (Phase 1 fix)
        # Front chamber is in PARALLEL with throat, meaning driver can push
        # air either into the horn throat OR compress the front chamber
        if self.params.front_chamber_volume:
            Z_fc = self._calculate_front_chamber_impedance(frequencies)
            # Parallel combination
            Z_acoustic_combined = (Z_acoustic_combined * Z_fc) / (Z_acoustic_combined + Z_fc)

        # Radiation loading from combined acoustic impedance
        Z_rad_load = (S_d ** 2) * Z_acoustic_combined

        # Mechanical impedance
        Z_m = R_ms + 1j * omega * M_ms + 1 / (1j * omega * C_ms) + Z_rad_load

        return Z_m

    def _calculate_front_chamber_response(
        self,
        frequencies: np.ndarray
    ) -> np.ndarray:
        """
        Calculate front chamber effect on frequency response.

        Phase 1 Enhancement: Multi-mode pipe resonator model.

        Models front chamber as closed-open pipe with standing wave modes.
        Each mode contributes with Q-dependent damping.

        Modes:
        - n=0: Fundamental Helmholtz resonance (mass-spring system)
        - n=1,2: Standing wave modes at f_n = (2n+1)×c/(4×L_eff)

        The number of modes is controlled by `front_chamber_modes` parameter:
        - 0 (default): Helmholtz only (backward compatible)
        - 3: Full multi-mode model with standing waves

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex transfer function array (1.0 if no front chamber)
        """
        if not self.params.front_chamber_volume:
            return np.ones_like(frequencies, dtype=complex)

        # Check how many modes to calculate
        num_modes = getattr(self.params, 'front_chamber_modes', 0)

        # Calculate acoustic compliance and mass for Helmholtz mode
        C_fc = self._calculate_acoustic_compliance(self.params.front_chamber_volume)

        # Use Hornresp-compatible acoustic parameters
        if self.params.front_chamber_area_cm2:
            area_cm2 = self.params.front_chamber_area_cm2
        else:
            area_cm2 = self.params.throat_area_cm2 if self.params.throat_area_cm2 else 50.0

        if self.params.rear_chamber_length_cm:
            length_m = self.params.rear_chamber_length_cm * 0.01
        else:
            length_m = self.calculate_effective_length() if self.horn_length else 0.0

        M_horn = self._calculate_acoustic_mass(area_cm2, length_m)

        # Calculate fundamental Helmholtz frequency (n=0)
        f_helmholtz = self._calculate_helmholtz_resonance(C_fc, M_horn)

        # Calculate Q for Helmholtz mode
        Q_helmholtz = self._calculate_helmholtz_q(f_helmholtz, C_fc, M_horn)

        # Start with Helmholtz mode (n=0)
        modes = [self._calculate_modal_response(frequencies, f_helmholtz, Q_helmholtz)]

        # If multi-mode enabled, add standing wave modes
        if num_modes >= 3:
            # Get effective chamber length for standing waves
            L_eff_chamber = self._calculate_effective_chamber_length()

            # Calculate standing wave modes n=1, n=2
            for n in [1, 2]:
                # Closed-open pipe resonator: f_n = (2n+1)×c/(4×L_eff)
                f_n = (2 * n + 1) * C / (4 * L_eff_chamber)

                # Get Q for this mode
                Q_n = self._calculate_standing_wave_q(n)

                # Calculate modal response
                H_n = self._calculate_modal_response(frequencies, f_n, Q_n)
                modes.append(H_n)

        # Sum all modal responses (coherent summation)
        H_total = np.sum(modes, axis=0)

        # Normalize to preserve energy (modes should sum to unity at high frequency)
        # At high frequencies well above all resonances, response → 1
        H_norm = H_total / (len(modes) + 1e-10)

        # Apply gentle low-frequency roll-off to avoid artificial boost
        # This preserves physical behavior while preventing numerical artifacts
        w = 2 * np.pi * frequencies
        wc = 2 * np.pi * f_helmholtz
        lf_rolloff = (1j * w / wc) / (1 + 1j * w / wc)

        H_final = H_norm * lf_rolloff

        return H_final

    def _calculate_front_chamber_impedance(
        self,
        frequencies: np.ndarray
    ) -> np.ndarray:
        """
        Calculate front chamber acoustic impedance (compliance only).

        Phase 1: Pure Helmholtz compliance model (no standing waves yet).

        Front chamber acts as acoustic compliance:
        Z_chamber = 1 / (jω × C_chamber)

        Where C_chamber = V_front / (ρ₀ × c²)

        This impedance is in PARALLEL with throat impedance, meaning
        the driver sees both loads simultaneously. The parallel combination
        properly models the acoustic circuit where driver diaphragm drives
        into throat AND front chamber at the same time.

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Complex front chamber impedance (Pa·s/m³)
        """
        if not self.params.front_chamber_volume:
            return np.inf * np.ones_like(frequencies, dtype=complex)

        # Front chamber compliance (m³/Pa)
        # C = V / (ρ₀ × c²)
        C_fc = self._calculate_acoustic_compliance(self.params.front_chamber_volume)

        # Angular frequency
        omega = 2 * np.pi * frequencies

        # Front chamber impedance (purely compliant)
        # Z = 1 / (jωC)
        Z_fc = 1 / (1j * omega * C_fc)

        return Z_fc

    def _calculate_horn_mass_loading(self, frequencies: np.ndarray) -> np.ndarray:
        """
        Calculate frequency-dependent mass loading from horn.

        Below cutoff, horn acts as reactive mass load.
        Above cutoff, horn provides impedance transformation.

        The reactive mass loading follows transmission line theory:
        - At low frequencies (kL << 1): Horn adds significant mass
        - At high frequencies (kL >> 1): Horn becomes resistive (no mass loading)

        Args:
            frequencies: Array of frequencies (Hz)

        Returns:
            Array of mass loading factors (unitless, ratio of M_horn/M_driver)
        """
        # Get horn parameters
        try:
            fc = self.calculate_cutoff_frequency()
        except ValueError:
            return np.zeros_like(frequencies)

        # Throat area (m²)
        St = self.throat_area

        # Effective horn length with end correction
        L_eff = self.calculate_effective_length()

        # Wavenumber array
        k = 2 * np.pi * frequencies / C

        # Reactive mass loading from horn (below cutoff)
        # Based on transmission line model for exponential horn
        kL = k * L_eff

        # For small kL (low frequencies): M_horn ≈ (ρ₀ × St × L) / 3
        # For large kL (high frequencies): M_horn → 0 (resistive loading)

        # Smooth transition using tanh(kL) / kL
        # This approximates the mass loading ratio from transmission line theory
        mass_loading_ratio = np.tanh(kL) / (kL + 1e-10)

        # Mass loading normalized to driver mass
        # M_horn / Mms (unitless ratio)
        rho_air = 1.18  # kg/m³ (air density)

        # Phase 1: Front chamber compliance now properly modeled in impedance chain
        # Reduce calibration factor from 4.0 → 1.0 as compensation is no longer needed
        # The previous 4.0× factor was compensating for missing front chamber physics
        calibration_factor = 1.0  # Was: 4.0 (before Phase 1 fix)

        M_horn = rho_air * St * L_eff * mass_loading_ratio * calibration_factor

        # Convert driver Mms from g to kg (Mms is the moving mass)
        Mms_kg = self.driver.mms / 1000 if self.driver.mms else 0.1

        # Return unitless mass loading factor
        mass_loading_factor = M_horn / (Mms_kg + 1e-10)

        return mass_loading_factor

    def _calculate_acoustic_compliance(self, volume_liters: float) -> float:
        """
        Calculate acoustic compliance of a chamber.

        C_acoustic = V / (ρ₀ × c²)

        Args:
            volume_liters: Chamber volume in liters

        Returns:
            Acoustic compliance in m⁵/N
        """
        from viberesp.core.constants import RHO, C

        volume_m3 = volume_liters * 0.001
        return volume_m3 / (RHO * C**2)

    def _calculate_acoustic_mass(self, area_cm2: float, length_m: float) -> float:
        """
        Calculate acoustic mass of a tube/horn section.

        M_acoustic = ρ₀ × L / S

        Args:
            area_cm2: Cross-sectional area in cm²
            length_m: Effective length in meters

        Returns:
            Acoustic mass in kg/m⁴
        """
        from viberesp.core.constants import RHO, CM2_TO_M2

        area_m2 = area_cm2 * CM2_TO_M2
        return RHO * length_m / area_m2

    def _calculate_helmholtz_resonance(
        self,
        compliance_m5_n: float,
        mass_kg_m4: float
    ) -> float:
        """
        Calculate Helmholtz resonance frequency.

        f_h = 1 / (2π × √(M × C))

        Args:
            compliance_m5_n: Acoustic compliance (m⁵/N)
            mass_kg_m4: Acoustic mass (kg/m⁴)

        Returns:
            Resonance frequency in Hz
        """
        return 1.0 / (2 * np.pi * np.sqrt(mass_kg_m4 * compliance_m5_n))

    def _calculate_helmholtz_q(
        self,
        resonance_freq: float,
        compliance_m5_n: float,
        mass_kg_m4: float,
        resistance: float = None
    ) -> float:
        """
        Calculate Q factor of Helmholtz resonator.

        Q = (1/R) × √(M/C) for parallel RLC
        Q = R × √(C/M) for series RLC

        Uses horn radiation resistance as damping.

        Args:
            resonance_freq: Resonance frequency (Hz)
            compliance_m5_n: Acoustic compliance (m⁵/N)
            mass_kg_m4: Acoustic mass (kg/m⁴)
            resistance: Acoustic resistance (optional, auto-calculated if None)

        Returns:
            Q factor (unitless)
        """
        from viberesp.core.constants import RHO, C

        if resistance is None:
            # Use horn characteristic impedance as reference
            # Z0 = (ρ₀ × c) / S_throat
            Z0 = (RHO * C) / self.throat_area if self.throat_area else (RHO * C) / 0.01
            resistance = Z0

        # Acoustic impedance at resonance
        # Z_acoustic = √(M/C) = 1/(2π × fc × C)
        z_acoustic = 1.0 / (2 * np.pi * resonance_freq * compliance_m5_n)

        # Q depends on coupling configuration
        # For driver-loaded system, Q is typically high (under-damped)
        q_factor = z_acoustic / resistance

        return q_factor

    def calculate_frequency_response(
        self,
        frequencies: np.ndarray,
        voltage: float = VOLTAGE_1W_8OHM
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate frequency response for front-loaded horn using physics-based model.

        Phase 1 Enhancement: Front chamber impedance is now properly integrated into the impedance chain.

        Physics model:
        1. Calculate driver mechanical impedance with horn loading
        2. Include rear chamber AND front chamber compliance in parallel with throat load
        3. Calculate electrical impedance with motional branch
        4. Calculate volume velocity at throat (driver already sees front chamber impedance)
        5. Calculate acoustic pressure at listening position
        6. Convert to SPL

        Note: Front chamber is no longer applied as post-processing transfer function.
        It is properly modeled in the impedance chain via parallel combination in
        _calculate_driver_mechanical_impedance().

        Args:
            frequencies: Array of frequencies (Hz)
            voltage: Input voltage (default: 2.83V for 1W into 8Ω)

        Returns:
            (spl_magnitude_db, phase_degrees)

        Raises:
            RuntimeError: If physics model calculation fails
        """
        P_ref = 20e-6

        # Physics-only calculation (empirical model removed in Phase 1)
        try:
            # Calculate volume velocity at throat
            # Front chamber impedance is now included in Z_acoustic_combined
            # so driver already sees it in the impedance chain
            U_throat = self._calculate_volume_velocity(frequencies, voltage)

            # Calculate acoustic pressure at listening position
            # No front chamber post-processing needed
            P_r = self._calculate_acoustic_pressure(frequencies, U_throat, distance=1.0)

            # Convert to SPL
            spl_db = 20 * np.log10(np.abs(P_r) / P_ref)

            # Calculate phase
            phase_degrees = np.angle(P_r, deg=True)

            return spl_db, phase_degrees

        except Exception as e:
            # Raise error instead of silent fallback
            raise RuntimeError(
                f"Physics model calculation failed: {e}\n"
                f"Front-loaded horn requires physics model. "
                f"Check parameters and ensure all required values are provided."
            ) from e

    def calculate_system_q(self) -> float:
        """
        Calculate system Q factor for front-loaded horn.

        The system Q is dominated by the rear chamber compliance:
        Qtc = Qts × sqrt(α + 1)

        Horn loading has minimal effect on system Q for front-loaded horns,
        as the horn primarily provides impedance transformation rather
        than changing the damping characteristics significantly.

        Returns:
            System Q factor
        """
        # Rear chamber compliance dominates system Q
        alpha = self.driver.vas / self.params.rear_chamber_volume
        qtc_system = self.driver.qts * np.sqrt(alpha + 1)

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

        Uses coupled impedance model accounting for:
        - Rear chamber compliance (stiffer spring)
        - Horn reactive mass loading (frequency-dependent)
        - Front chamber Helmholtz resonance (NEW)

        The system resonance is determined by the coupled mechanical impedance:
        Z_system = Z_driver + Z_rear_chamber + Z_horn_reactive + Z_front_chamber

        Below cutoff, the horn adds reactive mass loading, shifting Fs upward.
        When a front chamber is present, it creates an additional Helmholtz resonator
        that further modifies the system resonance.

        Returns:
            Dictionary with loaded parameters:
            - 'fs_loaded': Loaded resonance frequency (Hz)
            - 'vas_loaded': Loaded compliance volume (L)
            - 'alpha_rear': Compliance ratio of rear chamber
            - 'mass_loading_ratio': Horn mass loading at driver Fs
            - 'f_helmholtz': Front chamber Helmholtz resonance (Hz), if present
        """
        # Rear chamber compliance ratio
        alpha = self.driver.vas / self.params.rear_chamber_volume

        # Vas is effectively reduced by rear chamber compliance
        vas_loaded = self.driver.vas / (alpha + 1)

        # Get horn cutoff frequency
        try:
            fc_horn = self.calculate_cutoff_frequency()
        except ValueError:
            fc_horn = self.driver.fs

        # Calculate horn mass loading at driver Fs
        # This represents the additional inertial load from the horn
        fs_array = np.array([self.driver.fs])
        mass_loading_at_fs = self._calculate_horn_mass_loading(fs_array)[0]

        # Effective moving mass including horn loading
        Mms_kg = self.driver.mms / 1000 if self.driver.mms else 0.1  # g to kg
        Mms_effective = Mms_kg * (1 + mass_loading_at_fs)

        # System resonance with mass loading
        # fs_loaded = 1 / (2π × sqrt(Cms_effective × Mms_effective))
        # where Cms_effective = Cms / (alpha + 1)

        if self.driver.cms:
            Cms_m_per_N = self.driver.cms  # m/N
        else:
            # Calculate Cms from Vas if not provided
            # Vas = ρ₀ × c² × Sd² × Cms
            # Cms = Vas / (ρ₀ × c² × Sd²)
            rho_air = 1.18  # kg/m³
            vas_m3 = self.driver.vas * 0.001  # L to m³
            Cms_m_per_N = vas_m3 / (rho_air * C**2 * self.driver.sd**2 + 1e-10)

        Cms_effective = Cms_m_per_N / (alpha + 1)

        # Calculate loaded resonance frequency
        fs_loaded = 1 / (2 * np.pi * np.sqrt(Cms_effective * Mms_effective))

        # NEW: Calculate Helmholtz resonance if front chamber present
        if self.params.front_chamber_volume and self.throat_area:
            C_fc = self._calculate_acoustic_compliance(self.params.front_chamber_volume)

            # Use Hornresp-compatible parameters for front chamber Helmholtz resonance
            if self.params.front_chamber_area_cm2:
                area_cm2 = self.params.front_chamber_area_cm2
            else:
                area_cm2 = self.params.throat_area_cm2 if self.params.throat_area_cm2 else 50.0

            if self.params.rear_chamber_length_cm:
                length_m = self.params.rear_chamber_length_cm * 0.01
            else:
                length_m = self.calculate_effective_length() if self.horn_length else 0.0

            M_horn = self._calculate_acoustic_mass(area_cm2, length_m)
            f_helmholtz = self._calculate_helmholtz_resonance(C_fc, M_horn)

            # Coupled system resonance (driver + front chamber)
            # For coupled resonators: 1/f²_eff = 1/f²_driver + 1/f²_helmholtz
            f_system = 1.0 / np.sqrt(1.0/fs_loaded**2 + 1.0/f_helmholtz**2)
        else:
            f_system = fs_loaded
            f_helmholtz = None

        return {
            'fs_loaded': f_system,
            'vas_loaded': vas_loaded,
            'alpha_rear': alpha,
            'mass_loading_ratio': mass_loading_at_fs,
            'f_helmholtz': f_helmholtz,
        }

    def validate_helmholtz_model(
        self,
        hornresp_frequencies: np.ndarray,
        hornresp_impedance: np.ndarray
    ) -> Dict[str, float]:
        """
        Validate Helmholtz model against Hornresp impedance data.

        Calculates resonance frequency error, Q factor match, peak match.
        This is useful for validating that the calculated Helmholtz resonance
        matches the observed impedance peak in Hornresp simulations.

        Args:
            hornresp_frequencies: Frequency array from Hornresp (Hz)
            hornresp_impedance: Impedance array from Hornresp (Ω)

        Returns:
            Dictionary with validation metrics:
            - 'f_predicted': Predicted Helmholtz resonance (Hz)
            - 'f_measured': Measured resonance from impedance peak (Hz)
            - 'f_error_hz': Resonance frequency error (Hz)
            - 'f_error_percent': Resonance frequency error (%)
            - 'q_predicted': Predicted Q factor
            - 'q_measured': Measured Q from impedance ratio
            - 'q_error': Q factor error
        """
        if not self.params.front_chamber_volume:
            return {'error': 'No front chamber configured'}

        # Calculate theoretical values
        C_fc = self._calculate_acoustic_compliance(self.params.front_chamber_volume)

        # Use Hornresp-compatible parameters
        if self.params.front_chamber_area_cm2:
            area_cm2 = self.params.front_chamber_area_cm2
        else:
            area_cm2 = self.params.throat_area_cm2 if self.params.throat_area_cm2 else 50.0

        if self.params.rear_chamber_length_cm:
            length_m = self.params.rear_chamber_length_cm * 0.01
        else:
            length_m = self.calculate_effective_length() if self.horn_length else 0.0

        M_horn = self._calculate_acoustic_mass(area_cm2, length_m)
        f_helmholtz = self._calculate_helmholtz_resonance(C_fc, M_horn)

        # Find measured resonance (peak impedance)
        peak_idx = np.argmax(hornresp_impedance)
        f_measured = hornresp_frequencies[peak_idx]
        z_peak = hornresp_impedance[peak_idx]
        z_min = np.min(hornresp_impedance)
        q_measured = z_peak / z_min

        # Calculate Q from model
        Q_helmholtz = self._calculate_helmholtz_q(f_helmholtz, C_fc, M_horn)
        if self.driver.qts:
            Q_helmholtz = Q_helmholtz / self.driver.qts

        return {
            'f_predicted': f_helmholtz,
            'f_measured': f_measured,
            'f_error_hz': f_helmholtz - f_measured,
            'f_error_percent': 100 * (f_helmholtz - f_measured) / f_measured,
            'q_predicted': Q_helmholtz,
            'q_measured': q_measured,
            'q_error': Q_helmholtz - q_measured,
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
