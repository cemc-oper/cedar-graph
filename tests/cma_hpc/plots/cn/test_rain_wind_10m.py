from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.rain_wind_10m.default import PlotMetadata, plot, load_data
from cedar_graph.data import LocalDataSource, DataLoader


@pytest.fixture
def plot_name():
    return "rain_wind_10m"


@pytest.fixture(
    scope='module',
    params=[
        "1h",
        "3h",
        "6h",
        "12h",
        "24h",
    ]
)
def interval(request) -> str:
    return request.param


def test_cn(plot_name, system_name, last_two_day, output_dir, default_sample_step, interval):
    if system_name == "CMA-GFS" and interval == "1h":
        pytest.skip("CMA-GFS output interval is 3h.")
    start_time = last_two_day
    forecast_time = pd.to_timedelta("24h")
    plot_interval = pd.to_timedelta(interval)

    output_image_path = Path(output_dir, f"{plot_name}.{interval}.{system_name}.CN.png")

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        interval=plot_interval,
        system_name=system_name,
        sample_step=default_sample_step,
    )

    data_source = LocalDataSource(system_name=system_name)
    data_loader = DataLoader(data_source=data_source)

    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        interval=metadata.interval,
    )

    panel = plot(
        plot_data=plot_data,
        plot_metadata=metadata,
    )

    output_dir.mkdir(exist_ok=True, parents=True)
    panel.save(output_image_path)


def test_cn_area(
        plot_name, system_name, last_two_day, cn_area_north_china, output_dir, default_sample_step, interval
):
    if system_name == "CMA-GFS" and interval == "1h":
        pytest.skip("CMA-GFS output interval is 3h.")
    start_time = last_two_day
    plot_area = cn_area_north_china
    forecast_time = pd.to_timedelta("24h")
    plot_interval = pd.to_timedelta(interval)

    area_name = plot_area.name
    area_range = plot_area.area

    output_image_path = Path(output_dir, f"{plot_name}.{interval}.{system_name}.{area_name}.png")

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        interval=plot_interval,
        system_name=system_name,
        area_name=area_name,
        area_range=area_range,
        sample_step=default_sample_step,
    )

    data_source = LocalDataSource(system_name=system_name)
    data_loader = DataLoader(data_source=data_source)

    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        interval=metadata.interval,
    )

    panel = plot(
        plot_data=plot_data,
        plot_metadata=metadata,
    )

    output_dir.mkdir(exist_ok=True, parents=True)
    panel.save(output_image_path)
