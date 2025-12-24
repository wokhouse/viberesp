"""Physical constants for acoustic calculations."""

# Standard atmospheric conditions
RHO = 1.184  # Air density at 25°C (kg/m³)
C = 346.1    # Speed of sound at 25°C (m/s)

# Alternative values at 20°C
RHO_20C = 1.204  # Air density at 20°C (kg/m³)
C_20C = 343.0    # Speed of sound at 20°C (m/s)

# Standard atmospheric pressure
P_ATM = 101325  # Pa

# Reference SPL (threshold of hearing)
SPL_REFERENCE = 20e-6  # Pa (20 μPa)

# Reference efficiency (112.02 dB for 100% efficiency at 1W/1m)
REFERENCE_EFFICIENCY_SPL = 112.02  # dB

# Port velocity limits
PORT_VELOCITY_CHUFFING = 17.0  # m/s (approx 5% of speed of sound)
PORT_VELOCITY_HIGH = 13.0      # m/s (audible chuffing may occur)
PORT_VELOCITY_SAFE = 10.0      # m/s (safe limit)

# Standard test levels
VOLTAGE_1W_8OHM = 2.83  # V (2.83V = 1W into 8 ohms)
POWER_1W = 1.0          # W
DISTANCE_1M = 1.0       # m

# Default frequency range for simulations
FREQ_MIN = 10.0   # Hz
FREQ_MAX = 1000.0  # Hz
FREQ_POINTS_PER_DECADE = 24

# EBP (Efficiency Bandwidth Product) thresholds
EBP_SEALED_MAX = 50.0    # Below this, sealed is recommended
EBP_PORTED_MIN = 100.0   # Above this, ported is recommended
EBP_EITHER_MIN = 50.0    # Between these, either works
EBP_EITHER_MAX = 100.0

# Qtc (sealed box system Q) guidelines
QTC_BUTTERWORTH = 0.707  # Maximally flat response
QTC_BESSEL = 0.577       # Best transient response
QTC_MIN = 0.5            # Below this: underdamped, weak bass
QTC_MAX = 1.0            # Above this: peaked response, boomy
QTC_WARNING = 1.2        # Above this: very peaked

# Alignment quality factors
QL = 7.0     # Leakage losses (typical for sealed boxes)
QP = 10.0    # Port losses (typical for vented boxes)
QA = 100.0   # Absorption losses

# Unit conversions
M2_TO_CM2 = 10000.0        # m² to cm²
CM2_TO_M2 = 0.0001         # cm² to m²
L_TO_M3 = 0.001            # L to m³
M3_TO_L = 1000.0           # m³ to L
MM_TO_M = 0.001            # mm to m
M_TO_MM = 1000.0           # m to mm
G_TO_KG = 0.001            # g to kg

# Sensitivity calculation constants
# SPL = 112.02 + 10*log10(no) where no is reference efficiency
SPL_CONSTANT = 9.523e-7  # 4π²/c³ at 25°C (s³/m³)
SPL_CONSTANT_20C = 9.438e-7  # 4π²/c³ at 20°C (s³/m³)


# Frequency band definitions
SUB_BASS_RANGE = (20.0, 60.0)       # Hz
BASS_RANGE = (60.0, 250.0)          # Hz
MIDRANGE_RANGE = (250.0, 2000.0)    # Hz
PASSBAND_MIN = 200.0                # Hz (for flatness calc)
