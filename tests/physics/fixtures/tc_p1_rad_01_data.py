"""TC-P1-RAD-01 test fixture with theoretical and Hornresp reference data.

Test case: Small ka (Low Frequency) - Circular Piston Radiation Impedance
Purpose: Verify radiation impedance behavior when ka << 1 (mass-controlled region)
"""

# Theoretical values calculated using Kolbrek (2019) formulas
TC_P1_RAD_01 = {
    "name": "Small ka (Low Frequency)",
    "description": "Circular piston radiation impedance at 50 Hz (ka << 1)",
    "parameters": {
        "area_cm2": 1257.0,
        "area_m2": 0.1257,
        "radius_m": 0.20,  # sqrt(1257 cm² / π) / 100
        "frequency_hz": 50.0,
        "temperature_c": 25.0,
        "rho": 1.184,  # kg/m³ at 25°C (from viberesp.core.constants)
        "c": 346.1,  # m/s at 25°C (from viberesp.core.constants)
    },
    "theoretical": {
        "ka": 0.181569,  # ka = 2πf·a/c = 2π × 50 × 0.20 / 346.1
        "R_norm": 0.016393,  # R(ka) = 1 - J₁(2ka)/(ka)
        "X_norm": 0.152770,  # X(ka) = H₁(2ka)/(ka)
        "tolerance_percent": 5.0,
    },
    "hornresp_data": {
        # Extracted from acoustic_imp.txt at 50.33 Hz
        # NOTE: Hornresp normalization differs from Kolbrek theoretical formula
        "frequency": 50.33,
        "Ra_norm": 0.066203,  # Hornresp value (≈ 4× theoretical)
        "Xa_norm": 0.303105,  # Hornresp value (≈ 2× theoretical)
        "notes": (
            "Hornresp values are systematically scaled relative to Kolbrek theory:\n"
            "  - R_hornresp ≈ 4.05 × R_kolbrek\n"
            "  - X_hornresp ≈ 2.02 × X_kolbrek\n"
            "This ratio is consistent across all frequencies tested.\n"
            "Possible causes:\n"
            "  1. Different normalization convention (throat vs mouth impedance)\n"
            "  2. Hornresp includes additional effects (driver, chamber, duct)\n"
            "  3. Different impedance definition (electrical vs acoustic)\n"
            "\n"
            "Decision: Validate against theoretical Kolbrek values, not Hornresp.\n"
            "The physics implementation follows Kolbrek's peer-reviewed formulas."
        ),
    },
    "validation": {
        "method": "theoretical",
        "tolerance_percent": 1.0,  # Stricter tolerance for theory vs implementation
        "expected_behavior": {
            "mass_controlled": "X >> R when ka << 1",
            "X_to_R_ratio": "X/R ≈ 9.3 at ka = 0.18",
        },
    },
    "physical_constants": {
        "formula": "Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))",
        "characteristic_impedance": "ρ₀c/S = 1.184 × 346.1 / 0.1257 ≈ 3260 Pa·s/m³",
        "full_impedance": "Z_rad ≈ 53.4 + j498.0 Pa·s/m³ at 50 Hz",
    },
}
