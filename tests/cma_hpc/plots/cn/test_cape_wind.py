from pathlib import Path

import pytest
import pandas as pd

from cedar_graph.plots.cn.cape_wind.default import PlotMetadata, plot, load_data
from cedar_graph.data import LocalDataSource, DataLoader


@pytest.fixture
def plot_name():
    return "cape_wind"


@pytest.fixture
def output_dir(component_run_base_dir, plot_name):
    return Path(component_run_base_dir) / plot_name


@pytest.fixture
def default_wind_level() -> float:
    return 850



def test_cma_meso_cn(plot_name, cma_meso_system_name, last_two_day, default_wind_level, output_dir):
    system_name = cma_meso_system_name
    start_time = last_two_day
    forecast_time = pd.to_timedelta("24h")
    wind_level = default_wind_level

    output_image_path = Path(output_dir, f"{plot_name}.{system_name}.CN.png")

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        wind_level=wind_level,
    )

    data_source = LocalDataSource(system_name=system_name)
    data_loader = DataLoader(data_source=data_source)

    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        wind_level=wind_level,
    )

    panel = plot(
        plot_data=plot_data,
        plot_metadata=metadata,
    )

    output_dir.mkdir(exist_ok=True, parents=True)
    panel.save(output_image_path)


def test_cma_meso_cn_area(plot_name, cma_meso_system_name, last_two_day, cn_area_north_china, output_dir):
    system_name = cma_meso_system_name
    start_time = last_two_day
    forecast_time = pd.to_timedelta("24h")
    area_name = cn_area_north_china.name
    area_range = cn_area_north_china.area
    wind_level = cn_area_north_china.level

    output_image_path = Path(output_dir, f"{plot_name}.{system_name}.{area_name}.png")

    metadata = PlotMetadata(
        start_time=start_time,
        forecast_time=forecast_time,
        system_name=system_name,
        area_name=area_name,
        area_range=area_range,
        wind_level=wind_level,
    )

    data_source = LocalDataSource(system_name=system_name)
    data_loader = DataLoader(data_source=data_source)

    plot_data = load_data(
        data_loader=data_loader,
        start_time=start_time,
        forecast_time=forecast_time,
        wind_level=wind_level,
    )

    panel = plot(
        plot_data=plot_data,
        plot_metadata=metadata,
    )

    output_dir.mkdir(exist_ok=True, parents=True)
    panel.save(output_image_path)