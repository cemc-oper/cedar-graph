from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import xarray as xr
import pandas as pd
import numpy as np

import matplotlib.colors as mcolors

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedarkit.maps.style import ContourStyle, ContourLabelStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import hgt_info, mslp_info
from cedar_graph.data.operator import prepare_data
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata(BasePlotMetadata):
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: str = None


@dataclass
class PlotData:
    field_hgt_500: xr.DataArray
    field_mslp: xr.DataArray


def load_data(
        data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta, **kwargs
) -> PlotData:
    # data loader -> data field
    plot_logger.debug("loading height 500hPa...")
    hgt_500_info = deepcopy(hgt_info)
    hgt_500_info.level_type = "pl"
    hgt_500_info.level = 500
    field_h_500 = data_loader.load(
        field_info=hgt_500_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug("loading mslp...")
    field_mslp = data_loader.load(
        field_info=mslp_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    # data field -> plot data
    plot_logger.debug("calculating...")
    # 单位转换
    field_h_500 = field_h_500 / 10.
    # 平滑
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))
    field_h_500 = apply_to_xarray_values(field_h_500, lambda x: smth9(x, 0.5, 0.25, False))

    field_mslp = field_mslp / 100.
    field_mslp = apply_to_xarray_values(field_mslp, lambda x: smth9(x, 0.5, -0.25, False))
    field_mslp = apply_to_xarray_values(field_mslp, lambda x: smth9(x, 0.5, -0.25, False))

    plot_logger.debug("loading done")

    return PlotData(
        field_hgt_500=field_h_500,
        field_mslp=field_mslp,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range

    # style
    map_colors = np.array([
        (255, 255, 255),
        (0, 0, 0),
        (20, 100, 210),
        (40, 130, 240),
        (80, 165, 245),
        (150, 210, 250),
        (180, 240, 250),
        (203, 248, 253),
        (255, 255, 255),
        (180, 250, 170),
        (120, 245, 115),
        (55, 210, 60),
        (30, 180, 30),
        (15, 160, 15),
        (0, 0, 255),
        (255, 0, 0),
        (255, 140, 0),
        (238, 18, 137),
        (255, 121, 121),
        (211, 211, 211),
    ], dtype=float) / 255
    colormap = mcolors.ListedColormap(map_colors)

    mslp_colormap = mcolors.ListedColormap(colormap(np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])))
    mslp_contour_lev = np.array([980, 985, 990, 995, 1000, 1005, 1020, 1025, 1030, 1035, 1040])
    mslp_style = ContourStyle(
        colors=mslp_colormap,
        levels=mslp_contour_lev,
        fill=True,
    )

    h_contour_lev = np.linspace(500, 588, endpoint=True, num=23)
    h_linewidths = np.where(h_contour_lev == 588, 1.4, 0.7)
    color_list = np.where(h_contour_lev == 588, 1, 14)
    hgt_style = ContourStyle(
        levels=h_contour_lev,
        colors=mcolors.ListedColormap(colormap(color_list)),
        linewidths=h_linewidths,
        label=True,
        label_style=ContourLabelStyle(
            manual=False,
            inline=True,
            fontsize=7,
            fmt="{:.0f}".format,
            colors=colormap([15]),
        )
    )

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=area_range)

    graph_name = "500 hPa Height(10gpm), Sea Level Pressure(hPa,shadow)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_mslp = plot_data.field_mslp
    plot_field_hgt_500 = plot_data.field_hgt_500

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_mslp, style=mslp_style)
    panel.plot(plot_field_hgt_500, style=hgt_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=mslp_style)
    plot_logger.debug("plotting...done")

    return panel
