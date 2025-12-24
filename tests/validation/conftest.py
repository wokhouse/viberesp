"""Shared pytest fixtures for validation tests."""

import json
from pathlib import Path

import pytest
import numpy as np

from viberesp.core.models import ThieleSmallParameters, EnclosureParameters
from viberesp.enclosures.horns import ExponentialHorn, FrontLoadedHorn
from viberesp.validation import parse_hornresp_output, parse_hornresp_params


@pytest.fixture
def fixture_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def synthetic_dir(fixture_dir):
    """Path to synthetic test cases directory."""
    return fixture_dir / "hornresp" / "synthetic"


@pytest.fixture
def driver_from_json(fixture_dir):
    """Load a driver from JSON file by name."""
    def _load_driver(driver_name: str) -> ThieleSmallParameters:
        driver_path = fixture_dir / "drivers" / f"{driver_name}.json"
        with open(driver_path) as f:
            data = json.load(f)
        return ThieleSmallParameters(**data)
    return _load_driver


@pytest.fixture
def load_hornresp_case():
    """Load a Hornresp test case (params, sim, metadata)."""
    def _load_case(case_dir: Path):
        """Load Hornresp parameters, simulation, and metadata from a case directory."""
        # Load parameters
        params_path = case_dir / "parameters.txt"
        hr_params = parse_hornresp_params(params_path)

        # Load simulation
        sim_path = case_dir / "simulation.txt"
        hr_sim = parse_hornresp_output(sim_path)

        # Load metadata
        metadata_path = case_dir / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)

        return hr_params, hr_sim, metadata
    return _load_case


@pytest.fixture
def baseline_metrics(fixture_dir):
    """Load global baseline metrics."""
    baseline_path = fixture_dir / "baselines" / "current.json"
    with open(baseline_path) as f:
        return json.load(f)


@pytest.fixture
def case_baseline():
    """Load baseline metrics for a specific test case."""
    def _load_baseline(case_dir: Path):
        baseline_path = case_dir / "baseline.json"
        with open(baseline_path) as f:
            return json.load(f)
    return _load_baseline


@pytest.fixture
def create_enclosure():
    """Create an enclosure from driver and parameters."""
    def _create(driver: ThieleSmallParameters, enclosure_type: str, params: dict):
        enclosure_params = EnclosureParameters(
            enclosure_type=enclosure_type,
            vb=0.0,  # Not used for horns
            **params
        )

        if enclosure_type == "front_loaded_horn":
            return FrontLoadedHorn(driver, enclosure_params)
        elif enclosure_type == "exponential_horn":
            return ExponentialHorn(driver, enclosure_params)
        else:
            raise ValueError(f"Unsupported enclosure type: {enclosure_type}")
    return _create
