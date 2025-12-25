"""TC-P1-RAD-04 test fixture with theoretical reference data.

Test case: Small Piston Scaling - Circular Piston Radiation Impedance
Purpose: Verify area scaling relationship with smaller piston
"""

# Theoretical values calculated using Kolbrek (2019) formulas
TC_P1_RAD_04 = {
    "name": "Small Piston Scaling",
    "description": "Circular piston radiation impedance for 50 cm² piston at 50 Hz",
    "parameters": {
        "area_cm2": 50.0,
        "area_m2": 0.0050,
        "radius_m": 0.04,  # sqrt(50 cm² / π) / 100
        "frequency_hz": 50.0,
        "temperature_c": 25.0,
        "rho": 1.184,
        "c": 346.1,
    },
    "theoretical": {
        "ka": 0.0363,  # ka = 2πf·a/c = 2π × 50 × 0.04 / 346.1
        "R_norm": 0.000659,  # R(ka) = 1 - J₁(2ka)/(ka)
        "X_norm": 0.030809,  # X(ka) = H₁(2ka)/(ka)
        "tolerance_percent": 5.0,
    },
    "hornresp_data": {
        "frequency": 50.33,
        "Ra_norm": 0.002689,
        "Xa_norm": 0.064022,
        "R_ratio": 4.03,
        "X_ratio": 2.06,
        "notes": "Consistent with TC-P1-RAD-01: R_hr≈4×R_th, X_hr≈2×X_th at low ka",
    },
    "validation": {
        "method": "theoretical",
        "tolerance_percent": 5.0,
        "expected_behavior": {
            "mass_controlled": "X dominates R (ka << 1)",
            "X_to_R_ratio": "X/R ≈ 47 at ka = 0.036",
            "area_scaling": "Z_char ≈ 25x larger than TC-P1-RAD-01 (50 cm² vs 1257 cm²)",
        },
    },
    "comparison_with_tc_p1_rad_01": {
        "area_ratio": "TC-P1-RAD-01 has 25.1x larger area",
        "ka_ratio": "TC-P1-RAD-01 has 5x larger ka (0.18 vs 0.036)",
        "Z_char_ratio": "TC-P1-RAD-04 has 25x larger characteristic impedance",
        "notes": "Both in mass-controlled region, but different ka due to radius difference",
    },
    "physical_constants": {
        "formula": "Z_rad = (ρ₀c/S) · (R(ka) + j·X(ka))",
        "characteristic_impedance": "ρ₀c/S = 1.184 × 346.1 / 0.0050 ≈ 82200 Pa·s/m³",
        "full_impedance": "Z_rad ≈ 54 + j2525 Pa·s/m³ at 50 Hz",
    },
}
