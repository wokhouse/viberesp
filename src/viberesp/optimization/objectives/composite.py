"""
Multi-objective optimization problem for enclosure design.

This module implements the EnclosureOptimizationProblem class that
integrates viberesp's objective functions with pymoo's optimization
framework.

Literature:
    - Deb (2001) - Multi-Objective Optimization using Evolutionary Algorithms
    - pymoo documentation - NSGA-II implementation
    - Small (1972) - Enclosure design objectives

The problem class supports:
- Multiple objectives (F3, flatness, efficiency, size)
- Mixed constraints (physical and performance)
- Different enclosure types (sealed, ported)
"""

import numpy as np
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass

from pymoo.core.problem import Problem

from viberesp.driver.parameters import ThieleSmallParameters


@dataclass
class ObjectiveConfig:
    """
    Configuration for a single objective.

    Attributes:
        name: Objective name (e.g., "f3", "size")
        function: Objective function that takes (design_vector, driver, enclosure_type)
        minimize: True if objective should be minimized, False if maximized
        weight: Weight for weighted sum calculations (optional)
    """
    name: str
    function: Callable
    minimize: bool = True
    weight: float = 1.0


class EnclosureOptimizationProblem(Problem):
    """
    Multi-objective enclosure optimization problem for pymoo.

    This class wraps viberesp's objective functions into a format that
    pymoo's optimization algorithms can work with.

    Literature:
        - Deb (2001) - Multi-Objective Optimization using Evolutionary Algorithms
        - pymoo documentation - NSGA-II implementation
        - Small (1972) - Enclosure design objectives

    Attributes:
        driver: ThieleSmallParameters instance
        enclosure_type: Type of enclosure to optimize
        objective_configs: List of ObjectiveConfig objects
        constraint_funcs: List of constraint functions
        parameter_bounds: Dict mapping parameter names to (min, max) tuples
        param_names: List of parameter names in order
        n_obj: Number of objectives
        n_constr: Number of constraints
        num_segments: Number of segments for multisegment_horn (2 or 3)

    Examples:
        >>> driver = get_bc_8ndl51()
        >>> problem = EnclosureOptimizationProblem(
        ...     driver=driver,
        ...     enclosure_type="sealed",
        ...     objectives=["f3", "size"],
        ...     parameter_bounds={"Vb": (0.005, 0.030)}
        ... )
        >>> from pymoo.optimize import minimize
        >>> from pymoo.algorithms.moo.nsga2 import NSGA2
        >>> algorithm = NSGA2(pop_size=100)
        >>> result = minimize(problem, algorithm, termination=('n_gen', 100))
    """

    def __init__(
        self,
        driver: ThieleSmallParameters,
        enclosure_type: str,
        objectives: List[str],
        parameter_bounds: Dict[str, tuple],
        constraints: List[str] = None,
        num_segments: int = 2
    ):
        """
        Initialize optimization problem.

        Args:
            driver: ThieleSmallParameters instance
            enclosure_type: "sealed", "ported", "exponential_horn", "multisegment_horn", etc.
            objectives: List of objective names ["f3", "flatness", "efficiency", "size",
                       "wavefront_sphericity", "impedance_smoothness"]
            parameter_bounds: Dict of parameter ranges
            constraints: Optional list of constraint function names
            num_segments: Number of segments for multisegment_horn (2 or 3)
        """
        # Import objective functions
        from viberesp.optimization.objectives.response_metrics import (
            objective_f3,
            objective_response_flatness,
            objective_wavefront_sphericity,
            objective_impedance_smoothness,
        )
        from viberesp.optimization.objectives.efficiency import (
            objective_efficiency,
        )
        from viberesp.optimization.objectives.size_metrics import (
            objective_enclosure_volume,
        )

        # Map objective names to functions
        objective_map = {
            "f3": objective_f3,
            "flatness": objective_response_flatness,
            "efficiency": objective_efficiency,
            "size": objective_enclosure_volume,
            "wavefront_sphericity": objective_wavefront_sphericity,
            "impedance_smoothness": objective_impedance_smoothness,
        }

        # Create objective configurations
        self.objective_configs = []
        for obj_name in objectives:
            if obj_name not in objective_map:
                raise ValueError(f"Unknown objective: {obj_name}")

            self.objective_configs.append(ObjectiveConfig(
                name=obj_name,
                function=objective_map[obj_name],
                minimize=True  # All objectives are minimization
            ))

        # Import constraint functions
        self.constraint_funcs = []
        if constraints:
            from viberesp.optimization.constraints.physical import (
                constraint_max_displacement,
                constraint_port_velocity,
                constraint_multisegment_continuity,
                constraint_multisegment_flare_limits,
            )
            from viberesp.optimization.constraints.performance import (
                constraint_f3_limit,
                constraint_qtc_range,
                constraint_volume_limit,
            )

            constraint_map = {
                "max_displacement": constraint_max_displacement,
                "port_velocity": constraint_port_velocity,
                "f3_limit": constraint_f3_limit,
                "qtc_range": constraint_qtc_range,
                "volume_limit": constraint_volume_limit,
                "segment_continuity": constraint_multisegment_continuity,
                "flare_constant_limits": constraint_multisegment_flare_limits,
            }

            for constr_name in constraints:
                if constr_name in constraint_map:
                    self.constraint_funcs.append(constraint_map[constr_name])

        # Store problem parameters
        self.driver = driver
        self.enclosure_type = enclosure_type
        self.param_names = list(parameter_bounds.keys())
        self.num_segments = num_segments

        # Extract parameter bounds in order
        xl = np.array([parameter_bounds[p][0] for p in self.param_names])
        xu = np.array([parameter_bounds[p][1] for p in self.param_names])

        # Determine problem dimensions
        n_var = len(self.param_names)
        n_obj = len(self.objective_configs)
        n_constr = len(self.constraint_funcs)

        # Initialize parent Problem class
        super().__init__(
            n_var=n_var,
            n_obj=n_obj,
            n_constr=n_constr,
            xl=xl,
            xu=xu,
            vtype_double=True  # All parameters are continuous
        )

    def _evaluate(self, X, out, *args, **kwargs):
        """
        Evaluate objective functions for population X.

        pymoo calls this method with design matrix X (n_individuals × n_variables)

        Args:
            X: Design matrix where each row is a design vector
            out: Output dictionary to store results

        Note:
            Invalid designs (e.g., calculation failures) are heavily penalized
            by assigning large objective values.
        """
        n_individuals = X.shape[0]

        # Initialize objective matrix
        F = np.zeros((n_individuals, self.n_obj))

        # Determine if we need to pass num_segments parameter
        # (for multisegment_horn objectives)
        needs_num_segments = self.enclosure_type == "multisegment_horn"

        # Evaluate each individual
        for i in range(n_individuals):
            design_vector = X[i]

            # Evaluate each objective
            for j, obj_config in enumerate(self.objective_configs):
                try:
                    # For multisegment_horn objectives, pass num_segments
                    if needs_num_segments and obj_config.name in [
                        "wavefront_sphericity", "impedance_smoothness",
                        "response_flatness", "response_slope", "flatness", "slope"
                    ]:
                        obj_value = obj_config.function(
                            design_vector,
                            self.driver,
                            self.enclosure_type,
                            num_segments=self.num_segments
                        )
                    else:
                        obj_value = obj_config.function(
                            design_vector,
                            self.driver,
                            self.enclosure_type
                        )
                    F[i, j] = obj_value
                except Exception as e:
                    # Penalize invalid designs heavily
                    F[i, j] = 1e10
                    # Log warning for debugging (in development)
                    import warnings
                    warnings.warn(
                        f"Objective evaluation failed for design {i}, "
                        f"objective {j} ({obj_config.name}): {e}"
                    )

        # Evaluate constraints if any
        if self.n_constr > 0:
            G = np.zeros((n_individuals, self.n_constr))
            for i in range(n_individuals):
                design_vector = X[i]
                for j, constraint_func in enumerate(self.constraint_funcs):
                    try:
                        # For multisegment_horn constraints, pass num_segments
                        # Check if this is a multisegment constraint by name
                        func_name = constraint_func.__name__ if hasattr(constraint_func, '__name__') else ''
                        if needs_num_segments and 'multisegment' in func_name:
                            G[i, j] = constraint_func(
                                design_vector,
                                self.driver,
                                self.enclosure_type,
                                num_segments=self.num_segments
                            )
                        else:
                            G[i, j] = constraint_func(
                                design_vector,
                                self.driver,
                                self.enclosure_type
                            )
                    except Exception:
                        # If constraint fails, treat as violation
                        G[i, j] = 1000.0
            out["G"] = G

        out["F"] = F

    def decode_design_vector(self, x: np.ndarray) -> Dict[str, float]:
        """
        Decode design vector into parameter dictionary.

        Args:
            x: Design vector (1D array)

        Returns:
            Dict mapping parameter names to values
        """
        return dict(zip(self.param_names, x))

    def encode_design_vector(self, params: Dict[str, float]) -> np.ndarray:
        """
        Encode parameter dictionary into design vector.

        Args:
            params: Dict mapping parameter names to values

        Returns:
            Design vector (1D array)
        """
        return np.array([params[p] for p in self.param_names])
