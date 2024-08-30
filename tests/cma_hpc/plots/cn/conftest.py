from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pytest

from cedarkit.maps.util import AreaRange


@pytest.fixture
def default_wind_level() -> float:
    return 850


@pytest.fixture
def default_sample_step() -> float:
    return 0.5


@pytest.fixture(
    scope='module',
    params=[
        "CMA-MESO",
        "CMA-TYM",
        "CMA-GFS",
        # "CMA-MESO-1KM"
    ]
)
def system_name(request) -> str:
    return request.param


@pytest.fixture
def component_run_base_dir(run_base_dir):
    return Path(run_base_dir, "plots/cn")


@pytest.fixture
def output_dir(component_run_base_dir, plot_name):
    return Path(component_run_base_dir) / plot_name


@dataclass
class PlotArea:
    name: str
    area: AreaRange
    level: float


cn_areas = [
    PlotArea(name="NorthEast", area=AreaRange.from_tuple((108, 137, 37, 55)), level=850),
    PlotArea(name="NorthChina", area=AreaRange.from_tuple((105, 125, 34, 45)), level=850),
    PlotArea(name="EastChina", area=AreaRange.from_tuple((105, 130, 28, 40)), level=850),
    PlotArea(name="SouthChina", area=AreaRange.from_tuple((103, 128, 15, 32)), level=850),
    PlotArea(name="East_NorthWest", area=AreaRange.from_tuple((85, 115, 30, 45)), level=700),
    PlotArea(name="East_SouthWest", area=AreaRange.from_tuple((95, 113, 20, 35)), level=700),
    PlotArea(name="XinJiang", area=AreaRange.from_tuple((70, 100, 33, 50)), level=700),
    PlotArea(name="XiZang", area=AreaRange.from_tuple((75, 105, 25, 40)), level=500),
    PlotArea(name="CentralChina", area=AreaRange.from_tuple((95, 120, 25, 40)), level=850),
]


@pytest.fixture(
    scope='module',
    params=cn_areas
)
def cn_area(request) -> PlotArea:
    return request.param


def get_plot_area(name: str) -> Optional[PlotArea]:
    for plot_area in cn_areas:
        if plot_area.name == name:
            return plot_area
    return None


@pytest.fixture
def cn_area_north_china():
    return get_plot_area("NorthChina")
