"""Plotting utilities for frequency response and optimization results."""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib.figure as mpl_figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available. Plotting functions will return None.")


def check_matplotlib() -> bool:
    """Check if matplotlib is available."""
    return MATPLOTLIB_AVAILABLE


def plot_frequency_response(
    frequency: np.ndarray,
    spl_db: np.ndarray,
    f3: Optional[float] = None,
    f10: Optional[float] = None,
    title: str = "Frequency Response",
    xlabel: str = "Frequency (Hz)",
    ylabel: str = "SPL (dB)",
    grid: bool = True,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    reference_line: bool = True,
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot frequency response curve.

    Args:
        frequency: Frequency array (Hz)
        spl_db: SPL array (dB)
        f3: -3dB frequency to mark (Hz)
        f10: -10dB frequency to mark (Hz)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        grid: Show grid
        xlim: X-axis limits (min, max)
        ylim: Y-axis limits (min, max)
        reference_line: Show -3dB reference line
        show: Display plot
        save_path: Save plot to file (optional)

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot frequency response
    ax.semilogx(frequency, spl_db, linewidth=2)

    # Mark F3 and F10
    if f3 is not None:
        ax.axvline(f3, color='r', linestyle='--', alpha=0.7, label=f'F3 = {f3:.1f} Hz')
        if reference_line:
            ax.axhline(-3, color='r', linestyle='--', alpha=0.3)

    if f10 is not None:
        ax.axvline(f10, color='orange', linestyle='--', alpha=0.7, label=f'F10 = {f10:.1f} Hz')
        if reference_line:
            ax.axhline(-10, color='orange', linestyle='--', alpha=0.3)

    # Labels and title
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(grid, alpha=0.3)

    # Set limits
    if xlim is not None:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim([20, 1000])

    if ylim is not None:
        ax.set_ylim(ylim)

    # Legend if markers were added
    if f3 is not None or f10 is not None:
        ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_multiple_responses(
    responses: List[Dict],
    labels: List[str],
    title: str = "Frequency Response Comparison",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot multiple frequency responses for comparison.

    Args:
        responses: List of dicts with 'frequency' and 'spl_db' arrays
        labels: Labels for each response
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    if len(responses) != len(labels):
        raise ValueError("Number of responses must match number of labels")

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.tab10(np.linspace(0, 1, len(responses)))

    for i, (response, label) in enumerate(zip(responses, labels)):
        ax.semilogx(
            response['frequency'],
            response['spl_db'],
            label=label,
            linewidth=2,
            color=colors[i]
        )

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("SPL (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([20, 1000])
    ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_pareto_front(
    pareto_front: List[Dict],
    objective_x: str = 'flatness',
    objective_y: str = 'bass_extension',
    title: str = "Pareto Front",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot Pareto front from multi-objective optimization.

    Args:
        pareto_front: List of solution dicts with 'objectives' key
        objective_x: X-axis objective name
        objective_y: Y-axis objective name
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Extract objective values
    x_values = [s['objectives'][objective_x] for s in pareto_front]
    y_values = [s['objectives'][objective_y] for s in pareto_front]

    # Plot Pareto front
    ax.scatter(x_values, y_values, alpha=0.6, s=50)

    # Label axes
    axis_labels = {
        'flatness': 'Passband Ripple (dB)',
        'bass_extension': 'F3 Frequency (normalized)',
        'efficiency': 'Efficiency (normalized)',
        'size': 'Box Volume (normalized)'
    }

    ax.set_xlabel(axis_labels.get(objective_x, objective_x))
    ax.set_ylabel(axis_labels.get(objective_y, objective_y))
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_impedance(
    frequency: np.ndarray,
    resistance: np.ndarray,
    reactance: Optional[np.ndarray] = None,
    impedance_mag: Optional[np.ndarray] = None,
    title: str = "Impedance",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot impedance response.

    Args:
        frequency: Frequency array (Hz)
        resistance: Resistance array (ohms)
        reactance: Reactance array (ohms), optional
        impedance_mag: Impedance magnitude array (ohms), optional
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot impedance magnitude if provided
    if impedance_mag is not None:
        ax.semilogx(frequency, impedance_mag, 'k-', linewidth=2, label='|Z|')

    # Plot resistance and reactance
    ax.semilogx(frequency, resistance, 'r-', linewidth=1.5, label='R')

    if reactance is not None:
        ax.semilogx(frequency, reactance, 'b-', linewidth=1.5, label='X')

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Impedance (Ω)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_group_delay(
    frequency: np.ndarray,
    group_delay_ms: np.ndarray,
    title: str = "Group Delay",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot group delay.

    Args:
        frequency: Frequency array (Hz)
        group_delay_ms: Group delay array (ms)
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.semilogx(frequency, group_delay_ms, linewidth=2)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Group Delay (ms)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([20, 1000])

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_cone_displacement(
    frequency: np.ndarray,
    displacement_mm: np.ndarray,
    xmax: Optional[float] = None,
    title: str = "Cone Displacement",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot cone displacement vs frequency.

    Args:
        frequency: Frequency array (Hz)
        displacement_mm: Displacement array (mm)
        xmax: Maximum linear excursion to mark (mm)
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.semilogx(frequency, displacement_mm, linewidth=2, label='Displacement')

    if xmax is not None:
        ax.axhline(xmax, color='r', linestyle='--', label=f'Xmax = {xmax:.1f} mm')
        ax.axhline(-xmax, color='r', linestyle='--', alpha=0.5)

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Displacement (mm)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([20, 500])
    ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_port_velocity(
    frequency: np.ndarray,
    velocity_m_s: np.ndarray,
    max_velocity: float = 17.0,
    title: str = "Port Air Velocity",
    show: bool = True,
    save_path: Optional[str] = None
) -> Optional[mpl_figure.Figure]:
    """
    Plot port air velocity (for detecting chuffing).

    Args:
        frequency: Frequency array (Hz)
        velocity_m_s: Port velocity array (m/s)
        max_velocity: Safe velocity limit (m/s)
        title: Plot title
        show: Display plot
        save_path: Save plot to file

    Returns:
        matplotlib Figure object or None if matplotlib unavailable
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available. Cannot create plot.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot velocity
    ax.semilogx(frequency, velocity_m_s, linewidth=2, label='Port Velocity')

    # Mark safety limits
    ax.axhline(max_velocity, color='g', linestyle='--', label=f'Safe ({max_velocity} m/s)')
    ax.axhline(max_velocity * 0.75, color='orange', linestyle='--',
              label=f'High ({max_velocity * 0.75:.1f} m/s)')
    ax.axhline(10.0, color='r', linestyle='--', label='Chuffing Risk (10 m/s)')

    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Port Air Velocity (m/s)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([20, 200])
    ax.legend()

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig
