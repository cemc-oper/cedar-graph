from dataclasses import dataclass
from copy import deepcopy
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, ContourLabelStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedarkit.comp.smooth import smth9
from cedarkit.comp.util import apply_to_xarray_values

from cemc_plot_kit.data import DataLoader
from cemc_plot_kit.data.field_info import div_info, u_info, v_info
from cemc_plot_kit.logger import get_logger


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
    div_field: xr.DataArray
    u_field: xr.DataArray
    v_field: xr.DataArray
    div_level: float
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        div_level: float,
        wind_level: float,
) -> PlotData:
    # data loader -> data field
    plot_logger.debug(f"loading wind {wind_level}hPa...")

    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    u_field = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    v_field = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading div {div_level}hPa...")
    div_level_info = deepcopy(div_info)
    div_level_info.level_type = "pl"
    div_level_info.level = div_level
    div_field = data_loader.load(
        field_info=div_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    # data field -> plot data
    plot_logger.debug("calculating...")
    div_field = div_field * 1.0e5
    div_field = apply_to_xarray_values(div_field, lambda x: smth9(x, 0.5, -0.25, False))
    div_field = apply_to_xarray_values(div_field, lambda x: smth9(x, 0.5, -0.25, False))

    return PlotData(
        div_field=div_field,
        u_field=u_field,
        v_field=v_field,
        div_level=div_level,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    div_field = plot_data.div_field
    u_field = plot_data.u_field
    v_field = plot_data.v_field

    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name

    div_levels = np.arange(-50, -5 + 5, 5)
    div_colormap = get_ncl_colormap("WhBlGrYeRe", count=len(div_levels) + 1, spread_start=98, spread_end=0)

    div_style = ContourStyle(
        colors=div_colormap,
        levels=div_levels,
        fill=True,
    )
    div_line_style = ContourStyle(
        colors="black",
        levels=div_levels,
        linewidths=0.5,
        linestyles="solid",
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
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
    else:
        domain = CnAreaMapTemplate(area=plot_metadata.area_range)

    panel = Panel(domain=domain)
    panel.plot(div_field[::5, ::5], style=div_style)
    panel.plot(div_field[::5, ::5], style=div_line_style)
    panel.plot([[u_field[::3, ::3], v_field[::3, ::3]]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=f"{plot_metadata.area_name} {plot_metadata.div_level}hPa Divergence ($1.0^{{-5}}s^{{-1}}$) and Wind(m/s)",
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=div_style)

    return panel
