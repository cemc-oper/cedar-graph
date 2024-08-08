from dataclasses import dataclass
from typing import Optional, Dict
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.colors as mcolors

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, cin_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: str = None
    div_level: float = None
    wind_level: float = None


@dataclass
class PlotData:
    cin_field: xr.DataArray
    u_field: xr.DataArray
    v_field: xr.DataArray
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        **kwargs
) -> PlotData:
    plot_logger.debug("loading cin...")
    cin_field = data_loader.load(
        field_info=cin_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    u_field = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading v {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    return PlotData(
        cin_field=cin_field,
        u_field=u_field,
        v_field=v_field,
        wind_level=wind_level,
    )


def plot(
        plot_data: PlotData, plot_metadata: PlotMetadata
) -> Panel:
    cin_field = plot_data.cin_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name
    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    wind_level = plot_metadata.wind_level

    cin_levels = np.array([0, 10, 20, 30 ,40, 50, 60, 70, 80, 100, 150, 200])
    color_index = np.array([0, 64, 67, 70, 73, 76, 79, 82, 85, 88, 91, 94, 97])
    cin_colormap = get_ncl_colormap("WhViBlGrYeOrRe", index=color_index)

    cin_style = ContourStyle(
        colors=cin_colormap,
        levels=cin_levels,
        fill=True,
        # label=True,
        # label_style=ContourLabelStyle(
        #     fontsize=7,
        #     background_color="white"
        # )
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
        graph_name = f"CIN & {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} CIN & {wind_level}hPa Wind(m/s)"

    panel = Panel(domain=domain)
    panel.plot(cin_field[::2, ::2], style=cin_style)
    panel.plot([[u_field[::8, ::8], v_field[::8, ::8]]], style=barb_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=cin_style)

    return panel
