"""Test cape_wind plot with mock data."""
from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.cape_wind.default import PlotMetadata, plot, load_data
from cedar_graph.data import DataLoader


@pytest.fixture
def plot_name():
    return "cape_wind"


def test_cape_wind_cn(mock_data_source, start_time, forecast_time, system_name, sample_step, output_dir):
    """Test CAPE + wind plot for China domain."""
    wind_level = 850.0

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        wind_level=wind_level,
    )

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        wind_level=wind_level,
        sample_step=sample_step,
    )

    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    output_path = Path(output_dir, "cape_wind.CN.png")
    panel.save(output_path)
    assert output_path.exists()
