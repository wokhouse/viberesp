"""TC-P1-RAD-02 test fixture with theoretical reference data.

Test case: Transition Region (ka ≈ 1) - Circular Piston Radiation Impedance
Purpose: Verify radiation impedance behavior in transition region
"""

# Theoretical values calculated using Kolbrek (2019) formulas
TC_P1_RAD_02 = {
    "name": "Transition Region (ka ≈ 1)",
    "description": "Circular piston radiation impedance at 275 Hz (ka ≈ 1)",
    "parameters": {
        "area_cm2": 1257.0,
        "area_m2": 0.1257,
        "radius_m": 0.20,
        "frequency_hz": 275.0,
        "temperature_c": 25.0,
        "rho": 1.184,
        "c": 346.1,
    },
    "theoretical": {
        "ka": 0.9985,  # ka = 2πf·a/c = 2π × 275 × 0.20 / 346.1
        "R_norm": 0.422205,  # R(ka) = 1 - J₁(2ka)/(ka)
        "X_norm": 0.646326,  # X(ka) = H₁(2ka)/(ka)
        "tolerance_percent": 5.0,
    },
    "hornresp_data": {
        "frequency": 276.05,
        "Ra_norm": 1.050311,
        "Xa_norm": 0.529867,
        "R_ratio": 2.47,
        "X_ratio": 0.82,
        "notes": "Hornresp normalization varies with ka - not constant! At ka≈1, R_hr≈2.5×R_th",
    },
    "validation": {
        "method": "theoretical",
        "tolerance_percent": 5.0,
        "expected_behavior": {
            "transition_region": "R and X are comparable (neither dominates)",
            "X_to_R_ratio": "X/R ≈ 1.5 at ka ≈ 1",
        },
    },
    "physical_constants": {
        "formula": "Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))",
        "characteristic_impedance": "ρ₀c/S = 1.184 × 346.1 / 0.1257 ≈ 3260 Pa·s/m³",
        "full_impedance": "Z_rad ≈ 1376 + j2107 Pa·s/m³ at 275 Hz",
    },
}
