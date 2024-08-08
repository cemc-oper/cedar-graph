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
from cedar_graph.data.field_info import u_info, v_info, cape_info
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
    cape_field: xr.DataArray
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
    plot_logger.debug("loading cape...")
    cape_field = data_loader.load(
        field_info=cape_info,
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

    plot_logger.debug(f"loading u {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    return PlotData(
        cape_field=cape_field,
        u_field=u_field,
        v_field=v_field,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    cape_field = plot_data.cape_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    system_name = plot_metadata.system_name
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    area_range = plot_metadata.area_range
    area_name = plot_metadata.area_name
    wind_level = plot_metadata.wind_level

    cape_levels = np.array([
        0, 10, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000,
        1100, 1200, 1300, 1400, 1500, 1750, 2000, 2250, 2500
    ])

    color_index = np.array([2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57, 62, 67, 72, 77, 82, 87, 90, 93, 96, 99, 101]) - 2
    cape_colormap = get_ncl_colormap("WhBlGrYeRe", index=color_index)

    cape_style = ContourStyle(
        colors=cape_colormap,
        levels=cape_levels,
        fill=True,
    )
    cape_line_style = ContourStyle(
        # colors="white",
        colors=[cape_colormap.colors[0]],
        levels=cape_levels,
        linewidths=0.15,
        fill=False,
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
        graph_name = f"CAPE(J/kg) & {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} CAPE(J/kg) & {wind_level}hPa Wind(m/s)"

    panel = Panel(domain=domain)
    panel.plot(cape_field[::2, ::2], style=cape_style)
    panel.plot(cape_field[::2, ::2], style=cape_line_style)
    panel.plot([[u_field[::8, ::8], v_field[::8, ::8]]], style=barb_style)

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=cape_style)

    return panel
