"""Pydantic models for Thiele-Small parameters and enclosure configurations."""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class DriverType(str, Enum):
    """Loudspeaker driver type classification."""
    WOOFER = "woofer"
    MIDRANGE = "midrange"
    TWEETER = "tweeter"
    FULL_RANGE = "full_range"
    SUBWOOFER = "subwoofer"


class EnclosureType(str, Enum):
    """Supported enclosure types."""
    SEALED = "sealed"
    PORTED = "ported"
    PASSIVE_RADIATOR = "passive_radiator"
    TRANSMISSION_LINE = "transmission_line"
    BANDPASS = "bandpass"
    TAPPED_HORN = "tapped_horn"
    EXPONENTIAL_HORN = "exponential_horn"
    FRONT_LOADED_HORN = "front_loaded_horn"


class ThieleSmallParameters(BaseModel):
    """
    Thiele-Small parameters for loudspeaker drivers.

    These electromechanical parameters define the low-frequency performance
    of a loudspeaker driver and are essential for enclosure design.

    References:
        - Thiele, A.N. (1971). "Loudspeakers in Vented Boxes"
        - Small, R.H. (1972). "Direct Radiator Loudspeaker System Analysis"
    """

    # ===== Core Small-Signal Parameters (Required) =====
    fs: float = Field(
        ...,
        gt=0,
        description="Free-air resonance frequency (Hz)"
    )
    vas: float = Field(
        ...,
        gt=0,
        description="Equivalent compliance volume of driver suspension (L)"
    )
    qes: float = Field(
        ...,
        gt=0,
        description="Electrical Q factor at Fs (considering Re only)"
    )
    qms: float = Field(
        ...,
        gt=0,
        description="Mechanical Q factor at Fs (suspension losses only)"
    )
    sd: float = Field(
        ...,
        gt=0,
        description="Effective diaphragm area (m²)"
    )
    re: float = Field(
        ...,
        gt=0,
        description="Voice coil DC resistance (ohms)"
    )
    bl: float = Field(
        ...,
        gt=0,
        description="Force factor - magnetic field × voice coil length (T·m)"
    )

    # ===== Derived/Optional Small-Signal Parameters =====
    mms: Optional[float] = Field(
        None,
        gt=0,
        description="Moving mass of diaphragm and voice coil assembly (g)"
    )
    cms: Optional[float] = Field(
        None,
        gt=0,
        description="Mechanical compliance of suspension (mm/N)"
    )
    rms: Optional[float] = Field(
        None,
        gte=0,
        description="Mechanical resistance of suspension (N·s/m)"
    )
    le: Optional[float] = Field(
        None,
        gte=0,
        description="Voice coil inductance (mH)"
    )

    # ===== Large-Signal Parameters =====
    xmax: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum linear peak excursion (mm)"
    )
    pe: Optional[float] = Field(
        None,
        gt=0,
        description="Thermal power handling capacity (W)"
    )
    vd: Optional[float] = Field(
        None,
        gt=0,
        description="Peak displacement volume = Sd × Xmax (L)"
    )

    # ===== Metadata =====
    manufacturer: Optional[str] = Field(
        None,
        description="Driver manufacturer name"
    )
    model_number: Optional[str] = Field(
        None,
        description="Driver model number"
    )
    driver_type: Optional[DriverType] = Field(
        None,
        description="Driver type classification"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes or comments"
    )

    @field_validator('sd')
    @classmethod
    def validate_sd(cls, v: float) -> float:
        """
        Validate and convert diaphragm area.

        Many datasheets specify Sd in cm². Convert to m² if value > 1.
        """
        # If Sd > 1 m² (10,000 cm²), it's likely in cm²
        # Typical woofers: 50-500 cm² (0.005-0.05 m²)
        if v > 1.0:
            # Likely in cm², convert to m²
            return v / 10000.0
        return v

    @model_validator(mode='after')
    def calculate_qts(self) -> 'ThieleSmallParameters':
        """Calculate total Q factor (Qts) from Qes and Qms."""
        # Qts = (Qes × Qms) / (Qes + Qms)
        if not hasattr(self, 'qts') or self.model_dump(exclude_unset=True).get('qts') is None:
            qts = (self.qes * self.qms) / (self.qes + self.qms)
            # Store as internal attribute (not a field)
            object.__setattr__(self, '_qts', qts)
        return self

    @property
    def qts(self) -> float:
        """Total Q factor at Fs."""
        if hasattr(self, '_qts'):
            return self._qts
        return (self.qes * self.qms) / (self.qes + self.qms)

    @model_validator(mode='after')
    def calculate_ebp(self) -> 'ThieleSmallParameters':
        """Calculate Efficiency Bandwidth Product (EBP)."""
        # EBP = Fs / Qes
        # EBP < 50: sealed box
        # EBP > 100: ported box
        # 50 < EBP < 100: either type
        ebp = self.fs / self.qes
        object.__setattr__(self, '_ebp', ebp)
        return self

    @property
    def ebp(self) -> float:
        """Efficiency Bandwidth Product."""
        if hasattr(self, '_ebp'):
            return self._ebp
        return self.fs / self.qes

    @model_validator(mode='after')
    def validate_physical_consistency(self) -> 'ThieleSmallParameters':
        """Validate parameter relationships for physical consistency."""
        qts = self.qts

        # Qts should be in realistic range [0.1, 2.0]
        if not (0.1 <= qts <= 2.0):
            raise ValueError(
                f"Qts={qts:.3f} outside realistic range [0.1, 2.0]. "
                f"Check Qes={self.qes:.3f} and Qms={self.qms:.3f}."
            )

        # Fs/Qts ratio for enclosure suitability
        fs_qts_ratio = self.fs / qts
        if fs_qts_ratio < 20:
            raise ValueError(
                f"Fs/Qts={fs_qts_ratio:.1f} too low for typical use. "
                f"Fs={self.fs:.1f}Hz, Qts={qts:.3f}"
            )

        # Vas should be reasonable for driver size
        # Typical range: 5L (small woofers) to 500L (large woofers)
        if not (1.0 <= self.vas <= 2000.0):
            raise ValueError(
                f"Vas={self.vas:.1f}L outside typical range [1, 2000]L"
            )

        # Re should be reasonable for nominal impedance
        # For 8 ohm nominal: Re should be 5.5-7.5 ohms
        # For 4 ohm nominal: Re should be 2.7-4.0 ohms
        if not (2.0 <= self.re <= 16.0):
            raise ValueError(
                f"Re={self.re:.2f} ohms outside typical range [2, 16] ohms"
            )

        # Bl should be reasonable
        # Typical: 3-30 T·m for woofers
        if not (1.0 <= self.bl <= 50.0):
            raise ValueError(
                f"Bl={self.bl:.2f} T·m outside typical range [1, 50] T·m"
            )

        return self

    @model_validator(mode='after')
    def calculate_optional_parameters(self) -> 'ThieleSmallParameters':
        """Calculate derived parameters if not provided."""
        # Calculate Vd if Xmax is known
        if self.xmax is not None and self.vd is None:
            # Vd = Sd × Xmax
            # Convert Xmax from mm to m for calculation
            # Result in m³, convert to L
            vd_m3 = self.sd * (self.xmax / 1000.0)
            object.__setattr__(self, 'vd', vd_m3 * 1000.0)

        return self

    def get_recommended_enclosure(self) -> str:
        """
        Get recommended enclosure type based on EBP.

        Returns:
            Enclosure type recommendation
        """
        if self.ebp < 50:
            return "sealed"
        elif self.ebp > 100:
            return "ported"
        else:
            return "sealed or ported"

    def model_dump_with_derived(self) -> Dict[str, Any]:
        """Export model including derived/calculated properties."""
        data = self.model_dump()
        data['qts'] = self.qts
        data['ebp'] = self.ebp
        data['recommended_enclosure'] = self.get_recommended_enclosure()
        return data


class EnclosureParameters(BaseModel):
    """Base enclosure configuration parameters."""

    enclosure_type: EnclosureType

    # Common to all enclosures
    vb: float = Field(
        ...,
        gte=0,
        description="Net internal box volume (L)"
    )
    depth_cm: Optional[float] = Field(
        None,
        gt=0,
        description="Enclosure internal depth (cm)"
    )

    # Ported enclosure parameters
    fb: Optional[float] = Field(
        None,
        gt=0,
        description="Port/vent tuning frequency (Hz)"
    )
    port_length: Optional[float] = Field(
        None,
        gte=0,
        description="Port length (cm)"
    )
    port_diameter: Optional[float] = Field(
        None,
        gt=0,
        description="Port diameter (cm)"
    )
    number_of_ports: int = Field(
        1,
        ge=1,
        description="Number of ports"
    )

    # Passive radiator parameters
    pr_mass: Optional[float] = Field(
        None,
        gt=0,
        description="Passive radiator moving mass (g)"
    )
    pr_sd: Optional[float] = Field(
        None,
        gt=0,
        description="Passive radiator diaphragm area (m²)"
    )
    number_of_prs: int = Field(
        1,
        ge=1,
        description="Number of passive radiators"
    )

    # Transmission line parameters
    line_length: Optional[float] = Field(
        None,
        gt=0,
        description="Transmission line length (cm)"
    )
    taper_ratio: Optional[float] = Field(
        None,
        gt=0,
        description="Line taper ratio (end area/start area)"
    )
    stuffing_density: Optional[float] = Field(
        None,
        gte=0,
        description="Line stuffing density (kg/m³)"
    )

    # Bandpass parameters
    vb1: Optional[float] = Field(
        None,
        gt=0,
        description="Rear chamber volume (L)"
    )
    vb2: Optional[float] = Field(
        None,
        gt=0,
        description="Front chamber volume (L)"
    )
    fb1: Optional[float] = Field(
        None,
        gt=0,
        description="Rear port tuning (Hz)"
    )
    fb2: Optional[float] = Field(
        None,
        gt=0,
        description="Front port tuning (Hz)"
    )

    # Horn parameters
    throat_area_cm2: Optional[float] = Field(
        None,
        gt=0,
        description="Throat cross-sectional area (cm²)"
    )
    mouth_area_cm2: Optional[float] = Field(
        None,
        gt=0,
        description="Mouth cross-sectional area (cm²)"
    )
    horn_length_cm: Optional[float] = Field(
        None,
        gt=0,
        description="Horn axial length (cm)"
    )
    flare_rate: Optional[float] = Field(
        None,
        gt=0,
        description="Exponential flare rate m (1/m)"
    )
    cutoff_frequency: Optional[float] = Field(
        None,
        gt=0,
        description="Horn cutoff frequency fc (Hz)"
    )
    horn_type: Optional[str] = Field(
        None,
        description="Horn flare type: exponential, hyperbolic, conical, tractrix"
    )
    t_value: Optional[float] = Field(
        None,
        gte=0,
        description="Hyperbolic horn T parameter (0=infinite flare, 1=exponential)"
    )

    # Tapped horn specific parameters
    tap_position_cm: Optional[float] = Field(
        None,
        gt=0,
        description="Driver tap position from throat (cm)"
    )
    rear_chamber_volume: Optional[float] = Field(
        None,
        gte=0,
        description="Rear chamber volume (L)"
    )
    rear_chamber_length_cm: Optional[float] = Field(
        None,
        gt=0,
        description="Rear chamber acoustic path length (cm) - used for Hornresp compatibility"
    )
    front_chamber_volume: Optional[float] = Field(
        None,
        gte=0,
        description="Front chamber volume (L)"
    )
    front_chamber_area_cm2: Optional[float] = Field(
        None,
        gt=0,
        description="Front chamber throat area Atc (cm²) - used for Hornresp compatibility"
    )
    end_correction: bool = Field(
        default=True,
        description="Apply mouth end correction for finite horn length"
    )

    # Phase 1: Enhanced horn modeling parameters
    front_chamber_modes: int = Field(
        default=0,
        ge=0,
        le=3,
        description="Number of front chamber pipe modes (0=Helmholtz only, 3=with standing waves)"
    )
    radiation_model: str = Field(
        default="simple",
        description="Radiation impedance model: 'simple' (end correction) or 'beranek' (piston impedance)"
    )
    use_physics_model: bool = Field(
        default=True,
        description="Use physics-based impedance model (True) or empirical model (False)"
    )


class OptimizationObjectives(BaseModel):
    """Multi-objective optimization weights and targets."""

    flatness_weight: float = Field(
        default=1.0,
        ge=0,
        description="Response flatness priority (minimize ripple)"
    )
    bass_extension_weight: float = Field(
        default=1.0,
        ge=0,
        description="Low-frequency extension priority (minimize F3)"
    )
    efficiency_weight: float = Field(
        default=0.5,
        ge=0,
        description="SPL efficiency priority (maximize output)"
    )
    size_constraint_weight: float = Field(
        default=0.8,
        ge=0,
        description="Size minimization priority"
    )

    # Optional target values
    target_f3: Optional[float] = Field(
        None,
        gt=0,
        description="Target -3dB frequency (Hz)"
    )
    target_ripple: Optional[float] = Field(
        None,
        gte=0,
        description="Target maximum passband ripple (dB)"
    )
    target_sensitivity: Optional[float] = Field(
        None,
        description="Target sensitivity at 1W/1m (dB)"
    )


class OptimizationConstraints(BaseModel):
    """Physical constraints for optimization."""

    # Volume constraints
    max_volume: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum box volume (L)"
    )
    min_volume: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum box volume (L)"
    )

    # Frequency response constraints
    max_f3: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum acceptable -3dB frequency (Hz)"
    )
    min_f3: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum -3dB frequency (Hz)"
    )

    # Port constraints
    max_port_velocity: float = Field(
        default=17.0,
        gt=0,
        description="Maximum port air velocity (m/s)"
    )
    min_port_diameter: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum port diameter (cm)"
    )
    max_port_length: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum port length (cm)"
    )

    # Displacement constraints
    max_displacement_ratio: Optional[float] = Field(
        None,
        gt=0,
        le=1.0,
        description="Maximum displacement as ratio of Xmax"
    )

    # System Q constraints
    max_qtc: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum system Q (Qtc for sealed)"
    )
    min_qtc: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum system Q"
    )


class SimulationResults(BaseModel):
    """Container for simulation results."""

    frequency_hz: list[float] = Field(
        ...,
        description="Frequency array (Hz)"
    )
    spl_db: list[float] = Field(
        ...,
        description="SPL magnitude (dB)"
    )
    phase_degrees: list[float] = Field(
        ...,
        description="Phase response (degrees)"
    )
    group_delay_ms: list[float] = Field(
        ...,
        description="Group delay (ms)"
    )

    # Performance metrics
    f3: float = Field(
        ...,
        description="-3dB frequency (Hz)"
    )
    f10: float = Field(
        ...,
        description="-10dB frequency (Hz)"
    )
    passband_ripple_db: float = Field(
        ...,
        description="Passband ripple (dB)"
    )
    sensitivity_db: float = Field(
        ...,
        description="Sensitivity at 1kHz (dB, 1W/1m)"
    )
    max_spl_db: Optional[float] = Field(
        None,
        description="Maximum SPL at full power (dB)"
    )
