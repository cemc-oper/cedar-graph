"""Test radar_reflectivity plot with mock data."""
from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.radar_reflectivity.default import PlotMetadata, plot, load_data
from cedar_graph.data import DataLoader


@pytest.fixture
def plot_name():
    return "radar_reflectivity"


def test_radar_reflectivity_cn(mock_data_source, start_time, forecast_time, system_name, sample_step, output_dir):
    """Test radar composite reflectivity plot for China domain."""
    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        sample_step=sample_step,
    )

    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    output_path = Path(output_dir, "radar_reflectivity.CN.png")
    panel.save(output_path)
    assert output_path.exists()
