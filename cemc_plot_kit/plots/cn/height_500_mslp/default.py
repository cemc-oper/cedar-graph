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

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import hgt_info, mslp_info
from cemc_plot_kit.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotData:
    hgt_500_field: xr.DataArray
    mslp_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp
    forecast_time: pd.Timedelta
    system_name: str
    area_range: Optional[AreaRange] = None


def load_data(data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta) -> PlotData:
    # data loader -> data field
    plot_logger.info("loading height 500hPa...")
    hgt_500_info = deepcopy(hgt_info)
    hgt_500_info.level_type = "pl"
    hgt_500_info.level = 500
    h_500_field = data_loader.load(
        field_info=hgt_500_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.info("loading mslp...")
    mslp_field = data_loader.load(
        field_info=mslp_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    # data field -> plot data
    plot_logger.info("calculating...")
    # 单位转换
    h_500_field = h_500_field / 10.
    # 平滑
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))

    mslp_field = mslp_field / 100.
    mslp_field = apply_to_xarray_values(mslp_field, lambda x: smth9(x, 0.5, -0.25, False))
    mslp_field = apply_to_xarray_values(mslp_field, lambda x: smth9(x, 0.5, -0.25, False))

    return PlotData(
        hgt_500_field=h_500_field,
        mslp_field=mslp_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    h_500_field = plot_data.hgt_500_field
    mslp_field = plot_data.mslp_field

    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

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

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(mslp_field, style=mslp_style)
    panel.plot(h_500_field[::10, ::10], style=hgt_style)

    domain.set_title(
        panel=panel,
        graph_name="500 hPa Height(10gpm), Sea Level Pressure(hPa,shadow)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=mslp_style)

    return panel
