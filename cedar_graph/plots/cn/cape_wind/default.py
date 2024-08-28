from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

import numpy as np
import pandas as pd
import xarray as xr

from cedarkit.maps.style import ContourStyle, BarbStyle
from cedarkit.maps.chart import Panel
from cedarkit.maps.domains import CnAreaMapTemplate, EastAsiaMapTemplate
from cedarkit.maps.colormap import get_ncl_colormap
from cedarkit.maps.util import AreaRange

from cedar_graph.metadata import BasePlotMetadata
from cedar_graph.data import DataLoader
from cedar_graph.data.field_info import u_info, v_info, cape_info
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
    wind_level: float = None


@dataclass
class PlotData:
    field_cape: xr.DataArray
    field_u: xr.DataArray
    field_v: xr.DataArray
    wind_level: float


def load_data(
        data_loader: DataLoader,
        start_time: pd.Timestamp,
        forecast_time: pd.Timedelta,
        wind_level: float,
        **kwargs
) -> PlotData:
    plot_logger.debug("loading cape...")
    field_cape = data_loader.load(
        field_info=cape_info,
        start_time=start_time,
        forecast_time=forecast_time,
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    u_level_info = deepcopy(u_info)
    u_level_info.level_type = "pl"
    u_level_info.level = wind_level
    field_u = data_loader.load(
        field_info=u_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug(f"loading u {wind_level}hPa...")
    v_level_info = deepcopy(v_info)
    v_level_info.level_type = "pl"
    v_level_info.level = wind_level
    field_v = data_loader.load(
        field_info=v_level_info,
        start_time=start_time,
        forecast_time=forecast_time
    )

    plot_logger.debug("loading done")

    return PlotData(
        field_cape=field_cape,
        field_u=field_u,
        field_v=field_v,
        wind_level=wind_level,
    )


def plot(plot_data: PlotData, plot_metadata: PlotMetadata) -> Panel:
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

    # create domain
    if plot_metadata.area_range is None:
        domain = EastAsiaMapTemplate()
        graph_name = f"CAPE(J/kg) & {wind_level}hPa Wind(m/s)"
    else:
        domain = CnAreaMapTemplate(area=area_range)
        graph_name = f"{area_name} CAPE(J/kg) & {wind_level}hPa Wind(m/s)"

    # prepare data
    plot_logger.debug(f"preparing data...")
    total_area = domain.total_area()
    plot_data = prepare_data(plot_data=plot_data, plot_metadata=plot_metadata, total_area=total_area)

    plot_field_cape = plot_data.field_cape
    plot_field_u = plot_data.field_u
    plot_field_v = plot_data.field_v

    # plot
    plot_logger.debug(f"plotting...")
    panel = Panel(domain=domain)
    panel.plot(plot_field_cape, style=cape_style)
    panel.plot(plot_field_cape, style=cape_line_style)
    panel.plot([[plot_field_u, plot_field_v]], style=barb_style, layer=[0])

    domain.set_title(
        panel=panel,
        graph_name=graph_name,
        system_name=system_name,
        start_time=start_time,
        forecast_time=forecast_time,
    )
    domain.add_colorbar(panel=panel, style=cape_style)
    plot_logger.debug(f"plotting...done")

    return panel
