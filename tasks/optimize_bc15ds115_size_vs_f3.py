#!/usr/bin/env python3
"""
Multi-objective optimization for BC_15DS115 bass horn:
- Minimize cabinet size (horn volume + rear chamber)
- Minimize F3 (maximize bass extension)

Uses NSGA-II to find the Pareto front of optimal designs balancing
these competing objectives.

Literature:
    - Deb et al. (2002) - NSGA-II multi-objective optimization
    - Olson (1947) - Horn geometry and bass extension
    - Salmon (1946) - Hyperbolic horns for extended bass
    - literature/horns/olson_1947.md
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.lhs import LHS
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from pymoo.termination import get_termination

from viberesp.driver import load_driver
from viberesp.driver.parameters import ThieleSmallParameters
from viberesp.optimization.parameters.multisegment_horn_params import (
    get_hyperbolic_parameter_space,
    decode_hyperbolic_design,
    build_multisegment_horn,
)
from viberesp.optimization.objectives.response_metrics import objective_f3, objective_passband_flatness
from viberesp.optimization.parameters.multisegment_horn_params import calculate_multisegment_horn_volume
from viberesp.optimization.constraints.physical import (
    constraint_multisegment_continuity,
    constraint_multisegment_flare_limits,
    constraint_horn_throat_sizing,
    constraint_max_displacement,
    constraint_minimum_expansion,
    constraint_mouth_loading,
)


class SizeVsF3Problem(Problem):
    """
    Multi-objective optimization problem for BC_15DS115 bass horn.

    Objectives (when target_f3 is None):
    1. F3: -3dB cutoff frequency (minimize for better bass)
    2. Total volume: Horn volume + Rear chamber (minimize for smaller cabinet)
    3. Passband flatness: SPL variation from F3 to 200 Hz (minimize for smoother response)

    Objectives (when target_f3 is set):
    1. Total volume: Horn volume + Rear chamber (minimize for smaller cabinet)
    2. Passband flatness: SPL variation from F3 to 200 Hz (minimize for smoother response)
    (F3 becomes a constraint instead of an objective)

    Constraints:
    1. Monotonic expansion (throat < middle < mouth)
    2. Flare constant limits (0.5 < m·L < 6.0)
    3. Throat sizing (50-100% of driver area)
    4. Max displacement (Xmax protection)
    5. Minimum expansion (≥10% per segment, prevents straight pipes)
    6. Mouth loading (circumference ≥ 0.3× wavelength at Fs)
    7. F3 target (if target_f3 is set): F3 ≤ target_f3
    """

    def __init__(self, driver: ThieleSmallParameters, param_space, num_segments=2,
                 folded_horn=False, max_volume_liters=None, target_f3=None):
        from viberesp.optimization.objectives.response_metrics import objective_response_flatness

        self.driver = driver
        self.param_space = param_space
        self.num_segments = num_segments
        self.enclosure_type = "multisegment_horn"
        self.folded_horn = folded_horn
        self.max_volume_liters = max_volume_liters
        self.target_f3 = target_f3  # F3 target in Hz (None = minimize as objective)

        # Volume overhead for folded horns (accounts for folding dead space,
        # cabinet walls, bracing, driver displacement)
        self.volume_overhead = 1.30 if folded_horn else 1.0

        # Get bounds from parameter space
        xl, xu = param_space.get_bounds_array()
        n_var = len(xl)

        # Number of objectives:
        # - 3 if target_f3 is None (F3, volume, flatness)
        # - 2 if target_f3 is set (volume, flatness only)
        n_obj = 2 if target_f3 is not None else 3

        # Number of constraints: 6 physical + 1 F3 (if target set) + 1 volume (if max_volume)
        n_constr = 6 + (1 if target_f3 is not None else 0) + (1 if max_volume_liters is not None else 0)

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
        n_obj = 2 if self.target_f3 is not None else 3
        objectives = np.zeros((n_samples, n_obj))

        # Calculate constraints: 6 physical + 1 F3 (if target) + 1 volume (if max_volume)
        n_constraints = 6 + (1 if self.target_f3 is not None else 0) + (1 if self.max_volume_liters is not None else 0)
        constraints = np.zeros((n_samples, n_constraints))

        for i in range(n_samples):
            design = X[i]

            try:
                # Decode design
                params = decode_hyperbolic_design(design, self.driver, self.num_segments)

                # Calculate F3 (needed for both objective and constraint)
                f3 = objective_f3(design, self.driver, "multisegment_horn")

                # Calculate total volume
                horn_vol = calculate_multisegment_horn_volume(
                    params['throat_area'],
                    params['segments'][0][1],  # middle_area
                    params['mouth_area'],
                    params['segments'][0][2],  # length1
                    params['segments'][1][2],  # length2
                )
                # Rear chamber volume
                v_rc = params['V_rc']
                # Apply folded horn overhead if needed
                total_volume = (horn_vol + v_rc) * self.volume_overhead

                # Calculate passband flatness
                try:
                    flatness = objective_passband_flatness(
                        design,
                        self.driver,
                        "multisegment_horn",
                        hf_cutoff=200.0,  # Subwoofer upper limit
                        n_points=30,  # Fewer points for speed
                        num_segments=self.num_segments,
                    )
                except:
                    # If flatness calculation fails, use a moderate penalty
                    flatness = 10.0

                # Set objectives based on whether target_f3 is set
                if self.target_f3 is not None:
                    # 2 objectives: volume and flatness (F3 is a constraint)
                    objectives[i, 0] = total_volume
                    objectives[i, 1] = flatness
                else:
                    # 3 objectives: F3, volume, and flatness
                    objectives[i, 0] = f3
                    objectives[i, 1] = total_volume
                    objectives[i, 2] = flatness

                # Constraints
                c_continuity = constraint_multisegment_continuity(
                    design, self.driver, "multisegment_horn", self.num_segments
                )
                c_flare = constraint_multisegment_flare_limits(
                    design, self.driver, "multisegment_horn", self.num_segments,
                    min_mL=0.5, max_mL=6.0
                )
                c_throat = constraint_horn_throat_sizing(
                    design, self.driver, "multisegment_horn",
                    min_compression_ratio=0.5,
                    max_compression_ratio=1.0
                )
                c_disp = constraint_max_displacement(
                    design, self.driver, "multisegment_horn",
                    max_excursion_ratio=0.8
                )

                # Minimum expansion constraint (prevents straight pipes)
                c_expansion = constraint_minimum_expansion(
                    design, self.driver, "multisegment_horn",
                    num_segments=self.num_segments,
                    min_expansion_ratio=1.1  # 10% minimum expansion per segment
                )

                # Mouth loading constraint (ensures proper bass loading)
                # Aggressive relaxation to 0.3 for ultra-compact designs
                # Trade-off: Some bass loading compromise for much smaller cabinets
                # Actual horn cutoff is typically 1.5-2× higher than Fs
                c_loading = constraint_mouth_loading(
                    design, self.driver, "multisegment_horn",
                    min_circumference_ratio=0.3  # 30% of wavelength at Fs (ultra-compact)
                )

                constraint_list = [c_continuity, c_flare, c_throat, c_disp,
                                 c_expansion, c_loading]

                # F3 target constraint (if specified)
                if self.target_f3 is not None:
                    # Constraint: f3 <= target_f3
                    # Formulated as: f3 - target <= 0 (violated if > 0)
                    f3_excess = f3 - self.target_f3
                    c_f3 = max(0.0, f3_excess)  # Penalize if F3 exceeds target
                    constraint_list.append(c_f3)

                # Volume constraint (if specified)
                if self.max_volume_liters is not None:
                    # Constraint: total_volume <= max_volume_liters / 1000
                    # Formulated as: volume - max <= 0 (violated if > 0)
                    volume_excess = total_volume - (self.max_volume_liters / 1000.0)
                    c_volume = max(0.0, volume_excess)  # Penalize if over limit
                    constraint_list.append(c_volume)

                constraints[i] = constraint_list

            except Exception as e:
                # Penalize invalid designs heavily
                if self.target_f3 is not None:
                    objectives[i] = [10.0, 20.0]  # High volume, high flatness (2 objectives)
                else:
                    objectives[i] = [200.0, 10.0, 20.0]  # High F3, high volume, high flatness (3 objectives)
                constraints[i] = [1000.0] * n_constraints

        out["F"] = objectives
        out["G"] = constraints


def main(driver_name="BC_15DS115", folded_horn=False, pop_size=120, n_generations=80, max_volume_liters=None, target_f3=None):
    print("=" * 80)
    print(f"{driver_name} Bass Horn Optimization")
    if target_f3 is not None:
        print(f"Multi-objective: Minimize Cabinet Size AND Passband Flatness")
        print(f"CONSTRAINT: F3 ≤ {target_f3} Hz")
    else:
        print("Multi-objective: Minimize F3, Cabinet Size, AND Passband Flatness")
    if folded_horn:
        print("MODE: Folded Horn (+30%% volume overhead for practical construction)")
    else:
        print("MODE: Theoretical Acoustic Volume")

    if max_volume_liters:
        print(f"CONSTRAINT: Maximum cabinet volume = {max_volume_liters} L")

    print("=" * 80)

    # Load driver
    print("\n[1/5] Loading driver parameters...")
    driver = load_driver(driver_name)

    print(f"  Driver: {driver_name}")
    print(f"  Fs: {driver.F_s:.1f} Hz")
    print(f"  Sd: {driver.S_d*10000:.0f} cm²")
    print(f"  Vas: {driver.V_as*1000:.0f} L")
    print(f"  Xmax: {driver.X_max*1000:.1f} mm")
    print(f"  Qts: {driver.Q_ts:.3f}")

    # Setup parameter space
    print("\n[2/5] Setting up hyperbolic parameter space...")

    from viberesp.optimization.parameters.multisegment_horn_params import (
        get_multisegment_horn_parameter_space,
    )
    from viberesp.optimization.parameters.parameter_space import ParameterRange

    base_space = get_multisegment_horn_parameter_space(
        driver, preset="bass_horn", num_segments=2
    )

    # RESTRICTED parameter bounds (after investigation - see horn_volume_investigation_report.md)
    # Previous expansion caused unrealistic cabinet sizes (680+ L minimum)
    # New bounds based on practical horn design limits:
    base_space.parameters[2].max_value = 1.2  # mouth_max: 1.5 → 1.2 m² (practical limit)
    base_space.parameters[3].max_value = 2.5  # length_max: 3.0 → 2.5 m (compact design focus)
    base_space.parameters[4].max_value = 2.5  # length_max: 3.0 → 2.5 m
    base_space.parameters[6].max_value = 2.0 * driver.V_as  # V_rc_max: 2.0×Vas (was 3.0×)

    # Add T parameters for hyperbolic profile
    t_parameters = [
        ParameterRange(
            name="T1",
            min_value=0.6,  # Deep hypex for bass loading
            max_value=1.0,  # Exponential
            units="",
            description="Shape parameter T for segment 1"
        ),
        ParameterRange(
            name="T2",
            min_value=0.7,
            max_value=1.0,
            units="",
            description="Shape parameter T for segment 2"
        ),
    ]

    base_params = base_space.parameters.copy()
    vtc_idx = next(i for i, p in enumerate(base_params) if p.name == "V_tc")
    new_parameters = base_params[:vtc_idx] + t_parameters + base_params[vtc_idx:]
    base_space.parameters = new_parameters

    param_space = base_space

    print(f"  Throat: {param_space.parameters[0].min_value*10000:.0f}-{param_space.parameters[0].max_value*10000:.0f} cm²")
    print(f"  Mouth: {param_space.parameters[2].min_value:.1f}-{param_space.parameters[2].max_value:.1f} m²")
    print(f"  Length: {param_space.parameters[3].min_value:.1f}-{param_space.parameters[3].max_value:.1f} m")
    print(f"  T1: {param_space.parameters[5].min_value:.2f}-{param_space.parameters[5].max_value:.2f}")
    print(f"  T2: {param_space.parameters[6].min_value:.2f}-{param_space.parameters[6].max_value:.2f}")
    print(f"  V_rc: {param_space.parameters[8].min_value*1000/driver.V_as:.1f}×-{param_space.parameters[8].max_value*1000/driver.V_as:.1f}×Vas")

    # Create optimization problem
    print("\n[3/5] Creating optimization problem...")
    problem = SizeVsF3Problem(driver, param_space, num_segments=2,
                               folded_horn=folded_horn,
                               max_volume_liters=max_volume_liters,
                               target_f3=target_f3)

    if target_f3 is not None:
        print(f"  Objectives: Total Volume (m³), Passband Flatness (dB)")
    else:
        print(f"  Objectives: F3 (Hz), Total Volume (m³), Passband Flatness (dB)")
    print(f"  Variables: {problem.n_var}")
    print(f"  Constraints: {problem.n_constr}")

    # Setup NSGA-II algorithm
    print("\n[4/5] Configuring NSGA-II algorithm...")
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=LHS(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )

    # Run optimization
    print("\n[5/5] Running optimization...")
    print(f"  Population: {pop_size}, Generations: {n_generations}")
    print("  This may take 10-30 minutes...")
    print("  Progress: [", end="", flush=True)

    termination = get_termination("n_gen", n_generations)

    res = minimize(
        problem,
        algorithm,
        termination,
        seed=42,
        verbose=True
    )

    print("] Done!")

    # Analyze results
    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)

    # Check if optimization found any feasible solutions
    if res.F is None or len(res.F) == 0:
        print("\n⚠️  NO FEASIBLE SOLUTIONS FOUND!")
        print(f"\nThe volume constraint ({max_volume_liters} L) may be too restrictive.")

        if res.CV is not None and len(res.CV) > 0:
            print(f"Minimum constraint violation: {res.CV.min():.3f}")
        else:
            print("No valid solutions found.")

        print("\nSuggestions:")
        print("  1. Increase --max-volume to allow larger cabinets")
        print("  2. Remove --folded flag to reduce volume overhead by 30%")
        print("  3. Consider a different driver with smaller requirements")
        return

    # Extract Pareto front
    F = res.F  # Objective values
    X = res.X  # Design variables

    # Handle different objective configurations
    if target_f3 is not None:
        # 2 objectives: volume, flatness (F3 is a constraint)
        volume_values = F[:, 0] * 1000  # Convert to liters
        flatness_values = F[:, 1]

        # Calculate F3 from designs (for reporting)
        f3_values = np.zeros(len(X))
        for i, design in enumerate(X):
            f3_values[i] = objective_f3(design, driver, "multisegment_horn")
    else:
        # 3 objectives: F3, volume, flatness
        f3_values = F[:, 0]
        volume_values = F[:, 1] * 1000  # Convert to liters
        flatness_values = F[:, 2]

    print(f"\nPareto-optimal designs found: {len(f3_values)}")
    print(f"  F3 range: {f3_values.min():.1f} - {f3_values.max():.1f} Hz")
    print(f"  Volume range: {volume_values.min():.0f} - {volume_values.max():.0f} L")
    print(f"  Passband flatness range: {flatness_values.min():.2f} - {flatness_values.max():.2f} dB")

    # Plot Pareto front (3 objectives shown as 2D projections)
    print("\nGenerating plots...")

    if target_f3 is not None:
        # For target_f3 mode, create simpler 2-objective plots
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Plot 1: Volume vs Flatness scatter
        scatter1 = axes[0].scatter(volume_values, flatness_values, c=f3_values,
                                  cmap='RdYlGn_r', s=100, alpha=0.6,
                                  edgecolors='black', linewidths=1)

        min_vol_idx = np.argmin(volume_values)
        min_flat_idx = np.argmin(flatness_values)

        axes[0].scatter(volume_values[min_vol_idx], flatness_values[min_vol_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Smallest Cabinet', zorder=10)
        axes[0].scatter(volume_values[min_flat_idx], flatness_values[min_flat_idx],
                       c='green', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Flattest Response', zorder=10)

        axes[0].set_xlabel('Total Cabinet Volume (L)', fontsize=12)
        axes[0].set_ylabel('Passband Flatness (dB)', fontsize=12)
        axes[0].set_title(f'Volume vs Flatness (F3 ≤ {target_f3} Hz)', fontsize=14)
        axes[0].grid(True, alpha=0.3)
        axes[0].legend(fontsize=10)
        cbar1 = plt.colorbar(scatter1, ax=axes[0])
        cbar1.set_label('F3 (Hz)', fontsize=10)

        # Plot 2: F3 vs Volume
        scatter2 = axes[1].scatter(f3_values, volume_values, c=flatness_values,
                       cmap='viridis_r', s=100, alpha=0.6,
                       edgecolors='black', linewidths=1)
        axes[1].scatter(f3_values[min_vol_idx], volume_values[min_vol_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Smallest Cabinet', zorder=10)
        axes[1].scatter(f3_values[min_flat_idx], volume_values[min_flat_idx],
                       c='green', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Flattest Response', zorder=10)
        axes[1].axvline(x=target_f3, color='red', linestyle='--', alpha=0.5, label='F3 Target')
        axes[1].set_xlabel('F3 (Hz)', fontsize=12)
        axes[1].set_ylabel('Total Cabinet Volume (L)', fontsize=12)
        axes[1].set_title('F3 vs Volume (colored by flatness)', fontsize=14)
        axes[1].grid(True, alpha=0.3)
        axes[1].legend(fontsize=10)
        cbar2 = plt.colorbar(scatter2, ax=axes[1])
        cbar2.set_label('Passband Flatness (dB)', fontsize=10)

        plt.tight_layout()
        plot_file = "tasks/bc15ds115_size_vs_f3_pareto.png"
        plt.savefig(plot_file, dpi=150)
        print(f"Pareto front plot saved to: {plot_file}")

        # Find best trade-off (minimize combined normalized score)
        vol_norm = (volume_values - volume_values.min()) / (volume_values.max() - volume_values.min())
        flat_norm = (flatness_values - flatness_values.min()) / (flatness_values.max() - flatness_values.min())
        combined = vol_norm + flat_norm
        knee_idx = np.argmin(combined)

        # Print key designs
        print("\n" + "=" * 80)
        print("KEY DESIGNS")
        print("=" * 80)

        analyze_design(min_vol_idx, "SMALLEST CABINET", folded_horn)
        analyze_design(min_flat_idx, "FLATTEST RESPONSE", folded_horn)
        analyze_design(knee_idx, "BEST TRADE-OFF", folded_horn)

        return  # Skip the rest of the plotting code which is for 3-objective case

    # Original 3-objective plotting code continues below
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: F3 vs Volume (colored by flatness)
    scatter1 = axes[0, 0].scatter(volume_values, f3_values, c=flatness_values,
                                  cmap='viridis_r', s=100, alpha=0.6,
                                  edgecolors='black', linewidths=1)

    min_f3_idx = np.argmin(f3_values)
    min_vol_idx = np.argmin(volume_values)
    min_flat_idx = np.argmin(flatness_values)

    axes[0, 0].scatter(volume_values[min_f3_idx], f3_values[min_f3_idx],
                       c='blue', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Best F3', zorder=10)
    axes[0, 0].scatter(volume_values[min_vol_idx], f3_values[min_vol_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Smallest Cabinet', zorder=10)
    axes[0, 0].scatter(volume_values[min_flat_idx], f3_values[min_flat_idx],
                       c='green', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Flattest Response', zorder=10)

    axes[0, 0].set_xlabel('Total Cabinet Volume (L)', fontsize=12)
    axes[0, 0].set_ylabel('F3 (Hz)', fontsize=12)
    axes[0, 0].set_title('F3 vs Volume (colored by flatness)', fontsize=14)
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].legend(fontsize=10)
    cbar1 = plt.colorbar(scatter1, ax=axes[0, 0])
    cbar1.set_label('Passband Flatness (dB)', fontsize=10)

    # Plot 2: F3 vs Flatness (colored by volume)
    scatter2 = axes[0, 1].scatter(flatness_values, f3_values, c=volume_values,
                                  cmap='plasma', s=100, alpha=0.6,
                                  edgecolors='black', linewidths=1)

    axes[0, 1].scatter(flatness_values[min_f3_idx], f3_values[min_f3_idx],
                       c='blue', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Best F3', zorder=10)
    axes[0, 1].scatter(flatness_values[min_vol_idx], f3_values[min_vol_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Smallest Cabinet', zorder=10)
    axes[0, 1].scatter(flatness_values[min_flat_idx], f3_values[min_flat_idx],
                       c='green', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Flattest Response', zorder=10)

    axes[0, 1].set_xlabel('Passband Flatness (dB)', fontsize=12)
    axes[0, 1].set_ylabel('F3 (Hz)', fontsize=12)
    axes[0, 1].set_title('F3 vs Passband Flatness (colored by volume)', fontsize=14)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].legend(fontsize=10)
    cbar2 = plt.colorbar(scatter2, ax=axes[0, 1])
    cbar2.set_label('Volume (L)', fontsize=10)

    # Plot 3: Volume vs Flatness (colored by F3)
    scatter3 = axes[1, 0].scatter(flatness_values, volume_values, c=f3_values,
                                  cmap='RdYlGn_r', s=100, alpha=0.6,
                                  edgecolors='black', linewidths=1)

    axes[1, 0].scatter(flatness_values[min_f3_idx], volume_values[min_f3_idx],
                       c='blue', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Best F3', zorder=10)
    axes[1, 0].scatter(flatness_values[min_vol_idx], volume_values[min_vol_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Smallest Cabinet', zorder=10)
    axes[1, 0].scatter(flatness_values[min_flat_idx], volume_values[min_flat_idx],
                       c='green', s=300, marker='*', edgecolors='black', linewidths=2,
                       label='Flattest Response', zorder=10)

    axes[1, 0].set_xlabel('Passband Flatness (dB)', fontsize=12)
    axes[1, 0].set_ylabel('Total Cabinet Volume (L)', fontsize=12)
    axes[1, 0].set_title('Volume vs Passband Flatness (colored by F3)', fontsize=14)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].legend(fontsize=10)
    cbar3 = plt.colorbar(scatter3, ax=axes[1, 0])
    cbar3.set_label('F3 (Hz)', fontsize=10)

    # Plot 4: 3D scatter using color for flatness
    # Show F3 vs Volume with point size indicating flatness
    scatter4 = axes[1, 1].scatter(volume_values, f3_values, s=flatness_values*30,
                                  c=flatness_values, cmap='coolwarm',
                                  alpha=0.6, edgecolors='black', linewidths=1)

    # Best trade-off (knee point)
    # Normalize all objectives to 0-1
    f3_norm = (f3_values - f3_values.min()) / (f3_values.max() - f3_values.min())
    vol_norm = (volume_values - volume_values.min()) / (volume_values.max() - volume_values.min())
    flat_norm = (flatness_values - flatness_values.min()) / (flatness_values.max() - flatness_values.min())

    # Combined score (lower is better)
    combined = f3_norm + vol_norm + flat_norm
    knee_idx = np.argmin(combined)

    axes[1, 1].scatter(volume_values[knee_idx], f3_values[knee_idx],
                       c='purple', s=400, marker='*', edgecolors='black', linewidths=2,
                       label='Best Trade-off', zorder=10)

    axes[1, 1].set_xlabel('Total Cabinet Volume (L)', fontsize=12)
    axes[1, 1].set_ylabel('F3 (Hz)', fontsize=12)
    axes[1, 1].set_title('Pareto Front (bubble size = flatness)', fontsize=14)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].legend(fontsize=10)
    cbar4 = plt.colorbar(scatter4, ax=axes[1, 1])
    cbar4.set_label('Passband Flatness (dB)', fontsize=10)

    plt.tight_layout()

    plot_file = "tasks/bc15ds115_size_vs_f3_pareto.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Pareto front plot saved to: {plot_file}")

    # Print key designs
    print("\n" + "=" * 80)
    print("KEY DESIGNS")
    print("=" * 80)

    def analyze_design(idx, label, folded_horn):
        """Analyze and print design details."""
        design = X[idx]
        params = decode_hyperbolic_design(design, driver, num_segments=2)

        f3 = f3_values[idx]
        vol = volume_values[idx]
        flat = flatness_values[idx]

        throat_area = params['throat_area']
        middle_area = params['segments'][0][1]
        mouth_area = params['mouth_area']
        length1 = params['segments'][0][2]
        length2 = params['segments'][1][2]
        total_length = length1 + length2
        T1 = params['T_params'][0]
        T2 = params['T_params'][1]
        V_rc = params['V_rc']

        m1 = np.log(middle_area / throat_area) / length1 if length1 > 0 else 0
        m2 = np.log(mouth_area / middle_area) / length2 if length2 > 0 else 0

        horn_vol = calculate_multisegment_horn_volume(
            throat_area, middle_area, mouth_area, length1, length2
        )

        # Calculate acoustic volume for display
        acoustic_vol = horn_vol + V_rc

        print(f"\n{label}")
        print("-" * 70)
        print(f"  F3: {f3:.1f} Hz")
        print(f"  Passband flatness: {flat:.2f} dB (F3 to 200 Hz)")

        if folded_horn:
            print(f"  Practical cabinet volume: {vol:.0f} L (includes +30%% folding overhead)")
            print(f"    - Acoustic volume: {acoustic_vol*1000:.0f} L (horn: {horn_vol*1000:.0f} L + rear: {V_rc*1000:.0f} L)")
            print(f"    - Folding overhead: {vol - acoustic_vol*1000:.0f} L")
        else:
            print(f"  Total acoustic volume: {vol:.0f} L (horn: {horn_vol*1000:.0f} L + rear: {V_rc*1000:.0f} L)")

        print(f"  Throat: {throat_area*10000:.0f} cm²")
        print(f"  Mouth: {mouth_area*10000:.0f} cm² ({np.sqrt(mouth_area)*100:.0f}×{np.sqrt(mouth_area)*100:.0f} cm)")
        print(f"  Length: {total_length:.2f} m (L1: {length1:.2f} m, L2: {length2:.2f} m)")
        print(f"  T1: {T1:.3f}, T2: {T2:.3f}")
        print(f"  Flare: m1·L1 = {m1*length1:.2f}, m2·L2 = {m2*length2:.2f}")
        print(f"  Cutoff: {343*m1/(4*np.pi):.1f} Hz (seg1), {343*m2/(4*np.pi):.1f} Hz (seg2)")

    analyze_design(min_f3_idx, "LOWEST F3 (Best Bass Extension)", folded_horn)
    analyze_design(min_vol_idx, "SMALLEST CABINET (Most Compact)", folded_horn)
    analyze_design(min_flat_idx, "FLATTEST RESPONSE (Smoother)", folded_horn)
    analyze_design(knee_idx, "BEST TRADE-OFF (Balanced)", folded_horn)

    # Save detailed results
    output_file = "tasks/bc15ds115_size_vs_f3_results.txt"
    with open(output_file, 'w') as f:
        f.write("BC_15DS115 Bass Horn - Size vs F3 vs Passband Flatness Optimization\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Pareto-optimal designs: {len(f3_values)}\n")
        f.write(f"F3 range: {f3_values.min():.1f} - {f3_values.max():.1f} Hz\n")
        f.write(f"Volume range: {volume_values.min():.0f} - {volume_values.max():.0f} L\n")
        f.write(f"Passband flatness range: {flatness_values.min():.2f} - {flatness_values.max():.2f} dB\n\n")

        f.write("All Pareto-optimal designs:\n")
        f.write(f"{'F3':<8} {'Vol':<8} {'PBFlat':<8} {'Throat':<10} {'Mouth':<10} {'Length':<10} {'T1':<6} {'T2':<6}\n")
        f.write("-" * 80 + "\n")

        # Sort by F3
        sorted_indices = np.argsort(f3_values)

        for idx in sorted_indices:
            design = X[idx]
            params = decode_hyperbolic_design(design, driver, num_segments=2)

            f.write(f"{f3_values[idx]:<8.1f} {volume_values[idx]:<8.0f} "
                   f"{flatness_values[idx]:<8.2f} "
                   f"{params['throat_area']*10000:<10.0f} "
                   f"{params['mouth_area']*10000:<10.0f} "
                   f"{(params['segments'][0][2] + params['segments'][1][2]):<10.2f} "
                   f"{params['T_params'][0]:<6.3f} {params['T_params'][1]:<6.3f}\n")

    print(f"\nResults saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Optimization complete!")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimize bass horn for size vs F3 vs flatness"
    )
    parser.add_argument(
        "--driver",
        type=str,
        default="BC_15DS115",
        help="Driver name (default: BC_15DS115, also supports BC_21DS115, etc.)"
    )
    parser.add_argument(
        "--folded",
        action="store_true",
        help="Add 30%% volume overhead for folded horn construction (accounts for "
             "folding dead space, cabinet walls, bracing, driver displacement)"
    )
    parser.add_argument(
        "--max-volume",
        type=float,
        default=None,
        help="Maximum cabinet volume constraint in liters (e.g., 350 for 350L max)"
    )
    parser.add_argument(
        "--target-f3",
        type=float,
        default=None,
        help="Target F3 frequency in Hz (e.g., 32 for F3 ≤ 32 Hz constraint). "
             "If set, F3 becomes a constraint instead of an objective."
    )
    parser.add_argument(
        "--pop-size",
        type=int,
        default=120,
        help="Population size for NSGA-II (default: 120)"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=80,
        help="Number of generations (default: 80)"
    )

    args = parser.parse_args()

    main(driver_name=args.driver, folded_horn=args.folded,
         pop_size=args.pop_size, n_generations=args.generations,
         max_volume_liters=args.max_volume, target_f3=args.target_f3)
