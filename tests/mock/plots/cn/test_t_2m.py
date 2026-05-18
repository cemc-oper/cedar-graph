"""Test t_2m plot with mock data."""
from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.t_2m.default import PlotMetadata, PlotData, plot


@pytest.fixture
def plot_name():
    return "t_2m"


def test_t_2m_cn(mock_data_source, start_time, forecast_time, system_name, sample_step, output_dir):
    """Test 2m temperature plot for China domain."""
    from cedar_graph.data import DataLoader
    from cedar_graph.plots.cn.t_2m.default import load_data

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
    output_path = Path(output_dir, "t_2m.CN.png")
    panel.save(output_path)
    assert output_path.exists()
