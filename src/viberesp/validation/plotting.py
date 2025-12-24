"""Generate validation plots comparing Viberesp and Hornresp.

This module creates multi-subplot figures showing SPL comparison,
difference plots, phase comparison, and metrics summary.
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from .comparison import ComparisonResult
from .metrics import ValidationMetrics


def plot_validation(
    comparison: ComparisonResult,
    metrics: ValidationMetrics,
    driver_name: str,
    volume: float,
    output_path: Optional[str | Path] = None,
    show: bool = False,
) -> plt.Figure:
    """Generate comprehensive validation comparison plot.

    Creates a 2x2 subplot layout:
    - Top left: SPL overlay comparison
    - Top right: SPL difference with reference bands
    - Bottom left: Phase comparison (if available)
    - Bottom right: Metrics summary text

    Args:
        comparison: ComparisonResult from compare_responses()
        metrics: ValidationMetrics from calculate_validation_metrics()
        driver_name: Driver name for title
        volume: Enclosure volume in liters
        output_path: Path to save figure (optional)
        show: Whether to display the plot interactively

    Returns:
        matplotlib Figure object
    """
    # Determine if phase data is available
    has_phase = (
        comparison.viberesp_phase_aligned is not None
        and comparison.hornresp_phase is not None
    )

    # Create figure with appropriate subplot layout
    if has_phase:
        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        ax_spl, ax_diff, ax_phase, ax_metrics = axes.flatten()
    else:
        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        ax_spl, ax_diff, ax_metrics, ax_empty = axes.flatten()
        ax_empty.axis('off')
        ax_phase = None

    fig.suptitle(
        f'Hornresp Validation: {driver_name} in {volume:.1f}L Sealed Enclosure',
        fontsize=14,
        fontweight='bold',
    )

    # Plot 1: SPL overlay
    ax_spl.semilogx(
        comparison.common_freq,
        comparison.hornresp_spl,
        'r--',
        linewidth=1.5,
        label='Hornresp',
        alpha=0.8,
    )
    ax_spl.semilogx(
        comparison.common_freq,
        comparison.viberesp_spl_aligned,
        'b-',
        linewidth=1.5,
        label='Viberesp',
        alpha=0.8,
    )
    ax_spl.set_xlabel('Frequency (Hz)')
    ax_spl.set_ylabel('SPL (dB)')
    ax_spl.set_title('Frequency Response Comparison')
    ax_spl.grid(True, alpha=0.3)
    ax_spl.legend(loc='best')

    # Set reasonable y-limits
    all_spl = np.concatenate([
        comparison.hornresp_spl,
        comparison.viberesp_spl_aligned,
    ])
    valid_spl = all_spl[~np.isnan(all_spl)]
    if len(valid_spl) > 0:
        y_min = np.min(valid_spl) - 5
        y_max = np.max(valid_spl) + 5
        ax_spl.set_ylim(y_min, y_max)

    # Plot 2: SPL difference
    ax_diff.semilogx(
        comparison.common_freq,
        comparison.spl_difference,
        'g-',
        linewidth=1.5,
    )
    ax_diff.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax_diff.axhline(0.5, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.axhline(-0.5, color='gray', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.axhline(1.0, color='orange', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.axhline(-1.0, color='orange', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.axhline(2.0, color='red', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.axhline(-2.0, color='red', linestyle=':', linewidth=0.8, alpha=0.6)
    ax_diff.set_xlabel('Frequency (Hz)')
    ax_diff.set_ylabel('Difference (Viberesp - Hornresp) [dB]')
    ax_diff.set_title('SPL Difference')
    ax_diff.grid(True, alpha=0.3)

    # Add reference band labels
    ax_diff.text(
        0.02,
        0.95,
        'Reference: ±0.5, ±1, ±2 dB',
        transform=ax_diff.transAxes,
        fontsize=8,
        verticalalignment='top',
    )

    # Set reasonable y-limits for difference plot
    valid_diff = comparison.spl_difference[~np.isnan(comparison.spl_difference)]
    if len(valid_diff) > 0:
        max_diff = np.max(np.abs(valid_diff))
        y_limit = max(3, max_diff + 0.5)
        ax_diff.set_ylim(-y_limit, y_limit)

    # Plot 3: Phase comparison (if available)
    if has_phase and ax_phase is not None:
        ax_phase.semilogx(
            comparison.common_freq,
            comparison.hornresp_phase,
            'r--',
            linewidth=1.5,
            label='Hornresp',
            alpha=0.8,
        )
        ax_phase.semilogx(
            comparison.common_freq,
            comparison.viberesp_phase_aligned,
            'b-',
            linewidth=1.5,
            label='Viberesp',
            alpha=0.8,
        )
        ax_phase.set_xlabel('Frequency (Hz)')
        ax_phase.set_ylabel('Phase (degrees)')
        ax_phase.set_title('Phase Comparison')
        ax_phase.grid(True, alpha=0.3)
        ax_phase.legend(loc='best')
        ax_phase.set_ylim(-200, 200)

    # Plot 4: Metrics summary
    ax_metrics.axis('off')

    # Build metrics text
    metrics_text = f"""
VALIDATION METRICS
{'=' * 40}

Overall Agreement: {metrics.agreement_score:.1f}%

SPL Magnitude Errors:
  RMSE: {metrics.rmse:.3f} dB
  MAE:  {metrics.mae:.3f} dB
  Max:  {metrics.max_error:.3f} dB @ {metrics.max_error_freq:.1f} Hz

Band-Specific RMSE:
  Passband (200-500 Hz):
    {metrics.passband_rmse:.3f} dB
  Bass (20-200 Hz):
    {metrics.bass_rmse:.3f} dB

F3 Frequency:
  Viberesp:  {metrics.f3_viberesp:.2f} Hz
  Hornresp:  {metrics.f3_hornresp:.2f} Hz
  Error:     {metrics.f3_error:.2f} Hz

Correlation: {metrics.correlation:.4f}

Passband Offset Applied: {comparison.passband_offset:.3f} dB
"""

    ax_metrics.text(
        0.1,
        0.95,
        metrics_text,
        transform=ax_metrics.transAxes,
        fontsize=10,
        verticalalignment='top',
        fontfamily='monospace',
    )

    plt.tight_layout()

    # Save or show
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

    if show:
        plt.show()

    return fig


def plot_spl_only(
    comparison: ComparisonResult,
    driver_name: str,
    volume: float,
    output_path: Optional[str | Path] = None,
    show: bool = False,
) -> plt.Figure:
    """Generate simple SPL-only comparison plot.

    Useful for quick validation checks without full metrics.

    Args:
        comparison: ComparisonResult from compare_responses()
        driver_name: Driver name for title
        volume: Enclosure volume in liters
        output_path: Path to save figure (optional)
        show: Whether to display the plot interactively

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.semilogx(
        comparison.common_freq,
        comparison.hornresp_spl,
        'r--',
        linewidth=2,
        label='Hornresp',
        alpha=0.8,
    )
    ax.semilogx(
        comparison.common_freq,
        comparison.viberesp_spl_aligned,
        'b-',
        linewidth=2,
        label='Viberesp',
        alpha=0.8,
    )

    ax.set_xlabel('Frequency (Hz)', fontsize=12)
    ax.set_ylabel('SPL (dB)', fontsize=12)
    ax.set_title(
        f'Hornresp Validation: {driver_name} in {volume:.1f}L Sealed Enclosure',
        fontsize=14,
        fontweight='bold',
    )
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=11)

    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

    if show:
        plt.show()

    return fig


def plot_hornresp_style(
    comparison: ComparisonResult,
    data_source: str = 'viberesp',
    output_path: Optional[str | Path] = None,
    show: bool = False,
) -> plt.Figure:
    """Generate Hornresp-style single curve plot.

    Creates a minimal, clean visualization matching Hornresp's style:
    - Single SPL curve (red solid line)
    - Semilog frequency axis
    - Clean grid
    - No legend or metrics overlay

    Args:
        comparison: ComparisonResult from compare_responses()
        data_source: Which data to plot - 'viberesp', 'hornresp', or 'both'
            If 'both', plots Viberesp as solid red and Hornresp as dashed gray
        output_path: Path to save figure (optional)
        show: Whether to display the plot interactively

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Select data based on source preference
    if data_source == 'hornresp':
        data = comparison.hornresp_spl
        color = 'red'
        linestyle = '-'
        linewidth = 2.0
        label = None
    elif data_source == 'viberesp':
        data = comparison.viberesp_spl_aligned
        color = 'red'
        linestyle = '-'
        linewidth = 2.0
        label = None
    elif data_source == 'both':
        # Plot Viberesp as solid red
        ax.semilogx(
            comparison.common_freq,
            comparison.viberesp_spl_aligned,
            'r-',
            linewidth=2.0,
            label='Viberesp',
        )
        # Plot Hornresp as dashed gray for comparison
        ax.semilogx(
            comparison.common_freq,
            comparison.hornresp_spl,
            color='gray',
            linestyle='--',
            linewidth=1.5,
            alpha=0.7,
            label='Hornresp',
        )
        color = None  # Already set above
        linestyle = None
        linewidth = None
        label = None
    else:
        raise ValueError(f"Invalid data_source: {data_source}. Must be 'viberesp', 'hornresp', or 'both'")

    # Plot single curve if not 'both'
    if data_source in ('viberesp', 'hornresp'):
        ax.semilogx(
            comparison.common_freq,
            data,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            label=label,
        )

    # Style to match Hornresp
    ax.set_xlabel('Frequency (Hz)', fontsize=11)
    ax.set_ylabel('Sound Pressure Level (dB)', fontsize=11)
    ax.grid(True, which='both', alpha=0.4, linestyle='-', linewidth=0.5)

    # Set reasonable y-limits
    all_data = [comparison.hornresp_spl, comparison.viberesp_spl_aligned]
    valid_data = np.concatenate([d[~np.isnan(d)] for d in all_data])
    if len(valid_data) > 0:
        y_min = np.min(valid_data) - 5
        y_max = np.max(valid_data) + 5
        ax.set_ylim(y_min, y_max)

    # Add legend only if showing both curves
    if data_source == 'both':
        ax.legend(loc='best', fontsize=10)

    plt.tight_layout()

    # Save or show
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")

    if show:
        plt.show()

    return fig
