from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info
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
    field_u_10m: xr.DataArray
    field_v_10m: xr.DataArray
    field_wind_speed_10m: xr.DataArray


def load_data(
        data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta,
        **kwargs
) -> PlotData:
    # data file -> data field
    plot_logger.debug("loading u 10m...")
    u_10m_info = deepcopy(u_info)
    u_10m_info.level_type = "heightAboveGround"
    u_10m_info.level = 10
    field_u_10m = data_loader.load(
        field_info=u_10m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading v 10m...")
    v_10m_info = deepcopy(v_info)
    v_10m_info.level_type = "heightAboveGround"
    v_10m_info.level = 10
    field_v_10m = data_loader.load(
        field_info=v_10m_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    # data field -> plot data
    plot_logger.debug("calculating...")
    field_u_10m = field_u_10m * 2.5
    field_v_10m = field_v_10m * 2.5
    field_wind_speed_10m = (np.sqrt(field_u_10m * field_u_10m + field_v_10m * field_v_10m)) / 2.5

    plot_logger.debug("loading done")

    return PlotData(
        field_u_10m=field_u_10m,
        field_v_10m=field_v_10m,
        field_wind_speed_10m=field_wind_speed_10m,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_range = plot_metadata.area_range

    # style
    map_colors = np.array([
        (255, 255, 255),
        (0, 0, 0),
        (255, 255, 255),
        (0, 200, 200),
        (0, 210, 140),
        (0, 220, 0),
        (160, 230, 50),
        (230, 220, 50),
        (230, 175, 45),
        (240, 130, 40),
        (250, 60, 60),
        (240, 0, 130),
        (0, 0, 255),
        (255, 140, 0),
        (238, 18, 137)
    ], dtype=float) / 255
    colormap = mcolors.ListedColormap(map_colors)

    wind_speed_colormap = mcolors.ListedColormap(colormap(np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])))
    wind_speed_contour_lev = np.array([3.4, 5.5, 8, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5])
    wind_speed_style = ContourStyle(
        colors=wind_speed_colormap,
        levels=wind_speed_contour_lev,
        fill=True,
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)
    graph_name = "10m Wind, 10m Wind Speed(m/s, shadow)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data : PlotData = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_wind_speed_10m = plot_data.field_wind_speed_10m
    plot_field_u_10m = plot_data.field_u_10m
    plot_field_v_10m = plot_data.field_v_10m

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_wind_speed_10m, style=wind_speed_style)
    panel.plot([[plot_field_u_10m, plot_field_v_10m]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=wind_speed_style)
    plot_logger.debug("plotting...done")

    return panel
