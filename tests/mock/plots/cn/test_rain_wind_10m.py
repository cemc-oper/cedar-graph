"""Test rain_wind_10m plot with mock data."""
from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.rain_wind_10m.default import PlotMetadata, plot, load_data
from cedar_graph.data import DataLoader


@pytest.fixture
def plot_name():
    return "rain_wind_10m"


def test_rain_wind_10m_24h_cn(mock_data_source, start_time, forecast_time, system_name, sample_step, output_dir):
    """Test 24h rain + 10m wind plot for China domain."""
    interval = pd.Timedelta(hours=24)
    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        interval=interval,
    )

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        interval=interval,
        system_name=system_name,
        sample_step=sample_step,
    )

    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    output_path = Path(output_dir, "rain_wind_10m.24h.CN.png")
    panel.save(output_path)
    assert output_path.exists()
