"""
Predefined optimization presets for common horn design scenarios.

This module provides pre-configured optimization templates that encapsulate
best practices for different design goals. Each preset specifies objectives,
constraints, and parameter space settings for a specific use case.

Presets:
    f3_target: Optimize for specific cutoff frequency with smooth response
    size_vs_f3: Explore trade-off between enclosure size and bass extension
    compact_bass: Small enclosure with acceptable bass extension
    max_efficiency: Maximize horn efficiency at target frequency
    flat_response: Prioritize smooth frequency response over extension
    balanced: Balanced trade-off between size, extension, and response quality
"""

from typing import Dict, Any, List


# Preset configurations
# Each preset defines: objectives, default constraints, parameter space preset
OPTIMIZATION_PRESETS: Dict[str, Dict[str, Any]] = {
    "f3_target": {
        "description": "Optimize for specific cutoff frequency with smooth response",
        "objectives": ["f3_deviation", "flatness"],
        "default_constraints": {
            "f3_target": 34.0,
            "f3_tolerance": 2.0,
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "Match room gain characteristics",
            "Align with main speaker crossover point",
            "Meet specific performance requirements",
        ],
    },

    "size_vs_f3": {
        "description": "Explore trade-off between enclosure size and bass extension",
        "objectives": ["f3", "volume", "flatness"],
        "default_constraints": {
            "max_volume": 500.0,  # liters
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "Find optimal size for given space constraints",
            "Understand size vs performance trade-offs",
            "Select design for specific application",
        ],
    },

    "compact_bass": {
        "description": "Small enclosure with acceptable bass extension",
        "objectives": ["volume", "flatness"],
        "default_constraints": {
            "f3_max": 45.0,
            "max_volume": 200.0,  # liters
        },
        "parameter_space_preset": "compact",
        "typical_use_cases": [
            "Desktop or bookshelf systems",
            "Portable sound systems",
            "Space-constrained installations",
        ],
    },

    "max_efficiency": {
        "description": "Maximize horn efficiency at target frequency",
        "objectives": ["efficiency", "flatness"],
        "default_constraints": {
            "f3_max": 50.0,
            "min_efficiency": 0.15,  # 15%
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "High-efficiency main speakers",
            "Sound reinforcement systems",
            "Applications requiring high SPL with low power",
        ],
    },

    "flat_response": {
        "description": "Prioritize smooth frequency response over extension",
        "objectives": ["flatness", "f3"],
        "default_constraints": {
            "max_volume": 400.0,  # liters
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "High-fidelity systems",
            "Critical listening applications",
            "Studio monitoring",
        ],
    },

    "balanced": {
        "description": "Balanced trade-off between size, extension, and response quality",
        "objectives": ["f3", "volume", "flatness"],
        "default_constraints": {
            "max_volume": 350.0,  # liters
            "f3_max": 40.0,
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "General purpose bass horn",
            "Home theater subwoofers",
            "All-around performance",
        ],
    },

    "large_bass_horn": {
        "description": "Large bass horn for maximum extension and output",
        "objectives": ["f3", "flatness"],
        "default_constraints": {
            "min_mouth_area": 0.8,  # m² (large mouth for proper loading)
            "min_length": 2.5,  # meters (long horn for low cutoff)
        },
        "parameter_space_preset": "bass_horn",
        "typical_use_cases": [
            "Dedicated home theater",
            "High-output PA systems",
            "Applications where size is not constrained",
        ],
    },

    "midrange_horn": {
        "description": "Optimize midrange horn for smooth response and pattern control",
        "objectives": ["passband_flatness", "wavefront_sphericity"],
        "default_constraints": {
            "passband_range": [500, 5000],  # Hz
            "max_volume": 50.0,  # liters
        },
        "parameter_space_preset": "midrange_horn",
        "typical_use_cases": [
            "Midrange horns in multi-way systems",
            "Constant directivity horns",
            "PA system midrange drivers",
        ],
    },

    "folded_compact": {
        "description": "Optimize horn for compact folded implementation",
        "objectives": ["volume", "flatness", "f3"],
        "default_constraints": {
            "max_depth": 0.6,  # meters (fold depth constraint)
            "max_width": 0.5,  # meters
            "max_height": 0.5,  # meters
            "f3_max": 45.0,
        },
        "parameter_space_preset": "compact",
        "typical_use_cases": [
            "Folded horns for home use",
            "Compact bass bins",
            "Space-constrained folded designs",
        ],
    },
}


def get_available_presets() -> List[str]:
    """
    Get list of available preset names.

    Returns:
        List of preset names

    Examples:
        >>> get_available_presets()
        ['f3_target', 'size_vs_f3', 'compact_bass', ...]
    """
    return list(OPTIMIZATION_PRESETS.keys())


def get_preset_info(preset: str) -> Dict[str, Any]:
    """
    Get detailed information about a preset.

    Args:
        preset: Preset name

    Returns:
        Dictionary with preset information including description,
        objectives, constraints, and use cases

    Raises:
        ValueError: If preset not found

    Examples:
        >>> info = get_preset_info("f3_target")
        >>> print(info['description'])
        Optimize for specific cutoff frequency with smooth response
        >>> print(info['objectives'])
        ['f3_deviation', 'flatness']
    """
    if preset not in OPTIMIZATION_PRESETS:
        raise ValueError(
            f"Unknown preset '{preset}'. Available: {get_available_presets()}"
        )

    return OPTIMIZATION_PRESETS[preset].copy()


def print_preset_table():
    """
    Print a formatted table of all available presets.

    Useful for CLI display of available options.

    Examples:
        >>> print_preset_table()
        Available Optimization Presets:
        ...
    """
    print("\nAvailable Optimization Presets:")
    print("=" * 80)

    for name, config in OPTIMIZATION_PRESETS.items():
        print(f"\n{name}:")
        print(f"  Description: {config['description']}")
        print(f"  Objectives: {', '.join(config['objectives'])}")
        print(f"  Parameter Space: {config['parameter_space_preset']}")
        print(f"  Use Cases:")
        for use_case in config['typical_use_cases']:
            print(f"    - {use_case}")

    print("=" * 80)


def suggest_preset(
    target_f3: float = None,
    max_volume_liters: float = None,
    priority: str = "balanced"
) -> str:
    """
    Suggest appropriate preset based on design requirements.

    Args:
        target_f3: Target cutoff frequency in Hz
        max_volume_liters: Maximum enclosure volume in liters
        priority: Design priority ("size", "extension", "efficiency", "balanced")

    Returns:
        Recommended preset name

    Examples:
        >>> suggest_preset(target_f3=35, max_volume_liters=300)
        'f3_target'
        >>> suggest_preset(max_volume_liters=100, priority="size")
        'compact_bass'
    """
    # Size-constrained designs
    if max_volume_liters and max_volume_liters < 150:
        if target_f3 and target_f3 < 40:
            return "folded_compact"
        return "compact_bass"

    # Extension-focused
    if target_f3 and target_f3 < 35:
        if max_volume_liters and max_volume_liters > 400:
            return "large_bass_horn"
        return "f3_target"

    # Priority-based selection
    if priority == "size":
        return "compact_bass"
    elif priority == "extension":
        return "f3_target"
    elif priority == "efficiency":
        return "max_efficiency"
    elif priority == "balanced":
        if max_volume_liters and max_volume_liters < 300:
            return "size_vs_f3"
        return "balanced"

    # Default
    return "balanced"
