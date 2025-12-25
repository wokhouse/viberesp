"""TC-P1-RAD-03 test fixture with theoretical reference data.

Test case: High Frequency (ka >> 1) - Circular Piston Radiation Impedance
Purpose: Verify high frequency behavior where radiation becomes purely resistive
"""

# Theoretical values calculated using Kolbrek (2019) formulas
TC_P1_RAD_03 = {
    "name": "High Frequency (ka >> 1)",
    "description": "Circular piston radiation impedance at 2000 Hz (ka >> 1)",
    "parameters": {
        "area_cm2": 1257.0,
        "area_m2": 0.1257,
        "radius_m": 0.20,
        "frequency_hz": 2000.0,
        "temperature_c": 25.0,
        "rho": 1.184,
        "c": 346.1,
    },
    "theoretical": {
        "ka": 7.2617,  # ka = 2πf·a/c = 2π × 2000 × 0.20 / 346.1
        "R_norm": 0.973131,  # R(ka) → 1 as ka → ∞
        "X_norm": 0.077552,  # X(ka) → 0 as ka → ∞
        "tolerance_percent": 5.0,
    },
    "hornresp_data": {
        "frequency": 1986.72,
        "Ra_norm": 1.007744,
        "Xa_norm": 0.053764,
        "R_ratio": 1.03,
        "X_ratio": 0.71,
        "notes": "At high ka, Hornresp R ≈ Theory R! Ratio approaches 1.0",
    },
    "validation": {
        "method": "theoretical",
        "tolerance_percent": 10.0,  # Slightly relaxed for small X value
        "expected_behavior": {
            "radiation_controlled": "R dominates, X is small",
            "R_approaches_1": "R_norm > 0.95",
            "X_approaches_0": "X_norm < 0.2",
        },
    },
    "physical_constants": {
        "formula": "Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))",
        "characteristic_impedance": "ρ₀c/S = 1.184 × 346.1 / 0.1257 ≈ 3260 Pa·s/m³",
        "full_impedance": "Z_rad ≈ 3172 + j253 Pa·s/m³ at 2000 Hz",
        "efficiency": "Near 100% radiation efficiency at high frequencies",
    },
}
