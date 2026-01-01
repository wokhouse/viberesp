#!/usr/bin/env python3
"""
Generate all plot presets for available optimization results.

This script generates plots for all 4 presets (overview, spl, quality, correlations)
for each available optimization result file.

Author: Claude Code
Date: 2025-12-31
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import subprocess
from pathlib import Path

# Available optimization results
RESULT_FILES = [
    "tasks/results/bc_de250_optimization_FIXED.json",
    "tasks/results/bc_8ndl51_optimization_FIXED.json",
]

# Available plot presets
PRESETS = [
    "overview",
    "spl",
    "quality",
    "correlations",
]


def generate_plots():
    """Generate all plot presets for all result files."""
    print("=" * 80)
    print("GENERATING ALL PLOT PRESETS")
    print("=" * 80)
    print()

    plots_dir = Path("plots")
    plots_dir.mkdir(exist_ok=True)

    for result_file in RESULT_FILES:
        result_path = Path(result_file)

        if not result_path.exists():
            print(f"⚠️  Result file not found: {result_file}")
            continue

        # Extract driver name from filename
        driver_name = result_path.stem.replace("_optimization_FIXED", "")

        print(f"\n{'=' * 80}")
        print(f"Processing: {driver_name}")
        print(f"Result file: {result_file}")
        print(f"{'=' * 80}\n")

        for preset in PRESETS:
            print(f"  Generating preset: {preset}...", end=" ")

            # Build command
            cmd = [
                "viberesp",
                "plot",
                "auto",
                "--input", result_file,
                "--preset", preset,
                "--output-dir", f"plots/{driver_name}"
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    print("✅ SUCCESS")
                else:
                    print(f"❌ FAILED")
                    if result.stderr:
                        print(f"    Error: {result.stderr.strip()[:100]}")
            except subprocess.TimeoutExpired:
                print("❌ TIMEOUT")
            except Exception as e:
                print(f"❌ ERROR: {e}")

    print(f"\n{'=' * 80}")
    print("PLOT GENERATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nOutput directory: plots/")
    print("\nGenerated plots:")
    list_plots(plots_dir)


def list_plots(directory: Path):
    """List all generated plot files."""
    plot_files = []
    for ext in ["*.png", "*.pdf", "*.svg"]:
        plot_files.extend(directory.rglob(ext))

    if plot_files:
        for plot_file in sorted(plot_files):
            rel_path = plot_file.relative_to(directory.parent)
            size_kb = plot_file.stat().st_size / 1024
            print(f"  📊 {rel_path} ({size_kb:.1f} KB)")
    else:
        print("  (No plot files found)")

    print(f"\nTotal: {len(plot_files)} plot files")


if __name__ == "__main__":
    generate_plots()
