"""Test shr (vertical wind shear) plot with mock data."""
from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.shr.default import PlotMetadata, plot, load_data
from cedar_graph.data import DataLoader


@pytest.fixture
def plot_name():
    return "shr"


def test_shr_0_6km_cn(mock_data_source, start_time, forecast_time, system_name, sample_step, output_dir):
    """Test 0-6km vertical wind shear plot for China domain."""
    first_level = 6000.0
    second_level = 0.0

    data_loader = DataLoader(data_source=mock_data_source)
    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        first_level=first_level,
        second_level=second_level,
    )

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        first_level=first_level,
        second_level=second_level,
        area_name="CN",
        sample_step=sample_step,
    )

    panel = plot(plot_data=plot_data, plot_metadata=metadata)
    output_path = Path(output_dir, "shr.0_6km.CN.png")
    panel.save(output_path)
    assert output_path.exists()
