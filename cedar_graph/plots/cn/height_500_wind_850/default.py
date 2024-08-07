from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.colors as mcolors

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import EastAsiaMapTemplate, CnAreaMapTemplate
from cedarkit.maps.util import AreaRange

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import hgt_info, u_info, v_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotData:
    hgt_500_field: xr.DataArray
    u_850_field: xr.DataArray
    v_850_field: xr.DataArray
    wind_speed_850_field: xr.DataArray


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None


def load_data(data_loader: DataLoader, start_time: pd.Timestamp, forecast_time: pd.Timedelta, **kwargs) -> PlotData:
    # data file -> data field
    plot_logger.debug("loading height 500hPa...")
    hgt_500_info = deepcopy(hgt_info)
    hgt_500_info.level_type = "pl"
    hgt_500_info.level = 500
    h_500_field = data_loader.load(
        field_info=hgt_500_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading u 850hPa...")
    u_850_info = deepcopy(u_info)
    u_850_info.level_type = "pl"
    u_850_info.level = 850
    u_850_field = data_loader.load(
        field_info=u_850_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading v 850hPa...")
    v_850_info = deepcopy(v_info)
    v_850_info.level_type = "pl"
    v_850_info.level = 850
    v_850_field = data_loader.load(
        field_info=v_850_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    # data field -> plot data
    plot_logger.debug("calculating...")
    # 单位转换
    h_500_field = h_500_field / 10.
    # 平滑
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))
    h_500_field = apply_to_xarray_values(h_500_field, lambda x: smth9(x, 0.5, 0.25, False))

    wind_speed_850_field = (np.sqrt(u_850_field * u_850_field + v_850_field * v_850_field))

    return PlotData(
        hgt_500_field=h_500_field,
        u_850_field=u_850_field,
        v_850_field=v_850_field,
        wind_speed_850_field=wind_speed_850_field,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    h_500_field = plot_data.hgt_500_field
    u_850_field = plot_data.u_850_field
    v_850_field = plot_data.v_850_field
    wind_speed_850_field = plot_data.wind_speed_850_field

    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

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

    wind_speed_colormap = mcolors.ListedColormap(colormap(np.array([2, 4, 5, 6, 7, 9, 10, 11])))
    wind_speed_contour_lev = np.array([12, 15, 18, 21, 24, 27, 30], dtype=int)
    wind_speed_style = ContourStyle(
        colors=wind_speed_colormap,
        levels=wind_speed_contour_lev,
        fill=True,
    )

    h_contour_lev = np.linspace(500, 588, endpoint=True, num=23)
    h_linewidths = np.where(h_contour_lev == 588, 1.4, 0.7)
    hgt_style = ContourStyle(
        levels=h_contour_lev,
        colors=mcolors.ListedColormap(colormap(np.full(len(h_contour_lev), 12))),
        linewidths=h_linewidths,
        label=True,
        label_style=ContourLabelStyle(
            manual=False,
            inline=True,
            fontsize=7,
            fmt="{:.0f}".format,
        )
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # plot
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)
    panel = Panel(domain=domain)
    panel.plot(wind_speed_850_field, style=wind_speed_style)
    panel.plot(h_500_field[::8, ::8], style=hgt_style)
    panel.plot([[u_850_field[::64, ::64], v_850_field[::64, ::64]]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name="500 hPa HGT (10gpm), 850 hPa Wind and Wind Speed(m/s, shadow)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=wind_speed_style)

    return panel