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
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import cr_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_name: Optional[str] = None
    area_range: Optional[AreaRange] = None


@dataclass
class PlotData:
    field_cr: xr.DataArray


def load_data(
        data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta,
        **kwargs,
) -> PlotData:
    # data file -> data field
    plot_logger.debug("loading cr...")
    cr_field = data_loader.load(
        field_info=cr_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    # data field -> plot data
    plot_logger.debug("calculating...")
    cr_field = apply_to_xarray_values(cr_field, lambda x: smth9(x, 0.5, -0.25, False))
    cr_field = apply_to_xarray_values(cr_field, lambda x: smth9(x, 0.5, -0.25, False))

    plot_logger.debug("loading done")

    return PlotData(
        field_cr=cr_field
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range

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

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    graph_name = "Radar Composite Reflectivity(dBZ)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_cr = plot_data.field_cr

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_cr, style=cr_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=cr_style)
    plot_logger.debug("plotting...done")

    return panel
