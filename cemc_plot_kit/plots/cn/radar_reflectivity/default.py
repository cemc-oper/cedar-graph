from dataclasses import dataclass
from typing import Optional

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.colors as mcolors

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedarkit.maps.style import ContourStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import cr_info


@dataclass
class PlotData:
    cr_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None


def load_data(data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta) -> PlotData:
    # data file -> data field
    cr_field = data_loader.load(
        field_info=cr_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    # data field -> plot data
    cr_field = apply_to_xarray_values(cr_field, lambda x: smth9(x, 0.5, -0.25, False))
    cr_field = apply_to_xarray_values(cr_field, lambda x: smth9(x, 0.5, -0.25, False))

    return PlotData(
        cr_field=cr_field
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

    cr_field = plot_data.cr_field

    map_colors = np.array([
        (255, 255, 255),
        (0, 0, 0),
        (216, 216, 216),
        (1, 160, 246),
        (0, 236, 236),
        (0, 216, 0),
        (1, 144, 0),
        (255, 255, 0),
        (231, 192, 0),
        (255, 144, 0),
        (255, 0, 0),
        (214, 0, 0),
        (192, 0, 0),
        (255, 0, 240),
        (150, 0, 180),
        (173, 144, 240),
        (255, 140, 0),
        (238, 18, 137),
        (0, 0, 128)
    ], dtype=float) / 255
    colormap = mcolors.ListedColormap(map_colors)

    cr_contour_lev = np.arange(10, 75, 5)
    cr_color_map = mcolors.ListedColormap(colormap(np.array([0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])))
    cr_style = ContourStyle(
        colors=cr_color_map,
        levels=cr_contour_lev,
        fill=True,
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(cr_field, style=cr_style)

    domain.set_title(
        panel=panel,
        graph_name="Radar Composite Reflectivity(dBZ)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=cr_style)

    return panel
