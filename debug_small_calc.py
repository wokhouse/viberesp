#!/usr/bin/env python3
"""Debug Small's transfer function calculation."""

import sys
import cmath
import math

sys.path.insert(0, 'src')

from viberesp.driver.bc_drivers import get_bc_8ndl51
from viberesp.enclosure.ported_box import ported_box_impedance_small


def debug_calculation():
    """Debug the impedance calculation at a specific frequency."""

    driver = get_bc_8ndl51()
    Vb = driver.V_as  # 10.1 L
    Fb = driver.F_s   # 75 Hz
    Qp = 7.0

    # Test at Fb (should see impedance dip)
    frequency = Fb
    print(f"Testing at f = {frequency} Hz (Fb)")
    print(f"Driver parameters:")
    print(f"  Fs = {driver.F_s} Hz")
    print(f"  M_ms = {driver.M_ms} kg")
    print(f"  Q_ms = {driver.Q_ms}")
    print(f"  BL = {driver.BL} T·m")
    print(f"  Re = {driver.R_e} Ohms")
    print(f"  Vas = {driver.V_as} m³")
    print(f"  Vb = {Vb} m³")

    # Calculate intermediate values
    omega_s = 2 * math.pi * driver.F_s
    omega_p = 2 * math.pi * Fb
    Ts = 1.0 / omega_s
    Tp = 1.0 / omega_p
    alpha = driver.V_as / Vb

    print(f"\nSmall's parameters:")
    print(f"  ω_s = {omega_s} rad/s")
    print(f"  ω_p = {omega_p} rad/s")
    print(f"  T_s = {Ts:.6e} s")
    print(f"  T_p = {Tp:.6e} s")
    print(f"  α = {alpha:.2f}")

    # Calculate R_ms and R_es
    R_ms = omega_s * driver.M_ms / driver.Q_ms
    R_es = (driver.BL ** 2) / R_ms

    print(f"\nMotional resistance:")
    print(f"  R_ms = {R_ms:.3f} N·s/m")
    print(f"  R_es = {R_es:.3f} Ohms")

    # Complex frequency
    omega = 2 * math.pi * frequency
    s = complex(0, omega)

    print(f"\nComplex frequency:")
    print(f"  ω = {omega} rad/s")
    print(f"  s = {s}")

    # Port polynomial
    port_poly = (s ** 2) * (Tp ** 2) + s * (Tp / Qp) + 1

    print(f"\nPort polynomial (creates dip):")
    print(f"  s²T_p² = {(s**2)*(Tp**2)}")
    print(f"  sT_p/Q_p = {s*(Tp/Qp)}")
    print(f"  port_poly = {port_poly}")
    print(f"  |port_poly| = {abs(port_poly):.6f}")

    # Numerator
    numerator = s * (Ts ** 3 / driver.Q_ms) * port_poly

    print(f"\nNumerator:")
    print(f"  s × (T_s³/Q_ms) = {s * (Ts**3 / driver.Q_ms)}")
    print(f"  numerator = {numerator}")
    print(f"  |numerator| = {abs(numerator):.6e}")

    # Denominator coefficients
    a4 = (Ts ** 2) * (Tp ** 2)
    a3 = (Tp ** 2 * Ts / Qp) + (Ts * Tp ** 2 / driver.Q_ms)
    a2 = (alpha + 1) * (Tp ** 2) + (Ts * Tp / (driver.Q_ms * Qp)) + (Ts ** 2)
    a1 = Tp / Qp + Ts / driver.Q_ms
    a0 = 1

    print(f"\nDenominator coefficients:")
    print(f"  a4 (s⁴) = {a4:.6e}")
    print(f"  a3 (s³) = {a3:.6e}")
    print(f"  a2 (s²) = {a2:.6e}  ← (α+1) term here!")
    print(f"  a1 (s) = {a1:.6e}")
    print(f"  a0 (const) = {a0:.6f}")

    # Full denominator
    denominator = (s ** 4) * a4 + (s ** 3) * a3 + (s ** 2) * a2 + s * a1 + a0

    print(f"\nDenominator terms:")
    print(f"  s⁴ × a4 = {(s**4)*a4}")
    print(f"  s³ × a3 = {(s**3)*a3}")
    print(f"  s² × a2 = {(s**2)*a2}")
    print(f"  s × a1 = {s*a1}")
    print(f"  a0 = {a0}")
    print(f"  denominator = {denominator}")
    print(f"  |denominator| = {abs(denominator):.6e}")

    # Motional impedance
    Z_mot = R_es * numerator / denominator

    print(f"\nMotional impedance:")
    print(f"  R_es × num/den = {R_es} × {numerator/denominator}")
    print(f"  Z_mot = {Z_mot}")
    print(f"  |Z_mot| = {abs(Z_mot):.6f} Ohms")

    # Total impedance
    Z_total = complex(driver.R_e, 0) + Z_mot

    print(f"\nTotal impedance:")
    print(f"  Z_vc = Re + Z_mot = {driver.R_e} + {Z_mot}")
    print(f"  Z_vc = {Z_total}")
    print(f"  |Z_vc| = {abs(Z_total):.2f} Ohms")

    # Expected behavior
    print(f"\n{'='*60}")
    print("Expected behavior at Fb:")
    print("  Impedance should dip toward Re")
    print("  Z ≈ Re + small_motional_term")
    print(f"  Expected: ~{driver.R_e + 0.5:.1f} to {driver.R_e + 2:.1f} Ohms")
    print(f"  Actual: {abs(Z_total):.2f} Ohms")
    print(f"{'='*60}")


if __name__ == "__main__":
    debug_calculation()
