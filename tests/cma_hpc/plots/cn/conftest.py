from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pytest

from cedarkit.maps.util import AreaRange


@pytest.fixture
def component_run_base_dir(run_base_dir):
    return Path(run_base_dir, "plots/cn")


@dataclass
class PlotArea:
    name: str
    area: AreaRange
    level: float


@pytest.fixture
def cn_areas() -> list[PlotArea]:
    areas = [
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
    return areas


def get_plot_area(cn_areas, name: str) -> Optional[PlotArea]:
    for plot_area in cn_areas:
        if plot_area.name == name:
            return plot_area
    return None


@pytest.fixture
def cn_area_north_china(cn_areas):
    return get_plot_area(cn_areas, "NorthChina")
