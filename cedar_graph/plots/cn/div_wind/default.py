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

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import div_info, u_info, v_info
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
    div_level: float = None
    wind_level: float = None


@dataclass
class PlotData:
    field_div: xr.DataArray
    field_u: xr.DataArray
    field_v: xr.DataArray
    div_level: float
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        div_level: float,
        wind_level: float,
        **kwargs
) -> PlotData:
    # data loader -> data field
    plot_logger.debug(f"loading wind {wind_level}hPa...")

    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    field_u = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    field_v = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading div {div_level}hPa...")
    div_level_info = deepcopy(div_info)
    div_level_info.level_type = "pl"
    div_level_info.level = div_level
    field_div = data_loader.load(
        field_info=div_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )


    # data field -> plot data
    plot_logger.debug("calculating...")
    field_div = field_div * 1.0e5
    field_div = apply_to_xarray_values(field_div, lambda x: smth9(x, 0.5, -0.25, False))
    field_div = apply_to_xarray_values(field_div, lambda x: smth9(x, 0.5, -0.25, False))

    plot_logger.debug("loading done")

    return PlotData(
        field_div=field_div,
        field_u=field_u,
        field_v=field_v,
        div_level=div_level,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
    start_time = plot_metadata.start_time
    forecast_time = plot_metadata.forecast_time
    system_name = plot_metadata.system_name
    area_name = plot_metadata.area_name
    area_range = plot_metadata.area_range
    div_level = plot_metadata.div_level

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

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"{area_name} {div_level}hPa Divergence ($1.0^{{-5}}s^{{-1}}$) and Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{div_level}hPa Divergence ($1.0^{{-5}}s^{{-1}}$) and Wind(m/s)"

    # prepare data
    plot_logger.debug("preparing data...")
    total_area = domain.total_area()
    plot_data = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_div = plot_data.field_div
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # plot
    plot_logger.debug("plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_div, style=div_style)
    panel.plot(plot_field_div, style=div_line_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=div_style)
    plot_logger.debug("plotting...done")

    return panel
