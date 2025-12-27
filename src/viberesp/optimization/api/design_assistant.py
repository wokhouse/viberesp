"""
High-level API for AI-assisted enclosure design.

This module provides the DesignAssistant class, which offers a clean,
agent-friendly interface for exploring enclosure design space. All methods
return structured data (dataclasses) rather than printing to stdout.

Example usage:
    >>> assistant = DesignAssistant()
    >>>
    >>> # Get recommendation
    >>> rec = assistant.recommend_design(
    ...     driver_name="BC_12NDL76",
    ...     max_volume_liters=50,
    ...     target_f3=60
    ... )
    >>> print(rec.enclosure_type)  # "sealed"
    >>> print(rec.reasoning)  # Explanation with citations
    >>>
    >>> # Explore parameter space
    >>> result = assistant.optimize_design(
    ...     driver_name="BC_12NDL76",
    ...     enclosure_type="sealed",
    ...     objectives=["f3", "size"]
    ... )
    >>> for design in result.best_designs[:3]:
    ...     print(design['parameters'], design['objectives'])
"""

import numpy as np
from typing import List, Dict, Optional

from viberesp.optimization.api.result_structures import (
    DesignRecommendation,
    OptimizationResult,
    ParameterSweepResult,
)
from viberesp.driver.parameters import ThieleSmallParameters


class DesignAssistant:
    """
    High-level API for AI-assisted enclosure design.

    This class provides a clean, agent-friendly interface for exploring
    enclosure design space. All methods return structured data (dataclasses)
    rather than printing to stdout.

    Attributes:
        validation_mode: If True, validate designs against Hornresp (when implemented)

    Example:
        >>> assistant = DesignAssistant()
        >>> rec = assistant.recommend_design(driver_name="BC_12NDL76")
        >>> print(rec.enclosure_type, rec.confidence)
    """

    def __init__(self, validation_mode: bool = True):
        """
        Initialize design assistant.

        Args:
            validation_mode: If True, validate designs against Hornresp
        """
        self.validation_mode = validation_mode

    def recommend_design(
        self,
        driver_name: str,
        objectives: List[str] = None,
        max_volume_liters: float = None,
        target_f3: float = None,
        enclosure_preference: str = "auto",
        efficiency_priority: bool = False
    ) -> DesignRecommendation:
        """
        Recommend enclosure type and initial design based on driver parameters.

        Literature:
            - Small (1972), Table 2 - Qts-based enclosure selection
            - Thiele (1971) - Alignment selection
            - Olson (1947) - Horn loading requirements

        Args:
            driver_name: Name of driver (must be in DRIVER_FACTORY)
            objectives: List of objectives (default: ["f3", "size"])
            max_volume_liters: Maximum enclosure volume in liters
            target_f3: Target cutoff frequency in Hz
            enclosure_preference: Preferred type ("sealed", "ported", "horn", "auto")
            efficiency_priority: Whether efficiency is critical

        Returns:
            DesignRecommendation with enclosure type, parameters, and reasoning

        Examples:
            >>> assistant = DesignAssistant()
            >>> rec = assistant.recommend_design(
            ...     driver_name="BC_12NDL76",
            ...     max_volume_liters=50,
            ...     target_f3=60
            ... )
            >>> rec.enclosure_type
            'sealed'
            >>> rec.confidence > 0.7
            True
        """
        from viberesp.driver import bc_drivers

        # Driver name to function mapping
        driver_functions = {
            "BC_8NDL51": bc_drivers.get_bc_8ndl51,
            "BC_12NDL76": bc_drivers.get_bc_12ndl76,
            "BC_15DS115": bc_drivers.get_bc_15ds115,
            "BC_18PZW100": bc_drivers.get_bc_18pzw100,
        }

        # Load driver
        if driver_name not in driver_functions:
            return DesignRecommendation(
                enclosure_type="unknown",
                confidence=0.0,
                reasoning=f"Unknown driver: {driver_name}",
                suggested_parameters={},
                expected_performance={},
                validation_notes=[f"Driver '{driver_name}' not found"]
            )

        driver = driver_functions[driver_name]()

        # Build user constraints dict
        user_constraints = {}
        if max_volume_liters:
            user_constraints["max_volume"] = max_volume_liters / 1000.0  # L to m³
        if target_f3:
            user_constraints["target_f3"] = target_f3
        if efficiency_priority:
            user_constraints["efficiency_priority"] = True

        # Get recommendation based on Qts
        qts = driver.Q_ts

        if enclosure_preference == "auto":
            # Qts-based recommendation (Small 1972, Table 2)
            if qts < 0.35:
                enc_type = "exponential_horn"
                confidence = 0.8
                reasoning = (
                    f"Qts={qts:.3f} is very low - excellent for horn loading.\n"
                    f"  • Small (1972): Qts < 0.40 suitable for horns\n"
                    f"  • High efficiency possible with proper horn design\n"
                    f"  • Note: Horn optimization requires horn simulation (Phase 3)"
                )
                alternatives = [
                    {"type": "sealed", "reason": "Possible but requires very small box (Qtc > 1.0)"}
                ]
            elif 0.35 <= qts < 0.45:
                enc_type = "sealed"
                confidence = 0.85
                reasoning = (
                    f"Qts={qts:.3f} is ideal for sealed box.\n"
                    f"  • Small (1972): Qts 0.35-0.45 optimal for sealed\n"
                    f"  • Butterworth alignment (Qtc=0.707) achievable\n"
                    f"  • Excellent transient response"
                )
                alternatives = [
                    {"type": "ported", "reason": "Possible but may require tuning below Fs"}
                ]
            elif 0.45 <= qts < 0.55:
                enc_type = "ported"
                confidence = 0.85
                reasoning = (
                    f"Qts={qts:.3f} is ideal for ported box.\n"
                    f"  • Thiele (1971): Qts ~0.38-0.45 for B4 alignment\n"
                    f"  • Lower F3 than sealed for same size\n"
                    f"  • Good efficiency"
                )
                alternatives = [
                    {"type": "sealed", "reason": "Good alternative with slightly larger box"}
                ]
            else:  # qts >= 0.55
                enc_type = "sealed"
                confidence = 0.75
                reasoning = (
                    f"Qts={qts:.3f} is high - best for sealed box or infinite baffle.\n"
                    f"  • Small (1972): Qts > 0.55 for large sealed boxes\n"
                    f"  • Ported box would be very large\n"
                    f"  • Good bass extension with large box"
                )
                alternatives = [
                    {"type": "infinite_baffle", "reason": "Also suitable for high Qts drivers"}
                ]
        else:
            enc_type = enclosure_preference
            confidence = 1.0  # User override
            reasoning = f"User-selected enclosure type: {enclosure_preference}"
            alternatives = []

        # Get alignment suggestions (simplified version)
        if enc_type == "sealed":
            # Target Qtc = 0.707 for Butterworth
            qtc_target = 0.707
            # Small (1972): Qtc = Qts × √(1 + Vas/Vb)
            # Solve for Vb: Vb = Vas / ((Qtc/Qts)² - 1)
            alpha = (qtc_target / qts) ** 2 - 1
            Vb = driver.V_as / alpha

            from viberesp.enclosure.sealed_box import calculate_sealed_box_system_parameters
            params = calculate_sealed_box_system_parameters(driver, Vb)

            expected_perf = {
                "F3": params.F3,
                "Qtc": params.Qtc,
                "Fc": params.Fc,
                "volume_liters": Vb * 1000
            }
            suggested_params = {"Vb": Vb}

        elif enc_type == "ported":
            # B4 alignment: Fb ≈ Fs, Vb ≈ Vas
            Vb = driver.V_as
            Fb = driver.F_s

            from viberesp.enclosure.ported_box import calculate_ported_box_system_parameters
            params = calculate_ported_box_system_parameters(driver, Vb, Fb)

            expected_perf = {
                "F3": params.F3,
                "Fb": Fb,
                "volume_liters": Vb * 1000
            }
            suggested_params = {"Vb": Vb, "Fb": Fb}

        else:
            # Horn - simplified placeholder
            expected_perf = {
                "note": "Horn optimization requires horn simulation (Phase 3)"
            }
            suggested_params = {}

        return DesignRecommendation(
            enclosure_type=enc_type,
            confidence=confidence,
            reasoning=reasoning,
            suggested_parameters=suggested_params,
            expected_performance=expected_perf,
            alternatives=alternatives,
            trade_offs=self._explain_trade_offs(driver, enc_type, expected_perf),
            validation_notes=[]
        )

    def optimize_design(
        self,
        driver_name: str,
        enclosure_type: str,
        objectives: List[str],
        constraints: Dict[str, float] = None,
        population_size: int = 100,
        generations: int = 100,
        top_n: int = 10
    ) -> OptimizationResult:
        """
        Run multi-objective optimization for enclosure design.

        Uses NSGA-II algorithm to find Pareto-optimal designs trading off
        multiple objectives.

        Literature:
            - Deb et al. (2002) - NSGA-II algorithm
            - Small (1972) - Enclosure design objectives

        Args:
            driver_name: Name of driver
            enclosure_type: "sealed", "ported" (horn not yet supported)
            objectives: List of objectives ["f3", "flatness", "efficiency", "size"]
            constraints: Dict of constraint values (optional)
            population_size: Population size for NSGA-II (default 100)
            generations: Number of generations (default 100)
            top_n: Number of top designs to return (default 10)

        Returns:
            OptimizationResult with Pareto front and best designs

        Examples:
            >>> assistant = DesignAssistant()
            >>> result = assistant.optimize_design(
            ...     driver_name="BC_12NDL76",
            ...     enclosure_type="sealed",
            ...     objectives=["f3", "size"],
            ...     population_size=50,
            ...     generations=50
            ... )
            >>> result.success
            True
            >>> result.n_designs_found
            47
            >>> len(result.best_designs)
            10
        """
        from viberesp.driver import bc_drivers
        from viberesp.optimization.parameters import (
            get_sealed_box_parameter_space,
            get_ported_box_parameter_space
        )
        from viberesp.optimization.objectives.composite import EnclosureOptimizationProblem
        from viberesp.optimization.optimizers.pymoo_interface import run_nsga2
        from viberesp.optimization.results.pareto_front import rank_designs

        # Driver name to function mapping
        driver_functions = {
            "BC_8NDL51": bc_drivers.get_bc_8ndl51,
            "BC_12NDL76": bc_drivers.get_bc_12ndl76,
            "BC_15DS115": bc_drivers.get_bc_15ds115,
            "BC_18PZW100": bc_drivers.get_bc_18pzw100,
        }

        # Validate driver
        if driver_name not in driver_functions:
            return OptimizationResult(
                success=False,
                pareto_front=[],
                n_designs_found=0,
                best_designs=[],
                parameter_names=[],
                objective_names=objectives,
                optimization_metadata={},
                warnings=[f"Unknown driver: {driver_name}"]
            )

        # Load driver
        driver = driver_functions[driver_name]()

        # Validate enclosure type
        if enclosure_type not in ["sealed", "ported"]:
            return OptimizationResult(
                success=False,
                pareto_front=[],
                n_designs_found=0,
                best_designs=[],
                parameter_names=[],
                objective_names=objectives,
                optimization_metadata={},
                warnings=[
                    f"Unsupported enclosure type: {enclosure_type}",
                    "Currently supported: sealed, ported"
                ]
            )

        # Get parameter space
        if enclosure_type == "sealed":
            param_space = get_sealed_box_parameter_space(driver)
        elif enclosure_type == "ported":
            param_space = get_ported_box_parameter_space(driver)
        else:
            return OptimizationResult(
                success=False,
                pareto_front=[],
                n_designs_found=0,
                best_designs=[],
                parameter_names=[],
                objective_names=objectives,
                optimization_metadata={},
                warnings=[f"Enclosure type {enclosure_type} not yet implemented"]
            )

        bounds_dict = param_space.get_bounds_dict()

        # Build constraint list
        constraint_list = []
        if constraints:
            if enclosure_type == "sealed":
                if "max_qtc" in constraints or "min_qtc" in constraints:
                    constraint_list.append("qtc_range")
            if "max_f3" in constraints:
                constraint_list.append("f3_limit")
            if "max_volume_liters" in constraints:
                constraint_list.append("volume_limit")

            # Add physical constraints
            constraint_list.append("max_displacement")

            if enclosure_type == "ported":
                constraint_list.append("port_velocity")
        else:
            # Default constraints
            constraint_list = ["max_displacement"]
            if enclosure_type == "ported":
                constraint_list.append("port_velocity")

        # Setup problem
        try:
            problem = EnclosureOptimizationProblem(
                driver=driver,
                enclosure_type=enclosure_type,
                objectives=objectives,
                parameter_bounds=bounds_dict,
                constraints=constraint_list
            )
        except Exception as e:
            return OptimizationResult(
                success=False,
                pareto_front=[],
                n_designs_found=0,
                best_designs=[],
                parameter_names=[],
                objective_names=objectives,
                optimization_metadata={},
                warnings=[f"Problem setup failed: {e}"]
            )

        # Run optimization
        try:
            result, metadata = run_nsga2(
                problem=problem,
                pop_size=population_size,
                n_generations=generations,
                verbose=False  # Don't print progress
            )
        except Exception as e:
            return OptimizationResult(
                success=False,
                pareto_front=[],
                n_designs_found=0,
                best_designs=[],
                parameter_names=param_space.get_parameter_names(),
                objective_names=objectives,
                optimization_metadata={},
                warnings=[f"Optimization failed: {e}"]
            )

        # Rank designs
        ranked = rank_designs(
            result,
            objectives=objectives,
            parameter_names=param_space.get_parameter_names(),
            top_n=top_n
        )

        # Convert to structured format
        pareto_designs = []
        for i in range(len(result.F)):
            # Handle both 1D and 2D arrays
            if len(result.X.shape) == 1:
                x_row = result.X
            elif len(result.X.shape) == 2:
                x_row = result.X[i]
            else:
                x_row = result.X[i]

            if len(result.F.shape) == 1:
                f_row = [result.F[i]]  # Make it iterable
            elif len(result.F.shape) == 2:
                f_row = result.F[i]
            else:
                f_row = result.F[i]

            pareto_designs.append({
                "parameters": dict(zip(param_space.get_parameter_names(), x_row)),
                "objectives": dict(zip(objectives, f_row))
            })

        # Apply constraint-specific overrides if provided
        if constraints:
            for i, design in enumerate(pareto_designs):
                # Add constraint values to metadata
                design["constraint_values"] = constraints

        return OptimizationResult(
            success=True,
            pareto_front=pareto_designs,
            n_designs_found=len(result.F),
            best_designs=ranked,
            parameter_names=param_space.get_parameter_names(),
            objective_names=objectives,
            optimization_metadata=metadata,
            warnings=[]
        )

    def sweep_parameter(
        self,
        driver_name: str,
        enclosure_type: str,
        parameter: str,
        param_min: float,
        param_max: float,
        steps: int = 50,
        fixed_params: Dict[str, float] = None
    ) -> ParameterSweepResult:
        """
        Perform parameter sweep to explore design space.

        Note: This is a simplified placeholder. Full implementation requires
        completing Phase 7.4 (parameter sweep).

        Args:
            driver_name: Name of driver
            enclosure_type: "sealed" or "ported"
            parameter: Parameter name to sweep (e.g., "Vb", "Fb")
            param_min: Minimum parameter value
            param_max: Maximum parameter value
            steps: Number of steps
            fixed_params: Dict of other fixed parameters

        Returns:
            ParameterSweepResult with sweep data and recommendations

        Examples:
            >>> assistant = DesignAssistant()
            >>> sweep = assistant.sweep_parameter(
            ...     driver_name="BC_12NDL76",
            ...     enclosure_type="sealed",
            ...     parameter="Vb",
            ...     param_min=0.01,
            ...     param_max=0.03,
            ...     steps=30
            ... )
            >>> len(sweep.parameter_values)
            30
        """
        # Placeholder - full implementation in Phase 7.4
        return ParameterSweepResult(
            parameter_swept=parameter,
            parameter_values=np.linspace(param_min, param_max, steps),
            results={
                "F3": np.array([]),
                "flatness": np.array([]),
                "efficiency": np.array([]),
                "size": np.array([])
            },
            sensitivity_analysis={},
            recommendations=[
                "Parameter sweep not yet implemented.",
                "See Phase 7.4 in the implementation plan."
            ]
        )

    def _explain_trade_offs(
        self,
        driver: ThieleSmallParameters,
        enclosure_type: str,
        performance: Dict
    ) -> str:
        """Generate explanation of design trade-offs."""
        if enclosure_type == "sealed":
            qtc = performance.get('Qtc', 'N/A')
            f3 = performance.get('F3', 'N/A')

            return (
                f"Sealed box trade-offs:\n"
                f"  • Larger box → lower F3 (better bass extension) but bigger size\n"
                f"  • Qtc = {qtc}: "
                f"{'Butterworth (flat)' if isinstance(qtc, float) and abs(qtc - 0.707) < 0.05 else 'Custom alignment'}\n"
                f"  • F3 = {f3 if isinstance(f3, float) else 'N/A'} Hz: "
                f"{'Good bass' if isinstance(f3, float) and f3 < 60 else 'Limited bass'}\n"
                f"  • Transient response: Excellent (sealed box has best damping)\n"
                f"  • Power handling: Good (acoustic suspension)"
            )
        elif enclosure_type == "ported":
            fb = performance.get('Fb', 'N/A')

            return (
                f"Ported box trade-offs:\n"
                f"  • Lower F3 than sealed for same size (~3-5 Hz improvement)\n"
                f"  • Fb = {fb if isinstance(fb, float) else 'N/A'} Hz: tuning frequency\n"
                f"  • Trade-off: Steep rolloff below Fb (driver unloading risk)\n"
                f"  • Size vs bass: Larger box + lower tuning = deeper bass\n"
                f"  • Efficiency: Better than sealed (typically +3dB)\n"
                f"  • Transient response: Good near Fb, poorer below tuning"
            )
        elif enclosure_type == "exponential_horn":
            return (
                f"Horn-loaded trade-offs:\n"
                f"  • Efficiency: Much higher than direct radiator (+6-10dB)\n"
                f"  • Size: Large enclosure required for low-frequency extension\n"
                f"  • Bass extension: Limited by horn length and mouth size\n"
                f"  • Complexity: More difficult to design and build\n"
                f"  • Note: Requires horn simulation (Phase 3) for optimization"
            )
        return "Trade-off analysis not available for this enclosure type."
