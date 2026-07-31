"""
Fixtures for mock-based tests that can run in CI without CMA-HPC.

The :class:`MockDataSource` lives in :mod:`cedar_graph.testing` so it
can be reused by the documentation gallery as well as the test suite.
"""
import sys
from pathlib import Path

import pandas as pd
import matplotlib
import pytest
from loguru import logger

from cedar_graph.data import DataLoader
from cedar_graph.testing import MockDataSource

# Use non-interactive backend for CI
matplotlib.use("Agg")


def pytest_addoption(parser):
    parser.addoption(
        "--update-baseline",
        action="store_true",
        default=False,
        help="regenerate image baselines instead of comparing against them",
    )


@pytest.fixture(scope="session")
def update_baseline(request) -> bool:
    """Whether to regenerate image baselines."""
    return request.config.getoption("--update-baseline")


@pytest.fixture(scope="session")
def baseline_dir() -> Path:
    """Directory storing image baseline PNGs."""
    return Path(__file__).parent.absolute() / "baseline"


@pytest.fixture(scope="session")
def mock_data_source() -> MockDataSource:
    """Session-scoped mock data source."""
    return MockDataSource()


@pytest.fixture(scope="session")
def mock_data_loader(mock_data_source) -> DataLoader:
    """Session-scoped data loader with mock source."""
    return DataLoader(data_source=mock_data_source)


@pytest.fixture
def start_time() -> pd.Timestamp:
    """Fixed start time for reproducible tests."""
    return pd.Timestamp("2024-07-01 00:00:00")


@pytest.fixture
def forecast_time() -> pd.Timedelta:
    """Default 24h forecast time."""
    return pd.Timedelta(hours=24)


@pytest.fixture
def sample_step() -> float:
    """Sample step for metadata."""
    return 0.5


@pytest.fixture
def system_name() -> str:
    """System name for metadata."""
    return "CMA-GFS"


@pytest.fixture
def run_base_dir() -> Path:
    """Output directory for test images."""
    run_base_dir = Path(Path(__file__).parent.absolute(), "run_base_dir")
    return run_base_dir


logger.remove()
logger.add(sys.stderr, level="WARNING")
