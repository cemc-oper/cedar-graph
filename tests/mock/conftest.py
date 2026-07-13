"""
Fixtures for mock-based tests that can run in CI without CMA-HPC.

Provides a MockDataSource that generates synthetic xarray DataArrays
with realistic coordinate structure (latitude/longitude grid covering
the East Asia domain).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
import pytest
from loguru import logger

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import FieldInfo
from cedar_graph.data.source import DataSource

# Use non-interactive backend for CI
matplotlib.use("Agg")


class MockDataSource(DataSource):
    """
    A mock data source that generates synthetic 2D fields.

    The generated fields cover the East Asia domain (60°E–150°E, 0°–70°N)
    with 0.25° resolution, producing smooth spatial patterns suitable
    for exercising the full plotting pipeline.
    """

    def __init__(self, resolution: float = 0.25):
        super().__init__()
        self.resolution = resolution
        # Grid covering East Asia + buffer
        self.lon = np.arange(60, 150 + resolution, resolution)
        self.lat = np.arange(70, 0 - resolution, -resolution)
        self._lon2d, self._lat2d = np.meshgrid(self.lon, self.lat)

    def retrieve(
            self,
            field_info: FieldInfo,
            start_time: pd.Timestamp,
            forecast_time: pd.Timedelta,
    ) -> xr.DataArray:
        """
        Generate a synthetic field based on field_info.name.

        Different field types produce different value ranges to ensure
        the plotting styles (colormaps, contour levels) work correctly.
        """
        field = self._generate_field(field_info)
        return field

    def _generate_field(self, field_info: FieldInfo) -> xr.DataArray:
        """Generate a synthetic field with values appropriate for the field type."""
        lon2d = self._lon2d
        lat2d = self._lat2d

        name = field_info.name
        # Use deterministic seed based on field name for reproducibility
        seed = sum(ord(c) for c in name)
        rng = np.random.default_rng(seed)

        if name == "t2m":
            # 2m temperature in K (270-310K range)
            values = 273.15 + 20.0 * np.cos(np.deg2rad(lat2d)) + 5.0 * np.sin(np.deg2rad(lon2d))
        elif name == "t":
            # Temperature at pressure level in K
            values = 250.0 + 15.0 * np.cos(np.deg2rad(lat2d)) + 3.0 * np.sin(np.deg2rad(lon2d * 2))
        elif name == "rh2m":
            # 2m relative humidity (50-100%)
            values = 75.0 + 20.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d))
        elif name == "h":
            # Geopotential height (5000-5900 gpm)
            values = 5500.0 + 300.0 * np.cos(np.deg2rad(lat2d)) - 100.0 * np.sin(np.deg2rad(lon2d))
        elif name == "mslp":
            # Mean sea level pressure (98000-104000 Pa)
            values = 101325.0 + 2000.0 * np.cos(np.deg2rad(lat2d * 1.5)) - 500.0 * np.sin(np.deg2rad(lon2d))
        elif name in ("u", ):
            # U wind component (-20 to 20 m/s)
            values = 10.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d * 1.5))
        elif name in ("v", ):
            # V wind component (-20 to 20 m/s)
            values = 8.0 * np.cos(np.deg2rad(lat2d * 1.5)) * np.sin(np.deg2rad(lon2d * 2))
        elif name == "cr":
            # Composite radar reflectivity (0-70 dBZ)
            values = 35.0 + 25.0 * np.sin(np.deg2rad(lat2d * 3)) * np.cos(np.deg2rad(lon2d * 3))
        elif name == "apcp":
            # Accumulated precipitation (0-200 mm)
            values = 50.0 + 40.0 * np.maximum(0, np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d * 2)))
            # Add some noise
            values = values + rng.uniform(0, 5, values.shape)
        elif name == "asnow":
            # Accumulated snow (0-0.05 m)
            values = 0.02 + 0.015 * np.maximum(0, np.cos(np.deg2rad(lat2d - 40))) * np.cos(np.deg2rad(lon2d * 2))
        elif name == "div":
            # Divergence (-5e-5 to 5e-5 s^-1)
            values = 3e-5 * np.sin(np.deg2rad(lat2d * 4)) * np.cos(np.deg2rad(lon2d * 3))
        elif name == "k":
            # K index (10-50)
            values = 30.0 + 15.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d))
        elif name == "cape":
            # CIN or CAPE (0-2500 J/kg)
            values = 800.0 + 600.0 * np.maximum(0, np.sin(np.deg2rad(lat2d * 2))) * np.cos(np.deg2rad(lon2d))
        elif name == "bli":
            # Best lifted index (-48 to 10)
            values = -20.0 + 15.0 * np.cos(np.deg2rad(lat2d * 2)) * np.sin(np.deg2rad(lon2d))
        elif name == "qv_div":
            # Moisture flux divergence
            values = -3e-7 + 2e-7 * np.sin(np.deg2rad(lat2d * 3)) * np.cos(np.deg2rad(lon2d * 2))
        elif name == "pte":
            # Pseudo-equivalent potential temperature (300-360 K)
            values = 330.0 + 20.0 * np.cos(np.deg2rad(lat2d)) + 5.0 * np.sin(np.deg2rad(lon2d))
        elif name == "vwsh":
            # Vertical wind shear (0-30 m/s)
            values = 10.0 + 8.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d * 1.5))
        elif name == "dpt":
            # Dew point temperature (240-290 K)
            values = 260.0 + 15.0 * np.cos(np.deg2rad(lat2d)) + 3.0 * np.sin(np.deg2rad(lon2d))
        else:
            # Generic field
            values = 10.0 * np.sin(np.deg2rad(lat2d * 2)) * np.cos(np.deg2rad(lon2d * 2))

        da = xr.DataArray(
            values,
            dims=["latitude", "longitude"],
            coords={"latitude": self.lat, "longitude": self.lon},
            name=name,
        )
        return da


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
