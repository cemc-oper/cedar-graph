import sys
from pathlib import Path

import pandas as pd
from loguru import logger

import pytest


@pytest.fixture
def run_base_dir() -> Path:
    run_base_dir = Path(Path(__file__).parent.absolute(), "run_base_dir")
    return run_base_dir


@pytest.fixture
def last_two_day() -> pd.Timestamp:
    current = pd.Timestamp.now().floor(freq="D")
    last_two_day = current - pd.Timedelta(days=2)
    return last_two_day


@pytest.fixture
def cma_gfs_system_name() -> str:
    return "CMA-GFS"


@pytest.fixture
def cma_meso_system_name() -> str:
    return "CMA-MESO"


@pytest.fixture
def cma_tym_system_name() -> str:
    return "CMA-TYM"



logger.remove()
logger.add(sys.stderr, level="INFO")