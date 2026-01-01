#!/usr/bin/env python3
"""
Evaluate frequency response flatness for BC_15DS115 Pareto-optimal designs.

Analyzes all designs from the size vs F3 optimization to understand
the trade-off between cabinet size, F3, and response flatness.

Literature:
    - Beranek (1954) - Frequency response evaluation metrics
    - Small (1972) - Bandwidth and flatness definitions
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import numpy as np
import matplotlib.pyplot as plt
import pickle

from viberesp.driver import load_driver
from viberesp.optimization.parameters.multisegment_horn_params import (
    decode_hyperbolic_design,
    build_multisegment_horn,
)
from viberesp.optimization.objectives.response_metrics import (
    objective_response_flatness,
    objective_passband_flatness,
    objective_f3,
)
from viberesp.enclosure.front_loaded_horn import FrontLoadedHorn


def calculate_comprehensive_flatness(design, driver, flh, f3):
    """
    Calculate multiple flatness metrics for a horn design.

    Returns:
        dict with flatness metrics for different frequency ranges
    """
    # Flatness in different ranges
    bass_flatness = objective_response_flatness(
        design, driver, "multisegment_horn",
        frequency_range=(20, 100),
        n_points=50,
        num_segments=2
    )

    midbass_flatness = objective_response_flatness(
        design, driver, "multisegment_horn",
        frequency_range=(f3, 200),
        n_points=80,
        num_segments=2
    )

    full_band_flatness = objective_response_flatness(
        design, driver, "multisegment_horn",
        frequency_range=(20, 500),
        n_points=100,
        num_segments=2
    )

    # Passband flatness (F3 to 200 Hz)
    try:
        passband_flat = objective_passband_flatness(
            design, driver, "multisegment_horn",
            hf_cutoff=200.0,
            n_points=80,
            num_segments=2
        )
    except:
        passband_flat = float('nan')

    return {
        'bass_flatness': bass_flatness,
        'midbass_flatness': midbass_flatness,
        'full_band_flatness': full_band_flatness,
        'passband_flatness': passband_flat,
    }


def main():
    print("=" * 80)
    print("BC_15DS115 Flatness Analysis")
    print("Evaluating frequency response flatness for Pareto-optimal designs")
    print("=" * 80)

    # Load driver
    print("\nLoading driver...")
    driver = load_driver("BC_15DS115")
    print(f"  Driver: BC_15DS115")

    # Since we don't have the saved optimization results, we'll re-generate
    # a few key designs from the results file
    print("\nGenerating key designs for flatness analysis...")

    # Key designs from the optimization results
    # Format: [throat_area, middle_area, mouth_area, length1, length2, T1, T2, V_tc, V_rc]
    key_designs = {
        'Best F3 (20 Hz)': np.array([
            0.0798, 0.150, 0.3285, 2.55, 3.77, 0.810, 1.000, 0.0, 0.151
        ]),
        'Good F3 (25 Hz)': np.array([
            0.0562, 0.150, 0.3003, 2.55, 3.12, 0.986, 0.990, 0.0, 0.127
        ]),
        'Balanced (32 Hz)': np.array([
            0.0445, 0.150, 0.3000, 1.60, 2.46, 0.961, 1.000, 0.0, 0.127
        ]),
        'Compact (35 Hz)': np.array([
            0.0445, 0.150, 0.3000, 1.50, 2.27, 0.981, 0.999, 0.0, 0.127
        ]),
        'Smallest (44 Hz)': np.array([
            0.0428, 0.150, 0.3000, 1.50, 1.51, 0.981, 0.996, 0.0, 0.127
        ]),
    }

    # Also create a sweep across the Pareto front
    print("\nGenerating Pareto front sweep...")
    pareto_designs = []

    # Sample from the optimization results (from the output file)
    # These represent the full range from best F3 to smallest cabinet
    sample_configs = [
        # [throat, middle, mouth, L1, L2, T1, T2, V_tc, V_rc, label_f3, label_vol]
        [0.0798, 0.150, 0.3285, 2.55, 3.77, 0.810, 1.000, 0.0, 0.151, 20.0, 1365],
        [0.0794, 0.150, 0.3028, 2.50, 3.60, 0.779, 1.000, 0.0, 0.145, 20.1, 1243],
        [0.0769, 0.150, 0.3000, 2.40, 3.29, 0.981, 0.999, 0.0, 0.137, 20.4, 1108],
        [0.0707, 0.150, 0.3000, 2.45, 3.26, 0.955, 0.996, 0.0, 0.127, 20.6, 1063],
        [0.0562, 0.150, 0.3003, 2.55, 3.12, 0.986, 0.990, 0.0, 0.127, 21.6, 998],
        [0.0496, 0.150, 0.3003, 2.50, 3.14, 0.981, 0.998, 0.0, 0.127, 22.3, 951],
        [0.0450, 0.150, 0.3000, 2.40, 3.14, 0.941, 0.992, 0.0, 0.127, 23.0, 906],
        [0.0428, 0.150, 0.3000, 2.50, 3.10, 0.969, 1.000, 0.0, 0.127, 23.1, 887],
        [0.0428, 0.150, 0.3000, 2.10, 3.29, 0.985, 0.997, 0.0, 0.127, 24.2, 848],
        [0.0428, 0.150, 0.3000, 2.05, 3.19, 0.987, 0.998, 0.0, 0.127, 24.6, 837],
        [0.0428, 0.150, 0.3000, 1.90, 3.27, 0.981, 0.996, 0.0, 0.127, 25.0, 826],
        [0.0445, 0.150, 0.3000, 1.95, 3.12, 0.968, 1.000, 0.0, 0.127, 25.4, 810],
        [0.0428, 0.150, 0.3000, 1.85, 3.10, 0.981, 0.996, 0.0, 0.127, 25.8, 802],
        [0.0430, 0.150, 0.3000, 1.80, 3.13, 0.980, 0.996, 0.0, 0.127, 26.2, 788],
        [0.0428, 0.150, 0.3000, 1.75, 3.14, 0.980, 0.996, 0.0, 0.127, 26.5, 778],
        [0.0428, 0.150, 0.3002, 1.70, 3.15, 0.986, 1.000, 0.0, 0.127, 26.7, 772],
        [0.0428, 0.150, 0.3001, 1.65, 3.20, 0.972, 0.999, 0.0, 0.127, 27.1, 762],
        [0.0434, 0.150, 0.3000, 1.60, 3.17, 0.985, 1.000, 0.0, 0.127, 27.6, 750],
        [0.0430, 0.150, 0.3000, 1.55, 3.19, 0.978, 1.000, 0.0, 0.127, 28.0, 739],
        [0.0428, 0.150, 0.3002, 1.50, 3.20, 0.974, 1.000, 0.0, 0.127, 28.1, 733],
        [0.0430, 0.150, 0.3000, 1.50, 3.10, 0.982, 0.999, 0.0, 0.127, 28.3, 730],
        [0.0428, 0.150, 0.3000, 1.45, 3.12, 0.982, 0.996, 0.0, 0.127, 28.7, 721],
        [0.0443, 0.150, 0.3000, 1.40, 3.08, 0.982, 0.995, 0.0, 0.127, 28.7, 724],
        [0.0428, 0.150, 0.3000, 1.40, 3.08, 0.981, 0.999, 0.0, 0.127, 29.0, 713],
        [0.0443, 0.150, 0.3000, 1.35, 3.13, 0.981, 0.999, 0.0, 0.127, 29.4, 702],
        [0.0440, 0.150, 0.3001, 1.30, 3.16, 0.978, 1.000, 0.0, 0.127, 29.5, 693],
        [0.0440, 0.150, 0.3001, 1.25, 3.14, 0.978, 0.998, 0.0, 0.127, 29.8, 689],
        [0.0445, 0.150, 0.3001, 1.20, 3.17, 0.989, 0.999, 0.0, 0.127, 29.9, 686],
        [0.0445, 0.150, 0.3001, 1.15, 3.15, 0.972, 0.999, 0.0, 0.127, 30.3, 676],
        [0.0445, 0.150, 0.3001, 1.10, 3.18, 0.981, 0.999, 0.0, 0.127, 30.4, 672],
        [0.0428, 0.150, 0.3000, 1.10, 3.18, 0.981, 0.996, 0.0, 0.127, 30.9, 665],
        [0.0428, 0.150, 0.3000, 1.05, 3.15, 0.981, 0.996, 0.0, 0.127, 31.3, 660],
        [0.0442, 0.150, 0.3000, 1.00, 3.18, 0.981, 0.996, 0.0, 0.127, 31.4, 651],
        [0.0452, 0.150, 0.3000, 0.95, 3.14, 0.906, 0.998, 0.0, 0.127, 31.9, 644],
        [0.0430, 0.150, 0.3000, 1.05, 3.10, 0.978, 1.000, 0.0, 0.127, 32.3, 641],
        [0.0445, 0.150, 0.3000, 1.00, 3.06, 0.961, 1.000, 0.0, 0.127, 32.4, 633],
        [0.0432, 0.150, 0.3000, 0.95, 3.07, 0.962, 1.000, 0.0, 0.127, 32.9, 632],
        [0.0428, 0.150, 0.3001, 0.95, 3.07, 0.961, 0.994, 0.0, 0.127, 33.0, 625],
        [0.0430, 0.150, 0.3007, 0.90, 3.14, 0.980, 1.000, 0.0, 0.127, 33.3, 622],
        [0.0430, 0.150, 0.3007, 0.85, 3.16, 0.975, 1.000, 0.0, 0.127, 33.5, 618],
        [0.0464, 0.150, 0.3006, 0.75, 3.13, 0.985, 0.999, 0.0, 0.127, 33.5, 611],
        [0.0429, 0.150, 0.3001, 0.82, 3.10, 0.980, 1.000, 0.0, 0.127, 33.8, 610],
        [0.0428, 0.150, 0.3001, 0.80, 3.10, 0.980, 1.000, 0.0, 0.127, 34.0, 607],
        [0.0450, 0.150, 0.3001, 0.75, 3.09, 0.982, 1.000, 0.0, 0.127, 34.1, 600],
        [0.0438, 0.150, 0.3007, 0.72, 3.12, 0.973, 0.999, 0.0, 0.127, 34.5, 596],
        [0.0431, 0.150, 0.3001, 0.76, 3.10, 0.984, 1.000, 0.0, 0.127, 34.7, 594],
        [0.0431, 0.150, 0.3001, 0.68, 3.10, 0.984, 1.000, 0.0, 0.127, 35.0, 589],
        [0.0431, 0.150, 0.3001, 0.66, 3.10, 0.982, 1.000, 0.0, 0.127, 35.1, 587],
        [0.0450, 0.150, 0.3001, 0.61, 3.10, 0.962, 1.000, 0.0, 0.127, 35.2, 580],
        [0.0428, 0.150, 0.3001, 0.61, 3.10, 0.978, 0.995, 0.0, 0.127, 35.7, 577],
        [0.0535, 0.150, 0.3001, 0.51, 3.00, 0.935, 1.000, 0.0, 0.127, 36.3, 571],
        [0.0428, 0.150, 0.3001, 0.72, 2.90, 0.957, 0.992, 0.0, 0.127, 36.7, 564],
        [0.0445, 0.150, 0.3008, 0.67, 2.90, 0.988, 0.996, 0.0, 0.127, 36.9, 557],
        [0.0531, 0.150, 0.3001, 0.51, 2.90, 0.983, 1.000, 0.0, 0.127, 37.4, 554],
        [0.0457, 0.150, 0.3000, 0.58, 2.90, 0.980, 1.000, 0.0, 0.127, 37.5, 543],
        [0.0440, 0.150, 0.3000, 0.58, 2.90, 0.980, 1.000, 0.0, 0.127, 37.9, 542],
        [0.0447, 0.150, 0.3001, 0.59, 2.90, 0.959, 0.999, 0.0, 0.127, 38.0, 541],
        [0.0440, 0.150, 0.3000, 0.58, 2.90, 0.956, 0.998, 0.0, 0.127, 38.2, 536],
        [0.0440, 0.150, 0.3000, 0.49, 2.90, 0.978, 1.000, 0.0, 0.127, 38.8, 527],
        [0.0447, 0.150, 0.3001, 0.47, 2.90, 0.939, 0.999, 0.0, 0.127, 39.0, 527],
        [0.0433, 0.150, 0.3002, 0.46, 2.90, 0.953, 1.000, 0.0, 0.127, 39.4, 520],
        [0.0429, 0.150, 0.3001, 0.45, 2.90, 0.975, 1.000, 0.0, 0.127, 39.8, 516],
        [0.0443, 0.150, 0.3001, 0.38, 2.90, 0.959, 0.999, 0.0, 0.127, 40.2, 513],
        [0.0437, 0.150, 0.3002, 0.39, 2.90, 0.954, 0.996, 0.0, 0.127, 40.7, 507],
        [0.0444, 0.150, 0.3002, 0.33, 2.90, 0.960, 0.996, 0.0, 0.127, 40.7, 503],
        [0.0444, 0.150, 0.3015, 0.30, 2.90, 0.959, 1.000, 0.0, 0.127, 41.2, 502],
        [0.0444, 0.150, 0.3000, 0.26, 2.90, 0.962, 0.993, 0.0, 0.127, 41.7, 493],
        [0.0428, 0.150, 0.3014, 0.27, 2.90, 0.920, 0.996, 0.0, 0.127, 42.1, 489],
        [0.0428, 0.150, 0.3000, 0.24, 2.90, 0.959, 0.998, 0.0, 0.127, 42.7, 484],
        [0.0444, 0.150, 0.3001, 0.16, 2.90, 0.959, 0.998, 0.0, 0.127, 43.0, 478],
        [0.0428, 0.150, 0.3001, 0.16, 2.90, 0.959, 0.998, 0.0, 0.127, 43.4, 471],
        [0.0428, 0.150, 0.3000, 0.15, 2.86, 0.981, 0.996, 0.0, 0.127, 44.0, 466],
        [0.0428, 0.150, 0.3000, 0.15, 2.85, 0.941, 0.998, 0.0, 0.127, 44.2, 465],
        [0.0428, 0.150, 0.3000, 0.15, 2.86, 0.979, 1.000, 0.0, 0.127, 76.2, 463],
        [0.0428, 0.150, 0.3000, 0.15, 2.86, 0.979, 0.996, 0.0, 0.127, 76.3, 460],
    ]

    results = []

    print(f"\nEvaluating {len(sample_configs)} designs...")
    for i, cfg in enumerate(sample_configs):
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(sample_configs)}]")

        design = np.array(cfg[:9])
        f3_target = cfg[9]
        vol_target = cfg[10]

        # Build horn
        try:
            horn, V_tc, V_rc = build_multisegment_horn(design, driver, num_segments=2)
            flh = FrontLoadedHorn(driver, horn, V_tc=V_tc, V_rc=V_rc)

            # Calculate F3
            f3_actual = objective_f3(design, driver, "multisegment_horn")

            # Calculate flatness metrics
            flatness = calculate_comprehensive_flatness(design, driver, flh, f3_actual)

            # Get parameters
            params = decode_hyperbolic_design(design, driver, num_segments=2)

            results.append({
                'f3_target': f3_target,
                'f3_actual': f3_actual,
                'volume': vol_target,
                'throat': params['throat_area'] * 10000,
                'mouth': params['mouth_area'] * 10000,
                'length': params['segments'][0][2] + params['segments'][1][2],
                'T1': params['T_params'][0],
                'T2': params['T_params'][1],
                **flatness,
            })
        except Exception as e:
            print(f"  Error evaluating design {i}: {e}")
            continue

    # Convert to arrays for plotting
    f3_values = np.array([r['f3_actual'] for r in results])
    vol_values = np.array([r['volume'] for r in results])
    bass_flat = np.array([r['bass_flatness'] for r in results])
    midbass_flat = np.array([r['midbass_flatness'] for r in results])
    full_band_flat = np.array([r['full_band_flatness'] for r in results])

    print("\n" + "=" * 80)
    print("FLATNESS ANALYSIS RESULTS")
    print("=" * 80)

    print(f"\nEvaluated {len(results)} designs successfully")
    print(f"\nBass flatness (20-100 Hz): {bass_flat.min():.2f} - {bass_flat.max():.2f} dB")
    print(f"Midbass flatness (F3-200 Hz): {midbass_flat.min():.2f} - {midbass_flat.max():.2f} dB")
    print(f"Full band flatness (20-500 Hz): {full_band_flat.min():.2f} - {full_band_flat.max():.2f} dB")

    # Find best designs by different metrics
    best_bass_idx = np.argmin(bass_flat)
    best_midbass_idx = np.argmin(midbass_flat)
    best_full_idx = np.argmin(full_band_flat)

    print("\n" + "=" * 80)
    print("BEST DESIGNS BY FLATNESS METRIC")
    print("=" * 80)

    def print_design(idx, label):
        r = results[idx]
        print(f"\n{label}")
        print("-" * 70)
        print(f"  F3: {r['f3_actual']:.1f} Hz")
        print(f"  Volume: {r['volume']:.0f} L")
        print(f"  Bass flatness (20-100 Hz): {r['bass_flatness']:.2f} dB")
        print(f"  Midbass flatness (F3-200 Hz): {r['midbass_flatness']:.2f} dB")
        print(f"  Full band flatness (20-500 Hz): {r['full_band_flatness']:.2f} dB")
        print(f"  Length: {r['length']:.2f} m")
        print(f"  Throat: {r['throat']:.0f} cm²")
        print(f"  Mouth: {r['mouth']:.0f} cm²")
        print(f"  T1: {r['T1']:.3f}, T2: {r['T2']:.3f}")

    print_design(best_bass_idx, "BEST BASS FLATNESS (20-100 Hz)")
    print_design(best_midbass_idx, "BEST MIDBASS FLATNESS (F3-200 Hz)")
    print_design(best_full_idx, "BEST FULL BAND FLATNESS (20-500 Hz)")

    # Find balanced design (good F3 + good flatness)
    # Normalize all metrics to 0-1
    f3_norm = (f3_values - f3_values.min()) / (f3_values.max() - f3_values.min())
    vol_norm = (vol_values - vol_values.min()) / (vol_values.max() - vol_values.min())
    bass_flat_norm = (bass_flat - bass_flat.min()) / (bass_flat.max() - bass_flat.min())

    # Combined score (lower is better)
    combined = f3_norm + vol_norm + bass_flat_norm
    balanced_idx = np.argmin(combined)

    print("\n" + "=" * 80)
    print("BALANCED DESIGN (Best F3 + Size + Flatness)")
    print("=" * 80)
    print_design(balanced_idx, "BALANCED OPTIMUM")

    # Create plots
    print("\nGenerating plots...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Bass flatness vs F3
    sc1 = axes[0, 0].scatter(f3_values, bass_flat, c=vol_values, cmap='viridis',
                              s=100, alpha=0.7, edgecolors='black', linewidths=1)
    axes[0, 0].scatter(f3_values[best_bass_idx], bass_flat[best_bass_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2, zorder=10)
    axes[0, 0].set_xlabel('F3 (Hz)', fontsize=12)
    axes[0, 0].set_ylabel('Bass Flatness (dB)', fontsize=12)
    axes[0, 0].set_title('Bass Flatness (20-100 Hz) vs F3', fontsize=14)
    axes[0, 0].grid(True, alpha=0.3)
    cbar1 = plt.colorbar(sc1, ax=axes[0, 0])
    cbar1.set_label('Volume (L)', fontsize=10)

    # Plot 2: Midbass flatness vs F3
    sc2 = axes[0, 1].scatter(f3_values, midbass_flat, c=vol_values, cmap='viridis',
                              s=100, alpha=0.7, edgecolors='black', linewidths=1)
    axes[0, 1].scatter(f3_values[best_midbass_idx], midbass_flat[best_midbass_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2, zorder=10)
    axes[0, 1].set_xlabel('F3 (Hz)', fontsize=12)
    axes[0, 1].set_ylabel('Midbass Flatness (dB)', fontsize=12)
    axes[0, 1].set_title('Midbass Flatness (F3-200 Hz) vs F3', fontsize=14)
    axes[0, 1].grid(True, alpha=0.3)
    cbar2 = plt.colorbar(sc2, ax=axes[0, 1])
    cbar2.set_label('Volume (L)', fontsize=10)

    # Plot 3: Full band flatness vs Volume
    sc3 = axes[1, 0].scatter(vol_values, full_band_flat, c=f3_values, cmap='RdYlGn_r',
                              s=100, alpha=0.7, edgecolors='black', linewidths=1)
    axes[1, 0].scatter(vol_values[best_full_idx], full_band_flat[best_full_idx],
                       c='red', s=300, marker='*', edgecolors='black', linewidths=2, zorder=10)
    axes[1, 0].set_xlabel('Total Volume (L)', fontsize=12)
    axes[1, 0].set_ylabel('Full Band Flatness (dB)', fontsize=12)
    axes[1, 0].set_title('Full Band Flatness (20-500 Hz) vs Volume', fontsize=14)
    axes[1, 0].grid(True, alpha=0.3)
    cbar3 = plt.colorbar(sc3, ax=axes[1, 0])
    cbar3.set_label('F3 (Hz)', fontsize=10)

    # Plot 4: 3D scatter - F3, Volume, Bass Flatness
    sc4 = axes[1, 1].scatter(f3_values, vol_values, c=bass_flat, cmap='coolwarm',
                              s=100, alpha=0.7, edgecolors='black', linewidths=1)
    axes[1, 1].scatter(f3_values[balanced_idx], vol_values[balanced_idx],
                       c='purple', s=300, marker='*', edgecolors='black', linewidths=2, zorder=10)
    axes[1, 1].set_xlabel('F3 (Hz)', fontsize=12)
    axes[1, 1].set_ylabel('Total Volume (L)', fontsize=12)
    axes[1, 1].set_title('Pareto Front colored by Bass Flatness', fontsize=14)
    axes[1, 1].grid(True, alpha=0.3)
    cbar4 = plt.colorbar(sc4, ax=axes[1, 1])
    cbar4.set_label('Bass Flatness (dB)', fontsize=10)

    plt.tight_layout()

    plot_file = "tasks/bc15ds115_flatness_analysis.png"
    plt.savefig(plot_file, dpi=150)
    print(f"Plot saved to: {plot_file}")

    # Save results
    output_file = "tasks/bc15ds115_flatness_results.txt"
    with open(output_file, 'w') as f:
        f.write("BC_15DS115 Flatness Analysis Results\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Evaluated {len(results)} designs\n\n")

        f.write("Flatness Ranges:\n")
        f.write(f"  Bass (20-100 Hz): {bass_flat.min():.2f} - {bass_flat.max():.2f} dB\n")
        f.write(f"  Midbass (F3-200 Hz): {midbass_flat.min():.2f} - {midbass_flat.max():.2f} dB\n")
        f.write(f"  Full band (20-500 Hz): {full_band_flat.min():.2f} - {full_band_flat.max():.2f} dB\n\n")

        f.write("All Results:\n")
        f.write(f"{'F3':<8} {'Vol':<8} {'Bass':<8} {'Midbass':<10} {'Full':<8} {'T1':<6} {'T2':<6}\n")
        f.write("-" * 80 + "\n")

        for r in results:
            f.write(f"{r['f3_actual']:<8.1f} {r['volume']:<8.0f} "
                   f"{r['bass_flatness']:<8.2f} {r['midbass_flatness']:<10.2f} "
                   f"{r['full_band_flatness']:<8.2f} "
                   f"{r['T1']:<6.3f} {r['T2']:<6.3f}\n")

    print(f"Results saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
