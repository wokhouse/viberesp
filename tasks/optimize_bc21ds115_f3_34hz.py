#!/usr/bin/env python3
"""
Optimize BC_21DS115 bass horn for F3 = 34 Hz target.

Uses hyperbolic profiles with T < 1.0 for extended low-frequency loading
and larger rear chambers for lower tuning.

Literature:
    - Salmon (1946) - Hyperbolic (Hypex) horns for extended bass
    - Kolbrek (2018) - T parameter effect on low-frequency loading
    - Olson (1947) - Rear chamber compliance effects on F3
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_hyperbolic_parameter_space,
    decode_hyperbolic_design,
    build_multisegment_horn,
)
from viberesp.optimization.objectives.response_metrics import (
    objective_f3,
    objective_response_flatness,
)
from viberesp.optimization.constraints.physical import (
    constraint_multisegment_continuity,
    constraint_multisegment_flare_limits,
    constraint_horn_throat_sizing,
    constraint_max_displacement,
)


class HyperbolicBassHornProblem(Problem):
    """Multi-objective optimization problem for F3=34Hz bass horn.

    Objectives:
    1. F3 deviation from 34 Hz target (minimize)
    2. Response flatness 20-200 Hz (minimize)

    Constraints:
    1. Monotonic expansion (throat < middle < mouth)
    2. Flare constant limits (0.5 < m·L < 6.0)
    3. Throat sizing (50-100% of driver area)
    4. Max displacement (Xmax protection)
    """

    def __init__(self, driver: ThieleSmallParameters, param_space, num_segments=2):
        self.driver = driver
        self.param_space = param_space
        self.num_segments = num_segments
        self.enclosure_type = "multisegment_horn"  # Will use hyperbolic segments

        # Get bounds from parameter space
        xl, xu = param_space.get_bounds_array()

        # Number of variables depends on segments
        # 2-seg hyperbolic: [throat, middle, mouth, L1, L2, T1, T2, V_tc, V_rc] = 9 vars
        n_var = len(xl)

        # Number of objectives: F3 deviation, flatness
        n_obj = 2

        # Number of constraints: continuity, flare limits, throat sizing, displacement
        n_constr = 4

        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_constr=n_constr,
            xl=xl,
            xu=xu,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        """Evaluate design vectors for objectives and constraints."""

        n_samples = X.shape[0]
        objectives = np.zeros((n_samples, 2))
        constraints = np.zeros((n_samples, 4))

        for i in range(n_samples):
            design = X[i]

            try:
                # Calculate objectives
                f3 = objective_f3(
                    design,
                    self.driver,
                    "multisegment_horn",  # Will build hyperbolic internally
                )

                # Objective 1: F3 deviation from 34 Hz target
                f3_deviation = abs(f3 - 34.0)

                # Objective 2: Response flatness 20-200 Hz
                flatness = objective_response_flatness(
                    design,
                    self.driver,
                    "multisegment_horn",
                    frequency_range=(20.0, 200.0),
                    n_points=100,
                    num_segments=self.num_segments,
                )

                objectives[i] = [f3_deviation, flatness]

                # Calculate constraints
                # Constraint 1: Monotonic expansion
                c_continuity = constraint_multisegment_continuity(
                    design, self.driver, "multisegment_horn", self.num_segments
                )

                # Constraint 2: Flare limits
                c_flare = constraint_multisegment_flare_limits(
                    design, self.driver, "multisegment_horn", self.num_segments,
                    min_mL=0.5, max_mL=6.0  # Relaxed for long bass horns
                )

                # Constraint 3: Throat sizing
                c_throat = constraint_horn_throat_sizing(
                    design, self.driver, "multisegment_horn",
                    min_compression_ratio=0.5,  # 50% of driver (2:1 max)
                    max_compression_ratio=1.0   # 100% of driver (no compression)
                )

                # Constraint 4: Max displacement
                c_disp = constraint_max_displacement(
                    design, self.driver, "multisegment_horn",
                    max_excursion_ratio=0.8
                )

                constraints[i] = [c_continuity, c_flare, c_throat, c_disp]

            except Exception as e:
                # Penalize invalid designs heavily
                objectives[i] = [1000.0, 1000.0]
                constraints[i] = [1000.0, 1000.0, 1000.0, 1000.0]

        out["F"] = objectives
        out["G"] = constraints


def main():
    """Run optimization for BC_21DS115 targeting F3 = 34 Hz."""

    print("=" * 80)
    print("BC_21DS115 Hyperbolic Bass Horn Optimization")
    print("Target: F3 = 34 Hz")
    print("=" * 80)

    # Load driver
    print("\n[1/6] Loading driver parameters...")
    driver = load_driver("BC_21DS115")

    print(f"  Driver: BC_21DS115 (B&C Speakers 21\" Subwoofer)")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")
    print(f"  Qts: {driver.Q_ts:.3f}")

    # Get parameter space for hyperbolic bass horn
    print("\n[2/6] Setting up hyperbolic parameter space...")
    print("  Strategy: Large mouth, long length, hyperbolic throat (T<1.0)")

    # For extended bass to 34 Hz, we need:
    # - Very large mouth: 1.5-2.5 m² (λ/2 at 34 Hz needs mouth ~1.5m diameter)
    # - Long horn: 4-6 m total length
    # - Hyperbolic throat: T=0.6-0.7 for better LF loading
    # - Large rear chamber: 2-3×Vas for lower tuning

    # Temporarily modify parameter space for aggressive bass extension
    from viberesp.optimization.parameters.multisegment_horn_params import (
        get_multisegment_horn_parameter_space,
    )

    base_space = get_multisegment_horn_parameter_space(
        driver, preset="bass_horn", num_segments=2
    )

    # Expand mouth and length bounds for 34 Hz target
    # λ/2 at 34 Hz = 343/(2×34) = 5.0 m → mouth needs circumference ≥ 5.0 m
    # For circular mouth: circumference = π×d → d ≥ 1.6 m → area ≥ 2.0 m²
    base_space.parameters[2].max_value = 3.0  # mouth_max: 1.5 → 3.0 m²
    base_space.parameters[3].max_value = 5.0  # length_max: 3.0 → 5.0 m
    base_space.parameters[4].max_value = 5.0  # length_max: 3.0 → 5.0 m
    base_space.parameters[6].max_value = 3.0 * driver.V_as  # V_rc_max: 2.0 → 3.0×Vas

    # Add T parameters for hyperbolic profile
    from viberesp.optimization.parameters.parameter_space import ParameterRange

    t_parameters = [
        ParameterRange(
            name="T1",
            min_value=0.6,  # Deep hypex for bass loading
            max_value=1.0,  # Exponential
            units="",
            description="Shape parameter T for segment 1 (0.6=hypex, 1.0=exponential)"
        ),
        ParameterRange(
            name="T2",
            min_value=0.8,  # Milder hypex for mouth
            max_value=1.0,  # Exponential
            units="",
            description="Shape parameter T for segment 2 (0.8=hypex, 1.0=exponential)"
        ),
    ]

    # Insert T parameters before V_tc
    base_params = base_space.parameters.copy()
    vtc_idx = next(i for i, p in enumerate(base_params) if p.name == "V_tc")
    new_parameters = base_params[:vtc_idx] + t_parameters + base_params[vtc_idx:]
    base_space.parameters = new_parameters

    param_space = base_space

    print(f"  Throat: {param_space.parameters[0].min_value*10000:.0f}-{param_space.parameters[0].max_value*10000:.0f} cm²")
    print(f"  Mouth: {param_space.parameters[2].min_value:.1f}-{param_space.parameters[2].max_value:.1f} m²")
    print(f"  Length: {param_space.parameters[3].min_value:.1f}-{param_space.parameters[3].max_value:.1f} m")
    print(f"  T1: {param_space.parameters[5].min_value:.2f}-{param_space.parameters[5].max_value:.2f} (hyperbolic)")
    print(f"  T2: {param_space.parameters[6].min_value:.2f}-{param_space.parameters[6].max_value:.2f} (hyperbolic)")
    print(f"  V_rc: {param_space.parameters[8].min_value*1000/driver.V_as:.1f}×-{param_space.parameters[8].max_value*1000/driver.V_as:.1f}×Vas")

    # Create optimization problem
    print("\n[3/6] Creating optimization problem...")
    problem = HyperbolicBassHornProblem(driver, param_space, num_segments=2)

    # Setup NSGA-II algorithm
    print("\n[4/6] Configuring NSGA-II algorithm...")
    algorithm = NSGA2(
        pop_size=100,  # Larger population for better search
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )

    # Run optimization
    print("\n[5/6] Running optimization...")
    print("  This may take 10-30 minutes depending on iterations...")
    print("  Progress: [", end="", flush=True)

    res = minimize(
        problem,
        algorithm,
        termination=('n_gen', 80),  # 80 generations
        verbose=False,
        callback=lambda alg: print("=", end="", flush=True) if alg.n_gen % 10 == 0 else None
    )

    print("] Done!")

    # Analyze results
    print("\n[6/6] Analyzing results...")

    # Find best design for F3 = 34 Hz
    f3_deviations = res.F[:, 0]
    best_idx = np.argmin(f3_deviations)
    best_design = res.X[best_idx]
    best_f3_dev = res.F[best_idx, 0]
    best_flatness = res.F[best_idx, 1]

    # Decode best design
    params = decode_hyperbolic_design(best_design, driver, num_segments=2)

    # Calculate actual F3
    f3_actual = objective_f3(best_design, driver, "multisegment_horn")

    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)

    print("\nBest Design for F3 ≈ 34 Hz:")
    print(f"  F3: {f3_actual:.1f} Hz (target: 34 Hz, deviation: {best_f3_dev:.1f} Hz)")
    print(f"  Flatness (20-200 Hz): {best_flatness:.2f} dB")

    print("\nHorn Geometry:")
    print(f"  Throat area: {params['throat_area']*10000:.0f} cm²")
    print(f"  Middle area: {params['segments'][0][1]*10000:.0f} cm²")
    print(f"  Mouth area: {params['mouth_area']*10000:.0f} cm² ({(params['mouth_area']*10000)**0.5*100:.0f} cm × {(params['mouth_area']*10000)**0.5*100:.0f} cm)")
    print(f"  Length 1: {params['segments'][0][2]:.2f} m")
    print(f"  Length 2: {params['segments'][1][2]:.2f} m")
    print(f"  Total length: {params['total_length']:.2f} m")
    print(f"  T1 (throat): {params['T_params'][0]:.3f}")
    print(f"  T2 (mouth): {params['T_params'][1]:.3f}")

    print("\nChamber Volumes:")
    print(f"  Throat chamber: {params['V_tc']*1000000:.1f} cm³")
    print(f"  Rear chamber: {params['V_rc']*1000:.1f} L ({params['V_rc']/driver.V_as:.2f}×Vas)")

    # Calculate flare constants
    S1, S2, S3 = params['throat_area'], params['segments'][0][1], params['mouth_area']
    L1, L2 = params['segments'][0][2], params['segments'][1][2]
    m1 = np.log(S2/S1)/L1 if L1 > 0 else 0
    m2 = np.log(S3/S2)/L2 if L2 > 0 else 0

    print("\nFlare Constants:")
    print(f"  Segment 1: m1·L1 = {m1*L1:.2f} (cutoff: {343*m1/(4*np.pi):.1f} Hz)")
    print(f"  Segment 2: m2·L2 = {m2*L2:.2f} (cutoff: {343*m2/(4*np.pi):.1f} Hz)")

    # Calculate compression ratio
    compression_ratio = driver.S_d / params['throat_area']
    print(f"\nCompression ratio: {compression_ratio:.2f}:1")

    # Check constraints
    print("\nConstraint Satisfaction:")
    c_cont = constraint_multisegment_continuity(best_design, driver, "multisegment_horn", 2)
    c_flare = constraint_multisegment_flare_limits(best_design, driver, "multisegment_horn", 2)
    c_throat = constraint_horn_throat_sizing(best_design, driver, "multisegment_horn")
    print(f"  Continuity: {'✓' if c_cont <= 0 else '✗'} ({c_cont:.4f})")
    print(f"  Flare limits: {'✓' if c_flare <= 0 else '✗'} ({c_flare:.4f})")
    print(f"  Throat sizing: {'✓' if c_throat <= 0 else '✗'} ({c_throat:.4f})")

    # Build horn and calculate performance
    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)

    horn, V_tc, V_rc = build_multisegment_horn(best_design, driver, num_segments=2)

    from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn
    flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

    # Frequency response
    frequencies = np.logspace(np.log10(20), np.log10(500), 200)
    spl_values = []
    efficiency_values = []

    for freq in frequencies:
        try:
            spl = flh.spl_response(freq, voltage=2.83)
            spl_values.append(spl)

            # Calculate efficiency
            # Power = V²/R (assuming 8 ohm nominal)
            # Efficiency = SPL - 10*log10(power)
            power = 2.83**2 / 8.0
            efficiency = 10**(spl/10) * power / 10**(spl/10)
            efficiency_values.append(efficiency)
        except:
            spl_values.append(np.nan)
            efficiency_values.append(np.nan)

    spl_values = np.array(spl_values)
    efficiency_values = np.array(efficiency_values)

    # Find reference SPL
    passband_mask = (frequencies >= 50) & (frequencies <= 500)
    reference_spl = np.max(spl_values[passband_mask])

    print(f"\nReference SPL (50-500 Hz): {reference_spl:.1f} dB @ 2.83V")

    # Key frequencies
    key_freqs = [30, 40, 50, 63, 80, 100, 125, 160, 200]
    print("\nFrequency Response:")
    print(f"{'Freq':>8} {'SPL':>8} {'Level':>10}")
    print("-" * 28)

    for f in key_freqs:
        idx = np.argmin(np.abs(frequencies - f))
        spl = spl_values[idx]
        level = spl - reference_spl
        print(f"{f:>8.0f} {spl:>8.1f} {level:>10.1f}")

    # Save results
    output_file = "tasks/BC21DS115_f3_34hz_hyperbolic_results.txt"
    with open(output_file, 'w') as f:
        f.write("BC_21DS115 Hyperbolic Bass Horn - F3 = 34 Hz Target\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Target F3: 34 Hz\n")
        f.write(f"Achieved F3: {f3_actual:.1f} Hz\n")
        f.write(f"Deviation: {best_f3_dev:.1f} Hz\n\n")

        f.write("Horn Geometry:\n")
        f.write(f"  Throat area: {params['throat_area']*10000:.0f} cm²\n")
        f.write(f"  Middle area: {params['segments'][0][1]*10000:.0f} cm²\n")
        f.write(f"  Mouth area: {params['mouth_area']*10000:.0f} cm²\n")
        f.write(f"  Length 1: {params['segments'][0][2]:.2f} m\n")
        f.write(f"  Length 2: {params['segments'][1][2]:.2f} m\n")
        f.write(f"  Total length: {params['total_length']:.2f} m\n")
        f.write(f"  T1 (throat): {params['T_params'][0]:.3f}\n")
        f.write(f"  T2 (mouth): {params['T_params'][1]:.3f}\n\n")

        f.write(f"Compression ratio: {compression_ratio:.2f}:1\n\n")

        f.write("Chamber Volumes:\n")
        f.write(f"  Throat chamber: {params['V_tc']*1000000:.1f} cm³\n")
        f.write(f"  Rear chamber: {params['V_rc']*1000:.1f} L ({params['V_rc']/driver.V_as:.2f}×Vas)\n\n")

        f.write("Design Vector:\n")
        f.write("  " + str(best_design) + "\n\n")

        f.write(f"Reference SPL: {reference_spl:.1f} dB @ 2.83V\n\n")

        f.write("Frequency Response:\n")
        for f_key in key_freqs:
            idx = np.argmin(np.abs(frequencies - f_key))
            spl = spl_values[idx]
            level = spl - reference_spl
            f.write(f"  {f_key:>4.0f} Hz: {spl:>6.1f} dB ({level:>+6.1f} dB)\n")

    print(f"\nResults saved to: {output_file}")

    # Plot results
    print("\nGenerating plots...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Frequency response
    ax1.semilogx(frequencies, spl_values, 'b-', linewidth=2, label='Hyperbolic horn')
    ax1.axhline(reference_spl - 3, color='r', linestyle='--', label='-3 dB reference')
    ax1.axvline(f3_actual, color='g', linestyle='--', label=f'F3 = {f3_actual:.1f} Hz')
    ax1.axvline(34.0, color='orange', linestyle=':', label='Target F3 = 34 Hz')
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('SPL (dB) @ 2.83V')
    ax1.set_title(f'BC_21DS115 Hyperbolic Bass Horn - F3 = {f3_actual:.1f} Hz')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_xlim([20, 500])
    ax1.set_ylim([80, 110])

    # Plot 2: Horn profile
    x_points = np.linspace(0, params['total_length'], 200)
    area_points = []

    x_transition = params['segments'][0][2]
    S_throat = params['throat_area']
    S_middle = params['segments'][0][1]
    S_mouth = params['mouth_area']
    T1 = params['T_params'][0]
    T2 = params['T_params'][1]

    for x in x_points:
        if x <= x_transition:
            # Segment 1: hyperbolic
            from viberesp.simulation.types import HyperbolicHorn
            seg = HyperbolicHorn(S_throat, S_middle, x_transition, T=T1)
            area_points.append(seg.area_at(x))
        else:
            # Segment 2: hyperbolic
            from viberesp.simulation.types import HyperbolicHorn
            seg = HyperbolicHorn(S_middle, S_mouth, params['segments'][1][2], T=T2)
            area_points.append(seg.area_at(x - x_transition))

    radius_points = [np.sqrt(a) * 100 for a in area_points]  # cm

    ax2.plot(x_points, radius_points, 'b-', linewidth=2)
    ax2.axvline(x_transition, color='gray', linestyle='--', alpha=0.5, label='Segment transition')
    ax2.set_xlabel('Axial distance (m)')
    ax2.set_ylabel('Horn radius (cm)')
    ax2.set_title(f'Horn Profile (T1={T1:.2f}, T2={T2:.2f})')
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()

    plot_file = "tasks/BC21DS115_f3_34hz_hyperbolic.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Plot saved to: {plot_file}")

    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
