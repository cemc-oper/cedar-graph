from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, k_index_info
from cedar_graph.logger import get_logger


plot_logger = get_logger(__name__)


@dataclass
class PlotMetadata:
    start_time: pd.Timestamp = None
    forecast_time: pd.Timedelta = None
    system_name: str = None
    area_range: Optional[AreaRange] = None
    area_name: str = None
    wind_level: float = None


@dataclass
class PlotData:
    k_field: xr.DataArray
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
    plot_logger.debug("loading k index...")
    k_field = data_loader.load(
        field_info=k_index_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug("loading u...")
    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    u_field = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug("loading v...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    return PlotData(
        k_field=k_field,
        u_field=u_field,
        v_field=v_field,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    k_field = plot_data.k_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    wind_level = plot_metadata.wind_level

    k_levels = np.array([20, 25, 30, 35, 40, 45, 50])
    k_colormap = get_ncl_colormap("WhBlGrYeRe", index=[0, 15, 45, 55, 65, 75, 85, 95, 100])

    k_style = ContourStyle(
        colors=k_colormap,
        levels=k_levels,
        fill=True,
    )
    k_line_style = ContourStyle(
        colors="black",
        levels=k_levels,
        linewidths=0.5,
        fill=False,
        label=True,
        label_style=ContourLabelStyle(
            fontsize=7,
            background_color="white"
        )
    )

    barb_style = BarbStyle(
        barbcolor="black",
        flagcolor="black",
        linewidth=0.3,
        # barb_increments=dict(half=2, full=4, flag=20)
    )

    # plot
    if area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)

    panel = Panel(domain=domain)
    panel.plot(k_field[::3, ::3], style=k_style)
    panel.plot(k_field[::3, ::3], style=k_line_style)
    panel.plot([[u_field[::8, ::8], v_field[::8, ::8]]], style=barb_style)

    domain.set_title(
        panel=panel,
        graph_name=f"{area_name} K index(shadow) {wind_level}hPa Wind(m/s)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=k_style)

    return panel